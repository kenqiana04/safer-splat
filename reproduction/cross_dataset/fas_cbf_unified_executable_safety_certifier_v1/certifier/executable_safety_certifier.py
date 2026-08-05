"""Unified candidate-level actuator/CBF/segment/backup certifier."""
from __future__ import annotations

import time

from adapters.current_cbf_adapter import CurrentCBFAdapter
from .actuator_certificate import certify_actuator
from .backup_certifier import BackupCertifier
from .braking_backup_policy import DeterministicBrakingPolicy
from .candidate_library import frozen_candidate_order
from .current_feasibility_certificate import certify_current_feasibility
from .result_types import BarrierStatus,Control,ExecutableSafetyResult,ExecutableStatus,RejectedCandidate,SegmentStatus,State
from .segment_certificate import SweptSegmentCertifier
from .terminal_certificate import TerminalCertifier


class ExecutableSafetyCertifier:
    identity="UNIFIED_EXECUTABLE_SAFETY_CERTIFIER_V1"

    def __init__(self,current_adapter:CurrentCBFAdapter,segment_certifier:SweptSegmentCertifier,terminal_certifier:TerminalCertifier,backup_certifier:BackupCertifier,braking_policy:DeterministicBrakingPolicy,immutable_identities:dict[str,str])->None:
        self.current_adapter=current_adapter; self.segment_certifier=segment_certifier
        self.terminal_certifier=terminal_certifier; self.backup_certifier=backup_certifier
        self.braking_policy=braking_policy; self.immutable_identities=dict(immutable_identities)

    def certify(self,state:State,nominal_control:Control,alternative_controls:tuple[Control,...],map_snapshot:str,time_budget:float)->ExecutableSafetyResult:
        started=time.perf_counter(); timing={}; rejected=[]; last_actuator=None; last_current=None; last_segment=None; last_backup=None
        if not state.finite or not isinstance(time_budget,(int,float)) or time_budget<=0:
            return self._result(ExecutableStatus.INFRASTRUCTURE_FAILURE,None,None,None,None,None,(),"INVALID_STATE_OR_TIME_BUDGET","NOT_CLASSIFIED","INVALID_INPUT",timing)
        if state.map_snapshot_id!=map_snapshot:
            return self._result(ExecutableStatus.NOT_EVALUABLE_MAP_QUERY_UNKNOWN,None,None,None,None,None,(),"MAP_SNAPSHOT_MISMATCH","NOT_EVALUABLE","OK",timing)
        deadline=started+float(time_budget)
        terminal=self.terminal_certifier.certify(state,map_snapshot)
        if terminal.certified:
            zero=Control((0.0,0.0,0.0),"TERMINAL_ZERO_HOLD","terminal-zero-hold")
            witness=self.backup_certifier.certify(state,zero,map_snapshot,deadline)
            if witness.certified:
                timing["total"]=time.perf_counter()-started
                return self._result(ExecutableStatus.CERTIFIED_TERMINAL_ACTION,zero,certify_actuator(zero,self.backup_certifier.dynamics.bounds),certify_current_feasibility(state,self.current_adapter,zero),terminal.zero_hold_segment,witness,(),None,"CERTIFIED","OK",timing)
        candidates=frozen_candidate_order(state,nominal_control,alternative_controls,self.braking_policy)
        for candidate in candidates:
            if time.perf_counter()>deadline:
                timing["total"]=time.perf_counter()-started
                return self._result(ExecutableStatus.SOLVER_FAILED_NOT_SCIENTIFICALLY_CLASSIFIED,None,last_actuator,last_current,last_segment,last_backup,tuple(rejected),"TIME_BUDGET_EXHAUSTED","NOT_CLASSIFIED","OK",timing)
            t=time.perf_counter(); actuator=certify_actuator(candidate,self.backup_certifier.dynamics.bounds); timing["actuator_check"]=timing.get("actuator_check",0.0)+time.perf_counter()-t; last_actuator=actuator
            if not actuator.certified:
                rejected.append(RejectedCandidate(candidate.candidate_id,candidate.source,actuator.reason_code,"ACTUATOR_CHECK")); continue
            t=time.perf_counter(); current=certify_current_feasibility(state,self.current_adapter,candidate,use_reduced_query=False); timing["current_cbf_query"]=timing.get("current_cbf_query",0.0)+time.perf_counter()-t; last_current=current
            if not current.certified:
                rejected.append(RejectedCandidate(candidate.candidate_id,candidate.source,current.reason_code,"CURRENT_FEASIBILITY_CHECK"))
                if current.full_query.status in (BarrierStatus.UNKNOWN,BarrierStatus.NONFINITE,BarrierStatus.ERROR): break
                continue
            t=time.perf_counter(); segment=self.segment_certifier.certify(state,candidate,map_snapshot); timing["segment_certification"]=timing.get("segment_certification",0.0)+time.perf_counter()-t; last_segment=segment
            if not segment.certified:
                rejected.append(RejectedCandidate(candidate.candidate_id,candidate.source,segment.reason_code,"SWEPT_SEGMENT_CERTIFICATION"))
                if segment.status in (SegmentStatus.MAP_QUERY_UNKNOWN,SegmentStatus.MAP_QUERY_NONFINITE,SegmentStatus.MAP_SNAPSHOT_MISMATCH): break
                continue
            t=time.perf_counter(); witness=self.backup_certifier.certify(state,candidate,map_snapshot,deadline); timing["backup_rollout"]=timing.get("backup_rollout",0.0)+time.perf_counter()-t; last_backup=witness
            if not witness.certified:
                rejected.append(RejectedCandidate(candidate.candidate_id,candidate.source,witness.reason_code,"TERMINAL_BACKUP_CERTIFICATION")); continue
            if candidate.candidate_id==nominal_control.candidate_id: out=ExecutableStatus.CERTIFIED_NOMINAL_CONTROL
            elif candidate.source=="DETERMINISTIC_BRAKING_BACKUP": out=ExecutableStatus.CERTIFIED_BACKUP_CONTROL
            else: out=ExecutableStatus.CERTIFIED_ALTERNATIVE_CONTROL
            timing["terminal_check"]=0.0; timing["total"]=time.perf_counter()-started
            return self._result(out,candidate,actuator,current,segment,witness,tuple(rejected),None,"CERTIFIED","OK",timing)
        timing["total"]=time.perf_counter()-started
        status=self._failure_status(last_actuator,last_current,last_segment,last_backup,rejected)
        return self._result(status,None,last_actuator,last_current,last_segment,last_backup,tuple(rejected),status.value,"FAIL_CLOSED_NOT_CERTIFIED_WITHIN_FROZEN_LIBRARY","OK",timing)

    def _failure_status(self,actuator,current,segment,backup,rejected):
        if current is not None:
            if current.full_query.status==BarrierStatus.UNKNOWN: return ExecutableStatus.NOT_EVALUABLE_MAP_QUERY_UNKNOWN
            if current.full_query.status in (BarrierStatus.NONFINITE,BarrierStatus.ERROR): return ExecutableStatus.NOT_EVALUABLE_MAP_QUERY_NONFINITE
            if not current.certified: return ExecutableStatus.FAIL_CLOSED_CURRENT_CBF_INFEASIBLE
        if segment is not None:
            if segment.status==SegmentStatus.CERTIFIED_UNSAFE: return ExecutableStatus.FAIL_CLOSED_IMMEDIATE_SEGMENT_UNSAFE
            if segment.status==SegmentStatus.NOT_CERTIFIED_WITHIN_BUDGET: return ExecutableStatus.FAIL_CLOSED_NOT_CERTIFIED_WITHIN_BUDGET
        if backup is not None and "BUDGET" in backup.reason_code: return ExecutableStatus.FAIL_CLOSED_NOT_CERTIFIED_WITHIN_BUDGET
        if backup is not None: return ExecutableStatus.FAIL_CLOSED_BACKUP_WITNESS_NOT_FOUND_IN_FROZEN_LIBRARY
        if actuator is not None and not actuator.certified: return ExecutableStatus.FAIL_CLOSED_ACTUATOR_VIOLATION
        return ExecutableStatus.FAIL_CLOSED_BACKUP_WITNESS_NOT_FOUND_IN_FROZEN_LIBRARY

    def _result(self,status,control,actuator,current,segment,backup,rejected,reason,scientific,infrastructure,timing):
        return ExecutableSafetyResult(status,control,actuator,current,segment,backup,rejected,reason,scientific,infrastructure,dict(timing),dict(self.immutable_identities))
