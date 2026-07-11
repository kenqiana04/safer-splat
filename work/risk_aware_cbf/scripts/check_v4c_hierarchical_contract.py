#!/usr/bin/env python3
"""Check Stage-A constraints and exact original full-search fallback semantics."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import random
from pathlib import Path
from typing import Any

import numpy as np
import torch

import run_v4c_hstep_predictive_recovery as v4c
from run_v4c_hierarchical_paired_audit import build_initial_context, build_preregistered_args, load_runtime
from v4c_hierarchical_candidate_evaluator import build_stage_a_args, evaluate_hierarchical


def tensor_digest(value: torch.Tensor) -> str:
    return hashlib.sha256(value.detach().cpu().contiguous().numpy().tobytes()).hexdigest()


def source_digest(candidates: list[Any]) -> str:
    return hashlib.sha256("\n".join(str(candidate.source) for candidate in candidates).encode("utf-8")).hexdigest()


def rng_snapshot() -> tuple[object, tuple[Any, ...], torch.Tensor, list[torch.Tensor] | None]:
    cuda = torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else None
    return random.getstate(), np.random.get_state(), torch.random.get_rng_state().clone(), cuda


def rng_equal(before: tuple[object, tuple[Any, ...], torch.Tensor, list[torch.Tensor] | None], after: tuple[object, tuple[Any, ...], torch.Tensor, list[torch.Tensor] | None]) -> bool:
    py_ok = before[0] == after[0]
    np_ok = before[1][0] == after[1][0] and np.array_equal(before[1][1], after[1][1]) and before[1][2:] == after[1][2:]
    torch_ok = bool(torch.equal(before[2], after[2]))
    cuda_ok = (before[3] is None and after[3] is None) or (
        before[3] is not None and after[3] is not None and len(before[3]) == len(after[3])
        and all(torch.equal(left, right) for left, right in zip(before[3], after[3]))
    )
    return bool(py_ok and np_ok and torch_ok and cuda_ok)


def add(rows: list[dict[str, Any]], check_id: str, passed: bool, critical: bool, notes: str) -> None:
    rows.append({"check_id": check_id, "passed": bool(passed), "critical": bool(critical), "notes": notes})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    original_args = build_preregistered_args(args.output_dir, 14)
    runtime = load_runtime(original_args)
    context = build_initial_context(runtime, 14)
    x_before = context["x"].detach().clone()
    args_before = copy.deepcopy(vars(original_args))
    stage_a_args = build_stage_a_args(original_args)
    stage_a_candidates = v4c.generate_sequences(
        args=stage_a_args, trial=14, step=0, gsplat=runtime.gsplat,
        scene_cfg=runtime.scene_cfg, **context,
    )
    stage_a_result = v4c.evaluate_sequences(
        args=stage_a_args, scene="flight", method=original_args.method, trial=14, step=0,
        x=context["x"], goal=context["goal"], u_base=context["u_base"],
        u_prev=context["u_prev"], candidates=stage_a_candidates, gsplat=runtime.gsplat,
        scene_cfg=runtime.scene_cfg,
    )
    rows: list[dict[str, Any]] = []
    add(rows, "stage_a_no_random", all(not str(c.source).startswith("random_around_base_") for c in stage_a_candidates), True, "Stage A generated with num_sequences=0.")
    add(rows, "stage_a_no_cem", all(not str(c.source).startswith("cem_") for c in stage_a_candidates), True, "Stage A generated with use_cem=False.")
    add(rows, "stage_a_uses_original_evaluate", stage_a_result[0].__class__ is v4c.SequenceCandidate, True, "Returned object is from original evaluate_sequences.")
    add(rows, "state_unchanged_after_stage_a", torch.equal(x_before, context["x"]), True, "Original rollout clones input state.")
    add(rows, "original_args_unchanged_after_stage_a", args_before == vars(original_args), True, "Stage A uses a deep-copied Namespace.")
    direct_rng_before = rng_snapshot()
    direct_candidates = v4c.generate_sequences(
        args=original_args, trial=14, step=0, gsplat=runtime.gsplat,
        scene_cfg=runtime.scene_cfg, **context,
    )
    direct_result = v4c.evaluate_sequences(
        args=original_args, scene="flight", method=original_args.method, trial=14, step=0,
        x=context["x"], goal=context["goal"], u_base=context["u_base"],
        u_prev=context["u_prev"], candidates=direct_candidates, gsplat=runtime.gsplat,
        scene_cfg=runtime.scene_cfg,
    )
    direct_rng_after = rng_snapshot()
    forced_rng_before = rng_snapshot()
    forced = evaluate_hierarchical(
        original_args=original_args, scene="flight", method=original_args.method, trial=14, step=0,
        x=context["x"], goal=context["goal"], u_base=context["u_base"], u_nom=context["u_nom"],
        u_prev=context["u_prev"], gsplat=runtime.gsplat, scene_cfg=runtime.scene_cfg,
        stage_a_candidates=[], generate_fn=v4c.generate_sequences, evaluate_fn=v4c.evaluate_sequences,
    )
    forced_rng_after = rng_snapshot()
    forced_sources = hashlib.sha256("\n".join(forced.stage_b_sources).encode("utf-8")).hexdigest()
    add(rows, "stage_b_source_list", source_digest(direct_candidates) == forced_sources, True, "Stage-B uses the untouched original full generator.")
    add(rows, "stage_b_selected_source", str(direct_result[0].source) == forced.selected_source, True, "Selected source matches direct original full evaluation.")
    add(rows, "stage_b_selected_first_control", tensor_digest(direct_result[1]) == tensor_digest(forced.selected_first_control), True, "First control matches exactly.")
    add(rows, "stage_b_h_sequence", direct_result[2] == forced.selected_hs, True, "Horizon h sequence matches exactly.")
    add(rows, "stage_b_min_h", abs(float(direct_result[3]) - forced.selected_min_h) <= 1e-12, True, "Selected horizon minimum h matches.")
    add(rows, "stage_b_success_failed", bool(direct_result[4]) == forced.recovery_success and bool(direct_result[5]) == forced.recovery_failed, True, "Success and failure flags match.")
    add(rows, "rng_unchanged_direct", rng_equal(direct_rng_before, direct_rng_after), True, "Original local default RNG does not alter global RNG state.")
    add(rows, "rng_unchanged_stage_b", rng_equal(forced_rng_before, forced_rng_after), True, "Forced Stage-B full generation preserves global RNG state.")
    add(rows, "state_unchanged_after_stage_b", torch.equal(x_before, context["x"]), True, "No formal state propagation occurs in contract check.")
    add(rows, "original_args_unchanged_after_stage_b", args_before == vars(original_args), True, "Full args are not mutated.")
    add(rows, "no_formal_command_execution", True, True, "Check calls only generation/evaluation, never run_trial.")
    with (args.output_dir / "contract_check.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check_id", "passed", "critical", "notes"])
        writer.writeheader()
        writer.writerows(rows)
    failures = [row for row in rows if row["critical"] and not row["passed"]]
    print(f"contract_checks={len(rows)} critical_failures={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
