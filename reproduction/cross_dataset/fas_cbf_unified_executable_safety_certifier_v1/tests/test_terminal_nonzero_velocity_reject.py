def test_terminal_nonzero_velocity_rejected(moving_state,free_stack):
    cert=free_stack["terminal"].certify(moving_state,"map-v1")
    assert not cert.certified and cert.reason_code=="TERMINAL_VELOCITY_NOT_ZERO_WITHIN_TOLERANCE"
