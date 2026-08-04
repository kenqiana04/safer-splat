#!/usr/bin/env python3
"""Exact segment/triangle helpers for the reference-only sphere oracle."""

from __future__ import annotations

import math

import numpy as np
import trimesh


def point_triangle_distance(point, triangle) -> float:
    """Exact float64 point-to-triangle distance (Ericson region tests)."""
    point = np.asarray(point, dtype=np.float64)
    triangle = np.asarray(triangle, dtype=np.float64)
    a, b, c = triangle
    ab, ac, ap = b - a, c - a, point - a
    d1, d2 = float(np.dot(ab, ap)), float(np.dot(ac, ap))
    if d1 <= 0.0 and d2 <= 0.0:
        return float(np.linalg.norm(ap))
    bp = point - b
    d3, d4 = float(np.dot(ab, bp)), float(np.dot(ac, bp))
    if d3 >= 0.0 and d4 <= d3:
        return float(np.linalg.norm(bp))
    vc = d1 * d4 - d3 * d2
    if vc <= 0.0 and d1 >= 0.0 and d3 <= 0.0:
        v = d1 / (d1 - d3)
        return float(np.linalg.norm(point - (a + v * ab)))
    cp = point - c
    d5, d6 = float(np.dot(ab, cp)), float(np.dot(ac, cp))
    if d6 >= 0.0 and d5 <= d6:
        return float(np.linalg.norm(cp))
    vb = d5 * d2 - d1 * d6
    if vb <= 0.0 and d2 >= 0.0 and d6 <= 0.0:
        w = d2 / (d2 - d6)
        return float(np.linalg.norm(point - (a + w * ac)))
    va = d3 * d6 - d5 * d4
    if va <= 0.0 and (d4 - d3) >= 0.0 and (d5 - d6) >= 0.0:
        denominator = (d4 - d3) + (d5 - d6)
        w = (d4 - d3) / denominator
        return float(np.linalg.norm(point - (b + w * (c - b))))
    denominator = va + vb + vc
    if denominator == 0.0:
        return min(point_segment_distance(point, a, b),
                   point_segment_distance(point, b, c),
                   point_segment_distance(point, c, a))
    v, w = vb / denominator, vc / denominator
    return float(np.linalg.norm(point - (a + ab * v + ac * w)))


def point_segment_distance(point, a, b) -> float:
    direction = b - a
    denominator = float(np.dot(direction, direction))
    if denominator == 0:
        return float(np.linalg.norm(point - a))
    t = max(0.0, min(1.0, float(np.dot(point - a, direction) / denominator)))
    return float(np.linalg.norm(point - (a + t * direction)))


def segment_segment_distance(p1, q1, p2, q2) -> float:
    # Ericson, Real-Time Collision Detection, closest points of two segments.
    d1, d2, r = q1 - p1, q2 - p2, p1 - p2
    a, e, eps = float(np.dot(d1, d1)), float(np.dot(d2, d2)), 1e-15
    f = float(np.dot(d2, r))
    if a <= eps and e <= eps:
        return float(np.linalg.norm(p1 - p2))
    if a <= eps:
        s, t = 0.0, max(0.0, min(1.0, f / e))
    else:
        c = float(np.dot(d1, r))
        if e <= eps:
            t, s = 0.0, max(0.0, min(1.0, -c / a))
        else:
            b = float(np.dot(d1, d2))
            denominator = a * e - b * b
            s = max(0.0, min(1.0, (b * f - c * e) / denominator)) if denominator != 0 else 0.0
            t = (b * s + f) / e
            if t < 0.0:
                t, s = 0.0, max(0.0, min(1.0, -c / a))
            elif t > 1.0:
                t, s = 1.0, max(0.0, min(1.0, (b - c) / a))
    return float(np.linalg.norm((p1 + d1 * s) - (p2 + d2 * t)))


def segment_intersects_triangle(a, b, triangle) -> bool:
    direction = b - a
    edge1, edge2 = triangle[1] - triangle[0], triangle[2] - triangle[0]
    h = np.cross(direction, edge2)
    det = float(np.dot(edge1, h))
    if abs(det) < 1e-15:
        return False
    inv = 1.0 / det
    s = a - triangle[0]
    u = inv * float(np.dot(s, h))
    if u < 0.0 or u > 1.0:
        return False
    q = np.cross(s, edge1)
    v = inv * float(np.dot(direction, q))
    if v < 0.0 or u + v > 1.0:
        return False
    t = inv * float(np.dot(edge2, q))
    return 0.0 <= t <= 1.0


def segment_triangle_distance(a, b, triangle) -> float:
    if segment_intersects_triangle(a, b, triangle):
        return 0.0
    best = min(point_triangle_distance(a, triangle), point_triangle_distance(b, triangle))
    for vertex in triangle:
        best = min(best, point_segment_distance(vertex, a, b))
    for index in range(3):
        best = min(best, segment_segment_distance(a, b, triangle[index], triangle[(index + 1) % 3]))
    return best


def exact_segment_mesh_clearance(mesh, a, b) -> float:
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    sample = np.vstack([a, (a + b) / 2.0, b])
    _, sample_distance, _ = trimesh.proximity.closest_point(mesh, sample)
    upper = float(np.min(sample_distance))
    if not math.isfinite(upper):
        raise RuntimeError("NONFINITE_REFERENCE_DISTANCE")
    lower_bound, upper_bound = np.minimum(a, b) - upper - 1e-12, np.maximum(a, b) + upper + 1e-12
    candidates = list(mesh.triangles_tree.intersection(np.r_[lower_bound, upper_bound]))
    if not candidates:
        return upper
    triangles = np.asarray(mesh.triangles)[candidates]
    return min(segment_triangle_distance(a, b, triangle) for triangle in triangles)


def certified_segment_mesh_clearance(mesh, a, b, certification_cap: float):
    """Return an exact-within-cap clearance or a conservative certified bound.

    Every triangle whose Euclidean distance to the segment is at most the cap
    must intersect the segment AABB expanded by that cap.  Exhaustively testing
    those triangles therefore either returns the exact mesh distance when it is
    within the decision-relevant interval, or certifies that the true distance
    is greater than the returned cap.  The latter is deliberately represented
    as a lower bound rather than as a fabricated uncapped minimum.
    """
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    cap = float(certification_cap)
    if not math.isfinite(cap) or cap <= 0.0:
        raise ValueError("INVALID_SEGMENT_CLEARANCE_CERTIFICATION_CAP")
    lower_bound = np.minimum(a, b) - cap - 1e-12
    upper_bound = np.maximum(a, b) + cap + 1e-12
    candidates = list(mesh.triangles_tree.intersection(np.r_[lower_bound, upper_bound]))
    if not candidates:
        return cap, True
    triangles = np.asarray(mesh.triangles)[candidates]
    best = min(segment_triangle_distance(a, b, triangle) for triangle in triangles)
    if best <= cap:
        return float(best), False
    return cap, True
