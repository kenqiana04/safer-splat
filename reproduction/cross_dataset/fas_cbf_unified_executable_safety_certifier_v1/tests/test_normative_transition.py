from certifier.result_types import ActuatorBounds,Control,State
from adapters.normative_dynamics_adapter import PositionFirstForwardEulerDoubleIntegrator,diagnostic_constant_acceleration_zoh


def test_position_first_transition():
    b=ActuatorBounds((-1.,)*3,(1.,)*3,(-2.,)*3,(2.,)*3,0.25)
    m=PositionFirstForwardEulerDoubleIntegrator(b)
    s=State((1.,2.,3.),(0.4,-0.2,0.0),5.0,"m")
    u=Control((1.,-1.,0.5),"NOMINAL","n")
    out=m.transition(s,u)
    assert out.position==(1.1,1.95,3.0)
    assert out.velocity==(0.65,-0.45,0.125)
    assert out.timestamp==5.25
    assert diagnostic_constant_acceleration_zoh(s,u,0.25).position!=out.position
