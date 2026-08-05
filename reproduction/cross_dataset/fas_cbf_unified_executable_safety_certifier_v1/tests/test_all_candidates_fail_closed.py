from certifier.result_types import BackupWitness,Control,ExecutableStatus


def test_candidate_exhaustion_is_bounded_non_certification(moving_state,free_stack):
    def reject(state,candidate,snapshot,deadline=None):
        return BackupWitness(False,candidate,(),(state,),(),None,0,snapshot,"FROZEN_LIBRARY_NO_WITNESS")
    free_stack["backup"].certify=reject
    result=free_stack["unified"].certify(moving_state,Control((0.,0.,0.),"NOMINAL","nominal"),(),"map-v1",5.0)
    assert result.status==ExecutableStatus.FAIL_CLOSED_BACKUP_WITNESS_NOT_FOUND_IN_FROZEN_LIBRARY
    assert result.committed_control_or_none is None
    assert "UNRECOVERABLE" not in result.to_json()
