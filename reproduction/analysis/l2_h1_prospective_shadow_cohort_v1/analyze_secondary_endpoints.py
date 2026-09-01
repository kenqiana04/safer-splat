#!/usr/bin/env python3
"""Compute only the pre-registered secondary endpoints."""

from __future__ import annotations

from collections import Counter
from typing import Any

from analysis_common import percentile


def per_trial_rows(rows: list[dict[str, Any]], intended_by_trial: dict[int, int]) -> list[dict[str, Any]]:
    output = []
    for trial_id in range(100):
        selected = [row for row in rows if int(row["trial_id"]) == trial_id and row.get("primary_eligible")]
        n_fail = sum(row["l2_status"] == "FAIL" for row in selected)
        n_unknown = sum(row["l2_status"] == "UNKNOWN" for row in selected)
        output.append({"trial_id": trial_id, "N_intended": intended_by_trial[trial_id], "N_primary": len(selected), "N_FAIL": n_fail,
                       "N_UNKNOWN": n_unknown, "primary_rate_if_denominator_positive": n_fail / len(selected) if selected else None})
    return output


def summarize_per_trial(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rates = [row["primary_rate_if_denominator_positive"] for row in rows if row["primary_rate_if_denominator_positive"] is not None]
    return {
        "denominator_positive_trial_count": len(rates), "median": percentile(rates, 0.5), "q1": percentile(rates, 0.25),
        "q3": percentile(rates, 0.75), "IQR": (percentile(rates, 0.75) - percentile(rates, 0.25)) if rates else None,
        "min": min(rates) if rates else None, "max": max(rates) if rates else None,
        "trials_with_at_least_1_FAIL": sum(row["N_FAIL"] > 0 for row in rows),
        "trials_with_at_least_1_UNKNOWN": sum(row["N_UNKNOWN"] > 0 for row in rows),
    }


def summarize_backend(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    eligible = [row for row in rows if row.get("primary_eligible")]
    counts = Counter(row["backend_class"] for row in eligible)
    unknown = Counter(row["backend_class"] for row in eligible if row["l2_status"] == "UNKNOWN")
    return [{"backend_class": key, "count": counts[key], "share": counts[key] / len(eligible) if eligible else None,
             "N_UNKNOWN": unknown[key]} for key in sorted(counts)]


def summarize_multi_candidate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if int(row.get("native_candidate_group_size", 1)) > 1:
            groups.setdefault(str(row["candidate_group_id"]), []).append(row)
    if not groups:
        return {"status": "MULTI_CANDIDATE_ANALYSIS_NOT_ESTIMABLE", "N_multi_candidate_groups": 0,
                "N_groups_status_disagreement": 0, "N_groups_PASS_AND_FAIL": 0, "multi_candidate_prevalence": 0.0,
                "synthetic_candidate_generation_count": 0, "u_des_is_native_alternative": False}
    disagreement = pass_fail = fully_evaluated = 0
    for members in groups.values():
        statuses = [item.get("l2_status") for row in members for item in row.get("native_sibling_candidates", []) if item.get("l2_status") in {"PASS", "FAIL", "UNKNOWN"}]
        statuses.extend(row["l2_status"] for row in members if row.get("primary_eligible"))
        if statuses:
            fully_evaluated += 1
            disagreement += len(set(statuses)) > 1
            pass_fail += "PASS" in statuses and "FAIL" in statuses
    return {"status": "ESTIMABLE" if fully_evaluated == len(groups) else "NATIVE_SIBLING_STATUS_NOT_FULLY_OBSERVED",
            "N_multi_candidate_groups": len(groups), "N_groups_all_candidates_evaluated": fully_evaluated,
            "N_groups_status_disagreement": disagreement, "N_groups_PASS_AND_FAIL": pass_fail,
            "multi_candidate_prevalence": len(groups) / len(rows) if rows else None,
            "synthetic_candidate_generation_count": 0, "u_des_is_native_alternative": False}


def summarize_selected_nonselected(rows: list[dict[str, Any]]) -> dict[str, Any]:
    selected = Counter(row["l2_status"] for row in rows if row.get("primary_eligible"))
    siblings = [item for row in rows for item in row.get("native_sibling_candidates", []) if item.get("l2_status") in {"PASS", "FAIL", "UNKNOWN"}]
    nonselected = Counter(item["l2_status"] for item in siblings)
    return {"status": "DESCRIPTIVE_MECHANISM_ONLY" if siblings else "NOT_ESTIMABLE_NO_EVALUATED_NATIVE_NONSELECTED",
            "selected_counts": {key: selected[key] for key in ("PASS", "FAIL", "UNKNOWN")},
            "native_nonselected_counts": {key: nonselected[key] for key in ("PASS", "FAIL", "UNKNOWN")},
            "native_nonselected_evaluated_count": len(siblings), "causal_claim": False, "selection_efficacy_claim": False}

