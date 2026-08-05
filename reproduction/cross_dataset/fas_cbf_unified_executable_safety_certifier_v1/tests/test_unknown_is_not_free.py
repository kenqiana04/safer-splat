from adapters.current_cbf_adapter import CurrentCBFAdapter
from adapters.gaussian_barrier_adapter import UnknownMapAdapter
from certifier.current_feasibility_certificate import certify_current_feasibility
from certifier.result_types import BarrierStatus,State


def test_unknown_rejected():
    state=State((0.,0.,0.),(0.,0.,0.),0.,"m")
    cert=certify_current_feasibility(state,CurrentCBFAdapter(UnknownMapAdapter("m",BarrierStatus.UNKNOWN)))
    assert not cert.certified and cert.reason_code=="CURRENT_MAP_QUERY_UNKNOWN"
    assert cert.reference_online_read_count==0
