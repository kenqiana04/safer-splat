"""Deterministically rank E3 sweep metrics and apply the preregistered gates."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def metric_value(item: dict, key: str) -> float:
    return float(item[key])


def rank(items: list[dict]) -> list[dict]:
    return sorted(items, key=lambda x: (-metric_value(x, "delta1"), metric_value(x, "AbsRel"), abs(metric_value(x, "median_predicted_over_gt_ratio") - 1.0), metric_value(x, "RMSE"), -float(x.get("rgb_metrics", {}).get("psnr", float("-inf")) or float("-inf"))))


def technical_eligible(item: dict, expected_step: int = 5999) -> tuple[bool, list[str]]:
    reasons = []
    gaussian = item.get("gaussian", {})
    if int(item.get("checkpoint_step", -1)) != expected_step: reasons.append("checkpoint_step")
    if float(item.get("valid_overlap_ratio", 0)) < .90: reasons.append("overlap")
    if int(gaussian.get("nonfinite_gaussian_count", -1)) != 0: reasons.append("nonfinite")
    if int(gaussian.get("invalid_covariance_count", -1)) != 0: reasons.append("invalid_covariance")
    ratio = float(item.get("median_predicted_over_gt_ratio", 0))
    if not .80 <= ratio <= 1.25: reasons.append("ratio")
    return not reasons, reasons


def selection_class(item: dict, baseline: dict) -> tuple[str | None, dict[str, float]]:
    values = {"delta1_improvement": float(item["delta1"]) - float(baseline["delta1"]), "AbsRel_change": float(item["AbsRel"]) - float(baseline["AbsRel"]), "ratio": float(item["median_predicted_over_gt_ratio"])}
    acceptable = float(item["AbsRel"]) <= .25 and float(item["delta1"]) >= .75
    meaningful = values["delta1_improvement"] >= .04 and values["AbsRel_change"] <= .01 and .85 <= values["ratio"] <= 1.15
    return ("ACCEPTABLE_SCREEN" if acceptable else "MEANINGFUL_IMPROVEMENT_SCREEN" if meaningful else None), values


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", type=Path, nargs="+", required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expected-step", type=int, default=5999)
    args = parser.parse_args()
    items = [json.loads(path.read_text(encoding="utf-8")) for path in args.metrics]
    for item, path in zip(items, args.metrics): item["metrics_path"] = str(path)
    ordered = rank(items)
    baseline = json.loads(args.baseline.read_text(encoding="utf-8")) if args.baseline else None
    ranked = []
    for index, item in enumerate(ordered, start=1):
        eligible, reasons = technical_eligible(item, args.expected_step)
        cls, deltas = selection_class(item, baseline) if baseline else (None, {})
        ranked.append({"rank": index, "candidate_id": item["candidate_id"], "technical_eligible": eligible, "technical_rejection_reasons": reasons, "selection_class": cls, "relative_to_baseline": deltas, "metrics": item})
    selected = next((entry for entry in ranked if entry["technical_eligible"] and entry["selection_class"] is not None), None)
    result = {"ranking_contract": ["delta1_desc", "AbsRel_asc", "ratio_distance_to_1_asc", "RMSE_asc", "PSNR_desc_tie_only"], "candidate_count": len(items), "ranked": ranked, "selected": selected, "status": "QUALIFIED_CANDIDATE_AVAILABLE" if selected else "TUM_E3_BOUNDED_SWEEP_NO_QUALIFIED_CANDIDATE"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "selected": selected and selected["candidate_id"]}, sort_keys=True))


if __name__ == "__main__":
    main()
