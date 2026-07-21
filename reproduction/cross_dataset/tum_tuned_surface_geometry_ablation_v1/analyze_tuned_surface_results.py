"""Apply the frozen 6K qualification rules to the four non-formal candidates."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


NAMES = {
    "S0": "S0_TUNED_BASELINE",
    "S1": "S1_SURFACE_ORIENTED_PRIOR",
    "S2": "S2_POINT_TO_PLANE_LOSS",
    "S3": "S3_SURFACE_PRIOR_PLUS_POINT_TO_PLANE",
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    paths = {
        "S0": ("S0_TUNED_BASELINE_6000_corrected", "S0_TUNED_BASELINE_6000_corrected"),
        "S1": ("S1_SURFACE_ORIENTED_PRIOR_6000", "S1_SURFACE_ORIENTED_PRIOR_6000"),
        "S2": ("S2_POINT_TO_PLANE_LOSS_6000", "S2_POINT_TO_PLANE_LOSS_6000"),
        "S3": ("S3_SURFACE_PRIOR_PLUS_POINT_TO_PLANE_6000", "S3_SURFACE_PRIOR_PLUS_POINT_TO_PLANE_6000"),
    }
    data = {}
    for short, (metric_dir, surface_dir) in paths.items():
        data[short] = {
            **load(args.metrics_root / metric_dir / "candidate_metrics.json"),
            **load(args.metrics_root / surface_dir / "surface_metrics.json"),
        }
    baseline = data["S0"]
    candidates = []
    for short in ("S1", "S2", "S3"):
        item = data[short]
        delta1_gain = item["delta1"] - baseline["delta1"]
        absrel_delta = item["AbsRel"] - baseline["AbsRel"]
        plane_relative_improvement = 1.0 - item["point_to_plane_mae"] / baseline["point_to_plane_mae"]
        normal_median_improvement = baseline["normal_angular_median_deg"] - item["normal_angular_median_deg"]
        common = (
            item["checkpoint_step"] == 5999
            and item["overlap"] >= 0.90
            and item["gaussian"]["nonfinite_gaussian_count"] == 0
            and item["gaussian"]["invalid_covariance_count"] == 0
            and 0.80 <= item["ratio"] <= 1.25
        )
        screen_a = item["AbsRel"] <= 0.22 and item["delta1"] >= 0.75
        screen_b = (
            delta1_gain >= 0.025
            and absrel_delta <= 0.005
            and 0.85 <= item["ratio"] <= 1.15
            and (plane_relative_improvement >= 0.05 or normal_median_improvement >= 2.0)
        )
        candidates.append({
            "id": short,
            "candidate": NAMES[short],
            "delta1_gain_vs_s0": delta1_gain,
            "absrel_delta_vs_s0": absrel_delta,
            "point_to_plane_mae_relative_improvement_vs_s0": plane_relative_improvement,
            "normal_median_improvement_deg_vs_s0": normal_median_improvement,
            "common_6k_stability_gate": common,
            "acceptable_depth_screen_pass": screen_a,
            "meaningful_surface_improvement_screen_pass": screen_b,
            "qualified": common and (screen_a or screen_b),
        })
    qualified = [x for x in candidates if x["qualified"]]
    selected = sorted(
        qualified,
        key=lambda x: (
            -data[x["id"]]["delta1"],
            data[x["id"]]["AbsRel"],
            data[x["id"]]["point_to_plane_mae"],
            data[x["id"]]["normal_angular_median_deg"],
            abs(data[x["id"]]["ratio"] - 1.0),
        ),
    )
    out = {
        "formal_training": False,
        "single_seed_interpretation": "SINGLE_SEED_ENGINEERING_ABLATION_NOT_STATISTICAL_SIGNIFICANCE",
        "baseline": {"id": "S0", "candidate": NAMES["S0"], **baseline},
        "candidates": candidates,
        "selected_candidate": selected[0] if selected else None,
        "selection_class": (
            "ACCEPTABLE_DEPTH_SCREEN_PASS" if selected and selected[0]["acceptable_depth_screen_pass"]
            else "MEANINGFUL_SURFACE_IMPROVEMENT_SCREEN_PASS" if selected
            else "NO_QUALIFIED_CANDIDATE"
        ),
        "final_10k_authorized_by_gate": bool(selected),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, sort_keys=True))


if __name__ == "__main__":
    main()
