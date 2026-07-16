#!/usr/bin/env python3
"""Read Git-historical TUM provenance without checking out or changing it."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HIST = "3e22a7cae6f4c3c2c192cc2d7af3c9fbd607a0a3"
REPORT = "work/risk_aware_cbf/REPORT_CROSS_DATASET_METRIC_PREPROCESSING.md"
HISTORICAL_SELECTED = "work/risk_aware_cbf/results/cross_dataset_metric_preprocessing/tum_selected_frames_summary.csv"
EXPECTED_REPORT_SHA = "ff0f43a4465faf76cb18bd77e044a4662b0f51dbcfc65277813689db80af4bd1"
EXPECTED_TRANSFORMS_SHA = "b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a"

def git_bytes(spec: str) -> bytes:
    return subprocess.run(["git", "show", spec], check=True, stdout=subprocess.PIPE).stdout

report = git_bytes(f"{HIST}:{REPORT}")
report_sha = hashlib.sha256(report).hexdigest()
sources = {
    "historical_commit": HIST,
    "historical_branch": "safer-cross-dataset-metric-preprocessing",
    "historical_report": REPORT,
    "historical_report_sha256_expected": EXPECTED_REPORT_SHA,
    "historical_report_sha256_observed": report_sha,
    "historical_report_hash_matches": report_sha == EXPECTED_REPORT_SHA,
    "historical_preprocessor": "work/risk_aware_cbf/scripts/preprocess_tum_rgbd_metric.py",
    "historical_raw_validation": "work/risk_aware_cbf/scripts/validate_cross_dataset_raw_assets.py",
    "historical_raw_asset_path": "/disk1/zlab/cross_dataset_assets/raw/tum_rgbd/rgbd_dataset_freiburg1_room",
    "historical_transforms_path": "external output path was supplied with --out and is not recorded by the historical commit",
    "expected_transforms_sha256": EXPECTED_TRANSFORMS_SHA,
    "source_url": "https://cvg.cit.tum.de/rgbd/dataset/freiburg1/rgbd_dataset_freiburg1_room.tgz",
    "read_only_operations": ["git show", "Git-historical SHA-256"],
}
identity = {
    "status": "resolved_from_historical_evidence",
    "dataset_id": "tum_metric_candidate",
    "dataset_family": "TUM_RGBD",
    "dataset_version": "TUM RGB-D benchmark",
    "sequence_name": "rgbd_dataset_freiburg1_room",
    "scene_identifier": "TUM_FR1_ROOM",
    "source_url_or_dataset_reference": sources["source_url"],
    "rgb_source_path": sources["historical_raw_asset_path"] + "/rgb",
    "depth_source_path": sources["historical_raw_asset_path"] + "/depth",
    "pose_source_path": sources["historical_raw_asset_path"] + "/groundtruth.txt",
    "transforms_path": "unavailable in current environment; historical external --out path was not recorded",
    "preprocessing_commit": HIST,
    "frame_count": 300,
    "timestamp_range": [1305031910.765238, 1305031956.136924],
    "identity_evidence": [REPORT, "work/risk_aware_cbf/results/cross_dataset_raw_acquisition/dataset_preregistration.csv", "work/risk_aware_cbf/results/cross_dataset_raw_acquisition/tum_file_integrity_summary.csv"],
    "identity_conflict": False,
}
environment = {"audit_mode": "windows_orchestration_only", "used_for_gate_decision": False, "historical_report_hash_matches": report_sha == EXPECTED_REPORT_SHA, "note": "A preliminary local Windows probe is non-authoritative and is superseded by the remote 4090 audit."}
remote_inputs = ROOT / "remote_outputs"
remote_inputs.mkdir(exist_ok=True)
selected = git_bytes(f"{HIST}:{HISTORICAL_SELECTED}")
(remote_inputs / "historical_tum_selected_frames.csv").write_bytes(selected)
for name, value in (("source_evidence_registry.json", sources), ("dataset_identity.json", identity), ("environment_provenance.json", environment)):
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print("historical_identity=TUM_FR1_ROOM report_hash_matches=" + str(report_sha == EXPECTED_REPORT_SHA).lower())
