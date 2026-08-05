from certifier.current_feasibility_certificate import certify_current_feasibility
import numpy as np
from adapters.current_cbf_adapter import CurrentCBFAdapter
from certifier.result_types import Control,State


def test_full_query_postcheck_required(free_stack):
    state=State((0.,0.,0.),(0.,0.,0.),0.,"map-v1")
    cert=certify_current_feasibility(state,free_stack["current"],Control((0.,0.,0.),"N","n"),use_reduced_query=True)
    assert cert.certified and cert.reduced_query_used and cert.full_query_postcheck_performed
    assert cert.full_query.query_scope=="FULL"


def test_full_candidate_rows_reject_even_when_map_query_passes(free_stack):
    state=State((0.,0.,0.),(0.,0.,0.),0.,"map-v1")
    provider=lambda state:(np.asarray([[1.,0.,0.]]),np.asarray([-0.1]))
    adapter=CurrentCBFAdapter(free_stack["adapter"],provider)
    cert=certify_current_feasibility(state,adapter,Control((0.,0.,0.),"N","n"),use_reduced_query=True)
    assert not cert.certified and cert.reason_code=="FULL_CBF_ROWS_INFEASIBLE"
    assert cert.full_query_postcheck_performed and cert.candidate_control_checked
