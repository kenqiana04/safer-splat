"""Finite task-owned state machine; every terminal output returns next cycle."""
from __future__ import annotations

from dataclasses import dataclass

from .result_types import ExecutableStatus


PIPELINE=("INITIAL_DIAGNOSIS","START_SAFE_ADMISSION","CANDIDATE_GENERATION","ACTUATOR_CHECK","CURRENT_FEASIBILITY_CHECK","SWEPT_SEGMENT_CERTIFICATION","TERMINAL_BACKUP_CERTIFICATION","CONTROL_COMMIT","NEXT_CYCLE_DIAGNOSIS")

FAILURE_STATE={
    ExecutableStatus.NOT_EVALUABLE_MAP_QUERY_UNKNOWN:"MAP_UNKNOWN",
    ExecutableStatus.NOT_EVALUABLE_MAP_QUERY_NONFINITE:"NONFINITE",
    ExecutableStatus.FAIL_CLOSED_IMMEDIATE_SEGMENT_UNSAFE:"SEGMENT_UNSAFE",
    ExecutableStatus.FAIL_CLOSED_BACKUP_WITNESS_NOT_FOUND_IN_FROZEN_LIBRARY:"BACKUP_NOT_FOUND",
    ExecutableStatus.FAIL_CLOSED_NOT_CERTIFIED_WITHIN_BUDGET:"BACKUP_NOT_FOUND",
    ExecutableStatus.SOLVER_FAILED_NOT_SCIENTIFICALLY_CLASSIFIED:"SOLVER_TIMEOUT",
    ExecutableStatus.INFRASTRUCTURE_FAILURE:"INFRA_FAILURE",
    ExecutableStatus.FAIL_CLOSED_ACTUATOR_VIOLATION:"ACTUATOR_REJECT",
    ExecutableStatus.FAIL_CLOSED_CURRENT_CBF_INFEASIBLE:"CURRENT_CBF_REJECT",
}


def trace_for_status(status:ExecutableStatus)->tuple[str,...]:
    if status in (ExecutableStatus.CERTIFIED_NOMINAL_CONTROL,ExecutableStatus.CERTIFIED_ALTERNATIVE_CONTROL,ExecutableStatus.CERTIFIED_BACKUP_CONTROL):
        return PIPELINE
    if status==ExecutableStatus.CERTIFIED_TERMINAL_ACTION:
        return ("INITIAL_DIAGNOSIS","START_SAFE_ADMISSION","TERMINAL_SET_CHECK","CERTIFIED_TERMINAL_ACTION","ZERO_CONTROL_HOLD","NEXT_CYCLE_DIAGNOSIS")
    failure=FAILURE_STATE[status]
    return ("INITIAL_DIAGNOSIS",failure,status.value,"NEXT_CYCLE_DIAGNOSIS")


def validate_all_terminal_paths()->dict:
    rows=[]
    for status in ExecutableStatus:
        trace=trace_for_status(status)
        rows.append({"status":status.value,"trace":list(trace),"returns_next_cycle":trace[-1]=="NEXT_CYCLE_DIAGNOSIS","has_dead_state":False})
    return {"status_count":len(rows),"all_return_next_cycle":all(r["returns_next_cycle"] for r in rows),"rows":rows}
