"""Componentwise hard actuator admission with explicit clipping provenance."""
from __future__ import annotations

import math

from .result_types import ActuatorBounds, ActuatorCertificate, Control


def certify_actuator(control: Control, bounds: ActuatorBounds) -> ActuatorCertificate:
    if not bounds.valid or not control.finite:
        return ActuatorCertificate(False, "ACTUATOR_INPUT_NONFINITE_OR_SHAPE_MISMATCH", None, control.candidate_id, (False, False, False))
    checks = tuple(
        bool(bounds.u_min[i] <= control.acceleration[i] <= bounds.u_max[i]) for i in range(3)
    )
    return ActuatorCertificate(all(checks), "ACTUATOR_BOUNDS_PASS" if all(checks) else "ACTUATOR_BOUNDS_VIOLATION", control if all(checks) else None, control.candidate_id, checks)


def clipped_alternative(control: Control, bounds: ActuatorBounds, candidate_id: str) -> Control:
    if not control.finite or not bounds.valid:
        raise ValueError("CANNOT_CLIP_NONFINITE_OR_INVALID_INPUT")
    clipped = tuple(max(bounds.u_min[i], min(bounds.u_max[i], control.acceleration[i])) for i in range(3))
    return Control(clipped, "ALTERNATIVE_CONTROL_CLIPPED_FROM:" + control.candidate_id, candidate_id)
