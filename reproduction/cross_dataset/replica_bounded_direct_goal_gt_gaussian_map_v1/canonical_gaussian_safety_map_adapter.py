"""Read-only adapter for linear-scale/probability-opacity canonical map arrays."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree


class CanonicalGaussianSafetyMapAdapter:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.means = np.load(root / "means_world_m.npy", mmap_mode="r")
        self.scales = np.load(root / "scales_linear_m.npy", mmap_mode="r")
        self.opacity_probability = np.load(root / "opacities_probability.npy", mmap_mode="r")
        if not np.allclose(self.scales[:, 0], self.scales[:, 1]) or not np.allclose(self.scales[:, 0], self.scales[:, 2]):
            raise ValueError("surface-voxel map requires isotropic Gaussian spheres")
        self.sphere_radius_m = float(self.scales[0, 0])
        self.tree = cKDTree(self.means)

    def point_clearance(self, points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        distance, active = self.tree.query(np.asarray(points, dtype=np.float64), workers=4)
        return distance - self.sphere_radius_m, np.asarray(active, dtype=np.int64)

    def segment_clearance(self, start: np.ndarray, goal: np.ndarray) -> float:
        start = np.asarray(start, dtype=np.float64); goal = np.asarray(goal, dtype=np.float64)
        direction = goal - start; denom = float(np.dot(direction, direction)); best = np.inf
        for offset in range(0, len(self.means), 200_000):
            centers = np.asarray(self.means[offset:offset + 200_000], dtype=np.float64)
            if denom == 0:
                dist2 = np.sum((centers - start) ** 2, axis=1)
            else:
                t = np.clip(((centers - start) @ direction) / denom, 0.0, 1.0)
                delta = centers - (start + t[:, None] * direction)
                dist2 = np.einsum("ij,ij->i", delta, delta)
            best = min(best, float(dist2.min()))
        return float(np.sqrt(best) - self.sphere_radius_m)
