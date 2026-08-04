#!/usr/bin/env python3
"""Frozen identities, paths, and deterministic I/O for the ETH3D benchmark."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

TASK_NAME = "TRAIN_ONE_ETH3D_3DGS_MAP_AND_RUN_FAS_CBF_MODULE_STRESS_BENCHMARK_V1"
BRANCH = "eth3d-single-map-fas-cbf-module-stress-benchmark-v1"
BASE_BRANCH = "eth3d-delivery-area-provision-7zz-resume-assets-v1"
BASE_HEAD = "4694a7cbfa062a53ac270c1c1c5654a2d1b5f166"
OFFICIAL_3DGS_COMMIT = "54c035f7834b564019656c3e3fcc3646292f727d"
PROTOCOL_V2_SHA256 = "a0a02fd284c75c600095510899e2878f198d69ff088b66eccd3313275fdbde7e"
SPLIT_SHA256 = "dc6729a60e0f2971cb671e30bcce3a04adcd8f99298395d42f21855d666cc435"
TRAIN_TREE_SHA256 = "5b0002cbdd4dff8985574c8f5d61640e9535709634959327e3b705794830b478"
REFERENCE_SHA256 = "82a9b20c9f3c7dc933f86c45e0855adf649fcf08b7549baba760cf385d489370"
PR79_REPORT_SHA256 = "6b827cc4eae4153dcd0458bf93dbc1405670e5a0a9920e82d407a596240a20ec"
PR79_ARTIFACT_MANIFEST_SHA256 = "8eecf5caad7966b9f27664557abb77b6c31b4b265c46ed799f2d9521f683abd5"
PR79_RUN_MANIFEST_SHA256 = "574c456ed9a60b11096a6b76e16a219b699ae8c686c41a24cd6488bfd74cff31"

TASK_ROOT = Path("/disk1/zlab/maintenance_records/eth3d_single_map_fas_cbf_module_stress_benchmark_v1")
MAP_ROOT = Path("/disk1/zlab/cross_dataset_maps/eth3d_delivery_area_official_3dgs_v1")
SOURCE_ROOT = Path("/disk1/zlab/source_snapshots/official_gaussian_splatting_54c035f")
ENV_ROOT = Path("/disk1/zlab/conda_envs/eth3d_official_3dgs_v1")
DATA_ROOT = Path("/disk1/zlab/cross_dataset_assets/eth3d_delivery_area_protocol_v2_v1")
TRAIN_ROOT = DATA_ROOT / "TRAIN_INPUT_ROOT"
EVAL_ROOT = DATA_ROOT / "EVAL_ORACLE_ROOT"
CONTRACTS = DATA_ROOT / "CONTRACTS"
LICENSES = DATA_ROOT / "LICENSES"
PR79_SERVER_ROOT = Path("/disk1/zlab/maintenance_records/eth3d_delivery_area_provision_7zz_resume_assets_v1")
PROXY_WRAPPER = Path.home() / ".config/scannetpp_proxy/run_with_scannetpp_proxy.sh"

SEED = 20260804
SMOKE_ITERATIONS = 500
FORMAL_ITERATIONS = 30000
CHECKPOINT_ITERATIONS = (7000, 15000, 30000)
PHYSICAL_GPU = 1
DISK_LIMIT_BYTES = 80_000_000_000
DT = 0.05
VMAX = 0.10
UMAX = 0.10
ROBOT_RADIUS = 0.10
EPSILON_BASE = 0.01
HORIZON = 3
MAX_STEPS = 500
SCENARIOS_PER_GROUP = 20
MIN_SCENARIOS_PER_GROUP = 10
MIN_TOTAL_SCENARIOS = 70
GROUPS = (
    "G0_SAFE_CONTROL",
    "G1_START_SAFE_BOUNDARY",
    "G2_FEASIBILITY_DENSE",
    "G3_SAMPLED_DATA_GAP",
    "G4_PREDICTIVE_RECOVERY",
)
METHODS = (
    "M0_SAFER_BASELINE",
    "M1_FAS_START_SAFE_ONLY",
    "M2_FAS_START_SAFE_PLUS_FEASIBILITY_AWARE",
    "M3_FAS_PLUS_DISCRETE_TIME_VERIFICATION",
    "M4_FULL_FAS_CBF",
)

TASK_SUBDIRS = (
    "input_freeze", "source", "environment", "input_adapter", "smoke",
    "formal_map", "canonical_export", "map_minimum_viability",
    "scenario_generation", "method_inventory", "unit_tests",
    "smoke_controller", "formal_controller", "paired_analysis", "figures",
    "report", "logs", "cache", "tmp",
)


def ensure_task_roots() -> None:
    TASK_ROOT.mkdir(parents=True, exist_ok=True)
    MAP_ROOT.mkdir(parents=True, exist_ok=True)
    for name in TASK_SUBDIRS:
        (TASK_ROOT / name).mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_identity(root: Path) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    files = sorted((path for path in root.rglob("*") if path.is_file()), key=lambda p: p.relative_to(root).as_posix())
    for path in files:
        rel = path.relative_to(root).as_posix()
        size = path.stat().st_size
        file_sha = sha256_file(path)
        mode = os.stat(path, follow_symlinks=False).st_mode & 0o777
        digest.update(rel.encode("utf-8") + b"\0" + str(size).encode() + b"\0" + file_sha.encode() + b"\0" + oct(mode).encode() + b"\n")
        rows.append({"path": rel, "size": size, "sha256": file_sha, "mode": oct(mode)})
    return {
        "tree_sha256": digest.hexdigest(),
        "file_count": len(rows),
        "total_bytes": sum(row["size"] for row in rows),
        "files": rows,
    }


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
