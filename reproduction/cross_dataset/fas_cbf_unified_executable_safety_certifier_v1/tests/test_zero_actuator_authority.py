import pytest
from certifier.braking_backup_policy import DeterministicBrakingPolicy,ZeroActuatorAuthority
from certifier.result_types import ActuatorBounds,State


def test_zero_actuator_authority_typed_failure():
    bounds=ActuatorBounds((0.,-1.,-1.),(0.,1.,1.),(-1.,)*3,(1.,)*3,0.1)
    policy=DeterministicBrakingPolicy(bounds,1e-12)
    with pytest.raises(ZeroActuatorAuthority):
        policy.control_for_state(State((0.,0.,0.),(0.1,0.,0.),0.,"m"))
