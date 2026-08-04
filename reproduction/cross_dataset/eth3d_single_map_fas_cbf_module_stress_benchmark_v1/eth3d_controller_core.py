#!/usr/bin/env python3
"""Frozen learned-map primitives for the ETH3D module stress benchmark."""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
from scipy.spatial import cKDTree

from fas_cbf_modules import DT, UMAX, VMAX


ROBOT_RADIUS = 0.10
EPSILON = 0.01
ALPHA = 5.0
BETA = 1.0
CANDIDATE_BUDGET = 2000
MAX_STEPS = 200
GOAL_TOLERANCE_M = 0.03
METHODS = (
    "M0_SAFER_BASELINE",
    "M1_FAS_START_SAFE_ONLY",
    "M2_FAS_START_SAFE_PLUS_FEASIBILITY_AWARE",
    "M3_FAS_PLUS_DISCRETE_TIME_VERIFICATION",
    "M4_FULL_FAS_CBF",
)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, ensure_ascii=True)
            stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def nominal_control(position: np.ndarray, velocity: np.ndarray,
                    goal: np.ndarray) -> np.ndarray:
    desired_velocity = np.clip(5.0 * (np.asarray(goal) - np.asarray(position)),
                               -VMAX, VMAX)
    return np.clip(desired_velocity - np.asarray(velocity), -UMAX, UMAX)


class LearnedEllipsoidMap:
    """Read-only adapter over canonical arrays and the unmodified SAFER query."""

    def __init__(self, canonical_root: Path, source_root: Path,
                 controller_snapshot: Path, device: str = "cuda:0") -> None:
        self.root = Path(canonical_root)
        self.means = np.load(self.root / "means_world_m.npy", mmap_mode="r")
        self.scales = np.load(self.root / "scales_linear_m.npy", mmap_mode="r")
        self.rotations = np.load(self.root / "rotations_unit_wxyz.npy", mmap_mode="r")
        self.opacity = np.load(self.root / "opacity.npy", mmap_mode="r")
        self.tree = cKDTree(self.means)
        sys.path[:0] = [str(Path(controller_snapshot)), str(Path(source_root))]
        import torch  # pylint: disable=import-outside-toplevel
        from splat.gsplat_utils import DummyGSplatLoader  # pylint: disable=import-outside-toplevel
        torch.set_default_dtype(torch.float64)
        self.torch = torch
        self.device = device
        self.loader = DummyGSplatLoader(device)
        self.query_count = 0

    def candidate_ids(self, position: np.ndarray,
                      budget: int = CANDIDATE_BUDGET) -> np.ndarray:
        count = min(int(budget), int(self.means.shape[0]))
        _, ids = self.tree.query(np.asarray(position, dtype=np.float64),
                                 k=count, workers=1)
        return np.atleast_1d(ids).astype(np.int64)

    def query(self, position: np.ndarray, budget: int = CANDIDATE_BUDGET) -> dict:
        ids = self.candidate_ids(position, budget)
        torch = self.torch
        self.loader.means = torch.as_tensor(np.asarray(self.means[ids]),
                                            dtype=torch.float64, device=self.device)
        self.loader.rots = torch.as_tensor(np.asarray(self.rotations[ids]),
                                           dtype=torch.float64, device=self.device)
        self.loader.scales = torch.as_tensor(np.asarray(self.scales[ids]),
                                             dtype=torch.float64, device=self.device)
        started = time.perf_counter()
        h, gradient, hessian, _ = self.loader.query_distance(
            torch.as_tensor(position, dtype=torch.float64, device=self.device),
            distance_type="ball-to-ellipsoid", radius=ROBOT_RADIUS, epsilon=EPSILON,
        )
        elapsed = time.perf_counter() - started
        h_np = h.detach().cpu().numpy().reshape(-1)
        grad_np = gradient.detach().cpu().numpy().reshape((-1, 3))
        hessian_np = hessian.detach().cpu().numpy().reshape((-1, 3, 3))
        finite = (np.isfinite(h_np) & np.isfinite(grad_np).all(axis=1)
                  & np.isfinite(hessian_np).all(axis=(1, 2)))
        self.query_count += 1
        return {"candidate_ids": ids, "h": h_np, "grad": grad_np,
                "hessian": hessian_np, "finite": finite,
                "runtime_seconds": elapsed}

    def min_h(self, position: np.ndarray, budget: int = CANDIDATE_BUDGET) -> float:
        result = self.query(position, budget)
        if not bool(np.all(result["finite"])):
            return float("nan")
        return float(np.min(result["h"]))

    @staticmethod
    def cbf_rows(result: dict, velocity: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        h = np.asarray(result["h"], dtype=np.float64)
        gradient = np.asarray(result["grad"], dtype=np.float64)
        hessian = np.asarray(result["hessian"], dtype=np.float64)
        velocity = np.asarray(velocity, dtype=np.float64).reshape(3)
        lfh = gradient @ velocity
        lflfh = np.einsum("i,nij,j->n", velocity, hessian, velocity)
        lower = -lflfh - ALPHA * lfh - BETA * (lfh + ALPHA * h)
        norms = np.linalg.norm(gradient, axis=1)
        valid = np.isfinite(lower) & np.isfinite(norms) & (norms > 1e-12)
        if not bool(np.all(valid)):
            raise FloatingPointError("NONFINITE_OR_ZERO_CBF_ROW")
        return -gradient / norms[:, None], -lower / norms


class ReferenceMeshOracle:
    """Independent evaluation-only mesh oracle; never passed to controllers."""

    def __init__(self, mesh_path: Path) -> None:
        import trimesh  # pylint: disable=import-outside-toplevel
        self.trimesh = trimesh
        mesh = trimesh.load(str(mesh_path), process=False, force="mesh")
        if isinstance(mesh, trimesh.Scene):
            mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
        self.mesh = mesh

    def evaluate(self, points: list[np.ndarray]) -> dict:
        if not points:
            return {"reference_collision": False, "collision_count": 0,
                    "first_collision_step": None, "min_reference_clearance": None,
                    "min_segment_clearance": None}
        array = np.asarray(points, dtype=np.float64)
        _, distance, _ = self.trimesh.proximity.closest_point(self.mesh, array)
        if not np.isfinite(distance).all():
            raise FloatingPointError("NONFINITE_REFERENCE_ORACLE")
        center_clearance = distance - ROBOT_RADIUS
        segment_lower = []
        for index in range(len(array) - 1):
            length = float(np.linalg.norm(array[index + 1] - array[index]))
            segment_lower.append(float(max(distance[index], distance[index + 1]) - length - ROBOT_RADIUS))
        if not segment_lower:
            segment_lower = [float(center_clearance[0])]
        collisions = np.flatnonzero(center_clearance <= 0.0)
        return {
            "reference_collision": bool(collisions.size),
            "collision_count": int(collisions.size),
            "first_collision_step": int(collisions[0]) if collisions.size else None,
            "min_reference_clearance": float(np.min(center_clearance)),
            "min_segment_clearance": float(np.min(segment_lower)),
            "segment_clearance_contract": "CERTIFIED_ENDPOINT_LIPSCHITZ_LOWER_BOUND",
        }
