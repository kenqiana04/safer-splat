import numpy as np
from alternative_library.represented_sphere_frame import build_frame


def test_tangent_frame_is_right_handed_and_orthogonal():
    status, normal, tangent, auxiliary = build_frame(np.array((1., 0., 0.)), np.array((1., 2., 3.)), np.zeros(3))
    assert status == "AVAILABLE"
    assert max(abs(normal @ tangent), abs(normal @ auxiliary), abs(tangent @ auxiliary)) <= 1e-10
    assert np.linalg.det(np.column_stack((normal, tangent, auxiliary))) > 0.0
