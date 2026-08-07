"""Frozen identities and output contracts for the specification-only task."""

from __future__ import annotations

from pathlib import Path


TASK_ID = "WRITE_CORE_V2_CAUSAL_INCREMENT_SPECIFICATION_V1"
TASK_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TASK_ROOT.parents[2]
EXPECTED_HEAD = "dfd9bce2633e542fdb72a1805f79cc4feeeebc3a"
BRANCH = "core-v2-causal-increment-specification-v1"
BASE_BRANCH = "core-causal-architecture-specification-v1"

EXPECTED_PRS = {
    83: ("fas-cbf-core-v1-conceptual-closure", "17805e67b75412dc21b1a5fff4143ea3bc985f7f"),
    84: ("fas-cbf-unified-executable-safety-certifier-v1", "04ebca2b1b35124ad0e61ebed96e491c9edae4bb"),
    86: ("replica-gt-executable-safety-method-matrix-v1", "d4f20f44a810afc2d6379853a286a3e18b175221"),
    87: ("resume-replica-gt-executable-safety-activated-benchmark-v1", "fbe67f0c607add7f8049d4ce75e8f9e1ae8498d9"),
    89: ("core-v1-cross-environment-activation-portability-audit-v1", "047513b5e612f91e63ab1e7054815615cb455fd7"),
    90: ("core-v1-representative-shortfall-causal-decomposition-v1", "48db34d4e61f019fcd2b578c04cc87eefb00747a"),
    91: ("core-v1-actionable-factor-ranking-v1", "e8ec67d5585f9634ae6a5d4991eac5f9e4abfbae"),
    92: ("core-causal-architecture-specification-v1", EXPECTED_HEAD),
}

PR92_TASK_ROOT = REPO_ROOT / "reproduction/specification/core_causal_architecture_specification_v1"
PR84_ROOT = "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1"

SUPPLEMENTAL_SOURCE_PATHS = [
    f"{PR84_ROOT}/adapters/normative_dynamics_adapter.py",
    f"{PR84_ROOT}/adapters/gaussian_barrier_adapter.py",
    f"{PR84_ROOT}/certifier/segment_backends/base.py",
    f"{PR84_ROOT}/certifier/segment_backends/analytic_primitive.py",
    f"{PR84_ROOT}/certifier/segment_backends/conservative_interval.py",
    f"{PR84_ROOT}/certifier/segment_backends/sampled_diagnostic.py",
    f"{PR84_ROOT}/certifier/segment_certificate.py",
    f"{PR84_ROOT}/certifier/result_types.py",
    f"{PR84_ROOT}/proof_artifacts/swept_segment_assumptions.json",
    f"{PR84_ROOT}/proof_artifacts/swept_segment_derivation.md",
    f"{PR84_ROOT}/proof_artifacts/execution_model_audit.json",
    f"{PR84_ROOT}/proof_artifacts/S1_segment_proposition.md",
    f"{PR84_ROOT}/task_config.py",
    "splat/gsplat_utils.py",
    "run.py",
    "work/risk_aware_cbf/scripts/run_v4b_corrective_dt_filter.py",
    "work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py",
]

FIGURES = [
    "control_authority_timeline_h1.png",
    "l1_vs_l2_segment_dependency.png",
    "h1_candidate_dependence.png",
    "frozen_geometry_backend_new_causal_role.png",
    "l2_l3_l4_l5_boundaries.png",
    "minimal_state_machine_delta.png",
    "h1_vs_h2_scope.png",
    "falsification_gates.png",
    "supported_vs_prohibited_claims.png",
    "final_case_decision.png",
]

FINAL_CASE = "CASE_A"
FINAL_STATUS = "PASS_CORE_V2_L2_H1_CAUSAL_INCREMENT_SPECIFICATION"
FINAL_DECISION = "FREEZE_MINIMAL_L2_H1_SPECIFICATION_AND_VALIDATE_IN_SHADOW_ONLY_MODE"
ONLY_NEXT_TASK = "IMPLEMENT_L2_H1_SHADOW_CERTIFIER_V1"
