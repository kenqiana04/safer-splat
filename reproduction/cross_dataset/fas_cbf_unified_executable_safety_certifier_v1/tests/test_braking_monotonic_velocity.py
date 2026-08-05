from certifier.result_types import State


def test_braking_never_reverses_velocity(free_stack,moving_state):
    policy=free_stack["policy"]; dynamics=free_stack["dynamics"]; state=moving_state
    for step in range(policy.h_stop(state)):
        nxt=dynamics.transition(state,policy.control_for_state(state,step))
        assert 0.0<=nxt.velocity[0]<=state.velocity[0]
        state=nxt
