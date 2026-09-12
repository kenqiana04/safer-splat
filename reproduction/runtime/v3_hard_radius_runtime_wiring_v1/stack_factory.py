"""Build and fail-closed audit a V3 stack using the frozen V2 composition.

The V2 builder has no registry-factory argument and is immutable evidence.  A
process-local, lock-guarded constructor scope therefore supplies the explicit
V3 geometry only while that existing builder creates the object graph.  The
original classmethod is restored in ``finally`` before this function returns.
"""

from __future__ import annotations

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
import importlib.util
import inspect
from pathlib import Path
import sys
from threading import RLock
from typing import Any, Callable, Iterator, Mapping

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.runtime_errors import AuthorityMismatch, DeadlineProfileRequired

from .geometry_policy import V3_GEOMETRY_POLICY, V3HardRadiusGeometryPolicy
from .stack_config import project_v3_runtime_config


_REGISTRY_CONSTRUCTION_LOCK = RLock()
_FROZEN_V2_RUNNER = Path("reproduction/smoke/active_runtime_smoke_v2/run_active_runtime_smoke_v2.py")


@dataclass(frozen=True)
class V3AuthorityRegistry(AuthorityRegistry):
    """Task-local registry that preserves every V2 authority except geometry."""

    def verify_all(self, active: bool = False) -> None:
        geometry = self.geometry
        values = (
            geometry.controller_radius_m,
            geometry.certification_margin_m,
            geometry.certification_effective_radius_m,
            geometry.rho_seg_m,
        )
        if geometry.identity.kind != "V3_HARD_RADIUS_GEOMETRY_AUTHORITY_V1" or values != (0.015, 0.0, 0.015, 0.0):
            raise AuthorityMismatch("V3_HARD_RADIUS_GEOMETRY_AUTHORITY_V1")
        if not self.map_identity:
            raise AuthorityMismatch("MAP_AUTHORITY_MISSING")
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


def make_v3_authority_registry(
    map_identity: str,
    dt_identity: str,
    deadline_profile_id: str | None = None,
    policy: V3HardRadiusGeometryPolicy = V3_GEOMETRY_POLICY,
) -> V3AuthorityRegistry:
    """Explicitly derive V3 from the frozen V2 non-geometry authorities."""

    policy.validate()
    base = AuthorityRegistry.frozen(map_identity, dt_identity, deadline_profile_id)
    return _registry_from_base(base, policy)


def _registry_from_base(
    base: AuthorityRegistry,
    policy: V3HardRadiusGeometryPolicy,
) -> V3AuthorityRegistry:
    return V3AuthorityRegistry(
        policy.to_geometry_authority(),
        base.actuator,
        base.dynamics,
        base.alternative,
        base.terminal,
        base.oracle,
        base.map_identity,
        base.transition_table_identity,
        base.deadline_profile_identity,
    )


def _unwrap(module: Any) -> Any:
    return getattr(module, "_module", module)


def _closure_value(function: Callable[..., Any], name: str) -> Any:
    try:
        values = inspect.getclosurevars(function).nonlocals
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"V3_WIRING_CLOSURE_UNAVAILABLE:{name}") from exc
    if name not in values:
        raise RuntimeError(f"V3_WIRING_CLOSURE_VALUE_MISSING:{name}")
    return values[name]


@contextmanager
def _explicit_v3_registry_scope(policy: V3HardRadiusGeometryPolicy) -> Iterator[None]:
    """Temporarily route the immutable V2 builder to an explicit V3 registry."""

    policy.validate()
    with _REGISTRY_CONSTRUCTION_LOCK:
        original_descriptor = AuthorityRegistry.__dict__["frozen"]
        original_factory = AuthorityRegistry.frozen

        def v3_frozen(
            cls: type[AuthorityRegistry],
            map_identity: str,
            dt_identity: str,
            deadline_profile_id: str | None = None,
        ) -> AuthorityRegistry:
            base = original_factory(map_identity, dt_identity, deadline_profile_id)
            return _registry_from_base(base, policy)

        setattr(AuthorityRegistry, "frozen", classmethod(v3_frozen))
        try:
            yield
        finally:
            setattr(AuthorityRegistry, "frozen", original_descriptor)


def validate_v3_stack_geometry(
    stack: Mapping[str, Any],
    projected_config: Mapping[str, Any],
    policy: V3HardRadiusGeometryPolicy = V3_GEOMETRY_POLICY,
) -> dict[str, Any]:
    """Prove the constructed object graph shares the one V3 geometry authority."""

    policy.validate()
    registry = stack.get("registry")
    coordinator = stack.get("coordinator")
    if not isinstance(registry, AuthorityRegistry) or coordinator is None:
        raise RuntimeError("V3_STACK_REQUIRED_OBJECTS_MISSING")
    registry.verify_all(active=True)

    start = _unwrap(coordinator.start_admission)
    l1 = _unwrap(coordinator.l1_runtime)
    l2 = _unwrap(coordinator.l2_runtime)
    l3 = _unwrap(coordinator.l3_runtime)
    terminal_runtime = _unwrap(coordinator.terminal_runtime)

    map_adapter = _closure_value(start._full_query, "map_adapter")
    l1_backend = _closure_value(l1._backend, "segment_backend")
    l2_backend = _closure_value(l2._backend, "segment_backend")
    backup_certifier = _closure_value(l3._builder, "backup_certifier")
    terminal_certifier = _closure_value(terminal_runtime._backend, "terminal_certifier")
    swept = backup_certifier.segment_certifier
    current_adapter = terminal_certifier.current_adapter

    expected = policy.hard_runtime_radius_q
    checks = {
        "registry_controller_radius_q": registry.geometry.controller_radius_m == expected,
        "registry_runtime_margin_q": registry.geometry.certification_margin_m == policy.runtime_margin_q,
        "registry_effective_radius_q": registry.geometry.certification_effective_radius_m == expected,
        "registry_rho_seg_q": registry.geometry.rho_seg_m == policy.rho_seg_q,
        "config_controller_radius_q": projected_config["controller"]["controller_radius"] == expected,
        "config_runtime_margin_q": projected_config["certification"]["certification_margin"] == policy.runtime_margin_q,
        "config_effective_radius_q": projected_config["certification"]["certification_effective_radius"] == expected,
        "config_rho_seg_q": projected_config["certification"]["rho_seg"] == policy.rho_seg_q,
        "map_adapter_effective_radius_q": getattr(map_adapter, "effective_radius", None) == expected,
        "l1_l2_share_segment_backend": l1_backend is l2_backend,
        "swept_uses_l1_l2_backend": getattr(swept, "backend", None) is l1_backend,
        "swept_effective_radius_q": getattr(swept, "effective_radius", None) == expected,
        "swept_rho_seg_q": getattr(swept, "rho_seg", None) == policy.rho_seg_q,
        "segment_backend_uses_map_adapter": getattr(l1_backend, "provider", None) is map_adapter,
        "current_adapter_uses_map_adapter": getattr(current_adapter, "barrier_adapter", None) is map_adapter,
        "terminal_shares_swept": terminal_certifier.segment_certifier is swept,
        "backup_shares_swept": backup_certifier.segment_certifier is swept,
        "backup_shares_terminal": backup_certifier.terminal_certifier is terminal_certifier,
        "historical_diagnostic_runtime_authority": policy.historical_diagnostic_runtime_authority is False,
    }
    failed = tuple(name for name, passed in checks.items() if not passed)
    if failed:
        raise RuntimeError("V3_STACK_GEOMETRY_WIRING_INVALID:" + ",".join(failed))
    return {
        "schema": "V3_RUNTIME_STACK_GEOMETRY_AUDIT_V1",
        "status": "PASS",
        "hard_runtime_radius_q": expected,
        "runtime_margin_q": policy.runtime_margin_q,
        "runtime_effective_radius_q": policy.runtime_effective_radius_q,
        "rho_seg_q": policy.rho_seg_q,
        "historical_diagnostic_radius_q": policy.historical_diagnostic_radius_q,
        "historical_diagnostic_runtime_authority": False,
        "checks": checks,
    }


def build_v3_stack(
    checkout: Any,
    output_dir: Any,
    trial_id: int,
    base_config: Mapping[str, Any],
    map_identity: str,
    *,
    v2_build_stack: Callable[..., Mapping[str, Any]],
    policy: V3HardRadiusGeometryPolicy = V3_GEOMETRY_POLICY,
) -> dict[str, Any]:
    """Reuse the supplied frozen V2 builder with explicit V3 geometry wiring."""

    projected = project_v3_runtime_config(base_config, policy)
    with _explicit_v3_registry_scope(policy):
        built = v2_build_stack(checkout, output_dir, int(trial_id), projected, str(map_identity))
    if not isinstance(built, Mapping):
        raise RuntimeError("V3_BASE_STACK_BUILDER_MAPPING_REQUIRED")
    stack = dict(built)
    audit = validate_v3_stack_geometry(stack, projected, policy)
    stack["v3_geometry_policy"] = policy
    stack["v3_projected_config"] = deepcopy(projected)
    stack["v3_wiring_audit"] = audit
    return stack


def load_frozen_v2_build_stack(checkout: Path) -> Callable[..., Mapping[str, Any]]:
    """Load the immutable V2 builder without executing its command-line entry."""

    root = Path(checkout).resolve(strict=True)
    runner_path = (root / _FROZEN_V2_RUNNER).resolve(strict=True)
    if root not in runner_path.parents:
        raise RuntimeError("V3_FROZEN_V2_RUNNER_OUTSIDE_CHECKOUT")
    module_name = "_v3_frozen_active_runtime_smoke_v2_builder"
    spec = importlib.util.spec_from_file_location(module_name, runner_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("V3_FROZEN_V2_RUNNER_IMPORT_SPEC_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(module_name)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            sys.modules.pop(module_name, None)
        else:
            sys.modules[module_name] = previous
    builder = getattr(module, "build_stack", None)
    if not callable(builder):
        raise RuntimeError("V3_FROZEN_V2_BUILD_STACK_UNAVAILABLE")
    return builder


def build_v3_stack_from_frozen_v2(
    checkout: Path,
    output_dir: Path,
    trial_id: int,
    base_config: Mapping[str, Any],
    map_identity: str,
    *,
    policy: V3HardRadiusGeometryPolicy = V3_GEOMETRY_POLICY,
) -> dict[str, Any]:
    """Project V3 geometry and reuse the exact V2 composition root."""

    return build_v3_stack(
        checkout,
        output_dir,
        trial_id,
        base_config,
        map_identity,
        v2_build_stack=load_frozen_v2_build_stack(checkout),
        policy=policy,
    )
