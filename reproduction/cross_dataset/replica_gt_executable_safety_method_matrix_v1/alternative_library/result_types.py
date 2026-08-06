"""Immutable result types for method-design-only candidate generation."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SlotAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    MAP_QUERY_UNAVAILABLE = "MAP_QUERY_UNAVAILABLE"
    ACTIVE_PRIMITIVE_UNAVAILABLE = "ACTIVE_PRIMITIVE_UNAVAILABLE"
    NORMAL_DEGENERATE = "NORMAL_DEGENERATE"
    GOAL_DEGENERATE_AXIS_FALLBACK_USED = "GOAL_DEGENERATE_AXIS_FALLBACK_USED"
    DIRECTION_NONFINITE = "DIRECTION_NONFINITE"
    DIRECTION_ZERO = "DIRECTION_ZERO"
    BRAKING_DIRECTION_UNAVAILABLE = "BRAKING_DIRECTION_UNAVAILABLE"
    DEGENERATE_AFTER_DECELERATION_PROJECTION = "DEGENERATE_AFTER_DECELERATION_PROJECTION"
    DUPLICATE_OF_EARLIER_SLOT = "DUPLICATE_OF_EARLIER_SLOT"
    ACTUATOR_CONTRACT_REJECTED = "ACTUATOR_CONTRACT_REJECTED"

    @property
    def usable(self) -> bool:
        return self in (SlotAvailability.AVAILABLE, SlotAvailability.GOAL_DEGENERATE_AXIS_FALLBACK_USED)


@dataclass(frozen=True)
class Bounds:
    u_min: tuple[float, float, float] = (-0.1, -0.1, -0.1)
    u_max: tuple[float, float, float] = (0.1, 0.1, 0.1)
    dt: float = 0.05


@dataclass(frozen=True)
class DirectionalSlot:
    slot_index: int
    candidate_id: str
    source: str
    formula: str
    availability: SlotAvailability
    acceleration: tuple[float, float, float] | None
    provenance: dict[str, Any]
    duplicate_of: str | None = None

    @property
    def available(self) -> bool:
        return self.availability.usable and self.acceleration is not None


@dataclass(frozen=True)
class CandidateSet:
    state_position: tuple[float, float, float]
    state_velocity: tuple[float, float, float]
    goal_position: tuple[float, float, float]
    active_primitive_id: int | None
    active_primitive_center: tuple[float, float, float] | None
    represented_normal: tuple[float, float, float] | None
    goal_tangent: tuple[float, float, float] | None
    auxiliary_tangent: tuple[float, float, float] | None
    braking_control: tuple[float, float, float] | None
    slots: tuple[DirectionalSlot, ...]
    map_query_status: str
    frame_status: str

    @property
    def available_slots(self) -> tuple[DirectionalSlot, ...]:
        return tuple(slot for slot in self.slots if slot.available)
