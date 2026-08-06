"""Frozen braking control and kinetic-non-increase halfspace projection."""
from __future__ import annotations

import numpy as np

from alternative_library.result_types import Bounds, SlotAvailability
from task_config import NORMAL_EPSILON


def braking_control(velocity: np.ndarray, bounds: Bounds) -> np.ndarray:
    return np.clip(-np.asarray(velocity, dtype=np.float64) / bounds.dt, np.asarray(bounds.u_min), np.asarray(bounds.u_max))


def project_kinetic_nonincrease(velocity: np.ndarray, direction: np.ndarray) -> tuple[SlotAvailability, np.ndarray | None]:
    v, raw = np.asarray(velocity, dtype=np.float64), np.asarray(direction, dtype=np.float64)
    if v.shape != (3,) or raw.shape != (3,) or not np.all(np.isfinite(v)) or not np.all(np.isfinite(raw)):
        return SlotAvailability.DIRECTION_NONFINITE, None
    velocity_norm_sq = float(v @ v)
    projected = raw if velocity_norm_sq <= NORMAL_EPSILON ** 2 or float(v @ raw) <= 0.0 else raw - (float(v @ raw) / velocity_norm_sq) * v
    if float(np.linalg.norm(projected)) <= NORMAL_EPSILON:
        return SlotAvailability.DEGENERATE_AFTER_DECELERATION_PROJECTION, None
    return SlotAvailability.AVAILABLE, projected / float(np.linalg.norm(projected))
