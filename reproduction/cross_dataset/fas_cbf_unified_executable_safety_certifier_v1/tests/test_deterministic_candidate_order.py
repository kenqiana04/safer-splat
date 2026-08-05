from certifier.candidate_library import frozen_candidate_order
from certifier.result_types import Control


def test_deterministic_candidate_order(moving_state,free_stack):
    nominal=Control((0.,0.,0.),"NOMINAL","nominal")
    alts=(Control((0.,0.,0.),"TASK_LOCAL_ALTERNATIVE","z"),Control((0.,0.,0.),"EXISTING_CBF_FILTERED","filtered"),Control((0.,0.,0.),"TASK_LOCAL_ALTERNATIVE","a"))
    ids=[c.candidate_id for c in frozen_candidate_order(moving_state,nominal,alts,free_stack["policy"])]
    assert ids==["nominal","filtered","a","z","brake--001"]
