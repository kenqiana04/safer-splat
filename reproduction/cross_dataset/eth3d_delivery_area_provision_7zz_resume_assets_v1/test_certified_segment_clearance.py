#!/usr/bin/env python3
"""Synthetic parity check for capped conservative segment-mesh clearance."""

import numpy as np
import trimesh

from reference_route_geometry import (
    certified_segment_mesh_clearance,
    exact_segment_mesh_clearance,
)


def main() -> None:
    mesh = trimesh.creation.box(extents=(2.0, 2.0, 2.0))
    cases = [
        ([-2, 0, 0], [2, 0, 0], 0.6352627944162882),
        ([-0.5, -0.5, 1.2], [0.5, 0.5, 1.2], 0.6352627944162882),
        ([-0.5, -0.5, 3.0], [0.5, 0.5, 3.0], 0.6352627944162882),
        ([1.1, -0.5, 0], [1.1, 0.5, 0], 0.1),
        ([4, 4, 4], [5, 5, 5], 0.1),
    ]
    records = []
    for index, (a, b, cap) in enumerate(cases):
        a = np.asarray(a, dtype=np.float64)
        b = np.asarray(b, dtype=np.float64)
        exact = exact_segment_mesh_clearance(mesh, a, b)
        value, capped = certified_segment_mesh_clearance(mesh, a, b, cap)
        if capped:
            assert exact > cap - 1e-12, (index, exact, value, capped)
            assert value == cap
        else:
            assert abs(exact - value) <= 1e-12, (index, exact, value, capped)
        records.append((index, exact, value, capped))
    print("PASS_CERTIFIED_SEGMENT_CLEARANCE_SYNTHETIC", records)


if __name__ == "__main__":
    main()
