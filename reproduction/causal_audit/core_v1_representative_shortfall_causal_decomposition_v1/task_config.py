"""Immutable contract for the Core V1 causal-decomposition audit."""
from __future__ import annotations

from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TASK_ROOT.parents[2]
UPSTREAM_ROOT = REPO_ROOT / "reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1"
SERVER_TASK_ROOT = "/disk1/zlab/maintenance_records/core_v1_representative_shortfall_causal_decomposition_v1"
SERVER_UPSTREAM_ROOT = "/disk1/zlab/maintenance_records/core_v1_cross_environment_activation_portability_audit_v1"
SERVER_PR87_ROOT = "/disk1/zlab/maintenance_records/resume_replica_gt_executable_safety_activated_benchmark_v1"

BRANCH = "core-v1-representative-shortfall-causal-decomposition-v1"
BASE_BRANCH = "core-v1-cross-environment-activation-portability-audit-v1"
BASE_HEAD = "047513b5e612f91e63ab1e7054815615cb455fd7"
PR89_BASE_BRANCH = "research-direction-novelty-data-winnability-audit-v1"
PR_HEADS = {
    84: "04ebca2b1b35124ad0e61ebed96e491c9edae4bb",
    85: "7afef38392bec36d9d9811e5a22c816da5faf1ff",
    86: "d4f20f44a810afc2d6379853a286a3e18b175221",
    87: "fbe67f0c607add7f8049d4ce75e8f9e1ae8498d9",
    88: "9287617cce74561aa434d1aca7eb684f79551188",
    89: BASE_HEAD,
}

METHODS = (
    "B0_CURRENT_CBF_ONLY",
    "B1_PLUS_SWEPT_SEGMENT",
    "B2_PLUS_TERMINAL_BACKUP",
    "B3_FULL_UNIFIED_WITH_DIRECTIONAL_ALTERNATIVES",
)
FORMAL_ENVIRONMENTS = ("E1_REPLICA_GT_FINE", "E5_STONEHENGE_SAFER", "E6_FLIGHT_SAFER")
ALL_ENVIRONMENTS = (
    "E1_REPLICA_GT_FINE", "E2_ETH3D_LEARNED_GAUSSIAN", "E3_TUM_SPLATAM",
    "E4_TUM_GAUSSIAN_SLAM", "E5_STONEHENGE_SAFER", "E6_FLIGHT_SAFER",
    "E7_TUM_SPLATFACTO_NEGATIVE_CONTROL",
)
EVIDENCE_CLASSES = (
    "E0_FROZEN_FORMAL_EVIDENCE", "E1_REANALYSIS_OF_FROZEN_RECORDS",
    "E2_SHADOW_DIAGNOSTIC", "E3_BOUNDED_APPROXIMATE_ORACLE",
    "E4_COUNTERFACTUAL_REGIME_DIAGNOSTIC", "E5_DATA_AVAILABILITY_AUDIT",
)
VERDICTS = (
    "SUPPORTED_PRIMARY", "SUPPORTED_CONTRIBUTING", "NOT_SUPPORTED",
    "PARTIALLY_SUPPORTED", "STRUCTURAL_FACT", "DATA_BLOCKED", "NOT_IDENTIFIABLE",
)

DT = 0.05
U_BOUND = 0.1
V_BOUND = 0.1
EFFECTIVE_RADIUS = 0.11
TERMINAL_TOLERANCE = 1e-12
H_STOP_MAX = 20
GRID7 = (-0.1, -0.0666667, -0.0333333, 0.0, 0.0333333, 0.0666667, 0.1)
SOBOL_SEED = 20260807
SOBOL_SCRAMBLE = True
