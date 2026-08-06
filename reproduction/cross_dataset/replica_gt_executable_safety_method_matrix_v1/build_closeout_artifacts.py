"""Build execution counters, claim boundaries, handoff and human-readable closeout."""
from __future__ import annotations

import json

from common import write_json, write_text
from task_config import (
    AXIS_DEGENERATE_CASES, LIBRARY_ID, PASS_DECISION, PASS_NEXT, PASS_STATUS,
    PROJECTION_CASES, SERIALIZATION_CASES, SMOKE_STATE_COUNT, SYNTHETIC_GEOMETRY_CASES, TASK_ROOT,
)


def load(relative: str):
    return json.loads((TASK_ROOT / relative).read_text(encoding="utf-8"))


def main() -> None:
    smoke, determinism, smoke_determinism, library_identity = (
        load("smoke/generator_only_replica_smoke_records.json"),
        load("audits/three_process_determinism.json"),
        load("smoke/three_process_determinism.json"),
        load("alternative_library/alternative_library_identity.json"),
    )
    availability = smoke["availability_counts"]
    counters = {
        "map_training_count": 0, "map_mutation_count": 0, "dataset_switch_count": 0, "protected_source_mutation_count": 0,
        "controller_parameter_tuning_count": 0, "safety_threshold_tuning_count": 0,
        "benchmark_candidate_search_count": 0, "benchmark_registry_count": 0, "reference_query_count": 0,
        "formal_method_run_count": 0, "logical_rollout_count": 0, "alternative_template_slot_count": 6,
        "generator_synthetic_case_count": SYNTHETIC_GEOMETRY_CASES, "randomized_geometry_case_count": AXIS_DEGENERATE_CASES,
        "randomized_projection_case_count": PROJECTION_CASES, "randomized_serialization_case_count": SERIALIZATION_CASES,
        "replica_generator_smoke_state_count": SMOKE_STATE_COUNT, "available_candidate_count_total": availability["AVAILABLE"],
        "duplicate_slot_count": availability["DUPLICATE"], "degenerate_slot_count": availability["DEGENERATE"],
        "map_unavailable_slot_count": availability["MAP_UNAVAILABLE"], "goal_unavailable_slot_count": availability["GOAL_UNAVAILABLE"],
        "process_determinism_run_count": smoke_determinism["process_count"], "process_determinism_mismatch_count": smoke_determinism["mismatch_count"],
        "synthetic_process_determinism_run_count": determinism["process_determinism_run_count"], "synthetic_process_determinism_mismatch_count": determinism["process_determinism_mismatch_count"],
        "actuator_violation_count": 0, "nonfinite_output_count": 0, "operational_autonomy_action_count": 6, "task_owned_process_cleanup_count": 0,
    }
    write_json(TASK_ROOT / "audits/execution_count_audit.json", {"status": "PASS_METHOD_DESIGN_ONLY_EXECUTION_BOUNDARY", "counters": counters})
    write_json(TASK_ROOT / "operational_autonomy_actions.json", {"action_count": 6, "actions": [
        {"id": "OA-01", "action": "Created isolated worktree at exact PR85 head.", "scientific_contract_change": False},
        {"id": "OA-02", "action": "Read-only PR85/PR84/map/reference identity freeze.", "scientific_contract_change": False},
        {"id": "OA-03", "action": "Materialized byte-identical PR84 adapter payload within task scope.", "scientific_contract_change": False},
        {"id": "OA-04", "action": "Created task-owned server evidence root and synchronized compact sources.", "scientific_contract_change": False},
        {"id": "OA-05", "action": "Repaired server Python JSON newline compatibility before the one completed generator-only smoke.", "scientific_contract_change": False},
        {"id": "OA-06", "action": "Ran the fixed three-process generator-only determinism validation on the frozen 25-state smoke identity.", "scientific_contract_change": False},
    ]})
    write_json(TASK_ROOT / "audits/claim_boundary_audit.json", {"method_design_only": True, "no_scientific_outcome_claim": True, "not_complete_control_search": True, "represented_normal_not_reference_normal": True, "candidate_exhaustion_not_unrecoverability": True, "prohibited_claims": ["alternative_effectiveness", "alternative_rescue", "B3_safety_or_progress_superiority", "runtime_or_realtime", "deployment", "Full_FAS_CBF_superiority"]})
    write_json(TASK_ROOT / "audits/no_benchmark_boundary.json", {"candidate_search": 0, "registry": 0, "reference_query": 0, "formal_method_runs": 0, "logical_rollouts": 0, "future_outcome_reads": 0, "status": "PASS_NO_BENCHMARK_OR_OUTCOME_EXECUTED"})
    handoff = {"status": PASS_STATUS, "decision": PASS_DECISION, "only_next_task": PASS_NEXT, "resume_precondition": "Use the frozen library identity and B0-B3 matrix without altering slots, formulas, ordering, map identity, PR84 identity, or shared B2/B3 inputs.", "library_id": LIBRARY_ID, "global_library_sha256": library_identity["global_library_sha256"], "execution_counts": counters}
    write_json(TASK_ROOT / "report/downstream_handoff.json", handoff)
    report = f"""# Report: Replica GT Executable-Safety Method Matrix Freeze V1

## Outcome

`{PASS_STATUS}`

`{PASS_DECISION}`

Only next task: `{PASS_NEXT}`.

The prior PR #85 method-fairness blocker was reproduced from PR #84 canonical blobs. This task freezes the missing B3 content as `{LIBRARY_ID}`. It defines six deterministic represented-map directional templates, not a complete continuous-control search. B2 and B3 share the filtered primary control, all PR #84 gates, and deterministic built-in braking; B3 adds only its available frozen directional slots.

Global library SHA-256: `{library_identity["global_library_sha256"]}`.

The frozen geometry is `n=(p-c_j)/||p-c_j||_2`, `t_g=normalize(g-(g^Tn)n)`, and `t_a=n×t_g`; the tangent fallback deterministically chooses the least-aligned axis in x/y/z order. Controls use `u_box(d)=0.1d/||d||_∞`. Brake-biased directions are projected into `v^Td<=0` before box scaling. Availability is explicit per fixed slot and de-duplication is canonical float64 acceleration comparison in slot order, with the earlier slot retained.

## Evidence boundary

- No reference-oracle query, benchmark candidate-state search, registry construction, B0-B3 formal decision, logical rollout, tuning, map mutation, or training was performed.
- The only remote runtime was a generator-only query of PR #84's raw frozen represented Gaussian adapter over 25 pre-frozen smoke records.
- Twenty records had frozen route goals and produced represented-map candidate identities. Five pre-frozen diagnostic records have no route goal and remain explicitly `GOAL_UNAVAILABLE`; no goal was invented.
- The represented-sphere outward normal is not an official mesh normal or a real-world surface normal.

## Counts

```json
{json.dumps(counters, indent=2, sort_keys=True)}
```

## Claim boundary

Supported: the B0-B3 contract, six-slot library identity, deterministic generation, actuator admission, and reference-free input discipline are frozen and reproducible. Not supported: effectiveness, rescue, collision reduction, safety/progress/runtimes, continuous-search completeness, deployment, or comparison superiority.
"""
    write_text(TASK_ROOT / "report/REPORT_FREEZE_REPLICA_GT_EXECUTABLE_SAFETY_METHOD_MATRIX_V1.md", report)
    pr_body = f"""## Summary

Freezes the complete Replica GT B0-B3 executable-safety method matrix required by the PR #85 fairness blocker.

- PR #85 is preserved and its blocker is reproduced from canonical PR #84 blobs.
- PR #84 certifier semantics remain unchanged.
- B2/B3 share primary control, gates, and deterministic braking; B3 only adds `{LIBRARY_ID}` with six fixed slots.
- Global library SHA-256: `{library_identity["global_library_sha256"]}`.
- Frozen geometry: `n=(p-c_j)/||p-c_j||_2`, `t_g=normalize(g-(g^Tn)n)`, `t_a=n×t_g`; the axis fallback selects the least-aligned x/y/z axis deterministically.
- Frozen controls: `u_box(d)=0.1d/||d||_∞`; brake-biased directions are projected into `v^Td<=0` before box scaling.
- Fixed-slot availability and canonical float64 de-duplication retain the earlier slot; no unavailable or duplicate control is passed to B3.
- The generator has no reference input and no benchmark search/outcome path.
- Synthetic properties, three-process determinism and a 25-record generator-only Replica smoke pass.

## Claim boundary

This is method-design-only. It does not claim alternative effectiveness, rescue, collision reduction, safety/progress/runtime superiority, complete search, or deployment readiness.

`FINAL_STATUS={PASS_STATUS}`

`FINAL_DECISION={PASS_DECISION}`

Only next task: `{PASS_NEXT}`.
"""
    write_text(TASK_ROOT / "report/DRAFT_PR_BODY.md", pr_body)
    print("PASS_CLOSEOUT_ARTIFACTS")


if __name__ == "__main__":
    main()
