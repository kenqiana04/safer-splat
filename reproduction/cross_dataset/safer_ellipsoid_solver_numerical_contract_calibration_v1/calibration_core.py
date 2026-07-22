"""Independent numerical references for signed squared ellipsoid distance.

This module deliberately does not import the frozen production solver.  It
solves the KKT scalar equation in float64 for a fixed ellipsoid and query.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
import numpy as np


@dataclass
class Projection:
    y: np.ndarray
    h: float
    phi: float
    lam: float
    root_residual: float
    surface_residual: float
    kkt_normalized_residual: float


def _f(a: np.ndarray, x: np.ndarray, lam: float) -> float:
    aa = a * a
    return float(np.sum(aa * x * x / (lam + aa) ** 2) - 1.0)


def _df(a: np.ndarray, x: np.ndarray, lam: float) -> float:
    aa = a * a
    return float(-2.0 * np.sum(aa * x * x / (lam + aa) ** 3))


def _bracket(a: np.ndarray, x: np.ndarray) -> tuple[float, float, float]:
    q = float(np.sum((x / a) ** 2) - 1.0)
    if q >= 0.0:
        lo, hi = 0.0, max(float(np.linalg.norm(a * x / (a.min() ** 2))), 1.0)
        while _f(a, x, hi) > 0.0:
            hi *= 2.0
    else:
        # Regular input registry excludes zero minimum-axis coordinates, which
        # are the familiar medial-axis/non-unique-projection degeneracy.
        lo = -(float(a.min()) ** 2) * (1.0 - 1e-15)
        hi = 0.0
        if _f(a, x, lo) <= 0.0:
            raise ValueError("projection is non-unique or too close to a medial axis")
    return lo, hi, 1.0 if q >= 0.0 else -1.0


def _pack(a: np.ndarray, x: np.ndarray, lam: float, phi: float) -> Projection:
    aa = a * a
    y = aa * x / (lam + aa)
    h = float(phi * np.sum((x - y) ** 2))
    root = abs(_f(a, x, lam))
    surface = abs(float(np.sum((y / a) ** 2) - 1.0))
    stationarity = y - x + lam * y / aa
    denom = max(1.0, float(np.linalg.norm(x)), float(np.linalg.norm(y)), abs(lam))
    return Projection(y=y, h=h, phi=phi, lam=lam, root_residual=root,
                      surface_residual=surface,
                      kkt_normalized_residual=float(np.linalg.norm(stationarity) / denom))


def bisection_projection(a: np.ndarray, x: np.ndarray, iterations: int = 240) -> Projection:
    a = np.asarray(a, dtype=np.float64); x = np.asarray(x, dtype=np.float64)
    lo, hi, phi = _bracket(a, x)
    for _ in range(iterations):
        mid = (lo + hi) * 0.5
        if _f(a, x, mid) >= 0.0:
            lo = mid
        else:
            hi = mid
        if hi - lo <= 1e-14:
            break
    return _pack(a, x, (lo + hi) * 0.5, phi)


def safeguarded_newton_projection(a: np.ndarray, x: np.ndarray, max_iterations: int = 100) -> Projection:
    a = np.asarray(a, dtype=np.float64); x = np.asarray(x, dtype=np.float64)
    lo, hi, phi = _bracket(a, x)
    lam = (lo + hi) * 0.5
    for _ in range(max_iterations):
        value = _f(a, x, lam)
        if abs(value) <= 1e-13:
            break
        deriv = _df(a, x, lam)
        candidate = lam - value / deriv if deriv != 0.0 else math.nan
        if not (lo < candidate < hi) or not math.isfinite(candidate):
            candidate = (lo + hi) * 0.5
        if value >= 0.0:
            lo = lam
        else:
            hi = lam
        lam = candidate
    # A final bracket midpoint guarantees a valid KKT root even when a Newton
    # candidate did not happen to hit the residual tolerance exactly.
    for _ in range(80):
        mid = (lo + hi) * 0.5
        if _f(a, x, mid) >= 0.0:
            lo = mid
        else:
            hi = mid
    return _pack(a, x, (lo + hi) * 0.5, phi)


def envelope_gradient(projection: Projection, x: np.ndarray) -> np.ndarray:
    return 2.0 * projection.phi * (np.asarray(x, dtype=np.float64) - projection.y)


def five_point_gradient(a: np.ndarray, x: np.ndarray) -> tuple[np.ndarray, bool]:
    x = np.asarray(x, dtype=np.float64)
    outputs = []
    stable = True
    for factor in (1.0, 0.5, 2.0):
        g = np.empty(3, dtype=np.float64)
        for j in range(3):
            step = max(1e-6, 1e-5 * (1.0 + abs(float(x[j])))) * factor
            offsets = []
            for sign in (2.0, 1.0, -1.0, -2.0):
                z = x.copy(); z[j] += sign * step
                offsets.append(bisection_projection(a, z).h)
            g[j] = (-offsets[0] + 8.0 * offsets[1] - 8.0 * offsets[2] + offsets[3]) / (12.0 * step)
        outputs.append(g)
    for g in outputs[1:]:
        if np.linalg.norm(g - outputs[0]) / (1.0 + np.linalg.norm(outputs[0])) > 1e-4:
            stable = False
    return outputs[0], stable


def norm_error(candidate: np.ndarray, reference: np.ndarray) -> float:
    return float(np.linalg.norm(candidate - reference) / (1.0 + np.linalg.norm(reference)))


def cosine(candidate: np.ndarray, reference: np.ndarray) -> float | None:
    nc, nr = float(np.linalg.norm(candidate)), float(np.linalg.norm(reference))
    if nc < 1e-7 or nr < 1e-7:
        return None
    return float(np.dot(candidate, reference) / (nc * nr))
