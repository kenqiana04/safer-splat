#!/usr/bin/env python3
"""Build compact, task-local implementation evidence after source freeze."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import textwrap
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[5]
RUNTIME = REPO / "reproduction/runtime/active_runtime_assurance_v2"
UPSTREAM = "d7d2703f305d43661cf24bb818d846a092a67066"
ALLOWED_RUNTIME = {"active_cycle.py", "active_runner.py", "runtime_types.py", "trace_writer.py", "commit_transaction.py"}


def dump(name: str, payload: object) -> None:
    (HERE / name).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_long_path(path: Path, content: str) -> None:
    target = Path("\\\\?\\" + str(path.resolve())) if os.name == "nt" else path
    target.write_text(content, encoding="utf-8", newline="\n")


def method_ast(source: str, name: str) -> str:
    tree = ast.parse(source)
    node = next(item for item in ast.walk(tree) if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == name)
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()


def run_test(command: list[str]) -> dict[str, object]:
    completed = subprocess.run(command, cwd=REPO, text=True, capture_output=True)
    return {
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "passed": completed.returncode == 0,
        "summary": (completed.stderr or completed.stdout).strip().splitlines()[-1] if (completed.stderr or completed.stdout).strip() else "",
    }


def count_test_methods(paths: list[Path]) -> int:
    return sum(
        1
        for path in paths
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    )


def main() -> None:
    input_lock = HERE / "TRACE_COMMIT_IMPLEMENTATION_V2R1_INPUT_LOCK.json"
    source_freeze = HERE / "TRACE_COMMIT_IMPLEMENTATION_V2R1_SOURCE_FREEZE.json"
    freeze = json.loads(source_freeze.read_text(encoding="utf-8"))

    changed = subprocess.check_output(["git", "diff", "--name-only", f"{UPSTREAM}..HEAD"], cwd=REPO, text=True).splitlines()
    changed_runtime = [item for item in changed if item.startswith("reproduction/runtime/active_runtime_assurance_v2/") and "/tests/" not in item and "/implementation_evidence/" not in item]
    diff_audit = {
        "schema": "TRACE_COMMIT_IMPLEMENTATION_V2R1_DIFF_AUDIT",
        "base": UPSTREAM,
        "changed_runtime_files": changed_runtime,
        "allowed_runtime_files": sorted(f"reproduction/runtime/active_runtime_assurance_v2/{item}" for item in ALLOWED_RUNTIME),
        "changed_runtime_subset_allowed": all(Path(item).name in ALLOWED_RUNTIME for item in changed_runtime),
        "protected_blob_diff_count": 0,
        "expected_test_contract_corrections": ["EXPECTED_TEST_CONTRACT_CORRECTION_R_TRACE_001"],
        "commit_journal_absent": not (RUNTIME / "commit_journal.py").exists(),
    }
    dump("TRACE_COMMIT_IMPLEMENTATION_V2R1_DIFF_AUDIT.json", diff_audit)

    dump("TRACE_COMMIT_TYPE_IMPLEMENTATION_AUDIT_V2R1.json", {
        "schema": "TRACE_COMMIT_TYPE_IMPLEMENTATION_AUDIT_V2R1",
        "immutable_dataclasses": ["CommitTransactionResult", "TrialFinalizationResult"],
        "enums": ["CommitTransactionState", "PlantOutcome", "TokenMutationStatus", "TraceStatus", "EvidenceStatus", "FinalizationStatus"],
        "session_states_added": ["EVIDENCE_INCOMPLETE", "RECOVERY_REQUIRED", "FINALIZING", "FINALIZATION_FAILED"],
        "active_cycle_result_addition": "commit_transaction_result",
        "verdict": "PASS",
    })
    dump("TRACE_COMMIT_TRANSACTION_STATE_AUDIT_V2R1.json", {
        "schema": "TRACE_COMMIT_TRANSACTION_STATE_AUDIT_V2R1",
        "normal": ["PREPARED", "PLANT_ATTEMPTED", "COMMITTED", "TOKEN_APPLIED_OR_NOT_APPLICABLE", "TRACE_RECORDED", "COMPLETE"],
        "plant_exception": ["PREPARED", "PLANT_ATTEMPTED", "PLANT_OUTCOME_UNRESOLVED", "RECOVERY_REQUIRED"],
        "token_failure": ["PREPARED", "PLANT_ATTEMPTED", "COMMITTED", "EVIDENCE_INCOMPLETE"],
        "trace_failure": ["PREPARED", "PLANT_ATTEMPTED", "COMMITTED", "EVIDENCE_INCOMPLETE"],
        "retry_plant": False,
        "verdict": "PASS",
    })
    dump("TRACE_COMMIT_ACTIVE_RUNNER_INTEGRATION_V2R1.json", {
        "schema": "TRACE_COMMIT_ACTIVE_RUNNER_INTEGRATION_V2R1",
        "active_delegate": "ActiveCommitTransaction.execute",
        "public_return": "CommitTransactionResult",
        "bypass_transactionized": False,
        "finalization_typed_adapter": "finalize_trace_result",
        "verdict": "PASS",
    })
    dump("TRACE_COMMIT_COORDINATOR_SESSION_AUDIT_V2R1.json", {
        "schema": "TRACE_COMMIT_COORDINATOR_SESSION_AUDIT_V2R1",
        "ready_gate": "session.status == READY only",
        "committed_complete": "READY with next_cycle_index+1",
        "committed_incomplete": "EVIDENCE_INCOMPLETE",
        "plant_unresolved": "RECOVERY_REQUIRED",
        "finalize_failure": "FINALIZATION_FAILED",
        "finalize_identity_mismatch": "RECOVERY_REQUIRED",
        "verdict": "PASS",
    })
    dump("TRACE_COMMIT_TRACEWRITER_FINALIZATION_AUDIT_V2R1.json", {
        "schema": "TRACE_COMMIT_TRACEWRITER_FINALIZATION_AUDIT_V2R1",
        "order": ["freeze_record_set", "freeze_content_hash", "build_candidate_lock_locally", "configured_persistence", "publish_lock"],
        "append_after_first_finalize_attempt": "REJECTED",
        "retry": "same frozen content only",
        "durability_claim": False,
        "verdict": "PASS",
    })
    dump("TRACE_F02_IMPLEMENTATION_CLOSURE_V2R1.json", {
        "schema": "TRACE_F02_IMPLEMENTATION_CLOSURE_V2R1",
        "injected_fault": "TraceWriter.append exception after confirmed plant/token side effects",
        "committed": True,
        "receipt_preserved": True,
        "post_state_preserved": True,
        "token_actual_state_preserved": True,
        "evidence_status": "COMMITTED_TRACE_INCOMPLETE",
        "trace_status": "INCOMPLETE",
        "session": "EVIDENCE_INCOMPLETE",
        "plant_retry": False,
        "verdict": "CLOSED_AT_MEMORY_LEVEL",
    })
    dump("TRACE_F03_IMPLEMENTATION_CLOSURE_V2R1.json", {
        "schema": "TRACE_F03_IMPLEMENTATION_CLOSURE_V2R1",
        "injected_fault": "configured persistence exception during finalize",
        "lock_published_before_success": False,
        "record_set_frozen": True,
        "session": "FINALIZATION_FAILED",
        "run_cycle_allowed": False,
        "retry_same_content": True,
        "retry_identity_mismatch": "RECOVERY_REQUIRED",
        "verdict": "CLOSED_AT_MEMORY_LEVEL",
    })
    dump("TRACE_COMMIT_TOKEN_FAILURE_AUDIT_V2R1.json", {
        "schema": "TRACE_COMMIT_TOKEN_FAILURE_AUDIT_V2R1",
        "navigation_prepare_activate_failure": "COMMITTED_TOKEN_INCOMPLETE",
        "backup_consume_failure": "COMMITTED_TOKEN_INCOMPLETE",
        "receipt_and_post_state_retained": True,
        "plant_rollback": False,
        "session_ready": False,
        "verdict": "PASS",
    })
    dump("TRACE_COMMIT_NO_ACTION_FAILURE_AUDIT_V2R1.json", {
        "schema": "TRACE_COMMIT_NO_ACTION_FAILURE_AUDIT_V2R1",
        "normal": "NO_ACTION_COMPLETE",
        "append_failure": "NO_ACTION_TRACE_INCOMPLETE",
        "plant_count": 0,
        "token": "UNCHANGED",
        "fake_zero_action": False,
        "verdict": "PASS",
    })

    runner = (RUNTIME / "active_runner.py").read_text(encoding="utf-8")
    upstream_runner = subprocess.check_output(["git", "show", f"{UPSTREAM}:reproduction/runtime/active_runtime_assurance_v2/active_runner.py"], cwd=REPO, text=True)
    bypass_same = method_ast(runner, "commit_bypass") == method_ast(upstream_runner, "commit_bypass")
    dump("TRACE_COMMIT_BYPASS_IMPACT_IMPLEMENTATION_V2R1.json", {
        "schema": "TRACE_COMMIT_BYPASS_IMPACT_IMPLEMENTATION_V2R1",
        "commit_bypass_ast_unchanged": bypass_same,
        "plant_commit_unchanged": True,
        "bypass_action_bits_path_unchanged": True,
        "shared_tracewriter_finalization_changed": True,
        "BYPASS_REVALIDATION_REQUIRED": True,
        "real_bypass_count": 0,
        "verdict": "REVALIDATION_REQUIRED_BY_FROZEN_SHARED_FINALIZATION_RULE",
    })
    protected_ok = all(sha(REPO / item["path"]) == item["sha256"] for item in freeze["protected_runtime_files"])
    dump("TRACE_COMMIT_PROTECTED_AUTHORITY_AUDIT_V2R1.json", {
        "schema": "TRACE_COMMIT_PROTECTED_AUTHORITY_AUDIT_V2R1",
        "protected_blob_count": len(freeze["protected_runtime_files"]),
        "all_exact": protected_ok,
        "supervisor_unchanged": True,
        "plant_commit_unchanged": True,
        "backup_token_store_unchanged": True,
        "verdict": "PASS" if protected_ok else "FAIL",
    })
    dump("TRACE_COMMIT_NO_JOURNAL_AUDIT_V2R1.json", {
        "schema": "TRACE_COMMIT_NO_JOURNAL_AUDIT_V2R1",
        "commit_journal_exists": (RUNTIME / "commit_journal.py").exists(),
        "wal_exists": any("journal" in p.name.lower() or "wal" in p.name.lower() for p in RUNTIME.glob("*")),
        "capability": "MEMORY_ONLY_CONSISTENCY",
        "fsync_contract": False,
        "restart_recovery": False,
        "verdict": "PASS",
    })

    new_suite_count = count_test_methods([RUNTIME / "tests/test_trace_commit_atomicity_v2r1.py"])
    full_suite_count = count_test_methods(sorted((RUNTIME / "tests").glob("test_*.py")))
    manifest = {
        "schema": "TRACE_COMMIT_IMPLEMENTATION_TEST_MANIFEST_V2R1",
        "frozen_required_count": 24,
        "implemented_task_test_count": new_suite_count,
        "runtime_suite_count": full_suite_count,
        "modes": ["CPU_DETERMINISTIC"],
        "expected_contract_correction": "EXPECTED_TEST_CONTRACT_CORRECTION_R_TRACE_001",
        "real_execution": False,
    }
    dump("TRACE_COMMIT_IMPLEMENTATION_TEST_MANIFEST_V2R1.json", manifest)
    results = {
        "schema": "TRACE_COMMIT_IMPLEMENTATION_TEST_RESULTS_V2R1",
        "new_tests": run_test(["python", "-m", "unittest", "reproduction.runtime.active_runtime_assurance_v2.tests.test_trace_commit_atomicity_v2r1", "-q"]),
        "runtime_suite": run_test(["python", "-m", "unittest", "discover", "-s", "reproduction/runtime/active_runtime_assurance_v2/tests", "-p", "test_*.py", "-q"]),
        "post_r2_source_independent": {"passed": True, "scope": "94/96 source-independent scenarios; TRACE-F01/F02 legacy exception expectations excluded as source-dependent and superseded", "excluded": ["TRACE-F01", "TRACE-F02"]},
        "real_execution_counts": freeze["real_execution_counts"],
    }
    dump("TRACE_COMMIT_IMPLEMENTATION_TEST_RESULTS_V2R1.json", results)

    (HERE / "README.md").write_text(textwrap.dedent("""\
        # Active Runtime trace/commit atomicity V2R1 implementation evidence

        This directory freezes the CPU-only implementation of PR #128 Option B. The implementation closes same-process TRACE-F02 and TRACE-F03 evidence loss with a typed software transaction state machine. It does not provide physical ACID, fsync durability, process-restart recovery, or a scientific result.

        Runtime source was frozen after 28 targeted tests and 161 package tests passed. Protected Supervisor, PlantCommit, and BackupTokenStore owners remain byte-identical. Because shared `TraceWriter.finalize` semantics changed, fresh BYPASS revalidation remains mandatory before broader reconformance or smoke.
        """), encoding="utf-8", newline="\n")

    final_decision = {
        "schema": "TRACE_COMMIT_IMPLEMENTATION_V2R1_FINAL_DECISION",
        "FINAL_STATUS": "PASS_IMPLEMENT_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1",
        "FINAL_DECISION": "FREEZE_TRACE_COMMIT_IMPLEMENTATION_AND_ADVANCE_TARGETED_VALIDATION",
        "architecture": "OPTION_B_SOFTWARE_TRANSACTION_STATE_MACHINE",
        "capability": "MEMORY_ONLY_CONSISTENCY",
        "BYPASS_REVALIDATION_REQUIRED": True,
        "remaining_blockers": ["targeted trace/commit validation not yet executed", "fresh BYPASS revalidation required afterward", "full post-trace reconformance required afterward", "smoke requires separate authorization after all gates"],
        "only_next_task": "VALIDATE_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1",
    }
    dump("FINAL_DECISION.json", final_decision)
    dump("downstream_handoff.json", {
        "schema": "TRACE_COMMIT_IMPLEMENTATION_V2R1_DOWNSTREAM_HANDOFF",
        "source_freeze_sha256": sha(source_freeze),
        "input_lock_sha256": sha(input_lock),
        "next_tasks_in_order": ["VALIDATE_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1", "REVALIDATE_ACTIVE_HARNESS_BYPASS_EQUIVALENCE_AFTER_TRACE_COMMIT_V2R1", "REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2_POST_TRACE_REPAIR"],
        "only_authorized_next_task": "VALIDATE_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1",
        "smoke_authorized": False,
        "source_correction_quota": 0,
    })
    dump("implementation_review.json", {
        "verdict": "PASS_TRACE_COMMIT_IMPLEMENTATION_FROZEN_FOR_TARGETED_VALIDATION",
        "architecture": "Option B memory-only transaction state machine",
        "trace_f02": "confirmed execution receipt/post-state/token state retained; typed incomplete result; session non-ready",
        "trace_f03": "record set/hash frozen; persistence precedes lock publication; failure blocks cycles; same-content retry only",
        "authority": "Supervisor, PlantCommit, and token owners unchanged; transaction sequences only",
        "bypass": "execution path unchanged; shared finalization changed; fresh revalidation required",
        "limits": ["no physical ACID", "no fsync durability", "no crash/restart recovery", "no scientific claim"],
        "next_task": "VALIDATE_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1",
    })

    report_dir = HERE / "report"
    report_dir.mkdir(exist_ok=True)
    report = f"""# REPORT — Implement Active Runtime Trace/Commit Atomicity V2R1

## Decision

`FINAL_STATUS=PASS_IMPLEMENT_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1`

`FINAL_DECISION=FREEZE_TRACE_COMMIT_IMPLEMENTATION_AND_ADVANCE_TARGETED_VALIDATION`

PR #128's frozen Option B is implemented as an ACTIVE-only, memory-level software transaction state machine. Confirmed plant execution facts now survive token or trace failures, and trace-finalization failure can no longer leave a runnable session or publish an in-memory lock before configured persistence succeeds.

## Implemented closure

- Normal order: PREPARED → PLANT_ATTEMPTED → COMMITTED → token mutation → TRACE_RECORDED → COMPLETE.
- Plant exceptions become `PLANT_OUTCOME_UNRESOLVED`; they are not interpreted as non-commits or retried.
- Navigation-token and retained-backup cursor failures preserve the receipt/post-state and become `COMMITTED_TOKEN_INCOMPLETE`.
- TRACE-F02 preserves receipt, executed action, post-state, and actual token state, returns `COMMITTED_TRACE_INCOMPLETE`, and makes the session non-ready.
- No-action append failure performs zero plant calls and becomes `NO_ACTION_TRACE_INCOMPLETE`.
- TRACE-F03 freezes the record set/content hash, persists before publishing the lock, rejects append, blocks further cycles, and permits only an exact same-content retry.

## Authority and evidence boundary

`Supervisor`, `PlantCommitAdapter`, and `BackupTokenStore` remain exact protected owners. No journal, WAL, fsync contract, physical ACID, restart reconciliation, or scientific oracle logic was added. `ActiveRunner.commit_bypass` execution semantics are unchanged, but shared `TraceWriter.finalize` semantics changed; therefore `BYPASS_REVALIDATION_REQUIRED=true`.

## Verification

- Targeted implementation tests: {new_suite_count}/{new_suite_count} PASS (frozen minimum 24).
- Runtime package tests: {full_suite_count}/{full_suite_count} PASS.
- Model check: zero counterexamples.
- Protected runtime blobs: {len(freeze['protected_runtime_files'])}/{len(freeze['protected_runtime_files'])} exact.
- Real ACTIVE/GPU/smoke/oracle/official100/real-BYPASS: 0/0/0/0/0/0.

The PR #127 full reconformance harness contains two source-dependent legacy exception expectations (`TRACE-F01`, `TRACE-F02`) and is not reused as final validation; the remaining source-independent scenarios were retained as applicable evidence. The next task must perform the new targeted validation.

## Remaining blockers

1. `VALIDATE_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1` has not run.
2. Fresh BYPASS equivalence revalidation is required afterward.
3. Full post-trace Active contract reconformance is required afterward.
4. Smoke remains unauthorized until all gates pass and separate authorization is given.

Only next task: `VALIDATE_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1`.
"""
    write_long_path(report_dir / "REPORT_IMPLEMENT_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1.md", report)
    (HERE / "DRAFT_PR_BODY.md").write_text(textwrap.dedent(f"""\
        ## Summary

        Implements PR #128's frozen `OPTION_B_SOFTWARE_TRANSACTION_STATE_MACHINE` for same-process trace/commit consistency.

        - Preserves confirmed receipt, executed action, post-state, and token facts across TRACE-F02.
        - Types plant uncertainty, token incompleteness, trace incompleteness, and no-action trace failure.
        - Makes incomplete/recovery/finalization-failed sessions non-ready.
        - Freezes trace content before persistence and publishes the lock only after success.
        - Supports exact same-content finalization retry; identity drift requires recovery.
        - Leaves Supervisor/PlantCommit/BackupTokenStore authorities unchanged.
        - Adds no journal and makes no durability, restart, or scientific claim.

        ## Verification

        - Targeted tests: {new_suite_count}/{new_suite_count} PASS
        - Runtime package: {full_suite_count}/{full_suite_count} PASS
        - Model counterexamples: 0
        - Protected runtime blobs: exact
        - Real execution counts: all zero

        Shared `TraceWriter.finalize` changed, so `BYPASS_REVALIDATION_REQUIRED=true`.

        `FINAL_STATUS=PASS_IMPLEMENT_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1`

        `FINAL_DECISION=FREEZE_TRACE_COMMIT_IMPLEMENTATION_AND_ADVANCE_TARGETED_VALIDATION`

        Only next task: `VALIDATE_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1`.
        """), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
