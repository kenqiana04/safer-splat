"""Frozen configuration for the Core V1 actionable-factor ranking decision."""

from pathlib import Path

TASK_ID = "RANK_CORE_V1_ACTIONABLE_FACTORS_AND_SELECT_ONE_BOUNDED_NEXT_STEP_V1"
BRANCH = "core-v1-actionable-factor-ranking-v1"
UPSTREAM_BRANCH = "core-v1-representative-shortfall-causal-decomposition-v1"
UPSTREAM_HEAD = "48db34d4e61f019fcd2b578c04cc87eefb00747a"
UPSTREAM_BASE_HEAD = "047513b5e612f91e63ab1e7054815615cb455fd7"
TASK_ROOT = Path(__file__).resolve().parent
UPSTREAM_ROOT = (
    TASK_ROOT.parents[1]
    / "causal_audit"
    / "core_v1_representative_shortfall_causal_decomposition_v1"
)
REMOTE_TASK_ROOT = "/disk1/zlab/maintenance_records/core_v1_actionable_factor_ranking_v1"

EXPECTED_PRS = {
    84: ("fas-cbf-unified-executable-safety-certifier-v1", "04ebca2b1b35124ad0e61ebed96e491c9edae4bb"),
    85: ("replica-gt-executable-safety-activated-benchmark-v1", "7afef38392bec36d9d9811e5a22c816da5faf1ff"),
    86: ("replica-gt-executable-safety-method-matrix-v1", "d4f20f44a810afc2d6379853a286a3e18b175221"),
    87: ("resume-replica-gt-executable-safety-activated-benchmark-v1", "fbe67f0c607add7f8049d4ce75e8f9e1ae8498d9"),
    88: ("research-direction-novelty-data-winnability-audit-v1", "9287617cce74561aa434d1aca7eb684f79551188"),
    89: ("core-v1-cross-environment-activation-portability-audit-v1", "047513b5e612f91e63ab1e7054815615cb455fd7"),
    90: (UPSTREAM_BRANCH, UPSTREAM_HEAD),
}

POSITIVE_KEYS = [
    "S1_SCIENTIFIC_PREREQUISITE", "S2_CAUSAL_INFORMATION_GAIN", "S3_FALSIFIABILITY",
    "S4_CLAIM_IMPACT", "S5_STRUCTURAL_IMPORTANCE", "S6_EXISTING_EVIDENCE_SUPPORT",
    "S7_ASSET_REUSE", "S8_DATA_INDEPENDENCE", "S9_IMPLEMENTATION_INDEPENDENCE",
    "S10_TIME_TO_DECISION", "S11_DOWNSTREAM_OPTION_VALUE", "S12_REVIEWER_DEFENSIBILITY",
]
RISK_KEYS = [
    "R1_DIRECTION_DRIFT", "R2_BENCHMARK_SHOPPING", "R3_DATA_DEPENDENCY",
    "R4_ENGINEERING_EXPANSION", "R5_CLAIM_AMBIGUITY", "R6_NON_IDENTIFIABILITY",
    "R7_COMPETITOR_OVERLAP", "R8_SUNK_COST_BIAS_RISK",
]
FATAL_GATES = [f"G{i}" for i in range(1, 13)]
FIGURES = [
    "pr87_pr90_decision_lineage.png", "f01_f11_current_status.png", "action_package_map.png",
    "dependency_graph.png", "fatal_dependency_matrix.png", "positive_score_comparison.png",
    "risk_penalty_comparison.png", "net_score_comparison.png", "five_day_decision_value.png",
    "asset_reuse_comparison.png", "data_dependency_comparison.png", "a1_control_authority_dependency.png",
    "a2_on_policy_asset_availability.png", "a3_eligible_state_availability.png",
    "a4_regime_legitimacy.png", "reviewer_preferences.png", "reviewer_disagreement.png",
    "claim_impact_comparison.png", "final_action_selection.png", "downstream_one_step.png",
]
