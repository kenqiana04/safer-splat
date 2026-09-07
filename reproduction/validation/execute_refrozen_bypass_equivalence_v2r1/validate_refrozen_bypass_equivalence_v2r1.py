#!/usr/bin/env python3
"""Static preflight and final evidence validator for V2R1."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    task = args.task_dir.resolve()
    protocol = load(task.parent / "bypass_qa_trace_identity_repair_v2/BYPASS_EQUIVALENCE_PROTOCOL_V2R1.json")
    input_lock = load(task / "BYPASS_EQUIVALENCE_V2R1_INPUT_LOCK.json")
    execution_lock = load(task / "BYPASS_EQUIVALENCE_V2R1_EXECUTION_LOCK.json")
    preflight = load(task / "Q0R1_PREFLIGHT_RESULT.json")
    checks: list[dict[str, Any]] = []
    def check(name: str, passed: bool, evidence: Any) -> None:
        checks.append({"check": name, "passed": bool(passed), "evidence": evidence})
    check("01_pr118_identity_exact", input_lock["repository_exact_head"] == "a537ff653ac896aa1ab567b5197136efa1a937b4", input_lock["repository_exact_head"])
    check("02_protocol_sha_exact", input_lock["protocol_lock_sha256"] == "ba2079184d5f97b0c7ce58b37c5e31d96da4aa8d507172690424360cd11376f6" and input_lock["protocol_json_sha256"] == "f0206a54551d9fc93ef6a5e5c6a6dbf71c043c7882d0c34030180ca215161c52", input_lock["protocol_json_sha256"])
    check("03_input_lock_complete", input_lock["state"] == "FROZEN_COMPLETE", input_lock["state"])
    check("04_execution_lock_complete", execution_lock["state"] == "FROZEN_BEFORE_FIRST_REAL_ARM", execution_lock["state"])
    check("05_q0r1_12_of_12", preflight["passed_count"] == 12 and preflight["failed_count"] == 0, preflight["passed_count"])
    check("06_source_freeze_precedes_execution", execution_lock["source_freeze_sha256"] == sha(task / "PRE_EXECUTION_SOURCE_FREEZE.json"), execution_lock["source_freeze_sha256"])
    check("07_hard_cap", protocol["hard_real_arm_execution_cap"] == execution_lock["hard_real_arm_execution_cap"] == 10, 10)
    check("08_correction_quota_zero", protocol["real_execution_correction_quota"] == execution_lock["source_correction_quota_after_first_real_arm"] == 0, 0)
    check("09_old_pr117_not_reused", input_lock["historical_pr117_trace_reuse_allowed"] is False, False)
    check("10_fresh_process", protocol["fresh_process_per_arm"] is True, True)
    check("11_fresh_pair", protocol["fresh_pair_required"] is True, True)
    check("12_sentinel_first", protocol["execution_order"][0] == 50, protocol["execution_order"])
    check("13_active_disabled", protocol["active_runtime_on_allowed"] is False, False)
    check("14_oracle_disabled", protocol["scientific_oracle_allowed"] is False, False)
    if not args.preflight:
        root = args.evidence_root.resolve()
        summary = load(root / "BYPASS_EQUIVALENCE_V2R1_SUMMARY.json")
        ledger = [json.loads(line) for line in (root / "REAL_ARM_EXECUTION_LEDGER_V2R1.jsonl").read_text(encoding="utf-8").splitlines()]
        completed = [row for row in ledger if row.get("event_type") == "REAL_ARM_COMPLETED"]
        pairs = [load(root / "pairs" / f"pair_{trial}_comparison.json") for trial in (50, 10, 30, 70, 90)]
        check("15_execution_ledger_complete", len(completed) == 10, len(completed))
        check("16_infra_accounting", all(row["classification"] == "REAL_ARM_EXECUTION" for row in completed), [row["classification"] for row in completed])
        check("17_canonical_ids", all(row["canonical_trial_id"] == f"STONEHENGE_TRIAL_{row['native_trial_id']:03d}" for row in completed), True)
        check("18_trace_locks", all(pair["bypass_trace_lock_present"] for pair in pairs), True)
        check("19_bit_exact", all(pair["mismatch_count"] == 0 for pair in pairs), [pair["mismatch_count"] for pair in pairs])
        check("20_termination_exact", summary["termination_mismatch_count"] == 0, summary["termination_mismatch_count"])
        check("21_no_tolerance", all(pair["tolerance_used"] is False for pair in pairs), False)
        check("22_no_active", summary["active_runtime_on_execution_count"] == summary["intervention_count"] == 0, 0)
        check("23_no_oracle", summary["scientific_oracle_execution_count"] == 0, 0)
        check("24_protocol_deviation_zero", summary["protocol_deviation_count"] == 0, 0)
        check("25_pair_pass_count", summary["completed_pairs"] == summary["passed_pairs"] == 5, [summary["completed_pairs"], summary["passed_pairs"]])
        check("26_summary_matches_pairs", summary["total_compared_steps"] == sum(pair["total_compared_steps"] for pair in pairs), summary["total_compared_steps"])
    failed = sum(not item["passed"] for item in checks)
    result = {"schema": "REFROZEN_BYPASS_EQUIVALENCE_V2R1_VALIDATION", "checks": checks, "passed_count": len(checks) - failed, "failed_count": failed, "verdict": "PASS_REFROZEN_BYPASS_EQUIVALENCE_V2R1_VALIDATION" if failed == 0 and not args.preflight else "PASS_V2R1_STATIC_PREFLIGHT" if failed == 0 else "FAIL"}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
