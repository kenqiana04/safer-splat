"""Frozen task configuration for the Core causal-architecture specification."""

from pathlib import Path

TASK_ID = "WRITE_CORE_CAUSAL_ARCHITECTURE_SPECIFICATION_V1"
BRANCH = "core-causal-architecture-specification-v1"
UPSTREAM_BRANCH = "core-v1-actionable-factor-ranking-v1"
UPSTREAM_HEAD = "e8ec67d5585f9634ae6a5d4991eac5f9e4abfbae"
TASK_ROOT = Path(__file__).resolve().parent
REMOTE_TASK_ROOT = "/disk1/zlab/maintenance_records/core_causal_architecture_specification_v1"
EXPECTED_PRS = {
    83: ("fas-cbf-core-v1-conceptual-closure", "17805e67b75412dc21b1a5fff4143ea3bc985f7f"),
    84: ("fas-cbf-unified-executable-safety-certifier-v1", "04ebca2b1b35124ad0e61ebed96e491c9edae4bb"),
    86: ("replica-gt-executable-safety-method-matrix-v1", "d4f20f44a810afc2d6379853a286a3e18b175221"),
    87: ("resume-replica-gt-executable-safety-activated-benchmark-v1", "fbe67f0c607add7f8049d4ce75e8f9e1ae8498d9"),
    89: ("core-v1-cross-environment-activation-portability-audit-v1", "047513b5e612f91e63ab1e7054815615cb455fd7"),
    90: ("core-v1-representative-shortfall-causal-decomposition-v1", "48db34d4e61f019fcd2b578c04cc87eefb00747a"),
    91: (UPSTREAM_BRANCH, UPSTREAM_HEAD),
}
ROLE_IDS = [
    "L0_START_STATE_ADMISSION", "L1_IMMEDIATE_UNAVOIDABLE_SEGMENT",
    "L2_CANDIDATE_DEPENDENT_FUTURE_SAFETY", "L3_CANDIDATE_RECOVERABILITY",
    "L4_ALTERNATIVE_CONTROL_SEARCH", "L5_TERMINAL_OR_FAIL_CLOSED_EXECUTION",
]
FIGURES = [
    "historical_b0_b3_vs_role_architecture.png", "control_authority_timeline.png", "position_first_euler_dependency.png",
    "first_control_affected_horizon.png", "start_safe_integration.png", "immediate_unavoidable_vs_candidate_future.png",
    "recoverability_entry_conditions.png", "alternative_search_eligibility.png", "state_machine.png", "failure_taxonomy.png",
    "gate_reachability_and_denominators.png", "unconditional_vs_conditional_metrics.png", "method_vs_evaluation_boundary.png",
    "historical_evidence_remapping.png", "architecture_A.png", "architecture_B.png", "architecture_C.png",
    "architecture_comparison.png", "reviewer_case_preferences.png", "final_architecture_decision.png", "downstream_single_next_step.png",
]
