"""Frozen primitives for the Replica bounded direct-goal benchmark.

The map is read-only.  The mesh oracle is evaluation-only and is never passed
to the controller, Start-Safe projection, verifier, or recovery planner.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

import clarabel
import numpy as np
from scipy import sparse
from scipy.spatial import cKDTree

from frozen_bounded_qp_adapter import BoundedCBFQPAdapter

DT = 0.05
VMAX = 0.10
UMAX = 0.10
ROBOT_RADIUS = 0.10
EPSILON_BASE = 0.01
SPHERE_TARGET_CLEARANCE = 0.005
ALPHA = 5.0
BETA = 1.0
MAX_STEPS = 500
METHODS = (
    "M0_BOUNDED_SAFER",
    "M1_BOUNDED_RISK_AWARE_V1",
    "M2_FAS_START_SAFE",
    "M3_FAS_START_SAFE_DISCRETE",
    "M4_FAS_START_SAFE_DISCRETE_RECOVERY",
)
TERMINAL_STATUSES = (
    "MAP_GEOMETRY_BLOCKED", "START_STATE_REJECTED", "QP_INFEASIBLE",
    "DISCRETE_VERIFICATION_FAILED", "RECOVERY_FAILED", "COLLISION",
    "SUCCESS", "TIMEOUT", "NUMERICAL_FAILURE",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def finite_vector(value: np.ndarray, size: int) -> bool:
    return bool(np.asarray(value).shape == (size,) and np.all(np.isfinite(value)))


def nominal_control(position: np.ndarray, velocity: np.ndarray, goal: np.ndarray) -> np.ndarray:
    vel_des = np.clip(5.0 * (np.asarray(goal) - np.asarray(position)), -VMAX, VMAX)
    return np.clip(vel_des - np.asarray(velocity), -UMAX, UMAX)


class FineSphereMap:
    """Read-only FINE sphere-union geometry with exact KD-tree branch-and-bound."""

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.means = np.load(self.root / "means_world_m.npy", mmap_mode="r")
        self.scales = np.load(self.root / "scales_linear_m.npy", mmap_mode="r")
        if self.means.ndim != 2 or self.means.shape[1] != 3:
            raise ValueError("invalid FINE means geometry")
        if not np.allclose(self.scales[:, 0], self.scales[:, 1]) or not np.allclose(self.scales[:, 0], self.scales[:, 2]):
            raise ValueError("FINE map is not an isotropic sphere union")
        self.sphere_radius = float(self.scales[0, 0])
        self.tree = cKDTree(self.means)
        self.bound_min = np.min(self.means, axis=0).astype(np.float64)
        self.bound_max = np.max(self.means, axis=0).astype(np.float64)

    @property
    def effective_radius(self) -> float:
        return self.sphere_radius + ROBOT_RADIUS + EPSILON_BASE

    def point_center_distance(self, point: np.ndarray) -> tuple[float, int]:
        distance, active = self.tree.query(np.asarray(point, dtype=np.float64), workers=1)
        return float(distance), int(active)

    def point_cg(self, point: np.ndarray) -> tuple[float, int]:
        distance, active = self.point_center_distance(point)
        return distance - self.effective_radius, active

    def exact_segment_center_distance(self, start: np.ndarray, end: np.ndarray) -> tuple[float, int, int]:
        """Exact segment-to-center minimum with a sound midpoint KD-tree bound.

        If a center improves the initial endpoint/midpoint upper bound U, it
        lies within U + half_segment_length of the midpoint.  Querying that
        ball therefore excludes no possible minimizer.
        """
        start = np.asarray(start, dtype=np.float64).reshape(3)
        end = np.asarray(end, dtype=np.float64).reshape(3)
        direction = end - start
        length = float(np.linalg.norm(direction))
        if length <= 0.0:
            # A forward-Euler step from rest is a degenerate segment.  Its
            # exact union distance is the ordinary nearest-center query;
            # querying a ball whose radius equals the nearest distance can be
            # numerically open at the KD-tree boundary.
            distance, active = self.tree.query(start, workers=1)
            return float(distance), int(active), 1
        midpoint = 0.5 * (start + end)
        samples = np.stack((start, midpoint, end))
        sample_distance, sample_index = self.tree.query(samples, workers=1)
        upper = float(np.min(sample_distance))
        candidates = np.asarray(self.tree.query_ball_point(midpoint, np.nextafter(upper + 0.5 * length, math.inf)), dtype=np.int64)
        if candidates.size == 0:
            raise RuntimeError("exact segment candidate set unexpectedly empty")
        centers = np.asarray(self.means[candidates], dtype=np.float64)
        denom = float(np.dot(direction, direction))
        if denom <= 0.0:
            delta = centers - start
        else:
            t = np.clip(((centers - start) @ direction) / denom, 0.0, 1.0)
            delta = centers - (start + t[:, None] * direction)
        distance2 = np.einsum("ij,ij->i", delta, delta)
        local = int(np.argmin(distance2))
        return float(math.sqrt(float(distance2[local]))), int(candidates[local]), int(candidates.size)

    def exact_segment_cg(self, start: np.ndarray, end: np.ndarray) -> tuple[float, int, int]:
        distance, active, candidates = self.exact_segment_center_distance(start, end)
        return distance - self.effective_radius, active, candidates

    def brute_segment_cg(self, start: np.ndarray, end: np.ndarray, chunk: int = 200_000) -> float:
        start = np.asarray(start, dtype=np.float64).reshape(3)
        end = np.asarray(end, dtype=np.float64).reshape(3)
        direction = end - start
        denom = float(np.dot(direction, direction))
        best2 = math.inf
        for offset in range(0, self.means.shape[0], chunk):
            centers = np.asarray(self.means[offset:offset + chunk], dtype=np.float64)
            if denom <= 0.0:
                delta = centers - start
            else:
                t = np.clip(((centers - start) @ direction) / denom, 0.0, 1.0)
                delta = centers - (start + t[:, None] * direction)
            best2 = min(best2, float(np.min(np.einsum("ij,ij->i", delta, delta))))
        return math.sqrt(best2) - self.effective_radius

    def potentially_active_ids(self, position: np.ndarray, velocity: np.ndarray) -> np.ndarray:
        """Return every CBF row that cannot be proved slack under frozen boxes.

        For legacy alpha=5 and beta=1 rows, b is at least
        ``5*h - 6*sqrt(3)*vmax``.  A row is redundant for all frozen box
        controls once b >= sqrt(3)*umax.  This is an exact dominance removal,
        not a top-k truncation or a tunable controller parameter.
        """
        del velocity
        h_limit = (math.sqrt(3.0) * UMAX + 6.0 * math.sqrt(3.0) * VMAX) / (ALPHA * BETA)
        radius = self.effective_radius + h_limit + 1e-12
        return np.asarray(self.tree.query_ball_point(np.asarray(position, dtype=np.float64), radius), dtype=np.int64)

    def map_applicable(self, start: np.ndarray, goal: np.ndarray) -> tuple[bool, float]:
        clearance, _, _ = self.exact_segment_cg(start, goal)
        return clearance > 0.0, clearance


def legacy_second_order_cbf_rows(map_geometry: FineSphereMap, position: np.ndarray,
                                 velocity: np.ndarray, ids: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Historical SAFER alpha=5, beta=1 rows with its frozen sign convention."""
    ids = np.asarray(ids, dtype=np.int64)
    if ids.size == 0:
        return np.empty((0, 3)), np.empty((0,)), ids
    centers = np.asarray(map_geometry.means[ids], dtype=np.float64)
    delta = np.asarray(position, dtype=np.float64)[None, :] - centers
    distance = np.linalg.norm(delta, axis=1)
    safe_distance = np.maximum(distance, 1e-12)
    normal = delta / safe_distance[:, None]
    h = distance - map_geometry.effective_radius
    projection = normal @ np.asarray(velocity, dtype=np.float64)
    hessian_v = (np.asarray(velocity, dtype=np.float64)[None, :] - normal * projection[:, None]) / safe_distance[:, None]
    v_h_v = np.einsum("ij,j->i", hessian_v, np.asarray(velocity, dtype=np.float64))
    legacy_l = -v_h_v - ALPHA * projection - BETA * (projection + ALPHA * h)
    # CBF.get_QP_matrices normalizes and negates both sides.  Norm(normal)=1.
    return -normal, -legacy_l, ids


class FrozenRiskAwareV1:
    """Historical bestD pre-CBF candidate budget with map-constant attributes.

    FINE spheres have equal opacity, scale, anisotropy, and volume features.
    The historical risk_v2_hybrid's dynamic inverse-distance and heading terms
    remain; ties are deterministically resolved by descending global ID, as
    NumPy's historical ``argsort(scores)[::-1]`` did for equal scores.
    """

    candidate_budget = 2000
    near_distance_threshold = 0.05
    heading_distance_threshold = 0.25
    heading_cos_threshold = 0.5
    min_candidate_budget = 200
    high_active_count = 500

    def __init__(self, map_geometry: FineSphereMap) -> None:
        self.map = map_geometry
        self.high_active_ids = np.arange(map_geometry.means.shape[0] - 1,
                                         max(-1, map_geometry.means.shape[0] - 1 - self.high_active_count),
                                         -1, dtype=np.int64)

    def select(self, position: np.ndarray, u_des: np.ndarray) -> tuple[np.ndarray | None, dict[str, Any]]:
        position = np.asarray(position, dtype=np.float64)
        u_des = np.asarray(u_des, dtype=np.float64)
        forced_near = np.asarray(self.map.tree.query_ball_point(position, self.near_distance_threshold), dtype=np.int64)
        local_heading = np.asarray(self.map.tree.query_ball_point(position, self.heading_distance_threshold), dtype=np.int64)
        if local_heading.size:
            vec = np.asarray(self.map.means[local_heading], dtype=np.float64) - position
            norms = np.linalg.norm(vec, axis=1)
            unorm = float(np.linalg.norm(u_des))
            cosine = (vec @ u_des) / np.maximum(norms * unorm, 1e-12) if unorm > 1e-12 else np.zeros_like(norms)
            forced_heading = local_heading[cosine >= self.heading_cos_threshold]
        else:
            forced_heading = np.empty((0,), dtype=np.int64)
        history_distance = max(self.heading_distance_threshold, 2.0 * self.near_distance_threshold)
        history_points = np.asarray(self.map.means[self.high_active_ids], dtype=np.float64)
        forced_history = self.high_active_ids[np.linalg.norm(history_points - position, axis=1) <= history_distance]
        forced = np.unique(np.concatenate((forced_near, forced_heading, forced_history))).astype(np.int64)
        # The score is 0.10 normalized inverse distance + 0.05 heading, because
        # all learned-attribute feature columns are constant on this map.
        k = min(self.map.means.shape[0], max(self.candidate_budget * 4, self.candidate_budget + forced.size))
        distances, nearest = self.map.tree.query(position, k=k, workers=1)
        nearest = np.atleast_1d(nearest).astype(np.int64)
        distances = np.atleast_1d(distances).astype(np.float64)
        points = np.asarray(self.map.means[nearest], dtype=np.float64)
        vectors = points - position
        norms = np.maximum(np.linalg.norm(vectors, axis=1), 1e-12)
        unorm = float(np.linalg.norm(u_des))
        heading = (vectors @ u_des) / (norms * unorm) if unorm > 1e-12 else np.zeros_like(norms)
        inverse = 1.0 / norms
        inverse_norm = (inverse - inverse.min()) / max(float(inverse.max() - inverse.min()), 1e-12)
        score = 0.10 * inverse_norm + 0.05 * np.clip(heading, 0.0, 1.0)
        order = np.lexsort((-nearest, -score))
        remaining = nearest[order]
        forced_set = set(int(i) for i in forced)
        selected: list[int] = [int(i) for i in forced]
        for candidate in remaining:
            if int(candidate) not in forced_set and len(selected) < self.candidate_budget:
                selected.append(int(candidate))
        selected_ids = np.asarray(sorted(set(selected)), dtype=np.int64)
        debug = {
            "candidate_budget": self.candidate_budget,
            "candidate_count_total": int(self.map.means.shape[0]),
            "candidate_count_forced_near": int(forced_near.size),
            "candidate_count_forced_heading": int(forced_heading.size),
            "candidate_count_forced_history": int(forced_history.size),
            "candidate_count_risk_ranked": int(max(0, selected_ids.size - forced.size)),
            "candidate_count_final": int(selected_ids.size),
            "fallback_used": False,
            "fallback_reason": "",
            "feature_mode": "constant_map_attributes_dynamic_distance_heading",
            "constant_feature_fraction": 1.0,
            "equal_static_score_fraction": 1.0,
        }
        if selected_ids.size < min(self.min_candidate_budget, self.map.means.shape[0]):
            debug.update({"fallback_used": True, "fallback_reason": "below_min_candidate_budget"})
            return None, debug
        return selected_ids, debug


def project_start_safe(map_geometry: FineSphereMap, position: np.ndarray) -> dict[str, Any]:
    """Frozen active-set outward-halfspace Start-Safe projection."""
    original = np.asarray(position, dtype=np.float64).reshape(3)
    current = original.copy()
    initial_cg, _ = map_geometry.point_cg(current)
    if initial_cg >= SPHERE_TARGET_CLEARANCE:
        return {"accepted": True, "classification": "SAFE", "position": current, "displacement": 0.0,
                "iterations": 0, "initial_cg": initial_cg, "final_cg": initial_cg}
    if initial_cg < -1e-6:
        classification = "UNSAFE"
    elif abs(initial_cg) <= 1e-6:
        classification = "CONTACT"
    else:
        classification = "NEAR_SAFE"
    target = map_geometry.effective_radius + SPHERE_TARGET_CLEARANCE
    for iteration in range(1, 21):
        ids = np.asarray(map_geometry.tree.query_ball_point(current, target + 0.05), dtype=np.int64)
        if ids.size == 0:
            break
        centers = np.asarray(map_geometry.means[ids], dtype=np.float64)
        delta = current[None, :] - centers
        distances = np.linalg.norm(delta, axis=1)
        relevant = distances < target
        if not np.any(relevant):
            final_cg, _ = map_geometry.point_cg(current)
            if final_cg >= SPHERE_TARGET_CLEARANCE:
                return {"accepted": True, "classification": classification, "position": current,
                        "displacement": float(np.linalg.norm(current-original)), "iterations": iteration - 1,
                        "initial_cg": initial_cg, "final_cg": final_cg}
            continue
        centers = centers[relevant]
        delta = current[None, :] - centers
        distances = np.linalg.norm(delta, axis=1)
        normals = np.empty_like(delta)
        normals[distances > 1e-12] = delta[distances > 1e-12] / distances[distances > 1e-12, None]
        normals[distances <= 1e-12] = np.array([1.0, 0.0, 0.0])
        # n dot (current + d - center) >= target -> -n dot d <= n dot(current-center)-target.
        rows = -normals
        rhs = np.einsum("ij,ij->i", normals, delta) - target
        settings = clarabel.DefaultSettings(); settings.verbose = False
        solver = clarabel.DefaultSolver(
            sparse.csc_matrix(np.eye(3)), np.zeros(3), sparse.csc_matrix(rows), rhs,
            [clarabel.NonnegativeConeT(rows.shape[0])], settings,
        )
        solution = solver.solve()
        if str(solution.status) != "Solved":
            break
        step = np.asarray(solution.x, dtype=np.float64)
        candidate = current + step
        if np.linalg.norm(candidate - original) > 0.05 + 1e-12:
            break
        current = candidate
        final_cg, _ = map_geometry.point_cg(current)
        if final_cg >= SPHERE_TARGET_CLEARANCE:
            return {"accepted": True, "classification": classification, "position": current,
                    "displacement": float(np.linalg.norm(current-original)), "iterations": iteration,
                    "initial_cg": initial_cg, "final_cg": final_cg}
    final_cg, _ = map_geometry.point_cg(current)
    return {"accepted": False, "classification": classification, "position": current,
            "displacement": float(np.linalg.norm(current-original)), "iterations": 20,
            "initial_cg": initial_cg, "final_cg": final_cg}


class ReplicaMeshOracle:
    """Batch client for the prevalidated float64 official-mesh oracle binary."""

    def __init__(self, backend: Path, mesh: Path, work_dir: Path) -> None:
        self.backend, self.mesh, self.work_dir = Path(backend), Path(mesh), Path(work_dir)

    @staticmethod
    def _segment_query(start: np.ndarray, end: np.ndarray) -> str:
        return "S " + " ".join(f"{float(v):.17g}" for v in np.concatenate((start, end)))

    @staticmethod
    def _point_query(point: np.ndarray) -> str:
        return "P " + " ".join(f"{float(v):.17g}" for v in point)

    def query_segments(self, segments: Iterable[tuple[np.ndarray, np.ndarray]], name: str) -> list[list[str]]:
        entries = [self._segment_query(a, b) for a, b in segments]
        return self._run(entries, name)

    def query_points(self, points: Iterable[np.ndarray], name: str) -> list[list[str]]:
        entries = [self._point_query(point) for point in points]
        return self._run(entries, name)

    def _run(self, queries: list[str], name: str) -> list[list[str]]:
        if not queries:
            return []
        self.work_dir.mkdir(parents=True, exist_ok=True)
        query_path = self.work_dir / f"{name}.queries.txt"
        output_path = self.work_dir / f"{name}.oracle.txt"
        atomic_text(query_path, "\n".join(queries) + "\n")
        subprocess.run([str(self.backend), str(self.mesh), str(query_path), str(output_path)], check=True)
        return [line.split() for line in output_path.read_text(encoding="utf-8").splitlines() if line]


def parse_oracle_distance(tokens: list[str]) -> float:
    if not tokens:
        raise ValueError("empty oracle row")
    # The validated C++ backend emits ``P|S min_distance ...``; its trailing
    # fields are closest-point/triangle diagnostics, not input coordinates.
    if tokens[0] not in {"P", "S"} or len(tokens) <= 1:
        raise ValueError(f"cannot parse oracle distance: {tokens}")
    value = float(tokens[1])
    if not math.isfinite(value):
        raise ValueError(f"non-finite oracle distance: {tokens}")
    return value


def environment_identity() -> dict[str, str]:
    import platform
    import scipy
    import numpy
    return {"python": platform.python_version(), "numpy": numpy.__version__, "scipy": scipy.__version__,
            "clarabel": getattr(clarabel, "__version__", "unknown")}
