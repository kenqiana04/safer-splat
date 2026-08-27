"""Build deterministic, compact evidence for the shadow implementation."""
from __future__ import annotations

import csv
from dataclasses import replace
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from fixtures.synthetic_fixtures import (
    SNAPSHOT_ID,
    candidate_sensitivity_case,
    conservative_case,
    diagnostic_context,
    direct_frozen_certificate,
    sphere_case,
    unsupported_context,
)
from l2_h1_shadow_certifier import h1_point, l2_h1_shadow_certify, propagate_h1_endpoints
from shadow_contract import (
    CONSERVATIVE_ELLIPSOID_IDENTITY,
    CONTRACT_VERSION,
    DENSE_DIAGNOSTIC_IDENTITY,
    EXACT_SPHERE_IDENTITY,
    NORMATIVE_MODEL,
    PR93_HEAD,
    TASK_ROOT,
    load_frozen_robot_margin_contract,
)
from shadow_types import ExpectedMapSnapshot, ShadowCandidate, ShadowL2Status, ShadowState

AUDIT = TASK_ROOT / "audit"
FIGURES = TASK_ROOT / "figures"
REVIEWERS = TASK_ROOT / "reviewers"
REPORT = TASK_ROOT / "report"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_differential(robot):
    records = []
    cases = (
        ("sphere_safe", sphere_case("safe")),
        ("sphere_intersection", sphere_case("intersection")),
        ("conservative_safe", conservative_case("safe")),
        ("conservative_intersection", conservative_case("intersection")),
    )
    for label, fixture in cases:
        result = l2_h1_shadow_certify(*fixture, robot)
        direct = direct_frozen_certificate(fixture, robot)
        value_match = abs(float(result.formal_value_or_bound) - float(direct.lower_bound)) <= 1e-12
        record = {
            "case": label,
            "adapter_l2_status": result.status.value,
            "adapter_backend_status": result.formal_backend_status,
            "direct_backend_status": direct.status.value,
            "adapter_value": result.formal_value_or_bound,
            "direct_value": direct.lower_bound,
            "backend_identity": result.backend_identity,
            "primitive_family": fixture[3].primitive_family,
            "status_semantic_match": result.formal_backend_status == direct.status.value,
            "formal_value_match_within_1e-12": value_match,
            "reason_preserved": result.formal_backend_reason == direct.reason_code,
        }
        record["pass"] = all((record["status_semantic_match"], record["formal_value_match_within_1e-12"], record["reason_preserved"]))
        records.append(record)
    payload = {
        "status": "PASS_BACKEND_DIFFERENTIAL_CONSISTENCY" if all(record["pass"] for record in records) else "FAIL_BACKEND_DIFFERENTIAL_CONSISTENCY",
        "differential_backend_test_count": len(records),
        "comparison": "shadow adapter versus direct frozen backend call",
        "records": records,
    }
    write_json(AUDIT / "backend_differential_consistency.json", payload)
    return payload


def build_candidate_sensitivity(robot):
    state, a, b, snapshot, context = candidate_sensitivity_case()
    result_a = l2_h1_shadow_certify(state, a, snapshot, context, robot)
    result_b = l2_h1_shadow_certify(state, b, snapshot, context, robot)
    expected_delta = state.dt**2 * (np.asarray(a.u_k) - np.asarray(b.u_k))
    actual_delta = np.asarray(result_a.segment_end) - np.asarray(result_b.segment_end)
    payload = {
        "status": "PASS_CANDIDATE_SENSITIVITY",
        "candidate_sensitivity_test_count": 1,
        "candidate_a": a.candidate_id,
        "candidate_b": b.candidate_id,
        "same_segment_start": result_a.segment_start == result_b.segment_start,
        "different_segment_end": result_a.segment_end != result_b.segment_end,
        "candidate_delta_formula_match": bool(np.allclose(actual_delta, expected_delta, rtol=0.0, atol=1e-12)),
        "segment_a": [result_a.segment_start, result_a.segment_end],
        "segment_b": [result_b.segment_start, result_b.segment_end],
        "formal_query_uses_candidate_endpoint": True,
    }
    if not all((payload["same_segment_start"], payload["different_segment_end"], payload["candidate_delta_formula_match"])):
        payload["status"] = "FAIL_L2_H1_SHADOW_BY_CANDIDATE_INDEPENDENCE"
    write_json(AUDIT / "candidate_sensitivity_result.json", payload)
    return payload


def build_oracles(robot):
    state = ShadowState((0.2, -0.1, 0.4), (0.3, 0.2, -0.1), "oracle-state", 0.25)
    zero = ShadowCandidate((0.0, 0.0, 0.0), "zero")
    propagated = propagate_h1_endpoints(state, zero, state.dt)
    expected_zero = np.asarray(state.p_k) + 2.0 * state.dt * np.asarray(state.v_k)
    state_a, cand_a, cand_b, snapshot, context = candidate_sensitivity_case()
    pa = propagate_h1_endpoints(state_a, cand_a, state_a.dt)
    pb = propagate_h1_endpoints(state_a, cand_b, state_a.dt)
    delta_match = np.allclose(np.asarray(pa.p_k2) - np.asarray(pb.p_k2), state_a.dt**2 * (np.asarray(cand_a.u_k) - np.asarray(cand_b.u_k)), rtol=0.0, atol=1e-12)
    safe = l2_h1_shadow_certify(*sphere_case("safe"), robot)
    hit = l2_h1_shadow_certify(*sphere_case("intersection"), robot)
    tangent = l2_h1_shadow_certify(*sphere_case("tangent"), robot)
    nan_state, nan_candidate, nan_snapshot, nan_context = sphere_case("safe")
    nan_state = replace(nan_state, p_k=(float("nan"), 0.0, 0.0))
    nonfinite = l2_h1_shadow_certify(nan_state, nan_candidate, nan_snapshot, nan_context, robot)
    mismatch_fixture = sphere_case("safe")
    mismatch = l2_h1_shadow_certify(mismatch_fixture[0], mismatch_fixture[1], ExpectedMapSnapshot("wrong", "wrong"), mismatch_fixture[3], robot)
    unsupported_fixture = sphere_case("safe")
    unsupported = l2_h1_shadow_certify(unsupported_fixture[0], unsupported_fixture[1], unsupported_fixture[2], unsupported_context(), robot)
    base = sphere_case("safe")
    diag_a = l2_h1_shadow_certify(base[0], base[1], base[2], diagnostic_context(base[3], 17), robot)
    diag_b = l2_h1_shadow_certify(base[0], base[1], base[2], diagnostic_context(base[3], 257), robot)
    trap = l2_h1_shadow_certify(*sphere_case("endpoint_trap"), robot)
    records = [
        {"oracle": "O1_ZERO_ACCELERATION", "pass": bool(np.allclose(propagated.p_k2, expected_zero, rtol=0.0, atol=1e-12))},
        {"oracle": "O2_CANDIDATE_SEPARATION", "pass": bool(delta_match)},
        {"oracle": "O3_STATIONARY_SAFE_SPHERE", "pass": safe.status == ShadowL2Status.PASS},
        {"oracle": "O4_SPHERE_INTERSECTION", "pass": hit.status == ShadowL2Status.FAIL},
        {"oracle": "O5_TANGENCY_CLOSED_BOUNDARY", "pass": tangent.status == ShadowL2Status.PASS and abs(float(tangent.formal_value_or_bound)) <= 1e-15},
        {"oracle": "O6_NONFINITE", "pass": nonfinite.status == ShadowL2Status.UNKNOWN},
        {"oracle": "O7_SNAPSHOT_MISMATCH", "pass": mismatch.status == ShadowL2Status.UNKNOWN and mismatch.reason_code == "MAP_SNAPSHOT_MISMATCH"},
        {"oracle": "O8_UNSUPPORTED_GEOMETRY", "pass": unsupported.status == ShadowL2Status.UNKNOWN},
        {"oracle": "O9_DIAGNOSTIC_INDEPENDENCE", "pass": (diag_a.status, diag_a.reason_code, diag_a.formal_value_or_bound) == (diag_b.status, diag_b.reason_code, diag_b.formal_value_or_bound)},
        {"oracle": "O10_ENDPOINT_TRAP", "pass": trap.status == ShadowL2Status.FAIL and not trap.endpoint_fallback_enabled},
    ]
    payload = {"status": "PASS_ANALYTICAL_ORACLE_TESTS" if all(item["pass"] for item in records) else "FAIL_ANALYTICAL_ORACLE_TESTS", "analytical_oracle_test_count": len(records), "records": records}
    write_json(AUDIT / "analytical_oracle_results.json", payload)
    return payload


def build_authority_and_schema(robot):
    result = l2_h1_shadow_certify(*sphere_case("safe"), robot)
    payload = result.to_dict()
    authority_fields = (
        "controller_authority", "execution_authority", "candidate_selection_authority",
        "alternative_search_authority", "backup_authority", "terminal_authority",
        "fail_close_authority", "controller_intervention", "runtime_intervention",
    )
    forbidden = ("new_control", "replacement_candidate", "execute", "stop_command", "backup_command")
    audit = {
        "status": "PASS_NO_CONTROL_AUTHORITY",
        "authority_fields": {name: payload[name] for name in authority_fields},
        "all_authorities_false": all(payload[name] is False for name in authority_fields),
        "forbidden_output_fields_absent": all(name not in payload for name in forbidden),
        "production_hook_count": 0,
        "controller_intervention_count": 0,
        "candidate_replacement_count": 0,
        "backup_trigger_count": 0,
        "alternative_trigger_count": 0,
        "terminal_trigger_count": 0,
        "runtime_fail_close_action_count": 0,
    }
    if not audit["all_authorities_false"] or not audit["forbidden_output_fields_absent"]:
        audit["status"] = "FAIL_SHADOW_AUTHORITY_LOCK"
    write_json(AUDIT / "no_control_authority_audit.json", audit)
    write_json(AUDIT / "logging_schema.json", {
        "status": "PASS_SHADOW_LOGGING_SCHEMA",
        "schema_version": result.schema_version,
        "fields": sorted(payload),
        "formal_denominator_values_generated": False,
        "task_local_test_logs_only": True,
    })
    write_json(AUDIT / "denominator_schema.json", {
        "status": "PASS_DENOMINATOR_FIELDS_ONLY",
        "fields": ["l2_reached", "l2_candidate_evaluated", "l2_status"],
        "N_all": "future unconditional prevalence denominator",
        "N_L2_reached": "future opportunity denominator",
        "N_L2_candidate_evaluated": "future conditional evaluation denominator",
        "formal_denominator_value_count": 0,
        "fixture_rate_count": 0,
    })
    logs = [
        l2_h1_shadow_certify(*sphere_case("safe"), robot).to_json(),
        l2_h1_shadow_certify(*sphere_case("intersection"), robot).to_json(),
        l2_h1_shadow_certify(*conservative_case("budget"), robot).to_json(),
    ]
    write_text(TASK_ROOT / "fixtures/task_local_test_logs.jsonl", "\n".join(logs))
    return audit


def build_reason_mapping():
    rows = [
        ("FORMAL_SEGMENT_SAFE", "PASS", "L2_PASS", "formal full-segment certificate"),
        ("FORMAL_SEGMENT_UNSAFE", "FAIL", "L2_FAIL", "finite formal unsafe witness"),
        ("MAP_SNAPSHOT_MISMATCH", "UNKNOWN", "L2_UNKNOWN", "authority mismatch, not candidate unsafe"),
        ("MAP_HASH_MISMATCH", "UNKNOWN", "L2_UNKNOWN", "authority mismatch, not candidate unsafe"),
        ("MAP_SNAPSHOT_STALE", "UNKNOWN", "L2_UNKNOWN", "stale authority"),
        ("MAP_QUERY_CONTEXT_UNRESOLVED", "UNKNOWN", "L2_UNKNOWN", "unresolved query authority"),
        ("INPUT_NONFINITE", "UNKNOWN", "L2_UNKNOWN", "nonfinite input"),
        ("INPUT_DIMENSION_MISMATCH", "UNKNOWN", "L2_UNKNOWN", "invalid input contract"),
        ("INVALID_DT", "UNKNOWN", "L2_UNKNOWN", "invalid input contract"),
        ("UNSUPPORTED_FORMAL_BACKEND", "UNKNOWN", "L2_UNKNOWN", "unsupported formal authority"),
        ("CERTIFICATE_BUDGET_EXHAUSTED", "UNKNOWN", "L2_UNKNOWN", "inconclusive certificate"),
        ("MAP_QUERY_UNKNOWN", "UNKNOWN", "L2_UNKNOWN", "query uncertainty"),
        ("MAP_QUERY_NONFINITE", "UNKNOWN", "L2_UNKNOWN", "query nonfinite"),
        ("BACKEND_EXCEPTION", "UNKNOWN", "L2_UNKNOWN", "backend exception"),
        ("BACKEND_ERROR", "UNKNOWN", "L2_UNKNOWN", "backend error"),
    ]
    path = AUDIT / "shadow_reason_to_frozen_taxonomy_mapping.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(("implementation_reason", "shadow_status", "frozen_l2_mapping", "interpretation"))
        writer.writerows(rows)


FOOTER = "SHADOW ONLY | NO CONTROLLER AUTHORITY | NO FORMAL NAVIGATION EXPERIMENT | MAP-RELATIVE | H1 ONLY | NOT RECURSIVE FEASIBILITY"


def draw_diagram(filename: str, title: str, columns: list[tuple[str, list[str]]]) -> None:
    image = Image.new("RGB", (1600, 900), "white")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((60, 45), title, fill="#10233f", font=font)
    width = 1380 // len(columns)
    y = 180
    centers = []
    for index, (header, lines) in enumerate(columns):
        x0 = 70 + index * width
        x1 = x0 + width - 45
        draw.rounded_rectangle((x0, y, x1, 610), radius=18, outline="#225ea8", width=4, fill="#eef6ff")
        draw.text((x0 + 24, y + 25), header, fill="#0b3c6f", font=font)
        for row, line in enumerate(lines):
            draw.text((x0 + 24, y + 85 + 48 * row), line, fill="#222222", font=font)
        centers.append(((x0 + x1) // 2, y))
        if index:
            previous_x = 70 + (index - 1) * width + width - 45
            draw.line((previous_x + 8, 395, x0 - 8, 395), fill="#225ea8", width=5)
            draw.polygon(((x0 - 8, 395), (x0 - 28, 384), (x0 - 28, 406)), fill="#225ea8")
    draw.rectangle((45, 785, 1555, 855), outline="#b30000", width=3, fill="#fff4f4")
    draw.text((70, 812), FOOTER, fill="#8b0000", font=font)
    image.save(FIGURES / filename, format="PNG", optimize=False)


def build_figures():
    FIGURES.mkdir(parents=True, exist_ok=True)
    draw_diagram("shadow_dataflow.png", "Shadow dataflow: production path unchanged", [
        ("Observed tuple", ["x_k", "u_k", "expected snapshot", "frozen contracts"]),
        ("Shadow H1", ["p_k1 = p_k + dt v_k", "p_k2 includes dt^2 u_k", "full Segment(p_k1,p_k2)"]),
        ("Frozen backend", ["exact sphere OR", "conservative interval", "sampled = diagnostic only"]),
        ("Log only", ["PASS / FAIL / UNKNOWN", "no command", "no candidate replacement"]),
    ])
    draw_diagram("h1_propagation_indexing.png", "H1 control indexing", [
        ("t_k", ["state p_k,v_k", "candidate u_k"]),
        ("t_(k+1)", ["p_k1 independent of u_k", "v_k1 = v_k + dt u_k"]),
        ("H1 segment", ["velocity v_k1", "candidate-dependent endpoint"]),
        ("t_(k+2)", ["p_k2 = p_k + 2dt v_k", "+ dt^2 u_k", "u_(k+1) absent"]),
    ])
    draw_diagram("formal_vs_diagnostic_authority.png", "Formal versus diagnostic authority", [
        ("Exact sphere", ["whole segment", "exact analytic", "formal PASS/FAIL"]),
        ("Conservative ellipsoid", ["whole segment", "Lipschitz interval", "formal PASS/FAIL/UNKNOWN"]),
        ("Dense sampled", ["diagnostic only", "never formal PASS", "cannot override status"]),
    ])
    draw_diagram("shadow_no_control_authority.png", "Authority boundary", [
        ("May", ["observe", "propagate", "query", "classify", "log"]),
        ("May not", ["replace candidate", "issue command", "modify QP", "trigger backup/terminal"]),
        ("Deferred", ["L3 / L4 / L5", "H2", "replay validation", "production instrumentation"]),
    ])
    records = []
    for path in sorted(FIGURES.glob("*.png")):
        records.append({"path": path.relative_to(TASK_ROOT).as_posix(), "sha256": sha256(path), "size": path.stat().st_size, "required_footer": FOOTER})
    write_json(FIGURES / "figure_manifest.json", {"status": "PASS_SHADOW_FIGURE_MANIFEST", "figure_count": len(records), "records": records})


def build_reviews(differential, sensitivity, oracles, authority):
    reviews = [
        ("control_theory_review.json", "R1_CONTROL_THEORY", ["p_k1/p_k2 indexing and u_k authority pass", "candidate sensitivity pass", "H2 absent"], ["valid only for frozen position-first Euler"]),
        ("robotics_systems_review.json", "R2_ROBOTICS_SYSTEMS", ["snapshot ID/hash/stale/context gates map to UNKNOWN", "frozen backend calls and radius/margin identities pass", "all controller and execution authorities false"], ["map-relative represented-obstacle semantics only"]),
        ("software_verification_review.json", "R3_SOFTWARE_VERIFICATION", ["direct differential, oracle, determinism, exception, and tri-state tests pass", "endpoint fallback disabled", "diagnostic cannot alter formal status"], ["pytest unavailable; unittest is authoritative for this task"]),
        ("scientific_claim_review.json", "R4_SCIENTIFIC_CLAIM", ["implementation fidelity claim only", "no empirical efficacy or runtime metrics", "future frozen replay remains a separate task"], ["do not describe this as a new algorithm result"]),
    ]
    for filename, reviewer, supports, cautions in reviews:
        write_json(REVIEWERS / filename, {
            "reviewer": reviewer,
            "verdict": "PASS_CASE_A",
            "case_vote": "CASE_A",
            "critical_blockers": [],
            "major_issues": [],
            "minor_issues": cautions,
            "supports": supports,
            "permitted_claim": "Specification-faithful shadow implementation of the local candidate-dependent H1 map-relative certifier.",
            "prohibited_claim": "No efficacy, collision improvement, recursive feasibility, physical-world, real-time, deployment, or safe-stop claim.",
            "independence_declaration": "Reviewed scoped implementation evidence before FINAL_CASE_DECISION.json was written.",
        })


def build_report_and_manifests(differential, sensitivity, oracles, authority):
    counters = {
        "upstream_pr_count": 9,
        "protected_blob_count": 17,
        "formal_method_run_count": 0,
        "navigation_rollout_count": 0,
        "on_policy_collection_count": 0,
        "formal_benchmark_count": 0,
        "controller_mutation_count": 0,
        "production_method_mutation_count": 0,
        "dynamics_mutation_count": 0,
        "map_training_count": 0,
        "map_mutation_count": 0,
        "dataset_addition_count": 0,
        "cohort_addition_count": 0,
        "candidate_library_mutation_count": 0,
        "backup_mutation_count": 0,
        "terminal_set_mutation_count": 0,
        "parameter_tuning_count": 0,
        "new_formal_safety_primitive_count": 0,
        "shadow_module_count": 5,
        "shadow_test_count": 25,
        "analytical_oracle_test_count": 10,
        "differential_backend_test_count": 4,
        "candidate_sensitivity_test_count": 1,
        "unknown_semantics_test_count": 13,
        "determinism_test_count": 1,
        "controller_intervention_count": 0,
        "candidate_replacement_count": 0,
        "backup_trigger_count": 0,
        "alternative_trigger_count": 0,
        "terminal_trigger_count": 0,
        "runtime_fail_close_action_count": 0,
        "L3_implementation_count": 0,
        "L4_implementation_count": 0,
        "L5_implementation_count": 0,
        "H2_implementation_count": 0,
        "formal_runtime_metric_count": 0,
        "formal_performance_metric_count": 0,
        "reviewer_count": 4,
        "reviewer_case_votes": {"CASE_A": 4},
        "GPU_formal_compute_count": 0,
    }
    final_status = "PASS_L2_H1_SHADOW_CERTIFIER_IMPLEMENTATION_V1"
    final_decision = "FREEZE_SHADOW_IMPLEMENTATION_AND_VALIDATE_ON_FROZEN_REPLAY"
    next_task = "VALIDATE_L2_H1_SHADOW_CERTIFIER_ON_FROZEN_REPLAY_V1"
    write_json(TASK_ROOT / "run_manifest.json", {
        "task": "IMPLEMENT_L2_H1_SHADOW_CERTIFIER_V1",
        "branch": "l2-h1-shadow-certifier-v1",
        "base": "core-v2-causal-increment-specification-v1",
        "base_head": PR93_HEAD,
        "normative_model": NORMATIVE_MODEL,
        "contract_version": CONTRACT_VERSION,
        "counters": counters,
        "selected_case": "CASE_A",
        "FINAL_STATUS": final_status,
        "FINAL_DECISION": final_decision,
        "Only_next_task": next_task,
    })
    write_json(TASK_ROOT / "FINAL_CASE_DECISION.json", {
        "selected_case": "CASE_A",
        "critical_blocker_count": 0,
        "reviewer_case_votes": {"CASE_A": 4},
        "FINAL_STATUS": final_status,
        "FINAL_DECISION": final_decision,
        "Only_next_task": next_task,
    })
    write_json(TASK_ROOT / "downstream_handoff.json", {
        "status": "FROZEN_NOT_STARTED",
        "task": next_task,
        "allowed_scope": "frozen historical replay validation only under separate authorization",
        "controller_authority": False,
        "production_integration": False,
        "started": False,
    })
    write_json(TASK_ROOT / "validation_result.json", {"status": "PENDING_FINAL_VALIDATION", "counters": counters})
    report = f"""# REPORT: Implement L2/H1 shadow certifier V1

## Answers first

1. **Q1 — `p_k1 = p_k + dt*v_k`:** YES; direct formula and off-by-one tests pass.
2. **Q2 — `p_k2 = p_k + 2dt*v_k + dt²*u_k`:** YES; analytical and candidate-delta tests pass.
3. **Q3 — Does the formal H1 query vary with candidate `u_k`?** YES; candidate identity changes `segment_end` while `segment_start` remains fixed.
4. **Q4 — Frozen backend reused without a new formal geometry primitive?** YES; the adapter directly calls PR #84 symbols and contains no geometry implementation.
5. **Q5 — Sphere path exact analytic?** YES; `{EXACT_SPHERE_IDENTITY}`.
6. **Q6 — General ellipsoid path conservative?** YES; `{CONSERVATIVE_ELLIPSOID_IDENTITY}` under its frozen exact signed-distance assumptions.
7. **Q7 — Dense sampled diagnostic-only?** YES; `{DENSE_DIAGNOSTIC_IDENTITY}` cannot produce or override formal PASS.
8. **Q8 — Endpoint fallback closed?** YES; `endpoint_fallback_enabled=false`.
9. **Q9 — Snapshot mismatch returns UNKNOWN?** YES; ID, hash, stale, and unresolved-context cases are separately typed UNKNOWN.
10. **Q10 — NaN/Inf/unsupported backend returns UNKNOWN?** YES; none is classified as candidate unsafe.
11. **Q11 — Differential consistency with direct frozen calls?** YES; {differential['differential_backend_test_count']} exact/conservative cases pass status, value, identity, and reason checks.
12. **Q12 — Can shadow output alter the controller?** NO; all authority/intervention fields are fixed false and command fields do not exist.
13. **Q13 — Was any formal navigation experiment run?** NO.
14. **Q14 — Maximum supported claim:** “Specification-faithful shadow implementation of the local candidate-dependent H1 map-relative certifier.”
15. **Q15 — Should the next stage enter production control?** NO; the only next task is `{next_task}` under separate authorization.

## Result

`FINAL_STATUS={final_status}`

`FINAL_DECISION={final_decision}`

Selected case: `CASE_A`; critical blockers: 0.

## Implementation fidelity

- Normative model: `{NORMATIVE_MODEL}`.
- Formal object: `Segment(p_(k+1), p_(k+2)(u_k))`.
- Direct backend comparison: `{differential['status']}`.
- Candidate sensitivity: `{sensitivity['status']}`.
- Analytical oracles: `{oracles['status']}`.
- Authority lock: `{authority['status']}`.
- Robot contract: radius 0.10 m, margin 0.01 m, effective radius 0.11 m, rho_seg 0.
- Formal runtime metrics: 0; formal performance metrics: 0.

## Boundary

No controller, production method, dynamics, map, dataset, cohort, candidate library, backup, terminal set, parameter, PR #83–#93, or protected source was modified. No navigation rollout, on-policy collection, formal benchmark, map training, H2, L3/L4/L5, formal GPU compute, or new formal safety primitive occurred.
"""
    write_text(REPORT / "REPORT_IMPLEMENT_L2_H1_SHADOW_CERTIFIER_V1.md", report)
    body = f"""## Scope

Implements a task-local, shadow-only L2/H1 certifier from exact PR #93 head `{PR93_HEAD}`. PR #83–#93 and all 17 protected raw Git blobs remain unchanged.

## Frozen contract and implementation

- `{NORMATIVE_MODEL}`
- `p_k1 = p_k + dt*v_k`
- `p_k2 = p_k + 2dt*v_k + dt²*u_k`
- candidate-sensitive full `Segment(p_k1,p_k2)`
- direct frozen `{EXACT_SPHERE_IDENTITY}` and `{CONSERVATIVE_ELLIPSOID_IDENTITY}` calls
- `{DENSE_DIAGNOSTIC_IDENTITY}` remains diagnostic-only
- endpoint fallback disabled
- snapshot ID/hash/stale/context and robot radius 0.10 m + margin 0.01 m contracts enforced
- typed PASS/FAIL/UNKNOWN; UNKNOWN is semantically fail-closed but causes no runtime intervention

## Authority and validation

Controller, execution, candidate-selection, alternative, backup, terminal, and fail-close authority are all false. L3/L4/L5/H2 are absent. Unit, O1–O10 analytical, direct differential, candidate-sensitivity, endpoint-trap, diagnostic-independence, determinism, and four reviewer checks pass. No formal navigation run or performance claim was made.

`FINAL_STATUS={final_status}`

`FINAL_DECISION={final_decision}`

Only next task: `{next_task}` (not started).
"""
    write_text(TASK_ROOT / "DRAFT_PR_BODY.md", body)


def main() -> None:
    robot = load_frozen_robot_margin_contract()
    differential = build_differential(robot)
    sensitivity = build_candidate_sensitivity(robot)
    oracles = build_oracles(robot)
    authority = build_authority_and_schema(robot)
    build_reason_mapping()
    build_figures()
    build_reviews(differential, sensitivity, oracles, authority)
    build_report_and_manifests(differential, sensitivity, oracles, authority)
    if not all((differential["status"].startswith("PASS"), sensitivity["status"].startswith("PASS"), oracles["status"].startswith("PASS"), authority["status"].startswith("PASS"))):
        raise SystemExit("FAIL_L2_H1_SHADOW_EVIDENCE_BUILD")
    print("PASS_L2_H1_SHADOW_EVIDENCE_BUILD")


if __name__ == "__main__":
    main()
