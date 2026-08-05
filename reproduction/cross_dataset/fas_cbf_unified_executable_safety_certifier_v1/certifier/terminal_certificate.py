"""Online terminal certificate with a mandatory zero-hold segment."""
from __future__ import annotations

from adapters.current_cbf_adapter import CurrentCBFAdapter
from .current_feasibility_certificate import certify_current_feasibility
from .result_types import Control, SegmentStatus, State, TerminalCertificate
from .segment_certificate import SweptSegmentCertifier
from .terminal_set import BrakingToRestTerminalSet


ASSUMPTIONS=(
    "STATIC_MAP_SNAPSHOT",
    "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1",
    "COMPONENTWISE_BOUNDED_ACCELERATION",
    "NO_MODELING_DISTURBANCE",
    "NO_ACTUATION_DELAY",
    "NO_TRACKING_ERROR",
    "UNKNOWN_IS_NOT_FREE",
    "SUFFICIENT_NOT_MAXIMAL_TERMINAL_SET",
)


class TerminalCertifier:
    def __init__(self,terminal_set:BrakingToRestTerminalSet,current_adapter:CurrentCBFAdapter,segment_certifier:SweptSegmentCertifier)->None:
        self.terminal_set=terminal_set; self.current_adapter=current_adapter; self.segment_certifier=segment_certifier

    def certify(self,state:State,expected_snapshot_id:str)->TerminalCertificate:
        if state.map_snapshot_id!=expected_snapshot_id:
            return TerminalCertificate(False,state,False,ASSUMPTIONS,"TERMINAL_MAP_SNAPSHOT_MISMATCH",self.terminal_set.velocity_tolerance)
        if not self.terminal_set.velocity_is_terminal(state):
            return TerminalCertificate(False,state,False,ASSUMPTIONS,"TERMINAL_VELOCITY_NOT_ZERO_WITHIN_TOLERANCE",self.terminal_set.velocity_tolerance)
        zero=Control((0.0,0.0,0.0),"TERMINAL_ZERO_HOLD","terminal-zero-hold")
        current=certify_current_feasibility(state,self.current_adapter,zero)
        if not current.certified:
            return TerminalCertificate(False,state,False,ASSUMPTIONS,"TERMINAL_CURRENT_MAP_UNSAFE_OR_UNKNOWN:"+current.reason_code,self.terminal_set.velocity_tolerance)
        segment=self.segment_certifier.certify(state,zero,expected_snapshot_id)
        if not segment.certified:
            return TerminalCertificate(False,state,False,ASSUMPTIONS,"TERMINAL_ZERO_HOLD_NOT_CERTIFIED:"+segment.reason_code,self.terminal_set.velocity_tolerance,segment)
        return TerminalCertificate(True,state,True,ASSUMPTIONS,"TERMINAL_SET_CERTIFIED",self.terminal_set.velocity_tolerance,segment)
