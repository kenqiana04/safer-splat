#!/usr/bin/env python3
"""Synthetic exactness checks for the segment/triangle clearance kernel."""

import numpy as np
import trimesh

from reference_route_geometry import exact_segment_mesh_clearance, segment_triangle_distance


def main() -> None:
    triangle = np.asarray([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
    cases = [
        ([-0.2, -0.2, 1.0], [-0.2, -0.2, 2.0], np.sqrt(0.08 + 1.0)),
        ([0.25, 0.25, -1.0], [0.25, 0.25, 1.0], 0.0),
        ([0.25, 0.25, 1.0], [0.75, 0.25, 1.0], 1.0),
    ]
    errors = []
    for start, end, expected in cases:
        observed = segment_triangle_distance(np.asarray(start), np.asarray(end), triangle)
        errors.append(abs(observed - expected))
    mesh = trimesh.Trimesh(vertices=triangle, faces=[[0, 1, 2]], process=False)
    mesh_value = exact_segment_mesh_clearance(mesh, np.asarray([0.25, 0.25, 1.0]), np.asarray([0.75, 0.25, 1.0]))
    errors.append(abs(mesh_value - 1.0))
    if max(errors) > 1e-12:
        raise RuntimeError(f"GEOMETRY_KERNEL_FAILURE {errors}")
    print("PASS_EXACT_GEOMETRY_KERNEL", max(errors))


if __name__ == "__main__":
    main()
