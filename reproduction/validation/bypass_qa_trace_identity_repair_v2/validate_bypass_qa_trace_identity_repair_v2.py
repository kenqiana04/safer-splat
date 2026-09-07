#!/usr/bin/env python3
"""Static/CPU validator for the BYPASS QA trace-identity repair and V2R1 freeze."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
import subprocess
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
TASK = ROOT / "reproduction/validation/bypass_qa_trace_identity_repair_v2"
OLD = ROOT / "reproduction/validation/active_harness_bypass_equivalence_v2"
UPSTREAM = "06833d2bcf9649c0912133b8a28b1a0c4ec6f4f8"
ALLOWED_OLD_DIFF = {
    "reproduction/validation/active_harness_bypass_equivalence_v2/compare_bypass_equivalence.py",
    "reproduction/validation/active_harness_bypass_equivalence_v2/reference_trial_adapter.py",
    "reproduction/validation/active_harness_bypass_equivalence_v2/run_qa_pipeline.py",
}


def load(name: str) -> dict[str, Any]:
    return json.loads((TASK / name).read_text(encoding="utf-8"))


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def git(*args: str) -> str:
    result = run("git", *args)
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def raw_git_blob_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main() -> int:
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, evidence: Any) -> None:
        checks.append({"check": name, "passed": bool(passed), "evidence": evidence})

    input_lock = load("BYPASS_QA_TRACE_IDENTITY_REPAIR_INPUT_LOCK.json")
    protocol = load("BYPASS_EQUIVALENCE_PROTOCOL_V2R1.json")
    identity = load("CANONICAL_QA_TRIAL_IDENTITY_V2.json")
    invariants = load("TRACE_IDENTITY_REPAIR_INVARIANTS_V2.json")
    execution_lock = load("BYPASS_QA_TRACE_IDENTITY_REPAIR_EXECUTION_LOCK.json")
    protocol_lock = load("BYPASS_EQUIVALENCE_V2R1_PROTOCOL_LOCK.json")
    source_lock = load("REFERENCE_SOURCE_LOCK_REGRESSION_V2.json")
    root_cause = (TASK / "TRACE_IDENTITY_ROOT_CAUSE_V2.md").read_text(encoding="utf-8")
    helper = (TASK / "canonical_trial_identity.py").read_text(encoding="utf-8")
    adapter = (OLD / "reference_trial_adapter.py").read_text(encoding="utf-8")
    trace_writer = (ROOT / "reproduction/runtime/active_runtime_assurance_v2/trace_writer.py").read_text(encoding="utf-8")

    pr = run("gh", "pr", "view", "117", "--repo", "kenqiana04/safer-splat", "--json", "state,isDraft,title,headRefName,headRefOid,baseRefName,baseRefOid")
    pr_data = json.loads(pr.stdout) if pr.returncode == 0 else {"error": pr.stderr.strip()}
    expected_pr = {
        "state": "OPEN", "isDraft": True, "title": "[Draft] Verify active harness BYPASS equivalence V2",
        "headRefName": "verify-active-harness-bypass-equivalence-v2", "headRefOid": UPSTREAM,
        "baseRefName": "implement-active-runtime-assurance-v2", "baseRefOid": "a8d7a3c9522583ad61dc9bc87585e41bb71a0f77",
    }
    check("01_pr117_identity_exact", pr.returncode == 0 and pr_data == expected_pr, pr_data)

    old_diff = set(filter(None, git("diff", "--name-only", UPSTREAM, "--", "reproduction/validation/active_harness_bypass_equivalence_v2").splitlines()))
    check("02_old_evidence_untouched", old_diff == ALLOWED_OLD_DIFF, sorted(old_diff))
    locked_blobs = []
    for entry in input_lock["immutable_historical_evidence"]:
        path = f"reproduction/validation/active_harness_bypass_equivalence_v2/{entry['path']}"
        locked_blobs.append((path, git("rev-parse", f"{UPSTREAM}:{path}") == entry["git_blob"], git("diff", "--name-only", UPSTREAM, "--", path) == ""))
    check("03_historical_locks_and_results_immutable", all(blob_ok and diff_ok for _, blob_ok, diff_ok in locked_blobs), locked_blobs)

    check("04_root_cause_unique", "UNIQUE_TASK_LOCAL_DUAL_FORMATTER_IDENTITY_DIVERGENCE" in root_cause and root_cause.count("Single root cause") == 1, "dual formatter in one run_trial function")
    check("05_single_formatter_authority", helper.count("def make_canonical_trial_identity") == 1 and adapter.count("make_canonical_trial_identity(trial_id)") == 1, "one definition and one adapter call")
    check("06_arm_trial_separation", identity["arm_encoded_in_trial_id"] is False and identity["example_canonical_trial_id"] == "STONEHENGE_TRIAL_050", identity["arm_format"])
    check("07_snapshot_writer_same_binding", "TraceWriter(qa_identity.canonical_trial_id)" in adapter and "RuntimeStateSnapshot.create(qa_identity.canonical_trial_id" in adapter, identity["example_canonical_trial_id"])
    check("08_mismatch_guard_unchanged", "raise ValueError(\"TRIAL_IDENTITY_MISMATCH\")" in trace_writer and git("diff", "--name-only", UPSTREAM, "--", "reproduction/runtime/active_runtime_assurance_v2/trace_writer.py") == "", git("rev-parse", "HEAD:reproduction/runtime/active_runtime_assurance_v2/trace_writer.py"))

    repair_tests = run("python", "-B", "-m", "unittest", "discover", "-s", str(TASK / "tests"), "-v")
    check("09_repair_tests_pass", repair_tests.returncode == 0 and "Ran 11 tests" in repair_tests.stderr, repair_tests.stderr[-500:])
    check("10_one_step_synthetic_pass", repair_tests.returncode == 0 and "test_real_bypass_commit_appends_and_finalizes_one_record" in repair_tests.stderr, "startup->commit->append->finalize->lock")
    check("11_dual_arm_pairing_pass", repair_tests.returncode == 0 and "test_all_frozen_trials_share_trial_identity_across_arms" in repair_tests.stderr, [10, 30, 50, 70, 90])
    check("12_negative_tests_pass", repair_tests.returncode == 0 and all(token in repair_tests.stderr for token in ("test_snapshot_050_writer_030_must_fail", "test_arm_encoded_writer_must_fail", "test_append_after_finalize_must_fail")), "strict mismatch/finalize guards")
    check("13_reference_source_lock_pass", source_lock["verdict"] == "PASS_REFERENCE_CONTROL_PLANT_PATH_SOURCE_LOCK" and source_lock["reference_control_plant_termination_payload_changed"] is False, source_lock["frozen_reference_semantics"])

    runtime_tests = run("python", "-B", "-m", "unittest", "discover", "-s", str(ROOT / "reproduction/runtime/active_runtime_assurance_v2/tests"), "-v")
    check("14_pr116_runtime_tests_pass", runtime_tests.returncode == 0 and "Ran 78 tests" in runtime_tests.stderr, runtime_tests.stderr[-500:])
    check("15_plantcommit_bypass_regression_pass", repair_tests.returncode == 0 and "test_bypass_delegates_exact_reference_bits" in repair_tests.stderr and "test_non_bypass_guard_remains_strict" in repair_tests.stderr, git("rev-parse", "HEAD:reproduction/runtime/active_runtime_assurance_v2/plant_commit.py"))

    protected = git("diff", "--name-only", UPSTREAM, "--", "run.py", "cbf", "dynamics", "splat", "reproduction/runtime", "reproduction/specification", "reproduction/design")
    check("16_production_runtime_diff_zero", protected == "", protected)
    check("17_pr107_pr116_frozen_diff_zero", protected == "", "protected authority/runtime/specification/design paths")
    check("18_no_execution_counts", all(execution_lock[key] == 0 for key in ("real_arm_execution_count", "gpu_qa_count", "reference_real_trial_count", "bypass_real_trial_count", "active_runtime_on_execution_count", "scientific_oracle_execution_count", "official100_execution_count")), {key: execution_lock[key] for key in execution_lock if key.endswith("count")})

    check("19_v2r1_protocol_exists", protocol["status"] == "FROZEN_FOR_FUTURE_EXECUTION_TASK", protocol["schema"])
    check("20_hard_cap_10", protocol["hard_real_arm_execution_cap"] == 10 and protocol["real_execution_counter_initial_value"] == 0, protocol["hard_real_arm_execution_cap"])
    check("21_correction_quota_zero", protocol["real_execution_correction_quota"] == 0, protocol["real_execution_correction_quota"])
    check("22_exact_criteria_unchanged", protocol["equality"]["action"] == "FLOAT32_BIT_EXACT" and protocol["equality"]["state"] == "FLOAT32_BIT_EXACT" and protocol["equality"]["tolerance_substitution_allowed"] is False, protocol["equality"])
    check("23_fresh_pair_rule", protocol["fresh_pair_required"] is True and protocol["pr117_historical_trace_reuse_allowed"] is False, ["REF50_new", "BYPASS50_new"])
    infra = protocol["infrastructure_not_counted_rule"]
    check("24_infra_accounting_rule", all(infra[key] == 0 for key in ("required_solver_steps", "required_plant_commits", "required_finalized_traces", "required_comparison_evidence")), infra)
    ids = [entry["id"] for entry in invariants["invariants"]]
    check("25_rti_invariants_complete", invariants["invariant_count"] == 20 and ids == [f"RTI-{index:02d}" for index in range(1, 21)], ids)
    check("26_protocol_lock_content_addressed", protocol_lock["protocol_raw_git_blob_sha256"] == raw_git_blob_sha256(TASK / "BYPASS_EQUIVALENCE_PROTOCOL_V2R1.json"), protocol_lock["protocol_raw_git_blob_sha256"])
    check("27_repair_input_lock_content_addressed", execution_lock["repair_input_lock_raw_git_blob_sha256"] == raw_git_blob_sha256(TASK / "BYPASS_QA_TRACE_IDENTITY_REPAIR_INPUT_LOCK.json"), execution_lock["repair_input_lock_raw_git_blob_sha256"])
    review_chars = len((TASK / "trace_identity_repair_review.json").read_text(encoding="utf-8"))
    check("28_reviewer_compact", review_chars <= 1000, review_chars)

    failed = sum(not item["passed"] for item in checks)
    verdict = "PASS_BYPASS_QA_TRACE_IDENTITY_REPAIR_V2_VALIDATION" if failed == 0 else "BLOCKED_BYPASS_QA_TRACE_IDENTITY_REPAIR_V2_VALIDATION"
    result = {"schema": "BYPASS_QA_TRACE_IDENTITY_REPAIR_V2_VALIDATION", "verdict": verdict, "passed_count": len(checks) - failed, "failed_count": failed, "checks": checks}
    (TASK / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(verdict)
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
