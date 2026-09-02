"""Pure validation rules for the frozen cross-layer geometry authority V2."""

from __future__ import annotations

import math
from typing import Any


POINT_CONSUMERS = {
    "I0A_INITIAL_ADMISSION",
    "I0B_REPAIR_VERIFICATION",
    "R0_DIAGNOSTIC_CURRENT",
    "L3_TERMINAL_POINT",
    "L5_TERMINAL_POINT",
}
SEGMENT_CONSUMERS = {
    "L1_IMMEDIATE_CLOSED_SEGMENT",
    "L2_H1_SEGMENT",
    "L3_BACKUP_SEGMENTS",
    "L3_TERMINAL_ZERO_HOLD",
    "L5_TERMINAL_ZERO_HOLD",
}
NONCONSUMERS = {
    "C0_ADMISSIBILITY_NONCONSUMER",
    "L4_PROPOSAL_NONCONSUMER",
    "SUPERVISOR_ARBITRATION_NONCONSUMER",
}
CONTROLLER = "CONTROLLER_ACTIVE_CBF"


def _close(a: float, b: float) -> bool:
    return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=1e-12)


def validate_scenario(scenario: dict[str, Any]) -> list[str]:
    """Return semantic violations for a synthetic or assembled authority scenario."""
    errors: list[str] = []
    controller_radius = scenario.get("controller_radius_m")
    margin = scenario.get("certification_margin_m")
    effective = scenario.get("certification_effective_radius_m")
    rho = scenario.get("rho_seg_m")
    if controller_radius is None:
        errors.append("G0_UNRESOLVED")
    elif not _close(controller_radius, 0.015):
        errors.append("CONTROLLER_RADIUS_MUTATION")
    if margin is None or not _close(margin, 0.01):
        errors.append("CERTIFICATION_MARGIN_AUTHORITY_MISMATCH")
    if scenario.get("margin_application_count") != 1:
        errors.append("MARGIN_APPLICATION_COUNT_NOT_ONE")
    if effective is None or not _close(effective, 0.025):
        errors.append("CANONICAL_EFFECTIVE_RADIUS_MISMATCH")
    if rho is None or not _close(rho, 0.0):
        errors.append("SEGMENT_RESERVE_MISMATCH")
    if scenario.get("map_authority") != "STATIC_IMMUTABLE_REPRESENTED_GAUSSIAN_MAP_AUTHORITY":
        errors.append("MAP_AUTHORITY_MISMATCH")
    if scenario.get("fallback_value_m") in (0.10, 0.11):
        errors.append("HISTORICAL_V1_FALLBACK")
    if scenario.get("v1_historical_valid") is not True:
        errors.append("V1_HISTORICAL_EVIDENCE_INVALIDATED")
    layer_radii = scenario.get("layer_effective_radius_m", {})
    for layer in POINT_CONSUMERS | SEGMENT_CONSUMERS:
        if layer not in layer_radii or not _close(layer_radii[layer], 0.025):
            errors.append(f"{layer}_RADIUS_MISMATCH")
    if not _close(layer_radii.get(CONTROLLER, -1), 0.015):
        errors.append("ACTIVE_CONTROLLER_RADIUS_MISMATCH")
    layer_rho = scenario.get("layer_rho_seg_m", {})
    for layer in SEGMENT_CONSUMERS:
        if layer not in layer_rho or not _close(layer_rho[layer], 0.0):
            errors.append(f"{layer}_RHO_SEG_MISMATCH")
    for layer in POINT_CONSUMERS:
        if layer_rho.get(layer) is not None:
            errors.append(f"{layer}_POINT_RHO_MUST_BE_NULL")
    if scenario.get("layer_local_margin_without_source"):
        errors.append("LAYER_LOCAL_MARGIN_WITHOUT_SOURCE")
    return errors


def canonical_scenario() -> dict[str, Any]:
    layer_radii = {layer: 0.025 for layer in POINT_CONSUMERS | SEGMENT_CONSUMERS}
    layer_radii[CONTROLLER] = 0.015
    layer_rho = {layer: 0.0 for layer in SEGMENT_CONSUMERS}
    layer_rho.update({layer: None for layer in POINT_CONSUMERS})
    return {
        "certification_effective_radius_m": 0.025,
        "certification_margin_m": 0.01,
        "controller_radius_m": 0.015,
        "fallback_value_m": None,
        "layer_effective_radius_m": layer_radii,
        "layer_local_margin_without_source": False,
        "layer_rho_seg_m": layer_rho,
        "map_authority": "STATIC_IMMUTABLE_REPRESENTED_GAUSSIAN_MAP_AUTHORITY",
        "margin_application_count": 1,
        "rho_seg_m": 0.0,
        "v1_historical_valid": True,
    }
