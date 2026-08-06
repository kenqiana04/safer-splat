"""Pure represented-sphere normal and deterministic tangent-frame construction."""
from __future__ import annotations

import numpy as np

from task_config import NORMAL_EPSILON, ORTHOGONALITY_TOL


def _unit(vector: np.ndarray) -> np.ndarray | None:
    value = np.asarray(vector, dtype=np.float64)
    norm = float(np.linalg.norm(value))
    return None if not np.all(np.isfinite(value)) or norm <= NORMAL_EPSILON else value / norm


def choose_axis(normal: np.ndarray) -> np.ndarray:
    axes = np.eye(3, dtype=np.float64)
    return axes[int(np.argmin(np.abs(axes @ normal)))]


def build_frame(position: np.ndarray, goal: np.ndarray, center: np.ndarray) -> tuple[str, np.ndarray | None, np.ndarray | None, np.ndarray | None]:
    p, g, c = (np.asarray(item, dtype=np.float64) for item in (position, goal, center))
    normal = _unit(p - c)
    if normal is None:
        return "NORMAL_DEGENERATE", None, None, None
    goal_unit = _unit(g - p)
    if goal_unit is None:
        return "DIRECTION_ZERO", normal, None, None
    tangent_raw = goal_unit - float(goal_unit @ normal) * normal
    tangent = _unit(tangent_raw)
    frame_status = "AVAILABLE"
    if tangent is None:
        axis = choose_axis(normal)
        tangent = _unit(axis - float(axis @ normal) * normal)
        if tangent is None:
            return "DIRECTION_ZERO", normal, None, None
        frame_status = "GOAL_DEGENERATE_AXIS_FALLBACK_USED"
    auxiliary = _unit(np.cross(normal, tangent))
    if auxiliary is None:
        return "DIRECTION_ZERO", normal, None, None
    matrix = np.column_stack((normal, tangent, auxiliary))
    if abs(float(normal @ tangent)) > ORTHOGONALITY_TOL or abs(float(normal @ auxiliary)) > ORTHOGONALITY_TOL or abs(float(tangent @ auxiliary)) > ORTHOGONALITY_TOL or float(np.linalg.det(matrix)) < -ORTHOGONALITY_TOL:
        raise ValueError("INVALID_TANGENT_FRAME")
    return frame_status, normal, tangent, auxiliary
