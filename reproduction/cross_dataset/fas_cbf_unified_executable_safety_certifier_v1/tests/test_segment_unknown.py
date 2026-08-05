import numpy as np
from adapters.gaussian_barrier_adapter import UnknownMapAdapter
from certifier.segment_backends.conservative_interval import ConservativeSignedDistanceIntervalBackend


def test_unknown_anywhere_fails_closed():
    backend=ConservativeSignedDistanceIntervalBackend(UnknownMapAdapter("m"))
    cert=backend.certify(np.zeros(3),np.ones(3),"m","m",0.1)
    assert not cert.certified and cert.reason_code=="MAP_QUERY_UNKNOWN"
