from certifier.result_types import Control,ExecutableStatus


def test_alternative_selected_after_nominal_rejection(moving_state,free_stack):
    nominal=Control((2.,0.,0.),"NOMINAL","nominal")
    alt=Control((0.,0.,0.),"TASK_LOCAL_ALTERNATIVE","alt-01")
    result=free_stack["unified"].certify(moving_state,nominal,(alt,),"map-v1",5.0)
    assert result.status==ExecutableStatus.CERTIFIED_ALTERNATIVE_CONTROL
    assert result.committed_control_or_none.candidate_id=="alt-01"
    assert result.rejected_candidates[0].stage=="ACTUATOR_CHECK"
