"""The one normative execution model shared by all V1 components."""
from __future__ import annotations

import math

from certifier.result_types import ActuatorBounds, Control, State


class PositionFirstForwardEulerDoubleIntegrator:
    identity = "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1"

    def __init__(self, bounds: ActuatorBounds) -> None:
        if not bounds.valid:
            raise ValueError("INVALID_ACTUATOR_BOUNDS")
        self.bounds = bounds

    def transition(self, state: State, control: Control) -> State:
        if not state.finite or not control.finite:
            raise ValueError("NONFINITE_DYNAMICS_INPUT")
        dt = self.bounds.dt
        p = tuple(float(state.position[i] + dt * state.velocity[i]) for i in range(3))
        v = tuple(float(state.velocity[i] + dt * control.acceleration[i]) for i in range(3))
        return State(p, v, float(state.timestamp + dt), state.map_snapshot_id)

    def interval_state(self, state: State, control: Control, tau: float) -> State:
        if not state.finite or not control.finite or not math.isfinite(tau):
            raise ValueError("NONFINITE_DYNAMICS_INPUT")
        if tau < 0.0 or tau > self.bounds.dt:
            raise ValueError("TAU_OUT_OF_INTERVAL")
        p = tuple(float(state.position[i] + tau * state.velocity[i]) for i in range(3))
        v = tuple(float(state.velocity[i] + tau * control.acceleration[i]) for i in range(3))
        return State(p, v, float(state.timestamp + tau), state.map_snapshot_id)

    def segment_endpoints(self, state: State) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        end = tuple(float(state.position[i] + self.bounds.dt * state.velocity[i]) for i in range(3))
        return state.position, end


def diagnostic_constant_acceleration_zoh(
    state: State, control: Control, dt: float
) -> State:
    """Non-normative diagnostic only; never used by a formal V1 certificate."""
    p = tuple(state.position[i] + dt * state.velocity[i] + 0.5 * dt * dt * control.acceleration[i] for i in range(3))
    v = tuple(state.velocity[i] + dt * control.acceleration[i] for i in range(3))
    return State(p, v, state.timestamp + dt, state.map_snapshot_id)
