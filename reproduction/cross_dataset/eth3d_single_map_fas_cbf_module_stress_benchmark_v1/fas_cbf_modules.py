#!/usr/bin/env python3
"""Task-owned FAS-CBF modules used by the frozen ETH3D benchmark.

The functions in this file do not read the independent reference mesh.  They
operate only on learned-map query callbacks, the frozen dynamics, and the
frozen actuator/state bounds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

import clarabel
import numpy as np
from scipy import sparse


DT = 0.05
VMAX = 0.10
UMAX = 0.10
START_SAFE_TARGET = 5.0e-4
START_SAFE_NEAR = 5.0e-3
START_SAFE_MAX_DISPLACEMENT_M = 0.05
DT_MARGIN = 5.0e-4
RECOVERY_HORIZON = 3


@dataclass(frozen=True)
class QPResult:
    status: str
    control: np.ndarray | None
    residual_max: float | None


def solve_bounded_qp(a_cbf: np.ndarray, b_cbf: np.ndarray, u_des: np.ndarray,
                     velocity: np.ndarray) -> QPResult:
    """Solve the frozen CBF QP with control and next-velocity bounds inside it."""
    a_cbf = np.asarray(a_cbf, dtype=np.float64).reshape((-1, 3))
    b_cbf = np.asarray(b_cbf, dtype=np.float64).reshape((-1,))
    u_des = np.asarray(u_des, dtype=np.float64).reshape(3)
    velocity = np.asarray(velocity, dtype=np.float64).reshape(3)
    eye = np.eye(3, dtype=np.float64)
    rows = np.concatenate((a_cbf, eye, -eye, DT * eye, -DT * eye), axis=0)
    rhs = np.concatenate((b_cbf, np.full(3, UMAX), np.full(3, UMAX),
                          np.full(3, VMAX) - velocity,
                          np.full(3, VMAX) + velocity))
    settings = clarabel.DefaultSettings()
    settings.verbose = False
    solution = clarabel.DefaultSolver(
        sparse.csc_matrix(np.eye(3, dtype=np.float64)), -u_des,
        sparse.csc_matrix(rows), rhs,
        [clarabel.NonnegativeConeT(rows.shape[0])], settings,
    ).solve()
    status = str(solution.status)
    if status != "Solved":
        return QPResult(status, None, None)
    control = np.asarray(solution.x, dtype=np.float64)
    return QPResult(status, control, float(np.max(rows @ control - rhs)))


def start_safe_classification(min_h: float) -> str:
    if min_h >= START_SAFE_TARGET:
        return "SAFE"
    if min_h >= 0.0:
        return "NEAR_BOUNDARY"
    return "MAP_UNSAFE"


def project_start_safe(position: np.ndarray,
                       query: Callable[[np.ndarray], dict],
                       max_iterations: int = 20) -> dict:
    """Active-set verified projection with a hard 5 cm displacement budget."""
    original = np.asarray(position, dtype=np.float64).reshape(3)
    current = original.copy()
    initial = query(current)
    initial_min = float(np.min(initial["h"]))
    classification = start_safe_classification(initial_min)
    if classification == "SAFE":
        return {"accepted": True, "classification": classification,
                "position": current, "displacement_m": 0.0,
                "iterations": 0, "initial_min_h": initial_min,
                "final_min_h": initial_min, "fallback": None}
    for iteration in range(1, max_iterations + 1):
        result = query(current)
        h = np.asarray(result["h"], dtype=np.float64)
        grad = np.asarray(result["grad"], dtype=np.float64)
        order = np.lexsort((np.asarray(result["candidate_ids"], dtype=np.int64), h))
        active = order[: min(64, len(order))]
        rows = -grad[active]
        rhs = h[active] - START_SAFE_TARGET
        finite = np.isfinite(rows).all(axis=1) & np.isfinite(rhs)
        rows, rhs = rows[finite], rhs[finite]
        if rows.shape[0] == 0:
            break
        settings = clarabel.DefaultSettings(); settings.verbose = False
        solver = clarabel.DefaultSolver(
            sparse.csc_matrix(np.eye(3)), np.zeros(3), sparse.csc_matrix(rows), rhs,
            [clarabel.NonnegativeConeT(rows.shape[0])], settings,
        )
        solution = solver.solve()
        if str(solution.status) != "Solved":
            break
        step = np.asarray(solution.x, dtype=np.float64)
        proposed = current + step
        displacement = float(np.linalg.norm(proposed - original))
        if displacement > START_SAFE_MAX_DISPLACEMENT_M + 1e-12:
            break
        current = proposed
        verified = query(current)
        final_min = float(np.min(verified["h"]))
        if final_min >= START_SAFE_TARGET:
            return {"accepted": True, "classification": classification,
                    "position": current, "displacement_m": displacement,
                    "iterations": iteration, "initial_min_h": initial_min,
                    "final_min_h": final_min, "fallback": None}
    final_min = float(np.min(query(current)["h"]))
    return {"accepted": False, "classification": classification,
            "position": current, "displacement_m": float(np.linalg.norm(current - original)),
            "iterations": max_iterations, "initial_min_h": initial_min,
            "final_min_h": final_min, "fallback": "START_STATE_REJECTED"}


def feasibility_aware_rows(a: np.ndarray, b: np.ndarray, h: np.ndarray,
                           candidate_ids: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """Exact box-dominance removal; no row that can bind is discarded."""
    a = np.asarray(a, dtype=np.float64).reshape((-1, 3))
    b = np.asarray(b, dtype=np.float64).reshape(-1)
    h = np.asarray(h, dtype=np.float64).reshape(-1)
    candidate_ids = np.asarray(candidate_ids, dtype=np.int64).reshape(-1)
    box_maximum = UMAX * np.sum(np.abs(a), axis=1)
    forced = h <= START_SAFE_NEAR
    can_bind = box_maximum > b + 1e-12
    keep = forced | can_bind
    indices = np.flatnonzero(keep)
    if indices.size:
        order = np.argsort(candidate_ids[indices], kind="stable")
        indices = indices[order]
    debug = {
        "input_constraint_count": int(len(h)),
        "forced_candidate_count": int(np.sum(forced)),
        "provably_redundant_count": int(np.sum(~keep)),
        "output_constraint_count": int(indices.size),
        "hidden_relaxation_count": 0,
        "same_control_bounds": True,
    }
    return a[indices], b[indices], candidate_ids[indices], debug


def integrate(position: np.ndarray, velocity: np.ndarray,
              control: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Frozen forward-Euler double-integrator update."""
    position = np.asarray(position, dtype=np.float64)
    velocity = np.asarray(velocity, dtype=np.float64)
    control = np.asarray(control, dtype=np.float64)
    return position + DT * velocity, velocity + DT * control


def verify_discrete_step(position: np.ndarray, velocity: np.ndarray,
                         control: np.ndarray,
                         min_h: Callable[[np.ndarray], float],
                         samples: int = 11) -> dict:
    """Verify endpoint and the exact forward-Euler position segment."""
    endpoint, next_velocity = integrate(position, velocity, control)
    values = []
    for fraction in np.linspace(0.0, 1.0, samples):
        point = (1.0 - fraction) * np.asarray(position) + fraction * endpoint
        values.append(float(min_h(point)))
    endpoint_h = values[-1]
    segment_h = min(values)
    return {
        "passed": bool(endpoint_h >= DT_MARGIN and segment_h >= DT_MARGIN),
        "endpoint_h": endpoint_h,
        "segment_h": segment_h,
        "endpoint_only_miss": bool(endpoint_h >= DT_MARGIN and segment_h < DT_MARGIN),
        "endpoint": endpoint,
        "next_velocity": next_velocity,
        "sample_count": samples,
    }


def recovery_desired_library(u_des: np.ndarray, velocity: np.ndarray) -> list[np.ndarray]:
    raw = [np.asarray(u_des, dtype=np.float64), np.zeros(3),
           np.clip(-np.asarray(velocity, dtype=np.float64) / DT, -UMAX, UMAX)]
    for axis in range(3):
        for sign in (-1.0, 1.0):
            value = np.zeros(3); value[axis] = sign * UMAX; raw.append(value)
    unique: list[np.ndarray] = []
    seen: set[bytes] = set()
    for value in raw:
        key = np.ascontiguousarray(value).tobytes()
        if key not in seen:
            seen.add(key); unique.append(value)
    return unique


def verify_horizon(position: np.ndarray, velocity: np.ndarray,
                   controls: Iterable[np.ndarray],
                   min_h: Callable[[np.ndarray], float],
                   horizon: int = RECOVERY_HORIZON) -> dict:
    controls = list(controls)
    if not controls:
        raise ValueError("empty recovery control sequence")
    p, v = np.asarray(position, dtype=np.float64), np.asarray(velocity, dtype=np.float64)
    minimum = float(min_h(p))
    for step in range(horizon):
        control = controls[min(step, len(controls) - 1)]
        check = verify_discrete_step(p, v, control, min_h)
        minimum = min(minimum, float(check["segment_h"]), float(check["endpoint_h"]))
        if not check["passed"]:
            return {"passed": False, "minimum_h": minimum, "failed_step": step + 1}
        p, v = check["endpoint"], check["next_velocity"]
    return {"passed": True, "minimum_h": minimum, "failed_step": None,
            "endpoint": p, "end_velocity": v}
