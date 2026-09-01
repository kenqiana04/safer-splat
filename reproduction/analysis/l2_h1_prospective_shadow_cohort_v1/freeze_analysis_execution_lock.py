#!/usr/bin/env python3
"""Freeze core analysis code before the first formal status is read."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from analysis_common import atomic_write_json, file_sha256, semantic_sha256

CORE = (
    "analysis_common.py", "build_formal_analysis_table.py", "analyze_primary_endpoint.py",
    "bootstrap_primary_by_trial.py", "analyze_secondary_endpoints.py", "run_formal_analysis.py", "validate_formal_analysis_v1.py",
)


def combined_lock_sha(value: dict[str, Any]) -> str:
    return semantic_sha256(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--analysis-contract", type=Path, required=True)
    parser.add_argument("--claim-contract", type=Path, required=True)
    parser.add_argument("--analysis-contract-sha256")
    parser.add_argument("--claim-contract-sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = {
        "schema_version": "L2_H1_FORMAL_ANALYSIS_EXECUTION_LOCK_V1", "created_before_outcome_reveal": True,
        "real_outcome_rows_read": 0, "analysis_contract_sha256": args.analysis_contract_sha256 or file_sha256(args.analysis_contract),
        "claim_contract_sha256": args.claim_contract_sha256 or file_sha256(args.claim_contract),
        "core_script_sha256": {name: file_sha256(args.task_dir / name) for name in CORE},
    }
    payload["combined_analysis_execution_sha256"] = combined_lock_sha(payload)
    atomic_write_json(args.output, payload)
    print(payload["combined_analysis_execution_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
