import numpy as np
from certifier.segment_backends.analytic_primitive import ExactSphereSegmentBackend


def test_endpoint_safe_interior_unsafe():
    backend=ExactSphereSegmentBackend(np.asarray([[0.,0.,0.]]),0.2,"m")
    cert=backend.certify(np.asarray([-1.,0.,0.]),np.asarray([1.,0.,0.]),"m","m",0.1)
    assert not cert.certified and cert.reason_code=="SEGMENT_EXACT_UNSAFE"
    assert 0.0<cert.witness_time_or_interval<1.0
