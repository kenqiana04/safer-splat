"""Finite braking-to-rest terminal-backup witness certification."""
from __future__ import annotations

import time

from adapters.normative_dynamics_adapter import PositionFirstForwardEulerDoubleIntegrator
from .actuator_certificate import certify_actuator
from .braking_backup_policy import DeterministicBrakingPolicy,ZeroActuatorAuthority
from .result_types import BackupWitness,Control,State
from .segment_certificate import SweptSegmentCertifier
from .terminal_certificate import TerminalCertifier


class BackupCertifier:
    def __init__(self,dynamics:PositionFirstForwardEulerDoubleIntegrator,segment_certifier:SweptSegmentCertifier,terminal_certifier:TerminalCertifier,braking_policy:DeterministicBrakingPolicy)->None:
        self.dynamics=dynamics; self.segment_certifier=segment_certifier
        self.terminal_certifier=terminal_certifier; self.braking_policy=braking_policy

    def certify(self,state:State,candidate:Control,expected_snapshot_id:str,deadline:float|None=None)->BackupWitness:
        states=[state]; segments=[]; controls=[]
        actuator=certify_actuator(candidate,self.dynamics.bounds)
        if not actuator.certified:
            return BackupWitness(False,candidate,(),tuple(states),(),None,0,expected_snapshot_id,"INITIAL_CANDIDATE_ACTUATOR_REJECT")
        immediate=self.segment_certifier.certify(state,candidate,expected_snapshot_id); segments.append(immediate)
        if not immediate.certified:
            return BackupWitness(False,candidate,(),tuple(states),tuple(segments),None,0,expected_snapshot_id,"IMMEDIATE_SEGMENT_NOT_CERTIFIED:"+immediate.reason_code)
        next_state=self.dynamics.transition(state,candidate); states.append(next_state)
        try: horizon=self.braking_policy.h_stop(next_state)
        except ZeroActuatorAuthority as exc:
            return BackupWitness(False,candidate,(),tuple(states),tuple(segments),None,0,expected_snapshot_id,"ZERO_ACTUATOR_AUTHORITY:"+str(exc))
        current=next_state
        for step in range(horizon):
            if deadline is not None and time.perf_counter()>deadline:
                return BackupWitness(False,candidate,tuple(controls),tuple(states),tuple(segments),None,horizon,expected_snapshot_id,"BACKUP_CERTIFICATION_BUDGET_EXHAUSTED")
            try: control=self.braking_policy.control_for_state(current,step)
            except ZeroActuatorAuthority as exc:
                return BackupWitness(False,candidate,tuple(controls),tuple(states),tuple(segments),None,horizon,expected_snapshot_id,"ZERO_ACTUATOR_AUTHORITY:"+str(exc))
            if not certify_actuator(control,self.dynamics.bounds).certified:
                return BackupWitness(False,candidate,tuple(controls),tuple(states),tuple(segments),None,horizon,expected_snapshot_id,"BACKUP_ACTUATOR_REJECT")
            segment=self.segment_certifier.certify(current,control,expected_snapshot_id); segments.append(segment)
            if not segment.certified:
                return BackupWitness(False,candidate,tuple(controls),tuple(states),tuple(segments),None,horizon,expected_snapshot_id,"BACKUP_SEGMENT_NOT_CERTIFIED:"+segment.reason_code)
            controls.append(control); current=self.dynamics.transition(current,control); states.append(current)
        terminal=self.terminal_certifier.certify(current,expected_snapshot_id)
        if terminal.zero_hold_segment is not None: segments.append(terminal.zero_hold_segment)
        # The final state is repeated to make the zero-hold transition explicit.
        if terminal.certified:
            zero=Control((0.0,0.0,0.0),"TERMINAL_ZERO_HOLD","terminal-zero-hold")
            states.append(self.dynamics.transition(current,zero))
        if not terminal.certified:
            return BackupWitness(False,candidate,tuple(controls),tuple(states),tuple(segments),terminal,horizon,expected_snapshot_id,"TERMINAL_CERTIFICATE_FAILED:"+terminal.reason_code)
        return BackupWitness(True,candidate,tuple(controls),tuple(states),tuple(segments),terminal,horizon,expected_snapshot_id,"BACKUP_WITNESS_CERTIFIED")
