from certifier.result_types import ActuatorBounds,Control,State
from conftest import build_stack


def test_immediate_segment_failure_cannot_be_repaired():
    bounds=ActuatorBounds((-1.,)*3,(1.,)*3,(-2.,)*3,(2.,)*3,1.0)
    stack=build_stack(centers=((0.,0.,0.),),primitive_radius=0.2,effective_radius=0.1,bounds=bounds)
    state=State((-1.,0.,0.),(2.,0.,0.),0.,"map-v1")
    witness=stack["backup"].certify(state,Control((-1.,0.,0.),"NOMINAL","n"),"map-v1")
    assert not witness.certified and witness.reason_code.startswith("IMMEDIATE_SEGMENT_NOT_CERTIFIED")
