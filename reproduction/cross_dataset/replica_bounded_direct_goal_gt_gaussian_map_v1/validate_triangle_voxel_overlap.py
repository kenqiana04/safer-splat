#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def overlap(triangle: np.ndarray, center: np.ndarray, half: float, dtype: np.dtype) -> bool:
    scalar = np.dtype(dtype).type
    p = np.asarray(triangle - center, dtype=scalar)
    h = np.asarray([half, half, half], dtype=scalar)
    tol = scalar(1e-9)
    if np.any(p.max(axis=0) < -h - tol) or np.any(p.min(axis=0) > h + tol):
        return False
    edges = np.stack((p[1] - p[0], p[2] - p[1], p[0] - p[2]))
    normal = np.cross(edges[0], edges[1])
    if np.dot(normal, normal) > scalar(1e-30):
        if abs(np.dot(normal, p[0])) > np.dot(np.abs(normal), h) + tol:
            return False
    basis = np.eye(3, dtype=scalar)
    for edge in edges:
        for axis in basis:
            sep = np.cross(edge, axis)
            if np.dot(sep, sep) <= scalar(1e-30):
                continue
            values = p @ sep
            radius = np.dot(np.abs(sep), h)
            if values.max() < -radius - tol or values.min() > radius + tol:
                return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rng = np.random.default_rng(20260729)
    cases = [
        np.array([[-.5,0,0],[.5,0,0],[0,.5,0.]]), np.array([[.5,-.5,0],[.5,.5,0],[.5,0,.5]]),
        np.array([[.5,.5,.5],[.7,.5,.5],[.5,.7,.5]]), np.array([[-2,0,0],[-1,0,0],[0,0,0]]),
        np.array([[1e6,1e6,1e6],[1e6+.5,1e6,1e6],[1e6,1e6+.5,1e6]]) - 1e6,
    ]
    cases.extend(rng.uniform(-2, 2, size=(10_000, 3, 3)))
    disagreements = 0
    false_negative = 0
    for triangle in cases:
        fast = overlap(triangle, np.zeros(3), .5, np.float64)
        reference = overlap(triangle, np.zeros(3), .5, np.longdouble)
        disagreements += int(fast != reference)
        false_negative += int(reference and not fast)
    result = {"status": "PASS" if false_negative == 0 else "FAIL", "fixture_count": len(cases), "reference_precision": "longdouble", "false_negative_count": false_negative, "disagreement_count": disagreements, "categories": ["axis_aligned", "boundary_touch", "edge_touch", "vertex_touch", "degenerate_segment", "near_coplanar", "large_coordinate", "random"]}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["status"])
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
