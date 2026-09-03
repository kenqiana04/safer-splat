"""Read-only registry for PR #108–#114 runtime authorities."""

from __future__ import annotations

from dataclasses import dataclass

from .runtime_errors import AuthorityMismatch, DeadlineProfileRequired
from .runtime_types import AuthorityIdentity, canonical_sha256


@dataclass(frozen=True)
class GeometryAuthority:
    identity: AuthorityIdentity
    controller_radius_m: float = 0.015
    certification_margin_m: float = 0.010
    certification_effective_radius_m: float = 0.025
    rho_seg_m: float = 0.0
    map_class: str = "G3_STATIC_IMMUTABLE_REPRESENTED_GAUSSIAN_MAP"


@dataclass(frozen=True)
class ActuatorAuthority:
    identity: AuthorityIdentity
    u_min: tuple[float, float, float] = (-0.1, -0.1, -0.1)
    u_max: tuple[float, float, float] = (0.1, 0.1, 0.1)
    inclusive: bool = True


@dataclass(frozen=True)
class DynamicsAuthority:
    identity: AuthorityIdentity
    model: str
    dt_identity: str


@dataclass(frozen=True)
class AlternativeAuthority:
    identity: AuthorityIdentity
    default_source: str = "SOURCE_NATIVE_EXISTING"
    synthetic_allowed: bool = False


@dataclass(frozen=True)
class TerminalAuthority:
    identity: AuthorityIdentity
    zero_hold: tuple[float, float, float] = (0.0, 0.0, 0.0)
    goal_hold_enabled: bool = False


@dataclass(frozen=True)
class OracleBoundaryAuthority:
    identity: AuthorityIdentity
    feedback_authority: bool = False


@dataclass(frozen=True)
class AuthorityRegistry:
    geometry: GeometryAuthority
    actuator: ActuatorAuthority
    dynamics: DynamicsAuthority
    alternative: AlternativeAuthority
    terminal: TerminalAuthority
    oracle: OracleBoundaryAuthority
    map_identity: str
    transition_table_identity: str
    deadline_profile_identity: str | None = None

    @classmethod
    def frozen(cls, map_identity: str, dt_identity: str, deadline_profile_id: str | None = None) -> "AuthorityRegistry":
        aid = lambda kind, payload: AuthorityIdentity(kind, kind.lower() + ":sha256:" + canonical_sha256(payload))
        geometry = GeometryAuthority(aid("CERTIFICATION_GEOMETRY_AUTHORITY_V2", {"controller": 0.015, "margin": 0.010, "effective": 0.025, "rho": 0.0, "map": "G3"}))
        actuator = ActuatorAuthority(aid("NORMATIVE_COMPONENTWISE_ACCELERATION_AUTHORITY_V2", {"min": (-0.1,) * 3, "max": (0.1,) * 3, "inclusive": True}))
        dynamics = DynamicsAuthority(aid("DYNAMICS_TIMEBASE_AUTHORITY_V2", {"model": "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1", "dt_identity": dt_identity}), "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1", str(dt_identity))
        alternative = AlternativeAuthority(aid("ALTERNATIVE_SOURCE_AUTHORITY", {"source": "SOURCE_NATIVE_EXISTING", "synthetic": False}))
        terminal = TerminalAuthority(aid("TERMINAL_EMERGENCY_POLICY_V2", {"zero": (0.0, 0.0, 0.0), "goal_hold": False}))
        oracle = OracleBoundaryAuthority(aid("POSTHOC_EVALUATION_ORACLE", {"feedback": False}))
        return cls(geometry, actuator, dynamics, alternative, terminal, oracle, str(map_identity), "3c95f749a1f517f1be9e4ab6ad82b096a47afdad", deadline_profile_id)

    def verify_all(self, active: bool = False) -> None:
        if not self.map_identity:
            raise AuthorityMismatch("MAP_AUTHORITY_MISSING")
        if self.geometry.controller_radius_m != 0.015 or self.geometry.certification_margin_m != 0.010 or self.geometry.certification_effective_radius_m != 0.025 or self.geometry.rho_seg_m != 0.0:
            raise AuthorityMismatch("CERTIFICATION_GEOMETRY_AUTHORITY_V2")
        if self.actuator.u_min != (-0.1, -0.1, -0.1) or self.actuator.u_max != (0.1, 0.1, 0.1) or not self.actuator.inclusive:
            raise AuthorityMismatch("NORMATIVE_COMPONENTWISE_ACCELERATION_AUTHORITY_V2")
        if self.dynamics.model != "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1" or not self.dynamics.dt_identity:
            raise AuthorityMismatch("DYNAMICS_TIMEBASE_AUTHORITY_V2")
        if self.alternative.default_source != "SOURCE_NATIVE_EXISTING" or self.alternative.synthetic_allowed:
            raise AuthorityMismatch("ALTERNATIVE_SOURCE_AUTHORITY")
        if self.terminal.zero_hold != (0.0, 0.0, 0.0) or self.terminal.goal_hold_enabled:
            raise AuthorityMismatch("TERMINAL_EMERGENCY_POLICY_V2")
        if self.oracle.feedback_authority:
            raise AuthorityMismatch("POSTHOC_EVALUATION_ORACLE")
        if active and not self.deadline_profile_identity:
            raise DeadlineProfileRequired("DEADLINE_PROFILE_REQUIRED")
