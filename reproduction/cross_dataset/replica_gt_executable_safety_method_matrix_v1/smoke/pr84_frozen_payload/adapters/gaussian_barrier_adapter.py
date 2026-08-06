"""Read-only Gaussian barrier adapters with snapshot and UNKNOWN discipline."""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Callable

import numpy as np

from certifier.result_types import BarrierQueryResult, BarrierStatus
from certifier.segment_backends.base import barrier_from_signed_distance
from certifier.segment_backends.analytic_primitive import ExactSphereSegmentBackend


class AnalyticSphereGaussianMapAdapter:
    """Exact represented-obstacle adapter for isotropic Gaussian safety spheres."""

    def __init__(self, centers: np.ndarray, primitive_radii: np.ndarray | float, map_snapshot_id: str, effective_radius: float) -> None:
        self.centers=np.asarray(centers,dtype=np.float64)
        self.primitive_radii=np.broadcast_to(np.asarray(primitive_radii,dtype=np.float64),(len(self.centers),)).copy()
        self.map_snapshot_id=map_snapshot_id
        self.effective_radius=float(effective_radius)
        if self.centers.ndim!=2 or self.centers.shape[1]!=3 or not np.all(np.isfinite(self.centers)) or not np.all(np.isfinite(self.primitive_radii)):
            raise ValueError("INVALID_SPHERE_GAUSSIAN_MAP")
        try:
            from scipy.spatial import cKDTree
            self.tree=cKDTree(self.centers)
        except ImportError:
            self.tree=None
        self._last_index=0
        self.segment_backend=ExactSphereSegmentBackend(self.centers,self.primitive_radii,map_snapshot_id)

    @classmethod
    def from_canonical_arrays(cls, root: Path, map_snapshot_id: str, effective_radius: float) -> "AnalyticSphereGaussianMapAdapter":
        centers=np.load(Path(root)/"means_world_m.npy",mmap_mode="r")
        scales=np.load(Path(root)/"scales_linear_m.npy",mmap_mode="r")
        if scales.ndim!=2 or scales.shape[1]!=3 or not np.allclose(scales[:,0],scales[:,1]) or not np.allclose(scales[:,0],scales[:,2]):
            raise ValueError("MAP_NOT_ISOTROPIC_SPHERE_PRIMITIVES")
        return cls(centers,scales[:,0],map_snapshot_id,effective_radius)

    def minimum_signed_distance(self, point: np.ndarray) -> tuple[str,float|None,int]:
        point=np.asarray(point,dtype=np.float64)
        if point.shape!=(3,) or not np.all(np.isfinite(point)):
            return "NONFINITE",None,len(self.centers)
        if self.tree is not None:
            distance,index=self.tree.query(point,k=1)
            signed=float(distance-self.primitive_radii[int(index)])
        else:
            best=float("inf"); index=0
            for offset in range(0,len(self.centers),200_000):
                centers=np.asarray(self.centers[offset:offset+200_000],dtype=np.float64)
                signed_chunk=np.linalg.norm(centers-point[None,:],axis=1)-self.primitive_radii[offset:offset+len(centers)]
                local=int(np.argmin(signed_chunk))
                if float(signed_chunk[local])<best: best=float(signed_chunk[local]); index=offset+local
            signed=best
        self._last_index=int(index)
        return "FINITE",signed,len(self.centers)

    def query(self, point: np.ndarray, expected_snapshot_id: str, query_scope: str="FULL") -> BarrierQueryResult:
        if expected_snapshot_id!=self.map_snapshot_id:
            return BarrierQueryResult(BarrierStatus.ERROR,None,None,None,(),self.map_snapshot_id,query_scope=query_scope,reason_code="MAP_SNAPSHOT_MISMATCH")
        status,signed,count=self.minimum_signed_distance(point)
        if status!="FINITE" or signed is None:
            bstatus=BarrierStatus.NONFINITE if status=="NONFINITE" else BarrierStatus.UNKNOWN
            return BarrierQueryResult(bstatus,None,None,None,(),self.map_snapshot_id,query_scope=query_scope,reason_code="MAP_QUERY_"+status,evaluated_gaussian_count=count)
        index=self._last_index
        center=np.asarray(self.centers[int(index)],dtype=np.float64); delta=np.asarray(point,dtype=np.float64)-center
        norm=float(np.linalg.norm(delta)); grad=(0.0,0.0,0.0) if norm<=1e-15 else tuple(float(2.0*signed*x/norm) for x in delta)
        return BarrierQueryResult(BarrierStatus.FINITE,barrier_from_signed_distance(signed,self.effective_radius),grad,None,(int(index),),self.map_snapshot_id,query_scope=query_scope,reason_code="FULL_GAUSSIAN_SPHERE_QUERY_FINITE",signed_distance=signed,evaluated_gaussian_count=count)


class SourceGaussianBarrierAdapter:
    """Adapter for the existing `GSplatLoader.query_distance` API.

    The wrapped callable must return `(h, gradient, hessian, info)`.  It is never
    given a reference mesh, depth image, route label, or collision oracle.
    """

    def __init__(self, query_distance: Callable[...,Any], map_snapshot_id: str, effective_radius: float, gaussian_count: int) -> None:
        self.query_distance=query_distance; self.map_snapshot_id=map_snapshot_id
        self.effective_radius=float(effective_radius); self.gaussian_count=int(gaussian_count)

    def query(self, point: Any, expected_snapshot_id: str, query_scope: str="FULL") -> BarrierQueryResult:
        if expected_snapshot_id!=self.map_snapshot_id:
            return BarrierQueryResult(BarrierStatus.ERROR,None,None,None,(),self.map_snapshot_id,query_scope=query_scope,reason_code="MAP_SNAPSHOT_MISMATCH")
        try:
            h,gradient,hessian,_=self.query_distance(point,radius=self.effective_radius,distance_type="ball-to-ellipsoid")
            h_np=np.asarray(h.detach().cpu() if hasattr(h,"detach") else h,dtype=np.float64).reshape(-1)
            if h_np.size==0:
                return BarrierQueryResult(BarrierStatus.UNKNOWN,None,None,None,(),self.map_snapshot_id,query_scope=query_scope,reason_code="EMPTY_GAUSSIAN_QUERY",evaluated_gaussian_count=0)
            if not np.all(np.isfinite(h_np)):
                return BarrierQueryResult(BarrierStatus.NONFINITE,None,None,None,(),self.map_snapshot_id,query_scope=query_scope,reason_code="NONFINITE_GAUSSIAN_QUERY",evaluated_gaussian_count=h_np.size)
            index=int(np.argmin(h_np)); raw=float(h_np[index]+self.effective_radius**2)
            signed=float(math.copysign(math.sqrt(abs(raw)),raw))
            grad_np=np.asarray(gradient.detach().cpu() if hasattr(gradient,"detach") else gradient,dtype=np.float64).reshape(-1,3)[index]
            hess_np=np.asarray(hessian.detach().cpu() if hasattr(hessian,"detach") else hessian,dtype=np.float64).reshape(-1,3,3)[index]
            return BarrierQueryResult(BarrierStatus.FINITE,float(h_np[index]),tuple(map(float,grad_np)),tuple(tuple(map(float,row)) for row in hess_np),(index,),self.map_snapshot_id,query_scope=query_scope,reason_code="SOURCE_FULL_GAUSSIAN_QUERY_FINITE",signed_distance=signed,evaluated_gaussian_count=h_np.size)
        except Exception as exc:
            return BarrierQueryResult(BarrierStatus.ERROR,None,None,None,(),self.map_snapshot_id,query_scope=query_scope,reason_code="SOURCE_QUERY_ERROR:"+type(exc).__name__)

    def minimum_signed_distance(self, point: Any) -> tuple[str,float|None,int]:
        result=self.query(point,self.map_snapshot_id,"FULL")
        return result.status.value,result.signed_distance,result.evaluated_gaussian_count


class UnknownMapAdapter:
    def __init__(self,map_snapshot_id:str,status:BarrierStatus=BarrierStatus.UNKNOWN)->None:
        self.map_snapshot_id=map_snapshot_id; self.status=status
    def minimum_signed_distance(self,point:np.ndarray)->tuple[str,float|None,int]:
        return self.status.value,None,0
    def query(self,point:np.ndarray,expected_snapshot_id:str,query_scope:str="FULL")->BarrierQueryResult:
        return BarrierQueryResult(self.status,None,None,None,(),self.map_snapshot_id,query_scope=query_scope,reason_code="FORCED_"+self.status.value)
