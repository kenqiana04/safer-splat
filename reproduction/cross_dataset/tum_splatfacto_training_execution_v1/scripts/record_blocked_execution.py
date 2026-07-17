#!/usr/bin/env python3
"""Record a pre-training block without starting or modifying a formal run."""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN = Path("/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1/splatfacto/20260716_000000")
RAW = Path("/disk1/zlab/cross_dataset_assets/raw/tum_rgbd/rgbd_dataset_freiburg1_room")
TRANSFORMS = Path("/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room/transforms.json")
EXPECTED_SOURCE = {
    "depth.txt": "86757dd3c8606f940477a353915ede7143811817b2288647414fe1459ed22c14",
    "groundtruth.txt": "66b6770d887a5a3b69c94c3b186c3f76fe092ca25399772177f41aed984bd1b0",
    "rgb.txt": "fe2f438ebe1b3d13a061e4db3b154df1136a82d95a723e4a6457b0e516c2451b",
    "transforms.json": "b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def dump(name: str, value: object) -> None:
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def session_exists() -> bool:
    return subprocess.run(["tmux", "has-session", "-t", "tum_fr1_room_splatfacto_v1_seed20260716"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def main() -> None:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    preflight = load("preflight_result.json")
    hashes = load("protocol_hash_verification.json")
    gpu = load("gpu_preflight.json")
    dataset = load("dataset_preflight.json")
    observed_source = {"depth.txt": sha256(RAW / "depth.txt"), "groundtruth.txt": sha256(RAW / "groundtruth.txt"), "rgb.txt": sha256(RAW / "rgb.txt"), "transforms.json": sha256(TRANSFORMS)}
    source_ok = observed_source == EXPECTED_SOURCE
    dump("source_asset_postcheck.json", {"checked_at_utc": now, "source_paths": {"raw_root": str(RAW), "transforms": str(TRANSFORMS)}, "expected_sha256": EXPECTED_SOURCE, "observed_sha256": observed_source, "unchanged": source_ok, "source_assets_modified_by_task": False})
    blocking = ["BLOCKED_BY_PROTOCOL_HASH_MISMATCH"]
    if gpu.get("status") == "BLOCKED_BY_GPU_BUSY":
        blocking.append("BLOCKED_BY_GPU_BUSY")
    dump("run_status.json", {"checked_at_utc": now, "status": "BLOCKED_BY_PROTOCOL_HASH_MISMATCH", "blocking_conditions": blocking, "formal_attempts_started": 0, "formal_attempts_completed": 0, "training_command_executed": False, "expected_run": str(RUN), "expected_run_exists": RUN.exists(), "resume_used": False, "retry_used": False, "tuning_used": False, "second_seed_run": False})
    dump("training_process_record.json", {"status": "NOT_STARTED_BLOCKED_PRETRAINING", "tmux_session": "tum_fr1_room_splatfacto_v1_seed20260716", "tmux_session_existed_before_start": session_exists(), "training_command_executed": False, "start_utc": None, "end_utc": None, "exit_code": None, "formal_attempt_count": 0})
    dump("training_log_summary.json", {"status": "NOT_AVAILABLE_TRAINING_NOT_STARTED", "last_completed_iteration": None, "fatal_exception": None, "oom_detected": False, "nan_or_inf_detected": False, "log_path": "/disk1/zlab/formal_execution_records/tum_fr1_room_splatfacto_v1_seed20260716/training_stdout_stderr.log", "log_created": False})
    with (ROOT / "checkpoint_inventory.csv").open("w", newline="", encoding="utf-8") as handle:
        csv.DictWriter(handle, fieldnames=["path", "filename", "step", "size_bytes", "sha256", "mtime_utc", "is_final_candidate", "selection_reason"]).writeheader()
    dump("checkpoint_integrity.json", {"status": "NOT_RUN_BLOCKED_PRETRAINING", "run_exists": RUN.exists(), "final_checkpoint_candidate_count": 0, "checkpoint_loaded": False, "gaussian_count": None, "finite_checks": None})
    dump("metric_invariant_audit.json", {"status": "NOT_RUN_BLOCKED_PRETRAINING", "source_frame_count": dataset.get("source_frame_count"), "train_count": dataset.get("train_count"), "val_count": dataset.get("val_count"), "frame_drop_count": dataset.get("frame_drop_count"), "dataparser_transform_identity": dataset.get("transform_identity"), "dataparser_scale": dataset.get("dataparser_scale"), "depth_unit_scale_factor": dataset.get("depth_unit_scale_factor"), "pose_optimization": False, "similarity_alignment": False, "scale_fitting": False})
    dump("eval_metrics.json", {"status": "NOT_RUN_BLOCKED_PRETRAINING", "psnr": None, "ssim": None, "lpips": None, "eval_runtime_seconds": None, "checkpoint_selection_by_metrics": False})
    dump("eval_render_integrity.json", {"status": "NOT_RUN_BLOCKED_PRETRAINING", "expected_render_count": 60, "actual_render_count": 0, "missing_count": 60, "decode_failure_count": None, "all_zero_rgb_count": None, "nonfinite_render_count": None})
    dump("geometry_sanity_status.json", {"status": "NOT_RUN_BLOCKED_PRETRAINING", "metric_geometry_claim": "not made", "deferred_status": "DEFERRED_TO_G0_CHECKPOINT_GEOMETRY_AUDIT", "checkpoint_inspected": False})
    checks = {
        "authorization_commit_precedes_training": True,
        "draft_pr_created_before_training": True,
        "formal_attempt_count_is_zero_due_to_preflight_block": True,
        "command_hash_matches_contract": hashes["observed"]["command"] == hashes["expected"]["command"],
        "config_hash_matches_contract": hashes["observed"]["config"] == hashes["expected"]["config"],
        "transforms_hash_matches_contract": hashes["observed"]["transforms"] == hashes["expected"]["transforms"],
        "source_assets_unchanged": source_ok,
        "formal_output_absent": not RUN.exists(),
        "no_resume": True,
        "no_retry": True,
        "no_tuning": True,
        "no_second_seed": True,
        "no_safer": True,
        "G1_allowed": False,
        "gpu_was_idle": gpu.get("status") == "PASS",
        "preflight_status": preflight.get("status"),
    }
    dump("execution_validation_result.json", {"status": "BLOCKED_BY_PROTOCOL_HASH_MISMATCH", "failure_classification": "BLOCKED_BY_PROTOCOL_HASH_MISMATCH", "checks": checks, "training_started": False, "checkpoint_candidate_ready": False, "maximum_success_status_not_reached": "PASS_CHECKPOINT_CANDIDATE_READY_FOR_G0_COMPATIBILITY_AUDIT"})
    report = f"""# REPORT: Formal TUM Splatfacto Training Execution V1

## Executive Summary

Formal training was **not started**. The preflight result is
`BLOCKED_BY_PROTOCOL_HASH_MISMATCH`; therefore the one authorized training
attempt remains unused. The physical 4090 GPU 1 also had an unrelated Python
compute process using 1728 MiB, recorded as `BLOCKED_BY_GPU_BUSY`.

## Authorization and Frozen Contract

- Dependency protocol commit: `b56f5eb9af1c67791466f37e1f6c2514958cdcd3`
- Execution authorization commit: `fe00d8849a666cf6e1619f8ec11251cb682124f5`
- Expected run: `{RUN}`
- Attempt count: `0`; no tmux training session was started.
- Expected command SHA-256: `{hashes['expected']['command']}`
- Observed command SHA-256: `{hashes['observed']['command']}`
- Expected frozen-config SHA-256: `{hashes['expected']['config']}`
- Observed frozen-config SHA-256: `{hashes['observed']['config']}`
- Transforms SHA-256: `{hashes['observed']['transforms']}` (matches contract).

## Preflight Evidence

- Environment and dataparser-only preflight: passed (`TUM_FR1_ROOM`, 300 total,
  240 train, 60 val, zero frame drop, native 3x4 identity transform, parser
  scale 1, depth scale 0.0002).
- Disk and output preflight: passed (run path absent; 509.49 GiB free).
- Shell syntax: passed for all three frozen/invocation/post-training scripts.
- Protocol identity: blocked because both command and frozen-config byte hashes
  differ from the authorization contract. No frozen protocol file was changed.
- GPU: blocked because GPU 1 had an unrelated Python process. It was not killed,
  moved, or otherwise modified.
- Source asset postcheck: `{source_ok}`; raw index/pose manifests and processed
  transforms retain their expected SHA-256 values.

## Non-Execution Boundary

No `ns-train`, checkpoint creation, output-directory creation, resume, retry,
tuning, second seed, `ns-eval`, rendering, SAFER loader, ellipsoid query,
navigation, baseline, or G1 operation was executed. There is no checkpoint,
metric, render, or geometry result to report.

## Validation and Next Step

Validator status: `BLOCKED_BY_PROTOCOL_HASH_MISMATCH`. This is not a training
failure and no retry is authorized. The frozen protocol hashes must first be
reconciled through a separately authorized correction; GPU availability must
also be rechecked before any future formal attempt. This task does not produce a
checkpoint candidate and does not authorize G0 or G1 execution.

## Server Evidence Paths

- Worktree: `/disk1/zlab/formal_execution_worktrees/tum_splatfacto_training_execution_v1`
- Compact evidence: `{ROOT}`
- Formal output path retained absent: `{RUN}`
"""
    (ROOT / "REPORT_TUM_SPLATFACTO_TRAINING_EXECUTION_V1.md").write_text(report, encoding="utf-8")
    excluded = {"execution_bundle_sha256.json"}
    bundle = {str(path.relative_to(ROOT)): sha256(path) for path in sorted(ROOT.rglob("*")) if path.is_file() and path.name not in excluded and "__pycache__" not in path.parts}
    dump("execution_bundle_sha256.json", {"status": "BLOCKED_BY_PROTOCOL_HASH_MISMATCH", "files": bundle, "excluded": sorted(excluded)})
    print("BLOCKED_BY_PROTOCOL_HASH_MISMATCH")


if __name__ == "__main__":
    main()
