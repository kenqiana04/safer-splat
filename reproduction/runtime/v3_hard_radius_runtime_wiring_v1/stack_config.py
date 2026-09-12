"""Project a V2-compatible configuration into the frozen V3 geometry."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .geometry_policy import V3_GEOMETRY_POLICY, V3HardRadiusGeometryPolicy


def _mapping(config: dict[str, Any], key: str) -> dict[str, Any]:
    value = config.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"V3_BASE_CONFIG_{key.upper()}_MAPPING_REQUIRED")
    return value


def project_v3_runtime_config(
    base_config: Mapping[str, Any],
    policy: V3HardRadiusGeometryPolicy = V3_GEOMETRY_POLICY,
) -> dict[str, Any]:
    """Return a defensive V3 projection without mutating ``base_config``."""

    if not isinstance(base_config, Mapping):
        raise TypeError("V3_BASE_CONFIG_MAPPING_REQUIRED")
    policy.validate()
    projected = deepcopy(dict(base_config))
    controller = _mapping(projected, "controller")
    certification = _mapping(projected, "certification")

    controller["controller_radius"] = policy.hard_runtime_radius_q
    certification["certification_margin"] = policy.runtime_margin_q
    certification["certification_effective_radius"] = policy.runtime_effective_radius_q
    certification["rho_seg"] = policy.rho_seg_q

    diagnostics = projected.setdefault("diagnostics", {})
    if not isinstance(diagnostics, dict):
        raise ValueError("V3_BASE_CONFIG_DIAGNOSTICS_MAPPING_REQUIRED")
    diagnostics["historical_v2_geometry"] = {
        "historical_v2_reserve_shell_q": policy.historical_diagnostic_radius_q,
        "historical_design_reserve_q": policy.historical_design_reserve_q,
        "runtime_authority": False,
        "diagnostic_only": True,
        "historical_v2_only": True,
        "coordinate_unit": "q",
    }
    projected["runtime_geometry_authority"] = {
        "schema": policy.schema,
        "hard_runtime_radius_q": policy.hard_runtime_radius_q,
        "runtime_margin_q": policy.runtime_margin_q,
        "runtime_effective_radius_q": policy.runtime_effective_radius_q,
        "rho_seg_q": policy.rho_seg_q,
        "coordinate_unit": policy.coordinate_unit,
    }
    return projected
