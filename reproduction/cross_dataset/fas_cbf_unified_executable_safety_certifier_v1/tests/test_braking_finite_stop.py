from certifier.result_types import State


def test_braking_reaches_numerical_zero(free_stack):
    state=State((0.,0.,0.),(0.23,-0.17,0.01),0.,"map-v1")
    horizon=free_stack["policy"].h_stop(state)
    assert horizon==5
    for step in range(horizon): state=free_stack["dynamics"].transition(state,free_stack["policy"].control_for_state(state,step))
    assert max(abs(v) for v in state.velocity)<=1e-12
    assert free_stack["policy"].h_stop_max()==20
