"""Deterministic IMPLEMENTATION_TEST_FIXTURES; these are not datasets or evidence."""
from __future__ import annotations

import numpy as np

from frozen_backend_adapter import (
    ConservativeSignedDistanceIntervalBackend,
    ExactSphereSegmentBackend,
    SampledDiagnosticBackend,
)
from l2_h1_shadow_certifier import propagate_h1_endpoints
from shadow_contract import CONSERVATIVE_ELLIPSOID_IDENTITY, DENSE_DIAGNOSTIC_IDENTITY, EXACT_SPHERE_IDENTITY
from shadow_types import ExpectedMapSnapshot, FrozenMapQueryContext, RobotMarginContract, ShadowCandidate, ShadowState

SNAPSHOT_ID = "synthetic-map-snapshot-v1"
SNAPSHOT_SHA256 = "implementation-test-fixture-not-authoritative"


class ExactSphereAsClosedEllipsoidProvider:
    """Exact signed distance to a sphere, a closed isotropic ellipsoid subcase."""
    primitive_family = "CLOSED_ELLIPSOID_SPECIAL_CASE_SPHERE"

    def __init__(self, center=(0.0, 0.0, 0.0), radius=0.5, map_snapshot_id=SNAPSHOT_ID):
        self.center = np.asarray(center, dtype=np.float64)
        self.radius = float(radius)
        self.map_snapshot_id = map_snapshot_id

    def minimum_signed_distance(self, point):
        point = np.asarray(point, dtype=np.float64)
        if point.shape != (3,) or not np.all(np.isfinite(point)):
            return "NONFINITE", None, 1
        return "FINITE", float(np.linalg.norm(point - self.center) - self.radius), 1


class ConstantDistanceBudgetProvider:
    primitive_family = "SYNTHETIC_BUDGET_PATH_ONLY"

    def __init__(self, value=0.2, map_snapshot_id=SNAPSHOT_ID):
        self.value = float(value)
        self.map_snapshot_id = map_snapshot_id

    def minimum_signed_distance(self, point):
        return "FINITE", self.value, 1


class UnsupportedBackend:
    method = "UNSUPPORTED_TASK_FIXTURE_BACKEND"


class SpoofingExactBackend:
    method = EXACT_SPHERE_IDENTITY


def _state_candidate_for_segment(start, end, candidate_id="candidate", dt=1.0):
    start = np.asarray(start, dtype=np.float64); end = np.asarray(end, dtype=np.float64)
    p_k = np.zeros(3, dtype=np.float64)
    v_k = start.copy()
    u_k = end - 2.0 * start
    return ShadowState(tuple(p_k), tuple(v_k), "fixture-state", dt), ShadowCandidate(tuple(u_k), candidate_id)


def _expected():
    return ExpectedMapSnapshot(SNAPSHOT_ID, SNAPSHOT_SHA256)


def sphere_case(name):
    if name == "safe":
        start, end, primitive_radius = (2.0, 2.0, 0.0), (3.0, 2.0, 0.0), 0.5
    elif name in ("intersection", "endpoint_trap"):
        start, end, primitive_radius = (-1.0, 0.0, 0.0), (1.0, 0.0, 0.0), 0.5
    elif name == "tangent":
        start, end, primitive_radius = (-1.0, 0.5, 0.0), (1.0, 0.5, 0.0), 0.38999999999999996
    else:
        raise ValueError(name)
    state, candidate = _state_candidate_for_segment(start, end, f"sphere-{name}")
    backend = ExactSphereSegmentBackend(np.asarray([[0.0, 0.0, 0.0]]), np.asarray([primitive_radius]), SNAPSHOT_ID)
    context = FrozenMapQueryContext(backend, SNAPSHOT_ID, EXACT_SPHERE_IDENTITY, "EXACT_ANALYTIC", None, "ISOTROPIC_SPHERE", SNAPSHOT_SHA256)
    return state, candidate, _expected(), context


def conservative_case(name):
    if name == "safe":
        start, end = (2.0, 2.0, 0.0), (2.1, 2.0, 0.0)
        provider = ExactSphereAsClosedEllipsoidProvider()
        budget = 4096
    elif name == "intersection":
        start, end = (-1.0, 0.0, 0.0), (1.0, 0.0, 0.0)
        provider = ExactSphereAsClosedEllipsoidProvider()
        budget = 4096
    elif name == "budget":
        start, end = (-1.0, 0.0, 0.0), (1.0, 0.0, 0.0)
        provider = ConstantDistanceBudgetProvider()
        budget = 1
    else:
        raise ValueError(name)
    state, candidate = _state_candidate_for_segment(start, end, f"conservative-{name}")
    backend = ConservativeSignedDistanceIntervalBackend(provider, node_budget=budget, parameter_tolerance=1e-10)
    context = FrozenMapQueryContext(backend, SNAPSHOT_ID, CONSERVATIVE_ELLIPSOID_IDENTITY, "CONSERVATIVE_LOWER_BOUND", None, provider.primitive_family, SNAPSHOT_SHA256)
    return state, candidate, _expected(), context


def candidate_sensitivity_case():
    state = ShadowState((0.0, 0.0, 0.0), (1.0, 0.5, 0.0), "sensitivity-state", 0.5)
    a = ShadowCandidate((0.0, 0.0, 0.0), "candidate-a")
    b = ShadowCandidate((0.4, -0.2, 0.1), "candidate-b")
    backend = ExactSphereSegmentBackend(np.asarray([[10.0, 10.0, 10.0]]), np.asarray([0.5]), SNAPSHOT_ID)
    context = FrozenMapQueryContext(backend, SNAPSHOT_ID, EXACT_SPHERE_IDENTITY, "EXACT_ANALYTIC", None, "ISOTROPIC_SPHERE", SNAPSHOT_SHA256)
    return state, a, b, _expected(), context


def diagnostic_context(context, samples, diagnostic_as_formal=False):
    provider = ExactSphereAsClosedEllipsoidProvider()
    diagnostic = SampledDiagnosticBackend(provider, samples=samples)
    if diagnostic_as_formal:
        return FrozenMapQueryContext(diagnostic, SNAPSHOT_ID, DENSE_DIAGNOSTIC_IDENTITY, "DIAGNOSTIC_ONLY", diagnostic, provider.primitive_family, SNAPSHOT_SHA256)
    return FrozenMapQueryContext(context.formal_backend, context.actual_map_snapshot_id, context.backend_identity, context.backend_class, diagnostic, context.primitive_family, context.actual_map_snapshot_sha256)


def unsupported_context():
    return FrozenMapQueryContext(UnsupportedBackend(), SNAPSHOT_ID, UnsupportedBackend.method, "UNSUPPORTED", None, "UNSUPPORTED", SNAPSHOT_SHA256)


def exploding_context():
    backend = ExactSphereSegmentBackend(np.asarray([[0.0, 0.0, 0.0]]), np.asarray([0.5]), SNAPSHOT_ID)

    def explode(*args, **kwargs):
        raise RuntimeError("TASK_FIXTURE_BACKEND_EXCEPTION")

    backend.certify = explode
    return FrozenMapQueryContext(backend, SNAPSHOT_ID, EXACT_SPHERE_IDENTITY, "EXACT_ANALYTIC", None, "ISOTROPIC_SPHERE", SNAPSHOT_SHA256)


def spoofed_context():
    return FrozenMapQueryContext(SpoofingExactBackend(), SNAPSHOT_ID, EXACT_SPHERE_IDENTITY, "EXACT_ANALYTIC", None, "ISOTROPIC_SPHERE", SNAPSHOT_SHA256)


def direct_frozen_certificate(fixture, robot: RobotMarginContract):
    state, candidate, snapshot, context = fixture
    propagation = propagate_h1_endpoints(state, candidate, state.dt)
    return context.formal_backend.certify(
        np.asarray(propagation.p_k1),
        np.asarray(propagation.p_k2),
        context.actual_map_snapshot_id,
        snapshot.snapshot_id,
        robot.effective_radius_m,
        robot.rho_seg,
    )
