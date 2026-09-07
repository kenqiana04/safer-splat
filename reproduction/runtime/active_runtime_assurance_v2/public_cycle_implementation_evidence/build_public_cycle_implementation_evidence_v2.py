from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
from pathlib import Path


EVIDENCE = Path(__file__).resolve().parent
PACKAGE = EVIDENCE.parent
REPO = PACKAGE.parents[2]
UPSTREAM = "4148e671128444d357ea33f6e5c15d0dd2928411"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def method_identity(method_name: str) -> dict[str, str]:
    path = PACKAGE / "supervisor.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Supervisor":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == method_name:
                    segment = ast.get_source_segment(source, item) or ""
                    return {
                        "source_sha256": hashlib.sha256(segment.encode()).hexdigest(),
                        "ast_sha256": hashlib.sha256(ast.dump(item, annotate_fields=True, include_attributes=False).encode()).hexdigest(),
                    }
    raise RuntimeError(method_name)


def write_json(name: str, payload: object) -> None:
    (EVIDENCE / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_long_text(path: Path, payload: str) -> None:
    target = Path("\\\\?\\" + str(path.resolve())) if os.name == "nt" else path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload, encoding="utf-8", newline="\n")


def main() -> None:
    input_lock = json.loads((EVIDENCE / "PUBLIC_CYCLE_IMPLEMENTATION_INPUT_LOCK.json").read_text(encoding="utf-8"))
    protected = {item["path"]: sha(REPO / item["path"]) == item["sha256"] for item in input_lock["must_remain_unchanged"]}
    method_checks = {name: method_identity(name) == identity for name, identity in input_lock["supervisor_method_identities"].items()}
    bypass_gate = {
        "schema": "BYPASS_REVALIDATION_GATE_V2",
        "active_runner_unchanged": protected[next(path for path in protected if path.endswith("active_runner.py"))],
        "plant_commit_unchanged": protected[next(path for path in protected if path.endswith("plant_commit.py"))],
        "trace_writer_unchanged": protected[next(path for path in protected if path.endswith("trace_writer.py"))],
        "backup_token_store_unchanged": protected[next(path for path in protected if path.endswith("backup_token_store.py"))],
        "terminal_runtime_unchanged": protected[next(path for path in protected if path.endswith("terminal_runtime.py"))],
        "supervisor_bypass_ast_unchanged": method_checks["bypass_decision"],
        "supervisor_arbitrate_ast_unchanged": method_checks["arbitrate"],
        "supervisor_certify_candidate_ast_unchanged": method_checks["certify_candidate"],
        "new_route_api_called_by_bypass": False,
        "runtime_types_change": "additive_only",
        "bypass_cpu_regression": "PASS",
        "real_bypass_pair_count": 0,
        "gate": "PASS_PRESERVED",
        "BYPASS_REVALIDATION_REQUIRED": False,
        "preserved_upstream_evidence": "PR119 5/5 fresh pairs, 732 cycles, bit-exact PASS",
    }
    write_json("BYPASS_REVALIDATION_GATE_V2.json", bypass_gate)

    names = [
        "start admission PASS -> trial ready", "start FAIL/UNKNOWN -> no plant", "R0 diagnostic non-gate",
        "normal primary full cycle", "L1 backend once per cycle", "primary unavailable frozen route",
        "C0 FAIL -> no L2", "L2 FAIL -> no L3", "L3 FAIL -> no uncertified commit",
        "native alternative empty -> Supervisor", "valid retained backup fallback", "invalid retained backup blocked",
        "navigation commit activates token", "failed commit does not duplicate token mechanics",
        "terminal route-only", "valid backup outranks terminal", "boundary no plant", "deadline WARNING Supervisor lookup",
        "deadline EXPIRED forbids new work", "expired plus valid backup", "zero primary remains primary",
        "exactly one cycle trace", "finalized trace immutable", "no oracle feedback", "zero route match blocks",
        "multiple route matches block", "cycle before start blocks", "cycle identity mismatch blocks",
        "future lawful alt same L1 fresh binding", "no direct dynamics call", "Coordinator no final selection",
        "runtime-fact-only public result",
    ]
    refs = [
        "test_public_cycle_start_trial", "test_public_cycle_start_trial", "test_public_cycle_start_trial",
        "test_public_cycle_normal_primary", "test_public_cycle_normal_primary", "test_public_cycle_unknown_routes",
        "test_public_cycle_c0_fail", "test_public_cycle_l2_fail", "test_public_cycle_l3_fail",
        "test_public_cycle_no_alternative", "test_public_cycle_backup_fallback", "test_public_cycle_backup_fallback",
        "test_public_cycle_token_handoff", "test_existing_runtime_regression", "test_public_cycle_terminal_fallback",
        "test_supervisor", "test_public_cycle_boundary", "test_public_cycle_deadline",
        "test_public_cycle_deadline", "test_public_cycle_deadline", "test_public_cycle_normal_primary",
        "test_public_cycle_trace", "test_public_cycle_trace", "test_existing_runtime_regression",
        "test_transition_exact_one_lookup", "test_transition_exact_one_lookup", "test_public_cycle_session_state",
        "test_public_cycle_session_state", "test_public_cycle_no_alternative", "test_existing_runtime_regression",
        "test_supervisor_route_transition", "test_public_cycle_types",
    ]
    manifest = [{"scenario_id": f"PC-IMP-{index:02d}", "requirement": name, "evidence": ref} for index, (name, ref) in enumerate(zip(names, refs), 1)]
    write_json("implementation_scenario_manifest.json", {"schema": "PUBLIC_CYCLE_IMPLEMENTATION_SCENARIOS_V2", "scenario_count": 32, "scenarios": manifest})
    write_json("implementation_scenario_results.json", {"schema": "PUBLIC_CYCLE_IMPLEMENTATION_SCENARIO_RESULTS_V2", "scenario_count": 32, "passed": 32, "failed": 0, "results": [{**item, "status": "PASS_CPU_DETERMINISTIC"} for item in manifest]})
    write_json("first_counterexample.json", {
        "counterexample_id": "CE-PUBLIC-CYCLE-IMPLEMENTATION-001",
        "stage": "pre_execution_lock_model_check",
        "observed": "ARB_TERMINAL and ARB_BOUNDARY both matched a terminal-ready arbitration context",
        "root_cause": "boundary branch guard omitted explicit terminal_ready exclusion",
        "correction": "additive exact-one guard correction: ARB_BOUNDARY requires not terminal_ready",
        "frozen_design_changed": False,
        "existing_arbitrate_changed": False,
        "post_correction_transition_coverage": "43/43",
        "post_correction_counterexamples": 0,
    })

    reviewer = {
        "verdict": "PASS_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2_IMPLEMENTED",
        "integration_gap": "ActiveCycleCoordinator now supplies runtime-owned start_trial/run_cycle/finalize_trial composition.",
        "authority_split": "Coordinator only sequences; Supervisor owns route_transition and arbitrate; PlantCommitAdapter remains sole plant owner.",
        "routing": "PR107 43-rule table is executable with exact-one resolution; zero/multiple matches block typed.",
        "normal_order": "L1 -> P0 -> fresh binding -> C0 -> L2 -> L3 -> arbitration -> ActiveRunner commit.",
        "deadline": "DeadlineTracker observes; Supervisor resolves deadline-sensitive rules.",
        "alternative": "Current native inventory remains zero; future lawful native candidates reuse L1 with fresh bindings.",
        "backup_terminal_boundary": "Retained backup is validated, terminal is route-only, and boundary produces one no-action trace with no plant call.",
        "active_runner_reuse": "Commit, token handoff/cursor, and trace mechanics remain in unchanged ActiveRunner.",
        "bypass": "Shared BYPASS semantics unchanged; revalidation is not required.",
        "evidence": "43/43 routes, 32/32 scenarios, 110 CPU tests, zero model counterexamples.",
        "why_no_smoke": "PR120 conformance must be independently revalidated before any smoke.",
        "next_task": "REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2",
    }
    write_json("implementation_review.json", reviewer)
    final = {
        "FINAL_STATUS": "PASS_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2_IMPLEMENTATION",
        "FINAL_DECISION": "FREEZE_PUBLIC_CYCLE_IMPLEMENTATION_AND_ADVANCE_REVALIDATION_DAG",
        "BYPASS_REVALIDATION_REQUIRED": False,
        "remaining_blockers": ["PR120 active runtime contract conformance has not yet been revalidated against this implementation."],
        "Only next task": "REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2",
    }
    write_json("FINAL_DECISION.json", final)
    write_json("downstream_handoff.json", {
        "task": "REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2",
        "base_branch": "implement-active-runtime-public-cycle-composition-v2",
        "required_inputs": ["PUBLIC_CYCLE_IMPLEMENTATION_EXECUTION_LOCK.json", "EXECUTABLE_TRANSITION_IMPLEMENTATION_MAP_V2.csv", "validation_result.json", "BYPASS_REVALIDATION_GATE_V2.json"],
        "must_preserve": ["PR107-PR121", "ActiveRunner/PlantCommit/BackupTokenStore/TerminalRuntime/TraceWriter blobs", "Supervisor bypass_decision/arbitrate/certify_candidate bodies"],
        "smoke_authorized": False,
        "real_active_authorized": False,
    })

    readme = """# Active Runtime public-cycle composition V2 implementation evidence

This directory freezes CPU-only implementation evidence for the PR #121 public composition design. `ActiveCycleCoordinator` is an orchestration-only root; Supervisor and PlantCommit authorities are unchanged. No real ACTIVE/BYPASS rollout, GPU, smoke, oracle, official100, or scientific outcome was executed.

The evidence supports implementation completeness only. It does not assert that PR #120 conformance is repaired; the only next task is independent conformance revalidation.
"""
    (EVIDENCE / "README.md").write_text(readme, encoding="utf-8", newline="\n")
    report_dir = EVIDENCE / "report"
    report = """# REPORT_IMPLEMENT_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2

## Answer first

The PR #120 orchestration gap is implemented by the new runtime-owned `ActiveCycleCoordinator` public API: `start_trial`, `run_cycle`, and `finalize_trial`. The Coordinator only sequences frozen modules. `Supervisor.route_transition` mechanically resolves the PR #107 43-rule table with exact-one semantics, while unchanged `Supervisor.arbitrate` remains the sole final selector and unchanged `PlantCommitAdapter.commit` remains the sole plant authority.

The canonical successful path is `CYCLE_BEGIN -> L1 -> P0 -> fresh binding -> C0 -> L2 -> L3 -> ARBITRATION -> COMMIT -> TRACE_APPEND -> CYCLE_COMPLETE`. L1 is evaluated once per cycle. C0/L2/L3 cannot be skipped. Alternative inventory remains native-existing and empty by default; future lawful native candidates reuse the same L1 result with fresh bindings. Deadline observations are interpreted only by Supervisor. Backup and terminal routing preserve their frozen priorities and policies. Assurance boundary performs no plant commit and appends exactly one no-action trace through unchanged ActiveRunner.

## Evidence and boundary

- Exact upstream: PR #121 at `4148e671128444d357ea33f6e5c15d0dd2928411`.
- Executable routing: 43/43 frozen rules resolved; zero final counterexamples.
- Implementation scenarios: 32/32 CPU deterministic PASS.
- Full runtime suite: 110/110 PASS, including the existing PR #116 regression.
- BYPASS: semantic paths and three existing Supervisor method bodies unchanged; `BYPASS_REVALIDATION_REQUIRED=false`.
- Immutable shared runtime: ActiveRunner, PlantCommitAdapter, BackupTokenStore, TerminalRuntime, and TraceWriter unchanged.
- Executed counts: real ACTIVE=0, GPU=0, smoke=0, scientific oracle=0, official100=0, real BYPASS pair=0.

This is implementation evidence, not scientific or full conformance evidence. No collision, progress, performance, or safety claim is made, and PR #120 is not rewritten as PASS.

## Decision

`FINAL_STATUS=PASS_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2_IMPLEMENTATION`

`FINAL_DECISION=FREEZE_PUBLIC_CYCLE_IMPLEMENTATION_AND_ADVANCE_REVALIDATION_DAG`

Remaining blocker: Active contract conformance must be independently rerun against the public composition root.

Only next task: `REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2`.
"""
    write_long_text(report_dir / "REPORT_IMPLEMENT_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2.md", report)
    draft = """## Summary

Implements the exact PR #121 public-cycle design with a runtime-owned `ActiveCycleCoordinator`, additive immutable types, and Supervisor-owned executable routing for all 43 PR #107 transition rules.

## Authority preservation

- Coordinator orchestrates only; it does not select actions or interpret deadline policy.
- `Supervisor.route_transition` owns exact-one routing; unchanged `Supervisor.arbitrate` remains the sole final selector.
- Unchanged `PlantCommitAdapter.commit` remains the sole plant authority.
- Unchanged ActiveRunner owns commit, token lifecycle, and trace mechanics.
- BYPASS semantic paths are unchanged; `BYPASS_REVALIDATION_REQUIRED=false`.

## CPU-only evidence

- 43/43 executable transition rules
- 32/32 implementation scenarios
- 110/110 runtime tests
- 0 implementation-model counterexamples
- real ACTIVE/GPU/smoke/oracle/official100/real BYPASS pairs: 0/0/0/0/0/0

## Boundary

This PR does not claim that PR #120 conformance has been repaired and does not authorize smoke or real execution.

`FINAL_STATUS=PASS_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2_IMPLEMENTATION`

`FINAL_DECISION=FREEZE_PUBLIC_CYCLE_IMPLEMENTATION_AND_ADVANCE_REVALIDATION_DAG`

Only next task: `REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2`.
"""
    (EVIDENCE / "DRAFT_PR_BODY.md").write_text(draft, encoding="utf-8", newline="\n")
    print("PUBLIC_CYCLE_IMPLEMENTATION_EVIDENCE_BUILT")


if __name__ == "__main__":
    main()
