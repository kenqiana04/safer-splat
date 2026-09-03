#!/usr/bin/env python3
"""Deterministically build the design-only Phase-1 oracle freeze artifacts."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASE = "5595e56b756291881fb9f6f17ba3d7551263574f"


def write_json(name: str, obj: object) -> None:
    (OUT / name).write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_md(name: str, text: str) -> None:
    (OUT / name).write_text(text.strip() + "\n", encoding="utf-8")


def git(*args: str, binary: bool = False):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=not binary)


def identity(path: str) -> dict:
    row = git("ls-tree", BASE, "--", path).strip().split()
    if len(row) < 3:
        raise RuntimeError(f"missing frozen input: {path}")
    mode, kind, blob = row[:3]
    raw = git("cat-file", "blob", blob, binary=True)
    return {
        "path": path,
        "mode": mode,
        "object_type": kind,
        "git_blob_sha1": blob,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size": len(raw),
    }


UPSTREAM_PRS = {
    "107": "a60665f3e29085cc18f1ee03828198074f52e4f0",
    "108": "f04a2077c4f483f20696bb5515c576cd75ddf449",
    "109": "729b3c78a81f2f3ca8948916b64dcb6e2c50fc66",
    "110": "52467acd2ab82c300a8f6c3ce712ab0d59d4f4cf",
    "111": "a658c858995d76a4baa1ad119701e2706df075be",
    "112": "8b47c5c9af05bbb022af4a964a6c8989231bc1bc",
    "113": BASE,
}

INPUTS = [
    "run.py",
    "reproduction/specification/cross_layer_geometry_authority_v2/CROSS_LAYER_GEOMETRY_AUTHORITY_V2.json",
    "reproduction/specification/control_authority_v2/SELECTED_CONTROL_ACTUATOR_CONTRACT_V2.json",
    "reproduction/specification/runtime_assurance_deadline_authority_v2/NONCLAIMS.md",
    "reproduction/specification/backup_token_runtime_schema_v2/BACKUP_TOKEN_RUNTIME_STATE_V2.json",
    "reproduction/specification/backup_token_runtime_schema_v2/TERMINAL_REFERENCE_BOUNDARY_V2.md",
    "reproduction/specification/terminal_emergency_policy_v2/FAIL_CLOSE_TERMINOLOGY_V2.json",
    "reproduction/specification/terminal_emergency_policy_v2/TERMINAL_SAFETY_LIVENESS_BOUNDARY_V2.md",
    "reproduction/specification/terminal_emergency_policy_v2/TERMINAL_EMERGENCY_POLICY_CONTRACT_V2.json",
    "reproduction/specification/terminal_emergency_policy_v2/UPDATED_PREIMPLEMENTATION_BLOCKER_REGISTER_V5.json",
    "reproduction/specification/terminal_emergency_policy_v2/UPDATED_PREIMPLEMENTATION_DEPENDENCY_DAG_V5.json",
    "work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py",
    "work/risk_aware_cbf/scripts/run_v4b_corrective_dt_filter.py",
    "reproduction/cross_dataset/replica_bounded_direct_goal_gt_gaussian_map_v1/replica_mesh_collision_oracle_contract.json",
    "reproduction/cross_dataset/replica_gt_executable_safety_method_matrix_v1/input_freeze/reference_mesh_identity.json",
]

write_json(
    "INDEPENDENT_EVALUATION_ORACLE_INPUT_LOCK.json",
    {
        "schema_version": "INDEPENDENT_EVALUATION_ORACLE_INPUT_LOCK_V2",
        "repository": "kenqiana04/safer-splat",
        "direct_upstream": {
            "pr": 113,
            "state": "OPEN",
            "draft": True,
            "branch": "freeze-terminal-emergency-policy-v2",
            "base_branch": "freeze-backup-token-runtime-schema-v2",
            "head": BASE,
            "base_head": "8b47c5c9af05bbb022af4a964a6c8989231bc1bc",
        },
        "preserved_upstream_pr_heads": UPSTREAM_PRS,
        "frozen_inputs": [identity(p) for p in INPUTS],
        "scope": "SPECIFICATION_STATIC_VALIDATION_ONLY",
        "outcome_data_read_count": 0,
        "trial_execution_count": 0,
        "gpu_execution_count": 0,
        "runtime_implementation_count": 0,
    },
)

write_json(
    "EVALUATION_ORACLE_AUTHORITY_V2.json",
    {
        "schema_version": "EVALUATION_ORACLE_AUTHORITY_V2",
        "unique_owner": "POSTHOC_EVALUATION_ORACLE",
        "execution_time": "AFTER_TRIAL_OR_AFTER_IMMUTABLE_TRACE_LOCK",
        "read_only": True,
        "ORACLE_FEEDBACK_AUTHORITY": False,
        "candidate_generation_authority": False,
        "selection_authority": False,
        "terminal_authority": False,
        "backup_authority": False,
        "controller_state_mutation_authority": False,
        "adaptive_threshold_authority": False,
        "allowed_inputs": [
            "IMMUTABLE_EXECUTED_TRACE",
            "FROZEN_SCENE_REFERENCE_AUTHORITY",
            "PRE_REGISTERED_EVALUATION_CONTRACT",
            "OPTIONAL_SCENE_MATCHED_EXTERNAL_GT_REFERENCE",
        ],
        "diagnostic_only_inputs": ["C0_STATUS", "L1_STATUS", "L2_STATUS", "L3_STATUS", "CBF_FEASIBILITY", "RUNTIME_INTERNAL_H", "CANDIDATE_RANKING_SCORE"],
        "primary_outcome_prohibited_inputs": ["CERTIFICATE_STATUS", "METHOD_INTERNAL_H", "METHOD_MARGIN_AS_COLLISION_RADIUS"],
    },
)

write_json(
    "EVALUATION_CLAIM_TIERS_V2.json",
    {
        "schema_version": "EVALUATION_CLAIM_TIERS_V2",
        "tiers": {
            "TIER_D_METHOD_INTERNAL_DIAGNOSTIC": {"sources": ["C0", "L1", "L2", "L3", "SUPERVISOR"], "supports": ["mechanism_analysis", "reachability", "routing_statistics"], "does_not_support": ["independent_collision_efficacy", "physical_safe_stop", "real_world_safety"]},
            "TIER_C_EXECUTION_TRACE_FACT": {"sources": ["immutable_committed_executed_trace"], "supports": ["action_source_rate", "backup_activation", "terminal_selection", "assurance_boundary_incidence", "runtime_event_facts"]},
            "TIER_B_INDEPENDENT_REPRESENTED_MAP_OUTCOME": {"sources": ["posthoc_recomputation_against_frozen_represented_map"], "scope_label": "REPRESENTED_MAP_RELATIVE", "supports": ["represented_map_collision_proxy", "represented_map_minimum_clearance", "certification_margin_violation"], "does_not_support": ["physical_collision_truth"]},
            "TIER_A_EXTERNAL_GROUND_TRUTH_OUTCOME": {"requires": ["scene_matched_external_geometry_or_simulator_reference", "independence_from_method_map_and_certifier"], "supports": ["scope_specific_external_GT_collision_outcome"]},
        },
    },
)

trial_fields = ["experiment_protocol_id", "trial_id", "scene_id", "start_state_id", "goal_state_id", "method_variant_id", "map_authority_id", "geometry_contract_id", "actuator_contract_id", "dynamics_timebase_id", "deadline_contract_id", "terminal_policy_id", "oracle_contract_id"]
step_fields = ["cycle_index_k", "simulation_time", "x_k", "x_k_hash", "selected_action_id", "selected_action_vector", "executed_action_id", "executed_action_vector", "action_role", "action_committed", "x_k1", "x_k1_hash", "solver_timing", "certification_timing", "deadline_state", "retained_backup_state", "terminal_lifecycle_state", "software_fail_close_event"]
write_json(
    "EVALUATION_TRACE_SCHEMA_V2.json",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "Immutable V2 evaluation trace",
        "type": "object",
        "required": ["trial", "steps", "trace_lock"],
        "properties": {
            "trial": {"type": "object", "required": trial_fields},
            "steps": {"type": "array", "items": {"type": "object", "required": step_fields, "properties": {"action_role": {"enum": ["PRIMARY_NAVIGATION", "ALTERNATIVE_NAVIGATION", "RETAINED_BACKUP", "TERMINAL", "NO_METHOD_ACTION", "ASSURANCE_BOUNDARY"]}}}},
            "trace_lock": {"type": "object", "required": ["sha256", "schema_sha256", "locked_before_evaluation"]},
        },
        "oracle_must_reject": ["missing_committed_transition", "nonfinite_state", "identity_mismatch", "mutable_trace"],
    },
)

write_md(
    "EVALUATION_TRACE_INTEGRITY_CONTRACT_V2.md",
    """
# Evaluation Trace Integrity Contract V2

The future oracle consumes only a content-addressed, immutable trace locked before evaluation. Every committed transition binds `x_k`, selected and executed action identities/vectors, action role, and exact `x_(k+1)` under one cycle index. Trial, map, geometry, actuator, dynamics/timebase, deadline, terminal-policy, and oracle identities are mandatory.

The oracle rejects missing committed transitions, sequence gaps, nonfinite states, hash mismatches, mutable references, or a selected/executed mismatch without an explicit actuator-authority explanation. Missing timing may make timing UNKNOWN without necessarily invalidating geometry, but missing state/action geometry makes the affected outcome `EVAL_UNKNOWN`; it is never silently SAFE.
""",
)

write_md(
    "LEGACY_EVALUATION_SEMANTICS_AUDIT_V2.md",
    """
# Legacy Evaluation Semantics Audit V2

Static evidence at PR #113 head:

- **EVAL-A:** `run.py:145-161` propagates the selected action, then calls `gsplat.query_distance(x, radius=radius, distance_type='ball-to-ellipsoid')` and records `min(h)`. It uses the represented Gaussian map/query family also used by the method. This is a method-map-relative endpoint diagnostic, not an independent final collision oracle.
- **EVAL-B:** `run.py:163-178` records explicit goal success only when the stalled pre-propagation 6-D state satisfies `||x_ - goal||_2 < 0.001`, but separately labels a moving timeout as success. V2 bans timeout-only goal success.
- **EVAL-C:** the legacy safety log checks post-step points only; it does not certify every closed executed segment. It can miss between-endpoint penetration and is not the V2 swept oracle.

Verdict: `LEGACY_RUN_PY_NOT_AUTHORIZED_AS_FINAL_V2_EVALUATION_ORACLE`. Historical outputs retain their historical meaning and are not rewritten.
""",
)

write_md(
    "COLLISION_VS_MARGIN_ORACLE_V2.md",
    """
# Collision versus Certification-Margin Oracle V2

Two outcomes are frozen and never merged:

1. `REPRESENTED_MAP_COLLISION_PROXY`: evaluate each closed, actually executed position segment against the frozen represented Gaussian obstacle reference using operational footprint radius **0.015 m** and no certification margin. Report per-segment minimum clearance, trial minimum clearance, penetration indicator, first violating cycle, and violating-segment count.
2. `CERTIFICATION_MARGIN_VIOLATION`: use effective certification radius **0.025 m = 0.015 m + 0.010 m**. This measures loss of reserved certification margin and must not be named physical collision.

The final collision proxy is swept-segment, posthoc, represented-map-relative, identical across compared variants, and independent of internal certificate PASS/FAIL. Endpoints alone are insufficient. Safety and task progress remain separate; no composite score is defined.
""",
)

write_md(
    "REPRESENTED_MAP_ORACLE_INDEPENDENCE_CONTRACT_V2.md",
    """
# Represented-Map Oracle Independence Contract V2

The future evaluator is a task-local posthoc code path with a separate code hash. It consumes the frozen map authority and immutable executed trace but imports no Supervisor, C0, L1, L2, or L3 decision object and never reads their status to decide collision. A deterministic read-only map loader or pure geometry primitive may be shared only under the label `ALGORITHM_INDEPENDENT_DECISION_PATH_WITH_SHARED_GEOMETRIC_PRIMITIVE`.

Outcome thresholds are frozen before active outcomes. Oracle output cannot flow to runtime, alter a candidate, mutate controller state, choose a terminal action, or change future thresholds. This supports Tier-B represented-map-relative claims, not independent physical ground truth.
""",
)

write_json(
    "EXTERNAL_GROUND_TRUTH_ORACLE_AUDIT_V2.json",
    {
        "schema_version": "EXTERNAL_GROUND_TRUTH_ORACLE_AUDIT_V2",
        "repository_static_audit_only": True,
        "download_count": 0,
        "findings": [
            {"scope": "REPLICA_APARTMENT_0", "status": "AVAILABLE_FOR_SCENE_SCOPED_PROTOCOL_ONLY", "authority": "official Replica apartment_0 visual mesh", "mesh_sha256": "274677d9b7caa413230363b68f4aa472e5cc1afe87e422a489fa1b7d844c6182", "query": "continuous segment-to-mesh distance", "robot_radius_m_in_historical_replica_contract": 0.1, "not_automatically_transferable_to_v2": True},
            {"scope": "CURRENT_STONEHENGE_OFFICIAL100_MAINLINE", "status": "UNAVAILABLE_IN_CURRENT_REPOSITORY", "reason": "No scene-matched external mesh/simulator/physical reference independent of the represented Gaussian control map was identified."},
        ],
        "EXTERNAL_GT_COLLISION_ORACLE": "UNAVAILABLE_FOR_CURRENT_STONEHENGE_MAINLINE",
        "physical_collision_claim_authorized": False,
        "represented_map_collision_proxy_claim_authorized_if_tier_b_valid": True,
        "cross_scene_substitution_forbidden": True,
    },
)

write_json(
    "GOAL_COMPLETION_ORACLE_V2.json",
    {
        "schema_version": "GOAL_COMPLETION_ORACLE_V2",
        "authority": "PRE_EXISTING_RUN_PY_EXPLICIT_GOAL_PREDICATE",
        "source": {"path": "run.py", "lines": [163, 168], "head": BASE},
        "state_components": "six-dimensional double-integrator state: position_xyz and velocity_xyz",
        "goal_components": "goal_position_xyz concatenated with zero_velocity_xyz",
        "norm": "Euclidean L2 norm",
        "predicate": "norm_2(x_k - goal_6d) < 0.001",
        "tolerance": 0.001,
        "units": "mixed state norm inherited from historical benchmark contract",
        "posthoc_application": "evaluate exact immutable executed states; threshold fixed before V2 outcomes",
        "typed_outcomes": ["GOAL_REACHED", "TIMEOUT_NOT_GOAL_REACHED", "STALLED_NOT_GOAL_REACHED", "ASSURANCE_BOUNDARY_NOT_GOAL_REACHED", "EVAL_UNKNOWN"],
        "timeout_alone_is_success": False,
    },
)

write_json(
    "PROGRESS_ORACLE_V2.json",
    {
        "schema_version": "PROGRESS_ORACLE_V2",
        "authority": "HISTORICAL_COMPARISON_FORMULA_CONTENT_ADDRESSED_AND_REUSED",
        "sources": ["work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py:1185-1191", "work/risk_aware_cbf/scripts/run_v4b_corrective_dt_filter.py:748-751"],
        "formula": "normalized_progress = (d_start - d_final) / d_start",
        "distance": "Euclidean L2 distance over position_xyz, consistent with the task position component of the goal contract",
        "normalization": "d_start",
        "clipping": "NONE",
        "negative_progress": "RETAIN_NEGATIVE_VALUE",
        "goal_reached": "report formula value and goal_reached separately; do not overwrite progress",
        "zero_initial_distance": "EVAL_UNKNOWN_INVALID_TRIAL_IDENTITY",
        "outcome_adaptation": False,
    },
)

metrics = {
    "safety": ["represented_map_collision_proxy_trial", "represented_map_collision_proxy_segment_count", "min_represented_map_clearance_m", "certification_margin_violation_trial", "min_certification_margin_clearance_m"],
    "liveness_task": ["goal_reached", "normalized_progress", "steps_executed", "timeout", "stall_if_future_preexisting_definition_available"],
    "runtime_assurance": ["primary_navigation_commit_count_rate", "alternative_navigation_commit_count_rate", "retained_backup_activation_count_rate", "terminal_commit_count_rate", "assurance_boundary_count_rate", "no_method_action_count"],
    "diagnostic_non_primary": ["C0_reject_rate", "L1_L2_L3_status_distributions", "alternative_attempts", "backup_invalidation_reasons", "terminal_certificate_readiness"],
    "computation_observations": ["per_step_method_compute_duration", "certificate_stage_duration_if_instrumented", "supervisor_arbitration_duration_if_instrumented", "episode_wall_and_sim_compute_observation"],
}
write_json("EVALUATION_METRIC_REGISTRY_V2.json", {"schema_version": "EVALUATION_METRIC_REGISTRY_V2", "metric_families": metrics, "composite_score": None, "safety_liveness_separated": True, "frozen_before_active_outcomes": True})

write_md(
    "RUNTIME_TIMING_EVALUATION_ORACLE_V2.md",
    """
# Runtime Timing Evaluation Oracle V2

Timing is an observation, not a real-time guarantee. Future implementation must use a declared monotonic clock and fixed start/end boundaries for whole-cycle, certificate-stage, and supervisor-arbitration measurements. Missing timing is typed UNKNOWN and cannot be imputed from successful trials.

Until a numerical deadline authority is separately instantiated and frozen, the only valid result is `DEADLINE_NUMERIC_COMPLIANCE_NOT_YET_EVALUABLE`. Observing runtime below `dt` does not establish hard real-time safety, hardware latency bounds, deployment readiness, or computational superiority.
""",
)

write_json(
    "ACTION_ROLE_OUTCOME_ORACLE_V2.json",
    {
        "schema_version": "ACTION_ROLE_OUTCOME_ORACLE_V2",
        "source": "exact selected/executed action role identity in immutable trace",
        "roles": ["PRIMARY_NAVIGATION", "ALTERNATIVE_NAVIGATION", "RETAINED_BACKUP", "TERMINAL", "ASSURANCE_BOUNDARY", "NO_METHOD_ACTION"],
        "zero_vector_heuristic_forbidden": True,
        "terminal_commit_requires": ["action_role_TERMINAL", "terminal_exact_certificate_identity", "supervisor_selection_identity", "executed_action_identity"],
        "software_break_is_terminal_commit": False,
        "terminal_ready_without_commit_is_terminal_commit": False,
        "backup_and_alternative_counts_separate": True,
    },
)

write_md(
    "SAFE_STOP_EVALUATION_BOUNDARY_V2.md",
    """
# Safe-Stop Evaluation Boundary V2

`SOFTWARE_FAIL_CLOSE != PHYSICAL_SAFE_STOP`. The oracle may count software fail-close events, assurance boundaries, and certified terminal commits from immutable role/evidence chains. It may not count physical safe stops or emergency-stop success without an independent execution/physical oracle. A software break, zero vector, backup exhaustion, or terminal READY state without an executed terminal commit is not physical safe-stop evidence.
""",
)

trial_outcome_fields = ["trial_id", "variant_id", "start_state_id", "goal_state_id", "trace_sha256", "oracle_version", "oracle_sha256", "represented_map_collision_proxy", "collision_first_step", "min_operational_footprint_clearance_m", "certification_margin_violation", "min_certification_margin_clearance_m", "goal_reached", "normalized_progress", "steps", "timeout", "final_action_role", "action_role_commit_counts", "assurance_boundary_count", "software_fail_close_count", "runtime_observations", "evaluation_unknown_flags", "external_gt_availability"]
write_json("TRIAL_OUTCOME_SCHEMA_V2.json", {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "V2 trial outcome", "type": "object", "required": trial_outcome_fields, "unknown_values_are_not_pass": True, "raw_null_is_forbidden_for_required_outcome": True})

write_json(
    "EVALUATION_UNKNOWN_POLICY_V2.json",
    {
        "schema_version": "EVALUATION_UNKNOWN_POLICY_V2",
        "states": ["EVAL_PASS", "EVAL_VIOLATION", "EVAL_UNKNOWN"],
        "unknown_reasons": ["TRACE_INCOMPLETE", "REFERENCE_MAP_UNRESOLVED", "ORACLE_BACKEND_FAILURE", "NONFINITE_STATE", "IDENTITY_MISMATCH", "EXTERNAL_GT_UNAVAILABLE"],
        "EVAL_UNKNOWN_IS_SAFE": False,
        "unknown_trials_retained_in_accounting": True,
        "tier_scoped_missingness": True,
        "timing_unknown_does_not_automatically_invalidate_geometry": True,
    },
)

write_md(
    "STATISTICAL_AGGREGATION_CONTRACT_V2.md",
    """
# Statistical Aggregation Contract V2

- The trial is the primary independent statistical unit; steps and segments are nested diagnostics, never iid replicates.
- Variants use identical trial IDs/start-goal pairs and are compared pairwise.
- Report raw, evaluable, and typed-UNKNOWN trial counts. Binary outcomes report count/rate and paired difference; continuous outcomes report trial-level distributions and paired differences.
- Runtime may have per-step descriptive summaries, but formal comparison remains trial-level and never averages only successful trials.
- Metric, subset, denominator, bootstrap/CI rule, and thresholds must be frozen before active collection. This specification invents no p-value cutoff and permits no outcome-conditioned selection.
""",
)

write_md(
    "VARIANT_COMPARABILITY_CONTRACT_V2.md",
    """
# Variant Comparability Contract V2

Comparable baseline/V2 trials share scene/reference identity, trial/start/goal identities, scientific dt/dynamics, nominal task input unless explicitly variant-defining, oracle version, operational collision footprint (0.015 m), goal oracle, and progress oracle. Method certification geometry or margin may differ, but the collision oracle radius must not follow those margins. Scene, trace, oracle, or operational-footprint mismatch invalidates paired comparison rather than being silently normalized.
""",
)

write_json(
    "PRE_REGISTERED_OUTCOME_HIERARCHY_V2.json",
    {
        "schema_version": "PRE_REGISTERED_OUTCOME_HIERARCHY_V2",
        "frozen_before_active_results": True,
        "primary": {
            "safety": {"metric": "trial_level_represented_map_collision_proxy_incidence", "tier": "TIER_B", "scope": "REPRESENTED_MAP_RELATIVE"},
            "task_liveness": {"metric": "goal_reached_rate", "companion": "normalized_progress"},
            "assurance_system": {"metric": "ASSURANCE_BOUNDARY_incidence"},
        },
        "secondary": ["minimum_clearance", "certification_margin_violation", "backup_activation_rate", "terminal_intervention_rate", "alternative_commit_rate", "runtime_observations", "internal_certification_distributions"],
        "external_gt_policy": "May add a Tier-A scene-scoped outcome when authority exists, but must not hide Tier-B results.",
        "internal_L2_PASS_rate_is_primary_safety_efficacy": False,
    },
)

invariant_texts = [
    "oracle has no runtime feedback authority", "evaluation runs only on immutable trace/reference", "internal certificate statuses cannot define collision outcome", "represented-map collision proxy uses operational footprint 0.015 m", "certification-margin violation uses 0.025 m and is not called collision", "swept executed segment is evaluated, not endpoint-only", "collision oracle version is identical across compared variants", "goal success cannot be granted by timeout alone", "goal threshold is pre-existing or frozen before V2 outcomes", "progress formula is pre-registered", "terminal commit requires terminal action role/evidence, not zero-vector heuristic", "software fail-close is not safe stop", "assurance boundary is not safe success", "backup activation and terminal intervention are separate metrics", "safety and liveness remain separate metric families", "no composite score hides tradeoffs", "evaluation UNKNOWN is never SAFE", "missing trials are not dropped silently", "trial is primary statistical unit", "variants use paired identical trial identities", "oracle definitions cannot adapt after outcome reveal", "physical collision claim requires Tier-A external GT", "represented-map oracle declares map-relative scope", "runtime timing observation is not hard real-time guarantee", "V1 historical metrics remain historical and are not silently reinterpreted", "oracle output cannot mutate supervisor/controller state",
]
write_json("INDEPENDENT_EVALUATION_ORACLE_INVARIANTS_V2.json", {"schema_version": "INDEPENDENT_EVALUATION_ORACLE_INVARIANTS_V2", "invariants": [{"id": f"EO-{i:02d}", "rule": rule, "mandatory": True} for i, rule in enumerate(invariant_texts, 1)]})

nodes = ["runtime_controller", "supervisor", "C0_L1_L2_L3", "execution_trace", "represented_map_reference", "external_GT_reference", "posthoc_oracle", "statistical_aggregator", "paper_outcome_table", "oracle_threshold_registry", "method_margin"]
edges = [
    ["runtime_controller", "supervisor", "candidate_and_status"],
    ["supervisor", "execution_trace", "committed_action_and_state"],
    ["C0_L1_L2_L3", "execution_trace", "diagnostic_covariates_only"],
    ["represented_map_reference", "posthoc_oracle", "frozen_map_authority"],
    ["external_GT_reference", "posthoc_oracle", "optional_scene_matched_reference"],
    ["execution_trace", "posthoc_oracle", "immutable_executed_trace"],
    ["oracle_threshold_registry", "posthoc_oracle", "pre_registered_thresholds"],
    ["posthoc_oracle", "statistical_aggregator", "typed_outcomes"],
    ["statistical_aggregator", "paper_outcome_table", "pre_registered_aggregation"],
]
write_json("evaluation_oracle_dataflow_graph.json", {"schema_version": "EVALUATION_ORACLE_DATAFLOW_GRAPH_V2", "nodes": nodes, "edges": [{"source": a, "target": b, "meaning": c} for a, b, c in edges], "forbidden_edges": [["posthoc_oracle", "runtime_controller"], ["certificate_status", "collision_ground_truth"], ["method_margin", "physical_collision_radius"], ["paper_outcome_table", "oracle_threshold_registry"]]})

scenarios = [
    ("S01", "L2_PASS_INDEPENDENT_PENETRATION", "EVAL_VIOLATION"), ("S02", "L2_FAIL_BACKUP_TRACE_CLEAR", "EVAL_PASS_WITH_L2_DIAGNOSTIC_FAIL"), ("S03", "ENDPOINT_SAFE_SEGMENT_CROSSES", "EVAL_VIOLATION"), ("S04", "R015_CLEAR_R025_MARGIN_VIOLATED", "COLLISION_PASS_MARGIN_VIOLATION"),
    ("S05", "MOVING_TIMEOUT_NOT_AT_GOAL", "TIMEOUT_NOT_GOAL_REACHED"), ("S06", "EXPLICIT_GOAL_PREDICATE_MET", "GOAL_REACHED"), ("S07", "ZERO_WITHOUT_TERMINAL_CHAIN", "NOT_TERMINAL_COMMIT"), ("S08", "CERTIFIED_EXECUTED_TERMINAL", "TERMINAL_COMMIT_COUNT_1"),
    ("S09", "SOFTWARE_BREAK", "SOFTWARE_FAIL_CLOSE_ONLY"), ("S10", "ASSURANCE_BOUNDARY", "NOT_SAFE_STOP_SUCCESS"), ("S11", "MISSING_TRACE_STEP", "EVAL_UNKNOWN"), ("S12", "NONFINITE_STATE", "EVAL_UNKNOWN"),
    ("S13", "INTERNAL_H_SAFE_ORACLE_VIOLATION", "EVAL_VIOLATION"), ("S14", "ORACLE_VERSION_MISMATCH", "COMPARISON_INVALID"), ("S15", "OPERATIONAL_RADIUS_CHANGED", "COMPARISON_INVALID"), ("S16", "CERT_MARGIN_DIFF_COLLISION_RADIUS_FIXED", "COMPARISON_VALID_IF_OTHERWISE_ALIGNED"),
    ("S17", "EXTERNAL_GT_UNAVAILABLE", "TIER_A_BLOCKED_TIER_B_AVAILABLE"), ("S18", "BACKUP_ACTION_ROLE", "BACKUP_COUNT_ONLY"), ("S19", "ALTERNATIVE_ACTION_ROLE", "ALTERNATIVE_COUNT_ONLY"), ("S20", "TERMINAL_READY_NOT_COMMITTED", "TERMINAL_COMMIT_COUNT_0"),
    ("S21", "UNKNOWN_TRIAL", "RETAIN_IN_ACCOUNTING"), ("S22", "MISSING_RUNTIME_ONE_STEP", "TIMING_UNKNOWN_GEOMETRY_MAY_REMAIN_EVALUABLE"), ("S23", "OUTCOME_DEPENDENT_THRESHOLD_EDIT", "CHECKER_REJECT"), ("S24", "IMPORT_V1_TIMEOUT_SUCCESS", "VALIDATOR_REJECT"),
]
write_json("ORACLE_SYNTHETIC_SCENARIOS_V2.json", {"schema_version": "ORACLE_SYNTHETIC_SCENARIOS_V2", "scenarios": [{"id": i, "fixture": f, "expected": e} for i, f, e in scenarios], "count": len(scenarios), "synthetic_only": True, "scientific_trial_count": 0})

write_json(
    "evaluation_oracle_counterexamples.json",
    {
        "schema_version": "EVALUATION_ORACLE_COUNTEREXAMPLES_V2",
        "counterexamples": [
            {"id": "CE1", "edge": "posthoc_oracle -> runtime_controller", "rejected_because": "feedback violates EO-01/EO-26"},
            {"id": "CE2", "edge": "certificate_status -> collision_ground_truth", "rejected_because": "circular safety evidence"},
            {"id": "CE3", "edge": "method_margin -> physical_collision_radius", "rejected_because": "variant-dependent outcome threshold"},
            {"id": "CE4", "edge": "paper_outcome_table -> oracle_threshold_registry", "rejected_because": "post-outcome adaptation"},
            {"id": "CE5", "legacy": "timeout_while_moving -> success", "rejected_because": "timeout is not goal completion"},
        ],
    },
)

write_md(
    "README.md",
    """
# Independent Evaluation Oracle V2

Design-only, posthoc/read-only freeze based exactly on PR #113 head `5595e56b756291881fb9f6f17ba3d7551263574f`. It separates method-internal diagnostics, execution-trace facts, represented-map-relative outcomes, and scene-scoped external ground truth. It defines immutable trace, swept-segment collision/margin outcomes, goal/progress, role accounting, UNKNOWN, paired trial aggregation, anti-circularity checks, and claim boundaries.

No runtime or oracle evaluator is implemented. No controller, map, dynamics, dataset, trial, GPU, rollout, benchmark, or formal collection is changed or executed.
""",
)
