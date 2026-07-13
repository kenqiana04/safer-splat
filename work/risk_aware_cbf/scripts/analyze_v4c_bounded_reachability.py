"""Candidate-independent double-integrator position-deviation bounds."""

from __future__ import annotations

import math


def maximum_position_deviation_m(dt: float, component_acceleration_bound: float, horizon: int) -> float:
    """Return the Euclidean bound relative to zero added acceleration.

    The repository uses forward Euler position updates, so an acceleration
    chosen at H1 first affects position at H2. This is a dynamics envelope,
    not a collision, h-improvement, or controllability certificate.
    """

    steps = max(0, int(horizon))
    per_component = abs(float(component_acceleration_bound)) * float(dt) ** 2 * steps * max(0, steps - 1) / 2.0
    return math.sqrt(3.0) * per_component


def reachability_row(dt: float, component_acceleration_bound: float) -> dict[str, float]:
    return {
        "dt": float(dt),
        "component_acceleration_bound": float(component_acceleration_bound),
        **{f"maximum_control_induced_position_deviation_h{h}_m": maximum_position_deviation_m(dt, component_acceleration_bound, h) for h in range(1, 6)},
    }
