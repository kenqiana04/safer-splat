import numpy as np
from alternative_library.directional_library import build_directional_library
from alternative_library.result_types import SlotAvailability


def test_earlier_slot_wins_when_outward_and_brake_biased_outward_match():
    record = build_directional_library((1., 0., 0.), (-0.02, 0., 0.), (1., 2., 0.), "FINITE", (0,), np.array(((0., 0., 0.),)))
    last = record.slots[-1]
    assert last.availability == SlotAvailability.DUPLICATE_OF_EARLIER_SLOT and last.duplicate_of == "ALT-01-OUTWARD"
