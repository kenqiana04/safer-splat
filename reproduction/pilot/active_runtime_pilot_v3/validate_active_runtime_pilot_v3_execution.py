#!/usr/bin/env python3
"""Validate the Pilot V3 execution lock or completed evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


BASE = "18664bcb8d6e71333e1216c5af0c6757840540f8"
TASK_REL = Path("reproduction/pilot/active_runtime_pilot_v3")
TRIALS = [5, 15, 25, 35, 45, 55, 65, 75, 85, 95]


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--repo-root", default="."); parser.add_argument("--phase", choices=["lock", "evidence"], required=True); args = parser.parse_args()
    repo = Path(args.repo_root).resolve(); task = repo / TASK_REL
    protocol, input_lock, execution_lock = load(task / "PILOT_V3_PROTOCOL.json"), load(task / "PILOT_V3_INPUT_LOCK.json"), load(task / "PILOT_V3_EXECUTION_LOCK.json")
    checks = {}
    checks["base_in_ancestry"] = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", BASE, "HEAD"], check=False).returncode == 0
    checks["protocol_immutable"] = sha(task / "PILOT_V3_PROTOCOL.json") == input_lock["protocol_sha256"] == execution_lock["protocol_sha256"]
    checks["runner_hash"] = sha(task / "run_active_runtime_pilot_v3.py") == execution_lock["runner_sha256"]
    checks["cohort_exact"] = protocol["trial_order"] == execution_lock["trial_order"] == TRIALS
    checks["execution_exact"] = execution_lock["max_cycles"] == 500 and execution_lock["seed"] == 0 and execution_lock["serial_execution"] is True and execution_lock["separate_process_per_trial"] is True
    checks["geometry_exact"] = execution_lock["v3_geometry"] == {"r_body_q": 0.015, "m_hard_q": 0.0, "r_hard_q": 0.015, "rho_seg_q": 0.0}
    checks["historical_authority_false"] = execution_lock["historical_diagnostic_shell"]["radius_q"] == 0.025 and all(value is False for key, value in execution_lock["historical_diagnostic_shell"].items() if key.endswith("authority"))
    changed = subprocess.check_output(["git", "-C", str(repo), "diff", "--name-only", BASE, "--", "cbf", "dynamics", "splat", "run.py", "reproduction/runtime", "reproduction/smoke/active_runtime_smoke_v3", "reproduction/formal"], text=True).strip()
    checks["protected_diff_zero"] = not changed
    if args.phase == "lock":
        checks["execution_counts_zero"] = execution_lock["execution_counts_at_lock"] == {"gpu_pilot": 0, "official100": 0, "scientific_oracle": 0, "formal": 0, "reference_arm": 0}
        checks["no_trial_evidence"] = not any((task / "raw" / f"trial_{trial}").exists() for trial in TRIALS)
    else:
        summary = load(task / "PILOT_V3_EXECUTION_SUMMARY.json")
        checks["all_trials_accounted"] = summary["completed_trials"] == 10 and summary["trial_ids"] == TRIALS
        checks["trace_cardinality_pass"] = summary["trace_cardinality"] == "PASS"
        checks["zero_forbidden_execution"] = all(summary[key] == 0 for key in ("official100_count", "scientific_oracle_count", "formal_count", "reference_arm_count"))
        checks["hard_radius_exact"] = summary["hard_runtime_radius_observed_values_q"] == [0.015]
        checks["historical_authority_absent"] = summary["historical_diagnostic_runtime_authority_observed"] is False and summary["forbidden_diagnostic_authority_event_count"] == 0
    failed = sorted(key for key, value in checks.items() if not value)
    result = {"schema": "ACTIVE_RUNTIME_PILOT_V3_EXECUTION_VALIDATION_V1", "phase": args.phase, "status": "PASS_ACTIVE_RUNTIME_PILOT_V3_EXECUTION_LOCK_VALIDATION" if args.phase == "lock" and not failed else ("PASS_ACTIVE_RUNTIME_PILOT_V3_EXECUTION_VALIDATION" if not failed else "FAIL_ACTIVE_RUNTIME_PILOT_V3_EXECUTION_VALIDATION"), "checks": checks, "failed_checks": failed}
    path = task / ("PILOT_V3_EXECUTION_LOCK_VALIDATION.json" if args.phase == "lock" else "PILOT_V3_EXECUTION_VALIDATION.json")
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    if failed:
        print("FAILED_CHECKS=" + ",".join(failed), file=sys.stderr); return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
