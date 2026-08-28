"""Dry-run-only manifest preparation for the separately authorized next task."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from future_equivalence_comparator import COMPARISON_FIELDS, compare_traces


def build_dry_run_manifest() -> dict:
    return {
        "schema_version": "L2_H1_SHADOW_FUTURE_EQUIVALENCE_MANIFEST_V1",
        "dry_run_only": True,
        "observer_off_trace": "NOT_RUN",
        "observer_on_trace": "NOT_RUN",
        "comparison_fields": list(COMPARISON_FIELDS),
        "tolerance_contract_frozen_before_run": True,
        "real_navigation_equivalence_run_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    manifest = build_dry_run_manifest()
    empty = {field: "NOT_RUN" for field in COMPARISON_FIELDS}
    comparison = compare_traces(empty, empty)
    result = {"manifest": manifest, "dry_run_comparator": comparison, "status": "PASS_FUTURE_EQUIVALENCE_DRY_RUN_ONLY"}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
