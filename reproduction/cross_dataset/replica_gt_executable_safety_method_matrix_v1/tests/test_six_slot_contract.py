import numpy as np
from alternative_library.directional_library import build_directional_library
from task_config import SLOT_IDS


def test_generator_always_returns_the_six_frozen_slots():
    record = build_directional_library((1., 0., 0.), (-0.02, 0., 0.), (1., 2., 0.), "FINITE", (0,), np.array(((0., 0., 0.),)))
    assert tuple(slot.candidate_id for slot in record.slots) == SLOT_IDS
    assert len(record.slots) == 6 and record.active_primitive_id == 0
