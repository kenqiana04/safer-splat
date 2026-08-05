def test_terminal_zero_velocity_hold(zero_state,free_stack):
    cert=free_stack["terminal"].certify(zero_state,"map-v1")
    assert cert.certified and cert.zero_hold_certified
    assert cert.zero_hold_segment.certified
