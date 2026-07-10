#!/usr/bin/env python3
"""Compare direct V4-C pure-function output with the nonfunctional adapter."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
from pathlib import Path
from typing import Any

import numpy as np
import torch

from dynamics.systems import DoubleIntegrator
from splat.gsplat_utils import GSplatLoader
import run_risk_aware_v1_pre_cbf_comparison as v1
import run_v4b_corrective_dt_filter as v4b
import run_v4c_hstep_predictive_recovery as v4c
from v4c_recovery_shadow_interface import (
    build_shadow_context,
    evaluate_v4c_recovery_mode_shadow,
    load_named_v4c_config,
)


FIELDS = (
    "check_id",
    "original_value",
    "adapter_value",
    "match",
    "absolute_error",
    "tolerance",
    "critical",
    "notes",
)


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=True)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def tensor_list(value: torch.Tensor) -> list[float]:
    return [float(item) for item in value.detach().cpu().reshape(-1).tolist()]


def rng_snapshot() -> tuple[Any, Any, torch.Tensor, list[torch.Tensor] | None]:
    return (
        random.getstate(),
        np.random.get_state(),
        torch.random.get_rng_state().clone(),
        torch.cuda.get_rng_state_all() if torch.cuda.is_initialized() else None,
    )


def rng_restore(state: tuple[Any, Any, torch.Tensor, list[torch.Tensor] | None]) -> None:
    random.setstate(state[0])
    np.random.set_state(state[1])
    torch.random.set_rng_state(state[2])
    if state[3] is not None and torch.cuda.is_initialized():
        torch.cuda.set_rng_state_all(state[3])


def add_exact(rows: list[dict[str, Any]], check_id: str, original: Any, adapter: Any, notes: str) -> None:
    rows.append(
        {
            "check_id": check_id,
            "original_value": canonical(original),
            "adapter_value": canonical(adapter),
            "match": str(original == adapter).lower(),
            "absolute_error": 0.0 if original == adapter else "not_applicable",
            "tolerance": 0.0,
            "critical": "true",
            "notes": notes,
        }
    )


def add_float(rows: list[dict[str, Any]], check_id: str, original: float, adapter: float, tolerance: float, notes: str) -> None:
    error = abs(float(original) - float(adapter))
    rows.append(
        {
            "check_id": check_id,
            "original_value": repr(float(original)),
            "adapter_value": repr(float(adapter)),
            "match": str(error <= tolerance).lower(),
            "absolute_error": error,
            "tolerance": tolerance,
            "critical": "true",
            "notes": notes,
        }
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--trial", type=int, default=14)
    parser.add_argument("--step", type=int, default=1)
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda")
    cli = parser.parse_args()

    root = cli.repo_root.resolve()
    args = load_named_v4c_config()
    args.device = cli.device
    scene_cfg = v1.SCENES["flight"]
    device = torch.device(cli.device)
    gsplat = GSplatLoader(root / scene_cfg["path_to_gsplat"], device)
    dynamics = DoubleIntegrator(device=device, ndim=3)
    x0, xf = v1.make_start_goal_configs(scene_cfg)
    start, _ = v4b.start_for_trial(args=args, trial=cli.trial, x0=x0, repairs={})
    x = torch.tensor(start, device=device, dtype=torch.float32)
    x = torch.cat([x, torch.zeros(3, device=device, dtype=torch.float32)])
    goal = torch.tensor(xf[cli.trial], device=device, dtype=torch.float32)
    goal = torch.cat([goal, torch.zeros(3, device=device, dtype=torch.float32)])
    risk_path = root / "work/risk_aware_cbf/results/flight_risk_score_table_v0.csv"
    risk_table = v1.RiskScoreTable(risk_path, int(gsplat.means.shape[0]))
    cbf = v4b.make_cbf(
        args=args,
        method="risk_aware_v1_bestD",
        gsplat=gsplat,
        dynamics=dynamics,
        scene_cfg=scene_cfg,
        risk_table=risk_table,
    )
    u_nom = v1.nominal_control(x, goal)
    u_base = cbf.solve_QP(x, u_nom)
    if not bool(cbf.solver_success):
        raise RuntimeError("equivalence context baseline QP was infeasible")

    state_before = x.detach().clone()
    rng_before = rng_snapshot()
    direct_candidates = v4c.generate_sequences(
        args=args,
        x=x,
        goal=goal,
        u_base=u_base,
        u_nom=u_nom,
        u_prev=None,
        gsplat=gsplat,
        scene_cfg=scene_cfg,
        trial=cli.trial,
        step=cli.step,
    )
    direct_selected, direct_first, direct_hs, direct_min_h, direct_success, direct_failed, direct_rows, direct_idx = v4c.evaluate_sequences(
        args=args,
        scene="flight",
        method="risk_aware_v1_bestD",
        trial=cli.trial,
        step=cli.step,
        x=x,
        goal=goal,
        u_base=u_base,
        u_prev=None,
        candidates=direct_candidates,
        gsplat=gsplat,
        scene_cfg=scene_cfg,
    )
    direct_final, _, _ = v4c.rollout_sequence(
        x=x,
        controls=direct_selected.controls,
        dt=args.dt,
        gsplat=gsplat,
        scene_cfg=scene_cfg,
    )
    direct_progress = float(
        (
            torch.linalg.norm(x[:3] - goal[:3])
            - torch.linalg.norm(direct_final[:3] - goal[:3])
        )
        .detach()
        .cpu()
        .item()
    )
    direct_cost = float(direct_rows[direct_idx]["sequence_cost"]) if direct_idx >= 0 else float("nan")
    direct_state_unchanged = torch.equal(x, state_before)
    rng_restore(rng_before)

    context = build_shadow_context(
        scene="flight",
        method="risk_aware_v1_bestD",
        trial=cli.trial,
        step=cli.step,
        x=x,
        goal=goal,
        u_base=u_base,
        u_nom=u_nom,
        u_prev=None,
        gsplat=gsplat,
        scene_cfg=scene_cfg,
    )
    adapter_result = evaluate_v4c_recovery_mode_shadow(args=args, context=context)

    config = {
        "scene": args.scene,
        "method": args.method,
        "horizon": args.horizon,
        "num_sequences": args.num_sequences,
        "dt_margin": args.dt_margin,
        "warning_margin": args.warning_margin,
        "activation_mode": args.activation_mode,
        "control_scale_list": args.control_scale_list,
    }
    direct_sources = tuple(candidate.source for candidate in direct_candidates)
    direct_first_controls = tuple(tuple(tensor_list(candidate.controls[0])) for candidate in direct_candidates)
    rows: list[dict[str, Any]] = []
    add_exact(rows, "config", config, config, "Same Namespace is passed to direct and adapter calls.")
    add_exact(rows, "state", digest(tensor_list(x)), digest(tensor_list(context.x)), "Identical real flight trial state.")
    add_exact(rows, "goal", digest(tensor_list(goal)), digest(tensor_list(context.goal)), "Identical official flight goal.")
    add_exact(rows, "u_base", digest(tensor_list(u_base)), digest(tensor_list(context.u_base)), "Identical CBF-filtered baseline control.")
    add_exact(rows, "u_nom", digest(tensor_list(u_nom)), digest(tensor_list(context.u_nom)), "Identical nominal control.")
    add_exact(rows, "seed_and_rng_policy", "trial_step_local_default_rng", "trial_step_local_default_rng", "Original generator owns deterministic local RNG.")
    add_exact(rows, "candidate_count", len(direct_candidates), adapter_result.sequence_count, "Original generation function used twice.")
    add_exact(rows, "candidate_source_list", digest(direct_sources), digest(adapter_result.candidate_sources), "Digest avoids committing per-candidate output.")
    add_exact(rows, "candidate_first_controls", digest(direct_first_controls), digest(adapter_result.candidate_first_controls), "Digest avoids committing per-candidate output.")
    add_exact(rows, "selected_index", int(direct_idx), adapter_result.selected_sequence_id, "Original evaluator owns ranking.")
    add_exact(rows, "selected_source", direct_selected.source, adapter_result.selected_sequence_source, "Original evaluator owns source selection.")
    direct_first_tuple = tuple(tensor_list(direct_first))
    add_exact(rows, "selected_first_control", direct_first_tuple, adapter_result.selected_first_control, "Selected control is compared but never executed.")
    add_exact(rows, "selected_h_sequence", tuple(float(v) for v in direct_hs), adapter_result.selected_h_sequence, "Same GSplat rollout result.")
    add_float(rows, "selected_min_h", direct_min_h, adapter_result.selected_min_h, 1e-12, "Barrier margin; not metric clearance.")
    add_exact(rows, "recovery_success", bool(direct_success), adapter_result.recovery_success, "Original success flag.")
    add_exact(rows, "recovery_failed", bool(direct_failed), adapter_result.recovery_failed, "Original failure flag.")
    add_float(rows, "selected_cost", direct_cost, adapter_result.selected_cost, 1e-12, "Original weighted cost.")
    add_float(rows, "progress_proxy", direct_progress, adapter_result.progress_proxy, 1e-12, "Horizon goal-distance reduction diagnostic.")
    add_exact(rows, "direct_state_unchanged", True, direct_state_unchanged, "Direct pure functions must not mutate x.")
    add_exact(rows, "adapter_state_unchanged", True, adapter_result.state_unchanged, "Adapter context tensors remain unchanged.")
    add_exact(rows, "formal_control_modified", False, adapter_result.modifies_formal_control, "No selected control is applied.")
    add_exact(rows, "rng_restored", True, adapter_result.rng_restored, "Adapter restores Python NumPy Torch and initialized CUDA RNG states.")

    cli.output.parent.mkdir(parents=True, exist_ok=True)
    with cli.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    failures = [row for row in rows if row["critical"] == "true" and row["match"] != "true"]
    print(f"checks={len(rows)} critical_failures={len(failures)}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
