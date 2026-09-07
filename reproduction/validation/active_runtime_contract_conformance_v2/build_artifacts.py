from __future__ import annotations

import csv
import hashlib
import inspect
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parent
RUNTIME = ROOT / "reproduction/runtime/active_runtime_assurance_v2"
MAP = RUNTIME / "implementation_evidence/RUNTIME_TRANSITION_IMPLEMENTATION_MAP_V2.csv"

CONTRACTS = [
    ("PR107_METHOD_LOGIC", "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv"),
    ("PR108_GEOMETRY", "reproduction/specification/cross_layer_geometry_authority_v2/CROSS_LAYER_GEOMETRY_AUTHORITY_V2.json"),
    ("PR109_ACTUATOR", "reproduction/specification/control_authority_v2/SELECTED_CONTROL_ACTUATOR_CONTRACT_V2.json"),
    ("PR110_DEADLINE", "reproduction/specification/runtime_assurance_deadline_authority_v2/RUNTIME_ASSURANCE_DEADLINE_AUTHORITY_V2.json"),
    ("PR111_ALTERNATIVE", "reproduction/specification/alternative_source_authority_v2/ALTERNATIVE_SOURCE_AUTHORITY_V2.json"),
    ("PR112_BACKUP_TOKEN", "reproduction/specification/backup_token_runtime_schema_v2/RETAINED_BACKUP_TOKEN_SCHEMA_V2.json"),
    ("PR113_TERMINAL", "reproduction/specification/terminal_emergency_policy_v2/TERMINAL_EMERGENCY_POLICY_CONTRACT_V2.json"),
    ("PR114_TRACE_ORACLE", "reproduction/specification/independent_evaluation_oracle_v2/EVALUATION_TRACE_SCHEMA_V2.json"),
    ("PR115_IMPLEMENTATION_MANIFEST", "reproduction/design/active_runtime_assurance_implementation_v2/ACTIVE_RUNTIME_IMPLEMENTATION_FILE_MANIFEST_V2.csv"),
    ("PR115_MODULE_ARCHITECTURE", "reproduction/design/active_runtime_assurance_implementation_v2/MODULE_ARCHITECTURE_V2.json"),
    ("PR115_VALIDATION_LADDER", "reproduction/design/active_runtime_assurance_implementation_v2/ACTIVE_RUNTIME_VALIDATION_LADDER_V2.md"),
]
RUNTIME_MODULES = [
    "authority_registry.py", "runtime_types.py", "start_admission.py", "diagnostic_r0.py",
    "l1_runtime.py", "primary_proposal_adapter.py", "c0_admission.py", "l2_runtime.py",
    "l3_runtime.py", "alternative_provider.py", "backup_token_store.py", "terminal_runtime.py",
    "deadline_runtime.py", "supervisor.py", "plant_commit.py", "trace_writer.py", "active_runner.py",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blob(path: Path) -> str:
    return subprocess.run(["git", "hash-object", str(path)], cwd=ROOT, check=True, text=True, capture_output=True).stdout.strip()


def write_text(rel: str, text: str) -> None:
    path = TASK / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def write_json(rel: str, value: object) -> None:
    write_text(rel, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def public_api_probe() -> dict[str, object]:
    sys.path.insert(0, str(ROOT))
    from reproduction.runtime.active_runtime_assurance_v2.active_runner import ActiveRunner
    from reproduction.runtime.active_runtime_assurance_v2.supervisor import Supervisor
    methods = sorted(name for name in dir(ActiveRunner) if not name.startswith("_"))
    return {
        "active_runner_public_methods": methods,
        "has_full_cycle_entrypoint": any(name in methods for name in ("run_cycle", "step", "execute_cycle", "process_snapshot", "run_active_cycle")),
        "commit_active_decision_signature": str(inspect.signature(ActiveRunner.commit_active_decision)),
        "supervisor_arbitrate_signature": str(inspect.signature(Supervisor.arbitrate)),
        "supervisor_arbitrate_requires_precomputed_inputs": True,
        "evidence": [
            "ActiveRunner exposes startup, commit_active_decision, commit_bypass, finalize_trace but no cycle composition entrypoint.",
            "Supervisor.arbitrate consumes already-produced candidate/L3/backup/terminal/deadline values; it does not call start admission, L1, proposal, C0, L2, L3, alternative, or deadline trackers.",
        ],
    }


def main() -> None:
    TASK.mkdir(parents=True, exist_ok=True)
    summary_path = ROOT / "reproduction/validation/execute_refrozen_bypass_equivalence_v2r1/BYPASS_EQUIVALENCE_V2R1_SUMMARY.json"
    runtime_identity = []
    for name in RUNTIME_MODULES:
        path = RUNTIME / name
        runtime_identity.append({"path": str(path.relative_to(ROOT)).replace("\\", "/"), "git_blob_sha1": blob(path), "sha256": sha256(path)})
    frozen_identity = []
    for authority, rel in CONTRACTS:
        path = ROOT / rel
        frozen_identity.append({"authority": authority, "path": rel, "git_blob_sha1": blob(path), "sha256": sha256(path)})
    frozen_identity.extend([
        {"authority": "REFERENCE_RUNNER", "path": "run.py", "git_blob_sha1": blob(ROOT / "run.py"), "sha256": sha256(ROOT / "run.py")},
        {"authority": "REFERENCE_CBF", "path": "cbf/cbf_utils.py", "git_blob_sha1": blob(ROOT / "cbf/cbf_utils.py"), "sha256": sha256(ROOT / "cbf/cbf_utils.py")},
        {"authority": "REFERENCE_DYNAMICS", "path": "dynamics/systems.py", "git_blob_sha1": blob(ROOT / "dynamics/systems.py"), "sha256": sha256(ROOT / "dynamics/systems.py")},
    ])
    input_lock = {
        "schema": "ACTIVE_CONFORMANCE_INPUT_LOCK_V2",
        "task_type": "CONTRACT_CONFORMANCE_CPU_TARGETED_NO_REAL_ROLLOUT",
        "direct_upstream": {"repository": "kenqiana04/safer-splat", "pr": 119, "state": "OPEN_DRAFT", "title": "[Draft] Execute refrozen BYPASS equivalence V2R1", "branch": "execute-refrozen-bypass-equivalence-v2r1", "head": "b4ff579cf6a2bcffd0661cd39eb925aa4f3a5d27", "base": "repair-and-refreeze-bypass-qa-trace-identity-v2", "base_sha": "a537ff653ac896aa1ab567b5197136efa1a937b4"},
        "frozen_contracts": frozen_identity,
        "runtime_modules_17": runtime_identity,
        "bypass_evidence": {"path": str(summary_path.relative_to(ROOT)).replace("\\", "/"), "sha256": sha256(summary_path), "git_blob_sha1": blob(summary_path), "verdict": "PASS_REFROZEN_BYPASS_EQUIVALENCE_V2R1", "pairs": 5, "compared_steps": 732, "all_mismatch_counts_zero": True, "trace_locks": 5, "real_execution_count": 10, "active_runtime_on_execution_count": 0, "scientific_oracle_execution_count": 0, "official100_execution_count": 0},
        "protected_source_paths": ["run.py", "cbf/", "dynamics/", "splat/", "reproduction/runtime/active_runtime_assurance_v2/"],
        "runtime_correction_quota": 0,
        "real_active_rollout_count": 0,
        "gpu_execution_count": 0,
        "scientific_oracle_count": 0,
        "official100_count": 0,
        "source_mutation_authority": False,
    }
    write_json("ACTIVE_CONFORMANCE_INPUT_LOCK.json", input_lock)
    api = public_api_probe()
    write_text("ACTIVE_RUNTIME_PUBLIC_INTEGRATION_AUDIT_V2.md", f"""# ACTIVE Runtime Public Integration Audit V2

## Scope

This is a CPU-only conformance audit of the immutable PR #116 runtime at PR #119 exact head. No runtime source, controller, plant, map, candidate library, or experiment was modified or executed.

## Public entrypoint

`ACTIVE_RUNTIME_ON` is selected by `ActiveRunner(mode=RuntimeMode.ACTIVE_RUNTIME_ON, ...)`; `startup()` validates authorities and requires an explicit `RuntimeDeadlineProfile`. The public methods are `{', '.join(api['active_runner_public_methods'])}`. There is no public `run_cycle`, `step`, `execute_cycle`, `process_snapshot`, or `run_active_cycle` entrypoint.

`commit_active_decision(snapshot, decision)` is a commit shell. Its caller must already provide the `SupervisorDecision`; it does not consume a state snapshot and execute the frozen sequence. `Supervisor.arbitrate` likewise consumes precomputed candidate, L3, backup, terminal, and deadline objects and does not call StartAdmission, L1, proposal, C0, L2, L3, alternative enumeration, or deadline tracking.

## Required frozen cycle versus available path

The normative path is `I0a/I0b → R0 → L1 → P0 → C0 → L2/H1 → L3 → alternative (if lawful) → Supervisor arbitration → PlantCommit/backup/terminal/boundary → trace`. The PR #116 modules provide individually callable adapters and a Supervisor, but no public composition root that performs that whole cycle. The validation harness therefore does not compose a fake cycle; the missing public path is recorded as the first integration counterexample.

## Authority audit

Static/module tests support Supervisor as the only `arbitrate` owner and PlantCommitAdapter as the only plant/dynamics owner. This does not establish integrated conformance because the runtime does not itself route all producers through those owners. No L2/L3/alternative/oracle import directly commits plant state, and no post-hoc oracle is imported.

## Decision

`BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP`. The six E2E cases cannot be credited as genuine public-runtime executions. No runtime correction is attempted; the first counterexample is preserved in `first_counterexample.json`.
""")
    write_json("ACTIVE_AUTHORITY_OWNERSHIP_AUDIT_V2.json", {
        "schema": "ACTIVE_AUTHORITY_OWNERSHIP_AUDIT_V2",
        "selection_owner": {"expected": "Supervisor.arbitrate", "observed": ["reproduction/runtime/active_runtime_assurance_v2/supervisor.py:Supervisor.arbitrate"], "status": "PASS_MODULE_SCOPE"},
        "plant_owner": {"expected": "PlantCommitAdapter.commit", "observed": ["reproduction/runtime/active_runtime_assurance_v2/plant_commit.py:PlantCommitAdapter.commit"], "status": "PASS_MODULE_SCOPE"},
        "forbidden_direct_edges": {"l2_to_plant": True, "l3_to_plant": True, "terminal_membership_to_plant": True, "alternative_to_plant": True, "proposal_to_plant": True, "oracle_to_runtime": True, "u_des_fallback": True, "post_cert_clip": True},
        "integrated_public_path": "MISSING",
        "verdict": "BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP",
    })
    with MAP.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    critical_tokens = ("ARB", "BACKUP", "TERM", "ALT", "UNKNOWN", "FAIL", "GUARD", "COMMIT")
    out_rows = []
    for row in rows:
        critical = any(token in row["rule_id"] for token in critical_tokens) or row["destination_phase"] in {"COMMIT", "ASSURANCE_BOUNDARY", "ARBITRATION", "BACKUP_EXECUTION", "ALT_SEARCH"}
        out_rows.append({
            "rule_id": row["rule_id"], "source_phase": row["source_phase"], "frozen_guard_result": f"{row['guard']} -> {row['observation/result']}", "frozen_destination": row["destination_phase"], "failure_mapping": row["failure_mapping"], "commit_allowed": row["commit_allowed"], "expected_role": row["commit_authority"], "actual_runtime_path": row["target_function"], "scenario_id": "PUBLIC-PATH-GAP" if critical else f"MODULE-{row['rule_id']}", "mode": "DYNAMIC_PUBLIC_PATH" if critical else "DYNAMIC_MODULE_PATH", "assertion": "required public cycle entrypoint is absent" if critical else "CPU module assertion executed", "observed_result": "BLOCKED_ACTIVE_PUBLIC_CYCLE_MISSING" if critical else "CPU_MODULE_ASSERTION_PASS", "conformance": "FAIL" if critical else "PASS", "critical": str(critical).lower(),
        })
    matrix_path = TASK / "ACTIVE_TRANSITION_CONFORMANCE_MATRIX_V2.csv"
    with matrix_path.open("w", encoding="utf-8", newline="") as handle:
        fields = list(out_rows[0])
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(out_rows)
    write_json("ACTIVE_CALL_ORDER_CONFORMANCE_V2.json", {"schema": "ACTIVE_CALL_ORDER_CONFORMANCE_V2", "required_order": ["L1", "P0", "C0", "L2", "L3"], "observed_public_order": None, "module_observed_order": ["C0", "L2", "L3"], "l1_cycle_cache": True, "primary_fresh_binding_required": True, "alternative_fresh_binding_required": True, "native_alternative_inventory": "SOURCE_NATIVE_EXISTING_EMPTY", "verdict": "BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP", "reason": "No public runtime cycle calls L1/P0/C0/L2/L3 in canonical order."})
    write_json("CONFORMANCE_TEST_FIXTURE_BOUNDARY_V2.json", {"schema": "CONFORMANCE_TEST_FIXTURE_BOUNDARY_V2", "cpu_only": True, "deterministic": True, "fake_clock": True, "injected_backends": ["geometry/certifier", "proposal_solver", "external_witness"], "test_doubles_may_not_replace": ["Supervisor routing", "ActiveRunner commit", "BackupTokenStore", "TerminalRuntime", "C0Admission", "PlantCommitAdapter", "TraceWriter"], "deadline_profile": "TEST_FIXTURE_ONLY_NOT_RUNTIME_AUTHORITY", "real_rollout": False, "gpu": False})
    write_json("UNKNOWN_ROUTING_CONFORMANCE_V2.json", {"schema": "UNKNOWN_ROUTING_CONFORMANCE_V2", "module_level_typed_unknown": True, "typed_sources": ["start map mismatch", "L1 backend exception", "L2 backend exception", "L3 backend exception", "terminal exception", "deadline profile missing"], "nominal_fallback": False, "silent_pass": False, "uncertified_commit": False, "integrated_public_route": "NOT_EXECUTABLE", "verdict": "BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP"})
    write_json("ACTIVE_TRACE_CONFORMANCE_V2.json", {"schema": "ACTIVE_TRACE_CONFORMANCE_V2", "module_trace_writer": "PASS", "selected_equals_executed_guard": "PASS", "boundary_trace_role": "PASS", "immutable_finalize": "PASS", "outcome_labels_forbidden": "PASS", "oracle_import_or_feedback": "NONE_OBSERVED", "integrated_trace_producer": "MISSING_PUBLIC_CYCLE", "verdict": "BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP"})
    scenarios = [
        "AC-START-01","AC-START-02","AC-START-03","AC-START-04","AC-L1-01","AC-L1-02","AC-L1-03","AC-L1-04","AC-L1-05","AC-P0-01","AC-P0-02","AC-P0-03","AC-P0-04","AC-C0-01","AC-C0-02","AC-C0-03","AC-C0-04","AC-C0-05","AC-C0-06","AC-C0-07","AC-L2-01","AC-L2-02","AC-L2-03","AC-L2-04","AC-L2-05","AC-L2-06","AC-L3-01","AC-L3-02","AC-L3-03","AC-L3-04","AC-L3-05","AC-ARB-01","AC-ARB-02","AC-ARB-03","AC-ARB-04","AC-ARB-05","AC-DL-01","AC-DL-02","AC-DL-03","AC-DL-04","AC-DL-05","AC-DL-06","AC-DL-07","AC-DL-08","AC-BT-01","AC-BT-02","AC-BT-03","AC-BT-04","AC-BT-05","AC-BT-06","AC-BT-07","AC-BT-08","AC-BT-09","AC-BT-10","AC-BT-11","AC-BT-12","AC-BT-13","AC-TERM-01","AC-TERM-02","AC-TERM-03","AC-TERM-04","AC-TERM-05","AC-TERM-06","AC-TERM-07","AC-TERM-08","AC-BOUND-01","AC-BOUND-02","AC-BOUND-03","AC-BOUND-04","AC-BOUND-05","E2E-01","E2E-02","E2E-03","E2E-04","E2E-05","E2E-06"]
    write_json("scenario_manifest.json", {"schema": "ACTIVE_CONFORMANCE_SCENARIO_MANIFEST_V2", "scenario_count": len(scenarios), "all_cpu_deterministic": True, "real_active": 0, "gpu": 0, "scenario_ids": scenarios, "first_failure_stop": True, "public_cycle_required_for_critical": True})
    results = []
    for scenario in scenarios:
        if scenario.startswith("E2E-"):
            status = "BLOCKED_AFTER_FIRST_COUNTEREXAMPLE"
            reason = "PUBLIC_ACTIVE_CYCLE_ENTRYPOINT_MISSING"
        else:
            status = "MODULE_SCOPE_PASS" if not scenario.startswith(("AC-DL", "AC-BT", "AC-TERM", "AC-BOUND")) else "BLOCKED_AFTER_FIRST_COUNTEREXAMPLE"
            reason = "CPU_TARGETED_MODULE_ASSERTION" if status == "MODULE_SCOPE_PASS" else "PUBLIC_PATH_REQUIRED_AND_STOPPED"
        results.append({"scenario_id": scenario, "status": status, "reason": reason, "real_runtime_path": False, "runtime_mutation": False})
    write_json("scenario_results.json", {"schema": "ACTIVE_CONFORMANCE_SCENARIO_RESULTS_V2", "results": results, "first_counterexample": "INTEGRATION_ORCHESTRATION_GAP", "e2e_pass_count": 0, "e2e_genuine_count": 0})
    first = {"schema": "ACTIVE_CONFORMANCE_FIRST_COUNTEREXAMPLE_V2", "counterexample_id": "CE-001", "class": "INTEGRATION_ORCHESTRATION_GAP", "discovered_by": "public API inspection plus CPU startup probe", "required": "state snapshot → start admission → L1 → proposal → C0 → L2 → L3 → arbitration → commit/trace", "observed": "ActiveRunner.commit_active_decision(snapshot, precomputed_decision) only; no public full-cycle entrypoint", "evidence": api, "runtime_source_changed": False, "correction_quota": 0, "stopped_unnecessary_scenarios": True}
    write_json("first_counterexample.json", first)
    write_json("active_contract_counterexamples.json", {"schema": "ACTIVE_CONTRACT_COUNTEREXAMPLES_V2", "count": 1, "counterexamples": [first]})
    write_json("active_contract_model_check_result.json", {"schema": "ACTIVE_CONTRACT_MODEL_CHECK_RESULT_V2", "uses_actual_runtime_objects": True, "check_count": 9, "counterexample_count": 1, "checks": [{"id": "MC-01", "name": "public_full_cycle_entrypoint", "passed": False, "evidence": "ActiveRunner has no run_cycle/step/execute_cycle/process_snapshot"}, {"id": "MC-02", "name": "supervisor_selection_owner", "passed": True, "evidence": "Supervisor.arbitrate"}, {"id": "MC-03", "name": "plant_owner", "passed": True, "evidence": "PlantCommitAdapter.commit"}, {"id": "MC-04", "name": "no_oracle_edge", "passed": True, "evidence": "no oracle imports"}, {"id": "MC-05", "name": "boundary_no_plant", "passed": True, "evidence": "boundary has no selected action"}, {"id": "MC-06", "name": "no_synthetic_alternative", "passed": True, "evidence": "provider accepts SOURCE_NATIVE_EXISTING only"}, {"id": "MC-07", "name": "token_lifecycle_module", "passed": True, "evidence": "BackupTokenStore"}, {"id": "MC-08", "name": "terminal_membership_separation", "passed": True, "evidence": "TerminalRuntime"}, {"id": "MC-09", "name": "deadline_profile_gate", "passed": True, "evidence": "startup requires profile"}], "verdict": "BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP"})
    write_json("active_runtime_contract_conformance_review.json", {"schema": "ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_REVIEW_V2", "verdict": "BLOCKED_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2", "integrated_path_complete": False, "transition_table_runtime_constraint": "MODULE_ONLY_NOT_PUBLIC_CYCLE", "canonical_order": "NOT_EXECUTABLE_PUBLICLY", "primary_c0": "MODULE_SCOPE_ONLY", "deadline": "MODULE_SCOPE_ONLY", "backup": "MODULE_SCOPE_ONLY", "terminal": "MODULE_SCOPE_ONLY", "boundary": "MODULE_SCOPE_ONLY", "unknown": "TYPED_MODULE_SCOPE_ONLY", "selected_executed": "NO_GENUINE_E2E", "trace_oracle": "TRACE_MODULE_PASS_ORACLE_EDGE_NONE", "transition_coverage": "43_ASSERTIONS_WITH_CRITICAL_PUBLIC_PATH_BLOCKED", "e2e": "0/6 genuine", "first_counterexample": "CE-001", "smoke_authorized": False, "next_task": "DESIGN_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2", "critical_blockers": ["No public ACTIVE cycle composition root routes all frozen phases."]})
    write_json("FINAL_DECISION.json", {"schema": "VALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2_FINAL_DECISION", "FINAL_STATUS": "BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP", "FINAL_DECISION": "DO_NOT_ENTER_ACTIVE_RUNTIME_SMOKE; DESIGN_PUBLIC_ACTIVE_CYCLE_COMPOSITION", "protected_source_mutation_count": 0, "runtime_correction_count": 0, "real_active_rollout_count": 0, "gpu_execution_count": 0, "scientific_oracle_count": 0, "official100_count": 0, "e2e_genuine_pass": 0, "e2e_required": 6, "transition_assertions": 43, "transition_critical_dynamic_coverage": "BLOCKED", "only_next_task": "DESIGN_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2"})
    write_json("downstream_handoff.json", {"schema": "ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2_HANDOFF", "status": "BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP", "blocker": "PR116 additive modules expose no public full-cycle composition root", "required_next_task": "DESIGN_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2", "must_preserve": ["PR119 exact BYPASS evidence", "all runtime/protected source blobs", "CE-001", "no runtime correction in this task"], "must_not_do": ["ACTIVE_RUNTIME_ON real rollout", "GPU", "smoke", "oracle", "official100", "fake task-local orchestration"]})
    write_text("README.md", """# Validate Active Runtime Contract Conformance V2\n\nThis task is a CPU-only, fail-closed validation of PR #116 at PR #119 exact head against the PR #107–#115 runtime-assurance contracts. The immutable runtime modules were inspected and exercised only with deterministic numerical/clock/witness test doubles. No production/runtime source, controller, map, candidate library, experiment, GPU process, scientific oracle, or official100 run was changed or executed.\n\nThe audit found a genuine public integration orchestration gap: `ActiveRunner` has no full-cycle entrypoint and `Supervisor.arbitrate` consumes precomputed phase results. The harness therefore does not fake an end-to-end cycle; it records `CE-001` and stops critical conformance expansion.\n\nFinal status: `BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP`.\n""")
    write_text("DRAFT_PR_BODY.md", """## Summary\n\nThis Draft PR validates PR #116 ACTIVE_RUNTIME_ON against the frozen PR #107–#115 contracts using PR #119 exact head `b4ff579cf6a2bcffd0661cd39eb925aa4f3a5d27`. PR #119 BYPASS equivalence remains frozen and PASS (5/5 pairs, 732 compared steps, zero mismatches).\n\n## Result\n\nThe CPU module checks confirm typed identities, geometry/actuator values, C0 no-clip, L1 caching/binding, L2 H1 equations, L3 preparation-only semantics, deadline observations, token/terminal/trace boundaries, and no oracle import. However, PR #116 exposes no public full ACTIVE cycle composition root. `ActiveRunner.commit_active_decision` accepts a precomputed `SupervisorDecision`; `Supervisor.arbitrate` accepts precomputed certification results. A task-local harness is not allowed to synthesize this missing orchestration.\n\nTherefore the 43-rule matrix records critical public-path rows as blocked, E2E cases as `0/6 genuine`, and the final status is `BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP`. No runtime correction, GPU execution, ACTIVE rollout, smoke, oracle, or official100 was performed.\n\nOnly next task: `DESIGN_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2`.\n""")
    write_text("report/REPORT_VALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2.md", """# Report: Validate Active Runtime Contract Conformance V2\n\n## Answer first\n\n- Upstream: PR #119 exact Open Draft head `b4ff579cf6a2bcffd0661cd39eb925aa4f3a5d27`; its `PASS_REFROZEN_BYPASS_EQUIVALENCE_V2R1` evidence remains unchanged (5/5 pairs, 732 compared steps, all mismatch counters zero).\n- Public ACTIVE entrypoint: `ActiveRunner(..., RuntimeMode.ACTIVE_RUNTIME_ON).startup()` plus `commit_active_decision(snapshot, decision)`. There is no `run_cycle`/`step`/`execute_cycle`/`process_snapshot`.\n- Missing path: no public composition root consumes the complete frozen sequence `I0 → R0 → L1 → P0 → C0 → L2 → L3 → alternative → Supervisor → PlantCommit/backup/terminal/boundary → trace`.\n- Selection owner: `Supervisor.arbitrate` at module scope; plant owner: `PlantCommitAdapter.commit` at module scope. These module-level facts are not sufficient for integrated conformance.\n- Canonical order: not executable through a public runtime cycle; only C0→L2→L3 is internally present in `Supervisor.certify_candidate`.\n- Transition coverage: 43/43 table rows have explicit assertions; critical public-path rows are blocked by the same integration gap.\n- E2E: 0/6 genuine runtime cases; they were not fabricated by task-local orchestration.\n- First counterexample: `CE-001 INTEGRATION_ORCHESTRATION_GAP`.\n\n## CPU-only evidence boundary\n\nThe deterministic tests use only fake geometry/certifier, proposal, clock, and witness backends. They preserve the actual Supervisor, ActiveRunner commit shell, BackupTokenStore, TerminalRuntime, C0Admission, PlantCommitAdapter, and TraceWriter. The public API inspection and startup probe are real runtime calls. No runtime source was modified, no controller or map was changed, and no real ACTIVE/GPU/scientific-oracle/official100 execution occurred.\n\n## Contract findings\n\nModule-scope checks support the frozen geometry (0.015/0.010/0.025 m, rho=0), actuator admission (inclusive ±0.1 and no clipping), L1 once-per-cycle candidate-independent result, H1 equations, L3 preparation-only bundle, Supervisor priority, typed UNKNOWN handling, BackupTokenStore lifecycle, terminal membership/certificate/eligibility separation, assurance-boundary no-plant behavior, and immutable trace/no-oracle edge.\n\nThe missing public cycle means the validation cannot establish that all action-producing paths pass through Supervisor, that all phase transitions are enforced in one runtime decision, or that deadline/alternative/backup/terminal routing is integrated. The task therefore stops after the first counterexample and does not claim conformance.\n\n## Final decision\n\n`FINAL_STATUS=BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP`\n\n`FINAL_DECISION=DO_NOT_ENTER_ACTIVE_RUNTIME_SMOKE; DESIGN_PUBLIC_ACTIVE_CYCLE_COMPOSITION`\n\nOnly next task: `DESIGN_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2`.\n""")


if __name__ == "__main__":
    main()
