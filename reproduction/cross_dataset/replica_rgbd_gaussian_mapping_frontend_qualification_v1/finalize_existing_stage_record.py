#!/usr/bin/env python3
"""Repair only the manifest/summary record for an already-rendered terminal result.

This deliberately never loads a map, images, renderer, CUDA, or frontend code.
It is therefore safe for the one bookkeeping repair after the first SplaTAM
smoke evaluator wrote its immutable result before hitting an argument-name bug.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from _common import ROOT, atomic_json, load_json, mark_not_authorized, update_stage


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("frontend", choices=("splatam", "gaussian_slam"))
    parser.add_argument("--stage", required=True, choices=("smoke", "pilot"))
    args = parser.parse_args()
    result_path = ROOT / "geometry_evaluation" / f"{args.frontend}_{'smoke_' if args.stage == 'smoke' else ''}geometry_evaluation.json"
    result = load_json(result_path)
    status = result.get("status")
    if args.stage != "smoke" or status not in {"SMOKE_RENDER_FAILURE", "SMOKE_PASS"}:
        raise SystemExit(f"refusing non-smoke/non-terminal record repair: {result_path} -> {status}")
    summary_path = ROOT / args.frontend / "smoke_summary.json"
    summary = load_json(summary_path)
    summary["status"] = status
    summary["shared_holdout_render"] = str(result_path)
    summary["record_repair_only"] = True
    summary["record_repair_reason"] = "shared evaluation result existed before update_stage keyword collision; no render or map rerun"
    atomic_json(summary_path, summary)
    update_stage(args.frontend, "SMOKE", "TERMINAL_SCIENTIFIC_RESULT", result_status=status, record_repair_only=True)
    if status != "SMOKE_PASS":
        mark_not_authorized(args.frontend, "SMOKE")
    print(status)


if __name__ == "__main__":
    main()
