"""Dense sampled oracle for diagnostics only; never yields a formal pass."""
from __future__ import annotations

import numpy as np

from certifier.result_types import SegmentCertificate, SegmentStatus
from .base import SignedDistanceProvider, barrier_from_signed_distance


class SampledDiagnosticBackend:
    method = "DENSE_SAMPLED_DIAGNOSTIC_ONLY"

    def __init__(self, provider: SignedDistanceProvider, samples: int = 4097) -> None:
        self.provider=provider; self.samples=int(samples)

    def diagnose(self,start:np.ndarray,end:np.ndarray,map_snapshot_id:str,expected_snapshot_id:str,effective_radius:float,rho_seg:float=0.0)->SegmentCertificate:
        if map_snapshot_id!=expected_snapshot_id or self.provider.map_snapshot_id!=expected_snapshot_id:
            return SegmentCertificate(SegmentStatus.MAP_SNAPSHOT_MISMATCH,False,None,None,self.method,"DIAGNOSTIC_ONLY",map_snapshot_id,0,"MAP_SNAPSHOT_MISMATCH")
        best=float("inf"); best_t=0.0; evaluated=0
        for t in np.linspace(0.0,1.0,self.samples):
            status,signed,count=self.provider.minimum_signed_distance(np.asarray(start)+(np.asarray(end)-np.asarray(start))*t); evaluated=max(evaluated,count)
            if status!="FINITE" or signed is None:
                return SegmentCertificate(SegmentStatus.MAP_QUERY_UNKNOWN if status=="UNKNOWN" else SegmentStatus.MAP_QUERY_NONFINITE,False,None,float(t),self.method,"DIAGNOSTIC_ONLY",map_snapshot_id,evaluated,"DIAGNOSTIC_QUERY_FAILURE")
            h=barrier_from_signed_distance(signed,effective_radius)-rho_seg
            if h<best: best,best_t=h,float(t)
        return SegmentCertificate(SegmentStatus.CERTIFIED_UNSAFE if best<0 else SegmentStatus.NOT_CERTIFIED_WITHIN_BUDGET,False,best,best_t,self.method,"DIAGNOSTIC_ONLY",map_snapshot_id,evaluated,"DIAGNOSTIC_UNSAFE_WITNESS" if best<0 else "DIAGNOSTIC_NO_COUNTEREXAMPLE_NOT_A_CERTIFICATE")
