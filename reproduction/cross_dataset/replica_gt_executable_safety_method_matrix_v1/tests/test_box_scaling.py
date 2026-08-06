import numpy as np
from alternative_library.actuator_box_scaling import scale_to_box
from alternative_library.result_types import Bounds, SlotAvailability


def test_box_scaling_reaches_a_boundary_without_clipping():
    status, control = scale_to_box(np.array((2., -1., 0.5)), Bounds())
    assert status == SlotAvailability.AVAILABLE and np.allclose(control, (0.1, -0.05, 0.025))
    assert np.max(np.abs(control)) == 0.1
