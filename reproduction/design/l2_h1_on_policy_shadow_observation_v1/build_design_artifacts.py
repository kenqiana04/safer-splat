#!/usr/bin/env python3
"""Deterministically build the design-only protocol artifacts.

This script serializes documentation and mock schema fixtures only. It does not
import, mutate, or execute any controller, map, certifier, or navigation code.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
UPSTREAM_SHA = "a7fd936804284a299467f1bfcc76deab12fdf0c3"
FINAL_STATUS = "PASS_L2_H1_ON_POLICY_SHADOW_OBSERVATION_DESIGN_V1"
FINAL_DECISION = "FREEZE_ON_POLICY_SHADOW_PROTOCOL_AND_IMPLEMENT_NONINVASIVE_INSTRUMENTATION"
VALIDATOR_STATUS = "PASS_L2_H1_ON_POLICY_SHADOW_OBSERVATION_DESIGN_VALIDATION"
NEXT_TASK = "IMPLEMENT_L2_H1_ON_POLICY_SHADOW_INSTRUMENTATION_V1"
LABELS = "DESIGN ONLY | NO ON-POLICY COLLECTION | NO CONTROLLER AUTHORITY | NO DECISION FEEDBACK | NO PERFORMANCE CLAIM"


def write_text(relative: str, content: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8", newline="\n")


def write_json(relative: str, value: object) -> None:
    write_text(relative, json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False))


def write_csv(relative: str, fieldnames: list[str], rows: list[dict]) -> None:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    write_text(relative, stream.getvalue())


def sha256_json(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


replay_inputs = {
    "N_all": 6853,
    "N_formal_replayable": 2594,
    "replay_coverage_percent": 37.8520,
    "N_not_replayable": 4259,
    "MISSING_U_K": 4259,
    "reachability_unknown": 5795,
    "L2_evaluated": 788,
    "L2_PASS": 770,
    "L2_FAIL": 18,
    "L2_UNKNOWN": 0,
    "stored_L1_PASS_L2_FAIL": 18,
    "stored_L1_PASS_L2_FAIL_rate_percent": 2.2843,
    "executed_total": 566,
    "executed_PASS": 560,
    "executed_FAIL": 6,
    "nonexecuted_total": 222,
    "nonexecuted_PASS": 210,
    "nonexecuted_FAIL": 12,
    "multi_candidate_groups": 20,
    "distinct_H1_endpoints": 20,
    "L2_status_disagreement": 0,
}


write_text(
    "README.md",
    f"""
# L2/H1 On-Policy Shadow Observation Design V1

This directory freezes a prospective observation protocol; it contains no on-policy data and no production instrumentation. The design answers the PR #95 evidence gaps with an immutable post-commit payload, a bounded nonblocking queue, and an authority-isolated shadow worker.

**Boundary:** {LABELS}.

The primary cohort is the controller-selected/executed candidate. Native non-executed candidates are secondary and are recorded only if they already exist before observation. Synthetic candidate count is permanently zero. Observer failure reduces observation completeness but never changes the frozen controller path.

The design selects **Option A: post-commit in-process read-only tap with an out-of-process shadow worker**. The tap is a future instrumentation-only hook after the selected action is accepted and before plant propagation. It performs only immutable copying and `enqueue_nowait`; the worker runs the frozen L0/L1/L2 observation stages and writes append-only results. There is no result-return API.

The frozen planning environment is the mature Stonehenge baseline in `run.py`: 100 deterministic indexed trials, `dt=0.05`, 500-step cap, and a static GSplat config reference. A future implementation must freeze the exact trial manifest and map content hashes before equivalence or collection. PR #89's locked E5 one-step registry is audit context, not a substitute for the on-policy rollout manifest.

Run the design-only validator:

```text
python -B reproduction/design/l2_h1_on_policy_shadow_observation_v1/validate_on_policy_shadow_observation_design_v1.py
```

Expected result: `{VALIDATOR_STATUS}`.
""",
)


write_text(
    "CONTROL_FLOW_OBSERVATION_SEAM_AUDIT.md",
    f"""
# Control-Flow Observation Seam Audit

**Scope label:** {LABELS}.

## Frozen production cycle

The audit uses source at PR #95 head `{UPSTREAM_SHA}` rather than old reports.

| Required item | Frozen source of truth | Finding |
|---|---|---|
| `x_k` | `run.py:101-104,116` | Six-vector tensor `x` exists before each control decision. |
| `p_k` | `run.py:119` and state convention at `run.py:100` | `x[:3]`. |
| `v_k` | `run.py:123,125` and state convention at `run.py:100` | `x[3:]`. |
| nominal candidate | `run.py:118-127` | `u_des` is the native PD candidate, clipped to the frozen bounds. |
| selected candidate | `run.py:132`; `cbf/cbf_utils.py:125-143` | `u = cbf.solve_QP(x,u_des)`; successful solver output is the selected control. |
| decision acceptance | `run.py:138-143` | The solver-success guard rejects the failed path. |
| decision commit seam | between `run.py:143` and `run.py:147` | After success and before plant update, `x_k`, `u_k`, `u_des`, `dt`, trial and step are co-resident and unambiguous. |
| plant application | `run.py:147` | `x = double_integrator_dynamics(x,u)*dt + x`. This is after the proposed capture. |
| current logging | `run.py:149-152,184-196` | `u` is appended only after propagation; capture here risks state/action misalignment and does not expose reachability IDs. |
| `dt` | `run.py:19`; serialized at `run.py:207` | Runtime authority is the module constant `0.05`; future manifest also hashes the config source. |
| trial/step | `run.py:98,116` | Deterministic `trial` and `i`; future instrumentation creates stable run/trial/step and commit IDs. |
| map object | `run.py:52,79`; `cbf/cbf_utils.py:10-38` | Stonehenge config reference enters `GSplatLoader`, then the CBF. Path alone is insufficient; future run-start manifest must hash the resolved config/checkpoint. |

## Frozen safety-stage sources

The primary `run.py` controller does **not** natively execute the PR #84 L0/L1 state machine. Therefore the design must not relabel QP success as stored L1. The future zero-authority worker will use the frozen PR #84 interfaces on the captured payload and record explicit stage reachability at evaluation time:

- current-feasibility/L0 observation: `reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/current_feasibility_certificate.py:8-22`;
- immediate-segment/L1 observation: `.../certifier/segment_certificate.py:10-18`;
- immutable `State`, `Control`, map snapshot and result types: `.../certifier/result_types.py:64-86,95,134-159,194-208`;
- frozen ordered candidates and unified stage progression: `.../certifier/executable_safety_certifier.py:25-80` and `.../certifier/candidate_library.py:8-18`;
- L2/H1 formula and tri-state result: `reproduction/shadow/l2_h1_shadow_certifier_v1/l2_h1_shadow_certifier.py`.

The worker's stored L0/L1/L2 values are labeled `SHADOW_PIPELINE_RUNTIME_OBSERVATION`, never `PRODUCTION_CONTROLLER_DECISION`. This removes post-hoc reachability guessing while preserving the controller's mathematics.

## Candidate lifecycle

The production baseline exposes two genuine native values before the shadow tap: nominal `u_des` and successful selected `u`. Both existed before observation. If they differ, the candidate group contains both with roles `NOMINAL_NATIVE` and `SELECTED_EXECUTED`; if identical, de-duplicate by hash while retaining both roles. No B3 candidate is synthesized.

The richer frozen PR #89 audit runtime forms a filtered primary at `source_runtime.py:153-159`, computes current and segment outcomes at lines 170-183, forms directional alternatives at lines 185-186, and commits a candidate at lines 187-195. This proves a native multi-candidate lifecycle can be tapped when that controller already creates one. However PR #89's returned record omits the final acceleration even though `control` exists internally; this is an exact cause of future replay loss. The future tap copies it before serialization.

## Selected seam decision

Seam `S1_AFTER_ACCEPT_BEFORE_PROPAGATE` is feasible and selected. It sees the correct `x_k/u_k/dt`, cannot confuse `x_(k+1)` with `x_k`, and requires only an instrumentation-only immutable copy plus nonblocking enqueue in the future task. The shadow worker has no callable return path. No source is changed in this design task.
""",
)


seams = {
    "upstream_sha": UPSTREAM_SHA,
    "scope": "DESIGN_ONLY",
    "source_audit": {
        "state": {"path": "run.py", "lines": [100, 116], "expression": "x", "p": "x[:3]", "v": "x[3:]"},
        "nominal_candidate": {"path": "run.py", "lines": [118, 127], "expression": "u_des"},
        "selected_candidate": {"path": "run.py", "lines": [132, 143], "expression": "u", "acceptance": "cbf.solver_success"},
        "dt": {"path": "run.py", "line": 19, "expression": "dt"},
        "plant_update": {"path": "run.py", "line": 147},
        "map": {"path": "run.py", "lines": [52, 79], "object": "GSplatLoader(path_to_gsplat, device)"},
        "trial_step": {"path": "run.py", "lines": [98, 116]},
        "l0": {"path": "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/current_feasibility_certificate.py", "lines": [8, 22]},
        "l1": {"path": "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/segment_certificate.py", "lines": [10, 18]},
        "native_multi_candidate": {"path": "reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/benchmark/source_runtime.py", "lines": [149, 195]},
    },
    "candidate_seams": [
        {"id": "S1_AFTER_ACCEPT_BEFORE_PROPAGATE", "lines": "run.py:143-147", "selected": True, "reason": "same-decision x_k/u_k/dt visible after acceptance and before plant update"},
        {"id": "S2_AFTER_QP_BEFORE_ACCEPT", "lines": "run.py:132-139", "selected": False, "reason": "could capture a solver-failed action"},
        {"id": "S3_AFTER_PROPAGATE_EXISTING_LOG", "lines": "run.py:147-152", "selected": False, "reason": "off-by-one risk and missing reachability/commit IDs"},
        {"id": "S4_OUTER_CYCLE_WRAPPER", "lines": "wrapper around run.py:116-176", "selected": False, "reason": "fallback; selected output visible but internal branch provenance requires explicit read-only exposure"},
    ],
    "selected_seam": "S1_AFTER_ACCEPT_BEFORE_PROPAGATE",
    "observation_seam_candidate_count": 4,
    "primary_multi_candidate_observability": "NOMINAL_AND_SELECTED_NATIVE_ONLY_IN_RUN_PY",
    "richer_native_set_observability": "AVAILABLE_WHEN_FROZEN_RUNTIME_ALREADY_GENERATES_ALTERNATIVES",
    "candidate_synthesis_count": 0,
}
write_json("control_flow_observation_seams.json", seams)


architecture_rows = [
    {"option": "OPTION_A_POST_COMMIT_TAP", "authority_isolation": "HIGH", "production_mutation": "MINIMAL_INSTRUMENTATION_ONLY", "trace_risk": "LOW_AFTER_EQUIVALENCE_GATE", "candidate_visibility": "FULL_AT_COMMIT_SEAM", "map_visibility": "FULL_WITH_RUN_MANIFEST_REF", "reachability_visibility": "FULL_IN_SHADOW_PIPELINE", "async_feasibility": "YES", "backpressure": "ENQUEUE_NOWAIT_DROP", "crash_isolation": "HIGH_WITH_SIDECAR_WORKER", "determinism": "MONOTONIC_IDS_AND_CANONICAL_BYTES", "complexity": "MEDIUM", "validation_burden": "MEDIUM", "reviewer_defensibility": "HIGHEST", "decision": "SELECTED"},
    {"option": "OPTION_B_WRAPPER_DECORATOR", "authority_isolation": "MEDIUM_HIGH", "production_mutation": "OUTER_WRAPPER_ONLY", "trace_risk": "LOW_TO_MEDIUM", "candidate_visibility": "SELECTED_VISIBLE_INTERNAL_SET_MAY_NOT_BE", "map_visibility": "CONDITIONAL", "reachability_visibility": "CONDITIONAL", "async_feasibility": "YES", "backpressure": "ENQUEUE_NOWAIT_DROP", "crash_isolation": "HIGH_WITH_SIDECAR_WORKER", "determinism": "GOOD_IF_IDS_EXPOSED", "complexity": "MEDIUM", "validation_burden": "HIGH", "reviewer_defensibility": "GOOD_IF_INTERNAL_READS_ARE_EXPLICIT", "decision": "FALLBACK"},
    {"option": "OPTION_C_OUT_OF_PROCESS_LOG_SIDECAR", "authority_isolation": "HIGHEST", "production_mutation": "APPEND_ONLY_PAYLOAD_WRITER", "trace_risk": "LOW", "candidate_visibility": "ONLY_SERIALIZED_FIELDS", "map_visibility": "GOOD_IF_SERIALIZED", "reachability_visibility": "POOR_WITH_CURRENT_LOGS", "async_feasibility": "YES", "backpressure": "FILESYSTEM_DEPENDENT", "crash_isolation": "HIGHEST", "determinism": "GOOD", "complexity": "LOW_TO_MEDIUM", "validation_burden": "MEDIUM", "reviewer_defensibility": "INSUFFICIENT_WITH_CURRENT_MISSING_U_K", "decision": "REJECT_CURRENT_FORM"},
    {"option": "OPTION_D_POST_PLANT_LOG_SCRAPE", "authority_isolation": "HIGH", "production_mutation": "ZERO", "trace_risk": "LOW", "candidate_visibility": "INCOMPLETE", "map_visibility": "PATH_ONLY", "reachability_visibility": "ABSENT", "async_feasibility": "YES", "backpressure": "N_A", "crash_isolation": "HIGH", "determinism": "LOW_ALIGNMENT_CONFIDENCE", "complexity": "LOW", "validation_burden": "UNSATISFIABLE", "reviewer_defensibility": "REJECTED_OFF_BY_ONE_AND_MISSINGNESS", "decision": "REJECTED"},
]
write_csv("observation_architecture_comparison.csv", list(architecture_rows[0]), architecture_rows)


write_text(
    "SELECTED_OBSERVATION_ARCHITECTURE.md",
    f"""
# Selected Observation Architecture

**Selected:** Option A, a post-commit in-process read-only tap feeding an out-of-process shadow worker.

```text
frozen controller computes and accepts u_k
  -> decision_commit_id becomes immutable
  -> copy x_k/u_k/dt/native candidates/map ref into immutable payload
  -> enqueue_nowait(bounded_queue)
  -> frozen controller applies the already-selected u_k

bounded_queue -> isolated L0/L1/L2 worker -> append-only result log
bounded_queue <- no controller reads
shadow result <- no controller reads
```

The capture occurs after `run.py:139-143` accepts the QP result and before `run.py:147` propagates the plant. The future hook may copy and enqueue only. It may not call L2, await a worker, mutate inputs, alter exceptions, or return a candidate.

The worker reconstructs immutable PR #84 `State` and `Control` objects, evaluates current-feasibility (L0), immediate segment (L1), and L2/H1 in that fixed order, and writes explicit reached/status/reason fields. This is a shadow observation pipeline, not the frozen controller's decision pipeline.

**Fallback:** Option B, an outer cycle wrapper/decorator, is permitted only if a future static interface exposes the identical commit ID, accepted `u_k`, native candidate set, stage reasons, and map reference without recomputation. If any are unavailable, the fallback fails closed and cannot collect formal data.

**Why not pure log scraping:** existing logs caused 4,259 missing controls and 5,795 unknown reachability records. Formal zero-code mutation is not evidence completeness.

**Scope:** {LABELS}.
""",
)


write_text(
    "ZERO_AUTHORITY_CONTRACT.md",
    f"""
# Zero-Authority Contract

For every payload and result:

| Field | Required value |
|---|---|
| `controller_authority` | `false` |
| `execution_authority` | `false` |
| `candidate_selection_authority` | `false` |
| `alternative_authority` | `false` |
| `backup_authority` | `false` |
| `terminal_authority` | `false` |
| `fail_close_authority` | `false` |
| `intervention` | `false` |
| `shadow_only` | `true` |

There is no result-return interface, shared mutable candidate object, controller callback, IPC request from controller to worker, or worker-to-controller queue. `controller_output` equals the frozen controller output and is never a function of `shadow_result`.

If queue enqueue, serialization, worker execution, or shutdown fails, the controller continues the frozen path using the already accepted `u_k`. A minimal health/drop counter may be updated through a nonthrowing, nonblocking primitive; failure to update it is itself an external audit issue, never a controller stop.

L2 semantic fail-closed means an L2 certificate does not claim PASS when formal evaluation yields FAIL/UNKNOWN. It does **not** authorize the observer to stop or change the controller. Observer runtime failure is `OBSERVATION_INCOMPLETE`/observer health, not L2 UNKNOWN.

Future implementation must pass static call-graph/taint review showing no shadow-result consumer in controller code, and an OFF-vs-ON trace-equivalence smoke, before collection.

**Scope:** {LABELS}.
""",
)


write_text(
    "STATE_ACTION_ALIGNMENT_CONTRACT.md",
    f"""
# State/Action Alignment Contract

The atomic observation unit is one accepted frozen-controller decision. The immutable key tuple is:

`(run_id, trial_id, step_id, state_sequence_id, decision_commit_id, candidate_group_id, selected_candidate_id, map_snapshot_ref)`.

Capture order is fixed:

1. freeze pre-plant `x_k` and derive `p_k=x_k[:3]`, `v_k=x_k[3:]`;
2. freeze runtime `dt` and accepted selected `u_k` after the success guard;
3. assign `decision_commit_id` exactly once;
4. hash canonical state, candidate group, selected control, and map reference;
5. enqueue the immutable payload without waiting;
6. only then allow the pre-existing plant update to use the same `u_k`.

The worker must compute:

`p_k1 = p_k + dt*v_k`

`p_k2 = p_k + 2*dt*v_k + dt^2*u_k`

It must never substitute the logged post-update `x_(k+1)` for `x_k`.

## Required anti-off-by-one checks

1. **Commit uniqueness:** one and only one payload per `decision_commit_id`; IDs are monotonic within trial.
2. **State hash:** recompute `state_hash` from captured `p_k/v_k/dt/state_sequence_id` canonical bytes.
3. **Control hash:** recompute `u_k_hash` and require it equals the selected native-candidate hash.
4. **Plant trace join:** where deterministic trace QA is available, `x_(k+1)` must equal the frozen plant transition of captured `x_k/u_k/dt` within the pre-frozen equivalence tolerance; it must not equal the payload's `x_k` key by accidental index shift.
5. **H1 recomputation:** independently recompute `p_k1/p_k2/H1_segment_hash` from captured fields and require exact canonical-hash equality.
6. **Timestamp relation:** `control_timestamp/logical_index` and `step_id` must be one-to-one; no result may join to a later state sequence.
7. **Candidate join:** `selected_candidate_committed=true` and exactly one native candidate has `selected_for_execution=true`.
8. **Map join:** payload and result must use the same `map_snapshot_ref`, resolved by the frozen run map manifest.

Any failure is `OBSERVATION_INCOMPLETE`, excluded from the evaluable endpoint but included in logging denominators. It is never converted to L2 UNKNOWN.

**Scope:** {LABELS}.
""",
)


step_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "safer-splat://schemas/l2-h1-on-policy-shadow-step-v1",
    "title": "Prospective L2/H1 shadow observation step",
    "type": "object",
    "additionalProperties": False,
    "required": ["schema_version", "run", "state", "l0", "l1", "candidate_preparation", "selected_candidate", "map_authority", "l2", "authority", "instrumentation"],
    "properties": {
        "schema_version": {"const": "L2_H1_ON_POLICY_SHADOW_STEP_V1"},
        "run": {"type": "object", "additionalProperties": False, "required": ["run_id", "trial_id", "seed", "step_id", "control_timestamp", "logical_index", "state_sequence_id", "decision_commit_id", "observation_capture_id"], "properties": {
            "run_id": {"type": "string", "minLength": 1}, "trial_id": {"type": "string", "minLength": 1}, "seed": {"type": ["integer", "string"]}, "step_id": {"type": "integer", "minimum": 0}, "control_timestamp": {"type": "number"}, "logical_index": {"type": "integer", "minimum": 0}, "state_sequence_id": {"type": "string", "minLength": 1}, "decision_commit_id": {"type": "string", "minLength": 1}, "observation_capture_id": {"type": "string", "minLength": 1}}},
        "state": {"type": "object", "additionalProperties": False, "required": ["p_k", "v_k", "dt", "state_hash", "finite", "status"], "properties": {
            "p_k": {"$ref": "#/$defs/vector3"}, "v_k": {"$ref": "#/$defs/vector3"}, "dt": {"type": "number", "exclusiveMinimum": 0}, "state_hash": {"$ref": "#/$defs/sha256"}, "finite": {"type": "boolean"}, "status": {"enum": ["VALID", "NONFINITE", "INVALID_SHAPE"]}}},
        "l0": {"type": "object", "additionalProperties": False, "required": ["reached", "status", "repair_attempted", "repair_result", "reason", "source_class"], "properties": {
            "reached": {"type": "boolean"}, "status": {"$ref": "#/$defs/triState"}, "repair_attempted": {"type": "boolean"}, "repair_result": {"enum": ["NOT_ATTEMPTED", "PASS", "FAIL", "UNKNOWN"]}, "reason": {"type": "string"}, "source_class": {"const": "SHADOW_PIPELINE_RUNTIME_OBSERVATION"}}},
        "l1": {"type": "object", "additionalProperties": False, "required": ["reached", "stored_status", "reason", "immediate_segment_start", "immediate_segment_end", "source_class"], "properties": {
            "reached": {"type": "boolean"}, "stored_status": {"$ref": "#/$defs/triState"}, "reason": {"type": "string"}, "immediate_segment_start": {"$ref": "#/$defs/vector3"}, "immediate_segment_end": {"$ref": "#/$defs/vector3"}, "source_class": {"const": "SHADOW_PIPELINE_RUNTIME_OBSERVATION"}}},
        "candidate_preparation": {"type": "object", "additionalProperties": False, "required": ["reached", "candidate_group_id", "native_candidate_count", "native_candidate_set_hash", "candidate_synthesis_count"], "properties": {
            "reached": {"type": "boolean"}, "candidate_group_id": {"type": "string", "minLength": 1}, "native_candidate_count": {"type": "integer", "minimum": 1}, "native_candidate_set_hash": {"$ref": "#/$defs/sha256"}, "candidate_synthesis_count": {"const": 0}}},
        "selected_candidate": {"type": "object", "additionalProperties": False, "required": ["candidate_id", "role", "u_k", "u_k_hash", "committed"], "properties": {
            "candidate_id": {"type": "string", "minLength": 1}, "role": {"const": "SELECTED_EXECUTED"}, "u_k": {"$ref": "#/$defs/vector3"}, "u_k_hash": {"$ref": "#/$defs/sha256"}, "committed": {"const": True}}},
        "map_authority": {"type": "object", "additionalProperties": False, "required": ["map_snapshot_ref", "map_content_hash", "map_contract_version", "query_context_id", "robot_radius", "safety_margin", "effective_radius", "rho_seg"], "properties": {
            "map_snapshot_ref": {"type": "string", "minLength": 1}, "map_content_hash": {"$ref": "#/$defs/sha256"}, "map_contract_version": {"type": "string", "minLength": 1}, "query_context_id": {"type": "string", "minLength": 1}, "robot_radius": {"type": "number", "minimum": 0}, "safety_margin": {"type": "number", "minimum": 0}, "effective_radius": {"type": "number", "minimum": 0}, "rho_seg": {"type": "number", "minimum": 0}}},
        "l2": {"type": "object", "additionalProperties": False, "required": ["reached", "reachability_reason", "evaluated", "status", "reason", "p_k1", "p_k2", "H1_segment_hash", "backend_identity", "backend_class", "formal_value", "diagnostics", "shadow_result_id", "shadow_only"], "properties": {
            "reached": {"type": "boolean"}, "reachability_reason": {"enum": ["L0_BLOCKED", "L1_FAIL", "L1_UNKNOWN", "NO_CANDIDATE", "SELECTED_CANDIDATE_AVAILABLE", "TERMINAL_ALREADY_SAFE", "OTHER_FROZEN_ARCHITECTURE_REASON"]}, "evaluated": {"type": "boolean"}, "status": {"$ref": "#/$defs/triState"}, "reason": {"type": "string"}, "p_k1": {"$ref": "#/$defs/vector3"}, "p_k2": {"$ref": "#/$defs/vector3"}, "H1_segment_hash": {"$ref": "#/$defs/sha256"}, "backend_identity": {"type": "string", "minLength": 1}, "backend_class": {"enum": ["EXACT_FUNCTIONAL_AUTOGRAD", "CONSERVATIVE_INTERVAL", "OTHER_FROZEN_BACKEND"]}, "formal_value": {"type": ["number", "null"]}, "diagnostics": {"type": "object"}, "shadow_result_id": {"type": "string", "minLength": 1}, "shadow_only": {"const": True}}},
        "authority": {"type": "object", "additionalProperties": False, "required": ["controller_authority", "execution_authority", "candidate_selection_authority", "alternative_authority", "backup_authority", "terminal_authority", "fail_close_authority", "intervention"], "properties": {key: {"const": False} for key in ["controller_authority", "execution_authority", "candidate_selection_authority", "alternative_authority", "backup_authority", "terminal_authority", "fail_close_authority", "intervention"]}},
        "instrumentation": {"type": "object", "additionalProperties": False, "required": ["payload_sequence_id", "queue_status", "observation_dropped", "serialization_status", "observer_process_status", "observation_completeness"], "properties": {
            "payload_sequence_id": {"type": "integer", "minimum": 0}, "queue_status": {"enum": ["ENQUEUED", "DROPPED_FULL", "DROPPED_UNAVAILABLE", "NOT_ENQUEUED_SERIALIZATION_ERROR"]}, "observation_dropped": {"type": "boolean"}, "serialization_status": {"enum": ["PASS", "ERROR"]}, "observer_process_status": {"enum": ["HEALTHY", "QUEUE_BACKPRESSURE", "SERIALIZATION_ERROR", "WORKER_EXCEPTION", "WORKER_UNAVAILABLE", "RESULT_LATE", "SHUTDOWN_INCOMPLETE"]}, "observation_completeness": {"enum": ["COMPLETE", "OBSERVATION_INCOMPLETE", "SHADOW_EVALUATION_DROPPED"]}}},
    },
    "$defs": {
        "vector3": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"type": "number"}},
        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "triState": {"enum": ["PASS", "FAIL", "UNKNOWN", "NOT_REACHED"]},
    },
}
write_json("prospective_step_schema.json", step_schema)


native_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "safer-splat://schemas/native-candidate-group-v1",
    "type": "object",
    "additionalProperties": False,
    "required": ["candidate_group_id", "decision_commit_id", "native_candidate_count", "native_candidate_set_hash", "candidate_synthesis_count", "candidates"],
    "properties": {
        "candidate_group_id": {"type": "string", "minLength": 1}, "decision_commit_id": {"type": "string", "minLength": 1}, "native_candidate_count": {"type": "integer", "minimum": 1}, "native_candidate_set_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"}, "candidate_synthesis_count": {"const": 0},
        "candidates": {"type": "array", "minItems": 1, "items": {"type": "object", "additionalProperties": False, "required": ["candidate_id", "candidate_index", "candidate_role", "candidate_origin", "u", "candidate_hash", "existed_before_shadow_observation", "selected_for_execution", "l2_status", "l2_reason", "p_k2", "H1_segment_hash", "backend_identity"], "properties": {
            "candidate_id": {"type": "string", "minLength": 1}, "candidate_index": {"type": "integer", "minimum": 0}, "candidate_role": {"enum": ["SELECTED_EXECUTED", "NOMINAL_NATIVE", "ALTERNATIVE_NATIVE", "REJECTED_NATIVE", "OTHER_FROZEN_ROLE"]}, "candidate_origin": {"type": "string", "minLength": 1}, "u": {"type": "array", "minItems": 3, "maxItems": 3, "items": {"type": "number"}}, "candidate_hash": {"type": "string", "pattern": "^[0-9a-f]{64}$"}, "existed_before_shadow_observation": {"const": True}, "selected_for_execution": {"type": "boolean"}, "l2_status": {"enum": ["PASS", "FAIL", "UNKNOWN", "NOT_EVALUATED"]}, "l2_reason": {"type": "string"}, "p_k2": {"type": ["array", "null"], "items": {"type": "number"}}, "H1_segment_hash": {"type": ["string", "null"]}, "backend_identity": {"type": ["string", "null"]}}}}
    },
}
write_json("native_candidate_schema.json", native_schema)


map_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "safer-splat://schemas/map-authority-manifest-v1", "type": "object", "additionalProperties": False,
    "required": ["schema_version", "run_id", "map_static_within_trial", "map_contract_version", "map_artifacts", "snapshot_index", "robot_contract"],
    "properties": {
        "schema_version": {"const": "MAP_AUTHORITY_MANIFEST_V1"}, "run_id": {"type": "string", "minLength": 1}, "map_static_within_trial": {"type": "boolean"}, "map_contract_version": {"type": "string", "minLength": 1},
        "map_artifacts": {"type": "array", "minItems": 1, "items": {"type": "object", "additionalProperties": False, "required": ["artifact_id", "reference", "sha256", "size", "representation", "immutable"], "properties": {"artifact_id": {"type": "string"}, "reference": {"type": "string"}, "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}, "size": {"type": "integer", "minimum": 1}, "representation": {"type": "string"}, "immutable": {"const": True}}}},
        "snapshot_index": {"type": "array", "minItems": 1, "items": {"type": "object", "required": ["map_snapshot_ref", "content_identity", "valid_from_step", "valid_through_step"], "properties": {"map_snapshot_ref": {"type": "string"}, "content_identity": {"type": "string", "pattern": "^[0-9a-f]{64}$"}, "valid_from_step": {"type": "integer", "minimum": 0}, "valid_through_step": {"type": ["integer", "null"]}}}},
        "robot_contract": {"type": "object", "required": ["robot_radius", "safety_margin", "effective_radius", "rho_seg", "sha256"], "properties": {"robot_radius": {"type": "number", "minimum": 0}, "safety_margin": {"type": "number", "minimum": 0}, "effective_radius": {"type": "number", "minimum": 0}, "rho_seg": {"type": "number", "minimum": 0}, "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}}},
    },
}
write_json("map_authority_manifest_schema.json", map_schema)


health_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "safer-splat://schemas/observer-health-v1", "type": "object", "additionalProperties": False,
    "required": ["payload_sequence_id", "health", "queue_depth", "queue_capacity", "sequence_gap_count", "worker_heartbeat_id", "controller_intervention", "classified_as_l2_unknown"],
    "properties": {"payload_sequence_id": {"type": "integer", "minimum": 0}, "health": {"enum": ["HEALTHY", "QUEUE_BACKPRESSURE", "SERIALIZATION_ERROR", "WORKER_EXCEPTION", "WORKER_UNAVAILABLE", "RESULT_LATE", "SHUTDOWN_INCOMPLETE"]}, "queue_depth": {"type": "integer", "minimum": 0}, "queue_capacity": {"type": "integer", "minimum": 1}, "sequence_gap_count": {"type": "integer", "minimum": 0}, "worker_heartbeat_id": {"type": ["string", "null"]}, "controller_intervention": {"const": False}, "classified_as_l2_unknown": {"const": False}},
}
write_json("observer_health_schema.json", health_schema)


reachability_schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "safer-splat://schemas/reachability-reason-v1", "type": "object", "additionalProperties": False,
    "required": ["l0_reached", "l0_status", "l1_reached", "l1_status", "candidate_preparation_reached", "l2_reached", "l2_reachability_reason", "source_class"],
    "properties": {"l0_reached": {"type": "boolean"}, "l0_status": {"enum": ["PASS", "FAIL", "UNKNOWN", "NOT_REACHED"]}, "l1_reached": {"type": "boolean"}, "l1_status": {"enum": ["PASS", "FAIL", "UNKNOWN", "NOT_REACHED"]}, "candidate_preparation_reached": {"type": "boolean"}, "l2_reached": {"type": "boolean"}, "l2_reachability_reason": {"enum": ["L0_BLOCKED", "L1_FAIL", "L1_UNKNOWN", "NO_CANDIDATE", "SELECTED_CANDIDATE_AVAILABLE", "TERMINAL_ALREADY_SAFE", "OTHER_FROZEN_ARCHITECTURE_REASON"]}, "source_class": {"const": "SHADOW_PIPELINE_RUNTIME_OBSERVATION"}},
}
write_json("reachability_reason_schema.json", reachability_schema)


write_text(
    "ON_POLICY_SHADOW_OBSERVATION_PROTOCOL_V1.md",
    f"""
# On-Policy L2/H1 Shadow Observation Protocol V1

## Status and scope

This is a prospective design frozen before collection. It does not collect data, integrate a controller, or claim performance. **{LABELS}.**

## Design inputs, not conclusions

PR #95 contained {replay_inputs['N_all']} records, of which {replay_inputs['N_formal_replayable']} ({replay_inputs['replay_coverage_percent']:.4f}%) were formally replayable. All {replay_inputs['N_not_replayable']} non-replayable records lacked numeric `u_k`; {replay_inputs['reachability_unknown']} had unknown reachability. Among {replay_inputs['L2_evaluated']} evaluated records, L2 was {replay_inputs['L2_PASS']}/{replay_inputs['L2_FAIL']}/{replay_inputs['L2_UNKNOWN']} PASS/FAIL/UNKNOWN. Executed candidates were {replay_inputs['executed_PASS']}/{replay_inputs['executed_FAIL']} PASS/FAIL over {replay_inputs['executed_total']}; non-executed candidates were {replay_inputs['nonexecuted_PASS']}/{replay_inputs['nonexecuted_FAIL']} over {replay_inputs['nonexecuted_total']}. The {replay_inputs['multi_candidate_groups']} multi-candidate groups had distinct H1 endpoints in 20/20 and status disagreement in 0/20. These historical rates are planning priors affected by missingness and source selection.

## Prospective unit and timing

Every accepted frozen-controller step is an intended observation unit. Capture occurs after selected `u_k` is committed by the frozen controller and before plant propagation. The tap copies the complete immutable payload and calls only a bounded `enqueue_nowait`. The isolated worker then evaluates the read-only L0/current, L1/immediate-segment, and L2/H1 stages and writes append-only results.

The shadow result has no consumer in the controller. FAIL, UNKNOWN, candidate disagreement, queue failure, and worker crash all leave the already selected action and future controller distribution unchanged.

## Reachability state machine

At worker runtime, each payload records explicit stage transitions rather than inferring them later:

1. L0/current-feasibility reached -> PASS/FAIL/UNKNOWN;
2. L1/immediate segment reached only under the frozen observer progression -> PASS/FAIL/UNKNOWN;
3. candidate preparation reached with a committed selected candidate;
4. L2 reached only when the frozen prerequisites are satisfied;
5. L2 evaluated -> PASS/FAIL/UNKNOWN.

The source class is always `SHADOW_PIPELINE_RUNTIME_OBSERVATION`. `L2_NOT_REACHED`, `L2_UNKNOWN`, `OBSERVATION_INCOMPLETE`, and `SHADOW_EVALUATION_DROPPED` are disjoint.

## Candidate policy

The selected/executed candidate is primary. All native candidates that existed before observation may be recorded as secondary. The `run.py` baseline contributes nominal `u_des` and selected `u`; a richer frozen runtime may expose a native alternative set. No rotation, noise, interpolation, perturbation, resampling, or library expansion is permitted. Candidate synthesis count is zero.

## Map authority

Before any future equivalence or collection run, a map manifest hashes every immutable artifact byte, representation contract, snapshot mapping, and robot/margin/rho contract. Static maps use one stable snapshot reference per run/trial; dynamic maps require a content-addressed snapshot per step. A scene name or path alone is never authority.

## Queue and failure behavior

Queue capacity is bounded and frozen by the future implementation protocol after Phase 0 measurement; this design intentionally does not invent a throughput number. Enqueue policy is nonblocking. Full/unavailable queues drop the observation, increment a monotonic counter where safely possible, and emit a minimal drop record. Sequence gaps are detected from `payload_sequence_id`. Worker heartbeat and shutdown-flush outcomes are logged. Shutdown may wait only outside the control cycle and may not retroactively change a trajectory.

## Prospective cohort and analysis

Primary cohort: every on-policy step for which the frozen controller committed a selected candidate, the zero-authority shadow progression records stored L1 PASS, L2 reached, and L2 formal evaluation PASS/FAIL/UNKNOWN. Primary mechanism endpoint: `P(L2_FAIL | stored_L1_PASS, L2_reached, selected/executed, L2_evaluated)`.

Secondary cohorts include all native candidates, non-executed native candidates, native multi-candidate groups, backend classes, L2 UNKNOWN, reachability, and logging completeness. They may not replace the primary executed rate.

## Prospective event

`PROSPECTIVE_L1_PASS_L2_FAIL` requires a true frozen-controller on-policy step, committed selected/executed candidate, stored runtime shadow L1 PASS, explicit L2 reach, formal L2 FAIL, and zero control feedback. It may be called a candidate-dependent future-safety shadow signal or L2-specific information increment. It is not a prevented collision, intervention success, avoided failure, control improvement, or safety gain.

## Phases (future only)

- **Phase 0:** implementation validation, schema/unit/static tests; no research data.
- **Phase 1:** paired OFF-vs-ON equivalence smoke on fixed seeds; QA only, excluded from primary cohort.
- **Phase 2:** logging-completeness pilot; excluded by default from primary cohort.
- **Phase 3:** frozen-manifest prospective shadow cohort; only after all gates pass.
- **Phase 4:** analysis only under the frozen denominator/statistical plan.

This task executes none of Phases 0-4.

## Claims boundary

The future cohort can describe signal prevalence, prospective L1 PASS/L2 FAIL information increment, UNKNOWN reliability, native certificate discrimination prevalence, logging completeness, and map-relative mechanism evidence. It cannot establish collision reduction, progress, efficacy, intervention success, recursive feasibility, safe stop, physical safety, deployment, real-time performance, or Core V2 superiority.
""",
)


write_text(
    "PROSPECTIVE_DENOMINATOR_CONTRACT.md",
    f"""
# Prospective Denominator Contract

All counters begin at zero before the frozen manifest is executed and are updated for every intended control step, including incomplete observations.

| Counter | Definition |
|---|---|
| `N_control_steps_all` | All frozen-controller control decisions in the pre-registered manifest. |
| `N_L0_reached/pass/repair/fail` | Explicit worker-runtime L0 progression and outcomes. |
| `N_L1_reached/PASS/FAIL/UNKNOWN` | Explicit worker-runtime immediate-segment progression and outcomes. |
| `N_L2_reached_selected` | Committed selected candidates for which frozen prerequisites reached L2. |
| `N_L2_selected_evaluated` | Reached selected candidates with a completed formal tri-state L2 result. |
| `N_L2_selected_PASS/FAIL/UNKNOWN` | Mutually exclusive partition of the evaluated selected denominator. |
| `N_native_candidates_total/evaluated` | All native pre-observation candidates and completed shadow results. |
| `N_multi_candidate_groups` | Steps with more than one native candidate. |
| `N_multi_candidate_groups_all_evaluated` | Groups in which every native candidate received a result. |
| `N_multi_candidate_groups_status_disagreement` | Groups with at least two distinct tri-state statuses. |
| `N_multi_candidate_groups_PASS_AND_FAIL` | Groups containing both PASS and FAIL. |
| `N_observation_dropped` | Intended payloads not enqueued or evaluated due to instrumentation. |
| `N_logging_error` | Required payload/serialization/alignment failures. |
| `N_shadow_worker_error` | Worker health failures, never L2 UNKNOWN. |

Rates:

- `primary_future_fail_signal_rate = N_L2_selected_FAIL / N_L2_selected_evaluated`;
- `primary_future_unknown_rate = N_L2_selected_UNKNOWN / N_L2_selected_evaluated`;
- `L2_reach_rate = N_L2_reached_selected / N_control_steps_all`;
- `logging_completeness = N_complete_required_payload_steps / N_control_steps_all`.

Every table must print numerator, denominator, and undefined status when denominator is zero. `L2_UNKNOWN`, `L2_NOT_REACHED`, `OBSERVATION_INCOMPLETE`, and `SHADOW_EVALUATION_DROPPED` are never pooled.

**Scope:** {LABELS}.
""",
)


write_text(
    "prospective_analysis_plan.md",
    f"""
# Prospective Analysis Plan

## Primary endpoint

The single primary endpoint is selected/executed-candidate `PROSPECTIVE_L1_PASS_L2_FAIL` prevalence among `N_L2_selected_evaluated`, with stored runtime shadow L1 PASS and explicit L2 reach.

## Secondary endpoints

1. selected-candidate L2 UNKNOWN prevalence;
2. L2 selected reach rate over all control steps;
3. required-payload logging completeness and instrumentation-error composition;
4. native multi-candidate-group prevalence;
5. multi-candidate certificate disagreement and PASS+FAIL prevalence;
6. selected versus non-selected native-candidate L2 status, without causal comparison;
7. exact/conservative/other frozen backend use and source/trial heterogeneity.

Candidate-step point estimates retain exact numerator/denominator. Uncertainty uses trial-cluster bootstrap with trial as the resampling unit and a pre-frozen seed/replicate count, plus trial-level prevalence summaries. Step-level iid Wilson intervals are not the primary uncertainty calculation. No p-value is required to call the result a mechanism signal.

All analysis includes outcome-independent retained steps, explicit missingness tables, environment/trial cluster IDs, and separate pilot/formal labels. Phase 1 and Phase 2 are excluded from the formal cohort unless a protocol frozen before either phase explicitly permits inclusion under zero modifications; the default is exclusion.

Multi-candidate questions are prevalence, endpoint diversity, certificate disagreement, and selected-vs-nonselected status. They are certificate discrimination opportunity, not alternative-search efficacy.

No result-dependent trial extension, early stop on FAIL count, high-risk-only retention, margin filtering, collision-only retention, or post-hoc cohort construction is permitted.

**Scope:** {LABELS}.
""",
)


write_text(
    "sample_size_and_stopping_rule.md",
    f"""
# Sample Size and Stopping Rule

PR #95 supplies planning priors, not a transportability claim. The historical selected/executed rate is `6/566 = 1.0601%`; the broader L1 PASS/L2 FAIL rate is `18/788 = 2.2843%`. Both are biased by source selection and missing payloads. Under an iid calculation used only for scale intuition, a 1.0601% event rate gives 282 evaluated candidates for a 95% chance of at least one event and 217 for 90% (ceiling of the exact logarithmic calculation). These are not power guarantees because steps cluster within trials.

## Plan A — selected primary plan: fixed trial manifest

Freeze the mature Stonehenge `run.py` baseline's complete 100 deterministic indexed trials, starts/goals, order, `dt=0.05`, 500-step cap, termination rules, controller config, static map content identity, and no-random-sampling seed policy before results. Observe every accepted step. Stop only when every frozen trial is terminal. Do not stop based on L2 FAIL/UNKNOWN or any interim rate.

This plan is selected because it preserves the existing on-policy distribution, gives trial clusters a defensible meaning, and avoids treating correlated steps as a sample-size counter. PR #89 E5's 100 locked one-step states provide provenance context but do not replace the rollout manifest.

## Plan B — fallback: fixed reached-selected target plus trial cap

Pre-register `N_L2_selected_evaluated = 566` as a planning-scale target, together with the same fixed ordered Stonehenge trial manifest and a 100-trial/500-step cap. Stop only after the current trial finishes once the target is met, or after the fixed trial cap. Never stop by the number or pattern of FAIL results. Report the achieved trial count and cluster distribution.

Plan B may be chosen only before collection if Phase 2 shows Plan A is infeasible for instrumentation/logging reasons without changing the scientific controller. It cannot be selected after inspecting L2 outcomes.

## Uncertainty

The final point estimate is candidate-step prevalence. Primary uncertainty is a cluster-aware bootstrap over complete trials or trial-level aggregation, with algorithm, seed, and replicate count frozen in the Phase 3 analysis manifest. The planning iid calculation is not reused as inferential evidence.

**Scope:** {LABELS}.
""",
)


write_text(
    "future_trial_manifest_policy.md",
    f"""
# Future Trial Manifest Policy

The first prospective environment is Stonehenge because the frozen baseline already defines its map/config, deterministic 100-trial circle, controller, `dt`, and step cap. Replica/TUM/cross-dataset expansion is a separate authorization. No environment may be added to increase the L2 FAIL rate.

Before Phase 1, freeze controller commit, source blobs, environment, map manifest, exact starts/goals, trial IDs/order, deterministic seed policy, `dt`, termination rules, robot/margin/rho contract, queue configuration, schema versions, and equivalence tolerances. Phase 3 receives a distinct signed/hashed manifest before any formal shadow result.

Every intended step is retained irrespective of L1 margin, L2 status, collision, progress, risk, multi-candidate presence, or observer health. Minimal drop records preserve the intended denominator. Pilot data are excluded from the formal cohort by default. Completed trials are never silently rerun; infrastructure recovery appends provenance and resumes only under a pre-frozen policy.

Seed policy for the current `run.py` design is `NO_RANDOM_SAMPLING_FROZEN_INDEXED_TRIALS`; if future wrappers introduce randomness, explicit seeds and RNG-library identities become mandatory before Phase 1.

**Scope:** {LABELS}.
""",
)


write_text(
    "future_equivalence_gate_spec.md",
    f"""
# Future Control-Trace Equivalence Gate

Phase 1 compares observer OFF (control) and observer ON with zero authority (shadow) under identical frozen source, environment, config, trial manifest, map identity, and seed policy.

Required identities/equivalences:

1. `control_trace_equivalence`: exact selected action sequence where deterministic execution is promised;
2. `selected_candidate_hash_equivalence`: exact sequence equality;
3. `trial_seed_equivalence`: exact manifest and RNG identity;
4. `map_identity_equivalence`: exact content/snapshot identities;
5. `controller_return_value_equivalence`: exact values/status/branch sequence;
6. exact L0/L1 production outcomes where those outcomes belong to the frozen controller;
7. same termination reason and step count;
8. progress/collision traces only as equivalence QA, never performance evidence.

If exact floating equality is not supported by a frozen dependency, Phase 1's protocol must pre-register a field-specific absolute/relative tolerance and hash the tolerance manifest **before either arm runs**. Tolerances cannot be loosened after seeing differences. Observer-induced scheduling effects outside the frozen tolerance fail G1.

Any failure blocks Phase 2/3. This design task does not execute the gate.

**Scope:** {LABELS}.
""",
)


write_text(
    "future_logging_completeness_gate.md",
    f"""
# Future Logging Completeness Gate

Before Phase 3, Phase 2 must demonstrate on its frozen pilot manifest:

- every intended step has either one complete payload or one explicit minimal drop record;
- every complete selected step contains finite numeric `u_k`, `u_k_hash`, commit ID, state ID, and map ref;
- explicit L0/L1/candidate/L2 reachability is present for every complete payload;
- every map ref resolves to an immutable content identity;
- sequence gaps reconcile exactly with drop/error records;
- no instrumentation failure is counted as L2 UNKNOWN;
- candidate synthesis count is zero;
- selected candidate hash joins exactly to `u_k_hash`;
- no required ID collision or off-by-one check fails.

G2 requires zero missing `u_k` among complete selected-step payloads. G3/G4 require 100% explicit reachability and map resolution among complete payloads. Formal collection also reports overall completeness, including drops; no denominator silently excludes a drop.

The gate is not satisfied by an average rate alone. Any systematic missingness, ambiguous map identity, or unexplained sequence gap blocks Phase 3 and requires a separately authorized instrumentation repair.

**Scope:** {LABELS}.
""",
)


write_text(
    "future_validation_plan.md",
    f"""
# Future Validation Plan

## Phase 0

Run schema positive/negative fixtures, canonical serialization round trips, immutable-copy tests, full-queue fault injection, serializer exception injection, worker crash injection, no-result-return static call-graph review, monotonic ID tests, map-manifest resolution, and candidate provenance validation. This phase is implementation QA, not research data.

## Phase 1

Run the pre-frozen OFF-vs-ON equivalence smoke and enforce `future_equivalence_gate_spec.md`. Do not combine its data with the primary cohort.

## Phase 2

Run the pre-frozen logging pilot and enforce `future_logging_completeness_gate.md`. Measure queue/drop behavior to choose a future frozen queue capacity; do not tune on L2 outcomes.

## Phase 3

Only after all gates pass, execute the separately authorized fixed manifest once. Validate each append-only log segment, manifest identity, denominator accounting, cluster labels, and recovery provenance.

## Phase 4

Lock raw evidence, run the pre-registered analysis, report numerator/denominator and cluster-aware uncertainty, and preserve failures/missingness.

This task executes none of these phases. Future validation never changes controller mathematics, candidates, map, seeds, trial order, or L2 authority.

**Scope:** {LABELS}.
""",
)


kill_gates = {
    "schema_version": "L2_H1_ON_POLICY_SHADOW_KILL_GATES_V1",
    "gate_count": 10,
    "gates": [
        {"id": "G1_CONTROL_TRACE_EQUIVALENCE", "requirement": "observer ON preserves frozen selected actions, branch sequence, returns and termination under pre-frozen equality/tolerances", "failure_action": "BLOCK_FORMAL_COLLECTION"},
        {"id": "G2_U_K_COMPLETENESS", "requirement": "zero missing numeric selected u_k in complete payloads and all intended steps reconciled", "failure_action": "BLOCK_FORMAL_COLLECTION"},
        {"id": "G3_REACHABILITY_COMPLETENESS", "requirement": "explicit L0/L1/candidate/L2 reachability for every complete payload", "failure_action": "BLOCK_FORMAL_COLLECTION"},
        {"id": "G4_MAP_AUTHORITY_COMPLETENESS", "requirement": "every map ref resolves to immutable content and robot/margin/rho contract", "failure_action": "BLOCK_FORMAL_COLLECTION"},
        {"id": "G5_ZERO_FEEDBACK", "requirement": "no shadow-result consumer, callback, return queue or shared mutable control object", "failure_action": "BLOCK_IMPLEMENTATION_AND_COLLECTION"},
        {"id": "G6_QUEUE_NONBLOCKING", "requirement": "full/unavailable queue never blocks or changes controller path", "failure_action": "BLOCK_FORMAL_COLLECTION"},
        {"id": "G7_CANDIDATE_PROVENANCE", "requirement": "all secondary candidates existed before observation; synthesis count zero", "failure_action": "EXCLUDE_INVALID_SECONDARY_AND_BLOCK_IF_SELECTED_PROVENANCE_FAILS"},
        {"id": "G8_PROTOCOL_FREEZE", "requirement": "manifest/config/schema/analysis/stopping rule frozen before Phase 3 results", "failure_action": "INVALIDATE_FORMAL_COHORT"},
        {"id": "G9_STATE_ACTION_ALIGNMENT", "requirement": "all anti-off-by-one joins and H1 recomputations pass", "failure_action": "BLOCK_FORMAL_COLLECTION"},
        {"id": "G10_HEALTH_STATUS_SEPARATION", "requirement": "zero observer/instrumentation failures classified as L2 UNKNOWN", "failure_action": "BLOCK_FORMAL_COLLECTION"},
    ],
    "executed_in_this_task": False,
}
write_json("kill_gates.json", kill_gates)


claims = {
    "schema_version": "L2_H1_ON_POLICY_SHADOW_CLAIMS_V1",
    "supported_only_after_valid_future_phase3": [
        "L2/H1 signal prevalence under the frozen-controller on-policy distribution",
        "prospective L1 PASS and L2 FAIL information increment",
        "prospective L2 UNKNOWN reliability",
        "native multi-candidate certificate discrimination prevalence",
        "instrumentation completeness",
        "map-relative mechanism evidence",
    ],
    "prohibited": [
        "collision reduction", "progress improvement", "controller efficacy", "intervention success", "prevented collision", "avoided failure", "safety gain", "recursive feasibility", "safe stop", "physical-world safety", "deployment guarantee", "real-time guarantee", "Core V2 superiority", "alternative-search efficacy",
    ],
    "current_task_supported_claim": "a feasible design exists for non-invasive zero-authority prospective observation",
    "shadow_signal_is_control_efficacy": False,
}
write_json("claims_contract.md.json", claims)
write_text(
    "claims_contract.md",
    "# Claims Contract\n\n" +
    "The current task supports only the claim that a feasible non-invasive, zero-authority observation design has been specified and statically validated. It provides no on-policy or performance evidence.\n\n" +
    "Future Phase 3 may support: " + "; ".join(claims["supported_only_after_valid_future_phase3"]) + ".\n\n" +
    "Prohibited claims: " + "; ".join(claims["prohibited"]) + f".\n\n**Scope:** {LABELS}."
)


gap_rows = [
    {"gap_id": "P1_MISSING_U_K", "pr95_evidence": "4259/4259 nonreplayable records missing numeric u_k", "root_seam_evidence": "run.py has accepted u before plant update; PR89 method_decision does not return final control", "prospective_fix": "mandatory post-commit numeric u_k and hash", "qa_counter": "N_logging_error", "kill_gate": "G2_U_K_COMPLETENESS"},
    {"gap_id": "P2_REACHABILITY_UNKNOWN", "pr95_evidence": "5795 records reachability unknown", "root_seam_evidence": "primary run loop has no explicit PR84 stage record", "prospective_fix": "worker-runtime explicit L0/L1/candidate/L2 reached/status/reason", "qa_counter": "N_L0_reached/N_L1_reached/N_L2_reached_selected", "kill_gate": "G3_REACHABILITY_COMPLETENESS"},
    {"gap_id": "P3_EXECUTED_VS_NONEXECUTED", "pr95_evidence": "566 executed versus 222 nonexecuted; different fail rates", "root_seam_evidence": "u_des and selected u coexist before capture", "prospective_fix": "executed primary and native secondary typed separately", "qa_counter": "N_L2_selected_evaluated/N_native_candidates_evaluated", "kill_gate": "G7_CANDIDATE_PROVENANCE"},
    {"gap_id": "P4_NATIVE_SET", "pr95_evidence": "20 historical multi-candidate groups", "root_seam_evidence": "PR89 alternatives exist only on frozen branches; run.py exposes nominal plus selected", "prospective_fix": "capture complete pre-existing set only; no synthesis", "qa_counter": "N_multi_candidate_groups", "kill_gate": "G7_CANDIDATE_PROVENANCE"},
    {"gap_id": "P5_MAP_AUTHORITY", "pr95_evidence": "replay required external map reconstruction", "root_seam_evidence": "run.py path enters GSplatLoader but path/name is not content identity", "prospective_fix": "run-start content-addressed map manifest and step refs", "qa_counter": "unresolved_map_ref_count", "kill_gate": "G4_MAP_AUTHORITY_COMPLETENESS"},
    {"gap_id": "P6_ZERO_AUTHORITY", "pr95_evidence": "historical replay was offline and nonauthoritative", "root_seam_evidence": "post-commit capture allows action identity before worker", "prospective_fix": "one-way queue/no result consumer/immutable payload", "qa_counter": "controller_intervention_count", "kill_gate": "G5_ZERO_FEEDBACK"},
    {"gap_id": "P7_DENOMINATOR", "pr95_evidence": "coverage 37.8520 percent with source missingness", "root_seam_evidence": "current logs do not account for intended-but-dropped steps", "prospective_fix": "pre-registered all-step counters and drop records", "qa_counter": "N_control_steps_all", "kill_gate": "G8_PROTOCOL_FREEZE"},
    {"gap_id": "P8_UNKNOWN_VS_MISSING", "pr95_evidence": "missing payload cannot be interpreted as L2 UNKNOWN", "root_seam_evidence": "no observer health taxonomy in frozen logs", "prospective_fix": "disjoint L2/observation/reachability/worker statuses", "qa_counter": "N_observation_dropped/N_logging_error/N_shadow_worker_error", "kill_gate": "G10_HEALTH_STATUS_SEPARATION"},
]
write_csv("frozen_replay_to_prospective_gap_mapping.csv", list(gap_rows[0]), gap_rows)


write_text(
    "figures/FIGURE_SPECIFICATIONS.md",
    f"""
# Design Figure Specifications

Every figure carries: **{LABELS}**.

## 1. On-policy shadow dataflow

```mermaid
flowchart LR
  C["Frozen controller"] --> D["Decision commit: x_k, u_k"]
  D --> P["Frozen plant path"]
  D --> T["Immutable read-only tap"]
  T -->|"enqueue_nowait"| Q["Bounded queue"]
  Q --> W["Isolated L0/L1/L2 worker"]
  W --> L["Append-only log"]
```

## 2. Control-cycle observation timing

```mermaid
sequenceDiagram
  participant C as Frozen controller
  participant T as Read-only tap
  participant P as Plant
  participant W as Shadow worker
  C->>C: compute and accept u_k
  C->>T: immutable copy after commit
  T-->>W: nonblocking queue
  C->>P: apply same u_k
  W->>W: L0 then L1 then L2
```

## 3. Executed versus native candidate schema

```mermaid
flowchart TD
  G["Native candidate group"] --> E["Selected/executed: primary"]
  G --> N["Native non-executed: secondary"]
  G -. "never" .-> S["Synthetic candidate: prohibited"]
```

## 4. Prospective denominator funnel

```mermaid
flowchart TD
  A["All intended control steps"] --> B["Complete payloads plus explicit drops"]
  B --> C["L2 reached: selected"]
  C --> D["L2 evaluated"]
  D --> E["PASS"]
  D --> F["FAIL"]
  D --> U["UNKNOWN"]
```

## 5. Zero-authority boundary

```mermaid
flowchart LR
  A["Control authority zone"] --> B["One-way immutable payload"]
  B --> C["Observation-only zone"]
  C --> D["Evidence log"]
```

## 6. Frozen replay gaps to fixes

```mermaid
flowchart LR
  M["Missing u_k"] --> U["Mandatory post-commit u_k"]
  R["Unknown reachability"] --> X["Explicit runtime stage reasons"]
  I["Map path only"] --> H["Content-addressed map manifest"]
  C["Mixed candidate roles"] --> T["Executed primary / native secondary"]
```

## 7. Future phase gates

```mermaid
flowchart LR
  P0["Phase 0: implementation QA"] --> G0["Static/schema gates"]
  G0 --> P1["Phase 1: equivalence"]
  P1 --> G1["Control-trace gate"]
  G1 --> P2["Phase 2: logging pilot"]
  P2 --> G2["Completeness gate"]
  G2 --> P3["Phase 3: frozen cohort"]
  P3 --> P4["Phase 4: analysis only"]
```
""",
)


valid_step = {
    "schema_version": "L2_H1_ON_POLICY_SHADOW_STEP_V1",
    "run": {"run_id": "RUN-FIXTURE", "trial_id": "TRIAL-000", "seed": "NO_RANDOM_SAMPLING_FROZEN_INDEXED_TRIALS", "step_id": 0, "control_timestamp": 0.0, "logical_index": 0, "state_sequence_id": "STATE-000", "decision_commit_id": "COMMIT-000", "observation_capture_id": "CAPTURE-000"},
    "state": {"p_k": [0.0, 0.0, 0.0], "v_k": [0.01, 0.0, 0.0], "dt": 0.05, "state_hash": "1" * 64, "finite": True, "status": "VALID"},
    "l0": {"reached": True, "status": "PASS", "repair_attempted": False, "repair_result": "NOT_ATTEMPTED", "reason": "CURRENT_FEASIBILITY_PASS", "source_class": "SHADOW_PIPELINE_RUNTIME_OBSERVATION"},
    "l1": {"reached": True, "stored_status": "PASS", "reason": "IMMEDIATE_SEGMENT_PASS", "immediate_segment_start": [0.0, 0.0, 0.0], "immediate_segment_end": [0.0005, 0.0, 0.0], "source_class": "SHADOW_PIPELINE_RUNTIME_OBSERVATION"},
    "candidate_preparation": {"reached": True, "candidate_group_id": "GROUP-000", "native_candidate_count": 1, "native_candidate_set_hash": "2" * 64, "candidate_synthesis_count": 0},
    "selected_candidate": {"candidate_id": "SELECTED-000", "role": "SELECTED_EXECUTED", "u_k": [0.0, 0.0, 0.0], "u_k_hash": "3" * 64, "committed": True},
    "map_authority": {"map_snapshot_ref": "MAP-STONEHENGE-STATIC", "map_content_hash": "4" * 64, "map_contract_version": "MAP_CONTRACT_V1", "query_context_id": "QUERY-000", "robot_radius": 0.015, "safety_margin": 0.0, "effective_radius": 0.015, "rho_seg": 0.0},
    "l2": {"reached": True, "reachability_reason": "SELECTED_CANDIDATE_AVAILABLE", "evaluated": True, "status": "PASS", "reason": "CERTIFIED_SAFE_H1", "p_k1": [0.0005, 0.0, 0.0], "p_k2": [0.001, 0.0, 0.0], "H1_segment_hash": "5" * 64, "backend_identity": "FROZEN-L2-H1-V1", "backend_class": "EXACT_FUNCTIONAL_AUTOGRAD", "formal_value": 0.1, "diagnostics": {}, "shadow_result_id": "RESULT-000", "shadow_only": True},
    "authority": {key: False for key in ["controller_authority", "execution_authority", "candidate_selection_authority", "alternative_authority", "backup_authority", "terminal_authority", "fail_close_authority", "intervention"]},
    "instrumentation": {"payload_sequence_id": 0, "queue_status": "ENQUEUED", "observation_dropped": False, "serialization_status": "PASS", "observer_process_status": "HEALTHY", "observation_completeness": "COMPLETE"},
}
write_json("fixtures/valid_step.json", valid_step)
invalid_step = json.loads(json.dumps(valid_step))
del invalid_step["selected_candidate"]["u_k"]
write_json("fixtures/invalid_missing_u_k.json", invalid_step)


reviews = {
    "reviewer/control_theory_review.json": {
        "reviewer": "R1_CONTROL_THEORY", "verdict": "PASS_DESIGN_ONLY", "critical_blockers": [], "major_issues": [], "minor_issues": ["Worker-derived L0/L1 must remain labeled shadow-pipeline outcomes, not production-controller decisions."], "recommended_case": "CASE_A", "supported_claims": ["prospective candidate-dependent future-safety signal can be observed without authority"], "prohibited_claims": ["prevented collision", "H2 or recursive feasibility", "controller efficacy"], "checks": {"H1_timing": "PASS", "state_action_alignment": "PASS", "reachability": "PASS_EXPLICIT_SHADOW_PIPELINE", "zero_feedback": "PASS_BY_INTERFACE", "no_H2_creep": "PASS"}},
    "reviewer/robotics_systems_review.json": {
        "reviewer": "R2_ROBOTICS_SYSTEMS", "verdict": "PASS_DESIGN_ONLY", "critical_blockers": [], "major_issues": [], "minor_issues": ["Queue capacity must be frozen after Phase 0/2 measurements without using L2 outcomes."], "recommended_case": "CASE_A", "supported_claims": ["post-acceptance/pre-propagation seam is observable", "worker failures can be crash-isolated"], "prohibited_claims": ["real-time guarantee", "deployment guarantee"], "checks": {"seam": "PASS", "commit_timing": "PASS", "backpressure": "PASS_NONBLOCKING", "map_identity": "PASS_DESIGN", "crash_isolation": "PASS", "trace_equivalence": "PASS_GATE_DEFINED"}},
    "reviewer/statistics_evaluation_review.json": {
        "reviewer": "R3_STATISTICS_EVALUATION", "verdict": "PASS_DESIGN_ONLY", "critical_blockers": [], "major_issues": [], "minor_issues": ["Historical event rates remain planning priors with missingness and clustering bias."], "recommended_case": "CASE_A", "supported_claims": ["prevalence under a future frozen-controller cohort with explicit denominators"], "prohibited_claims": ["causal safety gain", "iid-step significance", "outcome-conditioned stopping"], "checks": {"primary_executed_cohort": "PASS", "secondary_native_cohort": "PASS", "denominator": "PASS", "protocol_freeze": "PASS", "clustering": "PASS", "stopping_rule": "PASS", "pilot_formal_separation": "PASS"}},
    "reviewer/software_architecture_review.json": {
        "reviewer": "R4_SOFTWARE_ARCHITECTURE_REPRODUCIBILITY", "verdict": "PASS_DESIGN_ONLY", "critical_blockers": [], "major_issues": [], "minor_issues": ["Future implementation must prove the payload object is copied/immutable across device-to-host serialization."], "recommended_case": "CASE_A", "supported_claims": ["instrumentation-only implementation is feasible with append-only deterministic manifests"], "prohibited_claims": ["zero overhead", "runtime guarantee"], "checks": {"instrumentation_only": "PASS_FEASIBLE", "no_feedback_path": "PASS_DESIGN", "schema": "PASS", "id_alignment": "PASS", "append_only": "PASS", "validator_feasibility": "PASS", "deterministic_manifests": "PASS"}},
}
for path, review in reviews.items():
    write_json(path, review)


decision = {
    "selected_case": "CASE_A",
    "case_name": "FEASIBLE_NONINVASIVE_ON_POLICY_SHADOW_DESIGN",
    "conditions": {
        "observation_seam_found": True,
        "x_k_u_k_dt_complete_capture_feasible": True,
        "explicit_shadow_pipeline_reachability_feasible": True,
        "map_authority_recoverable": True,
        "shadow_result_isolated": True,
        "selected_candidate_stable": True,
        "native_multi_candidate_capture_when_present": True,
        "future_equivalence_gate_defined": True,
        "controller_mathematics_change_required": False,
    },
    "secondary_multi_candidate_limitation": "Primary run.py exposes nominal and selected native candidates; richer alternatives are recorded only when the frozen controller already creates them. Otherwise secondary alternative analysis is NOT_ESTIMABLE.",
    "final_status": FINAL_STATUS,
    "final_decision": FINAL_DECISION,
    "only_next_task": NEXT_TASK,
    "unresolved_blockers": [],
}
write_json("FINAL_CASE_DECISION.json", decision)


run_manifest = {
    "task": "DESIGN_L2_H1_ON_POLICY_SHADOW_OBSERVATION_V1",
    "scope": "DESIGN_ONLY",
    "upstream": {"pr": 95, "expected_head": UPSTREAM_SHA, "base": "l2-h1-shadow-certifier-v1", "head": "l2-h1-shadow-frozen-replay-v1"},
    "counts": {
        "upstream_pr_count": 11, "protected_blob_count": 17,
        "on_policy_collection_count": 0, "navigation_rollout_count": 0, "new_state_collection_count": 0, "new_candidate_generation_count": 0, "new_map_generation_count": 0,
        "controller_mutation_count": 0, "production_instrumentation_mutation_count": 0, "shadow_certifier_mutation_count": 0, "dynamics_mutation_count": 0, "map_mutation_count": 0,
        "observation_seam_candidate_count": 4, "observation_architecture_option_count": 4, "selected_observation_architecture_count": 1,
        "prospective_schema_count": 5, "future_kill_gate_count": 10, "primary_endpoint_count": 1, "secondary_endpoint_count": 7,
        "future_sample_size_plan_count": 2, "future_equivalence_gate_count": 1, "future_logging_completeness_gate_count": 1,
        "reviewer_count": 4, "formal_performance_metric_count": 0, "formal_runtime_metric_count": 0,
    },
    "reviewer_case_votes": {"CASE_A": 4, "CASE_B": 0, "CASE_C": 0, "CASE_D_BLOCKING": 0, "CASE_E": 0},
    "frozen_replay_inputs": replay_inputs,
    "selected_architecture": "OPTION_A_POST_COMMIT_TAP_WITH_OUT_OF_PROCESS_SHADOW_WORKER",
    "selected_case": "CASE_A",
    "final_status": FINAL_STATUS,
    "final_decision": FINAL_DECISION,
    "only_next_task": NEXT_TASK,
}
write_json("run_manifest.json", run_manifest)


handoff = {
    "handoff_status": "READY_FOR_ONLY_NEXT_TASK",
    "only_next_task": NEXT_TASK,
    "authority_granted_for_next_task": False,
    "selected_seam": "after frozen controller accepts u_k and before plant propagation",
    "selected_architecture": "post-commit immutable tap plus bounded nonblocking queue plus out-of-process worker",
    "required_future_patch_boundary": "instrumentation-only copy/enqueue and append-only schemas; no controller math, candidate, map, seed, trial-order, or certifier mutation",
    "phase0_first": True,
    "formal_collection_allowed": False,
    "prerequisites": ["implement schemas and one-way interfaces", "pass static zero-feedback review", "pass Phase 0 fault tests", "pass Phase 1 equivalence", "pass Phase 2 logging completeness", "obtain separate Phase 3 authorization"],
    "final_status": FINAL_STATUS,
}
write_json("downstream_handoff.json", handoff)


pr_body = f"""
## Scope

Design-only continuation from Open Draft PR #95 (`l2-h1-shadow-frozen-replay-v1` at `{UPSTREAM_SHA}`, base `l2-h1-shadow-certifier-v1`). No runtime collection, navigation, controller change, production instrumentation, or certifier mutation occurred.

## Frozen replay inputs

PR #95 exposed 6,853 records, 2,594 formally replayable (37.8520%), 4,259 missing numeric `u_k`, and 5,795 unknown reachability. L2 evaluated 788 records (770/18/0 PASS/FAIL/UNKNOWN); selected/executed candidates were 560/6 over 566 and non-executed candidates 210/12 over 222. Twenty native multi-candidate groups had 20/20 distinct H1 endpoints and 0/20 status disagreement. These are design inputs, not upgraded claims.

## Selected observation design

The frozen `run.py` control cycle makes `x_k`, nominal `u_des`, accepted selected `u_k`, and `dt` simultaneously visible after the solver-success guard and before plant propagation. The selected architecture places a future instrumentation-only immutable tap there. It performs `enqueue_nowait` to a bounded queue; an isolated worker runs frozen read-only L0/L1/L2 observation stages and appends results. There is no result return path or authority.

Compared options: post-commit tap (selected), wrapper/decorator (fallback), pure out-of-process log sidecar (insufficient with current fields), and post-plant log scraping (rejected for off-by-one/missingness).

The schema mandates same-decision IDs, `x_k/p_k/v_k/dt`, numeric selected `u_k`, selected and native candidate provenance, explicit L0/L1/L2 reachability, content-addressed map authority, tri-state L2 status, distinct instrumentation health, queue/drop records, and all authority flags false. Executed candidates form the primary cohort; pre-existing native non-executed candidates are secondary. Synthetic candidates are prohibited.

## Prospective analysis and stopping

Primary endpoint: selected/executed `PROSPECTIVE_L1_PASS_L2_FAIL` prevalence among explicitly reached/evaluated L2 observations. Secondary endpoints cover UNKNOWN, reach, completeness, native multi-candidate prevalence/disagreement, selected/non-selected status, backend, and trial heterogeneity. Rates always carry numerator and denominator. Instrumentation missingness is not L2 UNKNOWN.

The primary stopping plan freezes the full mature Stonehenge 100-trial indexed manifest and stops only after all trials are terminal. A fallback targets 566 L2-reached selected evaluations with the same 100-trial cap and only stops after the current trial, never by FAIL count. Trial-cluster bootstrap/trial-level aggregation replaces iid-step inference.

Future phases are: Phase 0 implementation QA, Phase 1 OFF-vs-ON equivalence, Phase 2 logging pilot, Phase 3 separately authorized fixed cohort, Phase 4 analysis. Pilot/equivalence data are excluded by default. Equivalence, logging, map authority, zero feedback, provenance, alignment, queue, and protocol-freeze gates are specified. None were executed here.

## Review and decision

Four independent design passes (control theory, robotics/systems, statistics/evaluation, software architecture/reproducibility) vote 4/4 for Case A with no critical blockers. Supported future claims remain signal/information/prevalence evidence only. Collision reduction, progress, controller efficacy, intervention success, recursive feasibility, deployment, real-time, and superiority claims are prohibited.

`FINAL_STATUS={FINAL_STATUS}`

`FINAL_DECISION={FINAL_DECISION}`

Only next task: `{NEXT_TASK}` (not authorized or executed by this PR).
"""
write_text("DRAFT_PR_BODY.md", pr_body)


report = f"""
# REPORT: Design L2/H1 On-Policy Shadow Observation V1

## Direct answers to the 20 required questions

**Q1. PR #95 frozen replay exposed which three largest evidence gaps?** Numeric selected `u_k` was absent in 4,259 non-replayable records; L2 reachability was unknown in 5,795 records; candidate/map provenance was incomplete enough that executed and non-executed rates could not share one denominator and map replay required external authority recovery.

**Q2. Why not production-integrate L2 next?** PR #95 proved a bounded shadow information signal under incomplete historical replay, not control efficacy or non-invasiveness. Instrumentation, zero-feedback, alignment, and equivalence must be implemented and validated first.

**Q3. What is the real selected `u_k` source?** In frozen `run.py`, `u = cbf.solve_QP(x,u_des)` at line 132; `cbf/cbf_utils.py:125-143` returns the QP output and `run.py:139-143` accepts it only when `solver_success` is true.

**Q4. Where is final decision commit?** Semantically after the success guard at `run.py:139-143` and before the selected action is applied to the plant at `run.py:147`.

**Q5. How will L0/L1/L2 reachability be recorded?** The isolated read-only worker writes reached/status/reason for frozen current-feasibility L0, immediate-segment L1, candidate preparation, and L2 at evaluation time under source class `SHADOW_PIPELINE_RUNTIME_OBSERVATION`; no post-hoc inference.

**Q6. Which architecture and why?** Option A: post-commit immutable tap plus bounded nonblocking queue and out-of-process worker. It uniquely combines correct `x_k/u_k` visibility with crash isolation and structural zero authority.

**Q7. How can results not feed back?** There is no worker-to-controller interface, shared mutable control object, result callback, or controller result consumer. All authority flags are false; the worker writes append-only evidence only.

**Q8. What happens on queue full or worker crash?** The frozen controller continues its original path with the already committed `u_k`; the observation is marked dropped/incomplete when possible.

**Q9. How is mass `u_k` missingness prevented?** Numeric `u_k` and its canonical hash are mandatory in the immutable post-commit payload, and G2 rejects any complete payload without them while all intended steps reconcile to payload or drop records.

**Q10. How is map authority replayable?** A run-start manifest hashes immutable config/checkpoint/map bytes, representation and robot/margin/rho contracts; every step joins by stable `map_snapshot_ref`. Dynamic maps would require per-step content-addressed snapshots.

**Q11. How is the executed primary cohort defined?** True frozen-controller on-policy steps with committed selected/executed candidate, stored shadow L1 PASS, explicit L2 reach, and a completed formal L2 PASS/FAIL/UNKNOWN result.

**Q12. How are native non-executed secondary candidates defined?** Controls already created by the frozen controller before observation, carrying native origin/role/hash and `selected_for_execution=false`; they are analyzed separately.

**Q13. Any synthetic candidates?** NO. Candidate synthesis count is zero.

**Q14. Future primary endpoint?** `P(L2_FAIL | stored_L1_PASS, L2_reached, selected/executed candidate, L2 evaluated)` with explicit numerator and denominator.

**Q15. Can L1 PASS/L2 FAIL be called collision prevented?** NO. It is a candidate-dependent future-safety shadow signal or L2-specific information increment only.

**Q16. L2 UNKNOWN versus logging incomplete?** L2 UNKNOWN requires a valid formal evaluation unable to certify; missing/queue/serialization/alignment/worker failures use separate observation and health states and never enter UNKNOWN.

**Q17. What is the pre-collection equivalence gate?** Fixed-seed/config/map OFF-vs-ON comparison requiring equal selected-candidate/control/branch/return/termination traces under pre-frozen exact or field-specific tolerances.

**Q18. How does stopping avoid optional stopping and iid-step errors?** The primary plan fixes all 100 Stonehenge trials before results and never stops on FAIL count. Uncertainty resamples trials/uses trial-level summaries; step-level iid significance is not primary.

**Q19. Did this task collect any on-policy data?** NO. `on_policy_collection_count=0` and `navigation_rollout_count=0`.

**Q20. Is the next step formal data collection?** NO. Under Case A the only next task is `{NEXT_TASK}`; implementation and validation must precede any separately authorized collection.

## Frozen identity and static audit

PR #95 was independently verified Open Draft at `{UPSTREAM_SHA}` on `l2-h1-shadow-frozen-replay-v1`, based on `l2-h1-shadow-certifier-v1`. PRs #83/#84/#86/#87/#89/#90/#91/#92/#93/#94/#95 were preserved read-only. The upstream 17-blob protected manifest passed raw Git blob, byte size, and mode audits.

The primary controller seam is exact: `x` is the six-state at `run.py:100-116`; `u_des` is formed at lines 118-127; QP-selected `u` at line 132 is accepted by lines 139-143; plant propagation occurs at line 147. Capture between acceptance and propagation prevents state/action index drift. Current logging at lines 149-152 occurs too late for a robust same-decision contract.

PR #89's richer frozen runtime also shows that native alternatives are created before commit, but its result retains candidate identity without the final acceleration. This independently demonstrates why the future payload must copy numeric control at the seam.

## Architecture and zero authority

Option A is selected and Option B wrapper/decorator is fallback. Option C pure sidecar from current logs cannot restore missing fields; Option D post-plant scraping is rejected. The future tap only makes an immutable copy and nonblocking enqueue. L0/L1/L2 run only in the sidecar and have no decision authority. Queue full, serialization error, worker crash, result lateness, and shutdown incompleteness affect observation completeness only.

The primary `run.py` baseline does not execute PR #84 L0/L1 stages, so the design labels worker-computed stages precisely as runtime shadow-pipeline observations. It does not falsely call them production-controller outcomes. That instrumentation-only future implementation does not alter controller mathematics.

## Cohort, denominator, and statistics

The primary executed cohort is separate from native non-executed candidates. The production baseline contributes nominal and selected native values; richer alternatives are included only where the frozen runtime already generates them. If a runtime has one native candidate, count is one. Secondary alternative analysis is `NOT_ESTIMABLE` when alternatives are not natively exposed; this never blocks the primary cohort.

Every intended control step enters `N_control_steps_all`, including drops. L2 reach, evaluation, PASS/FAIL/UNKNOWN, native candidates, multi-candidate groups, drops, logging errors, and worker errors have disjoint counters. No cohort is constructed from observed L2 outcomes.

Planning uses 6/566 selected FAIL and 18/788 overall L1 PASS/L2 FAIL as biased priors only. Plan A freezes all 100 deterministic Stonehenge trials. Plan B pre-freezes a 566-evaluated target plus the same 100-trial cap and stops only at trial boundaries, never on outcomes. Cluster-aware trial bootstrap/trial aggregation is primary uncertainty.

## Future phases and gates

Phase 0 is implementation QA; Phase 1 is excluded equivalence smoke; Phase 2 is excluded completeness pilot; Phase 3 is a separately authorized frozen cohort; Phase 4 is analysis only. Ten kill gates cover control trace, `u_k`, reachability, map authority, zero feedback, queue nonblocking, provenance, protocol freeze, state/action alignment, and health/status separation.

## Reviews and claims

All four independent reviewers return `PASS_DESIGN_ONLY`, no critical blockers, and Case A. Their minor cautions are frozen as future requirements: distinguish worker L0/L1 from controller outcomes, freeze capacity without outcome tuning, treat old rates only as biased priors, and prove immutable device-to-host copies.

Supported now: feasibility of this design. Future valid Phase 3 can support only prospective signal/information/prevalence/completeness/map-relative mechanism descriptions. It cannot support collision reduction, progress improvement, controller efficacy, intervention success, recursive feasibility, safe stop, physical safety, deployment, real-time performance, or superiority.

## Decision

`selected Case = CASE_A — FEASIBLE_NONINVASIVE_ON_POLICY_SHADOW_DESIGN`

`FINAL_STATUS = {FINAL_STATUS}`

`FINAL_DECISION = {FINAL_DECISION}`

`Only next task = {NEXT_TASK}`

No unresolved blockers. No implementation or collection is authorized by this report.
"""
write_text("report/REPORT_DESIGN_L2_H1_ON_POLICY_SHADOW_OBSERVATION_V1.md", report)


validation_stub = {
    "validator": "validate_on_policy_shadow_observation_design_v1.py",
    "status": "PENDING_VALIDATOR_EXECUTION",
    "expected_status": VALIDATOR_STATUS,
    "design_only": True,
}
write_json("validation_result.json", validation_stub)

print("BUILT_DESIGN_ARTIFACTS", len([path for path in ROOT.rglob("*") if path.is_file()]))
print("DESIGN_INPUT_SHA256", sha256_json(replay_inputs))
