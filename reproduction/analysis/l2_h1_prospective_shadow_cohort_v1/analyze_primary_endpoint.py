#!/usr/bin/env python3
"""Compute and immutably lock the pre-registered primary endpoint."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
from typing import Any

from analysis_common import TRI_STATES, atomic_write_json, file_sha256, iter_jsonl, semantic_sha256


def primary_summary(rows: list[dict[str, Any]], n_intended: int) -> dict[str, Any]:
    eligible = [row for row in rows if row.get("primary_eligible") is True]
    counts = Counter(row["l2_status"] for row in eligible)
    n_primary = len(eligible)
    n_pass, n_fail, n_unknown = (counts.get(status, 0) for status in TRI_STATES)
    algebra = n_primary == n_pass + n_fail + n_unknown
    if not algebra:
        raise RuntimeError("primary tri-state algebra mismatch")
    known = n_pass + n_fail
    reasons = Counter(reason for row in rows if not row.get("primary_eligible") for reason in row.get("primary_ineligibility_reasons", []))
    return {
        "schema_version": "L2_H1_FORMAL_PRIMARY_RESULT_V1", "N_intended_control_steps": n_intended,
        "N_primary": n_primary, "N_primary_eligible": n_primary, "N_primary_ineligible": len(rows) - n_primary,
        "primary_eligibility_reason_counts": dict(sorted(reasons.items())), "N_L2_PASS": n_pass, "N_L2_FAIL": n_fail, "N_L2_UNKNOWN": n_unknown,
        "tri_state_algebra_pass": algebra, "prospective_future_safety_signal_rate": n_fail / n_primary if n_primary else None,
        "L2_UNKNOWN_RATE": n_unknown / n_primary if n_primary else None,
        "known_status_sensitivity": n_fail / known if known else None,
        "known_status_sensitivity_label": "SECONDARY_SENSITIVITY_ONLY",
    }


def lock_payload(primary: dict[str, Any], **identities: str) -> dict[str, Any]:
    return {
        "schema_version": "L2_H1_FORMAL_PRIMARY_RESULT_LOCK_V1", "primary_result": primary,
        "primary_result_sha256": semantic_sha256(primary), **identities,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--table", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lock-output", type=Path, required=True)
    parser.add_argument("--protocol-sha", required=True)
    parser.add_argument("--collection-lock-sha", required=True)
    parser.add_argument("--analysis-execution-lock-sha", required=True)
    parser.add_argument("--input-commitment-sha", required=True)
    args = parser.parse_args()
    primary = primary_summary(list(iter_jsonl(args.table)), 14122)
    atomic_write_json(args.output, primary)
    locked = lock_payload(primary, protocol_sha256=args.protocol_sha, collection_lock_sha256=args.collection_lock_sha,
                          analysis_execution_lock_sha256=args.analysis_execution_lock_sha, input_commitment_sha256=args.input_commitment_sha)
    locked["primary_result_file_sha256"] = file_sha256(args.output)
    atomic_write_json(args.lock_output, locked)
    print(f"primary_result_lock_sha256={file_sha256(args.lock_output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

