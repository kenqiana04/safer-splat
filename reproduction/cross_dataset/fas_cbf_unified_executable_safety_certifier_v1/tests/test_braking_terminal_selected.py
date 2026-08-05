from certifier.result_types import Control,ExecutableStatus


def test_braking_candidate_selected(moving_state,free_stack):
    nominal=Control((2.,0.,0.),"NOMINAL","nominal")
    result=free_stack["unified"].certify(moving_state,nominal,(),"map-v1",5.0)
    assert result.status==ExecutableStatus.CERTIFIED_BACKUP_CONTROL
    assert result.committed_control_or_none.source=="DETERMINISTIC_BRAKING_BACKUP"
