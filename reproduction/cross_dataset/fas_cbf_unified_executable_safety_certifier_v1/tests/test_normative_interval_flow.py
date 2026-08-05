from certifier.result_types import ActuatorBounds,Control,State
from adapters.normative_dynamics_adapter import PositionFirstForwardEulerDoubleIntegrator


def test_interval_flow_matches_end_transition_position():
    b=ActuatorBounds((-1.,)*3,(1.,)*3,(-2.,)*3,(2.,)*3,0.2); m=PositionFirstForwardEulerDoubleIntegrator(b)
    s=State((0.,0.,0.),(1.,2.,3.),0.,"m"); u=Control((.5,.5,.5),"N","n")
    assert m.interval_state(s,u,0.0)==s
    assert m.interval_state(s,u,0.2)==m.transition(s,u)
    mid=m.interval_state(s,u,0.1)
    assert mid.position==(0.1,0.2,0.30000000000000004)
