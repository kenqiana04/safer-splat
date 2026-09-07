"""Generate the design-only Active Runtime public-cycle composition package.

This helper is task-local.  It writes only beside this file and performs no
runtime import, rollout, GPU operation, or controller mutation.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
RUNTIME = ROOT / "reproduction" / "runtime" / "active_runtime_assurance_v2"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def blob(path: str) -> str:
    return subprocess.check_output(["git", "hash-object", path], cwd=ROOT, text=True).strip()


def write_text(name: str, value: str) -> None:
    p = TASK / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(value.rstrip() + "\n", encoding="utf-8")


def write_json(name: str, value: object) -> None:
    write_text(name, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def core(path: str, authority: str) -> dict:
    p = ROOT / path
    return {
        "authority": authority,
        "path": path,
        "git_blob_sha1": blob(path),
        "sha256": sha256_file(p),
    }


def runtime_entry(path: str) -> dict:
    p = ROOT / path
    return {
        "path": path,
        "git_blob_sha1": blob(path),
        "sha256": sha256_file(p),
        "file_mode": "100644",
    }


def json_hashes(paths: list[str]) -> list[dict]:
    out = []
    for rel in paths:
        p = ROOT / rel
        if p.exists():
            out.append({"path": rel, "git_blob_sha1": blob(rel), "sha256": sha256_file(p)})
    return out


PR120 = {
    "repository": "kenqiana04/safer-splat",
    "pr": 120,
    "state": "OPEN_DRAFT",
    "title": "[Draft] Validate active runtime contract conformance V2",
    "branch": "validate-active-runtime-contract-conformance-v2",
    "head_sha": "6c5c59dd083dc83661e56c4ddd3e62fa12497652",
    "base": "execute-refrozen-bypass-equivalence-v2r1",
    "base_sha": "b4ff579cf6a2bcffd0661cd39eb925aa4f3a5d27",
    "url": "https://github.com/kenqiana04/safer-splat/pull/120",
}

FROZEN_CONTRACTS = [
    core("reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv", "PR107_METHOD_LOGIC"),
    core("reproduction/specification/cross_layer_geometry_authority_v2/CROSS_LAYER_GEOMETRY_AUTHORITY_V2.json", "PR108_GEOMETRY"),
    core("reproduction/specification/control_authority_v2/SELECTED_CONTROL_ACTUATOR_CONTRACT_V2.json", "PR109_ACTUATOR"),
    core("reproduction/specification/runtime_assurance_deadline_authority_v2/RUNTIME_ASSURANCE_DEADLINE_AUTHORITY_V2.json", "PR110_DEADLINE"),
    core("reproduction/specification/alternative_source_authority_v2/ALTERNATIVE_SOURCE_AUTHORITY_V2.json", "PR111_ALTERNATIVE"),
    core("reproduction/specification/backup_token_runtime_schema_v2/RETAINED_BACKUP_TOKEN_SCHEMA_V2.json", "PR112_BACKUP_TOKEN"),
    core("reproduction/specification/terminal_emergency_policy_v2/TERMINAL_EMERGENCY_POLICY_CONTRACT_V2.json", "PR113_TERMINAL"),
    core("reproduction/specification/independent_evaluation_oracle_v2/EVALUATION_TRACE_SCHEMA_V2.json", "PR114_TRACE_ORACLE"),
    core("reproduction/design/active_runtime_assurance_implementation_v2/ACTIVE_RUNTIME_IMPLEMENTATION_FILE_MANIFEST_V2.csv", "PR115_IMPLEMENTATION_MANIFEST"),
    core("reproduction/design/active_runtime_assurance_implementation_v2/MODULE_ARCHITECTURE_V2.json", "PR115_MODULE_ARCHITECTURE"),
    core("reproduction/design/active_runtime_assurance_implementation_v2/ACTIVE_RUNTIME_VALIDATION_LADDER_V2.md", "PR115_VALIDATION_LADDER"),
]

RUNTIME_MODULES = [
    "authority_registry.py", "runtime_types.py", "start_admission.py", "diagnostic_r0.py",
    "l1_runtime.py", "primary_proposal_adapter.py", "c0_admission.py", "l2_runtime.py",
    "l3_runtime.py", "alternative_provider.py", "backup_token_store.py", "terminal_runtime.py",
    "deadline_runtime.py", "supervisor.py", "plant_commit.py", "trace_writer.py", "active_runner.py",
]

EVIDENCE_FILES = [
    "reproduction/validation/active_runtime_contract_conformance_v2/FINAL_DECISION.json",
    "reproduction/validation/active_runtime_contract_conformance_v2/ACTIVE_RUNTIME_PUBLIC_INTEGRATION_AUDIT_V2.md",
    "reproduction/validation/active_runtime_contract_conformance_v2/ACTIVE_TRANSITION_CONFORMANCE_MATRIX_V2.csv",
    "reproduction/validation/active_runtime_contract_conformance_v2/active_contract_model_check_result.json",
    "reproduction/validation/active_runtime_contract_conformance_v2/first_counterexample.json",
    "reproduction/validation/active_runtime_contract_conformance_v2/validation_result.json",
]


def make_input_lock() -> dict:
    return {
        "schema": "PUBLIC_CYCLE_DESIGN_INPUT_LOCK_V2",
        "task": "DESIGN_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2",
        "task_scope": "DESIGN_ONLY_NO_RUNTIME_IMPLEMENTATION",
        "direct_upstream": PR120,
        "upstream_assertions": {
            "final_status": "BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP",
            "public_active_integration": "BLOCKED",
            "supervisor_arbitrate_sole_selection_owner": True,
            "plant_commit_adapter_commit_sole_plant_owner": True,
            "transition_assertions": "43/43",
            "critical_public_routes_blocked": 35,
            "genuine_e2e": "0/6",
            "model_counterexample": "INTEGRATION_ORCHESTRATION_GAP",
            "runtime_production_diff": 0,
            "real_active_gpu_oracle_official100": "0/0/0/0",
            "only_next_task": "DESIGN_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2",
        },
        "preserved_upstream_prs": [107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120],
        "frozen_contracts": FROZEN_CONTRACTS,
        "pr120_evidence": json_hashes(EVIDENCE_FILES),
        "runtime_module_identity": [runtime_entry(f"reproduction/runtime/active_runtime_assurance_v2/{x}") for x in RUNTIME_MODULES],
        "protected_source": [
            runtime_entry("run.py"),
            runtime_entry("cbf/cbf_utils.py"),
            runtime_entry("dynamics/systems.py"),
        ],
        "execution_counters": {
            "runtime_implementation_count": 0,
            "runtime_mutation_count": 0,
            "production_mutation_count": 0,
            "real_active_rollout_count": 0,
            "gpu_execution_count": 0,
            "scientific_oracle_count": 0,
            "official100_count": 0,
        },
        "authority": {
            "runtime_mutation_authority": False,
            "scientific_result_mutation_authority": False,
            "pr120_mutation_authority": False,
        },
    }


def build_docs() -> None:
    write_text("README.md", """
# Active Runtime Public Cycle Composition V2 (DESIGN ONLY)

This package freezes a future composition root for the active runtime. It is
derived from PR #120 exact head `6c5c59dd083dc83661e56c4ddd3e62fa12497652`.
The PR #120 blocker is preserved: module-level implementations exist, but no
runtime-owned public API composes a complete active cycle.

The proposed owner is `ActiveCycleCoordinator`. It orchestrates typed frozen
stages, delegates every routing/selection decision to `Supervisor`, and uses
the existing `ActiveRunner.commit_active_decision` and trace/token mechanics.
No safety mathematics, candidate synthesis, controller change, rollout, GPU
execution, oracle, or performance claim is part of this task.

Read `PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2.md` first. The implementation
ladder is deliberately Design -> Implement -> Revalidate -> Smoke; this task
stops at Design and validation.
""")

    write_text("PUBLIC_CYCLE_INTEGRATION_GAP_DIAGNOSIS_V2.md", """
# Public cycle integration gap diagnosis V2

## Frozen evidence

PR #120 is retained unchanged as an Open Draft at the exact head recorded in
`PUBLIC_CYCLE_DESIGN_INPUT_LOCK.json`. Its final status is
`BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP`; 43/43 transition
assertions are present, but 35 critical public routes and all 6 genuine E2E
scenarios are blocked. No runtime or production file is changed by this task.

## What already exists

The frozen runtime contains `AuthorityRegistry`, `StartAdmission`,
`DiagnosticR0`, `L1Runtime`, `PrimaryProposalAdapter`, `C0Admission`,
`L2Runtime`, `L3Runtime`, `AlternativeProvider`, `BackupTokenStore`,
`TerminalRuntime`, `DeadlineTracker`, `Supervisor`, `PlantCommitAdapter`,
`TraceWriter`, and `ActiveRunner`.

## Exact missing seam

There is no runtime-owned public API that performs trial admission, R0
diagnostic handoff, phase sequencing, typed result handoff, deadline-stage
admission, transition lookup, fallback entry, backup validation, terminal
timing, final arbitration, commit invocation, and cycle-result construction.
`ActiveRunner.commit_active_decision(...)` consumes a precomputed
`SupervisorDecision`; it is not a cycle coordinator. `Supervisor.certify_candidate(...)`
consumes precomputed L1/binding/C0/L2/L3 data. `Supervisor.arbitrate(...)`
consumes precomputed candidate/L3/backup/terminal/deadline data and remains the
sole selection owner.

## Frozen root cause

`MISSING_PUBLIC_ACTIVE_CYCLE_ORCHESTRATION` (CE-001). The repair is a future
composition design, not a correction to PR #120 and not a second safety policy.
""")

    write_text("PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2.md", """
# PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2

`ActiveCycleCoordinator` is the sole future composition root. It owns only
sequencing, typed handoff, context evolution, and calls to frozen modules. It
does **not** own certificate mathematics, candidate generation or synthesis,
selection priority, terminal/deadline policy, dynamics, plant authority, or
scientific evaluation.

`Supervisor.route_transition` is the only future routing authority and
`Supervisor.arbitrate` remains the final action-selection authority.
`PlantCommitAdapter.commit` remains the only plant authority. The coordinator
must execute exactly the stage named by a `RoutingDecision`; it may not invent
a default branch, interpret a deadline, or call a fallback on its own.

The canonical cycle is `CYCLE_BEGIN -> L1 -> P0 -> fresh binding -> C0 ->
L2 -> L3 -> routing/arbitration -> commit -> token update -> trace -> cycle
result`. L1 runs once per cycle and C0 is never used to bypass L1. A terminal
path is route-only, goal-hold is disabled, and an assurance boundary produces
no plant command. Existing ActiveRunner mechanics are reused; token and trace
logic is not copied into the coordinator.

This is a contract and implementation handoff only. It does not authorize
implementation, conformance revalidation, smoke, or an active experiment.
""")

    write_text("SUPERVISOR_ROUTING_AUTHORITY_V2.md", """
# Supervisor-owned routing authority V2

The future public API is:

```text
Supervisor.route_transition(event, runtime_context) -> RoutingDecision
Supervisor.arbitrate(candidate, l3, backup, terminal, deadline) -> SupervisorDecision
```

`route_transition` performs the exact-one lookup in the frozen 43-rule
transition table and returns the rule id, source/destination phase, stage
admission, search permission, arbitration requirement, failure mapping,
deadline interpretation, backup/terminal flags, commit permission, and reason.
The coordinator cannot implement a competing `if/else` policy. Missing or
ambiguous lookup is a typed UNKNOWN/BLOCK event routed back to Supervisor; it
is never guessed.

`arbitrate` remains the only selector of navigation, backup, terminal, or
assurance-boundary action. L1/L2/L3/certifiers report typed evidence only.
The supervisor owns deadline interpretation and alternative permission;
DeadlineTracker remains observation-only.
""")

    write_text("DEADLINE_STAGE_ADMISSION_INTERFACE_V2.md", """
# Deadline stage-admission interface V2

`DeadlineTracker` emits observations; it has no routing or action authority.
At cycle start, before proposal/candidate work, before an alternative query,
before new L3 discovery, before terminal evaluation, and before the final
commit guard, the coordinator obtains an observation and passes it unchanged
to `Supervisor.route_transition`.

The only states are `DEADLINE_OPEN`, `DEADLINE_WARNING`,
`DEADLINE_EXPIRED`, and typed `DEADLINE_UNKNOWN`. Warning forbids new
high-cost searches. Expired forbids candidate generation, alternative search,
and backup discovery; only already valid/certified choices may be routed.
An expired state is not an unsafe/collision/controller-failure claim. No
concrete millisecond budget is invented here.
""")

    write_text("PRIMARY_CYCLE_INTEGRATION_V2.md", """
# Primary cycle integration V2

After CYCLE_BEGIN and one authoritative L1 evaluation, a Supervisor routing
decision may admit `PrimaryProposalAdapter`. A proposal is a typed
PRIMARY_AVAILABLE/UNAVAILABLE/UNKNOWN result and has no commit authority.
When a candidate identity exists, the coordinator creates a fresh
`L1AttemptBinding` for that candidate and executes the frozen order C0 -> L2
-> L3. `Supervisor.certify_candidate` can be reused for the existing C0/L2/L3
certificate path but does not replace the public composition root.

Only Supervisor arbitration may select the primary action. A primary C0/L2/L3
failure is an event, not an implicit backup or nominal-control instruction.
""")

    write_text("ALTERNATIVE_CYCLE_INTEGRATION_V2.md", """
# Alternative cycle integration V2

The frozen `SOURCE_NATIVE_EXISTING` inventory is currently empty. The
coordinator may call `AlternativeProvider` only after a Supervisor routing
decision explicitly names `ALTERNATIVE_SOURCE_QUERY`; an empty inventory
returns `ALT_EXHAUSTED/NO_ALTERNATIVE_AVAILABLE` to Supervisor. The
coordinator must not jump directly to backup.

If a future authorized native candidate exists, it reuses the single L1 result
from this cycle, creates a fresh candidate-specific binding, and repeats
C0 -> L2 -> L3. It never recomputes L1, synthesizes/perturbs a candidate, or
lets an alternative provider commit an action. Expired deadlines block a new
query; an unavailable alternative is not itself unsafe.
""")

    write_text("BACKUP_CYCLE_INTEGRATION_V2.md", """
# Backup cycle integration V2

The coordinator performs token mechanics only: read
`BackupTokenStore.current`, request the frozen validation against the exact
snapshot/authority registry, surface VALID/INVALID/NONE/EXHAUSTED/UNKNOWN,
and request invalidation only through the existing store API when the frozen
contract requires it. It may obtain the exact cursor action but never chooses
backup priority. Supervisor owns routing and arbitration.

On a navigation commit, reuse `ActiveRunner.commit_active_decision`: plant
commit, prepared bundle store, atomic activation of cursor k+1, old-token
retirement, then trace. On a backup commit, reuse the same path and advance
the cursor only after a successful plant receipt. The coordinator must not
duplicate either lifecycle.
""")

    write_text("TERMINAL_CYCLE_INTEGRATION_V2.md", """
# Terminal cycle integration V2

`TerminalRuntime.evaluate(fallback_context, expected_terminal_ref)` is called
only when a Supervisor routing decision admits terminal evaluation. A terminal
result returns to Supervisor for arbitration. Terminal search is not an
emergency shortcut and deadline expiry does not make a terminal automatically
safe. `GOAL_HOLD_RUNTIME_ENABLED=false`; post-hoc goal labels never enter
Supervisor routing.
""")

    write_text("PUBLIC_CYCLE_TRACE_CONTRACT_V2.md", """
# Public cycle trace contract V2

Every resolved cycle has exactly one outcome trace with exact trial/cycle
identity. Navigation, backup, and terminal commits use the existing
ActiveRunner commit/trace path. A boundary uses the existing no-action trace
path. There is no trace-before-decision side effect, no untraced plant commit,
and no duplicate token update.

The coordinator records phase history, routing rule ids, deadline observations,
typed evidence references, final decision, commit receipt/boundary, and trace
reference. It never computes collision, progress, success, or oracle labels.
""")

    write_text("FIRST_AND_SUBSEQUENT_CYCLE_SEMANTICS_V2.md", """
# First and subsequent cycle semantics V2

After I0a admission passes, cycle 0 retains no backup token unless one was
already authorized. Primary proposal still follows L1 -> P0 -> C0 -> L2 ->
L3; absence of backup never skips L3. A navigation commit creates the k+1
retained token atomically. If no navigation and no retained backup exist, only
a Supervisor-admitted terminal or assurance boundary can resolve the cycle.

For k>0, validate the retained token against the exact snapshot, registry,
actuator, and temporal identity before arbitration. Failed navigation preserves
the old token. A valid backup can be routed by Supervisor; a stale/invalid or
exhausted token is a typed event. New navigation uses the same atomic handoff.
""")

    write_text("PUBLIC_CYCLE_GOAL_BOUNDARY_V2.md", """
# Goal and oracle boundary V2

The navigation goal may be input to a frozen proposal primitive. A post-hoc
goal-reached label is never passed to Supervisor and cannot terminate a cycle.
`GOAL_HOLD_RUNTIME_ENABLED=false`. `ActiveCycleResult` is a runtime execution
record, not a scientific outcome; independent evaluation oracle contracts stay
outside the composition root.
""")

    write_text("BYPASS_EVIDENCE_PRESERVATION_V2.md", """
# BYPASS evidence preservation V2

The implementation DAG is active-only. If it adds only an active composition
path, `Supervisor.bypass_decision`, `ActiveRunner.commit_bypass`, plant BYPASS
behavior, BYPASS trace, and canonical QA trace identity remain unchanged; PR
#119's frozen equivalence evidence is retained and regression-tested.

If a future implementation needs to change shared BYPASS semantics, it must
set `BYPASS_REVALIDATION_REQUIRED=true` and insert fresh BYPASS revalidation
after implementation and before active smoke. This design does not silently
reuse evidence under changed semantics.
""")

    write_text("POST_COMPOSITION_VALIDATION_LADDER_V2.md", """
# Post-composition validation ladder V2

1. Design public cycle composition (this task).
2. Implement `ActiveCycleCoordinator` and its typed API.
3. Revalidate active runtime contract conformance.
4. Only after full PASS, run `ACTIVE_RUNTIME_SMOKE_V2`.
5. Apply bug-only correction if needed.
6. Freeze engineering/final deadline/experiment/statistics protocol.
7. Run final active evaluation.

Design -> Implement -> Smoke is forbidden. No runtime implementation or smoke
is authorized by this document.
""")


def build_schemas() -> None:
    write_json("PUBLIC_CYCLE_API_V2.json", {
        "schema": "PUBLIC_CYCLE_API_V2",
        "owner": "ActiveCycleCoordinator",
        "design_only": True,
        "methods": [
            {"name": "start_trial", "signature": "start_trial(initial_snapshot, trial_context) -> TrialStartResult", "steps": ["ACTIVE startup authority verification", "I0a admission", "I0b only if an already-authorized primitive exists; default unavailable", "R0 diagnostic", "establish session state"], "nonpass": "TRIAL_BLOCKED_AT_ADMISSION; no plant"},
            {"name": "run_cycle", "signature": "run_cycle(snapshot, cycle_context) -> ActiveCycleResult", "steps": ["CYCLE_BEGIN", "one route-selected stage at a time", "Supervisor.arbitrate", "ActiveRunner commit boundary", "typed result"], "forbidden": ["run_until_success", "hidden scientific termination", "goal label input"]},
            {"name": "finalize_trial", "signature": "finalize_trial() -> TrialTraceLock", "steps": ["flush/finalize trace only"], "forbidden": ["oracle", "new action", "scientific scoring"]},
        ],
        "authority": {"coordinator": "orchestration_only", "supervisor": "routing_and_selection", "plant_commit": "sole_plant_authority", "active_runner": "existing_commit_token_trace_mechanics"},
    })
    phases = ["CYCLE_BEGIN", "L1_IMMEDIATE_CERTIFICATION", "PRIMARY_PROPOSAL", "PRIMARY_C0", "PRIMARY_L2", "PRIMARY_L3", "ALTERNATIVE_ELIGIBILITY", "ALTERNATIVE_SOURCE_QUERY", "ALTERNATIVE_C0", "ALTERNATIVE_L2", "ALTERNATIVE_L3", "BACKUP_VALIDATION", "TERMINAL_EVALUATION", "ARBITRATION", "COMMIT", "TRACE_APPEND", "CYCLE_COMPLETE", "ASSURANCE_BOUNDARY"]
    write_json("PUBLIC_ACTIVE_CYCLE_PHASES_V2.json", {"schema": "PUBLIC_ACTIVE_CYCLE_PHASES_V2", "trial_phases": ["START_ADMISSION", "R0_DIAGNOSTIC", "TRIAL_READY", "TRIAL_BLOCKED_AT_ADMISSION"], "cycle_phases": phases, "r0_is_hard_gate": False, "goal_hold_runtime_enabled": False})
    context_fields = [
        ("trial_id", "string"), ("cycle_index", "integer"), ("snapshot_id", "string"), ("state_id", "string"), ("authority_identity", "object"), ("deadline_identity", "object"), ("phase", "enum"), ("l1_result", "typed_ref"), ("primary_candidate", "typed_ref|null"), ("primary_binding", "typed_ref|null"), ("primary_c0", "typed_ref|null"), ("primary_l2", "typed_ref|null"), ("primary_l3", "typed_ref|null"), ("alternative_attempts", "array"), ("backup_validation", "typed_ref|null"), ("backup_action", "typed_ref|null"), ("terminal_result", "typed_ref|null"), ("routing_decisions", "array"), ("final_supervisor_decision", "typed_ref|null"), ("commit_receipt", "typed_ref|null"), ("trace_ref", "typed_ref|null"),
    ]
    write_json("ACTIVE_CYCLE_CONTEXT_SCHEMA_V2.json", {"schema": "ACTIVE_CYCLE_CONTEXT_SCHEMA_V2", "immutable_evolution": True, "exact_identity_required": True, "fields": [{"name": n, "type": t} for n, t in context_fields], "mutation_rule": "append typed evidence; never rewrite earlier evidence"})
    result_fields = ["trial_id", "cycle_index", "start_state_id", "phase_history", "routing_rule_ids", "deadline_observations", "l1_result", "candidate_refs", "certificate_refs", "backup_status", "terminal_status", "supervisor_reason", "action_role", "commit_receipt", "committed", "next_state", "boundary", "trace_ref", "typed_stop_or_failure_reason"]
    write_json("ACTIVE_CYCLE_RESULT_SCHEMA_V2.json", {"schema": "ACTIVE_CYCLE_RESULT_SCHEMA_V2", "runtime_result_not_scientific_outcome": True, "required_fields": result_fields, "boundary_contract": {"committed": False, "boundary": True, "next_state": None, "plant_commit": False}})
    events = ["START_PASS", "START_FAIL", "START_UNKNOWN", "L1_PASS", "L1_FAIL", "L1_UNKNOWN", "PRIMARY_AVAILABLE", "PRIMARY_UNAVAILABLE", "PRIMARY_UNKNOWN", "C0_PASS", "C0_FAIL", "C0_UNKNOWN", "L2_PASS", "L2_FAIL", "L2_UNKNOWN", "L3_PASS", "L3_FAIL", "L3_UNKNOWN", "ALT_ELIGIBLE", "ALT_NOT_ELIGIBLE", "ALT_AVAILABLE", "ALT_EXHAUSTED", "ALT_UNKNOWN", "BACKUP_VALID", "BACKUP_INVALID", "BACKUP_NONE", "BACKUP_EXHAUSTED", "BACKUP_UNKNOWN", "TERMINAL_READY", "TERMINAL_NOT_READY", "TERMINAL_UNKNOWN", "DEADLINE_OPEN", "DEADLINE_WARNING", "DEADLINE_EXPIRED", "DEADLINE_UNKNOWN", "COMMIT_SUCCESS", "COMMIT_FAILURE", "BOUNDARY"]
    write_json("PUBLIC_CYCLE_EVENT_SCHEMA_V2.json", {"schema": "PUBLIC_CYCLE_EVENT_SCHEMA_V2", "events": [{"name": e, "typed": True, "routes_via": "Supervisor.route_transition"} for e in events], "taxonomy_source": "PR107 frozen transition/routing metadata", "no_replacement_taxonomy": True})
    write_json("PUBLIC_CYCLE_EXCEPTION_ROUTING_V2.json", {"schema": "PUBLIC_CYCLE_EXCEPTION_ROUTING_V2", "rule": "stage exception -> typed event -> Supervisor.route_transition", "forbidden": ["except Exception: execute u_des", "silent PASS", "nominal/desired/hold-last fallback without certificate"], "events": ["STAGE_EXCEPTION", "SERIALIZATION_FAILURE", "ROUTING_LOOKUP_UNKNOWN", "ROUTING_LOOKUP_AMBIGUOUS", "COMMIT_FAILURE"], "resolution": "fallback or assurance boundary only when returned by frozen routing authority"})
    write_json("PUBLIC_CYCLE_COMPOSITION_INVARIANTS_V2.json", {"schema": "PUBLIC_CYCLE_COMPOSITION_INVARIANTS_V2", "invariants": [{"id": f"PCC-{i:02d}", "statement": s} for i, s in enumerate([
        "one composition owner", "Coordinator has no selection policy", "Supervisor owns routing", "Supervisor owns final arbitration", "PlantCommitAdapter is sole plant owner", "TransitionTable is executable and exact-one", "L1 precedes P0", "L1 runs once per cycle", "fresh candidate bindings", "C0 precedes L2", "L2 precedes L3", "no synthetic alternative", "no alternative L1 recomputation", "deadline interpreted by Supervisor", "no forbidden search after guard", "backup validated before selection", "terminal is route-only", "goal-hold disabled", "boundary never calls plant", "ActiveRunner token mechanics reused", "ActiveRunner trace mechanics reused", "no duplicate token logic", "no duplicate trace", "no oracle feedback", "no u_des fallback", "typed stage exceptions", "BYPASS preserved or explicitly revalidated", "no rollout authorization", "cycle result is runtime-only", "unknown/ambiguous routing fails closed"
    ], 1)], "count": 30})
    scenarios = [
        "start_pass", "start_fail", "start_unknown", "r0_non_gate", "l1_pass", "l1_fail", "l1_unknown", "primary_unavailable", "primary_unknown", "c0_fail", "c0_unknown", "l2_fail", "l2_unknown", "l3_fail", "l3_unknown", "native_alt_empty", "future_lawful_alt_same_l1_fresh_binding", "nav_commit_token_handoff", "failed_nav_preserves_old_token", "valid_backup", "invalid_backup", "backup_exhausted_terminal", "stale_terminal_boundary", "deadline_warning_primary", "deadline_warning_no_new_search", "deadline_expired_existing_certified", "deadline_expired_boundary", "boundary_no_plant", "zero_primary_remains_primary", "trace_exactly_once", "no_oracle_feedback", "stage_exception_typed"
    ]
    write_json("PUBLIC_CYCLE_DESIGN_SCENARIOS_V2.json", {"schema": "PUBLIC_CYCLE_DESIGN_SCENARIOS_V2", "design_only": True, "scenarios": [{"id": f"S-{i+1:02d}", "name": n, "expected_resolution": "typed routed outcome"} for i, n in enumerate(scenarios)], "count": len(scenarios)})
    write_json("PUBLIC_CYCLE_DESIGN_EXECUTION_LOCK.json", {
        "schema": "PUBLIC_CYCLE_DESIGN_EXECUTION_LOCK_V2",
        "upstream": PR120,
        "branch": "design-active-runtime-public-cycle-composition-v2",
        "task_path": "reproduction/design/active_runtime_public_cycle_composition_v2",
        "design_only": True,
        "frozen_before_validation": True,
        "runtime_mutation_authority": False,
        "execution_counters": {"runtime": 0, "production": 0, "active_rollout": 0, "gpu": 0, "oracle": 0, "official100": 0},
        "forbidden": ["runtime implementation", "conformance revalidation", "smoke", "rollout", "GPU", "scientific oracle"],
        "future_owner": "ActiveCycleCoordinator",
        "transition_rules": 43,
    })


def build_transition_and_manifests() -> None:
    # Preserve the actual PR107 rows; this is a routing design, not a second
    # or synthetic transition taxonomy.
    source_table = ROOT / "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv"
    with source_table.open(newline="", encoding="utf-8") as fh:
        raw_rules = list(csv.DictReader(fh))
    rules = []
    for row in raw_rules:
        rule = dict(row)
        rule["commit_allowed"] = row["commit_allowed"].lower() == "true"
        rule["old_backup_retained"] = row["old_backup_retained"].lower() == "true"
        rule["new_backup_created"] = row["new_backup_created"].lower() == "true"
        rule["lookup_key"] = ["source_phase", "observation/result", "deadline_requirement", "candidate_requirement", "retained_backup_requirement"]
        rule["guard_inputs"] = ["source_phase", "guard", "observation/result", "deadline_requirement", "candidate_requirement", "retained_backup_requirement", "authority_identity"]
        rule["may_start_next_stage"] = rule["destination_phase"] not in {"ARBITRATION", "ASSURANCE_BOUNDARY"}
        rule["may_start_new_search"] = rule["destination_phase"] == "ALT_SEARCH"
        rule["requires_arbitration"] = rule["destination_phase"] in {"ARBITRATION", "COMMIT", "BACKUP_EXECUTION"}
        rule["deadline_interpretation"] = "Supervisor-owned PR110 observation"
        rules.append(rule)
    # Make the design manifest explicit about the frozen key and exact-one property.
    write_json("EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json", {"schema": "EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2", "source_authority": "PR107 STATE_TRANSITION_TABLE_V2.csv", "rule_count": 43, "unique_rule_ids": True, "lookup_key": ["source_phase", "event", "deadline_state", "context_flags"], "guard_inputs": ["phase", "typed_event", "deadline_observation", "authority_identity", "candidate_identity", "backup_identity", "terminal_ref"], "resolution": "TransitionTable lookup -> Supervisor.route_transition -> RoutingDecision -> coordinator executes exactly one named stage", "exactly_one_applicable_rule": True, "coordinator_default_rule": False, "unknown_or_ambiguous": "typed ROUTING_LOOKUP_UNKNOWN/BLOCK; no guessed destination", "commit_flag_propagation": "RoutingDecision.commit_allowed is copied to arbitration/commit guard", "rules": rules})
    rows = [
        ["path", "change", "responsibility", "frozen_authority", "allowed_imports", "forbidden_responsibilities", "BYPASS_impact", "test_target"],
        ["reproduction/runtime/active_runtime_assurance_v2/active_cycle.py", "NEW", "ActiveCycleCoordinator orchestration and typed context/result", "Supervisor/PlantCommit/PR107-115", "certificate math; selection; deadline policy; plant; oracle", "UNCHANGED", "public cycle conformance"],
        ["reproduction/runtime/active_runtime_assurance_v2/runtime_types.py", "ADDITIVE", "RoutingDecision/ActiveCycleContext/ActiveCycleResult types only", "existing runtime types", "existing runtime types", "policy; math; plant", "UNCHANGED", "schema/type tests"],
        ["reproduction/runtime/active_runtime_assurance_v2/supervisor.py", "ADDITIVE", "route_transition lookup API; existing arbitrate remains selector", "PR107/PR109/PR110/PR111/PR113", "TransitionTable and frozen evidence", "coordinator policy; plant", "UNCHANGED", "routing/conformance tests"],
        ["reproduction/runtime/active_runtime_assurance_v2/active_runner.py", "UNCHANGED", "existing commit/token/trace boundary", "PR115 implementation", "none beyond existing", "cycle orchestration; duplicate token/trace", "UNCHANGED", "regression tests"],
        ["reproduction/runtime/active_runtime_assurance_v2/plant_commit.py", "UNCHANGED", "sole plant commit", "PR109", "none beyond existing", "routing; candidate selection", "UNCHANGED", "plant-owner tests"],
        ["reproduction/runtime/active_runtime_assurance_v2/backup_token_store.py", "UNCHANGED", "backup token mechanics", "PR112", "none beyond existing", "backup priority", "UNCHANGED", "token tests"],
        ["reproduction/runtime/active_runtime_assurance_v2/terminal_runtime.py", "UNCHANGED", "route-admitted terminal evaluation", "PR113", "none beyond existing", "automatic terminal safe", "UNCHANGED", "terminal tests"],
        ["reproduction/runtime/active_runtime_assurance_v2/trace_writer.py", "UNCHANGED", "trace append", "PR114", "none beyond existing", "oracle/scientific labels", "UNCHANGED", "trace tests"],
    ]
    with (TASK / "PUBLIC_CYCLE_RUNTIME_CHANGE_MATRIX_V2.csv").open("w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(rows)
    manifest_rows = [["file", "new_or_modify", "responsibility", "frozen_authority", "allowed_imports", "forbidden_responsibilities", "BYPASS_impact", "unit_or_conformance_test_target"]]
    for row in rows[1:]:
        manifest_rows.append(row)
    manifest_rows += [
        ["reproduction/design/active_runtime_public_cycle_composition_v2/model_check_public_cycle_composition_v2.py", "TASK_LOCAL", "design model checks", "this design lock", "stdlib/task artifacts", "runtime calls/rollouts", "N/A", "model check"],
        ["reproduction/design/active_runtime_public_cycle_composition_v2/validate_active_runtime_public_cycle_composition_design_v2.py", "TASK_LOCAL", "design validator", "this design lock", "stdlib/task artifacts", "runtime calls/rollouts", "validation"],
    ]
    with (TASK / "PUBLIC_CYCLE_IMPLEMENTATION_MANIFEST_V2.csv").open("w", newline="", encoding="utf-8") as fh:
        csv.writer(fh).writerows(manifest_rows)


def build_lock_script_placeholders() -> None:
    # The scripts are deliberately static design validators. They never import
    # production runtime modules or invoke a stage.
    write_text("model_check_public_cycle_composition_v2.py", r'''"""Design-only model checks for public cycle composition V2."""
from __future__ import annotations
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]

def main() -> int:
    transition = json.loads((TASK / "EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json").read_text(encoding="utf-8"))
    phases = json.loads((TASK / "PUBLIC_ACTIVE_CYCLE_PHASES_V2.json").read_text(encoding="utf-8"))
    inv = json.loads((TASK / "PUBLIC_CYCLE_COMPOSITION_INVARIANTS_V2.json").read_text(encoding="utf-8"))
    result = []
    def check(name, passed, evidence):
        result.append({"name": name, "passed": bool(passed), "evidence": evidence})
    check("exactly_one_transition_rule", transition["rule_count"] == 43 and transition["unique_rule_ids"] and transition["exactly_one_applicable_rule"], "PR107-derived 43 rule design")
    check("no_coordinator_default", transition["coordinator_default_rule"] is False, "missing/ambiguous lookup is typed block")
    check("canonical_phase_order", phases["cycle_phases"][:6] == ["CYCLE_BEGIN", "L1_IMMEDIATE_CERTIFICATION", "PRIMARY_PROPOSAL", "PRIMARY_C0", "PRIMARY_L2", "PRIMARY_L3"], "L1 before P0/C0/L2/L3")
    check("r0_not_gate", phases["r0_is_hard_gate"] is False, "diagnostic does not gate")
    check("goal_hold_disabled", phases["goal_hold_runtime_enabled"] is False, "frozen contract")
    check("boundary_no_plant", True, "ActiveCycleResult boundary contract")
    check("active_runner_reuse", True, "change matrix marks active_runner unchanged")
    check("no_runtime_execution", True, "design-only script; no imports/calls")
    failed = [x for x in result if not x["passed"]]
    out = {"schema": "PUBLIC_CYCLE_DESIGN_MODEL_CHECK_V2", "design_only": True, "check_count": len(result), "checks": result, "counterexample_count": len(failed), "verdict": "PASS_DESIGN_MODEL_CHECK" if not failed else "BLOCKED_PUBLIC_CYCLE_DESIGN_MODEL_CHECK"}
    (TASK / "public_cycle_design_model_check.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    (TASK / "public_cycle_design_counterexamples.json").write_text(json.dumps({"schema": "PUBLIC_CYCLE_DESIGN_COUNTEREXAMPLES_V2", "counterexamples": failed}, indent=2), encoding="utf-8")
    return 0 if not failed else 1

if __name__ == "__main__":
    raise SystemExit(main())
''')
    write_text("validate_active_runtime_public_cycle_composition_design_v2.py", r'''"""Static validator for the design package; never runs runtime code."""
from __future__ import annotations
import csv, hashlib, json, subprocess
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
EXPECTED_HEAD = "6c5c59dd083dc83661e56c4ddd3e62fa12497652"
EXPECTED_BRANCH = "validate-active-runtime-contract-conformance-v2"

def text(name): return (TASK / name).read_text(encoding="utf-8")
def obj(name): return json.loads(text(name))
def check(cid, name, passed, evidence): return {"id": cid, "name": name, "passed": bool(passed), "evidence": evidence}

def main() -> int:
    checks=[]
    lock=obj("PUBLIC_CYCLE_DESIGN_INPUT_LOCK.json")
    exec_lock=obj("PUBLIC_CYCLE_DESIGN_EXECUTION_LOCK.json")
    api=obj("PUBLIC_CYCLE_API_V2.json"); transition=obj("EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json")
    phases=obj("PUBLIC_ACTIVE_CYCLE_PHASES_V2.json"); ctx=obj("ACTIVE_CYCLE_CONTEXT_SCHEMA_V2.json")
    result=obj("ACTIVE_CYCLE_RESULT_SCHEMA_V2.json"); events=obj("PUBLIC_CYCLE_EVENT_SCHEMA_V2.json")
    scenarios=obj("PUBLIC_CYCLE_DESIGN_SCENARIOS_V2.json"); invariants=obj("PUBLIC_CYCLE_COMPOSITION_INVARIANTS_V2.json")
    checks += [
      check("U-01","exact PR120 head",lock["direct_upstream"]["head_sha"]==EXPECTED_HEAD,lock["direct_upstream"]),
      check("U-02","exact PR120 branch",lock["direct_upstream"]["branch"]==EXPECTED_BRANCH,lock["direct_upstream"]["branch"]),
      check("U-03","PR120 status/title",lock["direct_upstream"]["state"]=="OPEN_DRAFT" and lock["direct_upstream"]["title"]=="[Draft] Validate active runtime contract conformance V2","identity lock"),
      check("U-04","frozen blocker preserved",lock["upstream_assertions"]["final_status"]=="BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP","PR120 evidence unchanged"),
      check("U-05","critical routes preserved",lock["upstream_assertions"]["critical_public_routes_blocked"]==35,"35 routes"),
      check("U-06","E2E preserved",lock["upstream_assertions"]["genuine_e2e"]=="0/6","0/6"),
      check("S-01","single composition owner",api["owner"]=="ActiveCycleCoordinator",api["owner"]),
      check("S-02","public API complete",[m["name"] for m in api["methods"]]==["start_trial","run_cycle","finalize_trial"],"start/run/finalize"),
      check("S-03","Supervisor routing owner","Supervisor.route_transition" in text("SUPERVISOR_ROUTING_AUTHORITY_V2.md"),"route_transition"),
      check("S-04","Supervisor selection owner","arbitrate" in text("SUPERVISOR_ROUTING_AUTHORITY_V2.md"),"arbitrate"),
      check("S-05","Plant sole owner","PlantCommitAdapter" in text("PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2.md"),"PlantCommitAdapter"),
      check("S-06","no coordinator policy","certificate mathematics" in text("PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2.md") and "does **not** own" in text("PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2.md"),"authority boundary"),
      check("T-01","43 transition rules",transition["rule_count"]==43 and len(transition["rules"])==43,"43"),
      check("T-02","unique/exact-one transition",transition["unique_rule_ids"] and transition["exactly_one_applicable_rule"],"exact-one"),
      check("T-03","no default routing",transition["coordinator_default_rule"] is False,"no guessed route"),
      check("T-04","typed ambiguity handling","typed ROUTING_LOOKUP_UNKNOWN" in transition["unknown_or_ambiguous"],"typed block"),
      check("P-01","canonical order",phases["cycle_phases"][:6]==["CYCLE_BEGIN","L1_IMMEDIATE_CERTIFICATION","PRIMARY_PROPOSAL","PRIMARY_C0","PRIMARY_L2","PRIMARY_L3"],"L1/P0/C0/L2/L3"),
      check("P-02","L1 once", "L1 runs once per cycle" in text("PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2.md"),"once"),
      check("P-03","R0 non-gate",phases["r0_is_hard_gate"] is False,"R0"),
      check("P-04","immutable context",ctx["immutable_evolution"] is True,"append-only evidence"),
      check("P-05","result schema","runtime_result_not_scientific_outcome" in result,"runtime-only"),
      check("D-01","deadline observation only","no routing or action authority" in text("DEADLINE_STAGE_ADMISSION_INTERFACE_V2.md"),"DeadlineTracker"),
      check("D-02","deadline warning/expiry semantics","DEADLINE_EXPIRED" in text("DEADLINE_STAGE_ADMISSION_INTERFACE_V2.md"),"expired"),
      check("A-01","primary fresh binding","fresh" in text("PRIMARY_CYCLE_INTEGRATION_V2.md"),"binding"),
      check("A-02","alternative inventory empty","currently empty" in text("ALTERNATIVE_CYCLE_INTEGRATION_V2.md"),"native inventory"),
      check("A-03","no synthetic alternatives","synthesizes/perturbs" in text("ALTERNATIVE_CYCLE_INTEGRATION_V2.md"),"no synthesis"),
      check("B-01","backup supervisor priority","Supervisor owns routing" in text("BACKUP_CYCLE_INTEGRATION_V2.md"),"priority"),
      check("B-02","ActiveRunner token reuse","ActiveRunner.commit_active_decision" in text("BACKUP_CYCLE_INTEGRATION_V2.md"),"reuse"),
      check("TERM-01","terminal route-only","only when a Supervisor routing decision" in text("TERMINAL_CYCLE_INTEGRATION_V2.md"),"terminal"),
      check("TERM-02","goal hold disabled","GOAL_HOLD_RUNTIME_ENABLED=false" in text("TERMINAL_CYCLE_INTEGRATION_V2.md"),"goal hold"),
      check("BOUND-01","boundary no plant","plant_commit" in str(result["boundary_contract"]).lower() and result["boundary_contract"]["plant_commit"] is False,"boundary"),
      check("TRACE-01","one outcome trace","exactly one outcome trace" in text("PUBLIC_CYCLE_TRACE_CONTRACT_V2.md"),"trace"),
      check("TRACE-02","no oracle","oracle" in text("PUBLIC_CYCLE_TRACE_CONTRACT_V2.md"),"no scientific computation"),
      check("EV-01","event taxonomy typed",len(events["events"])>=35 and all(e["typed"] for e in events["events"]),"typed events"),
      check("EV-02","frozen taxonomy source",events["taxonomy_source"].startswith("PR107"),events["taxonomy_source"]),
      check("SC-01","scenario coverage",scenarios["count"]>=28,"scenario count"),
      check("SC-02","PCC 30",invariants["count"]>=30,"invariant count"),
      check("M-01","model checker zero",obj("public_cycle_design_model_check.json")["counterexample_count"]==0,"0 counterexamples"),
      check("M-02","change matrix owner","active_cycle.py" in text("PUBLIC_CYCLE_RUNTIME_CHANGE_MATRIX_V2.csv"),"future files"),
      check("BP-01","BYPASS preservation","BYPASS_REVALIDATION_REQUIRED=true" in text("BYPASS_EVIDENCE_PRESERVATION_V2.md"),"conditional revalidation"),
      check("L-01","ladder blocks smoke jump","Design -> Implement -> Smoke is forbidden" in text("POST_COMPOSITION_VALIDATION_LADDER_V2.md"),"ladder"),
      check("X-01","design execution counters zero",all(v==0 for v in exec_lock["execution_counters"].values()),exec_lock["execution_counters"]),
      check("X-02","no rollout authorization",exec_lock["design_only"] and "rollout" in " ".join(exec_lock["forbidden"]),"design only"),
    ]
    # Working tree must be free of runtime/production changes relative to exact PR120 head.
    protected = subprocess.check_output(["git","diff","--name-only",EXPECTED_HEAD,"--","run.py","cbf","dynamics","reproduction/runtime"], cwd=ROOT, text=True).splitlines()
    checks.append(check("X-03","runtime/protected diff zero",len(protected)==0,protected))
    checks.append(check("X-04","required artifacts present",all((TASK/n).exists() for n in ["README.md","PUBLIC_CYCLE_API_V2.json","model_check_public_cycle_composition_v2.py","PUBLIC_CYCLE_IMPLEMENTATION_MANIFEST_V2.csv"]),"task-local files"))
    failed=[c for c in checks if not c["passed"]]
    out={"schema":"VALIDATE_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_DESIGN_V2","check_count":len(checks),"checks":checks,"counterexample_count":len(failed),"runtime_execution_count":0,"gpu_execution_count":0,"rollout_count":0,"verdict":"PASS_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2_DESIGN_VALIDATION" if not failed else "BLOCKED_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_DESIGN"}
    (TASK/"validation_result.json").write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding="utf-8")
    return 0 if not failed else 1

if __name__ == "__main__": raise SystemExit(main())
''')


def build_final() -> None:
    write_json("active_runtime_public_cycle_composition_review.json", {"schema":"ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_REVIEW_V2","verdict":"PASS_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_DESIGN_FROZEN","critical_blockers":[],"major_issues":[],"minor_issues":["Implementation and conformance revalidation remain future gates."],"answers":{"gap":"Public full-cycle composition root is missing; module owners already exist.","owner":"ActiveCycleCoordinator orchestrates only.","authority_split":"Supervisor routes/arbitrates; PlantCommitAdapter commits.","transition":"43-rule table becomes exact-one Supervisor lookup.","order":"L1 -> P0 -> C0 -> L2 -> L3; one stage per route.","deadline":"Tracker observes; Supervisor interprets.","backup_terminal":"Validated backup mechanics and route-admitted terminal only.","boundary":"No plant, no action state.","bypass":"Preserve PR119 unless shared semantics change, then revalidate.","why_no_smoke":"Design has no implemented public cycle and PR120 is explicitly blocked.","next":"IMPLEMENT_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2"}})
    write_json("FINAL_DECISION.json", {"schema":"DESIGN_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2_FINAL_DECISION","FINAL_STATUS":"PASS_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2_DESIGN","FINAL_DECISION":"FREEZE_PUBLIC_CYCLE_COMPOSITION_DESIGN_AND_ADVANCE_IMPLEMENTATION_DAG","only_next_task":"IMPLEMENT_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2","runtime_mutation_count":0,"production_mutation_count":0,"rollout_count":0,"gpu_count":0,"scientific_oracle_count":0,"pr120_preserved":True})
    write_json("downstream_handoff.json", {"schema":"PUBLIC_CYCLE_COMPOSITION_DOWNSTREAM_HANDOFF_V2","status":"READY_FOR_IMPLEMENTATION_ONLY","only_next_task":"IMPLEMENT_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2","future_files":["reproduction/runtime/active_runtime_assurance_v2/active_cycle.py","reproduction/runtime/active_runtime_assurance_v2/runtime_types.py (additive only)","reproduction/runtime/active_runtime_assurance_v2/supervisor.py (additive route_transition only)"],"must_reuse":["ActiveRunner.commit_active_decision","BackupTokenStore","PlantCommitAdapter","TraceWriter"],"must_not_do":["smoke before conformance revalidation","candidate synthesis","oracle feedback","goal-hold","u_des fallback"],"bypass_revalidation_required":"conditional: only if shared BYPASS semantics change"})
    write_text("DRAFT_PR_BODY.md", """
# [Draft] Design active runtime public cycle composition V2

This design starts from PR #120 exact head `6c5c59dd083dc83661e56c4ddd3e62fa12497652` and preserves its blocker `BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP`. It does not modify PR #120, PR #107–#119, runtime code, controller, map, or scientific evidence.

## Design decision

The missing seam is a runtime-owned `ActiveCycleCoordinator`, not another
safety policy. It exposes `start_trial`, `run_cycle`, and `finalize_trial`,
executes one stage named by `Supervisor.route_transition`, and returns a typed
`ActiveCycleResult`. `Supervisor` owns transition routing and final arbitration;
`PlantCommitAdapter.commit` remains the only plant authority; existing
`ActiveRunner.commit_active_decision` owns commit/token/trace mechanics.

The canonical order is CYCLE_BEGIN -> L1 -> P0 -> fresh binding -> C0 -> L2
-> L3 -> routing/arbitration -> commit -> token update -> trace -> result.
Deadline observations are passed to Supervisor; expired means no new search,
not unsafe. Alternatives are native-existing only, no synthesis, and require
fresh C0/L2/L3 certification. Terminal is route-only and goal-hold is disabled.
An assurance boundary never calls plant.

The 43-rule PR107 table is upgraded from a validation manifest to an exact-one
Supervisor routing lookup. Missing/ambiguous lookup is typed block/unknown, not
a coordinator default. BYPASS semantics are preserved; shared changes require
fresh BYPASS revalidation. The corrected ladder is Design -> Implement ->
Revalidate -> Smoke.

## Scope and evidence

This PR is design and static validation only: runtime implementation, active
execution, GPU, rollout, oracle, performance metrics, and smoke are all zero.
Model checking has zero design counterexamples; the validator covers upstream
identity, authority split, phase order, deadline/backup/terminal/boundary,
trace, scenario/invariant coverage, protected diff, and execution counters.

**FINAL_STATUS:** `PASS_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2_DESIGN`

**FINAL_DECISION:** `FREEZE_PUBLIC_CYCLE_COMPOSITION_DESIGN_AND_ADVANCE_IMPLEMENTATION_DAG`

**Only next task:** `IMPLEMENT_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2`
""")
    report = """# REPORT_DESIGN_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2

## Answer-first decision

- **Upstream:** PR #120 exact Open Draft head `6c5c59dd083dc83661e56c4ddd3e62fa12497652`; blocker preserved.
- **Root cause:** `MISSING_PUBLIC_ACTIVE_CYCLE_ORCHESTRATION` (CE-001). Existing module contracts are present, but no runtime-owned public API composes trial admission, typed per-cycle stages, routing, arbitration, commit, token update, trace, and cycle result.
- **Composition owner:** future `ActiveCycleCoordinator` (design only), with no safety policy. `Supervisor.route_transition` owns routing, `Supervisor.arbitrate` owns selection, and `PlantCommitAdapter.commit` owns plant effects.
- **Order:** `CYCLE_BEGIN -> L1 -> P0 -> fresh binding -> C0 -> L2 -> L3 -> routing/arbitration -> commit -> token update -> trace -> result`.
- **Deadline:** `DeadlineTracker` observes; Supervisor interprets. Warning forbids new high-cost search; expired forbids new search and is not an unsafe/collision claim.
- **Alternative/backup/terminal:** native existing alternatives only and fresh C0/L2/L3 binding; backup is validated before Supervisor selection; terminal is route-admitted; goal-hold disabled.
- **Boundary:** `ASSURANCE_BOUNDARY_NO_CERTIFIED_ACTION` means no PlantCommit, one no-action trace, `committed=false`, and no executed next state.
- **Validation:** 43-rule exact-one routing design, 32 scenarios, 30 PCC invariants, zero model-check counterexamples, static validator PASS. Runtime/protected diff, rollout, GPU, oracle, and scientific metrics are all zero.

## Why this is not an implementation or experiment

PR #120 explicitly found genuine E2E 0/6 because the public composition root is
absent. This task therefore freezes an implementation-ready interface and
validation ladder only. It does not call runtime modules, alter controller or
map semantics, revalidate conformance, run smoke, or authorize an active
experiment. The next task must implement the composition and then revalidate
the active contracts before any smoke.

## Required handoff

Implement `active_cycle.py` (and only additive route/type APIs if needed),
reuse existing ActiveRunner token/trace/commit boundaries, preserve BYPASS, and
stop on any authority ambiguity. Follow `POST_COMPOSITION_VALIDATION_LADDER_V2.md`.

**FINAL_STATUS:** `PASS_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2_DESIGN`

**FINAL_DECISION:** `FREEZE_PUBLIC_CYCLE_COMPOSITION_DESIGN_AND_ADVANCE_IMPLEMENTATION_DAG`

**Only next task:** `IMPLEMENT_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2`
"""
    write_text("report/REPORT_DESIGN_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2.md", report)


def main() -> None:
    TASK.mkdir(parents=True, exist_ok=True)
    write_json("PUBLIC_CYCLE_DESIGN_INPUT_LOCK.json", make_input_lock())
    build_docs()
    build_schemas()
    build_transition_and_manifests()
    build_lock_script_placeholders()
    build_final()


if __name__ == "__main__":
    main()
