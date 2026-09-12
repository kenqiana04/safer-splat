"""Frozen V3 hard-radius policy in Stonehenge query-space units (q)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import GeometryAuthority
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import AuthorityIdentity, canonical_sha256


@dataclass(frozen=True)
class V3HardRadiusGeometryPolicy:
    """The sole V3 action-producing geometry authority.

    The historical shell remains metadata only and has no runtime authority.
    """

    schema: str = "V3_HARD_RADIUS_GEOMETRY_POLICY_V1"
    coordinate_unit: str = "q"
    coordinate_semantics: str = "STONEHENGE_NERFSTUDIO_SCALED_REPRESENTED_MAP_QUERY_COORDINATE"
    hard_runtime_radius_q: float = 0.015
    runtime_margin_q: float = 0.0
    runtime_effective_radius_q: float = 0.015
    rho_seg_q: float = 0.0
    historical_diagnostic_radius_q: float = 0.025
    historical_diagnostic_runtime_authority: bool = False
    historical_design_reserve_q: float = 0.010
    historical_design_reserve_runtime_authority: bool = False
    historical_design_reserve_diagnostic_only: bool = True
    historical_design_reserve_v2_only: bool = True

    def validate(self) -> None:
        if self.coordinate_unit != "q":
            raise ValueError("V3_QUERY_SPACE_UNIT_MUST_BE_Q")
        if self.hard_runtime_radius_q != 0.015:
            raise ValueError("V3_HARD_RADIUS_AUTHORITY_DRIFT")
        if self.runtime_margin_q != 0.0:
            raise ValueError("V3_RUNTIME_MARGIN_MUST_BE_ZERO")
        if self.runtime_effective_radius_q != self.hard_runtime_radius_q:
            raise ValueError("V3_EFFECTIVE_RADIUS_MUST_EQUAL_HARD_RADIUS")
        if self.rho_seg_q != 0.0:
            raise ValueError("V3_RHO_SEG_MUST_BE_ZERO")
        if self.historical_diagnostic_radius_q <= self.hard_runtime_radius_q:
            raise ValueError("HISTORICAL_DIAGNOSTIC_SHELL_ORDERING_DRIFT")
        if self.historical_diagnostic_runtime_authority is not False:
            raise ValueError("HISTORICAL_DIAGNOSTIC_RUNTIME_AUTHORITY_FORBIDDEN")
        if self.historical_design_reserve_runtime_authority is not False:
            raise ValueError("HISTORICAL_RESERVE_RUNTIME_AUTHORITY_FORBIDDEN")
        if not self.historical_design_reserve_diagnostic_only or not self.historical_design_reserve_v2_only:
            raise ValueError("HISTORICAL_RESERVE_METADATA_CONTRACT_DRIFT")

    def to_geometry_authority(self) -> GeometryAuthority:
        self.validate()
        payload = {
            "controller": self.hard_runtime_radius_q,
            "margin": self.runtime_margin_q,
            "effective": self.runtime_effective_radius_q,
            "rho": self.rho_seg_q,
            "map": "G3",
            "coordinate_unit": self.coordinate_unit,
            "runtime_authority": "V3_HARD_RADIUS",
        }
        identity = AuthorityIdentity(
            "V3_HARD_RADIUS_GEOMETRY_AUTHORITY_V1",
            "v3_hard_radius_geometry_authority_v1:sha256:" + canonical_sha256(payload),
        )
        return GeometryAuthority(
            identity,
            self.hard_runtime_radius_q,
            self.runtime_margin_q,
            self.runtime_effective_radius_q,
            self.rho_seg_q,
        )

    def to_dict(self) -> dict[str, Any]:
        self.validate()
        return asdict(self)


V3_GEOMETRY_POLICY = V3HardRadiusGeometryPolicy()
V3_GEOMETRY_POLICY.validate()
