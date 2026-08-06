import numpy as np
from alternative_library.directional_library import build_directional_library
from alternative_library.result_types import SlotAvailability


def test_unknown_map_has_no_reference_fallback():
    record = build_directional_library((1., 0., 0.), (0., 0., 0.), (2., 0., 0.), "UNKNOWN", (), np.zeros((1, 3)))
    assert all(slot.availability == SlotAvailability.MAP_QUERY_UNAVAILABLE for slot in record.slots)
    assert all(slot.provenance["reference_input"] is False for slot in record.slots)
