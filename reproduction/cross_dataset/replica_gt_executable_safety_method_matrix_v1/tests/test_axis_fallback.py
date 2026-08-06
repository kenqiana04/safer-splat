import numpy as np
from alternative_library.represented_sphere_frame import build_frame


def test_parallel_goal_uses_fixed_axis_tie_order():
    status, normal, tangent, auxiliary = build_frame(np.array((1., 0., 0.)), np.array((2., 0., 0.)), np.zeros(3))
    assert status == "GOAL_DEGENERATE_AXIS_FALLBACK_USED"
    assert np.allclose(normal, (1., 0., 0.)) and np.allclose(tangent, (0., 1., 0.)) and np.allclose(auxiliary, (0., 0., 1.))
