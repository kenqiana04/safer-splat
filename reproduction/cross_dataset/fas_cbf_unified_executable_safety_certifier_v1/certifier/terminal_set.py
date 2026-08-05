"""Minimal sufficient terminal-set predicate for the frozen static model."""
from __future__ import annotations

from .result_types import State


class BrakingToRestTerminalSet:
    identity="BRAKING_TO_REST_TERMINAL_SET_V1"

    def __init__(self,velocity_tolerance:float)->None:
        self.velocity_tolerance=float(velocity_tolerance)

    def velocity_is_terminal(self,state:State)->bool:
        return state.finite and max(abs(float(v)) for v in state.velocity)<=self.velocity_tolerance
