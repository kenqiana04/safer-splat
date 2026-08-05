"""Current represented-map feasibility certificate."""
from __future__ import annotations

from adapters.current_cbf_adapter import CurrentCBFAdapter
from .result_types import BarrierStatus, Control, CurrentFeasibilityCertificate, State


def certify_current_feasibility(state:State,adapter:CurrentCBFAdapter,control:Control|None=None,use_reduced_query:bool=False)->CurrentFeasibilityCertificate:
    full,reduced=adapter.query_current(state,use_reduced_query)
    if full.map_snapshot_id!=state.map_snapshot_id or full.reason_code=="MAP_SNAPSHOT_MISMATCH": reason="MAP_SNAPSHOT_MISMATCH"
    elif full.status==BarrierStatus.UNKNOWN: reason="CURRENT_MAP_QUERY_UNKNOWN"
    elif full.status==BarrierStatus.NONFINITE: reason="CURRENT_MAP_QUERY_NONFINITE"
    elif full.status==BarrierStatus.ERROR: reason="CURRENT_MAP_QUERY_ERROR"
    elif full.h is None or full.h<0.0: reason="CURRENT_FULL_QUERY_INFEASIBLE"
    else: reason="CURRENT_FULL_QUERY_FEASIBLE"
    passed=reason=="CURRENT_FULL_QUERY_FEASIBLE"
    mode="MAP_FEASIBILITY_ONLY"; residual=None; candidate_checked=False
    if passed and control is not None:
        mode,residual=adapter.full_candidate_residual(state,control); candidate_checked=True
        if mode not in ("MAP_FEASIBILITY_ONLY","FULL_CBF_ROWS_PASS"):
            passed=False; reason=mode
        elif mode=="FULL_CBF_ROWS_PASS": reason="CURRENT_FULL_CBF_AND_MAP_FEASIBLE"
    return CurrentFeasibilityCertificate(passed,reason,full,use_reduced_query,True,0,candidate_checked,mode,residual)
