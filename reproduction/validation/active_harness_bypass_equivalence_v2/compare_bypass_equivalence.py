#!/usr/bin/env python3
"""Exact float32/branch comparison for one frozen REFERENCE/BYPASS pair."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import struct
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def ordered_u32(hex_bits: str) -> int:
    raw = int(hex_bits, 16)
    return 0xFFFFFFFF - raw if raw & 0x80000000 else raw + 0x80000000


def max_ulp(left: list[str] | None, right: list[str] | None) -> int | None:
    if left is None or right is None or len(left) != len(right):
        return None
    return max((abs(ordered_u32(a) - ordered_u32(b)) for a, b in zip(left, right)), default=0)


def max_abs(left: list[float] | None, right: list[float] | None) -> float | None:
    if left is None or right is None or len(left) != len(right):
        return None
    return max((abs(float(a) - float(b)) for a, b in zip(left, right)), default=0.0)


def compare_trial(reference_dir: Path, bypass_dir: Path, trial_id: int) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    reference = read_jsonl(reference_dir / f"trial_{trial_id}.jsonl")
    bypass = read_jsonl(bypass_dir / f"trial_{trial_id}.jsonl")
    reference_summary = read_json(reference_dir / f"trial_{trial_id}_summary.json")
    bypass_summary = read_json(bypass_dir / f"trial_{trial_id}_summary.json")
    rows: list[dict[str, Any]] = []
    first_mismatch = None
    total = max(len(reference), len(bypass))
    for index in range(total):
        ref = reference[index] if index < len(reference) else None
        byp = bypass[index] if index < len(bypass) else None
        if ref is None or byp is None:
            record = {
                "trial_id": trial_id, "step": index, "action_bits_equal": False,
                "selected_executed_equal": False, "state_bits_equal": False, "branch_equal": False,
                "reference_action": None if ref is None else ref.get("reference_action"),
                "bypass_action": None if byp is None else byp.get("executed_action"),
                "max_abs_action_diff": None, "max_abs_state_diff": None,
                "max_action_ulp_diff": None, "max_state_ulp_diff": None,
                "reference_branch": "ROW_MISSING" if ref is None else ref.get("native_termination_reason"),
                "bypass_branch": "ROW_MISSING" if byp is None else byp.get("native_termination_reason"),
            }
        else:
            action_equal = ref.get("reference_action_bits") == byp.get("reference_action_bits")
            supplied_selected = byp.get("supplied_action_bits") == byp.get("selected_action_bits")
            selected_executed = byp.get("selected_action_bits") == byp.get("executed_action_bits") and byp.get("selected_action_id") == byp.get("executed_action_id")
            state_equal = ref.get("post_state_bits") == byp.get("post_state_bits")
            branch_equal = ref.get("native_termination_reason") == byp.get("native_termination_reason") and ref.get("committed") == byp.get("committed") and ref.get("solver_success") == byp.get("solver_success")
            record = {
                "trial_id": trial_id,
                "step": index,
                "action_bits_equal": action_equal,
                "supplied_selected_equal": supplied_selected,
                "selected_executed_equal": selected_executed,
                "state_bits_equal": state_equal,
                "branch_equal": branch_equal,
                "reference_action": ref.get("reference_action"),
                "bypass_action": byp.get("executed_action"),
                "max_abs_action_diff": max_abs(ref.get("reference_action"), byp.get("executed_action")),
                "max_abs_state_diff": max_abs(ref.get("post_state"), byp.get("post_state")),
                "max_action_ulp_diff": max_ulp(ref.get("reference_action_bits"), byp.get("executed_action_bits")),
                "max_state_ulp_diff": max_ulp(ref.get("post_state_bits"), byp.get("post_state_bits")),
                "reference_branch": ref.get("native_termination_reason"),
                "bypass_branch": byp.get("native_termination_reason"),
                "solver_success_equal": ref.get("solver_success") == byp.get("solver_success"),
                "pre_state_bits_equal": ref.get("pre_state_bits") == byp.get("pre_state_bits"),
                "goal_bits_equal": ref.get("goal_bits") == byp.get("goal_bits"),
                "u_des_bits_equal": ref.get("u_des_bits") == byp.get("u_des_bits"),
                "bypass_reason_exact": byp.get("bypass_supervisor_reason") in {"BYPASS_REFERENCE_ACTION_UNCHANGED", None},
                "bypass_commit_exact": byp.get("commit_status") in {"COMMITTED", None},
            }
        rows.append(record)
        required = ("action_bits_equal", "selected_executed_equal", "state_bits_equal", "branch_equal")
        if first_mismatch is None and not all(record.get(key) is True for key in required):
            failed = [key for key in required if record.get(key) is not True]
            if "action_bits_equal" in failed:
                taxonomy = "M_REFERENCE_ACTION_DIVERGENCE"
            elif "selected_executed_equal" in failed:
                taxonomy = "M_BYPASS_ACTION_MUTATION"
            elif "state_bits_equal" in failed:
                taxonomy = "M_PLANT_TRANSITION_DIVERGENCE"
            elif "branch_equal" in failed:
                taxonomy = "M_TERMINATION_BRANCH_DIVERGENCE"
            else:
                taxonomy = "M_UNCLASSIFIED"
            first_mismatch = {"trial_id": trial_id, "step": index, "failed_fields": failed, "taxonomy": taxonomy, "diagnostic": record}

    committed_reference = reference_summary["committed_step_count"]
    committed_bypass = bypass_summary["committed_step_count"]
    termination_match = reference_summary["termination_reason"] == bypass_summary["termination_reason"] and reference_summary["termination_step"] == bypass_summary["termination_step"]
    structural = (
        bypass_summary["active_intervention_call_count"] == 0
        and bypass_summary["token_mutation_count"] == 0
        and bypass_summary["plant_commit_count"] == committed_reference
        and bypass_summary.get("trace_lock") is not None
    )
    verdict = (
        first_mismatch is None and committed_reference == committed_bypass and termination_match and structural
        and all(row.get("pre_state_bits_equal") is True and row.get("goal_bits_equal") is True and row.get("u_des_bits_equal") is True and row.get("solver_success_equal") is True for row in rows)
    )
    summary = {
        "trial_id": trial_id,
        "committed_steps_reference": committed_reference,
        "committed_steps_bypass": committed_bypass,
        "total_compared_rows": len(rows),
        "exact_action_rows": sum(row.get("action_bits_equal") is True for row in rows),
        "exact_state_rows": sum(row.get("state_bits_equal") is True for row in rows),
        "exact_branch_rows": sum(row.get("branch_equal") is True for row in rows),
        "termination_match": termination_match,
        "reference_termination": reference_summary["termination_reason"],
        "bypass_termination": bypass_summary["termination_reason"],
        "active_intervention_count": bypass_summary["active_intervention_call_count"],
        "token_mutation_count": bypass_summary["token_mutation_count"],
        "plant_commit_transparent": bypass_summary["plant_commit_count"] == committed_reference,
        "trace_lock_present": bypass_summary.get("trace_lock") is not None,
        "first_mismatch": first_mismatch,
        "trial_verdict": "PASS" if verdict else "FAIL",
    }
    return summary, rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "trial_id", "step", "action_bits_equal", "selected_executed_equal", "state_bits_equal", "branch_equal",
        "reference_action", "bypass_action", "max_abs_action_diff", "max_abs_state_diff", "max_action_ulp_diff",
        "max_state_ulp_diff", "reference_branch", "bypass_branch",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            cooked = dict(row)
            cooked["reference_action"] = json.dumps(cooked.get("reference_action"), separators=(",", ":"))
            cooked["bypass_action"] = json.dumps(cooked.get("bypass_action"), separators=(",", ":"))
            writer.writerow(cooked)


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference-dir", type=Path, required=True)
    parser.add_argument("--bypass-dir", type=Path, required=True)
    parser.add_argument("--trial-id", type=int, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    args = parser.parse_args()
    summary, rows = compare_trial(args.reference_dir, args.bypass_dir, args.trial_id)
    write_json(args.output_json, summary)
    write_csv(args.output_csv, rows)
    print(json.dumps({"trial_id": args.trial_id, "verdict": summary["trial_verdict"], "first_mismatch": summary["first_mismatch"]}, sort_keys=True), flush=True)
    return 0 if summary["trial_verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
