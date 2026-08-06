from methods.b2_primary_and_braking_wrapper import CandidateSpec, b2_call_spec, b2_ordered_candidate_roles


def test_b2_uses_only_frozen_primary_and_builtin_braking():
    primary = CandidateSpec("PRIMARY-CBF-FILTERED", "EXISTING_CBF_FILTERED", (0., 0., 0.))
    call = b2_call_spec(primary)
    assert call.nominal_control == primary and call.external_alternative_controls == ()
    assert b2_ordered_candidate_roles(primary) == ("PRIMARY-CBF-FILTERED", "DETERMINISTIC_BRAKING")
