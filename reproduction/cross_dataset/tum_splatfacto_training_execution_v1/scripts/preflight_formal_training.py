#!/usr/bin/env python3
"""Read-only preflight for the one frozen formal Splatfacto execution."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKTREE = ROOT.parents[2]
PROTOCOL = WORKTREE / "reproduction/cross_dataset/tum_splatfacto_training_protocol_v1"
DATA = Path("/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room")
TRANSFORMS = DATA / "transforms.json"
EXPECTED_RUN = Path("/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1/splatfacto/20260716_000000")
EXPECTED = {
    "command": "25e490904204622b0c2014ea4093f52efc507fb0543b675f9fe25871fd0d5b81",
    "config": "52fa5cdb93bcef333fc6e9f1c94043745a535e99d620e1f0fff85850f73f8105",
    "transforms": "b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def command(*args: str) -> dict[str, object]:
    completed = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {"argv": list(args), "returncode": completed.returncode, "stdout": completed.stdout.strip(), "stderr": completed.stderr.strip()}


def dump(name: str, value: object) -> None:
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def version(name: str) -> str | None:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return None


def main() -> None:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    host = command("hostname")
    environment: dict[str, object] = {
        "checked_at_utc": now,
        "hostname": host["stdout"],
        "conda_default_env": os.environ.get("CONDA_DEFAULT_ENV"),
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "expected": {"hostname": "zlab-Super-Server", "conda_name": "safer_splat_official", "conda_prefix": "/disk1/zlab/conda_envs/safer_splat_official", "python": "3.10.20", "cuda_visible_devices": "1", "torch": "2.1.2+cu118", "cuda": "11.8", "nerfstudio": "1.1.5", "gsplat": "1.4.0"},
    }
    try:
        import torch

        environment.update({"torch_version": torch.__version__, "cuda_version": torch.version.cuda, "cuda_available": torch.cuda.is_available(), "visible_device_count": torch.cuda.device_count(), "visible_device_0": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None})
    except Exception as exc:
        environment["torch_import_error"] = f"{type(exc).__name__}: {exc}"
    environment["nerfstudio_version"] = version("nerfstudio")
    environment["gsplat_version"] = version("gsplat")
    environment["status"] = "PASS" if all([
        environment["hostname"] == environment["expected"]["hostname"],
        environment["conda_default_env"] in {environment["expected"]["conda_name"], environment["expected"]["conda_prefix"]},
        environment["python_version"] == environment["expected"]["python"],
        environment["cuda_visible_devices"] == environment["expected"]["cuda_visible_devices"],
        environment.get("torch_version") == environment["expected"]["torch"],
        environment.get("cuda_version") == environment["expected"]["cuda"],
        environment["nerfstudio_version"] == environment["expected"]["nerfstudio"],
        environment["gsplat_version"] == environment["expected"]["gsplat"],
    ]) else "FAIL"
    dump("environment_preflight.json", environment)

    hashes = {
        "command_path": str(PROTOCOL / "exact_training_command.sh"),
        "frozen_config_path": str(PROTOCOL / "frozen_training_config.json"),
        "transforms_path": str(TRANSFORMS),
        "observed": {
            "command": sha256(PROTOCOL / "exact_training_command.sh"),
            "config": sha256(PROTOCOL / "frozen_training_config.json"),
            "transforms": sha256(TRANSFORMS),
        },
        "expected": EXPECTED,
    }
    hashes["status"] = "PASS" if hashes["observed"] == EXPECTED else "BLOCKED_BY_PROTOCOL_HASH_MISMATCH"
    dump("protocol_hash_verification.json", hashes)

    transforms = json.loads(TRANSFORMS.read_text(encoding="utf-8"))
    frames = transforms.get("frames", [])
    dataparser: dict[str, object] = {"model_created": False, "trainer_created": False, "optimizer_created": False, "data_path_exists": DATA.is_dir(), "transforms_exists": TRANSFORMS.is_file(), "source_frame_count": len(frames), "expected_train_count": 240, "expected_val_count": 60}
    try:
        from nerfstudio.data.dataparsers.nerfstudio_dataparser import Nerfstudio, NerfstudioDataParserConfig

        config = NerfstudioDataParserConfig(data=DATA, orientation_method="none", center_method="none", auto_scale_poses=False, downscale_factor=1, eval_mode="fraction", train_split_fraction=0.8, depth_unit_scale_factor=0.0002)
        parser = Nerfstudio(config)
        train = parser._generate_dataparser_outputs(split="train")
        val = parser._generate_dataparser_outputs(split="val")
        transform = train.dataparser_transform.detach().cpu()
        identity = __import__("torch").eye(4, dtype=transform.dtype)[: transform.shape[0], : transform.shape[1]]
        dataparser.update({
            "dataparser_api_invoked": True,
            "train_count": int(len(train.image_filenames)),
            "val_count": int(len(val.image_filenames)),
            "total_count": int(len(train.image_filenames) + len(val.image_filenames)),
            "frame_drop_count": int(len(frames) - len(train.image_filenames) - len(val.image_filenames)),
            "transform_shape": list(transform.shape),
            "transform_identity": bool(__import__("torch").allclose(transform, identity, atol=0.0, rtol=0.0)),
            "dataparser_scale": float(train.dataparser_scale),
            "orientation_method": config.orientation_method,
            "center_method": config.center_method,
            "auto_scale_poses": config.auto_scale_poses,
            "depth_unit_scale_factor": config.depth_unit_scale_factor,
        })
    except Exception as exc:
        dataparser["dataparser_error"] = f"{type(exc).__name__}: {exc}"
    dataparser["status"] = "PASS" if all([
        dataparser["data_path_exists"], dataparser["transforms_exists"], dataparser["source_frame_count"] == 300,
        dataparser.get("train_count") == 240, dataparser.get("val_count") == 60, dataparser.get("total_count") == 300,
        dataparser.get("frame_drop_count") == 0, dataparser.get("transform_identity") is True,
        dataparser.get("dataparser_scale") == 1.0, dataparser.get("orientation_method") == "none",
        dataparser.get("center_method") == "none", dataparser.get("auto_scale_poses") is False,
        dataparser.get("depth_unit_scale_factor") == 0.0002,
    ]) else "FAIL"
    dump("dataset_preflight.json", dataparser)

    gpu_query = command("nvidia-smi", "-i", "1", "--query-gpu=index,name,uuid,driver_version,memory.total", "--format=csv,noheader")
    compute_query = command("nvidia-smi", "-i", "1", "--query-compute-apps=pid,process_name,used_gpu_memory", "--format=csv,noheader")
    busy = compute_query["returncode"] == 0 and bool(compute_query["stdout"]) and "No running compute processes found" not in str(compute_query["stdout"])
    gpu = {"gpu_query": gpu_query, "compute_query": compute_query, "unrelated_compute_process_present": busy, "status": "BLOCKED_BY_GPU_BUSY" if busy else "PASS"}
    dump("gpu_preflight.json", gpu)

    requested_parent = EXPECTED_RUN.parent
    existing_parent = requested_parent
    while not existing_parent.exists():
        existing_parent = existing_parent.parent
    disk_usage = shutil.disk_usage(existing_parent)
    output = {"expected_run": str(EXPECTED_RUN), "exists_before_execution": EXPECTED_RUN.exists(), "requested_parent": str(requested_parent), "filesystem_probe_parent": str(existing_parent), "parent_writable": os.access(existing_parent, os.W_OK), "source_overlap": str(EXPECTED_RUN).startswith(str(DATA)), "free_bytes": disk_usage.free, "free_gib": disk_usage.free / (1024 ** 3), "minimum_free_gib": 20}
    disk_ok = output["free_gib"] >= 20 and output["parent_writable"] and not output["source_overlap"]
    output["status"] = "PASS" if disk_ok and not output["exists_before_execution"] else ("BLOCKED_BY_INSUFFICIENT_DISK" if output["free_gib"] < 20 else "FAIL")
    dump("disk_preflight.json", output)

    syntax_checks = [
        command("bash", "-n", str(PROTOCOL / "exact_training_command.sh")),
        command("bash", "-n", str(ROOT / "exact_execution_invocation.sh")),
        command("bash", "-n", str(ROOT / "exact_post_training_commands.sh")),
    ]
    syntax_ok = all(item["returncode"] == 0 for item in syntax_checks)
    checks = {"environment": environment["status"] == "PASS", "protocol_hashes": hashes["status"] == "PASS", "dataset_dataparser": dataparser["status"] == "PASS", "gpu_idle": gpu["status"] == "PASS", "disk_and_output": output["status"] == "PASS", "bash_syntax": syntax_ok}
    status = "PASS" if all(checks.values()) else next((str(value) for value in [hashes["status"], gpu["status"], output["status"]] if str(value).startswith("BLOCKED_")), "FAIL")
    dump("preflight_result.json", {"checked_at_utc": now, "status": status, "checks": checks, "bash_syntax_checks": syntax_checks, "training_command_executed": False, "model_created": False, "trainer_created": False})
    print(status)
    if status != "PASS":
        raise SystemExit(status)


if __name__ == "__main__":
    main()
