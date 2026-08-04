#!/usr/bin/env python3
"""Read-only diagnosis of the frozen blocked-straight-line route gate."""

import json

import numpy as np

from task_config import TASK_ROOT


def summary(values):
    values = np.asarray(list(values), dtype=np.float64)
    return {
        "minimum": float(values.min()),
        "median": float(np.median(values)),
        "maximum": float(values.max()),
    }


def main() -> None:
    candidates = json.loads(
        (TASK_ROOT / "routes/reference_route_candidates_full.json").read_text(encoding="utf-8"))
    split = json.loads((TASK_ROOT / "split/pose_block_split_v1.json").read_text(encoding="utf-8"))
    node_gate = json.loads((TASK_ROOT / "routes/reference_prm_node_gate_diagnostic.json").read_text(encoding="utf-8"))
    centers = np.asarray(list(split["capture_centers_m"].values()), dtype=np.float64)
    rows = candidates["candidates"]
    payload = {
        "status": "DIAGNOSIS_ONLY",
        "candidate_count": len(rows),
        "blocked_candidate_count": sum(row["blocked_straight_line"] for row in rows),
        "direct_clearance_m": summary(row["direct_segment_clearance_m"] for row in rows),
        "direct_clearance_capped_count": sum(
            row["direct_segment_clearance_is_conservative_lower_bound"] for row in rows),
        "path_node_count": summary(row["path_node_count"] for row in rows),
        "turning_segment_count": summary(row["turning_segment_count"] for row in rows),
        "path_length_m": summary(row["path_length_m"] for row in rows),
        "capture_center_bounds_m": [centers.min(axis=0).tolist(), centers.max(axis=0).tolist()],
        "capture_center_axis_extent_m": (centers.max(axis=0) - centers.min(axis=0)).tolist(),
        "current_candidate_generator_dimensionality": node_gate["candidate_voxel_dimensionality"],
        "frozen_robot_state_dimensionality": "6D_FREE_3D_DOUBLE_INTEGRATOR",
        "implementation_gap": None,
        "frozen_blocked_straight_line_ratio_minimum": 0.5,
        "scientific_contract_result": "FAIL_BLOCKED_STRAIGHT_LINE_QUOTA",
    }
    (TASK_ROOT / "routes/blocked_straight_line_gate_diagnostic.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
