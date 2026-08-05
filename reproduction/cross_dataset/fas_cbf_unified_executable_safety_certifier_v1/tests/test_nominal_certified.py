from certifier.result_types import Control,ExecutableStatus


def test_nominal_certified(moving_state,free_stack):
    result=free_stack["unified"].certify(moving_state,Control((0.,0.,0.),"NOMINAL","nominal"),(),"map-v1",5.0)
    assert result.status==ExecutableStatus.CERTIFIED_NOMINAL_CONTROL
    assert result.committed_control_or_none.candidate_id=="nominal"
    assert result.backup_witness.certified
