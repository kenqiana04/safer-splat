"""Conservative signed-distance interval certification by 1-Lipschitz bounds."""
from __future__ import annotations

from collections import deque
import math
import numpy as np

from certifier.result_types import SegmentCertificate, SegmentStatus
from .base import SignedDistanceProvider, barrier_from_signed_distance


class ConservativeSignedDistanceIntervalBackend:
    method = "CONSERVATIVE_SIGNED_DISTANCE_LIPSCHITZ_INTERVAL"

    def __init__(self, provider: SignedDistanceProvider, node_budget: int = 4096, parameter_tolerance: float = 1e-10) -> None:
        self.provider = provider
        self.node_budget = int(node_budget)
        self.parameter_tolerance = float(parameter_tolerance)

    def certify(self, start: np.ndarray, end: np.ndarray, map_snapshot_id: str, expected_snapshot_id: str, effective_radius: float, rho_seg: float = 0.0) -> SegmentCertificate:
        start=np.asarray(start,dtype=np.float64); end=np.asarray(end,dtype=np.float64)
        if map_snapshot_id != expected_snapshot_id or self.provider.map_snapshot_id != expected_snapshot_id:
            return SegmentCertificate(SegmentStatus.MAP_SNAPSHOT_MISMATCH,False,None,None,self.method,"CONSERVATIVE_LOWER_BOUND",map_snapshot_id,0,"MAP_SNAPSHOT_MISMATCH")
        if start.shape!=(3,) or end.shape!=(3,) or not np.all(np.isfinite(start)) or not np.all(np.isfinite(end)):
            return SegmentCertificate(SegmentStatus.MAP_QUERY_NONFINITE,False,None,None,self.method,"CONSERVATIVE_LOWER_BOUND",map_snapshot_id,0,"NONFINITE_SEGMENT")
        length=float(np.linalg.norm(end-start)); queue=deque([(0.0,1.0)]); nodes=0; evaluated=0; global_lower=math.inf
        while queue:
            a,b=queue.popleft(); mid=0.5*(a+b); point=start+mid*(end-start)
            status,signed,count=self.provider.minimum_signed_distance(point); nodes+=1; evaluated=max(evaluated,int(count))
            if status=="UNKNOWN":
                return SegmentCertificate(SegmentStatus.MAP_QUERY_UNKNOWN,False,None,(a,b),self.method,"CONSERVATIVE_LOWER_BOUND",map_snapshot_id,evaluated,"MAP_QUERY_UNKNOWN",nodes)
            if status!="FINITE" or signed is None or not math.isfinite(float(signed)):
                return SegmentCertificate(SegmentStatus.MAP_QUERY_NONFINITE,False,None,(a,b),self.method,"CONSERVATIVE_LOWER_BOUND",map_snapshot_id,evaluated,"MAP_QUERY_NONFINITE",nodes)
            exact_h=barrier_from_signed_distance(float(signed),effective_radius)-rho_seg
            if exact_h < 0.0:
                return SegmentCertificate(SegmentStatus.CERTIFIED_UNSAFE,False,float(exact_h),float(mid),self.method,"CONSERVATIVE_LOWER_BOUND",map_snapshot_id,evaluated,"FINITE_UNSAFE_WITNESS",nodes)
            signed_lower=float(signed)-0.5*(b-a)*length
            lower=barrier_from_signed_distance(signed_lower,effective_radius)-rho_seg
            global_lower=min(global_lower,lower)
            if lower >= 0.0:
                continue
            if nodes >= self.node_budget or (b-a) <= self.parameter_tolerance:
                return SegmentCertificate(SegmentStatus.NOT_CERTIFIED_WITHIN_BUDGET,False,float(global_lower),(a,b),self.method,"CONSERVATIVE_LOWER_BOUND",map_snapshot_id,evaluated,"INTERVAL_BOUND_INCONCLUSIVE",nodes)
            queue.append((a,mid)); queue.append((mid,b))
        return SegmentCertificate(SegmentStatus.CERTIFIED_SAFE,True,float(global_lower),None,self.method,"CONSERVATIVE_LOWER_BOUND",map_snapshot_id,evaluated,"SEGMENT_CONSERVATIVE_SAFE",nodes)
