#!/usr/bin/env python3
"""Stdlib-only static anti-circularity and synthetic-contract checker."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def main() -> int:
    graph = load("evaluation_oracle_dataflow_graph.json")
    authority = load("EVALUATION_ORACLE_AUTHORITY_V2.json")
    tiers = load("EVALUATION_CLAIM_TIERS_V2.json")
    radii = (ROOT / "COLLISION_VS_MARGIN_ORACLE_V2.md").read_text(encoding="utf-8")
    scenarios = load("ORACLE_SYNTHETIC_SCENARIOS_V2.json")
    actual = {(e["source"], e["target"]) for e in graph["edges"]}
    forbidden = {tuple(e) for e in graph["forbidden_edges"]}
    checks = {
        "unique_posthoc_owner": authority["unique_owner"] == "POSTHOC_EVALUATION_ORACLE",
        "feedback_false": authority["ORACLE_FEEDBACK_AUTHORITY"] is False,
        "forbidden_edges_absent": not bool(actual & forbidden),
        "certificate_not_primary_outcome": "CERTIFICATE_STATUS" in authority["primary_outcome_prohibited_inputs"],
        "tier_b_map_relative": tiers["tiers"]["TIER_B_INDEPENDENT_REPRESENTED_MAP_OUTCOME"]["scope_label"] == "REPRESENTED_MAP_RELATIVE",
        "radii_separated": "0.015 m" in radii and "0.025 m" in radii,
        "scenario_count_at_least_20": scenarios["count"] >= 20,
        "scenario_ids_unique": len({s["id"] for s in scenarios["scenarios"]}) == scenarios["count"],
        "timeout_success_rejected": any(s["fixture"] == "MOVING_TIMEOUT_NOT_AT_GOAL" and s["expected"] == "TIMEOUT_NOT_GOAL_REACHED" for s in scenarios["scenarios"]),
        "swept_crossing_detected": any(s["fixture"] == "ENDPOINT_SAFE_SEGMENT_CROSSES" and s["expected"] == "EVAL_VIOLATION" for s in scenarios["scenarios"]),
    }
    result = {"status": "PASS_EVALUATION_ORACLE_ANTI_CIRCULARITY_CHECK" if all(checks.values()) else "FAIL_EVALUATION_ORACLE_ANTI_CIRCULARITY_CHECK", "checks": checks, "forbidden_edge_hits": [list(x) for x in sorted(actual & forbidden)], "synthetic_scenarios_checked": scenarios["count"]}
    (ROOT / "evaluation_oracle_independence_check.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["status"])
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

