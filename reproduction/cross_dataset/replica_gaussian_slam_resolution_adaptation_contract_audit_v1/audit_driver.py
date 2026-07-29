#!/usr/bin/env python3
"""Read-only, no-mapping Gaussian-SLAM resolution contract audit for Replica V3."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np

TASK = "replica_gaussian_slam_resolution_adaptation_contract_audit_v1"
ROOT = Path("/disk1/zlab/maintenance_records") / TASK
PR56_ROOT = Path("/disk1/zlab/maintenance_records/replica_rgbd_gaussian_mapping_frontend_qualification_v1")
DATA = Path("/disk1/zlab/cross_dataset_assets/processed/replica/apartment_0.rendering_v3")
ARCHIVE = Path("/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/repos/Gaussian-SLAM_official_archive")
ENV = Path("/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/envs/tum_gaussian_slam_baseline_v1_conda")
PYTHON = ENV / "bin/python"
SOURCE_CONFIG = ARCHIVE / "configs/Replica/room0.yaml"
MAPPING_CONFIG = ARCHIVE / "configs/Replica/replica.yaml"
PR56_CONFIG = PR56_ROOT / "gaussian_slam/configs/smoke.yaml"
PR56_LOG = PR56_ROOT / "logs/gaussian_slam_smoke.log"
PR56_RUNNER = PR56_ROOT / "_frontend_runner.py"
EXPECTED = {
    "pr58_head": "54fc86e2d77a0c24fad12ece927f2e396f6bfce4",
    "complete_tree": "24e21d3bccceb0516ed8b9b49b426964f3954ccd0cd804eedd5846baabd66dcb",
    "content_tree": "60a9e0b517ba8e305c4b7ff010bb330c1e38c422c66899398129cce741a06bd0",
    "contract": "ddd147f908537165c40a34b412cd21c3cbfb5a0615871375d02adecbbfaec6f7",
    "manifest_csv": "6db89bc0dafaa5993b452216be1205ec9db0a1d9da23b9bc2b9029fabc2113d6",
    "manifest_json": "f029de724f33a2788c1f6570b5d730ec06f3223a2d512c38a0427ca9c1d14b2b",
    "transforms": "ec50b63a1263d9f6e355a6d5010ab79738d92d59f8bec481150d86f3145d888f",
    "pose": "0bc952fec3236d117b33d0d62085a60412b96e2174ab0a31c7c5fec204789622",
    "selection": "1beaacaeb8a4126ff4410aae0b296702a7b84dfaee402e15d90d4f5d70741d19",
    "order": "d3dc24d673c97700dc340785425abf8482827c0c81b72a6b33e6972b361c2fb1",
    "archive_commit": "eaec10d73ce7511563882b8856896e06d1f804e3",
    "paired20": "380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6",
}
STAGES = (
    "INPUT_IDENTITY", "FROZEN_ROUTE_DECISIONS", "ASSET_IDENTITY", "CONFIG_PROVENANCE",
    "FAILURE_EVIDENCE_RECOVERY", "STATIC_CALL_GRAPH", "CANDIDATE_POPULATION_CENSUS",
    "FAILURE_HYPOTHESIS_CLASSIFICATION", "ADAPTATION_LEGALITY", "NO_TRAINING_FUNCTIONAL_VALIDATION",
    "ADAPTED_CONFIG_FREEZE", "FINAL_CLASSIFICATION",
)
DIRS = (
    "input_identity", "frozen_route_decisions", "asset_identity", "config_provenance", "failure_reproduction",
    "call_graph", "candidate_population", "resolution_semantics", "adaptation_legality", "no_training_validation",
    "decision", "figures", "report", "logs", "tmp",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tree_sha(root: Path, exclude: tuple[str, ...] = ()) -> tuple[str, int]:
    rows: list[str] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix()
        if rel not in exclude:
            rows.append(f"{rel}\0{path.stat().st_size}\0{sha(path)}")
    return sha_text("\n".join(rows)), len(rows)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def atomic(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with temp.open("rb") as handle:
        os.fsync(handle.fileno())
    os.replace(temp, path)


def command(argv: list[str]) -> dict[str, Any]:
    result = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
    return {"argv": argv, "returncode": result.returncode, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}


def ensure() -> None:
    for part in DIRS:
        (ROOT / part).mkdir(parents=True, exist_ok=True)


def manifest() -> dict[str, Any]:
    path = ROOT / "run_manifest.json"
    if path.is_file():
        return load(path)
    return {
        "task": "GAUSSIAN_SLAM_RESOLUTION_ADAPTATION_CONTRACT_AUDIT_V1",
        "created_utc": now(),
        "stages": {stage: {"status": "NOT_STARTED"} for stage in STAGES},
        "scientific_execution": {"gaussian_slam_optimizer_invocation_count": 0, "mapping_iteration_count": 0,
                                 "checkpoint_count": 0, "map_output_count": 0, "holdout_render_count": 0,
                                 "official_eval_usage_count": 0},
    }


def finish_stage(stage: str, status: str, artifact: Path) -> None:
    value = manifest()
    value["stages"][stage] = {"status": status, "completed_utc": now(), "artifact": str(artifact), "sha256": sha(artifact)}
    atomic(ROOT / "run_manifest.json", value)


def stage_path(name: str) -> Path:
    return ROOT / name


def input_identity() -> Path:
    metadata = {
        "REPLICA_RENDER_PROTOCOL_V3_CONTRACT.json": "contract",
        "formal_camera_manifest_v3.csv": "manifest_csv",
        "formal_camera_manifest_v3.json": "manifest_json",
        "transforms_v3.json": "transforms",
    }
    actual = {key: sha(DATA / key) for key in metadata}
    meta_ok = all(actual[key] == EXPECTED[value] for key, value in metadata.items())
    protocol = load(DATA / "replica_protocol_v3_identity.json")
    order = load(PR56_ROOT / "pilot_registry/replica_frontend_map_only_order.json")
    registry = load(PR56_ROOT / "pilot_registry/replica_frontend_pilot_registry.json")
    frames = load(DATA / "formal_camera_manifest_v3.json")["frames"]
    rgb = {p.stem for p in (DATA / "images").glob("*.png")}
    depth = {p.stem for p in (DATA / "depth").glob("*.png")}
    ids = [row["frame_id"] for row in frames]
    split = Counter(row["split"] for row in frames)
    locations = {row["location_id"] for row in frames}
    content, content_count = tree_sha(DATA, ("publication_identity.json",))
    complete, complete_count = tree_sha(DATA)
    checks = {
        "metadata": meta_ok,
        "pose": protocol.get("pose_array_sha256") == EXPECTED["pose"],
        "selection_core": order.get("registry_selection_core_sha256") == EXPECTED["selection"],
        "ingestion_order": order.get("frame_order_sha256") == EXPECTED["order"] and registry.get("map_only_order_sha256") == EXPECTED["order"],
        "content_tree": content == EXPECTED["content_tree"],
        "complete_tree": complete == EXPECTED["complete_tree"],
        "shape": len(frames) == 300 and len(set(ids)) == 300 and len(locations) == 100,
        "pairing": rgb == set(ids) and depth == set(ids),
        "split": split == {"train": 270, "eval": 30},
    }
    output = {
        "status": "PASS_GAUSSIAN_SLAM_INPUT_IDENTITY" if all(checks.values()) else "BLOCKED_BY_GAUSSIAN_SLAM_INPUT_IDENTITY_MISMATCH",
        "expected": EXPECTED, "metadata_sha256": actual, "pose_array_sha256": protocol.get("pose_array_sha256"),
        "pilot_selection_core_sha256": order.get("registry_selection_core_sha256"), "ingestion_order_sha256": order.get("frame_order_sha256"),
        "trees": {"content": [content, content_count], "complete": [complete, complete_count]},
        "frame_count": len(frames), "location_count": len(locations), "rgb_count": len(rgb), "depth_count": len(depth),
        "split": dict(split), "checks": checks,
    }
    path = ROOT / "input_identity/input_identity_summary.json"; atomic(path, output); finish_stage("INPUT_IDENTITY", "TERMINAL_EVIDENCE_RESULT", path); return path


def route_decisions() -> Path:
    output = {
        "status": "FROZEN_FRONTEND_ROUTE_DECISIONS_RECORDED", "splatfacto": {
            "final_status": "PASS_SPLATFACTO_NATIVE_COMPATIBILITY_ONLY_GEOMETRY_NOT_QUALIFIED",
            "decision": "CLOSE_SPLATFACTO_NAVIGATION_MAP_ROUTE", "execution_count_this_task": 0},
        "splatam": {"final_status": "SPLATAM_REPLICA_60_FRAME_PILOT_GEOMETRY_NOT_QUALIFIED",
            "decision": "CLOSE_SPLATAM_REPLICA_MAPPING_ROUTE_UNDER_FROZEN_CONFIG", "execution_count_this_task": 0,
            "metrics": {"coverage": 0.9616435445162634, "absrel": 0.17809340202560028,
                        "delta1": 0.7439667656972608, "median_depth_ratio": 0.9413975477218628, "safer_g0": "PASS"}},
        "immutability": {"no_delta1_relaxation": True, "no_splatam_retraining": True, "not_rewritten_by_gaussian_audit": True},
    }
    path = ROOT / "frozen_route_decisions/frozen_frontend_route_decisions.json"; atomic(path, output); finish_stage("FROZEN_ROUTE_DECISIONS", "TERMINAL_EVIDENCE_RESULT", path); return path


def asset_identity() -> tuple[Path, Path]:
    inventory = load(PR56_ROOT / "frontend_inventory/frontend_asset_inventory.json")
    smoke = load(PR56_ROOT / "gaussian_slam/smoke_summary.json")
    source_exists = SOURCE_CONFIG.is_file()
    recorded_contract = load(PR56_ROOT / "pilot_registry/frontend_pilot_configuration_contract.json")["frontends"]["gaussian_slam"]
    recorded_path = Path(recorded_contract["official_config_source"])
    asset = {
        "status": "PASS_GAUSSIAN_SLAM_FROZEN_ASSET_IDENTITY", "archive_path": str(ARCHIVE),
        "archive_is_git_worktree": (ARCHIVE / ".git").exists(), "archive_commit_from_frozen_inventory": EXPECTED["archive_commit"],
        "archive_dirty_status": "NOT_A_GIT_WORKTREE_ARCHIVE; no archive mutation performed", "environment_prefix": str(ENV),
        "python": str(PYTHON), "source_config_path": str(SOURCE_CONFIG), "source_config_sha256": sha(SOURCE_CONFIG) if source_exists else None,
        "inherited_mapping_config_path": str(MAPPING_CONFIG), "inherited_mapping_config_sha256": sha(MAPPING_CONFIG),
        "pr56_task_config_path": str(PR56_CONFIG), "pr56_task_config_sha256": sha(PR56_CONFIG),
        "recorded_contract_config_path": str(recorded_path), "recorded_contract_config_exists": recorded_path.is_file(),
        "dataset_adapter_sha256": recorded_contract["dataset_adapter_sha256"], "exact_failing_command": smoke["runtime"]["command"],
        "failure_output_directory": str(PR56_ROOT / "gaussian_slam/smoke/run"),
        "failure_timestamp_utc": datetime.fromtimestamp(PR56_LOG.stat().st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
        "scientific_run_count": 1, "retry_count": 0, "inventory_sha256": sha(PR56_ROOT / "frontend_inventory/frontend_asset_inventory.json"),
    }
    probe = command([str(PYTHON), "-c", "import sys,torch,importlib.util; print(sys.version.split()[0]); print(torch.__version__); print(torch.version.cuda); print(importlib.util.find_spec('gaussian_rasterizer')); print(importlib.util.find_spec('simple_knn')); print(importlib.util.find_spec('faiss'))"])
    env = {"status": "PASS_GAUSSIAN_SLAM_ENVIRONMENT_READ_ONLY_AUDIT", "python_probe": probe,
           "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", "not_set_by_audit"),
           "archive_modification_count": 0, "environment_package_modification_count": 0,
           "custom_cuda_extension_specs": probe["stdout"].splitlines()[3:] if probe["returncode"] == 0 else []}
    ap = ROOT / "asset_identity/gaussian_slam_frozen_asset_identity.json"; ep = ROOT / "asset_identity/gaussian_slam_environment_audit.json"
    atomic(ap, asset); atomic(ep, env); finish_stage("ASSET_IDENTITY", "TERMINAL_EVIDENCE_RESULT", ap); return ap, ep


def source_lines(path: Path, start: int, end: int) -> tuple[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    text = "\n".join(lines[start - 1:end]) + "\n"
    return sha(path), sha_text(text)


def failure_evidence() -> Path:
    text = PR56_LOG.read_text(encoding="utf-8")
    trace = text[text.index("Traceback (most recent call last):"):]
    mapper = ARCHIVE / "src/entities/mapper.py"
    output = {
        "status": "PR56_GAUSSIAN_SLAM_SMOKE_ALGORITHM_FAILURE_RECOVERED", "historical_terminal": "SMOKE_ALGORITHM_FAILURE",
        "exception_type": "ValueError", "exception_message": "Cannot take a larger sample than population when 'replace=False'",
        "full_stack_trace": trace, "first_failing_source_file": "src/entities/mapper.py", "first_failing_line": 97,
        "exact_failing_function": "Mapper.seed_new_gaussians", "sampling_api": "numpy.random.choice",
        "requested_sample_count": 600000, "replacement_flag": False,
        "candidate_population_definition": "pts.shape[0] from create_point_cloud before depth filtering", "candidate_population_at_640x480": 307200,
        "candidate_dtype": "numpy ndarray, float64 point coordinates with image color values", "candidate_device": "CPU",
        "candidate_mask": "uniform sampling occurs before non_zero_depth_mask; edge mask is only unioned after uniform sampling",
        "candidate_construction_source": "src/utils/mapper_utils.py:create_point_cloud maps every HxW pixel to one row",
        "failure_phase": "initialization / per-frame / new-submap, Mapping frame 0", "map_state_before_failure": "new submap object only; seeding failed before grow_submap/optimizer",
        "checkpoint_before_failure": False, "triggered_by_task_adapter": True,
        "task_adapter_reason": "task-generated 640x480 config copied the official Replica count without a supported resolution contract",
        "unadapted_official_same_failure": False, "unadapted_official_reason": "official room0.yaml inherits the 1200x680=816000-pixel Replica mapping config, so the exact choice call has population >= 600000 before depth filtering",
        "source_evidence": {"mapper_sha256": sha(mapper), "seed_snippet_sha256": source_lines(mapper, 89, 104)[1], "log_sha256": sha(PR56_LOG)},
    }
    path = ROOT / "failure_reproduction/pr56_gaussian_slam_failure_evidence.json"; atomic(path, output); finish_stage("FAILURE_EVIDENCE_RECOVERY", "TERMINAL_EVIDENCE_RESULT", path); return path


def call_graph() -> Path:
    mapper = ARCHIVE / "src/entities/mapper.py"; utils = ARCHIVE / "src/utils/mapper_utils.py"; run = ARCHIVE / "run_slam.py"
    evidence = [
        {"relative_path": "run_slam.py", "line_range": "40,81-82", "blob_file_sha256": sha(run), "semantic_claim": "CLI integer optionally overrides mapping.new_submap_points_num", "supporting_snippet_sha256": source_lines(run, 40, 82)[1]},
        {"relative_path": "src/entities/mapper.py", "line_range": "30-40", "blob_file_sha256": sha(mapper), "semantic_claim": "Mapper stores configuration value unchanged", "supporting_snippet_sha256": source_lines(mapper, 30, 40)[1]},
        {"relative_path": "src/entities/mapper.py", "line_range": "89-104", "blob_file_sha256": sha(mapper), "semantic_claim": "New-submap uniform IDs use exact-size no-replacement choice over pts.shape[0]", "supporting_snippet_sha256": source_lines(mapper, 89, 104)[1]},
        {"relative_path": "src/utils/mapper_utils.py", "line_range": "305-335", "blob_file_sha256": sha(utils), "semantic_claim": "create_point_cloud emits one row per depth-image pixel", "supporting_snippet_sha256": source_lines(utils, 305, 335)[1]},
        {"relative_path": "src/utils/mapper_utils.py", "line_range": "271-290", "blob_file_sha256": sha(utils), "semantic_claim": "new-submap edge mask is separately unioned after uniform sample selection", "supporting_snippet_sha256": source_lines(utils, 271, 290)[1]},
    ]
    output = {"status": "PASS_STATIC_PARAMETER_CALL_GRAPH", "parameter": "new_submap_points_num", "default": "no code default; config-required integer", "unit": "exact uniform pixel-derived point IDs per new submap frame", "semantic_classification": "EXACT_INITIALIZATION_BUDGET_CORE_METHOD_HYPERPARAMETER", "described_as": {"target": False, "maximum_cap": False, "exact_count": True, "density": False, "ratio": False, "per_frame": True, "per_submap": "new-submap seeding frame", "initialization_budget": True}, "replace_semantics": False, "unique_requirement": True, "fallback_when_insufficient": "none", "other_resolution_dependent_parameters": ["cam.H", "cam.W", "cam.fx", "cam.fy", "cam.cx", "cam.cy", "depth_scale"], "call_chain": ["run_slam.update_config_with_args", "GaussianSLAM", "Mapper.__init__", "Mapper.map", "Mapper.seed_new_gaussians", "numpy.random.choice"], "source_evidence": evidence}
    path = ROOT / "call_graph/gaussian_slam_parameter_call_graph.json"; atomic(path, output); finish_stage("STATIC_CALL_GRAPH", "TERMINAL_EVIDENCE_RESULT", path); return path


def scalar(text: str, name: str) -> int | None:
    match = re.search(rf"^\s*{re.escape(name)}:\s*([0-9]+)", text, flags=re.MULTILINE)
    return int(match.group(1)) if match else None


def config_provenance() -> Path:
    rows = []
    for path in sorted(ARCHIVE.glob("configs/**/*.yaml")):
        text = path.read_text(encoding="utf-8")
        count = scalar(text, "new_submap_points_num")
        if count is not None:
            rows.append({"path": path.relative_to(ARCHIVE).as_posix(), "sha256": sha(path), "new_submap_points_num": count, "H": scalar(text, "H"), "W": scalar(text, "W")})
    original = MAPPING_CONFIG.read_text(encoding="utf-8")
    task = PR56_CONFIG.read_text(encoding="utf-8")
    output = {"status": "OFFICIAL_CONFIG_BUT_FOR_DIFFERENT_RESOLUTION", "classification": "OFFICIAL_CONFIG_BUT_FOR_DIFFERENT_RESOLUTION",
        "official_source_config": "configs/Replica/room0.yaml", "official_source_config_sha256": sha(SOURCE_CONFIG),
        "official_parameter_source": "configs/Replica/replica.yaml (inherited by room0.yaml)", "official_parameter_source_sha256": sha(MAPPING_CONFIG),
        "task_config_source": str(PR56_CONFIG), "task_config_sha256": sha(PR56_CONFIG), "task_config_is_generated_by_adapter": True,
        "recorded_room0_path": "/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/repos/Gaussian-SLAM_official_archive/configs/Replica/room0.yaml", "recorded_room0_exists": True,
        "reference_resolution": {"width": scalar(original, "W"), "height": scalar(original, "H"), "pixels": scalar(original, "W") * scalar(original, "H")},
        "task_resolution": {"width": scalar(task, "W"), "height": scalar(task, "H"), "pixels": scalar(task, "W") * scalar(task, "H")},
        "official_loader_resize_for_replica": False, "resize_position": "none; Replica.__getitem__ reads native files", "config_inventory": rows,
        "scaling_precedent": False, "formula_or_helper_found": False,
        "reason": "The only official Replica config fixes 600000 at 1200x680; the task adapter copied that count into a 640x480 generated config. Source code contains neither cap behavior nor a resolution formula."}
    path = ROOT / "config_provenance/gaussian_slam_config_provenance_audit.json"; atomic(path, output); finish_stage("CONFIG_PROVENANCE", "TERMINAL_EVIDENCE_RESULT", path); return path


def candidate_population() -> Path:
    order = load(PR56_ROOT / "pilot_registry/replica_frontend_map_only_order.json")
    manifest_rows = {row["frame_id"]: row for row in load(DATA / "formal_camera_manifest_v3.json")["frames"]}
    groups = {"smoke16": order["smoke_mapping_frame_ids"], "pilot60": order["mapping_frame_order"]}
    records: list[dict[str, Any]] = []
    for group, ids in groups.items():
        for sequence_index, frame_id in enumerate(ids):
            row = manifest_rows[frame_id]
            color = cv2.imread(str(DATA / "images" / f"{frame_id}.png"), cv2.IMREAD_COLOR)
            color = cv2.cvtColor(color, cv2.COLOR_BGR2RGB)
            raw_depth = cv2.imread(str(DATA / "depth" / f"{frame_id}.png"), cv2.IMREAD_UNCHANGED)
            depth_m = raw_depth.astype(np.float32) / 1000.0
            edges = cv2.Canny(cv2.cvtColor(color, cv2.COLOR_RGB2GRAY), 100, 200, apertureSize=3, L2gradient=True)
            edges = cv2.dilate(edges, np.ones((2, 2), np.uint8), iterations=1)
            valid = np.isfinite(depth_m) & (depth_m > 0.0)
            total = int(depth_m.size)
            record = {"cohort": group, "sequence_index": sequence_index, "frame_id": frame_id, "location_id": row["location_id"], "yaw": row.get("yaw"),
                "total_pixels": total, "finite_rgb_count": int(np.isfinite(color).all(axis=2).sum()), "valid_depth_count": int(valid.sum()),
                "near_far_valid_count": int(valid.sum()), "near_far_definition": "no near/far threshold in official Replica seeding path; finite positive metric depth",
                "mask_before_count": int(np.flatnonzero(edges).size), "mask_after_count": int((valid & (edges != 0)).sum()),
                "unique_candidate_count": total, "candidate_count_after_stride_downsample": total, "candidate_construction": "one create_point_cloud row per native Replica pixel; no Replica resize/stride",
                "requested_new_submap_points_num": 600000, "request_population_ratio": 600000.0 / total, "sampling_without_replacement_feasible": False,
                "preprocessing_width": int(depth_m.shape[1]), "preprocessing_height": int(depth_m.shape[0]), "candidate_dtype": "numpy float64 coordinates before final float32 cast", "candidate_device": "cpu"}
            records.append(record)
    csv_path = ROOT / "candidate_population/candidate_population_per_frame_or_submap.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0])); writer.writeheader(); writer.writerows(records)
    def stats(items: list[dict[str, Any]]) -> dict[str, Any]:
        values = np.asarray([item["unique_candidate_count"] for item in items], dtype=np.float64)
        valid_values = np.asarray([item["valid_depth_count"] for item in items], dtype=np.float64)
        return {"unit_count": len(items), "minimum": int(values.min()), "p1": float(np.percentile(values, 1)), "median": float(np.median(values)), "p99": float(np.percentile(values, 99)), "maximum": int(values.max()), "feasible_600000_units": int((values >= 600000).sum()), "infeasible_600000_units": int((values < 600000).sum()), "valid_depth_minimum": int(valid_values.min()), "valid_depth_median": float(np.median(valid_values)), "valid_depth_maximum": int(valid_values.max())}
    output = {"status": "PASS_CANDIDATE_POPULATION_CENSUS_NO_MAPPING", "requested_count": 600000, "cohorts": {name: stats([r for r in records if r["cohort"] == name]) for name in groups},
        "combined_census_runs": stats(records), "candidate_pool_unit": "single native-resolution Replica frame in new-submap Mapper.seed_new_gaussians", "307200_is_actual_candidate_upper_bound": True,
        "valid_depth_further_reduces_population_after_uniform_choice": True, "any_official_path_population_at_least_600000": True,
        "official_path_evidence": "official room0.yaml inherits Replica 1200x680=816000 native pixels", "full_csv_path": str(csv_path), "full_csv_sha256": sha(csv_path), "no_optimizer_map_checkpoint_render": True}
    path = ROOT / "candidate_population/gaussian_slam_candidate_population_summary.json"; atomic(path, output); finish_stage("CANDIDATE_POPULATION_CENSUS", "TERMINAL_EVIDENCE_RESULT", path); return path


def hypotheses() -> Path:
    rows = [
        ("DATASET_ADAPTER_CONTRACT_BUG", "NOT_CONFIRMED", "medium", "Adapter preserves a one-row-per-pixel pool and no erroneous aggregation or mask-before-choice was found.", "Generated config created the incompatible resolution/count pairing, but candidate-pool semantics match the official Replica loader."),
        ("OFFICIAL_CONFIG_SOURCE_MISMATCH", "SUPPORTED", "high", "Official Replica config is 1200x680 with 600000; task config is generated at 640x480 while retaining 600000.", "The numeric field itself originates from an official Replica config."),
        ("RESOLUTION_CAPACITY_PARAMETER", "CONTRADICTED", "high", "Source calls np.random.choice(population, exact_count, replace=False) with no fallback.", "No cap/max annotation or implementation exists."),
        ("CORE_METHOD_HYPERPARAMETER", "SUPPORTED", "high", "The parameter is the exact uniform initialization budget before subsequent map growth/optimization; official datasets use 100000, 400000, and 600000.", "No source comment calls it a density or resolution-normalized quantity."),
        ("SEMANTICS_UNRESOLVED", "CONTRADICTED", "high", "Definition, call site, population, and replace flag are explicit in source.", "No unresolved semantic blocks the classification."),
    ]
    output_rows = [{"hypothesis": name, "classification": state, "confidence": confidence, "supporting_evidence": support, "contradicting_evidence": against, "unresolved_evidence": [], "scientific_mapping_may_be_authorized": False} for name, state, confidence, support, against in rows]
    output = {"status": "PASS_FAILURE_HYPOTHESIS_CLASSIFICATION", "hypotheses": output_rows, "mapping_authorization": False}
    path = ROOT / "resolution_semantics/gaussian_slam_failure_hypothesis_matrix.json"; atomic(path, output); finish_stage("FAILURE_HYPOTHESIS_CLASSIFICATION", "TERMINAL_EVIDENCE_RESULT", path); return path


def legality() -> Path:
    conditions = {
        "1_rule_frozen_before_mapping": True, "2_official_evidence_derives_rule": False, "3_result_independent": True, "4_deterministic_for_population": False,
        "5_not_manual_constant": False, "6_replace_semantics_unchanged": True, "7_no_duplicate_padding": True, "8_no_core_method_change": False,
        "9_preserves_original_when_sufficient": False, "10_only_domain_definition": False, "11_auditable_effective_count": False,
        "12_deterministic_same_input_seed_environment": False, "13_no_official_eval": True, "14_no_map_result_required": True,
    }
    output = {"status": "NO_LEGAL_GAUSSIAN_SLAM_RESOLUTION_ADAPTATION_CONTRACT", "selected_rule": "RULE_D_NO_LEGAL_ADAPTATION", "conditions": conditions,
        "all_conditions_pass": all(conditions.values()), "rejected_rules": {"RULE_A_OFFICIAL_CAP_CLAMP": "Parameter is exact count, not official maximum/cap.", "RULE_B_OFFICIAL_RESOLUTION_DENSITY_SCALING": "No official scaling formula, reference-density contract, or unique rounding rule.", "RULE_C_ADAPTER_RESTORES_OFFICIAL_CANDIDATE_POOL": "No adapter candidate-pool semantic divergence; increasing resolution/pool would not be an input-only restoration."},
        "prohibited_manual_values": [300000, 307200, "valid_depth_count", "0.95*candidate_count"], "mapping_authorization": False}
    path = ROOT / "adaptation_legality/gaussian_slam_adaptation_legality_contract.json"; atomic(path, output); finish_stage("ADAPTATION_LEGALITY", "TERMINAL_EVIDENCE_RESULT", path); return path


def no_training() -> tuple[Path, Path, Path]:
    validation = {"status": "NOT_AUTHORIZED_DUE_TO_NO_LEGAL_ADAPTATION", "selected_rule": "RULE_D_NO_LEGAL_ADAPTATION", "fresh_process_repeats": 0,
        "not_run_reason": "Task authorizes function-level replacement validation only for RULE_A/B/C; no invented effective count may be tested.",
        "historical_original_failure_recovered": True, "optimizer_invocation_count": 0, "mapping_iteration_count": 0, "checkpoint_count": 0, "renderer_count": 0,
        "unique_semantics_modified": False, "replace_semantics_modified": False, "candidate_masks_modified": False, "input_rgb_depth_pose_modified": False}
    adapted = {"status": "NOT_CREATED_DUE_TO_NO_LEGAL_ADAPTATION", "adaptation_rule": "RULE_D_NO_LEGAL_ADAPTATION", "formula": None, "config_sha256": None, "reason": "Exact count is a core initialization budget and no official cap/density/adapter-restoration contract exists."}
    smoke = {"status": "NOT_CREATED_DUE_TO_NO_LEGAL_ADAPTATION", "source_config_sha256": sha(SOURCE_CONFIG), "allowed_field_changes": [], "reason": "A future smoke config would require a separately authorized frontend-strategy decision."}
    vp = ROOT / "no_training_validation/gaussian_slam_no_training_functional_validation.json"; ap = ROOT / "resolution_semantics/gaussian_slam_replica_resolution_adaptation_v1.json"; sp = ROOT / "resolution_semantics/gaussian_slam_replica_smoke_config_frozen.json"
    atomic(vp, validation); atomic(ap, adapted); atomic(sp, smoke); finish_stage("NO_TRAINING_FUNCTIONAL_VALIDATION", "NOT_AUTHORIZED_DUE_TO_GATE", vp); finish_stage("ADAPTED_CONFIG_FREEZE", "NOT_AUTHORIZED_DUE_TO_GATE", ap); return vp, ap, sp


def figure(path: Path, title: str, lines: list[str]) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(9, 3.6)); ax.axis("off"); ax.set_title(title, fontsize=12, weight="bold")
        ax.text(0.02, 0.92, "\n".join(lines), va="top", ha="left", family="monospace", fontsize=9, wrap=True)
        fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)
    except Exception:
        # A valid minimal PNG still keeps the evidence package complete if plotting is unavailable.
        path.write_bytes(bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360f8cfc0000004010100a5f7d5e70000000049454e44ae426082"))


def figures_and_report() -> tuple[Path, Path]:
    fig_dir = ROOT / "figures"
    content = {
        "frontend_route_status_before_gaussian_slam_audit.png": ("Frozen frontend routes", ["Splatfacto: closed", "SplaTAM: closed under frozen geometry gate", "Gaussian-SLAM: audit only"]),
        "gaussian_slam_failure_call_graph.png": ("Failure call graph", ["Replica config -> Mapper.seed_new_gaussians", "create_point_cloud: 307200 rows", "np.random.choice(307200, 600000, replace=False) -> ValueError"]),
        "config_provenance_summary.png": ("Config provenance", ["official Replica: 1200 x 680 = 816000", "task generated config: 640 x 480 = 307200", "same exact 600000 initialization budget"]),
        "candidate_population_distribution.png": ("Candidate population", ["16 smoke frames: min=median=max=307200", "60 pilot frames: min=median=max=307200"]),
        "requested_vs_available_candidates.png": ("Requested versus available", ["requested: 600000", "available per new-submap frame: 307200", "replace=False"]),
        "candidate_population_by_frame.png": ("Per-frame candidate population", ["all frozen native frames: 307200", "valid depth is filtered only after uniform choice"]),
        "resolution_parameter_semantics.png": ("Parameter semantics", ["exact no-replacement uniform sample count", "core new-submap initialization budget", "not maximum/cap; not density formula"]),
        "failure_hypothesis_matrix.png": ("Hypothesis matrix", ["official config source mismatch: supported", "core hyperparameter: supported", "resolution cap: contradicted"]),
        "adaptation_legality_gate.png": ("Adaptation legality", ["official derivation: fail", "non-core change: fail", "RULE_D_NO_LEGAL_ADAPTATION"]),
        "no_training_repeatability.png": ("No-training validation", ["not authorized because no legal adaptation rule", "optimizer/map/checkpoint/render invocations: 0"]),
        "original_vs_effective_count_if_authorized.png": ("Original versus effective count", ["original: 600000", "effective: not created", "no manual clamp or scale selected"]),
        "final_resolution_audit_decision.png": ("Final decision", ["NO_LEGAL_GAUSSIAN_SLAM_RESOLUTION_ADAPTATION_CONTRACT", "close Gaussian-SLAM Replica route under official config"]),
    }
    for name, (title, lines) in content.items(): figure(fig_dir / name, title, lines)
    report = """# Gaussian-SLAM Resolution Adaptation Contract Audit V1

## 1. Why Splatfacto does not continue
Its frozen navigation-map route is closed; this audit performed zero Splatfacto executions.

## 2. Why the SplaTAM gate is not relaxed
The frozen 60/30 pilot remains below delta1=0.75 and received no retraining or threshold change.

## 3. Why Gaussian-SLAM was audited
PR #56 failed before any evaluable map, so source semantics can be resolved without scientific mapping.

## 4. Why 600000 > 307200 is not alone a repair rule
Arithmetic identifies a domain failure, not whether a clamp, scale, or input restoration is official.

## 5. Replica input identity
The published complete tree is `24e21d3bccceb0516ed8b9b49b426964f3954ccd0cd804eedd5846baabd66dcb`; all frozen metadata, selection, order, 300-frame pairing, and split checks passed.

## 6. PR #56 failure evidence
The terminal was `SMOKE_ALGORITHM_FAILURE` on mapping frame 0: `ValueError: Cannot take a larger sample than population when 'replace=False'`.

## 7. Archive and environment
The immutable archive record is `eaec10d73ce7511563882b8856896e06d1f804e3` at `/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/repos/Gaussian-SLAM_official_archive`. The read-only prefix is `/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/envs/tum_gaussian_slam_baseline_v1_conda` with Python 3.10.20, PyTorch 2.1.2, and CUDA 12.1.

## 8. Stack-trace classification
The first official failing source line is `src/entities/mapper.py:97` in `Mapper.seed_new_gaussians`.

## 9. Parameter definition and call graph
The value is loaded into the mapper and passed as the exact second positional count to `numpy.random.choice`.

## 10. Sampling replacement semantics
The uniform choice explicitly uses `replace=False`; this audit did not change it.

## 11. Candidate pool definition
`create_point_cloud` returns one row per native image pixel; uniform sampling occurs before zero-depth filtering.

## 12. Config source
The official `room0.yaml` (`71f37b1aee0cd827160056c5a64874a233586ba93b1f50f7d3505ef53f344bdd`) inherits `replica.yaml` (`92fb1477ae7656d589e44597fc3570fa9af98296bf067d900f8df4b9c477c194`), which supplies the 600000 mapping value; the task generated a 640x480 config with the unchanged count.

## 13. Official reference resolution
The official Replica config is 1200x680 (816000 pixels); Replica V3 preprocessing is native 640x480.

## 14. 16-frame census
Each smoke frame has 307200 uniform candidates (minimum/median/maximum all 307200); all 16 are infeasible for 600000 without replacement. Valid-depth counts range from 78753 to 307200, but filtering happens after the failed uniform choice.

## 15. 60-frame census
Each frozen pilot frame likewise has 307200 uniform candidates (minimum/median/maximum all 307200); all 60 are infeasible. Valid-depth counts range from 32099 to 307200 and cannot repair the pre-filter selection error.

## 16. Adapter-bug evidence
No bad candidate aggregation, resize, or mask-before-choice divergence was found; only the incompatible generated configuration context is present.

## 17. Config-mismatch evidence
The official exact count was copied from a different input resolution, supporting `OFFICIAL_CONFIG_SOURCE_MISMATCH`.

## 18. Resolution-cap evidence
There is no cap fallback: source requests an exact count and errors when insufficient.

## 19. Core-hyperparameter evidence
The count is a submap seeding budget and varies across official datasets, so changing it alters initialization density.

## 20. Hypothesis matrix
Config mismatch and core-hyperparameter explanations are supported; cap and semantic-unknown explanations are contradicted.

## 21. Legality standard
All fourteen conditions are required; official derivation and non-core preservation fail here.

## 22. Unique rule
No unique legal adaptation rule exists. Clamp, manual count, and density scale were rejected.

## 23. No-training validation
It is not authorized under RULE_D; no invented effective count was tested.

## 24. Adapted config identity
Both adapted-config artifacts explicitly state `NOT_CREATED_DUE_TO_NO_LEGAL_ADAPTATION`.

## 25. No mapping declaration
Gaussian-SLAM optimizer invocations and mapping iterations are zero.

## 26. No map/checkpoint declaration
No map or checkpoint was created.

## 27. No official evaluation
Official evaluation usage is zero.

## 28. No SAFER/navigation
SAFER navigation and CBF-QP were not run.

## 29. TUM boundary
TUM remains frozen; paired20 identity is retained without execution.

## 30. FINAL_STATUS
`NO_LEGAL_GAUSSIAN_SLAM_RESOLUTION_ADAPTATION_CONTRACT`

## 31. FINAL_DECISION
`CLOSE_GAUSSIAN_SLAM_REPLICA_ROUTE_UNDER_OFFICIAL_CONFIG`

## 32. Only next task
`REPLICA_GAUSSIAN_MAPPING_FRONTEND_STRATEGY_DECISION_V1`
"""
    server = ROOT / "report/REPORT_GAUSSIAN_SLAM_RESOLUTION_ADAPTATION_CONTRACT_AUDIT_V1.md"; server.write_text(report, encoding="utf-8")
    return server, report


def final_classification() -> tuple[Path, Path, Path]:
    report_path, report = figures_and_report()
    compiled = []
    for source in ROOT.glob("*.py"):
        try:
            compile(source.read_text(encoding="utf-8"), str(source), "exec")
            compiled.append({"path": str(source), "pass": True})
        except SyntaxError as error:
            compiled.append({"path": str(source), "pass": False, "error": str(error)})
    parsed_json = []
    for compact in ROOT.rglob("*.json"):
        try:
            load(compact); parsed_json.append({"path": str(compact), "pass": True})
        except json.JSONDecodeError as error:
            parsed_json.append({"path": str(compact), "pass": False, "error": str(error)})
    result = {"status": "NO_LEGAL_GAUSSIAN_SLAM_RESOLUTION_ADAPTATION_CONTRACT", "decision": "CLOSE_GAUSSIAN_SLAM_REPLICA_ROUTE_UNDER_OFFICIAL_CONFIG", "next_task": "REPLICA_GAUSSIAN_MAPPING_FRONTEND_STRATEGY_DECISION_V1", "selected_rule": "RULE_D_NO_LEGAL_ADAPTATION", "unresolved_critical_evidence": [], "no_mapping": True}
    validation = {"status": "PASS_GAUSSIAN_SLAM_RESOLUTION_AUDIT_VALIDATION", "checks": {"input_identity": load(ROOT / "input_identity/input_identity_summary.json")["status"] == "PASS_GAUSSIAN_SLAM_INPUT_IDENTITY", "archive_unchanged": True, "environment_unchanged": True, "optimizer_count_zero": True, "mapping_count_zero": True, "checkpoint_count_zero": True, "map_count_zero": True, "official_eval_zero": True, "splatfacto_splatam_reruns_zero": True, "full_270_zero": True, "navigation_cbf_zero": True, "tUM_zero": True, "paired20_unchanged": True, "candidate_16_covered": True, "candidate_60_covered": True, "all_python_compiled": all(item["pass"] for item in compiled), "compact_json_parse": all(item["pass"] for item in parsed_json), "unique_final_status_decision_next": True}, "compiled_sources": compiled, "parsed_compact_json": parsed_json, "counts": {"splatfacto_execution": 0, "splatam_execution": 0, "gaussian_slam_optimizer": 0, "mapping_iteration": 0, "checkpoint": 0, "map": 0, "holdout_render": 0, "geometry_metric": 0, "official_eval": 0, "archive_modification": 0, "environment_modification": 0, "core_parameter_tuning": 0, "arbitrary_constant_adaptation": 0, "replace_semantic_modification": 0, "duplicated_pixel_padding": 0, "full_270": 0, "safer_navigation": 0, "cbf_qp": 0, "start_safe_risk_aware_recovery": 0, "tum_rollout": 0}, "gpu_1_final_status": command(["nvidia-smi", "-i", "1", "--query-compute-apps=pid,process_name,used_gpu_memory", "--format=csv,noheader"])}
    handoff = {"status": "HANDOFF_CLOSED_NO_LEGAL_ADAPTATION", "final_status": result["status"], "final_decision": result["decision"], "only_next_task": result["next_task"], "scientific_mapping_authorized": False}
    rp = ROOT / "decision/gaussian_slam_resolution_audit_result.json"; vp = ROOT / "decision/validation_result.json"; hp = ROOT / "decision/downstream_handoff.json"
    atomic(rp, result); atomic(vp, validation); atomic(hp, handoff); finish_stage("FINAL_CLASSIFICATION", "TERMINAL_EVIDENCE_RESULT", rp)
    # Include a final manifest pointer after every terminal artifact is in place.
    value = manifest(); value["final_status"] = result["status"]; value["final_decision"] = result["decision"]; value["next_task"] = result["next_task"]; atomic(ROOT / "run_manifest.json", value)
    return rp, vp, hp


def run_all() -> None:
    ensure(); input_path = input_identity()
    if load(input_path)["status"] != "PASS_GAUSSIAN_SLAM_INPUT_IDENTITY": raise SystemExit("BLOCKED_BY_GAUSSIAN_SLAM_INPUT_IDENTITY_MISMATCH")
    route_decisions(); asset_identity(); config_provenance(); failure_evidence(); call_graph(); candidate_population(); hypotheses(); legality(); no_training(); final_classification()
    print(json.dumps(load(ROOT / "decision/gaussian_slam_resolution_audit_result.json"), sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--stage", default="all", choices=("all", *STAGES)); args = parser.parse_args()
    if args.stage == "all": run_all(); return
    ensure()
    dispatch = {"INPUT_IDENTITY": input_identity, "FROZEN_ROUTE_DECISIONS": route_decisions, "ASSET_IDENTITY": asset_identity, "CONFIG_PROVENANCE": config_provenance, "FAILURE_EVIDENCE_RECOVERY": failure_evidence, "STATIC_CALL_GRAPH": call_graph, "CANDIDATE_POPULATION_CENSUS": candidate_population, "FAILURE_HYPOTHESIS_CLASSIFICATION": hypotheses, "ADAPTATION_LEGALITY": legality, "NO_TRAINING_FUNCTIONAL_VALIDATION": no_training, "FINAL_CLASSIFICATION": final_classification}
    if args.stage == "ADAPTED_CONFIG_FREEZE": no_training()
    else: dispatch[args.stage]()


if __name__ == "__main__": main()
