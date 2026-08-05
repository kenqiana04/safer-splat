from certifier.result_types import BackupWitness,Control,ExecutableStatus


def test_solver_budget_failure_not_unrecoverable(moving_state,free_stack):
    def timeout(state,candidate,snapshot,deadline=None):
        return BackupWitness(False,candidate,(),(state,),(),None,0,snapshot,"BACKUP_CERTIFICATION_BUDGET_EXHAUSTED")
    free_stack["backup"].certify=timeout
    result=free_stack["unified"].certify(moving_state,Control((0.,0.,0.),"NOMINAL","nominal"),(),"map-v1",5.0)
    assert result.status==ExecutableStatus.FAIL_CLOSED_NOT_CERTIFIED_WITHIN_BUDGET
    assert "CERTIFIED_UNRECOVERABLE" not in result.to_json()
