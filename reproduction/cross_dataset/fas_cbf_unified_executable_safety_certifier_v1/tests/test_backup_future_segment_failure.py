from certifier.result_types import ActuatorBounds,Control,State
from conftest import build_stack


def test_future_braking_segment_failure():
    bounds=ActuatorBounds((-0.5,)*3,(0.5,)*3,(-1.,)*3,(1.,)*3,0.1)
    # Immediate segment [0,.04] is safe; candidate makes v=.25 and the next
    # braking segment [0.04,.065] crosses the represented obstacle.
    stack=build_stack(centers=((0.065,0.,0.),),primitive_radius=0.002,effective_radius=0.002,bounds=bounds)
    state=State((0.,0.,0.),(0.4,0.,0.),0.,"map-v1")
    witness=stack["backup"].certify(state,Control((-0.5,0.,0.),"NOMINAL","n"),"map-v1")
    assert not witness.certified and witness.reason_code.startswith("BACKUP_SEGMENT_NOT_CERTIFIED")
