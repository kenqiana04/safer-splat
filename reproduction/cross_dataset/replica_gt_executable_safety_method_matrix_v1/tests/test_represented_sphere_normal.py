import numpy as np
from alternative_library.represented_sphere_frame import build_frame


def test_represented_sphere_outward_normal_and_center_degeneracy():
    status, normal, _, _ = build_frame(np.array((2., 0., 0.)), np.array((2., 1., 0.)), np.zeros(3))
    assert status == "AVAILABLE" and np.allclose(normal, (1., 0., 0.))
    status, normal, _, _ = build_frame(np.zeros(3), np.ones(3), np.zeros(3))
    assert status == "NORMAL_DEGENERATE" and normal is None
