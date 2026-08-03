#!/usr/bin/env python3
"""Create and freeze the task-owned SplaTAM M1 runtime checkout and configs."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pprint
import shutil
import subprocess


OFFICIAL_HEAD = "da6bbcd24c248dc884ac7f49d62e91b841b26ccc"
OFFICIAL_SCRIPT_SHA256 = "ad7af3a7fda35786205df60b3e068502fd2d7f2fa1fcc5b00ee662061941f018"
PARENT_SHA256 = "d0c5270d8f4e08206b531092c120ad3a923634af6979b4410f0a5c7c8144c9e2"
TRAIN_SHA256 = "167066916ce1a3281ac754dfdeec37ada9f5b0e31227c731c94cebb698a2a6e3"
HELDOUT_SHA256 = "7b65f741e901690f2a723579d75200eebe7b9e77b0cd57c030d4a14d0474c0c7"
COMPAT_SHA256 = "8930c9d2e5172d0c56e698a418b3f454171e6c9fd84e3079d1f7c3568436a6f3"
SCENE = "48018874"
SEED = 20260730


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(args, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE).stdout.strip()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def flatten(value: object, prefix: str = "config") -> dict[str, object]:
    if not isinstance(value, dict):
        return {prefix: value}
    result: dict[str, object] = {}
    for key in sorted(value):
        result.update(flatten(value[key], f"{prefix}.{key}"))
    return result


def config_diff(parent: dict, child: dict) -> dict[str, dict[str, object]]:
    before, after = flatten(parent), flatten(child)
    return {key: {"before": before.get(key), "after": after.get(key)} for key in sorted(before.keys() | after.keys()) if before.get(key) != after.get(key)}


def resolved(parent: dict, *, task_root: Path, asset_root: Path, run_name: str, start: int, end: int, frames: int) -> dict:
    cfg = copy.deepcopy(parent)
    cfg["workdir"] = str(task_root / "outputs")
    cfg["run_name"] = run_name
    cfg["seed"] = SEED
    cfg["primary_device"] = "cuda:0"
    cfg["use_wandb"] = False
    cfg["data"].update({
        "dataset_name": "arkitscenes_m1",
        "basedir": str(asset_root.resolve()),
        "sequence": SCENE,
        "gradslam_data_cfg": str(task_root / "config" / "arkitscenes_m1_dataset.json"),
        "desired_image_height": 192,
        "desired_image_width": 256,
        "desired_image_height_init": 192,
        "desired_image_width_init": 256,
        "start": start,
        "end": end,
        "stride": 1,
        "num_frames": frames,
        "eval_stride": 1,
        "eval_num_frames": frames,
    })
    return cfg


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--official", type=Path, required=True)
    parser.add_argument("--train-manifest", type=Path, required=True)
    parser.add_argument("--heldout-manifest", type=Path, required=True)
    parser.add_argument("--asset-root", type=Path, required=True)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--compat", type=Path, required=True)
    parser.add_argument("--patch", type=Path, required=True)
    args = parser.parse_args()
    root, official = args.task_root.resolve(), args.official.resolve()
    runtime = root / "runtime_checkout" / "SplaTAM-m1-empty-depth-safe"
    root.mkdir(parents=True, exist_ok=True)

    checks = {
        "official_head": run("git", "rev-parse", "HEAD", cwd=official) == OFFICIAL_HEAD,
        "official_clean": run("git", "status", "--porcelain", cwd=official) == "",
        "official_script_sha256": sha(official / "scripts" / "gaussian_splatting.py") == OFFICIAL_SCRIPT_SHA256,
        "parent_sha256": sha(official / "configs" / "scannetpp" / "gaussian_splatting.py") == PARENT_SHA256,
        "train_sha256": sha(args.train_manifest) == TRAIN_SHA256,
        "heldout_sha256": sha(args.heldout_manifest) == HELDOUT_SHA256,
        "compat_sha256": sha(args.compat) == COMPAT_SHA256,
        "asset_root": args.asset_root.is_dir(),
    }
    if not all(checks.values()):
        write_json(root / "input_identity_failure.json", {"status": "BLOCKED_BY_ARKITSCENES_M1_MAPPING_INPUT_IDENTITY", "checks": checks})
        raise SystemExit("input identity gate failed")

    if runtime.exists():
        raise SystemExit("runtime checkout already exists; fail closed")
    runtime.parent.mkdir(parents=True, exist_ok=True)
    run("git", "clone", "--no-hardlinks", "--quiet", str(official), str(runtime))
    run("git", "checkout", "--detach", "--quiet", OFFICIAL_HEAD, cwd=runtime)
    shutil.copy2(args.adapter, runtime / args.adapter.name)
    shutil.copy2(args.compat, runtime / args.compat.name)
    patch_result = subprocess.run(["git", "apply", "--check", str(args.patch)], cwd=runtime, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if patch_result.returncode:
        raise SystemExit(f"runtime patch check failed: {patch_result.stderr}")
    run("git", "apply", str(args.patch), cwd=runtime)

    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    dataset_cfg = {
        "dataset_name": "arkitscenes_m1",
        "scene_id": SCENE,
        "expected_split": "TRAIN",
        "depth_mask_contract": "DEPTH_GT_ZERO_AND_CONFIDENCE_GE1",
        "manifest_path": str(args.train_manifest.resolve()),
        "manifest_sha256": TRAIN_SHA256,
        "asset_root": str(args.asset_root.resolve()),
        "camera_params": {"png_depth_scale": 1000.0, "image_height": 192, "image_width": 256, "fx": 1.0, "fy": 1.0, "cx": 0.0, "cy": 0.0},
    }
    write_json(config_dir / "arkitscenes_m1_dataset.json", dataset_cfg)

    os.environ["SCENE"] = "0"
    spec = importlib.util.spec_from_file_location("frozen_parent_config", official / "configs" / "scannetpp" / "gaussian_splatting.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parent = module.config
    variants = {
        "smoke_a": resolved(parent, task_root=root, asset_root=args.asset_root, run_name="NONFORMAL_SMOKE_A_ROWS_0_11", start=0, end=12, frames=12),
        "smoke_b": resolved(parent, task_root=root, asset_root=args.asset_root, run_name="NONFORMAL_SMOKE_B_ROWS_70_82", start=70, end=83, frames=13),
        "formal": resolved(parent, task_root=root, asset_root=args.asset_root, run_name="ARKITSCENES_SPLATAM_M1_EMPTY_DEPTH_SAFE_GT_POSE_MAP_ONLY_V1", start=0, end=214, frames=214),
    }
    diffs = {name: config_diff(parent, cfg) for name, cfg in variants.items()}
    allowed_exact = {
        "config.workdir", "config.run_name", "config.seed", "config.primary_device", "config.use_wandb",
        "config.data.dataset_name", "config.data.basedir", "config.data.sequence", "config.data.gradslam_data_cfg",
        "config.data.desired_image_height", "config.data.desired_image_width",
        "config.data.desired_image_height_init", "config.data.desired_image_width_init",
        "config.data.start", "config.data.end", "config.data.num_frames", "config.data.eval_num_frames",
    }
    for name, diff in diffs.items():
        illegal = sorted(set(diff) - allowed_exact)
        if illegal:
            raise SystemExit(f"unauthorized config changes in {name}: {illegal}")
        path = config_dir / f"{name}.py"
        path.write_text("config = " + pprint.pformat(variants[name], sort_dicts=True, width=120) + "\n", encoding="utf-8", newline="\n")

    git_diff = run("git", "diff", "--", "scripts/gaussian_splatting.py", cwd=runtime)
    (root / "runtime_integration").mkdir(parents=True, exist_ok=True)
    (root / "runtime_integration" / "applied.patch").write_text(git_diff, encoding="utf-8", newline="\n")
    runtime_files = [runtime / "scripts" / "gaussian_splatting.py", runtime / args.adapter.name, runtime / args.compat.name]
    write_json(root / "runtime_integration" / "runtime_identity.json", {
        "status": "PASS_TASK_OWNED_RUNTIME_INTEGRATION",
        "official_head": OFFICIAL_HEAD,
        "official_checkout_clean": run("git", "status", "--porcelain", cwd=official) == "",
        "runtime_head": run("git", "rev-parse", "HEAD", cwd=runtime),
        "patch_sha256": sha(root / "runtime_integration" / "applied.patch"),
        "runtime_files": {str(p.relative_to(runtime)): {"sha256": sha(p), "size": p.stat().st_size} for p in runtime_files},
    })
    write_json(root / "config" / "resolved_config_diff.json", {
        "status": "PASS_AUTHORIZED_SPLATAM_M1_CONFIG_DIFF_ONLY",
        "parent_sha256": PARENT_SHA256,
        "variants": {name: {"sha256": sha(config_dir / f"{name}.py"), "changes": diffs[name]} for name in variants},
        "frozen_semantics": {
            "mapping_iterations": parent["train"]["num_iters_mapping"],
            "loss_weights": parent["train"]["loss_weights"],
            "learning_rates": parent["train"]["lrs_mapping"],
            "densification": parent["train"]["densify_dict"],
            "gaussian_distribution": parent["gaussian_distribution"],
        },
    })
    write_json(root / "input_identity_freeze.json", {
        "status": "PASS_ARKITSCENES_M1_MAPPING_INPUT_IDENTITY",
        "checks": checks,
        "scene": SCENE,
        "train_rows": 214,
        "heldout_rows": 53,
        "train_sha256": TRAIN_SHA256,
        "heldout_sha256": HELDOUT_SHA256,
        "compat_sha256": COMPAT_SHA256,
        "split_identity_sha256": "97a707510227271d12859ee78defc0d6170cc24cb67e423568cd1a72e3345dee",
        "group_tuple_sha256": "8ad320980bb36edb2accb38629ec3046095c9ef7735fbb748f4e112ee75bd388",
        "m1_valid_pixels": 9277821,
        "zero_valid_train_indices": [76, 79],
    })
    print("PASS_RUNTIME_AND_CONFIG_FREEZE")


if __name__ == "__main__":
    main()
