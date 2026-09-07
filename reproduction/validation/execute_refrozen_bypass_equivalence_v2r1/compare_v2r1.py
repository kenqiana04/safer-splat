#!/usr/bin/env python3
"""Frozen exact comparator for one V2R1 REFERENCE/BYPASS pair."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reproduction.validation.bypass_qa_trace_identity_repair_v2.canonical_trial_identity import make_canonical_trial_identity


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def compare_pair(reference_dir: Path, bypass_dir: Path, trial_id: int) -> dict[str, Any]:
    canonical_id = make_canonical_trial_identity(trial_id).canonical_trial_id
    ref_rows = load_jsonl(reference_dir / f"trial_{trial_id}.jsonl")
    byp_rows = load_jsonl(bypass_dir / f"trial_{trial_id}.jsonl")
    ref_summary = load_json(reference_dir / f"trial_{trial_id}_summary.json")
    byp_summary = load_json(bypass_dir / f"trial_{trial_id}_summary.json")
    mismatches: list[dict[str, Any]] = []
    counters = {
        "M_REFERENCE_TO_SUPPLIED_ACTION_BITS": 0,
        "M_SUPPLIED_TO_SELECTED_ACTION": 0,
        "M_SELECTED_TO_EXECUTED_ACTION": 0,
        "M_POST_STATE_BITS": 0,
        "M_SOLVER_BRANCH": 0,
        "M_TERMINATION_REASON": 0,
        "M_TERMINATION_STEP": 0,
        "M_STEP_COUNT": 0,
        "M_TRACE_INCOMPLETE": 0,
        "M_TRIAL_IDENTITY": 0,
        "M_UNEXPECTED_HARNESS_INTERVENTION": 0,
    }

    def fail(taxonomy: str, cycle: int | None, detail: str) -> None:
        counters[taxonomy] += 1
        if len(mismatches) < 20:
            mismatches.append({"taxonomy": taxonomy, "cycle_index": cycle, "detail": detail})

    if len(ref_rows) != len(byp_rows):
        fail("M_STEP_COUNT", None, f"reference={len(ref_rows)} bypass={len(byp_rows)}")
    total = min(len(ref_rows), len(byp_rows))
    for cycle, (ref, byp) in enumerate(zip(ref_rows, byp_rows)):
        expected_key = {"trial_id": canonical_id, "cycle_index": cycle}
        if ref.get("canonical_trial_id") != canonical_id or byp.get("canonical_trial_id") != canonical_id or ref.get("comparison_join_key") != expected_key or byp.get("comparison_join_key") != expected_key:
            fail("M_TRIAL_IDENTITY", cycle, "canonical id or join key mismatch")
        if ref.get("reference_action_bits") != byp.get("supplied_action_bits"):
            fail("M_REFERENCE_TO_SUPPLIED_ACTION_BITS", cycle, "reference action bits differ from BYPASS supplied bits")
        if byp.get("supplied_action_bits") != byp.get("selected_action_bits") or byp.get("supplied_action_id") != byp.get("selected_action_id"):
            fail("M_SUPPLIED_TO_SELECTED_ACTION", cycle, "BYPASS supplied/selected vector or identity differs")
        if byp.get("selected_action_bits") != byp.get("executed_action_bits") or byp.get("selected_action_id") != byp.get("executed_action_id"):
            fail("M_SELECTED_TO_EXECUTED_ACTION", cycle, "BYPASS selected/executed vector or identity differs")
        if ref.get("post_state_bits") != byp.get("post_state_bits"):
            fail("M_POST_STATE_BITS", cycle, "post-state bits differ")
        if ref.get("solver_success") != byp.get("solver_success") or ref.get("committed") != byp.get("committed") or ref.get("native_termination_reason") != byp.get("native_termination_reason"):
            fail("M_SOLVER_BRANCH", cycle, "typed solver/commit/native branch differs")

    if ref_summary.get("termination_reason") != byp_summary.get("termination_reason"):
        fail("M_TERMINATION_REASON", None, "termination reason differs")
    if ref_summary.get("termination_step") != byp_summary.get("termination_step"):
        fail("M_TERMINATION_STEP", None, "termination step differs")
    if ref_summary.get("committed_step_count") != byp_summary.get("committed_step_count"):
        fail("M_STEP_COUNT", None, "committed step count differs")
    trace_path = bypass_dir / f"trial_{trial_id}_trace_lock.json"
    trace_lock = load_json(trace_path) if trace_path.is_file() else None
    if trace_lock is None or byp_summary.get("trace_lock") is None:
        fail("M_TRACE_INCOMPLETE", None, "finalized BYPASS trace lock missing")
    if int(byp_summary.get("active_intervention_call_count", -1)) != 0 or int(byp_summary.get("token_mutation_count", -1)) != 0:
        fail("M_UNEXPECTED_HARNESS_INTERVENTION", None, "intervention or token mutation count nonzero")

    mismatch_count = sum(counters.values())
    return {
        "schema": "BYPASS_PAIR_EXACT_COMPARISON_V2R1",
        "native_trial_id": trial_id,
        "canonical_trial_id": canonical_id,
        "join_key": ["canonical_trial_id", "cycle_index"],
        "reference_row_count": len(ref_rows),
        "bypass_row_count": len(byp_rows),
        "total_compared_steps": total,
        "mismatch_counts": counters,
        "mismatch_count": mismatch_count,
        "first_mismatch": mismatches[0] if mismatches else None,
        "diagnostic_mismatches": mismatches,
        "termination": {
            "reference_reason": ref_summary.get("termination_reason"),
            "bypass_reason": byp_summary.get("termination_reason"),
            "reference_step": ref_summary.get("termination_step"),
            "bypass_step": byp_summary.get("termination_step"),
        },
        "bypass_trace_lock_present": trace_lock is not None,
        "active_intervention_count": int(byp_summary.get("active_intervention_call_count", 0)),
        "token_mutation_count": int(byp_summary.get("token_mutation_count", 0)),
        "tolerance_used": False,
        "verdict": "PASS" if mismatch_count == 0 and total > 0 else "FAIL",
    }
