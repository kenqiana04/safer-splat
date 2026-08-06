"""Exact analytic line-segment minima for supported primitive maps."""
from __future__ import annotations

import math
import numpy as np

from certifier.result_types import SegmentCertificate, SegmentStatus
from .base import barrier_from_signed_distance


def _closest_parameters_to_centers(start: np.ndarray, end: np.ndarray, centers: np.ndarray) -> np.ndarray:
    direction = end - start
    denom = float(direction @ direction)
    if denom == 0.0:
        return np.zeros(len(centers), dtype=np.float64)
    return np.clip(((centers - start) @ direction) / denom, 0.0, 1.0)


class ExactSphereSegmentBackend:
    method = "EXACT_ANALYTIC_SPHERE_SEGMENT_MINIMUM"

    def __init__(self, centers: np.ndarray, radii: np.ndarray | float, map_snapshot_id: str) -> None:
        self.centers = np.asarray(centers, dtype=np.float64)
        if self.centers.ndim != 2 or self.centers.shape[1] != 3:
            raise ValueError("SPHERE_CENTERS_SHAPE")
        self.radii = np.broadcast_to(np.asarray(radii, dtype=np.float64), (len(self.centers),)).copy()
        if not np.all(np.isfinite(self.centers)) or not np.all(np.isfinite(self.radii)) or np.any(self.radii < 0):
            raise ValueError("SPHERE_PRIMITIVE_NONFINITE")
        self.map_snapshot_id = map_snapshot_id
        self._tree = None
        if len(self.centers) >= 100_000:
            try:
                from scipy.spatial import cKDTree
                self._tree = cKDTree(self.centers)
            except ImportError:
                self._tree = None

    def certify(self, start: np.ndarray, end: np.ndarray, map_snapshot_id: str, expected_snapshot_id: str, effective_radius: float, rho_seg: float = 0.0) -> SegmentCertificate:
        start = np.asarray(start, dtype=np.float64); end = np.asarray(end, dtype=np.float64)
        if map_snapshot_id != expected_snapshot_id or self.map_snapshot_id != expected_snapshot_id:
            return SegmentCertificate(SegmentStatus.MAP_SNAPSHOT_MISMATCH, False, None, None, self.method, "EXACT_ANALYTIC", map_snapshot_id, 0, "MAP_SNAPSHOT_MISMATCH")
        if start.shape != (3,) or end.shape != (3,) or not np.all(np.isfinite(start)) or not np.all(np.isfinite(end)):
            return SegmentCertificate(SegmentStatus.MAP_QUERY_NONFINITE, False, None, None, self.method, "EXACT_ANALYTIC", map_snapshot_id, 0, "NONFINITE_SEGMENT")
        if len(self.centers) == 0:
            return SegmentCertificate(SegmentStatus.MAP_QUERY_UNKNOWN, False, None, None, self.method, "EXACT_ANALYTIC", map_snapshot_id, 0, "EMPTY_PRIMITIVE_MAP")
        centers = self.centers
        radii = self.radii
        original_indices = np.arange(len(centers), dtype=np.int64)
        if self._tree is not None:
            midpoint = 0.5 * (start + end)
            nearest_distance, nearest_index = self._tree.query(midpoint, k=1)
            half_length = 0.5 * float(np.linalg.norm(end - start))
            search_radius = float(nearest_distance) + half_length + float(np.max(self.radii))
            original_indices = np.asarray(self._tree.query_ball_point(midpoint, search_radius), dtype=np.int64)
            if len(original_indices) == 0:
                original_indices = np.asarray([int(nearest_index)], dtype=np.int64)
            centers = self.centers[original_indices]
            radii = self.radii[original_indices]
        t = _closest_parameters_to_centers(start, end, centers)
        closest = start[None, :] + t[:, None] * (end - start)[None, :]
        signed = np.linalg.norm(closest - centers, axis=1) - radii
        idx = int(np.argmin(signed))
        lower = barrier_from_signed_distance(float(signed[idx]), effective_radius) - rho_seg
        status = SegmentStatus.CERTIFIED_SAFE if lower >= 0.0 else SegmentStatus.CERTIFIED_UNSAFE
        return SegmentCertificate(status, lower >= 0.0, float(lower), float(t[idx]), self.method, "EXACT_ANALYTIC", map_snapshot_id, len(self.centers), "SEGMENT_EXACT_SAFE" if lower >= 0.0 else "SEGMENT_EXACT_UNSAFE", 1)


class ExactQuadraticEllipsoidSegmentBackend:
    """Synthetic exact backend for q(p)=(p-c)^T Q(p-c)-1-margin."""
    method = "EXACT_ANALYTIC_QUADRATIC_ELLIPSOID"

    def __init__(self, centers: np.ndarray, precision: np.ndarray, map_snapshot_id: str) -> None:
        self.centers = np.asarray(centers, dtype=np.float64)
        self.precision = np.asarray(precision, dtype=np.float64)
        self.map_snapshot_id = map_snapshot_id
        if self.centers.ndim != 2 or self.centers.shape[1] != 3 or self.precision.shape != (len(self.centers), 3, 3):
            raise ValueError("ELLIPSOID_PRIMITIVE_SHAPE")

    def certify(self, start: np.ndarray, end: np.ndarray, map_snapshot_id: str, expected_snapshot_id: str, effective_radius: float = 0.0, rho_seg: float = 0.0) -> SegmentCertificate:
        if map_snapshot_id != expected_snapshot_id or self.map_snapshot_id != expected_snapshot_id:
            return SegmentCertificate(SegmentStatus.MAP_SNAPSHOT_MISMATCH, False, None, None, self.method, "EXACT_ANALYTIC", map_snapshot_id, 0, "MAP_SNAPSHOT_MISMATCH")
        start=np.asarray(start,dtype=np.float64); end=np.asarray(end,dtype=np.float64); d=end-start
        best=math.inf; best_t=0.0
        for c,q in zip(self.centers,self.precision):
            y=start-c; a=float(d@q@d); b=float(2.0*y@q@d)
            t=0.0 if a <= 0.0 else float(np.clip(-b/(2.0*a),0.0,1.0))
            val=float((y+t*d)@q@(y+t*d)-1.0-rho_seg)
            if val < best: best,best_t=val,t
        status=SegmentStatus.CERTIFIED_SAFE if best>=0.0 else SegmentStatus.CERTIFIED_UNSAFE
        return SegmentCertificate(status,best>=0.0,best,best_t,self.method,"EXACT_ANALYTIC",map_snapshot_id,len(self.centers),"SEGMENT_EXACT_SAFE" if best>=0.0 else "SEGMENT_EXACT_UNSAFE",1)
