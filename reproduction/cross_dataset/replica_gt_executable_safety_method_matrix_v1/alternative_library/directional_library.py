"""Six fixed directional slots derived only from represented-map current inputs."""
from __future__ import annotations

from typing import Any

import numpy as np

from alternative_library.actuator_box_scaling import scale_to_box
from alternative_library.deceleration_projection import braking_control, project_kinetic_nonincrease
from alternative_library.represented_sphere_frame import build_frame
from alternative_library.result_types import Bounds, CandidateSet, DirectionalSlot, SlotAvailability
from task_config import DEDUP_ABS_TOL, LIBRARY_SOURCE, SLOT_IDS


FORMULAS = (
    "u_box(n)", "u_box(t_g)", "u_box(t_a)", "u_box(-t_a)",
    "u_box(normalize(project_Hv(b_hat+t_g)))", "u_box(normalize(project_Hv(b_hat+n)))",
)


def _status_slots(status: SlotAvailability, provenance: dict[str, Any]) -> tuple[DirectionalSlot, ...]:
    return tuple(DirectionalSlot(index + 1, identifier, LIBRARY_SOURCE, FORMULAS[index], status, None, provenance) for index, identifier in enumerate(SLOT_IDS))


def _slot(index: int, status: SlotAvailability, control: np.ndarray | None, provenance: dict[str, Any], frame_status: str) -> DirectionalSlot:
    availability = SlotAvailability.GOAL_DEGENERATE_AXIS_FALLBACK_USED if status.usable and frame_status == "GOAL_DEGENERATE_AXIS_FALLBACK_USED" else status
    acceleration = None if control is None else tuple(float(value) if float(value) != 0.0 else 0.0 for value in control)
    return DirectionalSlot(index + 1, SLOT_IDS[index], LIBRARY_SOURCE, FORMULAS[index], availability, acceleration, provenance)


def _deduplicate(slots: tuple[DirectionalSlot, ...]) -> tuple[DirectionalSlot, ...]:
    accepted: list[DirectionalSlot] = []
    result: list[DirectionalSlot] = []
    for slot in slots:
        if not slot.available:
            result.append(slot); continue
        candidate = np.asarray(slot.acceleration, dtype=np.float64)
        earlier = next((item for item in accepted if np.all(np.abs(candidate - np.asarray(item.acceleration, dtype=np.float64)) <= DEDUP_ABS_TOL)), None)
        if earlier is None:
            accepted.append(slot); result.append(slot)
        else:
            result.append(DirectionalSlot(slot.slot_index, slot.candidate_id, slot.source, slot.formula, SlotAvailability.DUPLICATE_OF_EARLIER_SLOT, None, slot.provenance, earlier.candidate_id))
    return tuple(result)


def build_directional_library(
    position: tuple[float, float, float] | np.ndarray,
    velocity: tuple[float, float, float] | np.ndarray,
    goal: tuple[float, float, float] | np.ndarray,
    query_status: str,
    active_gaussian_ids: tuple[int, ...],
    centers: np.ndarray,
    bounds: Bounds = Bounds(),
) -> CandidateSet:
    p, v, goal_vector = (np.asarray(item, dtype=np.float64) for item in (position, velocity, goal))
    base = {"query_status": query_status, "map_input": "REPRESENTED_GAUSSIAN_SPHERE_ONLY", "reference_input": False}
    if query_status != "FINITE":
        slots = _status_slots(SlotAvailability.MAP_QUERY_UNAVAILABLE, base)
        return CandidateSet(tuple(p), tuple(v), tuple(goal_vector), None, None, None, None, None, None, slots, query_status, "MAP_QUERY_UNAVAILABLE")
    if not active_gaussian_ids:
        slots = _status_slots(SlotAvailability.ACTIVE_PRIMITIVE_UNAVAILABLE, base)
        return CandidateSet(tuple(p), tuple(v), tuple(goal_vector), None, None, None, None, None, None, slots, query_status, "ACTIVE_PRIMITIVE_UNAVAILABLE")
    primitive_id = int(active_gaussian_ids[0])
    centers_value = np.asarray(centers, dtype=np.float64)
    if primitive_id < 0 or primitive_id >= len(centers_value):
        slots = _status_slots(SlotAvailability.ACTIVE_PRIMITIVE_UNAVAILABLE, {**base, "active_primitive_id": primitive_id})
        return CandidateSet(tuple(p), tuple(v), tuple(goal_vector), primitive_id, None, None, None, None, None, slots, query_status, "ACTIVE_PRIMITIVE_UNAVAILABLE")
    center = centers_value[primitive_id]
    frame_status, normal, goal_tangent, auxiliary_tangent = build_frame(p, goal_vector, center)
    provenance = {**base, "active_primitive_id": primitive_id, "active_primitive_center": tuple(float(item) for item in center), "normal_source": "REPRESENTED_SPHERE_OUTWARD_NORMAL", "frame_status": frame_status}
    brake = braking_control(v, bounds)
    if normal is None:
        status = SlotAvailability.NORMAL_DEGENERATE if frame_status == "NORMAL_DEGENERATE" else SlotAvailability.DIRECTION_ZERO
        slots = _status_slots(status, provenance)
        return CandidateSet(tuple(p), tuple(v), tuple(goal_vector), primitive_id, tuple(center), None, None, None, tuple(brake), slots, query_status, frame_status)
    statuses_controls: list[tuple[SlotAvailability, np.ndarray | None]] = [scale_to_box(normal, bounds)]
    if goal_tangent is None or auxiliary_tangent is None:
        statuses_controls.extend([(SlotAvailability.DIRECTION_ZERO, None)] * 4)
        if float(np.linalg.norm(brake)) <= 1e-12:
            statuses_controls.append((SlotAvailability.BRAKING_DIRECTION_UNAVAILABLE, None))
        else:
            projected_status, direction = project_kinetic_nonincrease(v, brake / float(np.linalg.norm(brake)) + normal)
            statuses_controls.append(scale_to_box(direction, bounds) if direction is not None else (projected_status, None))
    else:
        statuses_controls.extend([scale_to_box(goal_tangent, bounds), scale_to_box(auxiliary_tangent, bounds), scale_to_box(-auxiliary_tangent, bounds)])
        if float(np.linalg.norm(brake)) <= 1e-12:
            statuses_controls.extend([(SlotAvailability.BRAKING_DIRECTION_UNAVAILABLE, None), (SlotAvailability.BRAKING_DIRECTION_UNAVAILABLE, None)])
        else:
            brake_unit = brake / float(np.linalg.norm(brake))
            for raw in (brake_unit + goal_tangent, brake_unit + normal):
                projected_status, direction = project_kinetic_nonincrease(v, raw)
                statuses_controls.append(scale_to_box(direction, bounds) if direction is not None else (projected_status, None))
    slots = tuple(_slot(index, status, control, provenance, frame_status) for index, (status, control) in enumerate(statuses_controls))
    if len(slots) != 6:
        raise ValueError("INVALID_SLOT_COUNT")
    return CandidateSet(tuple(p), tuple(v), tuple(goal_vector), primitive_id, tuple(center), tuple(normal), None if goal_tangent is None else tuple(goal_tangent), None if auxiliary_tangent is None else tuple(auxiliary_tangent), tuple(brake), _deduplicate(slots), query_status, frame_status)
