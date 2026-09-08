from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
from pathlib import Path


TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
UPSTREAM = "72215ffb1b0a0bc9e7cc94155117ac8624ed0aa6"
BASE = "c38a51310767669e51ef6c87307c831405221277"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blob(path: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"{UPSTREAM}:{path}"], cwd=ROOT, text=True).strip()


def write_json(name: str, value: object) -> None:
    (TASK / name).parent.mkdir(parents=True, exist_ok=True)
    (TASK / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_md(name: str, value: str) -> None:
    (TASK / name).parent.mkdir(parents=True, exist_ok=True)
    (TASK / name).write_text(value.strip() + "\n", encoding="utf-8", newline="\n")


def write_csv(name: str, fields: list[str], rows: list[dict[str, object]]) -> None:
    path = TASK / name
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def phase_design() -> None:
    evidence = [
        "reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/report/REPORT_REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2_POST_R2.md",
        "reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/POST_R2_CONFORMANCE_FAILURE_REGISTER_V2.csv",
        "reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/POST_R2_TRACE_FAULT_SEMANTICS_V2.json",
        "reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/POST_R2_CONFORMANCE_SCENARIO_RESULTS_V2.json",
        "reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/POST_R2_ACTIVE_RUNTIME_COUNTEREXAMPLES_V2.json",
        "reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/validation_result.json",
        "reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/post_r2_active_runtime_contract_conformance_review.json",
        "reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/POST_R2_ACTIVE_RECONFORMANCE_INPUT_LOCK.json",
        "reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/POST_R2_ACTIVE_RECONFORMANCE_EXECUTION_LOCK.json",
    ]
    runtime = [
        "reproduction/runtime/active_runtime_assurance_v2/active_runner.py",
        "reproduction/runtime/active_runtime_assurance_v2/trace_writer.py",
        "reproduction/runtime/active_runtime_assurance_v2/active_cycle.py",
        "reproduction/runtime/active_runtime_assurance_v2/runtime_types.py",
        "reproduction/runtime/active_runtime_assurance_v2/plant_commit.py",
        "reproduction/runtime/active_runtime_assurance_v2/backup_token_store.py",
    ]
    authority = {
        "PR107": "a60665f3e29085cc18f1ee03828198074f52e4f0",
        "PR112": "8b47c5c9af05bbb022af4a964a6c8989231bc1bc",
        "PR114": "c924a959b1aa18b446a1d3c85afbe4f897604a84",
        "PR115": "44111d32031409338058e5da2f7e7a1f8d873323",
        "PR119": "b4ff579cf6a2bcffd0661cd39eb925aa4f3a5d27",
        "PR121": "4148e671128444d357ea33f6e5c15d0dd2928411",
    }
    write_json("TRACE_COMMIT_DESIGN_V2R1_INPUT_LOCK.json", {
        "schema": "TRACE_COMMIT_DESIGN_V2R1_INPUT_LOCK",
        "task": "DESIGN_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1",
        "pr127": {"number": 127, "state": "OPEN", "draft": True, "title": "[Draft] Revalidate active runtime contract conformance V2 after R1/R2", "branch": "revalidate-active-runtime-contract-conformance-v2-post-r2", "head": UPSTREAM, "base_branch": "repair-active-runtime-exception-and-unknown-routing-v2", "base_sha": BASE},
        "frozen_findings": {"closed_defects": ["D-AUTH-001", "D-TRANS-001", "D-EXC-001", "D-ALT-001"], "remaining_blocker": "R-TRACE-001", "trace_faults": ["TRACE-F02", "TRACE-F03"], "scenario_sweep": "94/96", "runtime_correction": 0},
        "evidence_sha256": {p: sha(ROOT / p) for p in evidence},
        "runtime_blob_sha1": {p: blob(p) for p in runtime},
        "frozen_authority_pr_heads": authority,
        "execution_counts": {"real_active": 0, "gpu": 0, "smoke": 0, "oracle": 0, "official100": 0, "real_bypass": 0},
        "runtime_mutation_authority": False,
        "scientific_result_mutation_authority": False,
    })

    write_json("CURRENT_ACTIVE_COMMIT_TRACE_ORDER_V2R1.json", {
        "schema": "CURRENT_ACTIVE_COMMIT_TRACE_ORDER_V2R1",
        "source": "active_runner.py:commit_active_decision",
        "actual_order": ["SupervisorDecision", "PlantCommitAdapter.commit", "BackupTokenStore.prepare_and_activate_OR_consume", "TraceWriter.append", "return_CommitReceipt"],
        "steps": [
            {"index": 1, "step": "SupervisorDecision", "owner": "Supervisor", "irreversible": False, "may_raise": False, "state_mutation": False, "evidence": "selection/routing fact", "durable": False, "rollback_authority": "none required"},
            {"index": 2, "step": "PlantCommitAdapter.commit", "owner": "PlantCommitAdapter", "irreversible": "operationally yes once committed", "may_raise": "authority validation may raise; transition exception returns committed=false", "state_mutation": "plant/dynamics side effect", "evidence": "CommitReceipt", "durable": False, "rollback_authority": "none"},
            {"index": 3, "step": "token mutation", "owner": "BackupTokenStore", "irreversible": "software state mutation", "may_raise": True, "state_mutation": True, "evidence": "token object only", "durable": False, "rollback_authority": "no physical rollback; no automatic token rollback"},
            {"index": 4, "step": "TraceWriter.append", "owner": "TraceWriter", "irreversible": "append-only memory fact", "may_raise": True, "state_mutation": True, "evidence": "TraceStepRecord", "durable": False, "rollback_authority": "none"},
            {"index": 5, "step": "return", "owner": "ActiveRunner", "irreversible": False, "may_raise": False, "state_mutation": False, "evidence": "receipt returned only if earlier steps did not raise", "durable": False, "rollback_authority": "none"},
        ],
        "trace_f02_window": "confirmed plant and token side effects occur before a raising trace append, so the receipt is not returned to the coordinator",
        "physical_atomicity_claim": False,
    })

    write_json("CURRENT_TRACE_FINALIZATION_ORDER_V2R1.json", {
        "schema": "CURRENT_TRACE_FINALIZATION_ORDER_V2R1",
        "actual_order": ["ActiveCycleCoordinator.finalize_trial", "ActiveRunner.finalize_trace", "TraceWriter.finalize", "canonicalize_records", "construct_and_publish_self._lock", "write_runtime_trace.jsonl", "write_runtime_trace_lock.json", "return_lock", "session_FINALIZED"],
        "in_memory_lock_created": "before either disk write",
        "runtime_trace_jsonl_written": "after self._lock publication",
        "runtime_trace_lock_written": "after runtime_trace.jsonl",
        "session_finalized": "only after finalize returns",
        "failure_state": {"trace_writer_lock": "may already be populated", "coordinator_session": "remains prior READY/BLOCKED state", "retry": "returns existing in-memory lock without proving disk persistence"},
        "trace_f03_window": "finalize exception escapes before coordinator session mutation; durable completion and retry result are ambiguous",
    })

    failures = [
        ("F1", "pre-plant validation/evidence failure", "NO", "UNCHANGED", "NONE", "BLOCKED", "ABORTED_BEFORE_PLANT", "NO", "NO", "no execution theorem"),
        ("F2", "PlantCommit committed=false", "NO", "UNCHANGED", "FAILURE_RECORD_REQUIRED", "BLOCKED", "PLANT_NOT_COMMITTED", "NO", "NO", "no execution theorem"),
        ("F3", "PlantCommit raises or outcome acknowledgement is uncertain", "UNKNOWN", "UNKNOWN", "INCOMPLETE", "RECOVERY_REQUIRED", "PLANT_OUTCOME_UNRESOLVED", "NO", "YES", "execution cannot be classified"),
        ("F4", "plant committed plus token mutation failure", "YES", "INCOMPLETE", "INCOMPLETE", "EVIDENCE_INCOMPLETE", "COMMITTED_TOKEN_INCOMPLETE", "NO", "YES", "execution fact retained"),
        ("F5", "plant committed plus trace append failure (TRACE-F02)", "YES", "ACTUAL_STATE_RETAINED", "INCOMPLETE", "EVIDENCE_INCOMPLETE", "COMMITTED_TRACE_INCOMPLETE", "NO", "YES", "execution fact retained"),
        ("F6", "no-action boundary plus trace append failure", "NO", "UNCHANGED", "INCOMPLETE", "EVIDENCE_INCOMPLETE", "NO_ACTION_TRACE_INCOMPLETE", "NO", "YES", "zero plant"),
        ("F7", "trace finalize failure (TRACE-F03)", "PRIOR_FACTS", "PRIOR_FACTS", "FINALIZATION_INCOMPLETE", "FINALIZATION_FAILED", "FINALIZATION_INCOMPLETE", "CONDITIONAL", "YES", "no new cycle"),
        ("F8", "partial finalize persistence failure", "PRIOR_FACTS", "PRIOR_FACTS", "FINALIZATION_INCOMPLETE", "FINALIZATION_FAILED", "FINALIZATION_INCOMPLETE", "CONDITIONAL", "YES", "durability not established"),
        ("F9", "process crash before plant", "NO_OR_UNKNOWN_IF_ATTEMPT_NOT_REACHED", "UNKNOWN", "INCOMPLETE", "RECOVERY_REQUIRED_AFTER_RESTART", "RECOVERY_REQUIRED", "NO", "YES", "outside memory-only guarantee"),
        ("F10", "process crash around plant/outcome acknowledgement", "UNKNOWN", "UNKNOWN", "INCOMPLETE", "RECOVERY_REQUIRED_AFTER_RESTART", "PLANT_OUTCOME_UNRESOLVED", "NO", "YES", "outside memory-only guarantee"),
        ("F11", "process crash after plant before trace completion", "YES_OR_UNKNOWN_AFTER_RESTART", "UNKNOWN", "INCOMPLETE", "RECOVERY_REQUIRED_AFTER_RESTART", "RECOVERY_REQUIRED", "NO", "YES", "requires durable journal for restart reconciliation"),
        ("F12", "process crash after append before finalize", "PRIOR_FACTS", "UNKNOWN_AFTER_RESTART", "UNFINALIZED", "RECOVERY_REQUIRED_AFTER_RESTART", "RECOVERY_REQUIRED", "NO", "YES", "requires durable trace contract"),
        ("F13", "BYPASS trace failure", "YES_IF_COMMIT_CONFIRMED", "NOT_APPLICABLE", "INCOMPLETE", "EVIDENCE_INCOMPLETE", "COMMITTED_TRACE_INCOMPLETE", "NO", "YES", "shared TraceWriter implications"),
    ]
    write_json("TRACE_COMMIT_FAILURE_MODEL_V2R1.json", {"schema": "TRACE_COMMIT_FAILURE_MODEL_V2R1", "failure_classes": [{"id": a, "fault": b, "plant_status": c, "token_status": d, "trace_status": e, "session_status": f, "typed_result": g, "retry_allowed": h, "recovery_required": i, "theorem_status": j} for a,b,c,d,e,f,g,h,i,j in failures], "process_crash_in_current_guarantee": False})

    write_json("TRACE_FINALIZE_IN_MEMORY_DURABILITY_HAZARD_V2R1.json", {
        "schema": "TRACE_FINALIZE_IN_MEMORY_DURABILITY_HAZARD_V2R1",
        "confirmed": True,
        "sequence": ["compute lines/hash", "assign self._lock", "write runtime_trace.jsonl", "write runtime_trace_lock.json"],
        "hazard": "a disk failure after self._lock assignment causes a later finalize call to return the cached lock without proving either durable artifact exists",
        "design_resolution_for_selected_architecture": ["do not publish candidate lock before configured persistence completes", "freeze records before persistence attempt", "return typed FINALIZATION_INCOMPLETE", "move session to FINALIZATION_FAILED", "permit only same-trial same-content evidence-only idempotent retry"],
        "does_not_claim": ["fsync durability", "atomic rename", "crash recovery", "physical transactionality"],
    })

    arch_rows = [
        {"option": "A_MINIMAL_TYPED_FAIL_CLOSE", "closes_TRACE_F02": "YES", "closes_TRACE_F03": "YES", "handles_process_crash": "NO", "handles_plant_outcome_uncertainty": "TYPED_ONLY", "session_fail_close": "YES", "implementation_complexity": "LOW", "new_modules": "NONE", "BYPASS_impact": "TRACE_WRITER_SHARED", "oracle_impact": "INCOMPLETE_INELIGIBLE", "smoke_eligibility": "CONDITIONAL", "scientific_benefit": "NONE", "overengineering_risk": "LOW", "frozen_requirement_fit": "INSUFFICIENT_STAGE_DISTINGUISHABILITY"},
        {"option": "B_SOFTWARE_TRANSACTION_STATE_MACHINE", "closes_TRACE_F02": "YES", "closes_TRACE_F03": "YES", "handles_process_crash": "NO", "handles_plant_outcome_uncertainty": "TYPED_RUNTIME_STATE", "session_fail_close": "YES", "implementation_complexity": "MEDIUM", "new_modules": "commit_transaction.py", "BYPASS_impact": "SHARED_TRACE_FINALIZATION_CHANGE", "oracle_impact": "INCOMPLETE_INELIGIBLE", "smoke_eligibility": "YES_AFTER_VALIDATION_AND_RECONFORMANCE", "scientific_benefit": "NONE", "overengineering_risk": "LOW", "frozen_requirement_fit": "SUFFICIENT"},
        {"option": "C_DURABLE_COMMIT_JOURNAL", "closes_TRACE_F02": "YES", "closes_TRACE_F03": "YES", "handles_process_crash": "YES_SUBJECT_TO_FILESYSTEM_ASSUMPTIONS", "handles_plant_outcome_uncertainty": "RECONCILIATION_REQUIRED", "session_fail_close": "YES", "implementation_complexity": "HIGH", "new_modules": "commit_transaction.py;commit_journal.py", "BYPASS_impact": "LIKELY_SHARED_TRANSACTION", "oracle_impact": "DURABLE_ELIGIBILITY_MARKERS", "smoke_eligibility": "YES_AFTER_PLATFORM_DURABILITY_VALIDATION", "scientific_benefit": "NONE", "overengineering_risk": "HIGH", "frozen_requirement_fit": "EXCEEDS_CURRENT_SCOPE"},
    ]
    write_csv("TRACE_COMMIT_ARCHITECTURE_COMPARISON_V2R1.csv", list(arch_rows[0]), arch_rows)
    write_json("TRACE_COMMIT_ARCHITECTURE_DECISION_V2R1.json", {
        "schema": "TRACE_COMMIT_ARCHITECTURE_DECISION_V2R1",
        "selected": "OPTION_B_SOFTWARE_TRANSACTION_STATE_MACHINE",
        "selection_method": {"mandatory": ["close TRACE-F02", "close TRACE-F03", "preserve execution fact", "typed plant outcome unresolved", "session fail-close", "explicit token/trace/finalization stages"], "minimize": ["new modules", "durability assumptions", "BYPASS coupling"], "excluded_requirement": "process crash/restart recovery is not in the current smoke theorem or frozen runtime contract"},
        "why_not_A": "A can catch same-process exceptions but does not provide the explicit ordered transaction-state evidence needed to distinguish committed/token-applied/trace-recorded and recovery-required states mechanically.",
        "why_not_C": "C adds filesystem durability and restart reconciliation assumptions not required for the currently authorized engineering smoke or frozen evaluation boundary.",
        "transaction_states": ["PREPARED", "PLANT_ATTEMPTED", "PLANT_NOT_COMMITTED", "PLANT_OUTCOME_UNRESOLVED", "COMMITTED", "TOKEN_APPLIED", "TRACE_RECORDED", "COMPLETE", "EVIDENCE_INCOMPLETE", "RECOVERY_REQUIRED"],
        "journal_decision": "JOURNAL_NOT_REQUIRED_FOR_CURRENT_CONTRACT",
        "journal_upgrade_triggers": ["formal experiment requires process-crash recovery", "restart reconciliation enters runtime theorem scope", "hardware execution acknowledgement must survive process restart"],
        "physical_atomicity_claim": False,
    })

    write_json("TRACE_COMMIT_SMOKE_DURABILITY_DECISION_V2R1.json", {
        "schema": "TRACE_COMMIT_SMOKE_DURABILITY_DECISION_V2R1",
        "decision": "SMOKE_ALLOWED_WITH_MEMORY_ONLY_FAIL_CLOSE",
        "reason": "The separately authorized engineering smoke evaluates in-process orchestration and typed fail-close behavior; process restart/crash recovery is not in its frozen evidence scope. Any incomplete trace remains evaluation-ineligible and stops the session.",
        "preconditions": ["implementation validation PASS", "BYPASS revalidation if shared semantics changed", "full post-trace contract reconformance PASS", "separate smoke authorization"],
        "excluded_claims": ["crash durability", "restart recovery", "hardware acknowledgement persistence", "real-time guarantee", "scientific efficacy"],
    })

    write_json("TRACE_COMMIT_IMPLEMENTATION_MODULE_DECISION_V2R1.json", {
        "schema": "TRACE_COMMIT_IMPLEMENTATION_MODULE_DECISION_V2R1",
        "selected_shape": "SHAPE_2_NEW_COMMIT_TRANSACTION",
        "reason": "A focused active-only transaction helper keeps ordered evidence state out of Coordinator and avoids inflating ActiveRunner while no durable journal is justified.",
        "new_modules": ["reproduction/runtime/active_runtime_assurance_v2/commit_transaction.py"],
        "modified_modules": ["active_runner.py", "active_cycle.py", "runtime_types.py", "trace_writer.py"],
        "unchanged_preferred": ["backup_token_store.py", "plant_commit.py", "supervisor.py"],
        "commit_journal": "NOT_CREATED",
    })

    write_md("NO_SILENT_UNTRACED_COMMIT_PROPERTY_V2R1.md", """
# No-silent-untraced-commit property V2R1

For every plant attempt, the runtime must retain a typed transaction result. If the plant confirms commitment, that result retains the `CommitReceipt`, selected and executed action identities, exact executed vector, and post-state identity even when token application, trace append, or finalization fails. A trace failure cannot erase execution, turn it into `committed=false`, or imply physical rollback.

`COMMITTED_TOKEN_INCOMPLETE` and `COMMITTED_TRACE_INCOMPLETE` are execution facts with incomplete evidence. Both force a non-runnable session and require reconciliation; neither is a safe stop. `PLANT_OUTCOME_UNRESOLVED` is distinct from both committed and not committed, forbids automatic retry, and requires manual or separately authorized reconciliation.

The selected software transaction state machine is memory-only. It does not claim physical ACID, crash durability, restart recovery, filesystem durability, or rollback authority.
""")
    write_md("TRACE_COMMIT_CONSISTENCY_PROPERTY_V2R1.md", """
# Trace/commit consistency property V2R1

Every authorized commit attempt terminates in exactly one typed class:

1. **No confirmed plant commit:** no executed-action claim is emitted; the result is `ABORTED_BEFORE_PLANT` or `PLANT_NOT_COMMITTED`.
2. **Confirmed plant commit:** the execution fact and receipt are retained, and evidence is either `COMPLETE`, `COMMITTED_TOKEN_INCOMPLETE`, or `COMMITTED_TRACE_INCOMPLETE`.
3. **Unresolved plant outcome:** the result is `PLANT_OUTCOME_UNRESOLVED` with `RECOVERY_REQUIRED`.

`CommitTransactionResult` is an immutable additive runtime fact with: attempt identity, plant outcome tri-state, committed tri-state, optional receipt, token status, trace status, evidence status, optional post-state, recovery-required flag, retry-allowed flag, failure reason, and software-transaction state. It is not a scientific outcome.

The evidence-status domain is: `COMPLETE`, `NO_ACTION_COMPLETE`, `ABORTED_BEFORE_PLANT`, `PLANT_NOT_COMMITTED`, `PLANT_OUTCOME_UNRESOLVED`, `COMMITTED_TOKEN_INCOMPLETE`, `COMMITTED_TRACE_INCOMPLETE`, `NO_ACTION_TRACE_INCOMPLETE`, `FINALIZATION_INCOMPLETE`, and `RECOVERY_REQUIRED`.

An incomplete or unresolved transaction never transitions directly to `READY`; automatic retry and automatic plant replay are forbidden; physical rollback is never fabricated; and a required incomplete trace is never oracle-eligible.
""")

    write_json("TRACE_FINALIZATION_RETRY_CONTRACT_V2R1.json", {
        "schema": "TRACE_FINALIZATION_RETRY_CONTRACT_V2R1",
        "selected_policy": "IDEMPOTENT_RETRY",
        "automatic_retry": False,
        "allowed_only_if": ["record set frozen", "same trial identity", "same canonical record content hash", "no new cycle or append", "failure is evidence-only persistence failure", "no plant operation occurs"],
        "on_first_attempt": ["session READY/BLOCKED -> FINALIZING", "freeze records and candidate hash", "persist according to configured memory-only/output mode", "publish lock only after configured persistence succeeds"],
        "on_failure": ["return/raise typed FINALIZATION_INCOMPLETE", "session -> FINALIZATION_FAILED", "append disabled", "run_cycle disabled", "retain frozen content hash"],
        "on_retry_success": "session -> FINALIZED with same content-addressed lock",
        "on_retry_identity_mismatch": "RECOVERY_REQUIRED; no retry",
    })

    write_json("TRACE_COMMIT_AUTHORITY_OWNERSHIP_V2R1.json", {
        "schema": "TRACE_COMMIT_AUTHORITY_OWNERSHIP_V2R1",
        "owners": {
            "Supervisor": "selection and routing only",
            "PlantCommitAdapter": "sole plant execution authority",
            "BackupTokenStore": "sole token mutation authority",
            "TraceWriter": "trace validation, append, freeze, and finalization authority",
            "ActiveRunner": "commit/evidence sequencing owner delegated to active-only CommitTransaction helper",
            "ActiveCycleCoordinator": "consumes typed transaction result and owns session lifecycle; no plant/token/trace transaction implementation",
            "Oracle": "posthoc read-only evaluator of complete locked traces only",
        },
        "authority_changes": "NONE",
    })

    write_json("TRACE_COMMIT_BYPASS_IMPACT_V2R1.json", {
        "schema": "TRACE_COMMIT_BYPASS_IMPACT_V2R1",
        "decision": "SHARED_TRACE_FINALIZATION_CHANGE",
        "active_commit_transaction": "ACTIVE_ONLY",
        "shared_change": "TraceWriter finalization lock-publication and typed failure semantics are shared by ACTIVE and BYPASS",
        "BYPASS_REVALIDATION_REQUIRED": True,
        "bypass_execution_policy_change_authorized": False,
        "required_downstream_order": ["IMPLEMENT_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1", "VALIDATE_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1", "REVALIDATE_ACTIVE_HARNESS_BYPASS_EQUIVALENCE_AFTER_TRACE_COMMIT_V2R1", "REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2_POST_TRACE_REPAIR", "ACTIVE_RUNTIME_SMOKE_V2 only after full PASS and separate authorization"],
    })

    write_json("TRACE_COMMIT_ORACLE_COMPATIBILITY_V2R1.json", {
        "schema": "TRACE_COMMIT_ORACLE_COMPATIBILITY_V2R1",
        "oracle_authority": "POSTHOC_READ_ONLY",
        "eligibility": {"COMPLETE_LOCKED_TRACE": "ELIGIBLE_SUBJECT_TO_PR114", "TRACE_INCOMPLETE": "EVALUATION_INELIGIBLE", "FINALIZATION_INCOMPLETE": "EVALUATION_INELIGIBLE", "PLANT_OUTCOME_UNRESOLVED": "EVALUATION_INELIGIBLE"},
        "forbidden_labels_for_incomplete": ["SAFE", "SUCCESS", "COLLISION_FREE", "NORMAL_FAIL"],
        "oracle_mutation": False,
    })

    fault_rows = []
    for a,b,c,d,e,f,g,h,i,j in failures:
        fault_rows.append({"fault_id": a, "fault": b, "plant_state": c, "token_state": d, "trace_state": e, "session_state": f, "typed_result": g, "retry": h, "recovery": i, "oracle_eligible": "NO" if g not in {"COMPLETE", "NO_ACTION_COMPLETE"} else "YES", "next_cycle": "NO" if f != "READY" else "YES", "claim_boundary": j})
    write_csv("TRACE_COMMIT_FAULT_MATRIX_V2R1.csv", list(fault_rows[0]), fault_rows)

    invariant_text = [
        "design-only; runtime diff is zero", "A/B/C compared without preselection", "no physical ACID claim", "selected is not executed until plant confirmation", "commit receipt preserved", "trace failure cannot erase execution fact", "token failure is typed", "trace failure is typed", "unresolved plant outcome is typed", "no automatic plant retry", "no fake rollback", "no fake safe stop", "incomplete evidence gives non-ready session", "finalize failure gives non-ready session", "boundary trace failure has zero plant", "token authority unchanged", "plant authority unchanged", "Supervisor authority unchanged", "oracle posthoc only", "BYPASS impact explicit", "memory-only capability explicit", "durable capability explicit", "smoke durability requirement explicit", "finalize retry explicit", "process-crash boundary explicit", "minimum sufficient architecture chosen", "future implementation tests frozen", "post-implementation reconformance required",
    ]
    write_json("TRACE_COMMIT_CONSISTENCY_INVARIANTS_V2R1.json", {"schema": "TRACE_COMMIT_CONSISTENCY_INVARIANTS_V2R1", "invariants": [{"id": f"TCC-{i:02d}", "statement": text, "required": True} for i,text in enumerate(invariant_text, 1)]})

    tests = [
        "precommit validation failure never calls plant", "plant committed=false is typed", "committed=true complete path", "token failure after commit", "TRACE-F02 append failure after commit", "boundary trace failure has zero plant", "TRACE-F03 finalize failure", "idempotent finalize retry", "run_cycle rejected after trace incomplete", "run_cycle rejected after token incomplete", "run_cycle rejected after unresolved plant", "receipt preserved after trace failure", "post-state preserved after trace failure", "no token rollback solely due to trace failure", "no fake zero action", "selected/executed identity remains exact", "incomplete trace is oracle-ineligible", "BYPASS shared-finalization revalidation gate", "memory-only semantics", "durable mode remains unsupported unless separately implemented", "crash-before-plant boundary", "crash-after-plant ambiguity boundary", "candidate lock not published before configured persistence", "finalization retry rejects changed content hash",
    ]
    write_json("TRACE_COMMIT_IMPLEMENTATION_TEST_PLAN_V2R1.json", {"schema": "TRACE_COMMIT_IMPLEMENTATION_TEST_PLAN_V2R1", "test_count": len(tests), "tests": [{"id": f"TC-TEST-{i:02d}", "test": text, "mode": "CPU_DETERMINISTIC", "real_execution": False} for i,text in enumerate(tests,1)]})

    scenario_names = [
        "primary commit complete", "backup commit complete", "terminal commit complete", "boundary complete", "preplant validation failure", "plant committed false", "plant authority exception before attempt", "plant outcome unresolved", "primary token prepare failure", "primary token activate failure", "backup token consume failure", "trace append failure after primary commit", "trace append failure after backup commit", "trace append failure after terminal commit", "boundary trace append failure", "finalize success memory-only", "finalize write runtime trace failure", "finalize lock write failure", "finalize retry same content", "finalize retry changed content rejected", "run after trace incomplete rejected", "run after token incomplete rejected", "run after plant unresolved rejected", "run after finalization failed rejected", "append after finalization failed rejected", "selected executed identity exact", "receipt retained after append failure", "post-state retained after append failure", "no token rollback on trace failure", "no plant replay on recovery", "oracle rejects trace incomplete", "oracle rejects finalize incomplete", "oracle rejects plant unresolved", "BYPASS append failure", "BYPASS finalize failure", "process crash before plant", "process crash around acknowledgement", "process crash after plant before trace", "process crash after trace before finalize", "memory-only capability boundary", "durable capability not implemented", "journal upgrade trigger", "shared TraceWriter revalidation gate", "Coordinator consumes typed transaction only", "Supervisor authority unchanged", "PlantCommit authority unchanged",
    ]
    scenario_rows = []
    for i,name in enumerate(scenario_names,1):
        incomplete = any(x in name for x in ["failure", "unresolved", "crash", "rejected"])
        scenario_rows.append({"scenario_id": f"TCC-SC-{i:02d}", "scenario": name, "selected_architecture": "B", "expected_session": "NON_READY_OR_RECOVERY" if incomplete else "READY_OR_FINALIZED", "expected_typed_class": "EXPLICIT", "plant_replay": "FORBIDDEN", "oracle_eligible": "NO" if incomplete else "CONDITIONAL_COMPLETE_TRACE", "runtime_execution": 0})
    write_csv("TRACE_COMMIT_DESIGN_SCENARIO_MATRIX_V2R1.csv", list(scenario_rows[0]), scenario_rows)

    change_rows = [
        {"file": "active_runner.py", "change_required": "YES", "exact_symbol": "ActiveRunner.commit_active_decision", "reason": "delegate active commit/evidence sequencing and return CommitTransactionResult", "authority_impact": "sequencing only", "BYPASS_impact": "NO if commit_bypass body unchanged", "architecture_dependent": "B", "required_tests": "TRACE-F02; token failures; complete path"},
        {"file": "active_cycle.py", "change_required": "YES", "exact_symbol": "ActiveCycleCoordinator._commit_or_boundary; finalize_trial; session guards", "reason": "consume typed transaction and enforce non-ready/finalization states", "authority_impact": "session lifecycle only", "BYPASS_impact": "NO", "architecture_dependent": "B", "required_tests": "session fail-close; TRACE-F03"},
        {"file": "runtime_types.py", "change_required": "YES_ADDITIVE", "exact_symbol": "CommitTransactionResult; PlantOutcome; EvidenceStatus; CommitTransactionState; TrialSessionStatus", "reason": "typed execution/evidence/session facts", "authority_impact": "none", "BYPASS_impact": "serialization compatibility audit", "architecture_dependent": "B", "required_tests": "enum/dataclass immutability"},
        {"file": "trace_writer.py", "change_required": "YES", "exact_symbol": "TraceWriter.finalize", "reason": "freeze records, delay lock publication, typed retry-safe finalization", "authority_impact": "trace authority unchanged", "BYPASS_impact": "YES_SHARED_FINALIZATION", "architecture_dependent": "A/B/C", "required_tests": "TRACE-F03; retry; BYPASS revalidation"},
        {"file": "commit_transaction.py", "change_required": "YES_NEW", "exact_symbol": "ActiveCommitTransaction", "reason": "ordered memory-level state machine and fact retention", "authority_impact": "no policy/plant/token/trace authority", "BYPASS_impact": "ACTIVE_ONLY", "architecture_dependent": "B", "required_tests": "state transitions; fault matrix"},
        {"file": "backup_token_store.py", "change_required": "NO", "exact_symbol": "existing mutation methods", "reason": "sole token owner reused", "authority_impact": "unchanged", "BYPASS_impact": "none", "architecture_dependent": "NO", "required_tests": "existing regression"},
        {"file": "plant_commit.py", "change_required": "NO", "exact_symbol": "PlantCommitAdapter.commit", "reason": "sole plant owner reused", "authority_impact": "unchanged", "BYPASS_impact": "none", "architecture_dependent": "NO", "required_tests": "existing regression"},
        {"file": "supervisor.py", "change_required": "NO", "exact_symbol": "route_transition; arbitrate", "reason": "routing/selection unaffected", "authority_impact": "unchanged", "BYPASS_impact": "none", "architecture_dependent": "NO", "required_tests": "existing regression"},
        {"file": "commit_journal.py", "change_required": "NO", "exact_symbol": "not created", "reason": "durable crash recovery outside current contract", "authority_impact": "none", "BYPASS_impact": "none", "architecture_dependent": "C_ONLY", "required_tests": "none in V2R1"},
        {"file": "tests/test_trace_commit_atomicity_v2r1.py", "change_required": "YES_NEW", "exact_symbol": "future test suite", "reason": "mechanically test frozen fault matrix", "authority_impact": "none", "BYPASS_impact": "gate only", "architecture_dependent": "B", "required_tests": "TC-TEST-01..24"},
    ]
    write_csv("TRACE_COMMIT_IMPLEMENTATION_CHANGE_MANIFEST_V2R1.csv", list(change_rows[0]), change_rows)

    write_md("README.md", """
# Active Runtime Trace/Commit Atomicity V2R1 — design only

This directory freezes the smallest sufficient software consistency contract for PR #127's R-TRACE-001 blocker. The mechanical choice is **Option B: an in-memory software transaction state machine**. It retains confirmed execution facts across token/trace failures and moves incomplete or unresolved sessions out of `READY`; it does not claim physical ACID, process-crash durability, restart recovery, or filesystem durability.

The current engineering smoke may proceed with memory-only fail-close only after implementation validation, required BYPASS revalidation, complete post-trace reconformance, and separate smoke authorization. A durable journal is deferred until crash/restart recovery enters the formal runtime scope.
""")


def phase_lock() -> None:
    names = [
        "TRACE_COMMIT_ARCHITECTURE_COMPARISON_V2R1.csv",
        "TRACE_COMMIT_ARCHITECTURE_DECISION_V2R1.json",
        "TRACE_COMMIT_FAILURE_MODEL_V2R1.json",
        "TRACE_COMMIT_DESIGN_SCENARIO_MATRIX_V2R1.csv",
        "TRACE_COMMIT_CONSISTENCY_INVARIANTS_V2R1.json",
        "model_check_trace_commit_consistency_design_v2r1.py",
        "validate_trace_commit_consistency_design_v2r1.py",
    ]
    write_json("TRACE_COMMIT_DESIGN_V2R1_EXECUTION_LOCK.json", {
        "schema": "TRACE_COMMIT_DESIGN_V2R1_EXECUTION_LOCK",
        "upstream": UPSTREAM,
        "locked_sha256": {name: sha(TASK / name) for name in names},
        "architecture": "OPTION_B_SOFTWARE_TRANSACTION_STATE_MACHINE",
        "design_only": True,
        "real_execution_counts": {"real_active": 0, "gpu": 0, "smoke": 0, "oracle": 0, "official100": 0, "real_bypass": 0},
    })


def phase_final() -> None:
    model = json.loads((TASK / "TRACE_COMMIT_DESIGN_MODEL_CHECK_V2R1.json").read_text())
    validation = json.loads((TASK / "validation_result.json").read_text())
    final_status = "PASS_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1_DESIGN" if model["counterexample_count"] == 0 and validation["failed_count"] == 0 else "BLOCKED_TRACE_COMMIT_DESIGN_BY_MODEL_COUNTEREXAMPLE"
    final_decision = "FREEZE_TRACE_COMMIT_CONSISTENCY_V2R1_AND_ADVANCE_IMPLEMENTATION" if final_status.startswith("PASS") else "DO_NOT_IMPLEMENT_OR_SMOKE"
    write_json("trace_commit_consistency_design_v2r1_review.json", {
        "schema": "TRACE_COMMIT_CONSISTENCY_DESIGN_V2R1_REVIEW",
        "verdict": "PASS_TRACE_COMMIT_CONSISTENCY_DESIGN_V2R1_FROZEN" if final_status.startswith("PASS") else "BLOCKED_TRACE_COMMIT_CONSISTENCY_DESIGN_V2R1",
        "answers": {
            "TRACE_F02_root": "Plant and token mutate before append; append failure escapes and hides the receipt from Coordinator.",
            "TRACE_F03_root": "TraceWriter publishes _lock before disk persistence and Coordinator changes session only after finalize returns.",
            "current_order": "decision -> plant -> token -> trace -> return",
            "physical_boundary": "No software design claims physical rollback or ACID.",
            "architecture_comparison": "A closes catches but lacks stage-state evidence; B closes same-process faults; C adds unneeded crash durability.",
            "selected": "B software transaction state machine",
            "plant_unknown": "PLANT_OUTCOME_UNRESOLVED; no retry or next cycle.",
            "token_trace_session": "Failures retain receipt/post-state and force EVIDENCE_INCOMPLETE/RECOVERY_REQUIRED.",
            "finalize_retry": "Evidence-only, explicit idempotent retry with same trial/content hash; never automatic.",
            "memory_durable": "Memory-only is current; durable restart recovery is explicitly unsupported.",
            "smoke": "SMOKE_ALLOWED_WITH_MEMORY_ONLY_FAIL_CLOSE after all gates and separate authorization.",
            "journal": "Not required until crash/restart durability enters scope.",
            "bypass": "Shared TraceWriter finalization change requires fresh BYPASS revalidation.",
            "oracle": "Incomplete/unresolved evidence is EVALUATION_INELIGIBLE.",
            "implementation": "new commit_transaction.py; additive types; active runner/coordinator/TraceWriter changes; plant/token/Supervisor unchanged.",
            "next": "IMPLEMENT_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1",
        },
        "critical_blockers": [],
    })
    write_json("FINAL_DECISION.json", {"schema": "TRACE_COMMIT_DESIGN_V2R1_FINAL_DECISION", "FINAL_STATUS": final_status, "FINAL_DECISION": final_decision, "selected_architecture": "OPTION_B_SOFTWARE_TRANSACTION_STATE_MACHINE", "smoke_durability_decision": "SMOKE_ALLOWED_WITH_MEMORY_ONLY_FAIL_CLOSE", "journal": "JOURNAL_NOT_REQUIRED_FOR_CURRENT_CONTRACT", "BYPASS_REVALIDATION_REQUIRED": True, "Only next task": "IMPLEMENT_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1", "execution_counts": {"real_active": 0, "gpu": 0, "smoke": 0, "oracle": 0, "official100": 0, "real_bypass": 0}})
    write_json("downstream_handoff.json", {"schema": "TRACE_COMMIT_DESIGN_V2R1_DOWNSTREAM_HANDOFF", "status": "READY_FOR_IMPLEMENTATION_ONLY" if final_status.startswith("PASS") else "BLOCKED", "selected_architecture": "OPTION_B_SOFTWARE_TRANSACTION_STATE_MACHINE", "only_next_task": "IMPLEMENT_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1", "future_files": ["commit_transaction.py", "runtime_types.py (additive)", "active_runner.py", "active_cycle.py", "trace_writer.py", "tests/test_trace_commit_atomicity_v2r1.py"], "must_preserve": ["Supervisor authority", "PlantCommitAdapter authority", "BackupTokenStore authority", "oracle isolation", "execution facts", "no automatic replay"], "post_implementation_ladder": ["VALIDATE_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1", "REVALIDATE_ACTIVE_HARNESS_BYPASS_EQUIVALENCE_AFTER_TRACE_COMMIT_V2R1", "REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2_POST_TRACE_REPAIR", "ACTIVE_RUNTIME_SMOKE_V2 after full PASS and separate authorization"]})
    body = f"""# Summary

Design-only closure for PR #127's sole remaining blocker, R-TRACE-001. TRACE-F02 and TRACE-F03 are preserved unchanged. The selected minimum sufficient architecture is an in-memory software transaction state machine (Option B), not a physical transaction and not a durable journal.

## Frozen decisions

- Preserve confirmed receipt/action/post-state across token or trace failure.
- Typed `PLANT_OUTCOME_UNRESOLVED`; no automatic replay.
- Incomplete evidence/finalization makes the session non-runnable and oracle-ineligible.
- Explicit idempotent evidence-only finalization retry with identical trial/content hash.
- `SMOKE_ALLOWED_WITH_MEMORY_ONLY_FAIL_CLOSE`, only after implementation validation, BYPASS revalidation, full reconformance, and separate authorization.
- `JOURNAL_NOT_REQUIRED_FOR_CURRENT_CONTRACT`; process-crash/restart recovery remains outside scope.
- Shared TraceWriter finalization semantics imply `BYPASS_REVALIDATION_REQUIRED=true`.

## Evidence

- Model counterexamples: {model['counterexample_count']}
- Validator: {validation['status']} ({validation['passed_count']}/{validation['check_count']})
- Runtime/production diff: 0
- Real ACTIVE/GPU/smoke/oracle/official100/real-BYPASS: 0/0/0/0/0/0

`FINAL_STATUS={final_status}`

`FINAL_DECISION={final_decision}`

Only next task: `IMPLEMENT_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1`
"""
    write_md("DRAFT_PR_BODY.md", body)
    report = f"""# Report: Design Active Runtime Trace/Commit Atomicity V2R1

## Answer-first decision

`FINAL_STATUS={final_status}`

`FINAL_DECISION={final_decision}`

TRACE-F02 is caused by the actual plant-first sequence: the plant and token can mutate before `TraceWriter.append`, so a raising append loses the returned receipt at the Coordinator boundary without undoing execution. TRACE-F03 is caused by `TraceWriter.finalize` publishing `_lock` before disk writes while Coordinator changes the session to FINALIZED only after the call returns.

The mechanically selected architecture is **Option B — SOFTWARE_TRANSACTION_STATE_MACHINE**. It is the minimum option that exposes PREPARED/COMMITTED/TOKEN_APPLIED/TRACE_RECORDED/COMPLETE/RECOVERY_REQUIRED stages, retains confirmed execution facts, and closes the two same-process faults without importing durable filesystem assumptions. Option A lacks mechanically distinguishable transaction stages; Option C is deferred because process-crash/restart recovery is outside the current engineering-smoke evidence boundary.

## Frozen semantics

- Current order: SupervisorDecision -> PlantCommit -> token mutation -> trace append -> return.
- Current finalize order: construct and publish `_lock` -> write trace -> write lock -> return -> session FINALIZED.
- Confirmed commit is never erased by trace/token/finalize failure; no fake rollback or safe-stop claim is allowed.
- `PLANT_OUTCOME_UNRESOLVED` forbids retry and ordinary next-cycle execution.
- `COMMITTED_TOKEN_INCOMPLETE`, `COMMITTED_TRACE_INCOMPLETE`, and `FINALIZATION_INCOMPLETE` force non-ready session states.
- Finalization retry is explicit and idempotent only for an immutable same-trial, same-content record set.
- Memory-only consistency is supported; crash durability and restart recovery are not.
- Smoke decision: `SMOKE_ALLOWED_WITH_MEMORY_ONLY_FAIL_CLOSE`, subject to all downstream gates and separate authorization.
- Journal decision: `JOURNAL_NOT_REQUIRED_FOR_CURRENT_CONTRACT`.
- Shared TraceWriter finalization change means `BYPASS_REVALIDATION_REQUIRED=true`.
- Incomplete or unresolved evidence is `EVALUATION_INELIGIBLE` for the posthoc oracle.

## Design verification

- Failure classes: 13.
- Architecture options compared: 3.
- Invariants: 28.
- Future implementation tests: 24.
- Symbolic scenarios: 46.
- Model counterexamples: {model['counterexample_count']}.
- Validator: {validation['status']} ({validation['passed_count']}/{validation['check_count']}).
- Runtime and production source diff: 0.
- Real ACTIVE/GPU/smoke/oracle/official100/real-BYPASS: 0/0/0/0/0/0.

## Implementation boundary

The next task may add `commit_transaction.py`, additive result/state types, and minimal ActiveRunner/Coordinator/TraceWriter wiring. PlantCommitAdapter, BackupTokenStore authority, Supervisor authority, and oracle logic remain unchanged. No implementation was performed here.

Only next task: `IMPLEMENT_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1`.
"""
    write_md("report/REPORT_DESIGN_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1.md", report)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["design", "lock", "final"])
    args = parser.parse_args()
    {"design": phase_design, "lock": phase_lock, "final": phase_final}[args.phase]()
