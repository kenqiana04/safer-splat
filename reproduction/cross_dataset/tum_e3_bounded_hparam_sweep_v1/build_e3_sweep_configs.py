"""Build the fixed, non-Cartesian TUM E3 coordinate-sweep registry."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


SOURCE_SHA256 = "96d1fe63019f04824c9dc4949f91d30627344bb8de05cd62ae3d33c2f3944947"
SEED = 20260716


def candidate(name: str, late_lambda: float, lock_step: int, beta_m: float, round_name: str) -> dict[str, object]:
    return {
        "id": name,
        "round": round_name,
        "source_sha256": SOURCE_SHA256,
        "steps": 6000,
        "seed": SEED,
        "candidate": "C3_METRIC_SEED_PLUS_DEPTH",
        "late_depth_hold_start": 3000,
        "late_depth_hold_lambda": late_lambda,
        "refinement_lock_step": lock_step,
        "depth_loss_beta_m": beta_m,
        "depth_loss_lambda": 0.10,
        "depth_unit_scale_factor": 0.0002,
        "depth_accumulation_threshold": 1e-4,
        "fresh_start_only": True,
        "resume_or_load_forbidden": True,
        "formal_training": False,
    }


def registry() -> dict[str, object]:
    round_a = [
        candidate("A_L020_K3000_B010", 0.20, 3000, 0.10, "A_lambda"),
        candidate("A_L030_K3000_B010", 0.30, 3000, 0.10, "A_lambda"),
        candidate("A_L040_K3000_B010", 0.40, 3000, 0.10, "A_lambda"),
        candidate("A_L050_K3000_B010", 0.50, 3000, 0.10, "A_lambda"),
    ]
    return {
        "protocol": "TUM E3 Bounded Hyperparameter Sweep V1",
        "coordinate_search": True,
        "cartesian_grid_forbidden": True,
        "max_unique_6000_candidates": 8,
        "max_independent_10000_candidates": 1,
        "round_a": round_a,
        "round_b_template": [
            candidate("B_LBEST_K2000_B010", -1.0, 2000, 0.10, "B_lock"),
            candidate("B_LBEST_K3000_B010", -1.0, 3000, 0.10, "B_lock"),
            candidate("B_LBEST_K4000_B010", -1.0, 4000, 0.10, "B_lock"),
        ],
        "round_c_template": [
            candidate("C_LBEST_KBEST_B005", -1.0, -1, 0.05, "C_beta"),
            candidate("C_LBEST_KBEST_B010", -1.0, -1, 0.10, "C_beta"),
            candidate("C_LBEST_KBEST_B020", -1.0, -1, 0.20, "C_beta"),
        ],
        "ranking": ["delta1_desc", "AbsRel_asc", "ratio_distance_to_1_asc", "RMSE_asc", "PSNR_desc_tie_only"],
        "selection_screen": {
            "acceptable": {"AbsRel_lte": 0.25, "delta1_gte": 0.75},
            "meaningful_improvement": {"delta1_improvement_gte": 0.04, "AbsRel_worsening_lte": 0.01, "ratio_range": [0.85, 1.15]},
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(registry(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.out)


if __name__ == "__main__":
    main()
