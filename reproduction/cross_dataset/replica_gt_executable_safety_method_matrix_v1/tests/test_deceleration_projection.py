import numpy as np
from alternative_library.deceleration_projection import project_kinetic_nonincrease
from alternative_library.result_types import SlotAvailability
from task_config import PROJECTION_CASES, PROPERTY_SEED


def test_projection_removes_positive_kinetic_component_and_keeps_nonpositive_one():
    status, projected = project_kinetic_nonincrease(np.array((1., 0., 0.)), np.array((1., 1., 0.)))
    assert status == SlotAvailability.AVAILABLE and abs(projected[0]) <= 1e-12
    status, retained = project_kinetic_nonincrease(np.array((1., 0., 0.)), np.array((-1., 1., 0.)))
    assert status == SlotAvailability.AVAILABLE and np.allclose(retained, np.array((-1., 1., 0.)) / np.sqrt(2.0))


def test_brake_biased_cancellation_is_degenerate():
    status, projected = project_kinetic_nonincrease(np.array((1., 0., 0.)), np.zeros(3))
    assert status == SlotAvailability.DEGENERATE_AFTER_DECELERATION_PROJECTION and projected is None


def test_five_thousand_random_halfspace_projections():
    rng = np.random.default_rng(PROPERTY_SEED)
    for _ in range(PROJECTION_CASES):
        velocity, direction = rng.normal(size=3), rng.normal(size=3)
        status, projected = project_kinetic_nonincrease(velocity, direction)
        if status == SlotAvailability.AVAILABLE:
            assert np.all(np.isfinite(projected)) and float(velocity @ projected) <= 1e-10
