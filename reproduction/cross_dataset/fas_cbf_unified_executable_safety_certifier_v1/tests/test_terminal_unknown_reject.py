from adapters.current_cbf_adapter import CurrentCBFAdapter
from adapters.gaussian_barrier_adapter import UnknownMapAdapter
from adapters.normative_dynamics_adapter import PositionFirstForwardEulerDoubleIntegrator
from certifier.result_types import ActuatorBounds,State
from certifier.segment_backends.conservative_interval import ConservativeSignedDistanceIntervalBackend
from certifier.segment_certificate import SweptSegmentCertifier
from certifier.terminal_certificate import TerminalCertifier
from certifier.terminal_set import BrakingToRestTerminalSet


def test_terminal_unknown_rejected(bounds):
    unknown=UnknownMapAdapter("m"); dynamics=PositionFirstForwardEulerDoubleIntegrator(bounds)
    segment=SweptSegmentCertifier(dynamics,ConservativeSignedDistanceIntervalBackend(unknown),0.1)
    terminal=TerminalCertifier(BrakingToRestTerminalSet(1e-12),CurrentCBFAdapter(unknown),segment)
    cert=terminal.certify(State((0.,0.,0.),(0.,0.,0.),0.,"m"),"m")
    assert not cert.certified and "UNKNOWN" in cert.reason_code
