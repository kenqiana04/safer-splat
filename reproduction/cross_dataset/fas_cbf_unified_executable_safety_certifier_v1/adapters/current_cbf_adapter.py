"""Read-only full-query post-check adapter for current CBF/map feasibility."""
from __future__ import annotations

from typing import Any,Callable

import math
import numpy as np

from certifier.result_types import BarrierQueryResult, BarrierStatus, State


class CurrentCBFAdapter:
    def __init__(self, barrier_adapter: Any, candidate_constraint_provider:Callable[[State],tuple[np.ndarray,np.ndarray]]|None=None, tolerance:float=1e-10) -> None:
        self.barrier_adapter=barrier_adapter
        self.candidate_constraint_provider=candidate_constraint_provider
        self.tolerance=float(tolerance)

    def query_current(self,state:State,use_reduced_query:bool=False)->tuple[BarrierQueryResult,BarrierQueryResult|None]:
        reduced=None
        if use_reduced_query:
            reduced=self.barrier_adapter.query(state.position,state.map_snapshot_id,"REDUCED_DIAGNOSTIC")
        full=self.barrier_adapter.query(state.position,state.map_snapshot_id,"FULL")
        return full,reduced

    def full_candidate_residual(self,state:State,control:Any)->tuple[str,float|None]:
        if self.candidate_constraint_provider is None:
            return "MAP_FEASIBILITY_ONLY",None
        try:
            a,b=self.candidate_constraint_provider(state)
            a=np.asarray(a,dtype=np.float64).reshape((-1,3)); b=np.asarray(b,dtype=np.float64).reshape((-1,))
            u=np.asarray(control.acceleration,dtype=np.float64)
            if len(a)!=len(b) or u.shape!=(3,) or not np.all(np.isfinite(a)) or not np.all(np.isfinite(b)) or not np.all(np.isfinite(u)):
                return "FULL_CBF_ROWS_NONFINITE_OR_SHAPE_MISMATCH",None
            residual=float(np.max(a@u-b)) if len(a) else -math.inf
            return "FULL_CBF_ROWS_PASS" if residual<=self.tolerance else "FULL_CBF_ROWS_INFEASIBLE",residual
        except Exception as exc:
            return "FULL_CBF_ROWS_ERROR:"+type(exc).__name__,None
