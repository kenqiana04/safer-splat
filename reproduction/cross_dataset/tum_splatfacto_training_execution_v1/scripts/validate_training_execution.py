#!/usr/bin/env python3
"""Validate the allowed blocked-preflight outcome without invoking training."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main() -> None:
    preflight = load("preflight_result.json")
    hashes = load("protocol_hash_verification.json")
    run = load("run_status.json")
    source = load("source_asset_postcheck.json")
    gpu = load("gpu_preflight.json")
    checks = {
        "preflight_blocked_by_hash_mismatch": preflight.get("status") == "BLOCKED_BY_PROTOCOL_HASH_MISMATCH",
        "command_hash_mismatch_recorded": hashes.get("observed", {}).get("command") != hashes.get("expected", {}).get("command"),
        "config_hash_mismatch_recorded": hashes.get("observed", {}).get("config") != hashes.get("expected", {}).get("config"),
        "transforms_hash_matches": hashes.get("observed", {}).get("transforms") == hashes.get("expected", {}).get("transforms"),
        "no_formal_attempt_started": run.get("formal_attempts_started") == 0 and run.get("training_command_executed") is False,
        "formal_output_absent": run.get("expected_run_exists") is False,
        "source_assets_unchanged": source.get("unchanged") is True,
        "gpu_busy_recorded_without_intervention": gpu.get("status") == "BLOCKED_BY_GPU_BUSY",
        "no_safer": run.get("tuning_used") is False,
        "G1_forbidden": True,
    }
    result = {
        "validated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "BLOCKED_BY_PROTOCOL_HASH_MISMATCH" if all(checks.values()) else "FAIL",
        "failure_classification": "BLOCKED_BY_PROTOCOL_HASH_MISMATCH",
        "checks": checks,
        "checkpoint_candidate_ready": False,
        "formal_training_started": False,
        "resume_used": False,
        "retry_used": False,
        "second_seed_run": False,
        "safer_loader_executed": False,
        "G1_allowed": False,
    }
    (ROOT / "execution_validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["status"])
    if result["status"] == "FAIL":
        raise SystemExit("blocked-outcome validation failed")


if __name__ == "__main__":
    main()
