#!/usr/bin/env python3
"""Cross-check direct float64 coverage against fresh Habitat measurements."""
from __future__ import annotations

import math
import numpy as np

from _v3_common import ROOT, atomic_json, ensure_server_root, load_json


def main() -> None:
    ensure_server_root()
    independent = load_json(ROOT / "independent_coverage" / "independent_candidate_coverage_summary.json")
    habitat = load_json(ROOT / "habitat_preprobe" / "habitat_preprobe_summary.json")
    indexed = {item["frame_id"]: item for item in independent["views"]}
    rows = []
    for result in habitat["results"]:
        for view in result.get("views", []):
            direct = indexed[view["frame_id"]]
            direct_pass = direct["status"] == "INDEPENDENT_VIEW_COVERAGE_PASS"
            habitat_pass = view["status"] == "HABITAT_VIEW_PREQUALIFICATION_PASS"
            category = "BOTH_PASS" if direct_pass and habitat_pass else "INDEPENDENT_PASS_HABITAT_FAIL" if direct_pass else "INDEPENDENT_FAIL_HABITAT_PASS" if habitat_pass else "BOTH_FAIL"
            rows.append({"frame_id": view["frame_id"], "candidate_id": view["candidate_id"], "independent_valid_hit_fraction": direct["valid_near_far_hit_fraction"], "habitat_depth_positive_fraction": view["metrics"]["depth_positive_fraction"], "independent_status": direct["status"], "habitat_status": view["status"], "category": category})
    mismatch = [row for row in rows if row["category"] == "INDEPENDENT_PASS_HABITAT_FAIL"]
    correlations = None
    if len(rows) > 1:
        a, b = np.asarray([row["independent_valid_hit_fraction"] for row in rows]), np.asarray([row["habitat_depth_positive_fraction"] for row in rows])
        correlations = float(np.corrcoef(a, b)[0, 1]) if float(a.std()) > 0 and float(b.std()) > 0 else None
    mismatch_fraction = len(mismatch) / len(rows) if rows else 1.0
    status = "PASS_REPLICA_V3_COVERAGE_CROSS_VALIDATION" if mismatch_fraction <= .05 else "BLOCKED_BY_REPLICA_V3_INDEPENDENT_HABITAT_COVERAGE_CONTRADICTION"
    payload = {"status": status, "view_count": len(rows), "both_pass_count": sum(row["category"] == "BOTH_PASS" for row in rows), "independent_pass_habitat_fail_count": len(mismatch), "independent_pass_habitat_fail_fraction": mismatch_fraction, "independent_fail_habitat_pass_count": sum(row["category"] == "INDEPENDENT_FAIL_HABITAT_PASS" for row in rows), "both_fail_count": sum(row["category"] == "BOTH_FAIL" for row in rows), "coverage_fraction_pearson_correlation": correlations, "clear_explanation": "none_required_when_threshold_not_exceeded" if mismatch_fraction <= .05 else "unexplained", "views": rows}
    atomic_json(ROOT / "habitat_preprobe" / "coverage_cross_validation_summary.json", payload)
    pool = [result for result in habitat["results"] if result["status"] == "HABITAT_LOCATION_TRIPLET_PASS"]
    atomic_json(ROOT / "qualified_location_pool" / "qualified_location_pool_summary.json", {"status": "PASS_HABITAT_TRIPLET_QUALIFIED_POOL" if len(pool) >= 120 else "BLOCKED_BY_REPLICA_V3_INSUFFICIENT_HABITAT_QUALIFIED_LOCATION_POOL", "qualified_location_count": len(pool), "locations": [{"candidate_id": result["candidate_id"], "location_hash": result["location_hash"], "source_navmesh_position": result["source_navmesh_position"]} for result in pool]})
    if status != "PASS_REPLICA_V3_COVERAGE_CROSS_VALIDATION":
        raise SystemExit(status)


if __name__ == "__main__":
    main()
