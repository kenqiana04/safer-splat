import numpy as np
from certifier.segment_backends.analytic_primitive import ExactSphereSegmentBackend


def test_exact_tangent_boundary_is_inclusive():
    backend=ExactSphereSegmentBackend(np.asarray([[0.,1.,0.]]),0.5,"m")
    cert=backend.certify(np.asarray([-1.,0.,0.]),np.asarray([1.,0.,0.]),"m","m",0.5)
    assert cert.certified and abs(cert.lower_bound)<=1e-15
    assert cert.exact_or_conservative=="EXACT_ANALYTIC"
