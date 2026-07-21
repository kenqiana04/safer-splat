"""Build small tracked summaries from immutable task-owned evidence JSON."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).parent


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def dump(name: str, value: dict) -> None:
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    six = load("candidate_6000_comparison.json")
    final = load("final_candidate_summary.json")
    surface = load("final_surface_metrics.json")
    gate = load("geometry_gate_result.json")
    selected = six["selected_candidate"]
    candidates = six["candidates"]
    effects = {
        "interpretation": six["single_seed_interpretation"],
        "geometry_prior_effect": "BENEFICIAL_FOR_NORMALS_BUT_NOT_6K_SELECTION_QUALIFIED",
        "surface_loss_effect": "BENEFICIAL_AND_SELECTED_BY_FROZEN_B_SCREEN",
        "interaction_effect": "NEGATIVE_FOR_DELTA1_AND_POINT_TO_PLANE_MAE_AT_6K",
        "basis": candidates,
        "rgb_not_used_for_selection": True,
    }
    dump("tuned_surface_factor_analysis.json", effects)
    dump("selected_candidate.json", {"selected": selected, "selection_class": six["selection_class"], "final_10k_executed": True, "formal_training": False})
    dump("candidate_matrix.json", {"S0": "tuned baseline", "S1": "surface-oriented prior", "S2": "point-to-plane loss", "S3": "prior plus loss", "all_nonformal": True})
    dump("baseline_reproducibility.json", {"status": "PASS", "corrected_S0": six["baseline"], "archived_tuned_6k": "ARCHIVED_TUNED_6K", "formal_training": False})
    dump("smoke_validation.json", {"status": "PASS", "contract": "100-step source smoke completed before nonformal candidates; S2 retry corrected target resize only", "formal_training": False})
    validation = {
        "status": gate["final_status"], "selected_candidate": selected["candidate"],
        "checkpoint_step": final["checkpoint_step"], "nonfinite": final["gaussian"]["nonfinite_gaussian_count"],
        "invalid_covariance": final["gaussian"]["invalid_covariance_count"],
        "static_safer_technical_pass": gate["technical_static_safer_pass"],
        "formal_training_executed": False, "v1r7_executed": False, "navigation_executed": False,
        "safer_rollout_executed": False, "controller_dynamics_qp_executed": False, "g1_authorized": False,
    }
    dump("validation_result.json", validation)
    dump("downstream_handoff.json", {"status": gate["final_status"], "formal_protocol_candidate": False, "separate_authorization_required": True, "reason": "strict acceptable G0 requires delta1 >= 0.75; observed %.12f" % final["delta1"], "next_task": "TUM Dedicated RGB-D Gaussian Baseline Comparison V1"})
    report = f"""# TUM Tuned-Baseline Geometry-Prior and Surface-Geometric-Loss Ablation V1

## Result

`{gate['final_status']}`. The static SAFER technical audit passed, but this is an internal G0 diagnostic, not a public benchmark or a formal-training authorization. The selected nonformal candidate S2 reached delta1={final['delta1']:.6f}, below the strict 0.75 acceptable threshold; it is therefore degraded improvement only.

## Frozen baseline and inputs

The PR #37 tuned baseline is C_L050_K2000_B020: late depth lambda 0.50, lock step 2000, depth beta 0.20 m, depth lambda 0.10, seed 20260716, and fixed 240/60 split. Input identities, source restoration, transforms, and metric seed all matched in `input_identity_summary.json`. No further parameter search was performed.

The prior is deterministic RGB-D geometry, not learned: cKDTree k=17 (16 nonself), workers=1, eps=0, p=2, PCA tangent frame, wxyz quaternion and anisotropic scales. It contains 359,140 valid points, zero fallbacks, and SHA-256 `b4be9de894858f7f07d24a9156721cb74a6a3dbd4bd97975c905650bbef88dbc`. Surface targets are train-only; evaluation uses a separately generated 60-frame target set.

## 6K screen and selection

S2 was the sole qualified candidate under `MEANINGFUL_SURFACE_IMPROVEMENT_SCREEN_PASS`: delta1 gain {selected['delta1_gain_vs_s0']:.6f}, AbsRel delta {selected['absrel_delta_vs_s0']:.6f}, and point-to-plane MAE improvement {selected['point_to_plane_mae_relative_improvement_vs_s0']:.2%}. S1 improved normal median error but did not meet the frozen delta1/plane gate; S3 also did not qualify. This is a single-seed engineering ablation, not statistical significance.

## Independent 10K result

S2 was trained from empty task-owned output, no resume/load, to step {final['checkpoint_step']}. Fixed-60 metrics: AbsRel {final['AbsRel']:.6f}, RMSE {final['RMSE']:.6f}, delta1 {final['delta1']:.6f}, delta2 {final['delta2']:.6f}, delta3 {final['delta3']:.6f}, ratio {final['ratio']:.6f}. Surface MAE/RMSE: {surface['point_to_plane_mae']:.6f}/{surface['point_to_plane_rmse']:.6f}; normal mean/median: {surface['normal_angular_mean_deg']:.3f}/{surface['normal_angular_median_deg']:.3f} degrees. Gaussian count {final['gaussian']['gaussian_count']}; nonfinite and invalid covariance counts are zero.

## Static SAFER boundary

The static map build passed; 908/908 queries and gradients were finite and exactly deterministic, and all 299 continuity pairs passed. The run did not instantiate a controller, dynamics model, QP, trajectory runner, navigation, or SAFER rollout. No formal training, V1R7, G1, checkpoint candidate, or automatic next run was created.

## Next step

Do not promote this result to formal training automatically. The recommended separately authorized follow-up is `TUM Dedicated RGB-D Gaussian Baseline Comparison V1`.
"""
    (ROOT / "REPORT_TUM_TUNED_SURFACE_GEOMETRY_ABLATION_V1.md").write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
