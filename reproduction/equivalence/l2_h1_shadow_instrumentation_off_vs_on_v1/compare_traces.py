#!/usr/bin/env python3
"""Exact paired comparison for uniform primary traces."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from canonical_trace_hash import PRIMARY_STEP_FIELDS, primary_trace, semantic_sha256
from find_first_divergence import first_divergence


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def field_equal(left: dict, right: dict, field: str) -> bool:
    if field in {"trial_id", "seed", "map_authority_id"}:
        return left.get(field) == right.get(field)
    return [step.get(field) for step in left["steps"]] == [step.get(field) for step in right["steps"]]


def compare(left: dict, right: dict, pair_label: str) -> dict:
    divergence = first_divergence(left, right, pair_label=pair_label)
    fields = {
        field: field_equal(left, right, field)
        for field in ("trial_id", "seed", "map_authority_id", *PRIMARY_STEP_FIELDS)
    }
    return {
        "schema_version": "L2_H1_SHADOW_EXACT_TRACE_COMPARISON_V1",
        "pair": pair_label,
        "trial_id": left.get("trial_id"),
        "left_run_id": left.get("run_id"),
        "right_run_id": right.get("run_id"),
        "left_trace_hash": semantic_sha256(primary_trace(left)),
        "right_trace_hash": semantic_sha256(primary_trace(right)),
        "left_step_count": len(left.get("steps", [])),
        "right_step_count": len(right.get("steps", [])),
        "field_exact": fields,
        "exact_match": divergence is None,
        "first_divergence": divergence,
        "numeric_tolerance": None,
        "post_hoc_tolerance_change": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("left", type=Path)
    parser.add_argument("right", type=Path)
    parser.add_argument("--pair", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(load(args.left), load(args.right), args.pair)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("EXACT_MATCH" if result["exact_match"] else "FIRST_DIVERGENCE")
    return 0 if result["exact_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
