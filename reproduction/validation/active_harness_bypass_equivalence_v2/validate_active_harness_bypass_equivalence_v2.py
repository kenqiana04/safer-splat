#!/usr/bin/env python3
"""Final evidence validator for Active Harness BYPASS equivalence V2."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import subprocess


EXPECTED_UPSTREAM = "a8d7a3c9522583ad61dc9bc87585e41bb71a0f77"
EXPECTED_IDS = [10, 30, 50, 70, 90]
EXPECTED_ORDER = [50, 10, 30, 70, 90]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--git-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root, git_root = args.task_root.resolve(), args.git_root.resolve()
    protocol = load(root / "BYPASS_EQUIVALENCE_PROTOCOL_V2.json")
    input_lock = load(root / "BYPASS_EQUIVALENCE_INPUT_LOCK.json")
    execution_lock = load(root / "BYPASS_EQUIVALENCE_EXECUTION_LOCK.json")
    q0 = load(root / "Q0_PREFLIGHT_RESULT.json")
    summary = load(root / "comparison/summary.json")
    trials = load(root / "comparison/per_trial_equivalence.json")["trials"]
    mismatch = load(root / "BYPASS_EQUIVALENCE_MISMATCH_REGISTER.json")
    with (root / "BYPASS_QA_EXECUTION_MANIFEST.csv").open(encoding="utf-8", newline="") as handle:
        executions = list(csv.DictReader(handle))
    with (root / "comparison/per_step_equivalence.csv").open(encoding="utf-8", newline="") as handle:
        steps = list(csv.DictReader(handle))
    checks = []

    def check(name, passed, evidence):
        checks.append({"check": name, "passed": bool(passed), "evidence": evidence})

    check("01_pr116_identity_exact", input_lock["upstream"]["head_sha"] == EXPECTED_UPSTREAM, input_lock["upstream"])
    check("02_protocol_commit_predates_artifacts", execution_lock["protocol_commit_sha"] and execution_lock["frozen_before_real_execution"], execution_lock["protocol_commit_sha"])
    check("03_trial_ids_exact", protocol["qa_trial_ids"] == EXPECTED_IDS, protocol["qa_trial_ids"])
    check("04_sentinel_order", [int(row["trial_id"]) for row in executions[::2]] == EXPECTED_ORDER and int(executions[0]["trial_id"]) == 50, [row["trial_id"] for row in executions])
    check("05_arms_exact", all([row["arm"] for row in executions[i:i+2]] == protocol["arm_order_per_trial"] for i in range(0, len(executions), 2)), [row["arm"] for row in executions])
    check("06_execution_cap", len(executions) == 10 and len(executions) <= protocol["normal_real_execution_cap"], len(executions))
    check("07_locks_complete", bool(input_lock["source_git_blobs"]) and bool(execution_lock["task_tool_sha256"]), True)
    protected_diff = subprocess.run(["git", "diff", f"{EXPECTED_UPSTREAM}..HEAD", "--", "run.py", "cbf", "dynamics", "splat", "reproduction/runtime/active_runtime_assurance_v2"], cwd=git_root, text=True, capture_output=True, check=True).stdout
    check("08_protected_diff_zero", protected_diff == "", protected_diff)
    check("09_reference_adapter_conformance", "PASS_REFERENCE_CONTROL_PLANT_PATH_SOURCE_LOCK" in (root / "REFERENCE_ADAPTER_CONFORMANCE_AUDIT.md").read_text(encoding="utf-8"), True)
    check("10_no_active_runtime_on", summary["active_runtime_on_execution_count"] == 0, summary["active_runtime_on_execution_count"])
    check("11_no_active_certification_influence", summary["active_intervention_count"] == 0, summary["active_intervention_count"])
    check("12_no_oracle", summary["scientific_oracle_execution_count"] == 0, summary["scientific_oracle_execution_count"])
    check("13_action_exact", bool(steps) and all(row["action_bits_equal"] == "True" for row in steps), summary["action_exact_rate"])
    check("14_selected_executed_exact", bool(steps) and all(row["selected_executed_equal"] == "True" for row in steps), summary["selected_executed_exact_rate"])
    check("15_state_exact", bool(steps) and all(row["state_bits_equal"] == "True" for row in steps), summary["state_exact_rate"])
    check("16_branch_termination_exact", all(item["termination_match"] and item["exact_branch_rows"] == item["total_compared_rows"] for item in trials), summary["termination_exact_rate"])
    check("17_no_token_mutation", summary["token_mutation_count"] == 0, summary["token_mutation_count"])
    check("18_no_tolerance_change", summary["outcome_tolerance_changed"] is False and protocol["post_data_tolerance_change_allowed"] is False, False)
    check("19_mismatch_register_empty", mismatch["mismatch_count"] == 0 and mismatch["first_mismatch"] is None, mismatch)
    check("20_all_trials_pass", len(trials) == 5 and all(item["trial_verdict"] == "PASS" for item in trials), [item["trial_verdict"] for item in trials])
    check("21_no_official100", summary["official100_execution_count"] == 0, summary["official100_execution_count"])
    report = (root / "report/REPORT_VERIFY_ACTIVE_HARNESS_BYPASS_EQUIVALENCE_V2.md").read_text(encoding="utf-8")
    nonclaims = ["collision reduction", "progress improvement", "real-time", "deployment"]
    check("22_report_nonclaims", all(term in report for term in nonclaims), nonclaims)
    check("23_q0_pass", q0["verdict"] == "PASS_BYPASS_EQUIVALENCE_Q0_PREFLIGHT", q0["verdict"])
    check("24_trace_locks_complete", summary["trace_lock_count"] == 5, summary["trace_lock_count"])
    result = {
        "schema": "ACTIVE_HARNESS_BYPASS_EQUIVALENCE_V2_VALIDATION",
        "checks": checks,
        "passed_count": sum(item["passed"] for item in checks),
        "failed_count": sum(not item["passed"] for item in checks),
        "verdict": "PASS_ACTIVE_HARNESS_BYPASS_EQUIVALENCE_V2_VALIDATION" if all(item["passed"] for item in checks) else "BLOCKED_ACTIVE_HARNESS_BYPASS_EQUIVALENCE_V2_VALIDATION",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["verdict"])
    return 0 if result["failed_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
