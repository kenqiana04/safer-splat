#!/usr/bin/env python3
"""Frozen paths, identities, methods, constants, and deterministic I/O for V2."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

TASK_NAME = "REFINE_FAS_CBF_STRESS_SCENARIO_ACTIVATION_ON_FROZEN_ETH3D_MAP_V1"
BRANCH = "eth3d-fas-cbf-stress-scenario-activation-v1"
BASE_BRANCH = "eth3d-single-map-fas-cbf-module-stress-benchmark-v1"
BASE_HEAD = "a05f8e1eca4c400a86583eb97fcce5be32062a0d"
SEED = 20260805
PHYSICAL_GPU = 1
TASK_ROOT = Path("/disk1/zlab/maintenance_records/eth3d_fas_cbf_stress_scenario_activation_v1")
PR80_ROOT = Path("/disk1/zlab/maintenance_records/eth3d_single_map_fas_cbf_module_stress_benchmark_v1")
PR79_ROOT = Path("/disk1/zlab/maintenance_records/eth3d_delivery_area_provision_7zz_resume_assets_v1")
MAP_ROOT = Path("/disk1/zlab/cross_dataset_maps/eth3d_delivery_area_official_3dgs_v1")
ENV_ROOT = Path("/disk1/zlab/conda_envs/eth3d_official_3dgs_v1")
DATA_ROOT = Path("/disk1/zlab/cross_dataset_assets/eth3d_delivery_area_protocol_v2_v1")
SOURCE_ROOT = Path("/disk1/zlab/source_snapshots/official_gaussian_splatting_54c035f")
CANONICAL_ROOT = PR80_ROOT / "canonical_export/fresh_1"
CONTROLLER_SNAPSHOT = PR80_ROOT / "controller_core_snapshot"
PRM_GRAPH = PR79_ROOT / "routes/reference_prm_graph_full.json"
REFERENCE_MESH = DATA_ROOT / "EVAL_ORACLE_ROOT/oracle_assets/delivery_area_rig_occlusion/delivery_area/occlusion/surface_mesh.ply"
V1_REGISTRY = PR80_ROOT / "scenario_generation/scenario_registry.json"
V1_RESULTS = PR80_ROOT / "formal_controller/results"
V1_REPORT = PR80_ROOT / "report/REPORT_TRAIN_ONE_ETH3D_3DGS_MAP_AND_RUN_FAS_CBF_MODULE_STRESS_BENCHMARK_V1.md"
MAP_PLY = MAP_ROOT / "point_cloud/iteration_30000/point_cloud.ply"
PROXY_WRAPPER = Path.home() / ".config/scannetpp_proxy/run_with_scannetpp_proxy.sh"

EXPECTED = {
    "pr80_report_sha256": "44035feae65f89ccf8b146fe29c26f81dd9388098e7d0bd66716d632e8422767",
    "v1_registry_logical_sha256": "9f9fce4d1875b57e7a55c3a9cbf5b5a0c3f8476d84b3deb53c920d9b6322bb1d",
    "official_3dgs_commit": "54c035f7834b564019656c3e3fcc3646292f727d",
    "map_ply_sha256": "927734a2339a3f2710640065b0893eaae162cc0144ac67e2f377bcff2e71ae34",
    "canonical_tree_sha256": "06c1ff17d2ed5eb184b6a9699a3a32da431a1460840431a3effe76d5f03b9ee3",
    "reference_mesh_sha256": "82a9b20c9f3c7dc933f86c45e0855adf649fcf08b7549baba760cf385d489370",
    "protocol_sha256": "a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e",
}
METHODS = (
    "M0_SAFER_BASELINE",
    "M1_FAS_START_SAFE_ONLY",
    "M2_FAS_START_SAFE_PLUS_FEASIBILITY_AWARE",
    "M3_FAS_PLUS_DISCRETE_TIME_VERIFICATION",
    "M4_FULL_FAS_CBF",
)
GROUPS = (
    "G0_SAFE_CONTROL_V2",
    "G1_START_SAFE_PROJECTABLE_V2",
    "G2_FEASIBILITY_DOMINANCE_V2",
    "G3_SAMPLED_DATA_TRIGGER_V2",
    "G4_PREDICTIVE_RECOVERY_TRIGGER_V2",
)
DT = 0.05
VMAX = 0.10
UMAX = 0.10
ROBOT_RADIUS = 0.10
EPSILON = 0.01
HORIZON = 3
CANDIDATE_BUDGET = 2000
MAX_STEPS = 200
UNKNOWN_CORRIDOR_M = 0.15
CANDIDATE_STATE_LIMIT = 200000
TASK_SUBDIRS = (
    "input_freeze", "v1_semantic_audit", "shadow_predicates", "candidate_pool",
    "stage_reachability", "scenario_registry_v2", "smoke", "formal",
    "paired_analysis", "failure_forensics", "figures", "report", "logs", "tmp",
)

def ensure_roots() -> None:
    TASK_ROOT.mkdir(parents=True, exist_ok=True)
    for name in TASK_SUBDIRS:
        (TASK_ROOT / name).mkdir(parents=True, exist_ok=True)

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")

def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()

def atomic_json(path: Path, value: Any) -> None:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=True)
            stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)

def append_autonomy(action: dict[str, Any]) -> None:
    path = TASK_ROOT / "operational_autonomy_actions.json"
    old = json.loads(path.read_text()) if path.exists() else {"actions": []}
    old["actions"].append(action); atomic_json(path, old)
