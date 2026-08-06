import numpy as np
from alternative_library.directional_library import build_directional_library
from task_config import AXIS_DEGENERATE_CASES, PROPERTY_SEED, SYNTHETIC_GEOMETRY_CASES


def test_twenty_thousand_random_geometries_and_five_thousand_axis_cases_are_finite_and_bounded():
    rng = np.random.default_rng(PROPERTY_SEED)
    centers = np.zeros((1, 3))
    for index in range(SYNTHETIC_GEOMETRY_CASES + AXIS_DEGENERATE_CASES):
        position = rng.normal(size=3) + np.array((0.5, 0.0, 0.0))
        velocity = rng.uniform(-0.1, 0.1, size=3)
        goal = position + (position if index >= SYNTHETIC_GEOMETRY_CASES else rng.normal(size=3))
        record = build_directional_library(position, velocity, goal, "FINITE", (0,), centers)
        for slot in record.available_slots:
            control = np.asarray(slot.acceleration)
            assert np.all(np.isfinite(control)) and np.all(np.abs(control) <= 0.1 + 1e-12)
            if slot.candidate_id.startswith("ALT-05") or slot.candidate_id.startswith("ALT-06"):
                assert float(velocity @ control) <= 1e-10
