import numpy as np
from alternative_library.directional_library import build_directional_library
from methods.b2_primary_and_braking_wrapper import CandidateSpec
from methods.b3_directional_library_wrapper import b3_ordered_candidate_roles


def test_b3_order_is_primary_then_slots_then_builtin_braking():
    generated = build_directional_library((1., 0., 0.), (-0.02, 0., 0.), (1., 2., 0.), "FINITE", (0,), np.array(((0., 0., 0.),)))
    primary = CandidateSpec("PRIMARY-CBF-FILTERED", "EXISTING_CBF_FILTERED", (0., 0., 0.))
    ordered = b3_ordered_candidate_roles(primary, generated)
    assert ordered[0] == "PRIMARY-CBF-FILTERED" and ordered[-1] == "DETERMINISTIC_BRAKING"
    assert list(ordered[1:-1]) == [slot.candidate_id for slot in generated.available_slots]
