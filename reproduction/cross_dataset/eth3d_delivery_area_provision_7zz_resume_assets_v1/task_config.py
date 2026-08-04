#!/usr/bin/env python3
"""Frozen paths and identities for the ETH3D Delivery Area asset audit."""

from __future__ import annotations

from pathlib import Path

TASK_ROOT = Path("/disk1/zlab/maintenance_records/eth3d_delivery_area_provision_7zz_resume_assets_v1")
DATA_ROOT = Path("/disk1/zlab/cross_dataset_assets/eth3d_delivery_area_protocol_v2_v1")
ARCHIVE_CACHE = DATA_ROOT / "ARCHIVE_CACHE"
QUARANTINE = DATA_ROOT / "RAW_EXTRACT_QUARANTINE"
TRAIN_ROOT = DATA_ROOT / "TRAIN_INPUT_ROOT"
EVAL_ROOT = DATA_ROOT / "EVAL_ORACLE_ROOT"
CONTRACTS = DATA_ROOT / "CONTRACTS"
SEVEN_Z = TASK_ROOT / "tools/7zz/7zz"
PROXY_WRAPPER = Path.home() / ".config/scannetpp_proxy/run_with_scannetpp_proxy.sh"
OFFICIAL_BASE = "https://www.eth3d.net/data"
DISK_LIMIT_BYTES = 30_000_000_000

ASSETS = [
    ("delivery_area_rig_undistorted.7z", 278_900_786, "MAPPING_INPUT_SOURCE_ARCHIVE"),
    ("delivery_area_rig_scan_eval.7z", 36_142_207, "HELDOUT_EVALUATION_ONLY"),
    ("delivery_area_rig_occlusion.7z", 56_643_980, "HELDOUT_EVALUATION_ONLY"),
    ("delivery_area_rig_depth.7z", 636_547_888, "HELDOUT_EVALUATION_ONLY"),
    ("delivery_area_scan_clean.7z", 381_363_091, "REFERENCE_ORACLE_ONLY"),
    ("delivery_area_dslr_undistorted.7z", 478_076_254, "CROSS_VIEW_EVALUATION_ONLY"),
    ("delivery_area_dslr_scan_eval.7z", 122_553_428, "CROSS_VIEW_EVALUATION_ONLY"),
    ("delivery_area_dslr_occlusion.7z", 56_850_384, "CROSS_VIEW_EVALUATION_ONLY"),
    ("delivery_area_dslr_depth.7z", 388_144_128, "CROSS_VIEW_EVALUATION_ONLY"),
]

DENYLIST = [
    "delivery_area_scan_raw.7z",
    "delivery_area_dslr_raw.7z",
    "delivery_area_dslr_jpg.7z",
    "delivery_area_rig.7z",
    "delivery_area_rig_stereo_pairs_gt.7z",
]


def ensure_roots() -> None:
    for path in (TASK_ROOT, ARCHIVE_CACHE, QUARANTINE, TRAIN_ROOT, EVAL_ROOT, CONTRACTS):
        path.mkdir(parents=True, exist_ok=True)
