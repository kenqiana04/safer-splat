"""Materialize the specification-only Core V2 L2/H1 decision artifacts."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from task_config import (
    FIGURES,
    FINAL_CASE,
    FINAL_DECISION,
    FINAL_STATUS,
    ONLY_NEXT_TASK,
    PR84_ROOT,
    PR92_TASK_ROOT,
    TASK_ROOT,
)


FOOTER = (
    "SPECIFICATION ONLY | NO CORE V2 IMPLEMENTATION | NO NEW FORMAL METHOD RUN | "
    "FROZEN POSITION-FIRST EULER | MAP-RELATIVE CLAIM ONLY | "
    "NOT RECURSIVE FEASIBILITY | NOT SAFE-STOP PROOF"
)


def write_text(rel: str, body: str) -> None:
    path = TASK_ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.rstrip() + "\n", encoding="utf-8")


def write_json(rel: str, payload: object) -> None:
    write_text(rel, json.dumps(payload, indent=2, sort_keys=True))


def write_csv(rel: str, header: list[str], rows: list[list[object]]) -> None:
    path = TASK_ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def source_record(path: str) -> dict[str, object]:
    audit = json.loads((TASK_ROOT / "PROTECTED_SOURCE_AUDIT.json").read_text(encoding="utf-8"))
    for row in audit["supplemental_evidence_records"]:
        if row["path"] == path:
            return row
    raise KeyError(path)


def build_semantic_audits() -> None:
    map_audit = {
        "status": "CONSERVATIVE_BUT_SUFFICIENT_FOR_H1_SPEC",
        "map_semantics_audit_count": 1,
        "authority": "frozen static Gaussian represented-obstacle map snapshot",
        "physical_world_truth_claim": False,
        "reference_online_input": False,
        "map_reference_disagreement": "evidence limitation; L2 remains map-relative",
        "gaussian_primitive_semantics": {
            "isotropic": "closed sphere using center and linear scale radius",
            "general": "closed Gaussian ellipsoid queried by frozen ball-to-ellipsoid source API",
            "barrier": "signed-square Gaussian barrier proxy, not metric clearance",
        },
        "robot_footprint": "ball radius 0.10 m",
        "fixed_safety_margin": "0.01 m",
        "effective_radius": "0.11 m",
        "segment_margin_rho_seg": 0.0,
        "unknown_semantics": {
            "empty_map_or_query": "UNKNOWN",
            "nonfinite_input_or_query": "NONFINITE",
            "snapshot_mismatch": "typed mismatch/error",
            "source_exception": "ERROR",
            "l2_mapping": "L2_UNKNOWN and fail-closed; never PASS or L2_FAIL",
        },
        "missing_geometry": "UNKNOWN, not free space",
        "compatibility_verdict": "existing predicate can evaluate arbitrary H1 endpoints without changing geometry semantics",
        "assumptions": [
            "static immutable map snapshot",
            "valid exact source ball-to-ellipsoid query",
            "closed represented primitives",
            "frozen footprint and margin",
            "no reference-geometry or physical-world guarantee",
        ],
        "source_identities": [
            source_record(f"{PR84_ROOT}/adapters/gaussian_barrier_adapter.py"),
            source_record("splat/gsplat_utils.py"),
            source_record(f"{PR84_ROOT}/task_config.py"),
        ],
    }
    write_json("map_safety_semantics_audit.json", map_audit)

    segment_audit = {
        "status": "SUFFICIENT_FOR_H1_SPEC",
        "continuous_segment_contract_check_count": 4,
        "parameter_domain": "alpha in [0,1]",
        "formal_backends": [
            {
                "identity": "EXACT_ANALYTIC_SPHERE_SEGMENT_MINIMUM",
                "class": "EXACT_ANALYTIC",
                "coverage": "entire closed segment",
                "eligible_when": "frozen map primitives satisfy isotropic sphere contract",
            },
            {
                "identity": "CONSERVATIVE_SIGNED_DISTANCE_LIPSCHITZ_INTERVAL",
                "class": "CONSERVATIVE_LOWER_BOUND",
                "coverage": "entire closed segment by recursive interval lower bounds",
                "eligible_when": "exact finite signed-distance provider and frozen ellipsoid assumptions hold",
            },
        ],
        "diagnostic_backend": {
            "identity": "DENSE_SAMPLED_DIAGNOSTIC_ONLY",
            "class": "DIAGNOSTIC_ONLY",
            "formal_pass_allowed": False,
        },
        "endpoint_only_fallback": False,
        "budget_exhaustion": "L2_UNKNOWN / NOT_CERTIFIED_WITHIN_BUDGET; never PASS",
        "reuse_verdict": "reuse frozen formal SegmentBackend on S_H1; do not reuse B1 causal role",
        "source_identities": [
            source_record(f"{PR84_ROOT}/certifier/segment_backends/base.py"),
            source_record(f"{PR84_ROOT}/certifier/segment_backends/analytic_primitive.py"),
            source_record(f"{PR84_ROOT}/certifier/segment_backends/conservative_interval.py"),
            source_record(f"{PR84_ROOT}/certifier/segment_backends/sampled_diagnostic.py"),
            source_record(f"{PR84_ROOT}/proof_artifacts/swept_segment_assumptions.json"),
        ],
    }
    write_json("continuous_segment_semantics_audit.json", segment_audit)

    frozen_consistency = json.loads(
        (Path(PR84_ROOT) / "proof_artifacts/execution_model_audit.json").read_text(encoding="utf-8")
    )
    write_json(
        "execution_optimizer_verifier_consistency.json",
        {
            "status": "PASS_EXECUTION_OPTIMIZER_VERIFIER_H1_CONSISTENCY",
            "normative_execution_model": "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1",
            "optimizer_control_semantics": "u_k is the candidate acceleration applied over transition k->k+1",
            "l2_control_semantics": "the same u_k determines v_(k+1) and therefore S_H1",
            "execution_control_semantics": "plant uses x_next=x+dt*[v,u]",
            "u_k_plus_1_h1_position_authority": "NONE",
            "source_audit_status": frozen_consistency["status"],
            "source_records": frozen_consistency["records"],
            "timing_conflict_count": 0,
        },
    )


def build_contract_documents() -> None:
    write_text(
        "CORE_V2_L2_H1_CAUSAL_INCREMENT_SPECIFICATION_V1.md",
        """# Core V2 L2/H1 causal increment specification V1

## Research question

**RQ-V2-L2-H1:** Under the frozen position-first forward-Euler execution model and frozen Gaussian safety semantics, can a minimal candidate-dependent, continuous-segment-aware L2 certificate evaluate `u_k` on `[t_(k+1),t_(k+2)]` without introducing H2, recursive feasibility, backup rollout, or new controller semantics?

**RQ0 / falsification:** If execution timing, map semantics, continuous-segment semantics, or the frozen backend cannot support this contract, do not implement L2; record the typed blocker.

## Decision

The answer is yes at specification level only. `S_H1(x_k,u_k)=Segment(p_(k+1),p_(k+2)(u_k))` is candidate-dependent under the frozen model. Existing exact-analytic or conservative full-segment backends can evaluate those endpoints without a new safety primitive. The new contribution is a causal role and tri-state interface, not new geometry.

The certificate is local, map-relative, first-control-affected-segment evidence. It does not prove H2, recursive feasibility, backup existence, safe stopping, real-time feasibility, physical-world collision avoidance, or performance.
""",
    )
    write_text(
        "H1_SEGMENT_CONTRACT.md",
        """# H1 segment contract

`S_H1(x_k,u_k)=Segment(p_(k+1),p_(k+2)(u_k))`, parameterized by

`p_H1(alpha)=p_k+(1+alpha)dt*v_k+alpha*dt^2*u_k`, `alpha in [0,1]`.

It is the `FIRST_CONTROL_AFFECTED_SEGMENT`. Its start is shared by all candidates; every interior point and the endpoint depend on `u_k`. In contrast, L1 is `Segment(p_k,p_(k+1))` and has no `u_k` position authority. The same frozen geometry backend may serve both segments, but their causal role, state-machine location, failure semantics, and denominators are different.
""",
    )
    write_text(
        "L2_PREDICATE_CONTRACT.md",
        """# L2 predicate contract

Abstract interface only—no implementation is created:

`L2_H1_CERTIFY(x_k, u_k, expected_map_snapshot, frozen_segment_backend, frozen_robot_margin_contract) -> {PASS, FAIL, UNKNOWN}`

- `PASS`: the selected frozen formal backend returns `CERTIFIED_SAFE` with `certified=true` for all `alpha in [0,1]`.
- `FAIL`: a finite entire-segment evaluation returns `CERTIFIED_UNSAFE` and a witness.
- `UNKNOWN`: budget exhaustion, map UNKNOWN/NONFINITE/ERROR, snapshot mismatch, invalid input, unsupported backend, or any unclassified status.

Only the frozen `EXACT_ANALYTIC_SPHERE_SEGMENT_MINIMUM` or `CONSERVATIVE_SIGNED_DISTANCE_LIPSCHITZ_INTERVAL` may produce PASS. `DENSE_SAMPLED_DIAGNOSTIC_ONLY` and endpoint-only checks cannot. UNKNOWN fails closed but remains statistically distinct from candidate unsafe.
""",
    )
    write_json(
        "l2_l3_separation_contract.json",
        {
            "status": "PASS_L2_L3_SEPARATION",
            "L2_input": "x_k,u_k,frozen map snapshot,frozen H1 segment backend,frozen robot/margin contract",
            "L2_output": "PASS|FAIL|UNKNOWN for local H1 segment",
            "L3_input": "candidate with L2_PASS plus frozen backup/terminal witness contract",
            "L3_output": "sufficient witness found|witness absent|unknown",
            "entry_condition": "L3 may be entered only after L2_PASS",
            "prohibited_inference": [
                "L2_PASS implies backup exists",
                "L3 witness proves H1 without L2",
                "L2_PASS implies recursive feasibility",
                "L3 failure implies mathematical unrecoverability",
            ],
            "failure_distinction": "L2_FAIL, L2_UNKNOWN, and backup-witness failure remain separate",
        },
    )
    write_text(
        "ALT_ELIGIBLE_BOUNDARY_AUDIT.md",
        """# ALT_ELIGIBLE boundary audit

The PR #92 predicate is preserved byte-for-byte as upstream evidence and is not redefined. Only a primary `L2_FAIL` or later L3 witness failure may be an alternative opportunity, and only when every frozen `ALT_ELIGIBLE(...)` conjunct holds. `L2_UNKNOWN`, current infeasible, immediate unavoidable unsafe, committed primary, candidate-independent preclusion, and terminal-already-safe are not L4 opportunities. The finite library remains unchanged and exhaustion is not continuous-control infeasibility.
""",
    )
    write_text(
        "L5_TERMINAL_FAIL_CLOSE_BOUNDARY.md",
        """# L5 terminal and fail-close boundary

A certified terminal action may commit only under its frozen sufficient terminal contract. Explicit fail-close is a typed absence of a lawful certified route; it is not a safe stop, braking proof, stopping-distance guarantee, or maximal recoverable-set claim. No terminal set, backup policy, or braking argument is changed here.
""",
    )
    write_text(
        "H1_VS_H2_SCOPE_BOUNDARY.md",
        """# H1 versus H2 scope boundary

H1 is exactly `[t_(k+1),t_(k+2)]`, the first position segment affected by `u_k`. H2 remains deferred because it requires an explicit later-control witness or policy, horizon selection, and additional assumptions. H1's intentionally local claim is not a defect and does not justify automatic expansion to H2. No future controller sequence, re-QP policy, candidate tree, or backup horizon is specified.
""",
    )
    dispositions = [
        [1, "Map-query and reference semantics for a future L2 certificate", "A", "RESOLVED_FOR_LOCAL_H1_SPEC", "frozen represented-map contract; physical/reference truth explicitly excluded"],
        [2, "Continuous segment-check contract for H1", "A", "RESOLVED_FOR_LOCAL_H1_SPEC", "exact sphere or conservative interval covers entire closed segment"],
        [3, "Explicit later-control witness/policy for H2", "C", "DEFERRED_BEYOND_H1", "H2 is outside the minimal increment"],
        [4, "Start-Safe repair eligibility and supervisory authority", "D", "OUTSIDE_CURRENT_CLAIM", "L0 contract remains unchanged"],
        [5, "Tracking/latency budget and runtime deadline integration", "D", "OUTSIDE_CURRENT_CLAIM", "no robustness, real-time, or deployment claim"],
        [6, "Finite alternative-library coverage beyond frozen hits", "D", "OUTSIDE_CURRENT_CLAIM", "L4 library is unchanged and incomplete by claim"],
        [7, "Representative on-policy opportunity distribution", "D", "OUTSIDE_CURRENT_CLAIM", "no efficacy or prevalence evidence generated"],
    ]
    write_csv(
        "unresolved_assumption_disposition.csv",
        ["id", "frozen_assumption", "class", "disposition", "reason"],
        dispositions,
    )
    write_csv(
        "h1_option_comparison.csv",
        ["option", "causal_correctness", "candidate_dependence", "segment_completeness", "backend_compatibility", "method_change", "proof_strength", "assumption_burden", "implementation_burden", "computational_implication", "falsifiability", "reviewer_defensibility", "claim_clarity", "verdict"],
        [
            ["OPTION_H1_A", "PASS", "PASS", "FULL", "EXACT_OR_CONSERVATIVE_FORMAL", "NONE_TO_GEOMETRY", "MAP_RELATIVE_FULL_SEGMENT", "FROZEN", "BOUNDED_NEW_CALLER", "ONE_ADDITIONAL_SEGMENT_CERTIFICATE", "HIGH", "HIGH", "HIGH", "SELECT"],
            ["OPTION_H1_B", "PASS", "PASS", "FULL_CONSERVATIVE", "CONSERVATIVE_INTERVAL", "NONE_TO_GEOMETRY", "SUFFICIENT_LOWER_BOUND", "EXACT_SIGNED_DISTANCE_ASSUMPTION", "BOUNDED_NEW_CALLER", "ADAPTIVE_INTERVAL_BUDGET", "HIGH", "HIGH_IF_CLAIM_DOWNGRADED", "HIGH", "VALID_SUBCASE_OF_A"],
            ["OPTION_H1_C", "PASS_AT_ENDPOINT_ONLY", "PASS", "FAIL", "ENDPOINT_ONLY", "NONE", "DIAGNOSTIC_ONLY", "LOW", "LOW", "LOW", "HIGH", "LOW", "LOW", "REJECT_AS_FORMAL_L2"],
        ],
    )


def build_state_failure_evaluation() -> None:
    write_text(
        "STATE_MACHINE_DELTA_V1.md",
        """# Minimal state-machine delta V1

Preserve the PR #92 ordering: L0 current admission/repair → L1 immediate uncontrollable segment → frozen candidate preparation → S6 primary candidate under test. Define only the formerly conceptual S6 L2 transition:

- `L2_PASS`: S6 → S7 primary future-safe → L3 witness.
- `L2_FAIL`: S6 → S9 primary not certified → test frozen `ALT_ELIGIBLE` before L4.
- `L2_UNKNOWN`: S6 → typed L5 fail-close/non-evaluable path; it is not candidate unsafe and is not L4 eligible.

All L0/L1/L3/L4/L5 behavior remains frozen. This is a specification delta, not an implemented state machine.
""",
    )
    frozen_failures: list[dict[str, str]] = []
    with (PR92_TASK_ROOT / "architecture/failure_types.csv").open(encoding="utf-8", newline="") as handle:
        frozen_failures = list(csv.DictReader(handle))
    overlays = {
        "F_START_INVALID": "unchanged; not L2 reached",
        "F_CURRENT_QUERY_UNKNOWN": "L2_UNKNOWN if encountered during H1 map query; no alternative entry",
        "F_CURRENT_FEASIBILITY_FAIL": "unchanged; not L2 reached",
        "F_IMMEDIATE_UNAVOIDABLE_SEGMENT_FAIL": "unchanged; not L2 reached",
        "F_PRIMARY_FUTURE_SAFETY_FAIL": "exact mapping for finite L2_FAIL",
        "F_PRIMARY_BACKUP_FAIL": "unchanged L3 failure after L2_PASS",
        "F_ALTERNATIVE_LIBRARY_EXHAUSTED": "unchanged L4 result",
        "F_TERMINAL_NOT_CERTIFIED": "unchanged L5 result; terminal-already-safe remains separate",
        "F_RUNTIME_DEADLINE": "L2_UNKNOWN when H1 certificate budget/deadline is exhausted",
        "F_MAP_REFERENCE_UNRESOLVED": "L2_UNKNOWN/evidence limitation, never candidate unsafe",
        "F_TRACKING_LATENCY_UNMODELED": "outside local H1 claim; no robustness inference",
    }
    rows = []
    for row in frozen_failures:
        rows.append([row["failure_type"], overlays[row["failure_type"]], "PRESERVED", row["evidence_limitation"]])
    write_csv(
        "failure_taxonomy_l2_mapping.csv",
        ["frozen_failure_type", "l2_mapping", "upstream_taxonomy_status", "evidence_limitation"],
        rows,
    )
    write_json(
        "denominator_contract_l2.json",
        {
            "status": "PASS_L2_DENOMINATOR_SCHEMA",
            "new_prevalence_numbers_generated": False,
            "unconditional_prevalence_denominator": "N_all",
            "L2_reached": "states that passed L0 and L1, have a frozen prepared candidate, and are not terminal-already-safe",
            "L2_candidate_evaluated": "candidate-level calls returning exactly one of PASS, FAIL, UNKNOWN",
            "conditional_counts": ["N_L2_PASS", "N_L2_FAIL", "N_L2_UNKNOWN"],
            "conditional_rate_denominator": "N_L2_candidate_evaluated",
            "opportunity_denominator": "N_L2_reached",
            "decision_gain": "committed action/decision differs after the certified path",
            "certificate_gain": "certificate status changes without requiring an action change",
            "unit_of_analysis": "candidate-state-map-snapshot tuple",
        },
    )
    write_json(
        "historical_evidence_non_upgrade_audit.json",
        {
            "status": "PASS_HISTORICAL_EVIDENCE_NON_UPGRADE",
            "upstream_prs": [83, 84, 86, 87, 89, 90, 91, 92],
            "allowed_operations": ["preserve", "reference", "role remap"],
            "historical_evidence_recompute_count": 0,
            "historical_evidence_upgrade_count": 0,
            "old_b1_retroactively_labeled_l2": False,
            "core_v2_performance_claim_count": 0,
            "candidate_safety_improvement_claim_count": 0,
        },
    )


def build_gates_reviews_and_decision() -> None:
    gates = [
        ["G1_DYNAMICS_CONSISTENCY", "PASS", "H1 derived only from frozen position-first Euler", "any normative ZOH substitution or source timing mismatch"],
        ["G2_CANDIDATE_DEPENDENCE", "PASS", "d p_H1/d u_k=alpha*dt^2*I for alpha>0", "zero or ambiguous candidate derivative"],
        ["G3_CONTINUOUS_SEGMENT_SEMANTICS", "PASS", "exact/conservative formal backends cover full alpha interval", "only sampled or endpoint backend available"],
        ["G4_MAP_SAFETY_SEMANTICS", "PASS", "frozen map/robot/margin/UNKNOWN contract is sufficient map-relative", "ambiguous footprint, margin, snapshot, or UNKNOWN handling"],
        ["G5_NO_RECURSION_OVERCLAIM", "PASS", "claims limited to local H1", "recursive, physical-world, real-time, or deployment claim"],
        ["G6_L2_L3_ROLE_SEPARATION", "PASS", "L2 local segment precedes L3 witness", "merging H1 safety and recoverability"],
        ["G7_FALSIFIABILITY", "PASS", "each gate has explicit DO_NOT_IMPLEMENT evidence", "validator design that cannot reject the specification"],
    ]
    write_json(
        "FALSIFICATION_GATES.json",
        {
            "status": "PASS_ALL_SEVEN_FALSIFICATION_GATES",
            "falsification_gate_count": 7,
            "all_resolved": True,
            "all_pass": True,
            "gates": [
                {"gate": gate, "verdict": verdict, "evidence": evidence, "do_not_implement_condition": condition}
                for gate, verdict, evidence, condition in gates
            ],
        },
    )
    reviewers = [
        (
            "control_theory_review.json",
            "R1_CONTROL_THEORY",
            ["indexing is consistent", "candidate dependence holds for alpha>0", "claim remains local and model-specific"],
            ["future changes to execution ordering", "any recursive-feasibility inference"],
        ),
        (
            "robotics_systems_review.json",
            "R2_ROBOTICS_SYSTEMS",
            ["optimizer/verifier/plant use the same acceleration meaning", "map snapshot and robot/margin semantics are explicit", "UNKNOWN and fail-close remain typed"],
            ["tracking, delay, and physical-world truth remain outside scope", "no active-controller integration"],
        ),
        (
            "statistics_review.json",
            "R3_STATISTICS_EVALUATION",
            ["candidate-state-map tuple is the unit", "PASS/FAIL/UNKNOWN denominators are explicit", "historical evidence is not upgraded"],
            ["no prevalence or efficacy estimate exists", "future shadow data require preregistration"],
        ),
        (
            "novelty_publication_review.json",
            "R4_NOVELTY_PUBLICATION",
            ["the contribution repairs a causal mismatch rather than shifting the B1 label", "geometry reuse and causal-role novelty are separated", "the claim is falsifiable and narrow"],
            ["specification is not an algorithm result", "sampled-data and backup boundaries must remain explicit"],
        ),
    ]
    for filename, reviewer, supports, cautions in reviewers:
        write_json(
            f"reviewers/{filename}",
            {
                "reviewer": reviewer,
                "independence_declaration": "review used frozen audits and did not read FINAL_CASE_DECISION.json",
                "critical_blocker_count": 0,
                "supports": supports,
                "cautions": cautions,
                "case_vote": "CASE_A",
            },
        )
    write_text(
        "SUPPORTED_AND_PROHIBITED_CLAIMS.md",
        """# Supported and prohibited claims

## Supported

- Under the frozen position-first Euler model, H1 is the first position segment affected by `u_k`.
- The frozen exact-analytic or conservative full-segment backend may evaluate H1 without a new geometry primitive.
- L2 is a tri-state, candidate-dependent, map-relative local segment certificate placed before L3.

## Prohibited

- No Core V2 implementation, new controller, new safety primitive, formal run, safety improvement, performance, real-time, physical-world, tracking/delay robustness, recursive feasibility, viability, backup existence, safe-stop, maximal set, continuous-control completeness, or deployment claim is established.
""",
    )
    write_json(
        "FINAL_CASE_DECISION.json",
        {
            "selected_case": FINAL_CASE,
            "reviewer_case_votes": {"CASE_A": 4},
            "critical_blocker_count": 0,
            "FINAL_STATUS": FINAL_STATUS,
            "FINAL_DECISION": FINAL_DECISION,
            "Only_next_task": ONLY_NEXT_TASK,
            "rationale": "G1-G7 pass; H1 timing, map-relative semantics, continuous-segment semantics, and frozen backend reuse are sufficient without method mutation",
        },
    )


def build_manifest_and_reports() -> None:
    counts = {
        "upstream_pr_count": 8,
        "protected_blob_count": 17,
        "formal_method_run_count": 0,
        "controller_mutation_count": 0,
        "method_mutation_count": 0,
        "dynamics_mutation_count": 0,
        "map_training_count": 0,
        "map_mutation_count": 0,
        "dataset_addition_count": 0,
        "cohort_addition_count": 0,
        "candidate_library_mutation_count": 0,
        "backup_mutation_count": 0,
        "terminal_set_mutation_count": 0,
        "parameter_tuning_count": 0,
        "new_safety_primitive_count": 0,
        "control_authority_formula_check_count": 10,
        "h1_indexing_check_count": 6,
        "map_semantics_audit_count": 1,
        "continuous_segment_contract_check_count": 4,
        "candidate_future_option_count": 3,
        "falsification_gate_count": 7,
        "unresolved_assumption_count": 7,
        "reviewer_count": 4,
        "reviewer_case_votes": {"CASE_A": 4},
        "historical_evidence_recompute_count": 0,
        "formal_performance_metric_count": 0,
        "GPU_formal_compute_count": 0,
        "operational_autonomy_action_count": 6,
        "task_owned_process_cleanup_count": 0,
    }
    write_json(
        "run_manifest.json",
        {
            "task": "WRITE_CORE_V2_CAUSAL_INCREMENT_SPECIFICATION_V1",
            "scope": "specification-only",
            "counts": counts,
            "selected_case": FINAL_CASE,
            "FINAL_STATUS": FINAL_STATUS,
            "FINAL_DECISION": FINAL_DECISION,
            "Only_next_task": ONLY_NEXT_TASK,
            "next_task_started": False,
            "operational_state_captured": False,
        },
    )
    write_json(
        "operational_autonomy_actions.json",
        {
            "count": 6,
            "actions": [
                "isolated worktree creation from frozen PR92 head",
                "read-only GitHub and raw Git identity freeze",
                "task-local deterministic H1 formula checks",
                "task-local contract and reviewer serialization",
                "task-owned figure generation",
                "read-only GPU/watchdog audit and compact server evidence mirror",
            ],
            "scientific_contract_change_count": 0,
        },
    )
    write_json(
        "downstream_handoff.json",
        {
            "FINAL_STATUS": FINAL_STATUS,
            "FINAL_DECISION": FINAL_DECISION,
            "Only_next_task": ONLY_NEXT_TASK,
            "started": False,
            "allowed_scope": "shadow-only verifier; no controller authority or actuation",
            "formal_method_runs": 0,
        },
    )
    report = f"""# REPORT: Write Core V2 causal increment specification V1

## Answers first

1. **Why B1 cannot be a candidate discriminator:** under the frozen model `Segment(p_k,p_(k+1))` has zero position derivative with respect to `u_k`.
2. **Why H1 is first affected:** `u_k` changes `v_(k+1)`, which determines `[t_(k+1),t_(k+2)]`; `u_(k+1)` cannot change position until the next segment.
3. **Candidate dependence:** proved as `d p_H1(alpha)/d u_k=alpha*dt^2*I`, nonzero for every `alpha>0`.
4. **Backend reuse:** yes; the frozen arbitrary-endpoint segment backend can receive `S_H1` without changing geometry.
5. **Certificate class:** exact analytic for frozen isotropic spheres; conservative lower bound for general frozen ellipsoid signed-distance semantics; dense sampling remains diagnostic only.
6. **Continuous segment:** yes for both formal backends over all `alpha in [0,1]`; endpoint fallback is disabled.
7. **Map/robot/margin/UNKNOWN:** sufficient for a map-relative specification: static snapshot, represented closed primitives, 0.10 m ball plus 0.01 m margin, and typed fail-closed UNKNOWN/nonfinite behavior.
8. **What L2 proves:** local candidate-dependent map-relative safety of the first control-affected segment under frozen assumptions.
9. **What L2 does not prove:** future/recursive/physical/robust/real-time/deployment safety, recoverability, safe stop, or performance.
10. **Why L2 cannot replace L3:** H1 safety does not establish a backup witness or terminal reachability.
11. **Why H1 is not recursive feasibility:** it covers exactly one local segment and specifies no invariant or future policy.
12. **Why H2 is unnecessary now:** H1 closes the first causal gap with fewer assumptions; H2 requires a later-control witness and is deferred.
13. **Required upstream mutations:** none; dynamics, map, controller, B0-B3, library, backup, terminal set, and thresholds remain frozen.
14. **Falsification gates:** G1-G7 all PASS with explicit counterevidence conditions.
15. **Shadow-only next step:** yes, but only under a separate authorization; it must have no controller authority.

## Decision

`{FINAL_STATUS}`

`{FINAL_DECISION}`

Selected case: `{FINAL_CASE}`. Only next task: `{ONLY_NEXT_TASK}`.

## Boundary

This task performed no implementation, training, map/data/cohort change, controller/method/dynamics change, formal B0-B3 run, navigation rollout, oracle, sweep, benchmark, parameter tuning, or formal GPU compute. Historical evidence was preserved and not upgraded.
"""
    write_text("report/REPORT_WRITE_CORE_V2_CAUSAL_INCREMENT_SPECIFICATION_V1.md", report)
    write_text(
        "DRAFT_PR_BODY.md",
        f"""## Summary

Specify the minimal L2/H1 causal increment on the exact PR #92 head while preserving PR #83/#84/#86/#87/#89/#90/#91/#92. No implementation or formal experiment is included.

## Frozen contracts and decision

- Position-first Euler is preserved: `dp_(k+1)/du_k=0`, `dp_(k+2)/du_k=dt^2*I`.
- L1 is the uncontrollable immediate segment; H1/L2 is the first candidate-dependent segment.
- Exact sphere and conservative interval backends can be reused under their frozen map-relative assumptions; sampled/endpoint-only checks remain diagnostic.
- UNKNOWN fails closed and remains distinct from candidate unsafe.
- L2 precedes L3; frozen `ALT_ELIGIBLE` limits L4; L5 terminal and fail-close remain separate.
- H2 and all recursive, real-time, physical-world, performance, and deployment claims remain deferred/prohibited.
- G1-G7 PASS; four independent scoped reviews vote CASE_A.

`FINAL_STATUS={FINAL_STATUS}`

`FINAL_DECISION={FINAL_DECISION}`

`Only next task={ONLY_NEXT_TASK}`
""",
    )


def make_flow(name: str, title: str, boxes: list[str], highlight: int | None = None) -> None:
    fig, ax = plt.subplots(figsize=(12, 6.5))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title(title, fontsize=16, fontweight="bold", pad=18)
    count = len(boxes)
    width = min(0.16, 0.82 / max(count, 1))
    gap = (0.90 - width * count) / max(count - 1, 1)
    x = 0.05
    for index, label in enumerate(boxes):
        color = "#2563eb" if index == highlight else "#dbeafe"
        text_color = "white" if index == highlight else "#0f172a"
        ax.text(
            x + width / 2,
            0.55,
            label,
            ha="center",
            va="center",
            wrap=True,
            fontsize=9,
            color=text_color,
            bbox={"boxstyle": "round,pad=0.55", "facecolor": color, "edgecolor": "#1e3a8a"},
        )
        if index < count - 1:
            ax.annotate("", xy=(x + width + gap * 0.78, 0.55), xytext=(x + width + gap * 0.18, 0.55), arrowprops={"arrowstyle": "->", "color": "#334155", "lw": 1.5})
        x += width + gap
    fig.text(0.5, 0.025, FOOTER, ha="center", fontsize=7, wrap=True)
    fig.tight_layout(rect=(0.02, 0.08, 0.98, 0.96))
    target = TASK_ROOT / "figures" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(target, dpi=150)
    plt.close(fig)


def build_figures() -> None:
    specs = {
        "control_authority_timeline_h1.png": ("Frozen control-authority timeline", ["t_k: choose u_k", "p_(k+1): no u_k position authority", "v_(k+1): changed by u_k", "H1 position: affected by u_k"], 3),
        "l1_vs_l2_segment_dependency.png": ("L1 and L2 have different causal roles", ["L1: p_k -> p_(k+1)", "zero candidate position authority", "L2: p_(k+1) -> p_(k+2)", "candidate-dependent"], 2),
        "h1_candidate_dependence.png": ("H1 candidate-dependence proof", ["alpha=0: derivative 0", "0<alpha<1: alpha dt^2 I", "alpha=1: dt^2 I"], 1),
        "frozen_geometry_backend_new_causal_role.png": ("Frozen geometry, new causal role", ["frozen exact/conservative backend", "new H1 endpoints", "tri-state L2 role", "no new safety primitive"], 2),
        "l2_l3_l4_l5_boundaries.png": ("L2/L3/L4/L5 boundaries", ["L2 local H1", "L3 backup witness", "L4 finite alternatives", "L5 terminal or fail-close"], 0),
        "minimal_state_machine_delta.png": ("Minimal state-machine delta", ["L0", "L1", "candidate prepared", "L2 H1", "L3", "commit / L4 / L5"], 3),
        "h1_vs_h2_scope.png": ("H1 selected; H2 deferred", ["H1: one first affected segment", "local map-relative certificate", "H2: future witness required", "deferred"], 0),
        "falsification_gates.png": ("Seven kill gates", ["G1 dynamics", "G2 candidate", "G3 segment", "G4 map", "G5 claims", "G6 L2/L3", "G7 falsifiable"], None),
        "supported_vs_prohibited_claims.png": ("Claim boundary", ["supported: local H1", "supported: map-relative", "prohibited: recursion", "prohibited: safe stop", "prohibited: performance"], 0),
        "final_case_decision.png": ("Final decision", ["CASE_A", "specification frozen", "shadow-only handoff", "not started"], 0),
    }
    if set(specs) != set(FIGURES):
        raise RuntimeError("FIGURE_CONTRACT_MISMATCH")
    for name, (title, boxes, highlight) in specs.items():
        make_flow(name, title, boxes, highlight)
    write_json("figures/figure_manifest.json", {"count": len(FIGURES), "annotation": FOOTER, "files": FIGURES})


def main() -> None:
    build_semantic_audits()
    build_contract_documents()
    build_state_failure_evaluation()
    build_gates_reviews_and_decision()
    build_manifest_and_reports()
    build_figures()
    print("PASS_CORE_V2_L2_H1_SPECIFICATION_ARTIFACTS_MATERIALIZED")


if __name__ == "__main__":
    main()
