import numpy as np
from alternative_library.directional_library import build_directional_library
from methods.b2_primary_and_braking_wrapper import CandidateSpec, b2_call_spec
from methods.b3_directional_library_wrapper import b3_call_spec


def test_b3_only_adds_available_directional_slots_to_b2():
    primary = CandidateSpec("PRIMARY-CBF-FILTERED", "EXISTING_CBF_FILTERED", (0., 0., 0.))
    generated = build_directional_library((1., 0., 0.), (-0.02, 0., 0.), (1., 2., 0.), "FINITE", (0,), np.array(((0., 0., 0.),)))
    b2, b3 = b2_call_spec(primary), b3_call_spec(primary, generated)
    assert b3.nominal_control == b2.nominal_control and b3.builtin_braking_role == b2.builtin_braking_role
    assert b2.external_alternative_controls == () and len(b3.external_alternative_controls) == len(generated.available_slots)
