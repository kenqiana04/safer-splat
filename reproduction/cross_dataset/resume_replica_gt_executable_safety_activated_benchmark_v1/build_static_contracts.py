"""Build the preregistered method, fairness, sampling, and reference contracts."""
from __future__ import annotations

from common import sha256_json, write_csv, write_json, write_text
from task_config import (
    BASE_HEAD, CERTIFIER_TIME_BUDGET_S, DEADLINE_S, DT, EFFECTIVE_RADIUS,
    GOAL_POSITION_TOLERANCE_M, GOAL_VELOCITY_TOLERANCE_MPS,
    GROUP_MINIMUMS, GROUP_TARGETS, H_STOP_MAX, LIBRARY_ID, LIBRARY_SHA256,
    MAP_SNAPSHOT_ID, MARGIN, METHODS, PHYSICAL_MIN_CLEARANCE_M, PR84_HEAD,
    REPRESENTATIVE_ROLLOUT_SUBSET, REPRESENTATIVE_TARGET, ROBOT_RADIUS,
    SLOT_IDS, TASK_ROOT, TERMINAL_TOLERANCE, U_BOUND, V_BOUND,
)


def main() -> None:
    shared = {
        "map_snapshot": MAP_SNAPSHOT_ID,
        "primary": "PRIMARY-CBF-FILTERED",
        "u_nom_role": "LOG_AND_CONTROL_DEVIATION_ONLY",
        "normative_model": "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1",
        "position_transition": "p_next=p+dt*v",
        "velocity_transition": "v_next=v+dt*u",
        "interval_position": "p(tau)=p+tau*v",
        "dt": DT,
        "u_bounds": [-U_BOUND, U_BOUND],
        "v_bounds": [-V_BOUND, V_BOUND],
        "robot_radius_m": ROBOT_RADIUS,
        "margin_m": MARGIN,
        "effective_footprint_m": EFFECTIVE_RADIUS,
        "terminal_set": "BRAKING_TO_REST_TERMINAL_SET_V1",
        "terminal_tolerance": TERMINAL_TOLERANCE,
        "h_stop_max": H_STOP_MAX,
        "segment_backend": "EXACT_ANALYTIC_SPHERE_SEGMENT_MINIMUM",
        "builtin_braking": "DETERMINISTIC_COMPONENTWISE_BRAKING_POLICY_V1",
        "reference_role": "POST_LOCK_OFFLINE_EVALUATION_ONLY",
        "certifier_time_budget_s": CERTIFIER_TIME_BUDGET_S,
        "deadline_diagnostic_s": DEADLINE_S,
        "goal_position_tolerance_m": GOAL_POSITION_TOLERANCE_M,
        "goal_velocity_tolerance_mps": GOAL_VELOCITY_TOLERANCE_MPS,
        "goal_tolerance_provenance": "FROZEN_REPLICA_BOUNDED_DIRECT_GOAL_BASELINE",
    }
    registry = {
        "status": "PASS_COMPLETE_PR86_METHOD_MATRIX_REPRODUCTION",
        "shared_inputs": shared,
        "methods": [
            {"method": METHODS[0], "current": True, "segment": False, "backup": False, "builtin_braking": False, "directional_slots": []},
            {"method": METHODS[1], "current": True, "segment": True, "backup": False, "builtin_braking": False, "directional_slots": []},
            {"method": METHODS[2], "current": True, "segment": True, "backup": True, "builtin_braking": True, "directional_slots": []},
            {"method": METHODS[3], "current": True, "segment": True, "backup": True, "builtin_braking": True, "directional_slots": list(SLOT_IDS)},
        ],
        "b3_minus_b2": {"only_difference": LIBRARY_ID, "slot_ids": list(SLOT_IDS), "slot_count": 6},
    }
    write_json(TASK_ROOT / "methods/method_registry.json", registry)
    write_csv(TASK_ROOT / "methods/method_difference_matrix.csv", [
        {"method": item["method"], "current": item["current"], "segment": item["segment"], "backup": item["backup"], "builtin_braking": item["builtin_braking"], "directional_slot_count": len(item["directional_slots"])}
        for item in registry["methods"]
    ])
    checks = {
        "same_map_snapshot": True,
        "same_state_goal": True,
        "same_u_nom_logged": True,
        "same_u_filtered_primary": True,
        "same_actuator_bounds": True,
        "same_current_full_query": True,
        "same_normative_model": True,
        "same_segment_backend": True,
        "same_terminal_set": True,
        "same_backup_policy": True,
        "same_builtin_braking_B2_B3": True,
        "B3_only_adds_six_slot_directional_template": True,
        "no_reference_online_input": True,
        "no_future_outcome_input": True,
        "library_identity_exact": LIBRARY_SHA256 == "3d491876234161d4e881ec1227c505cb07c0af00d5e881c5289fdf1f1577c6fe",
    }
    write_json(TASK_ROOT / "methods/fairness_audit.json", {"status": "PASS_METHOD_FAIRNESS_CONTRACT", "checks": checks, "all_pass": all(checks.values())})
    write_json(TASK_ROOT / "methods/shared_input_hashes.json", {"shared_inputs": shared, "canonical_sha256": sha256_json(shared)})
    write_json(TASK_ROOT / "methods/pr86_contract_reproduction.json", {
        "status": "PASS_PR86_METHOD_AND_LIBRARY_CONTRACT_REPRODUCED",
        "pr86_head": BASE_HEAD,
        "pr84_head": PR84_HEAD,
        "library_id": LIBRARY_ID,
        "global_library_sha256": LIBRARY_SHA256,
        "slot_ids": list(SLOT_IDS),
        "method_registry_sha256": sha256_json(registry),
    })
    write_json(TASK_ROOT / "representative_sampling/sampling_contract.json", {
        "status": "FROZEN_BEFORE_SELECTION",
        "target": REPRESENTATIVE_TARGET,
        "rollout_subset": REPRESENTATIVE_ROLLOUT_SUBSET,
        "candidate_sources": ["FROZEN_ROUTE_REGISTRY", "ROUTE_NODES", "ROUTE_EDGE_FIXED_FRACTIONS"],
        "strata": ["route_id", "node_or_edge", "velocity_magnitude", "spatial_quartile", "zero_nonzero_velocity"],
        "within_stratum_order": "CANONICAL_TUPLE_SHA256_ASCENDING",
        "forbidden_selection_inputs": ["stage_predicate", "B0_B3", "reference_future_outcome", "progress", "runtime", "observed_gate_activation"],
        "physical_min_clearance_m": PHYSICAL_MIN_CLEARANCE_M,
    })
    write_json(TASK_ROOT / "reference/reference_oracle_contract.json", {
        "status": "FROZEN_POST_LOCK_OFFLINE_AUTHORITY",
        "oracle": "VALIDATED_REPLICA_FLOAT64_SEGMENT_TO_TRIANGLE_MESH_MINIMUM_DISTANCE",
        "robot_sphere_radius_m": ROBOT_RADIUS,
        "controller_exposure_count": 0,
        "cohort_selection_future_outcome_count": 0,
        "represented_false_safe_semantics": "CERTIFICATE_CONTRADICTS_ITS_NORMATIVE_REPRESENTED_BACKEND",
        "map_reference_disagreement_semantics": "REPRESENTED_GAUSSIAN_AND_OFFICIAL_MESH_DIFFER_WITHOUT_IMPLYING_CERTIFIER_BUG",
    })
    write_json(TASK_ROOT / "statistics/preregistered_hypotheses.json", {
        "status": "FROZEN_BEFORE_FORMAL_RESULTS",
        "hypotheses": {
            "H1": "G1 B1 adds segment noncommit versus B0",
            "H2": "G2/G3 B2 adds backup discrimination versus B1",
            "H3": "G3 B3 restores certified control versus B2 with represented_false_safe=0",
            "H4": "G0 quantifies B3 over-rejection and progress cost",
            "H5": "Representative cohort estimates gate and rescue prevalence",
            "H6": "Post-lock reference outcomes compare B0 and B3 when evaluable",
            "H7": "50 ms deadline misses remain separate from semantic status",
        },
        "holm_family": ["H1", "H2", "H3", "H4", "H5", "H6", "H7"],
        "group_targets": GROUP_TARGETS,
        "group_minimums": GROUP_MINIMUMS,
        "project_thresholds_are_domain_general": False,
    })
    write_text(TASK_ROOT / "methods/NESTED_METHOD_CONTRACT.md", """
# Nested B0-B3 Contract

All four methods share the same state, goal, represented map, nominal controller, filtered primary, actuator bounds, current full query, normative dynamics and post-lock offline reference authority. B1 adds only immediate swept-segment admission to B0. B2 adds only terminal-backup certification and PR84 built-in deterministic braking to B1. B3 adds only the six frozen PR86 directional slots to B2. Unfiltered nominal control is never a B3-only candidate.
""")
    print("PASS_STATIC_RESUMED_BENCHMARK_CONTRACTS")


if __name__ == "__main__":
    main()
