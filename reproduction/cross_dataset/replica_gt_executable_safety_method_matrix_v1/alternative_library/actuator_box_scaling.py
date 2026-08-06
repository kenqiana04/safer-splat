"""Frozen symmetric actuator-box scaling without hidden clipping."""
from __future__ import annotations

import numpy as np

from alternative_library.result_types import Bounds, SlotAvailability
from task_config import NORMAL_EPSILON


def scale_to_box(direction: np.ndarray, bounds: Bounds) -> tuple[SlotAvailability, np.ndarray | None]:
    vector = np.asarray(direction, dtype=np.float64)
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        return SlotAvailability.DIRECTION_NONFINITE, None
    nonzero = np.abs(vector) > NORMAL_EPSILON
    if not bool(np.any(nonzero)):
        return SlotAvailability.DIRECTION_ZERO, None
    scales = np.asarray(bounds.u_max, dtype=np.float64)[nonzero] / np.abs(vector[nonzero])
    alpha = float(np.min(scales))
    control = alpha * vector
    if not np.all(np.isfinite(control)):
        return SlotAvailability.DIRECTION_NONFINITE, None
    if np.any(control < np.asarray(bounds.u_min) - NORMAL_EPSILON) or np.any(control > np.asarray(bounds.u_max) + NORMAL_EPSILON):
        return SlotAvailability.ACTUATOR_CONTRACT_REJECTED, None
    if not bool(np.any(np.isclose(np.abs(control), np.asarray(bounds.u_max), atol=NORMAL_EPSILON, rtol=0.0))):
        return SlotAvailability.ACTUATOR_CONTRACT_REJECTED, None
    control[np.abs(control) == 0.0] = 0.0
    return SlotAvailability.AVAILABLE, control
