#!/usr/bin/env python3
"""Classify source pairs without ever pooling incompatible outcomes."""
from __future__ import annotations

from itertools import combinations

from evidence_common import TASK, load_json, write_csv

FIELDS = ["evidence_id_a", "evidence_id_b", "classification", "rationale"]


def classify(a: dict, b: dict) -> tuple[str, str]:
    pair = {a["evidence_id"], b["evidence_id"]}
    if pair == {"E13_V4C_H3", "E14_V4C_TUNED_H2"}:
        return "CONFIGURATION_SPECIFIC", "same dense-flight family but different horizon/candidate configuration; compare runtime descriptively only"
    if "E15_HCE_HELDOUT" in pair and ("E13_V4C_H3" in pair or "E14_V4C_TUNED_H2" in pair):
        return "COHORT_OVERLAP_RISK", "HCE is a selected activated held-out cohort from the same broad dense-flight setting"
    if a["dataset"] == b["dataset"] and a["scene"] == b["scene"] and a["map_role"] == b["map_role"]:
        return "CONFIGURATION_SPECIFIC", "same named setting but module/configuration/result-type differ"
    if a["map_role"] != b["map_role"]:
        return "MAP_SPECIFIC", "different map role; effects cannot be numerically pooled"
    if a["dataset"] == b["dataset"]:
        return "COMPLEMENTARY_NOT_POOLABLE", "same dataset but different scene/cohort or protocol"
    return "NOT_COMPARABLE", "different dataset, map, cohort, and execution contract"


def main() -> int:
    sources = load_json("source_inventory/source_inventory.json")["sources"]
    rows = []
    for a, b in combinations(sources, 2):
        status, rationale = classify(a, b)
        rows.append({"evidence_id_a": a["evidence_id"], "evidence_id_b": b["evidence_id"], "classification": status, "rationale": rationale})
    write_csv(TASK / "config_compatibility/configuration_compatibility_matrix.csv", rows, FIELDS)
    print(f"PASS_CONFIGURATION_COMPATIBILITY pairs={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
