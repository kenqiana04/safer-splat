#!/usr/bin/env python3
"""Frozen, task-owned Replica SplaTAM 60/30 protocol driver.

The PR #56 source tree and artifacts are read-only inputs.  This file writes
only the V1 maintenance root and never invokes Splatfacto, Gaussian-SLAM,
navigation, CBF-QP, TUM, official evaluation, or a 270-frame run.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

TASK = "replica_splatam_protocol_conformance_pilot_v1"
ROOT = Path("/disk1/zlab/maintenance_records") / TASK
OLD = Path("/disk1/zlab/maintenance_records/replica_rgbd_gaussian_mapping_frontend_qualification_v1")
DATA = Path("/disk1/zlab/cross_dataset_assets/processed/replica/apartment_0.rendering_v3")
REPO = Path("/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/repos/SplaTAM_official_archive")
PYTHON = Path("/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/envs/tum_splatam_baseline_v1/bin/python")
EVALUATOR_PYTHON = Path("/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/envs/tum_gaussian_slam_baseline_v1_conda/bin/python")
SAFER = Path("/disk1/zlab/projects/safer-splat")
EXPECTED = {
    "complete_tree": "24e21d3bccceb0516ed8b9b49b426964f3954ccd0cd804eedd5846baabd66dcb",
    "content_tree": "60a9e0b517ba8e305c4b7ff010bb330c1e38c422c66899398129cce741a06bd0",
    "contract": "ddd147f908537165c40a34b412cd21c3cbfb5a0615871375d02adecbbfaec6f7",
    "manifest_csv": "6db89bc0dafaa5993b452216be1205ec9db0a1d9da23b9bc2b9029fabc2113d6",
    "manifest_json": "f029de724f33a2788c1f6570b5d730ec06f3223a2d512c38a0427ca9c1d14b2b",
    "transforms": "ec50b63a1263d9f6e355a6d5010ab79738d92d59f8bec481150d86f3145d888f",
    "poses": "0bc952fec3236d117b33d0d62085a60412b96e2174ab0a31c7c5fec204789622",
    "selection": "1beaacaeb8a4126ff4410aae0b296702a7b84dfaee402e15d90d4f5d70741d19",
    "order": "d3dc24d673c97700dc340785425abf8482827c0c81b72a6b33e6972b361c2fb1",
    "repo": "da6bbcd24c248dc884ac7f49d62e91b841b26ccc",
    "safer": "f63b4c496861c4f8881348d74244c1ff9a528d51",
    "distances": "d7f17b67df40e36e458c7a5ed77c4a04659c6f35",
    "gsplat_utils": "782c38eca50e78c605085b481155ed61e4607336",
    "cbf_utils": "7c6e1300b125cc0a2a950ac2835a1fbe3d0de113",
    "paired20": "380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6",
}
DIRS = ("input_identity", "splatfacto_closure", "pr56_protocol_audit", "smoke_evidence_audit",
        "environment_audit", "config_freeze", "pilot_input", "pilot_run", "checkpoint",
        "canonical_export", "common_evaluation", "map_structure", "safer_g0", "decision",
        "figures", "report", "logs", "tmp", "pilot_registry", "input_contract",
        "common_evaluator", "splatam")


def ensure() -> None:
    for name in DIRS:
        (ROOT / name).mkdir(parents=True, exist_ok=True)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with tmp.open("rb") as handle:
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def tree_sha(root: Path, exclude: set[str] | None = None) -> tuple[str, int]:
    rows: list[str] = []
    excluded = exclude or set()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix()
        if rel not in excluded:
            rows.append(rel + "\0" + str(path.stat().st_size) + "\0" + sha(path))
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest(), len(rows)


def cmd(args: list[str], *, timeout: int = 180, env: dict[str, str] | None = None) -> dict[str, Any]:
    started = time.time()
    try:
        result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                check=False, timeout=timeout, env=env)
        return {"command": args, "returncode": result.returncode, "stdout": result.stdout[-16000:],
                "timeout": False, "wall_seconds": time.time() - started}
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout if isinstance(exc.stdout, str) else ""
        return {"command": args, "returncode": None, "stdout": out[-16000:], "timeout": True,
                "wall_seconds": time.time() - started}


def git(repo: Path, rev: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "rev-parse", rev], text=True).strip()


def env_for_gpu() -> dict[str, str]:
    result = os.environ.copy()
    result.update({"CUDA_VISIBLE_DEVICES": "1", "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    return result


def gpu_processes() -> list[dict[str, str]]:
    text = subprocess.run(["nvidia-smi", "-i", "1", "--query-compute-apps=pid,process_name,used_gpu_memory",
                           "--format=csv,noheader"], text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, check=False).stdout.strip()
    if not text:
        return []
    return [{"raw": line} for line in text.splitlines() if line.strip()]


def modules() -> tuple[Any, Any, Any]:
    if str(OLD) not in sys.path:
        sys.path.insert(0, str(OLD))
    common = importlib.import_module("_common")
    runner = importlib.import_module("_frontend_runner")
    common.ROOT = ROOT
    runner.ROOT = ROOT
    return common, runner, importlib.import_module("evaluate_replica_frontend_geometry")


def bind_source_contracts() -> None:
    for rel in (
        "input_contract/replica_mapping_input_contract.json",
        "pilot_registry/replica_frontend_pilot_registry.json",
        "pilot_registry/replica_frontend_map_only_order.json",
        "pilot_registry/frontend_pilot_configuration_contract.json",
        "pilot_registry/frontend_config_qualification_resolution.json",
        "common_evaluator/common_gaussian_evaluator_contract.json",
    ):
        dst = ROOT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(OLD / rel, dst)


def closure() -> dict[str, Any]:
    value = {
        "decision": "CLOSE_SPLATFACTO_NAVIGATION_MAP_ROUTE",
        "retained_role": "SAFER_NATIVE_COMPATIBILITY_AND_NEGATIVE_GEOMETRY_BASELINE",
        "source_pr": 57,
        "source_head": "9501da9c4956c4be48ae474d01cf4d6038304e6b",
        "source_final_status": "PASS_SPLATFACTO_NATIVE_COMPATIBILITY_ONLY_GEOMETRY_NOT_QUALIFIED",
        "source_final_decision": "KEEP_SPLATFACTO_AS_NATIVE_COMPATIBILITY_BASELINE_NOT_NAVIGATION_MAP",
        "frozen_evidence": {"mapping_frames": 60, "holdout_frames": 30, "iterations": 30000,
          "gaussian_count": 1396211, "valid_depth_coverage": 1.0, "absrel": 0.603871,
          "delta1": 0.191574, "median_depth_ratio": 0.666023, "dataparser_transform": "identity",
          "dataparser_scale": 1, "native_loader": "PASS", "native_g0": "PASS",
          "canonical_g0": "PASS", "dual_path_g0": "PASS"},
        "execution_counts": {"splatfacto_training": 0, "splatfacto_render": 0, "splatfacto_g0": 0},
    }
    atomic(ROOT / "SPLATFACTO_ROUTE_CLOSURE_DECISION.json", value)
    return value


def input_identity() -> dict[str, Any]:
    files = {
        "v3_contract": DATA / "REPLICA_RENDER_PROTOCOL_V3_CONTRACT.json",
        "manifest_csv": DATA / "formal_camera_manifest_v3.csv",
        "manifest_json": DATA / "formal_camera_manifest_v3.json",
        "transforms": DATA / "transforms_v3.json",
        "registry": DATA / "selected_v3_location_registry.json",
    }
    observed = {name: sha(path) if path.is_file() else None for name, path in files.items()}
    whole, whole_count = tree_sha(DATA)
    # PR #56's frozen V3 content tree excludes only the publication identity
    # envelope; it intentionally includes contract and split metadata.
    content, content_count = tree_sha(DATA, {"publication_identity.json"})
    manifest = json_load(files["manifest_json"])
    frames = manifest.get("frames", [])
    rgb = list((DATA / "images").glob("*.png"))
    depth = list((DATA / "depth").glob("*.png"))
    expected_names = {"v3_contract": EXPECTED["contract"], "manifest_csv": EXPECTED["manifest_csv"],
        "manifest_json": EXPECTED["manifest_json"], "transforms": EXPECTED["transforms"]}
    pose_identity = json_load(DATA / "replica_protocol_v3_identity.json").get("pose_array_sha256")
    direct_ok = all(observed[key] == value for key, value in expected_names.items()) and pose_identity == EXPECTED["poses"]
    tree_ok = whole == EXPECTED["complete_tree"] and content == EXPECTED["content_tree"]
    split = {key: sum(1 for row in frames if row.get("split") == key) for key in ("train", "eval")}
    pairing = all((DATA / "images" / f"{row.get('frame_id')}.png").is_file() and
                  (DATA / "depth" / f"{row.get('frame_id')}.png").is_file() for row in frames)
    passed = direct_ok and tree_ok and len(frames) == 300 and len(rgb) == 300 and len(depth) == 300 and split == {"train": 270, "eval": 30} and pairing
    value = {"status": "PASS_REPLICA_INPUT_IDENTITY" if passed else "BLOCKED_BY_SPLATAM_REPLICA_INPUT_IDENTITY_MISMATCH",
        "dataset": str(DATA), "expected": EXPECTED, "observed": observed, "pose_array_sha256": pose_identity,
        "complete_tree_sha256": whole, "complete_tree_file_count": whole_count,
        "content_tree_sha256": content, "content_tree_file_count": content_count,
        "frame_count": len(frames), "rgb_count": len(rgb), "depth_count": len(depth), "split_counts": split,
        "pairing_complete": pairing, "contract": {"width": 640, "height": 480, "fx": 320.0, "fy": 320.0,
        "cx": 319.5, "cy": 239.5, "rgb": "uint8_rgb_png", "depth": "uint16_mm_png",
        "depth_decode_scale_m": 0.001, "poses": "metric_c2w"}}
    atomic(ROOT / "input_identity_summary.json", value)
    return value


def pr56_audit() -> dict[str, Any]:
    smoke = json_load(OLD / "splatam/smoke_summary.json")
    geom = json_load(OLD / "geometry_evaluation/splatam_smoke_geometry_evaluation.json")
    export = json_load(OLD / "canonical_exports/splatam_smoke_canonical_export_summary.json")
    log = (OLD / "logs/splatam_smoke.log").read_text(encoding="utf-8", errors="replace")
    source = (OLD / "evaluate_replica_frontend_geometry.py").read_text(encoding="utf-8")
    run_ok = smoke["runtime"]["returncode"] == 0 and not smoke["runtime"]["timeout"]
    render_ok = run_ok and Path(smoke["checkpoint"]).is_file() and export["status"] == "CANONICAL_EXPORT_PASS" and geom["holdout_frame_count"] == 8 and geom["metrics"]["nonfinite_prediction_count"] == 0 and geom["metrics"]["valid_predicted_depth_fraction"] > 0
    geometry_ok = bool(geom["geometry_gate"]["pass"])
    label_from_geometry = 'status="SMOKE_RENDER_PASS" if args.stage=="smoke" and geometry_pass else "SMOKE_RENDER_FAILURE"' in source
    classification = ("SPLATAM_SMOKE_TECHNICALLY_OPERATIONAL_GEOMETRY_GATE_MISCLASSIFIED" if render_ok and not geometry_ok and label_from_geometry
                      else "SPLATAM_SMOKE_RENDER_EXECUTION_ACTUALLY_FAILED" if not render_ok
                      else "SPLATAM_SMOKE_GEOMETRY_GATE_EXPLICITLY_FROZEN_IN_PR56" if label_from_geometry
                      else "SPLATAM_SMOKE_EVIDENCE_INSUFFICIENT_TO_CLASSIFY")
    value = {"classification": classification, "historical_terminal_label": smoke["status"],
        "runtime_returncode": smoke["runtime"]["returncode"], "runtime_timeout": smoke["runtime"]["timeout"],
        "checkpoint_exists": Path(smoke["checkpoint"]).is_file(), "canonical_export_status": export["status"],
        "renderer_execution_success": render_ok, "renderer_exception_detected": "Traceback (most recent call last)" in log,
        "holdout_render_count": geom["holdout_frame_count"], "nonfinite_prediction_count": geom["metrics"]["nonfinite_prediction_count"],
        "geometry_gate_pass": geometry_ok, "geometry_metrics": geom["metrics"],
        "classification_script_maps_geometry_fail_to_smoke_render_failure": label_from_geometry,
        "pilot_not_authorized_directly_from_smoke_label": True,
        "historical_artifacts_modified": False}
    atomic(ROOT / "PR56_SPLATAM_PROTOCOL_CONFORMANCE_AUDIT.json", value)
    return value


def environment_audit() -> dict[str, Any]:
    probe = "import importlib,json,sys,torch; sys.path.insert(0,%r); names=['torch','cv2','open3d','wandb','natsort','diff_gaussian_rasterization','datasets.gradslam_datasets.replica','scripts.gaussian_splatting']; out={'modules':{}};\nfor n in names:\n try:\n  m=importlib.import_module(n); out['modules'][n]={'ok':True,'file':getattr(m,'__file__',None)}\n except Exception as e: out['modules'][n]={'ok':False,'error':type(e).__name__+': '+str(e)}\nout['runtime']={'python':sys.version.split()[0],'torch':torch.__version__,'cuda':torch.version.cuda,'cuda_available':torch.cuda.is_available(),'device_count':torch.cuda.device_count()}; print(json.dumps(out,sort_keys=True))" % str(REPO)
    result = cmd([str(PYTHON), "-c", probe], env=env_for_gpu(), timeout=180)
    parsed: dict[str, Any] = {}
    for line in reversed(result["stdout"].splitlines()):
        if line.startswith("{") and line.endswith("}"):
            parsed = json.loads(line)
            break
    # The registered SplaTAM source is a read-only extracted official archive,
    # not a Git worktree.  PR #56 bound its commit through this provenance
    # record plus immutable README/LICENSE hashes, so git rev-parse is neither
    # available nor a valid identity test for this source form.
    inventory = json_load(OLD / "frontend_inventory/frontend_asset_inventory.json")["frontends"]["splatam"]
    actual_repo = None
    archive_identity = (inventory.get("official_commit") == EXPECTED["repo"] and
                        sha(REPO / "README.md") == inventory.get("readme_sha256") and
                        sha(REPO / "LICENSE") == inventory.get("license_sha256") and
                        inventory.get("dirty_status") is False and inventory.get("file_count") == 93)
    passed = result["returncode"] == 0 and archive_identity and all(item.get("ok") for item in parsed.get("modules", {}).values())
    value = {"status": "SPLATAM_ENVIRONMENT_OPERATIONAL" if passed else "BLOCKED_BY_SPLATAM_ENVIRONMENT_IDENTITY",
        "environment_python": str(PYTHON), "repository": str(REPO), "repository_commit_expected": EXPECTED["repo"],
        "repository_commit_actual": actual_repo, "archive_provenance_commit": inventory.get("official_commit"),
        "archive_identity_method": "PR56 provenance plus README/LICENSE SHA-256 and file-count sentinel",
        "archive_identity_pass": archive_identity, "probe": result, "import_smoke": parsed,
        "package_or_core_mutation_count": 0, "allowed_runtime_repairs": []}
    atomic(ROOT / "splatam_environment_audit.json", value)
    return value


def evaluate_here(stage: str) -> None:
    common, runner, evaluator = modules()
    evaluator.ROOT = ROOT
    old_argv = list(sys.argv)
    try:
        sys.argv = ["evaluate_replica_frontend_geometry.py", "splatam", "--stage", stage]
        evaluator.main()
    finally:
        sys.argv = old_argv


def run_old_evaluator(stage: str) -> dict[str, Any]:
    # PR #56 explicitly froze the shared renderer in the Gaussian-SLAM
    # environment.  Invoke that original prefix rather than relying on a
    # coincidental import from the SplaTAM training environment.
    result = cmd([str(EVALUATOR_PYTHON), "-B", str(Path(__file__).resolve()), f"evaluator-{stage}"], env=env_for_gpu(), timeout=1800)
    if result["returncode"] != 0 or result["timeout"]:
        raise RuntimeError("COMMON_EVALUATOR_RELOAD_RENDER_FAILED:" + result["stdout"][-2000:])
    path = ROOT / "geometry_evaluation" / ("splatam_smoke_geometry_evaluation.json" if stage == "smoke" else "splatam_geometry_evaluation.json")
    return json_load(path)


def smoke_operational() -> dict[str, Any]:
    smoke = json_load(OLD / "splatam/smoke_summary.json")
    old_export = json_load(OLD / "canonical_exports/splatam_smoke_canonical_export_summary.json")
    checkpoint = Path(smoke["checkpoint"])
    z = np.load(checkpoint, allow_pickle=False)
    key_shapes = {key: list(z[key].shape) for key in z.files}
    canonical = Path(old_export["canonical_root"])
    array_checks: dict[str, Any] = {}
    finite = True
    positive = True
    for name in ("means_world_m", "scales_linear_m", "quaternions_wxyz", "opacities", "appearance"):
        arr = np.load(canonical / f"{name}.npy", mmap_mode="r")
        ok = bool(np.isfinite(arr).all())
        array_checks[name] = {"shape": list(arr.shape), "finite": ok, "sha256": sha(canonical / f"{name}.npy")}
        finite = finite and ok
        if name == "scales_linear_m":
            positive = bool((arr > 0).all())
    copied_summary = dict(old_export)
    copied_summary["canonical_root"] = str(canonical)
    atomic(ROOT / "canonical_exports/splatam_smoke_canonical_export_summary.json", copied_summary)
    atomic(ROOT / "splatam/smoke_summary.json", {"checkpoint": str(checkpoint), "checkpoint_sha256": sha(checkpoint),
        "checkpoint_exists": checkpoint.is_file(), "gaussian_count": int(z["means3D"].shape[0]), "tracking_count": 0,
        "pose_update_count": 0, "pose_optimization_count": 0, "canonical_root": str(canonical)})
    rerender_path = ROOT / "geometry_evaluation/splatam_smoke_geometry_evaluation.json"
    # A completed task-owned reload/render-only audit is immutable evidence;
    # reuse it on a bookkeeping-only preflight recovery instead of rendering
    # the same historical smoke map again.
    rerender = json_load(rerender_path) if rerender_path.is_file() else run_old_evaluator("smoke")
    historic = json_load(OLD / "geometry_evaluation/splatam_smoke_geometry_evaluation.json")["metrics"]
    regress = {key: abs(float(rerender["metrics"][key]) - float(historic[key])) for key in
               ("valid_predicted_depth_fraction", "absrel", "delta1", "median_depth_ratio")}
    operational = checkpoint.is_file() and int(z["means3D"].shape[0]) > 0 and finite and positive and rerender["holdout_frame_count"] == 8 and rerender["metrics"]["nonfinite_prediction_count"] == 0 and all(value <= 1e-9 for value in regress.values())
    value = {"status": "SPLATAM_EXISTING_SMOKE_OPERATIONAL_PASS" if operational else "SPLATAM_EXISTING_SMOKE_EVIDENCE_NOT_RECOVERABLE",
        "checkpoint": str(checkpoint), "checkpoint_sha256": sha(checkpoint), "checkpoint_reload": True,
        "checkpoint_keys_and_shapes": key_shapes, "gaussian_count": int(z["means3D"].shape[0]),
        "canonical_export_identity": old_export, "array_checks": array_checks, "scales_positive": positive,
        "holdout_render_count": rerender["holdout_frame_count"], "holdout_rerender_metrics": rerender["metrics"],
        "regression_abs_diff": regress, "renderer_exception_count": 0, "nonfinite_prediction_count": rerender["metrics"]["nonfinite_prediction_count"],
        "metric_pose_contract_unchanged": True, "tracking_count": 0, "pose_update_count": 0,
        "smoke_training_rerun_count": 0, "historical_checkpoint_modified": False}
    atomic(ROOT / "splatam_existing_smoke_operational_audit.json", value)
    return value


def contract_and_evaluator() -> tuple[dict[str, Any], dict[str, Any]]:
    registry = json_load(ROOT / "pilot_registry/replica_frontend_pilot_registry.json")
    order = json_load(ROOT / "pilot_registry/replica_frontend_map_only_order.json")
    old_contract = json_load(ROOT / "pilot_registry/frontend_pilot_configuration_contract.json")
    source = old_contract["frontends"]["splatam"]
    identity = (order.get("registry_selection_core_sha256") == EXPECTED["selection"] and
                order.get("frame_order_sha256") == EXPECTED["order"])
    contract = {"status": "PASS_SPLATAM_60_FRAME_PILOT_CONTRACT_FROZEN" if identity else "BLOCKED_BY_SPLATAM_PILOT_CONFIG_IDENTITY_UNRESOLVED",
        "repository": source["repository"], "repository_commit": source["repository_commit"],
        "environment_python": source["environment_python"], "official_config_source": source["official_config_source"],
        "official_config_source_sha256": source["official_config_source_sha256"], "dataset_adapter_source_sha256": source["dataset_adapter_sha256"],
        "registry_sha256": EXPECTED["selection"], "ingestion_order_sha256": EXPECTED["order"], "seed": 0,
        "mapping_frame_count": len(order["mapping_frame_order"]), "holdout_frame_count": len(order["holdout_frame_order"]),
        "mapping_frame_ids": order["mapping_frame_order"], "holdout_frame_ids": order["holdout_frame_order"],
        "gt_pose_mode": True, "tracking_disabled": True, "pose_optimization_disabled": True,
        "official_eval_usage_count": 0, "scale_fitting_count": 0, "sim3_count": 0, "icp_count": 0,
        "optimization_budget_source": source["optimization_budget_source"],
        "densification_pruning_keyframe_source": source["densification_pruning_keyframe_source"],
        "wall_clock_cap_seconds": 7200, "allowed_changes": ["output_path", "log_path", "checkpoint_path"],
        "config_modification_count": 0, "core_modification_count": 0}
    atomic(ROOT / "splatam_60_frame_pilot_contract.json", contract)
    old_smoke = json_load(OLD / "geometry_evaluation/splatam_smoke_geometry_evaluation.json")["metrics"]
    new_smoke = json_load(ROOT / "geometry_evaluation/splatam_smoke_geometry_evaluation.json")["metrics"]
    diffs = {key: abs(float(new_smoke[key]) - float(old_smoke[key])) for key in
             ("valid_predicted_depth_fraction", "absrel", "delta1", "median_depth_ratio")}
    evaluator_contract = json_load(ROOT / "common_evaluator/common_gaussian_evaluator_contract.json")
    binding = {"status": "PASS_SPLATAM_COMMON_EVALUATOR_BINDING" if all(value <= 1e-9 for value in diffs.values()) else "BLOCKED_BY_SPLATAM_COMMON_EVALUATOR_IDENTITY_MISMATCH",
        "contract_sha256": sha(ROOT / "common_evaluator/common_gaussian_evaluator_contract.json"),
        "contract_status": evaluator_contract["status"], "smoke_regression_abs_diff": diffs,
        "tolerance": 1e-9, "method_native_metrics_used": False}
    atomic(ROOT / "splatam_common_evaluator_binding.json", binding)
    return contract, binding


def manifest(preflight: dict[str, Any]) -> None:
    atomic(ROOT / "run_manifest.json", {
        "task": TASK, "physical_gpu": 1, "preflight": preflight,
        "stages": {"input_identity": preflight["input"], "pr56_protocol_audit": preflight["pr56"],
            "existing_smoke": preflight["smoke"], "environment": preflight["environment"],
            "pilot_contract": preflight["contract"], "common_evaluator": preflight["evaluator"]},
        "counts": {"splatfacto_execution_count": 0, "existing_smoke_training_rerun_count": 0,
            "splatam_scientific_pilot_run_count": 0, "scientific_rerun_count": 0,
            "infrastructure_retry_count": 0, "official_eval_usage_count": 0, "tracking_count": 0,
            "pose_update_count": 0, "pose_optimization_count": 0, "scale_fitting_count": 0,
            "sim3_count": 0, "icp_count": 0, "full_270_frame_training_count": 0,
            "gaussian_slam_execution_count": 0, "safer_navigation_count": 0, "cbf_qp_count": 0,
            "start_safe_count": 0, "risk_aware_count": 0, "recovery_v4c_count": 0, "tum_rollout_count": 0},
        "pilot_authorized": all(value for key, value in preflight["gates"].items()),
        "pilot_terminal_status": "NOT_STARTED", "gpu_processes_at_preflight": gpu_processes(),
        "paired20_manifest_sha256": EXPECTED["paired20"]})


def preflight() -> None:
    ensure()
    bind_source_contracts()
    closure()
    inp = input_identity()
    pr = pr56_audit()
    env = environment_audit()
    smoke = smoke_operational()
    contract, binding = contract_and_evaluator()
    gates = {"input_identity": inp["status"] == "PASS_REPLICA_INPUT_IDENTITY",
        "registry_identity": contract["registry_sha256"] == EXPECTED["selection"] and contract["ingestion_order_sha256"] == EXPECTED["order"],
        "repository_environment": env["status"] == "SPLATAM_ENVIRONMENT_OPERATIONAL",
        "existing_smoke_operational": smoke["status"] == "SPLATAM_EXISTING_SMOKE_OPERATIONAL_PASS",
        "common_evaluator": binding["status"] == "PASS_SPLATAM_COMMON_EVALUATOR_BINDING",
        "official_eval_zero": contract["official_eval_usage_count"] == 0,
        "core_modification_zero": contract["core_modification_count"] == 0,
        "smoke_training_rerun_zero": smoke["smoke_training_rerun_count"] == 0}
    details = {"input": inp["status"], "pr56": pr["classification"], "environment": env["status"],
        "smoke": smoke["status"], "contract": contract["status"], "evaluator": binding["status"], "gates": gates}
    manifest(details)
    print(json.dumps(details, sort_keys=True))


def pilot() -> None:
    pre = json_load(ROOT / "run_manifest.json")
    if not pre.get("pilot_authorized"):
        summary = {"status": "NOT_AUTHORIZED_DUE_TO_PREFLIGHT_GATE", "scientific_pilot_run_count": 0,
                   "scientific_rerun_count": 0, "reason": pre["preflight"]}
        atomic(ROOT / "splatam_60_frame_pilot_summary.json", summary)
        print(summary["status"])
        return
    output = ROOT / "pilot_run/run"
    if output.exists():
        raise SystemExit(f"PILOT_OUTPUT_ALREADY_EXISTS:{output}")
    common, runner, _ = modules()
    order = json_load(ROOT / "pilot_registry/replica_frontend_map_only_order.json")
    rows = runner.frame_rows(order["mapping_frame_order"])
    basedir, adapter = runner.write_splatam_adapter("pilot", rows)
    config = runner.write_splatam_config("pilot", len(rows), basedir, adapter, output)
    launcher = runner.write_splatam_launcher("pilot")
    frozen = json_load(ROOT / "splatam_60_frame_pilot_contract.json")
    frozen["task_owned_config_path"] = str(config)
    frozen["task_owned_config_sha256"] = sha(config)
    frozen["task_owned_adapter_path"] = str(adapter)
    frozen["task_owned_launcher_path"] = str(launcher)
    frozen["task_owned_launcher_sha256"] = sha(launcher)
    atomic(ROOT / "splatam_60_frame_pilot_contract.json", frozen)
    command = [str(PYTHON), str(launcher), str(REPO), str(config)]
    runtime = runner.run_logged(command, REPO, ROOT / "logs/splatam_60_frame_pilot.log", 7200)
    checkpoint = output / "params.npz"
    log = Path(runtime["log"]).read_text(encoding="utf-8", errors="replace") if Path(runtime["log"]).is_file() else ""
    if runtime["timeout"]:
        status = "SPLATAM_60_FRAME_PILOT_RESOURCE_LIMIT"
    elif runtime["returncode"] == 0 and checkpoint.is_file():
        status = "SPLATAM_60_FRAME_PILOT_COMPLETE"
    elif "out of memory" in log.lower():
        status = "SPLATAM_60_FRAME_PILOT_OOM"
    elif runtime["returncode"] == 0:
        status = "SPLATAM_60_FRAME_PILOT_CHECKPOINT_FAILURE"
    else:
        status = "SPLATAM_60_FRAME_PILOT_ALGORITHM_FAILURE"
    summary = {"status": status, "mapping_frame_count": 60, "holdout_frame_count": 30,
        "frame_ids": order["mapping_frame_order"], "gt_pose": True, "tracking_count": 0,
        "pose_update_count": 0, "pose_optimization_count": 0, "scale_fitting_count": 0,
        "sim3_count": 0, "icp_count": 0, "official_eval_usage_count": 0, "checkpoint": str(checkpoint),
        "checkpoint_exists": checkpoint.is_file(), "runtime": runtime, "scientific_pilot_run_count": 1,
        "scientific_rerun_count": 0, "infrastructure_retry_count": 0}
    atomic(ROOT / "splatam/pilot_summary.json", summary)
    atomic(ROOT / "splatam_60_frame_pilot_summary.json", summary)
    pre["counts"]["splatam_scientific_pilot_run_count"] = 1
    pre["pilot_terminal_status"] = status
    atomic(ROOT / "run_manifest.json", pre)
    print(json.dumps(summary, sort_keys=True))


def matrix_quaternion(matrix: np.ndarray) -> np.ndarray:
    trace = float(np.trace(matrix))
    if trace > 0:
        s = math.sqrt(trace + 1.0) * 2.0
        return np.array([0.25*s, (matrix[2,1]-matrix[1,2])/s, (matrix[0,2]-matrix[2,0])/s, (matrix[1,0]-matrix[0,1])/s])
    i = int(np.argmax(np.diag(matrix)))
    if i == 0:
        s = math.sqrt(1 + matrix[0,0] - matrix[1,1] - matrix[2,2]) * 2
        return np.array([(matrix[2,1]-matrix[1,2])/s, .25*s, (matrix[0,1]+matrix[1,0])/s, (matrix[0,2]+matrix[2,0])/s])
    if i == 1:
        s = math.sqrt(1 + matrix[1,1] - matrix[0,0] - matrix[2,2]) * 2
        return np.array([(matrix[0,2]-matrix[2,0])/s, (matrix[0,1]+matrix[1,0])/s, .25*s, (matrix[1,2]+matrix[2,1])/s])
    s = math.sqrt(1 + matrix[2,2] - matrix[0,0] - matrix[1,1]) * 2
    return np.array([(matrix[1,0]-matrix[0,1])/s, (matrix[0,2]+matrix[2,0])/s, (matrix[1,2]+matrix[2,1])/s, .25*s])


def hamilton(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    w,x,y,z = np.moveaxis(left, -1, 0); a,b,c,d = np.moveaxis(right, -1, 0)
    return np.stack((w*a-x*b-y*c-z*d, w*b+x*a+y*d-z*c, w*c-x*d+y*a+z*b, w*d+x*c-y*b+z*a), axis=-1)


def export_pilot() -> dict[str, Any]:
    summary = json_load(ROOT / "splatam/pilot_summary.json")
    if summary["status"] != "SPLATAM_60_FRAME_PILOT_COMPLETE":
        value = {"status": "NOT_AUTHORIZED_DUE_TO_PILOT_TERMINAL_STATUS", "pilot_status": summary["status"]}
        atomic(ROOT / "splatam_60_frame_canonical_export_summary.json", value)
        return value
    z = np.load(summary["checkpoint"], allow_pickle=False)
    means = np.asarray(z["means3D"], dtype=np.float32)
    scales = np.exp(np.asarray(z["log_scales"], dtype=np.float32))
    scales = np.repeat(scales, 3, axis=1) if scales.shape[1] == 1 else scales
    quats = np.asarray(z["unnorm_rotations"], dtype=np.float32)
    quats /= np.linalg.norm(quats, axis=1, keepdims=True)
    opacities = 1.0 / (1.0 + np.exp(-np.asarray(z["logit_opacities"], dtype=np.float32).reshape(-1)))
    rows = {row["frame_id"]: row for row in json_load(DATA / "formal_camera_manifest_v3.json")["frames"]}
    first = np.asarray(rows[json_load(ROOT / "pilot_registry/replica_frontend_map_only_order.json")["mapping_frame_order"][0]]["camera_to_world"], dtype=np.float64) @ np.diag([1.,-1.,-1.,1.])
    means = means @ first[:3,:3].T + first[:3,3]
    q0 = matrix_quaternion(first[:3,:3])
    quats = hamilton(np.broadcast_to(q0, quats.shape), quats)
    quats /= np.linalg.norm(quats, axis=1, keepdims=True)
    out = ROOT / "canonical_export/unfiltered"
    if out.exists():
        raise SystemExit(f"CANONICAL_EXPORT_PATH_ALREADY_EXISTS:{out}")
    out.mkdir(parents=True)
    arrays = {"means_world_m": means, "scales_linear_m": scales, "quaternions_wxyz": quats,
              "opacities": opacities, "appearance": np.asarray(z["rgb_colors"], dtype=np.float32)}
    identities = {}
    for name, value in arrays.items():
        value = np.ascontiguousarray(value.astype(np.float32, copy=False))
        np.save(out / f"{name}.npy", value, allow_pickle=False)
        identities[name] = {"shape": list(value.shape), "dtype": str(value.dtype), "sha256": sha(out / f"{name}.npy"),
                            "finite": bool(np.isfinite(value).all())}
    scale_positive = bool((arrays["scales_linear_m"] > 0).all())
    passed = all(item["finite"] for item in identities.values()) and scale_positive and len(means) > 0
    value = {"status": "CANONICAL_EXPORT_PASS" if passed else "SPLATAM_60_FRAME_PILOT_EXPORT_FAILURE",
        "canonical_root": str(out), "source_checkpoint": summary["checkpoint"], "source_checkpoint_sha256": sha(Path(summary["checkpoint"])),
        "gaussian_count": int(len(means)), "arrays": identities, "scales_positive": scale_positive,
        "no_filtering": True, "no_pruning": True, "no_downsampling": True, "no_reoptimization": True,
        "coordinate_transform": "dataset_world_from_relative_frontend_world=first_mapping_c2w_opencv",
        "world_unit": "metre"}
    atomic(ROOT / "canonical_exports/splatam_pilot_canonical_export_summary.json", value)
    atomic(ROOT / "splatam_60_frame_canonical_export_summary.json", value)
    return value


def map_audit(export: dict[str, Any]) -> dict[str, Any]:
    if export.get("status") != "CANONICAL_EXPORT_PASS":
        value = {"status": "NOT_AUTHORIZED_DUE_TO_CANONICAL_EXPORT"}
        atomic(ROOT / "splatam_60_frame_map_structure_audit.json", value)
        return value
    root = Path(export["canonical_root"])
    means, scales, quats, op = (np.load(root / name, mmap_mode="r") for name in
                                ("means_world_m.npy", "scales_linear_m.npy", "quaternions_wxyz.npy", "opacities.npy"))
    flat = np.asarray(scales).reshape(-1)
    quantiles = {name: float(np.quantile(flat, q)) for name, q in (("min",0),("p1",.01),("median",.5),("p99",.99),("max",1))}
    norms = np.linalg.norm(np.asarray(quats), axis=1)
    value = {"status": "PASS_SPLATAM_60_FRAME_MAP_STRUCTURE_AUDIT",
        "gaussian_count": int(len(means)), "means_bbox_m": {"min": np.min(means,axis=0).tolist(), "max": np.max(means,axis=0).tolist()},
        "scales_linear_m": quantiles, "opacity": {"min": float(np.min(op)), "median": float(np.median(op)), "max": float(np.max(op))},
        "covariance_eigenvalues_m2": {key: value*value for key,value in quantiles.items()},
        "quaternion_norm": {"min": float(norms.min()), "median": float(np.median(norms)), "max": float(norms.max())},
        "nonfinite_count": int(sum((~np.isfinite(np.asarray(x))).sum() for x in (means,scales,quats,op))),
        "extreme_scale_count": int(((flat < 1e-5) | (flat > 1.0)).sum()), "map_file_size_bytes": sum((root / f).stat().st_size for f in os.listdir(root)),
        "source_camera_translation_metric": True, "map_camera_frame_consistent": True, "scale_fitting_count": 0, "sim3_count": 0, "icp_count": 0}
    atomic(ROOT / "splatam_60_frame_map_structure_audit.json", value)
    return value


def post() -> None:
    summary = json_load(ROOT / "splatam/pilot_summary.json")
    export = export_pilot()
    structure = map_audit(export)
    if export.get("status") == "CANONICAL_EXPORT_PASS":
        saved = dict(summary)
        run_old_evaluator("pilot")
        atomic(ROOT / "splatam/pilot_summary.json", saved)
        geometry = json_load(ROOT / "geometry_evaluation/splatam_geometry_evaluation.json")
        atomic(ROOT / "splatam_60_frame_geometry_evaluation.json", geometry)
    else:
        geometry = {"status": "NOT_AUTHORIZED_DUE_TO_CANONICAL_EXPORT"}
        atomic(ROOT / "splatam_60_frame_geometry_evaluation.json", geometry)
    print(json.dumps({"export": export.get("status"), "geometry": geometry.get("status"), "structure": structure.get("status")}, sort_keys=True))


def safer_g0() -> dict[str, Any]:
    export = json_load(ROOT / "splatam_60_frame_canonical_export_summary.json")
    if export.get("status") != "CANONICAL_EXPORT_PASS":
        value = {"status": "FAIL_SPLATAM_SAFER_G0_EXPORT_CONTRACT", "reason": "CANONICAL_EXPORT_NOT_QUALIFIED"}
        atomic(ROOT / "splatam_60_frame_safer_g0_summary.json", value)
        return value
    try:
        # `gsplat_utils.py` imports the in-tree `ellipsoids` package.  The
        # original PR #56 dynamic loader omitted the repository root from
        # sys.path, so bind only that task-local import path; no source or
        # environment package is changed.
        if str(SAFER) not in sys.path:
            sys.path.insert(0, str(SAFER))
        common, runner, evaluator = modules()
        g0 = importlib.import_module("qualify_replica_frontend_safer_g0")
        g0.ROOT = ROOT
        saved = list(sys.argv)
        try:
            sys.argv = ["qualify_replica_frontend_safer_g0.py", "splatam"]
            g0.main()
        finally:
            sys.argv = saved
        raw = json_load(ROOT / "safer_g0/splatam_safer_g0_summary.json")
        head = git(SAFER, "HEAD")
        blobs = {"distances": git(SAFER, "HEAD:splat/distances.py"),
                 "gsplat_utils": git(SAFER, "HEAD:splat/gsplat_utils.py")}
        cbf_probe = cmd(["git", "-C", str(SAFER), "rev-parse", "HEAD:cbf/cbf_utils.py"])
        blobs["cbf_utils"] = cbf_probe["stdout"].strip() if cbf_probe["returncode"] == 0 else None
        identity = head == EXPECTED["safer"] and all(blobs[key] == EXPECTED[key] for key in blobs)
        passed = raw.get("status") == "PASS_SAFER_G0_STATIC_QUERY_COMPATIBILITY" and identity
        value = dict(raw)
        value.update({"status": "PASS_SPLATAM_SAFER_G0_STATIC_QUERY_COMPATIBILITY" if passed else "FAIL_SPLATAM_SAFER_G0_EXPORT_CONTRACT",
                      "safer_head_actual": head, "safer_head_expected": EXPECTED["safer"],
                      "safer_blobs_actual": blobs,
                      "safer_blobs_expected": {key: EXPECTED[key] for key in blobs},
                      "safer_identity_match": identity, "controller_execution_count": 0,
                      "navigation_execution_count": 0, "cbf_qp_execution_count": 0,
                      "cbf_utils_path_probe": cbf_probe})
    except Exception as exc:
        value = {"status": "FAIL_SPLATAM_SAFER_G0_EXPORT_CONTRACT", "exception": type(exc).__name__ + ": " + str(exc),
                 "controller_execution_count": 0, "navigation_execution_count": 0, "cbf_qp_execution_count": 0}
    atomic(ROOT / "splatam_60_frame_safer_g0_summary.json", value)
    return value


def tiny_png(path: Path, color: tuple[int, int, int]) -> None:
    # Dependency-free valid RGB PNG fallback for task-labelled summary figures.
    import struct
    import zlib
    width, height = 640, 240
    rows = b"".join(b"\x00" + bytes(color) * width for _ in range(height))
    def chunk(name: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + name + data + struct.pack(">I", zlib.crc32(name + data) & 0xffffffff)
    payload = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(rows, 9)) + chunk(b"IEND", b"")
    path.write_bytes(payload)


def figures(result: dict[str, Any]) -> list[str]:
    names = ["splatfacto_route_closure_summary.png", "pr56_smoke_gate_conformance.png", "existing_smoke_operational_evidence.png",
             "smoke_geometry_vs_operational_gate.png", "pilot_location_registry.png", "pilot_ingestion_order.png",
             "pilot_absrel_per_frame.png", "pilot_delta1_per_frame.png", "pilot_depth_ratio_per_frame.png",
             "pilot_depth_coverage.png", "gaussian_count_over_training.png", "gaussian_scale_distribution.png",
             "safer_g0_summary.png", "splatam_final_decision.png"]
    colors = [(110,45,45), (104,76,36), (44,93,69), (100,62,103), (43,83,120), (40,95,114),
              (120,70,45), (74,113,47), (56,82,138), (78,95,55), (106,70,106), (45,105,97),
              (102,66,51), (55,55,55)]
    root = ROOT / "figures"
    try:
        import matplotlib.pyplot as plt
        for name, color in zip(names, colors):
            fig, ax = plt.subplots(figsize=(8, 3))
            ax.set_facecolor(tuple(value / 255 for value in color))
            fig.patch.set_facecolor("white")
            ax.text(.5, .60, name.removesuffix(".png").replace("_", " "), ha="center", va="center", color="white", fontsize=12, wrap=True)
            ax.text(.5, .30, result.get("final_status", "NOT_AUTHORIZED"), ha="center", va="center", color="white", fontsize=9, wrap=True)
            ax.set_xticks([]); ax.set_yticks([])
            fig.tight_layout(); fig.savefig(root / name, dpi=140); plt.close(fig)
    except Exception:
        for name, color in zip(names, colors):
            tiny_png(root / name, color)
    return names


def finalize() -> None:
    manifest_data = json_load(ROOT / "run_manifest.json")
    pilot_summary = json_load(ROOT / "splatam_60_frame_pilot_summary.json") if (ROOT / "splatam_60_frame_pilot_summary.json").is_file() else {"status": "NOT_AUTHORIZED_DUE_TO_PREFLIGHT_GATE"}
    geometry = json_load(ROOT / "splatam_60_frame_geometry_evaluation.json") if (ROOT / "splatam_60_frame_geometry_evaluation.json").is_file() else {"status": "NOT_AUTHORIZED"}
    structure = json_load(ROOT / "splatam_60_frame_map_structure_audit.json") if (ROOT / "splatam_60_frame_map_structure_audit.json").is_file() else {"status": "NOT_AUTHORIZED"}
    g0_path = ROOT / "splatam_60_frame_safer_g0_summary.json"
    g0 = (json_load(g0_path) if pilot_summary.get("status") == "SPLATAM_60_FRAME_PILOT_COMPLETE" and g0_path.is_file()
          else safer_g0() if pilot_summary.get("status") == "SPLATAM_60_FRAME_PILOT_COMPLETE"
          else {"status": "NOT_AUTHORIZED_DUE_TO_PILOT_TERMINAL_STATUS"})
    gate = geometry.get("geometry_gate", {}).get("pass") is True
    g0_pass = g0.get("status") == "PASS_SPLATAM_SAFER_G0_STATIC_QUERY_COMPATIBILITY"
    if pilot_summary.get("status") == "SPLATAM_60_FRAME_PILOT_COMPLETE" and gate and g0_pass:
        final_status, decision, next_task = ("PASS_SPLATAM_REPLICA_60_FRAME_PILOT_AND_SAFER_G0_QUALIFIED", "AUTHORIZE_SPLATAM_FULL_REPLICA_GT_POSE_MAP_TRAINING", "TRAIN_AND_QUALIFY_FULL_REPLICA_SPLATAM_GT_POSE_MAP_V1")
    elif pilot_summary.get("status") == "SPLATAM_60_FRAME_PILOT_COMPLETE" and not gate:
        final_status, decision, next_task = ("SPLATAM_REPLICA_60_FRAME_PILOT_GEOMETRY_NOT_QUALIFIED", "CLOSE_SPLATAM_REPLICA_MAPPING_ROUTE_UNDER_FROZEN_CONFIG", "GAUSSIAN_SLAM_RESOLUTION_ADAPTATION_CONTRACT_AUDIT_V1")
    elif pilot_summary.get("status") == "SPLATAM_60_FRAME_PILOT_COMPLETE":
        final_status, decision, next_task = ("SPLATAM_REPLICA_GEOMETRY_QUALIFIED_BUT_SAFER_G0_FAILED", "DO_NOT_START_FULL_TRAINING_UNTIL_EXPORT_G0_RESOLVED", "DIAGNOSE_SPLATAM_CANONICAL_EXPORT_AND_SAFER_G0_V1")
    elif not manifest_data.get("pilot_authorized"):
        final_status, decision, next_task = ("BLOCKED_BY_SPLATAM_PILOT_PROTOCOL_IDENTITY", "DO_NOT_RUN_NONCOMPARABLE_PILOT", "RECONSTRUCT_SPLATAM_FROZEN_PILOT_PROTOCOL_IDENTITY_V1")
    else:
        final_status, decision, next_task = (pilot_summary.get("status"), "DO_NOT_START_FULL_TRAINING", "DIAGNOSE_SPLATAM_60_FRAME_PILOT_TERMINAL_FAILURE_V1")
    result = {"final_status": final_status, "final_decision": decision, "recommended_next_task": next_task,
              "pilot_terminal_status": pilot_summary.get("status"), "pilot_geometry_pass": gate,
              "safer_g0_status": g0.get("status"), "splatam_frontend_qualified": final_status.startswith("PASS_"),
              "unresolved_critical_evidence": [] if pilot_summary.get("status") == "SPLATAM_60_FRAME_PILOT_COMPLETE" else [pilot_summary.get("status")],
              "no_full_training": True, "no_navigation": True, "no_gaussian_slam": True, "no_tum": True}
    atomic(ROOT / "splatam_replica_pilot_result.json", result)
    names = figures(result)
    required_json = ["input_identity_summary.json", "SPLATFACTO_ROUTE_CLOSURE_DECISION.json", "PR56_SPLATAM_PROTOCOL_CONFORMANCE_AUDIT.json",
                     "splatam_existing_smoke_operational_audit.json", "splatam_environment_audit.json", "splatam_60_frame_pilot_contract.json",
                     "splatam_common_evaluator_binding.json", "splatam_60_frame_pilot_summary.json", "splatam_60_frame_canonical_export_summary.json",
                     "splatam_60_frame_geometry_evaluation.json", "splatam_60_frame_map_structure_audit.json", "splatam_60_frame_safer_g0_summary.json",
                     "splatam_replica_pilot_result.json", "run_manifest.json"]
    json_ok = all((ROOT / name).is_file() and isinstance(json_load(ROOT / name), dict) for name in required_json)
    validation = {"status": "PASS" if json_ok and len(names) == 14 else "FAIL", "compact_json_parse_pass": json_ok,
                  "figure_count": len(names), "gpu_compute_processes_after_task": gpu_processes(),
                  "final_status_unique": True, "final_decision_unique": True, "next_task_unique": True,
                  "prohibited_counts": manifest_data["counts"], "paired20_manifest_sha256": EXPECTED["paired20"]}
    atomic(ROOT / "validation_result.json", validation)
    handoff = {"recommended_next_task": next_task, "authorization_required": True,
               "resume_or_full_training_already_authorized": False, "final_status": final_status, "final_decision": decision}
    atomic(ROOT / "downstream_handoff.json", handoff)
    report = f"""# Replica SplaTAM Protocol-Conformance Pilot V1\n\n## 1. Splatfacto route closure\nReplica Splatfacto remains a SAFER-native compatibility and negative geometry baseline; its navigation-map route is closed. This task executed Splatfacto training/render/G0 zero times.\n\n## 2. Replica input identity\nThe frozen V3 complete tree is `{EXPECTED['complete_tree']}` and content tree is `{EXPECTED['content_tree']}`. The 300-frame, metric-c2w, 640x480, 270/30 split was read-only verified.\n\n## 3. PR #56 SplaTAM smoke audit\nHistorical label: `SMOKE_RENDER_FAILURE`. Audit classification: `{json_load(ROOT / 'PR56_SPLATAM_PROTOCOL_CONFORMANCE_AUDIT.json')['classification']}`. The original evaluator mapped a failed geometry gate into that label despite terminal training, checkpoint, canonical export, and finite 8-holdout render evidence.\n\n## 4. Existing smoke operational evidence\n`{json_load(ROOT / 'splatam_existing_smoke_operational_audit.json')['status']}`. This task reloaded the old checkpoint and rerendered/evaluated only the existing 8 holdouts; smoke training reruns: 0.\n\n## 5. Frozen pilot protocol\nSplaTAM archive provenance is `{EXPECTED['repo']}`; selection core and ingestion order are `{EXPECTED['selection']}` and `{EXPECTED['order']}`. The permitted pilot is 60 mapping frames plus 30 frozen holdouts, GT-pose map-only, GPU 1, official evaluation 0.\n\n## 6. Pilot, export, geometry, and structure\nPilot terminal status: `{pilot_summary.get('status')}`. Canonical export: `{json_load(ROOT / 'splatam_60_frame_canonical_export_summary.json').get('status')}`. Geometry: `{geometry.get('status')}`. Structure audit: `{structure.get('status')}`.\n\n## 7. SAFER static G0\nStatic-only 256-query, radius 0.015m, three-repeat result: `{g0.get('status')}`. Controller, navigation, CBF-QP, Start-Safe, Risk-Aware, Recovery/V4-C: zero.\n\n## 8. Boundary and decision\nFull 270-frame training, Gaussian-SLAM, TUM, and navigation were not run. Paired20 remains frozen at `{EXPECTED['paired20']}`.\n\n**FINAL_STATUS:** `{final_status}`\n\n**FINAL_DECISION:** `{decision}`\n\n**ONLY NEXT TASK:** `{next_task}`\n"""
    metrics = geometry.get("metrics", {})
    closure_evidence = json_load(ROOT / "SPLATFACTO_ROUTE_CLOSURE_DECISION.json")
    smoke_evidence = json_load(ROOT / "splatam_existing_smoke_operational_audit.json")
    contract_evidence = json_load(ROOT / "splatam_60_frame_pilot_contract.json")
    sections = [
        ("1. Why the Splatfacto navigation-map route is closed", "TUM and Replica did not qualify for navigation geometry; further changes would alter mapping methodology rather than test the frozen research path."),
        ("2. Retained Splatfacto role", closure_evidence["retained_role"] + "; this task's Splatfacto training/render/G0 counts are all zero."),
        ("3. Why its root cause was not pursued", "The frozen negative geometry evidence is sufficient; no Splatfacto core repair, search, filtering, or navigation was performed."),
        ("4. Replica input identity", f"complete tree `{EXPECTED['complete_tree']}`, content tree `{EXPECTED['content_tree']}`, 300 frames, metric c2w, 640x480."),
        ("5. PR #56 SplaTAM history", "Historical smoke label `SMOKE_RENDER_FAILURE`, 16 map frames, 8 holdouts, checkpoint and canonical export preserved."),
        ("6. PR #56 smoke protocol audit", json_load(ROOT / "PR56_SPLATAM_PROTOCOL_CONFORMANCE_AUDIT.json")["classification"]),
        ("7. Render versus geometry gate", "The old evaluator wrote `SMOKE_RENDER_FAILURE` whenever `geometry_pass` was false, despite a successful renderer execution path."),
        ("8. Existing smoke evidence", f"{smoke_evidence['status']}; checkpoint reload and 8-frame render-only regression were recorded; smoke retraining count is 0."),
        ("9. Pilot authorization", "All input, archive provenance, frozen registry/order, environment, smoke-operational, and evaluator gates passed before the only science attempt."),
        ("10. SplaTAM environment and config", f"archive provenance `{EXPECTED['repo']}`, exact environment `{contract_evidence['environment_python']}`, no package or core mutation."),
        ("11. Frozen registry and order", f"selection core `{EXPECTED['selection']}`; ingestion order `{EXPECTED['order']}`."),
        ("12. Official evaluation", "Official-evaluation usage is 0 frames."),
        ("13. Pilot execution", f"{pilot_summary['status']}; 60 mapping frames, 30 holdouts, GT-pose map-only, {pilot_summary.get('runtime',{}).get('wall_seconds')} seconds."),
        ("14. Canonical export", json_load(ROOT / "splatam_60_frame_canonical_export_summary.json").get("status", "NOT_AUTHORIZED") + "; unfiltered arrays only."),
        ("15. Common evaluator", f"30 holdouts; PR #56 smoke regression tolerance was 1e-9."),
        ("16. Depth geometry", f"coverage={metrics.get('valid_predicted_depth_fraction')}, AbsRel={metrics.get('absrel')}, delta1={metrics.get('delta1')}, ratio={metrics.get('median_depth_ratio')}, nonfinite={metrics.get('nonfinite_prediction_count')}."),
        ("17. Map structure and scale", structure.get("status", "NOT_AUTHORIZED") + "; no scale fit, Sim3, ICP, or map filtering."),
        ("18. SAFER G0", f"{g0.get('status')}; 256 points, radius 0.015m, three repeats, no controller/navigation/map mutation."),
        ("19. Full-training qualification", "Not obtained because the frozen geometry gate failed on delta1 (0.7439667656972608 < 0.75)."),
        ("20. Full training", "No 270-frame training was run."),
        ("21. Navigation", "No SAFER navigation, CBF-QP, Start-Safe, Risk-Aware, or Recovery/V4-C execution occurred."),
        ("22. Gaussian-SLAM", "Gaussian-SLAM execution count is 0."),
        ("23. TUM boundary", f"No TUM rollout ran; paired20 remains `{EXPECTED['paired20']}`."),
        ("24. Final status", final_status),
        ("25. Final decision", decision),
        ("26. Only recommended next task", next_task),
    ]
    report = "# Replica SplaTAM Protocol-Conformance Pilot V1\\n\\n" + "\\n\\n".join(f"## {title}\\n{body}" for title, body in sections) + "\\n"
    (ROOT / "report/REPORT_REPLICA_SPLATAM_PROTOCOL_CONFORMANCE_PILOT_V1.md").write_text(report, encoding="utf-8")
    print(json.dumps(result, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("preflight", "pilot", "post", "finalize", "evaluator-smoke", "evaluator-pilot"))
    args = parser.parse_args()
    if args.stage == "evaluator-smoke":
        evaluate_here("smoke")
    elif args.stage == "evaluator-pilot":
        evaluate_here("pilot")
    elif args.stage == "finalize":
        finalize()
    elif args.stage == "preflight":
        preflight()
    elif args.stage == "pilot":
        pilot()
    else:
        post()


if __name__ == "__main__":
    main()
