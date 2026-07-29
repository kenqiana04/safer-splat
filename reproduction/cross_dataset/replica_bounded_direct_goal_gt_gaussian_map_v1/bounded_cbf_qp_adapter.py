"""Task-owned bounded QP adapter; it never changes SAFER core modules."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from scipy import sparse
import clarabel


@dataclass(frozen=True)
class BoundedQPResult:
    status: str
    control: np.ndarray | None
    residual_max: float | None
    post_qp_clip_count: int


class BoundedCBFQPAdapter:
    """Solve original CBF rows and actual actuator/state bounds in one QP.

    ``cbf_rows`` is the exact ``(A_cbf, b_cbf)`` contract exposed by an
    unmodified ``CBF.get_QP_matrices`` wrapper.  This adapter deliberately has
    no fallback control path: an unsolved QP returns ``control=None``.
    """

    def __init__(self, *, dt: float = 0.05, vmax_component: float = 0.10,
                 umax_component: float = 0.10) -> None:
        self.dt = float(dt)
        self.vmax = float(vmax_component)
        self.umax = float(umax_component)

    def constraints(self, a_cbf: np.ndarray, b_cbf: np.ndarray,
                    velocity: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        a_cbf = np.asarray(a_cbf, dtype=np.float64).reshape((-1, 3))
        b_cbf = np.asarray(b_cbf, dtype=np.float64).reshape((-1,))
        velocity = np.asarray(velocity, dtype=np.float64).reshape((3,))
        eye = np.eye(3, dtype=np.float64)
        rows = np.concatenate((
            a_cbf,
            eye,
            -eye,
            self.dt * eye,
            -self.dt * eye,
        ), axis=0)
        rhs = np.concatenate((
            b_cbf,
            np.full(3, self.umax),
            np.full(3, self.umax),
            np.full(3, self.vmax) - velocity,
            np.full(3, self.vmax) + velocity,
        ))
        return rows, rhs

    def solve(self, a_cbf: np.ndarray, b_cbf: np.ndarray, u_des: np.ndarray,
              velocity: np.ndarray) -> BoundedQPResult:
        rows, rhs = self.constraints(a_cbf, b_cbf, velocity)
        u_des = np.asarray(u_des, dtype=np.float64).reshape((3,))
        settings = clarabel.DefaultSettings()
        settings.verbose = False
        solver = clarabel.DefaultSolver(
            sparse.csc_matrix(np.eye(3, dtype=np.float64)),
            -u_des,
            sparse.csc_matrix(rows),
            rhs,
            [clarabel.NonnegativeConeT(rows.shape[0])],
            settings,
        )
        solution = solver.solve()
        status = str(solution.status)
        if status != "Solved":
            return BoundedQPResult(status=status, control=None,
                                   residual_max=None, post_qp_clip_count=0)
        control = np.asarray(solution.x, dtype=np.float64)
        residual = float(np.max(rows @ control - rhs))
        return BoundedQPResult(status=status, control=control,
                               residual_max=residual, post_qp_clip_count=0)

    def step(self, position: np.ndarray, velocity: np.ndarray,
             result: BoundedQPResult) -> tuple[np.ndarray, np.ndarray] | None:
        if result.control is None:
            return None
        position = np.asarray(position, dtype=np.float64).reshape((3,))
        velocity = np.asarray(velocity, dtype=np.float64).reshape((3,))
        # Forward Euler, exactly as frozen.  No clipping occurs after solve.
        return position + self.dt * velocity, velocity + self.dt * result.control
