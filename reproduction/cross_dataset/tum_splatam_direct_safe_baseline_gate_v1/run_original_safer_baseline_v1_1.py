#!/usr/bin/env python3
"""One frozen-registry Original SAFER baseline child process for V1.1 only."""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import torch

from cbf.cbf_utils import CBF
from dynamics.systems import DoubleIntegrator, double_integrator_dynamics
from splat.gsplat_utils import DummyGSplatLoader

ROOT = Path("/disk1/zlab/maintenance_records/tum_splatam_direct_safe_baseline_gate_v1_1")
MAP = Path("/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/splatam/canonical_export/export_a")
RADIUS, ALPHA, BETA, DT, MAX_STEPS, GOAL_TOLERANCE = 0.015, 5.0, 1.0, 0.05, 800, 0.001


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def original_clamped_pd(state: torch.Tensor, goal: torch.Tensor) -> torch.Tensor:
    """Exact controller algebra used by the authoritative original `run.py`."""
    velocity_desired = torch.clamp(5.0 * (goal[:3] - state[:3]), -0.1, 0.1)
    velocity_desired = velocity_desired + (goal[3:] - state[3:])
    return torch.clamp(velocity_desired - state[3:], -0.1, 0.1)


def load_map(device: torch.device) -> DummyGSplatLoader:
    arrays = {name: np.load(MAP / f"{name}.npy", mmap_mode="r") for name in ("means_world_m", "scales_linear_m", "quaternions_wxyz")}
    loader = DummyGSplatLoader(device)
    loader.initialize_attributes(
        torch.from_numpy(arrays["means_world_m"]),
        torch.from_numpy(arrays["quaternions_wxyz"]),
        torch.from_numpy(arrays["scales_linear_m"]),
    )
    return loader


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    registry = json.loads(arguments.registry.read_text(encoding="utf-8"))
    if registry.get("status") != "FROZEN":
        raise RuntimeError("FROZEN_REGISTRY_REQUIRED")
    pair = next((row for row in registry["registry"] if row["label"] == arguments.label), None)
    if pair is None:
        raise RuntimeError("UNKNOWN_FROZEN_LABEL")
    arguments.output.mkdir(parents=True, exist_ok=False)
    device = torch.device("cuda:0")
    torch.manual_seed(0)
    loader = load_map(device)
    start = torch.tensor(pair["start_position"], dtype=torch.float32, device=device)
    goal_position = torch.tensor(pair["goal_position"], dtype=torch.float32, device=device)
    state = torch.cat((start, torch.zeros(3, dtype=torch.float32, device=device)))
    goal = torch.cat((goal_position, torch.zeros(3, dtype=torch.float32, device=device)))
    dynamics = DoubleIntegrator(device=device, ndim=3)
    cbf = CBF(loader, dynamics, ALPHA, BETA, RADIUS, distance_type="ball-to-ellipsoid")
    rows: list[dict[str, object]] = []
    status = "MAX_STEPS"
    started = time.perf_counter()
    for step in range(1, MAX_STEPS + 1):
        torch.cuda.synchronize()
        desired_control = original_clamped_pd(state, goal)
        control = cbf.solve_QP(state, desired_control)
        if not cbf.solver_success:
            status = "QP_INFEASIBLE"
            break
        if not bool(torch.isfinite(control).all()):
            status = "NONFINITE_CONTROL"
            break
        prior = state.clone()
        state = double_integrator_dynamics(state, control) * DT + state
        if not bool(torch.isfinite(state).all()):
            status = "NONFINITE_STATE"
            break
        h, gradient, hessian, _ = loader.query_distance(state[:3], radius=RADIUS, distance_type="ball-to-ellipsoid")
        finite_query = bool(torch.isfinite(h).all() and torch.isfinite(gradient).all() and torch.isfinite(hessian).all())
        if not finite_query:
            status = "NONFINITE_QUERY"
            break
        active = int(torch.argmin(h).item())
        minimum_h = float(torch.min(h).item())
        position_goal_distance = float(torch.linalg.vector_norm(state[:3] - goal[:3]).item())
        state_increment = float(torch.linalg.vector_norm(state - prior).item())
        row = {
            "step": step,
            "time_seconds": step * DT,
            "state": state.detach().cpu().double().tolist(),
            "desired_control": desired_control.detach().cpu().double().tolist(),
            "control": control.detach().cpu().double().tolist(),
            "position_goal_distance": position_goal_distance,
            "state_increment_norm": state_increment,
            "min_h_float32": minimum_h,
            "active_gaussian": active,
            "active_constraints": [active],
            "qp_solver": "Clarabel",
            "qp_success": True,
            "qp_residual": None,
            "gpu_memory_allocated_bytes": int(torch.cuda.memory_allocated(device)),
        }
        rows.append(row)
        if minimum_h < 0.0:
            status = "FLOAT32_PROXY_OVERLAP_STOP"
            break
        if position_goal_distance <= GOAL_TOLERANCE:
            status = "STRICT_GOAL_REACHED"
            break
        # This is the original no-motion stopping test, retained verbatim in
        # threshold and purpose; it is a diagnostic terminal, not a new control rule.
        if state_increment < GOAL_TOLERANCE:
            status = "CBF_BOUNDARY_STALL"
            break
    torch.cuda.synchronize()
    write_json(arguments.output / "steps.json", rows)
    summary = {
        "schema": "TUM_DIRECT_SAFE_ORIGINAL_SAFER_BASELINE_V1_1",
        "label": arguments.label,
        "pair": pair,
        "terminal_status": status,
        "strict_goal_reached": status == "STRICT_GOAL_REACHED",
        "float32_proxy_overlap": status == "FLOAT32_PROXY_OVERLAP_STOP",
        "qp_infeasible": status == "QP_INFEASIBLE",
        "nonfinite": status.startswith("NONFINITE"),
        "watchdog_timeout": False,
        "cbf_boundary_stall": status == "CBF_BOUNDARY_STALL",
        "max_steps": status == "MAX_STEPS",
        "steps": len(rows),
        "runtime_seconds": time.perf_counter() - started,
        "parameters": {"radius": RADIUS, "alpha": ALPHA, "beta": BETA, "dt": DT, "max_steps": MAX_STEPS, "goal_tolerance": GOAL_TOLERANCE, "integrator": "explicit Euler", "qp_solver": "Clarabel"},
        "controller_identity": "ORIGINAL_SAFER_CLAMPED_PD_AND_CBF_QP",
        "forbidden_execution_counts": {"start_safe": 0, "risk_aware": 0, "recovery": 0, "v4_c": 0, "replica": 0},
    }
    write_json(arguments.output / "summary.json", summary)
    print(json.dumps({"label": arguments.label, "terminal_status": status, "steps": len(rows)}, sort_keys=True))


if __name__ == "__main__":
    main()
