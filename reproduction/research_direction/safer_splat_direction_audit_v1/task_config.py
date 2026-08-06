"""Frozen configuration for the SAFER-Splat research-direction audit V1."""

from __future__ import annotations

AUDIT_ID = "AUDIT_SAFER_SPLAT_RESEARCH_DIRECTION_NOVELTY_DATA_AND_WINNABILITY_V1"
SEARCH_CUTOFF = "2026-08-06"
UPSTREAM = {
    84: "04ebca2b1b35124ad0e61ebed96e491c9edae4bb",
    85: "7afef38392bec36d9d9811e5a22c816da5faf1ff",
    86: "d4f20f44a810afc2d6379853a286a3e18b175221",
    87: "fbe67f0c607add7f8049d4ce75e8f9e1ae8498d9",
}

DIRECTIONS = {
    "D0": "STOP_NEW_METHOD_AND_CONSOLIDATE_EXISTING_EVIDENCE",
    "D1": "CORE_V1_RARE_EVENT_EXECUTABLE_SAFETY",
    "D2": "FAST_CERTIFIED_ANISOTROPIC_GAUSSIAN_SWEPT_QUERY",
    "D3": "CONTROL_CONDITIONED_SELECTIVE_FALSE_FREE_QUERY",
    "D4": "GAUSSIAN_AWARE_BACKUP_SET",
    "D5": "CERTIFICATE_AWARE_CONTINUOUS_CONTROL_OPTIMIZATION",
    "D6": "RISK_AWARE_GAUSSIAN_CONSTRAINT_BUDGETING",
    "D7": "LEARNED_GAUSSIAN_MAP_NAVIGATION_QUALIFICATION_BENCHMARK",
    "D8": "HYBRID_MAP_TRUST_GATED_SAFETY_CONTROL",
}

POSITIVE_WEIGHTS = {
    "S1": 8.0,
    "S2": 12.0,
    "S3": 10.0,
    "S4": 4.0,
    "S5": 10.0,
    "S6": 8.0,
    "S7": 4.0,
    "S8": 12.0,
    "S9": 4.0,
    "S10": 8.0,
    "S11": 3.0,
    "S12": 12.0,
    "S13": 3.0,
    "S14": 2.0,
}

RISK_WEIGHTS = {
    "R1": 10.0,
    "R2": 15.0,
    "R3": 7.0,
    "R4": 12.0,
    "R5": 7.0,
    "R6": 10.0,
    "R7": 6.0,
    "R8": 10.0,
    "R9": 12.0,
    "R10": 11.0,
}

FATAL_GATES = {
    "G1": "one_sentence_difference_supported_by_full_text",
    "G2": "three_strong_baselines_runnable_or_fairly_reimplementable",
    "G3": "two_independent_learned_maps_with_credible_reference",
    "G4": "cross_map_train_calibration_test_protocol",
    "G5": "required_events_not_zero_or_extremely_rare",
    "G6": "likely_case_deliverable_within_eight_weeks",
    "G7": "no_post_freeze_contract_tuning_for_positive_result",
    "G8": "contribution_not_only_existing_module_combination",
    "G9": "fewer_than_three_open_subproblems_before_minimum_paper",
    "G10": "bounded_publishable_fallback_if_main_hypothesis_fails",
}

METHOD_THRESHOLDS = {
    "net_score_min": 62.0,
    "S2_min": 4,
    "S3_min": 3,
    "S5_min": 3,
    "S8_min": 3,
    "S12_min": 3,
    "R2_max": 3,
    "R4_max": 3,
    "R9_max": 3,
}

QUERY_LIMITS = {"point_per_map": 2000, "short_segment_per_map": 1000}
EXECUTION_COUNTS = {
    "new_training_count": 0,
    "map_mutation_count": 0,
    "controller_mutation_count": 0,
    "new_method_implementation_count": 0,
    "formal_navigation_run_count": 0,
    "scoring_contract_change_count": 0,
    "fatal_gate_change_count": 0,
    "protected_source_mutation_count": 0,
}

assert set(DIRECTIONS) == {f"D{i}" for i in range(9)}
assert sum(POSITIVE_WEIGHTS.values()) == 100.0
assert sum(RISK_WEIGHTS.values()) == 100.0
assert set(FATAL_GATES) == {f"G{i}" for i in range(1, 11)}
