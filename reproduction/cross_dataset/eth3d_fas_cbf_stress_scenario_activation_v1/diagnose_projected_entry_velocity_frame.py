#!/usr/bin/env python3
"""Plant-free diagnostic for critical-Gaussian direction after Start-Safe projection."""
from __future__ import annotations

import json
import sys

import numpy as np

from build_shadow_stage_reachability import ShadowEvaluator, normalized
from task_config_v2 import (  # noqa: F401
    CANONICAL_ROOT,
    CONTROLLER_SNAPSHOT,
    PR80_ROOT,
    PRM_GRAPH,
    SOURCE_ROOT,
    TASK_ROOT,
    V1_REGISTRY,
    atomic_json,
)

if str(PR80_ROOT) not in sys.path:
    sys.path.insert(0, str(PR80_ROOT))
from eth3d_controller_core import LearnedEllipsoidMap  # type: ignore  # noqa: E402
from fas_cbf_modules import project_start_safe  # type: ignore  # noqa: E402


def main() -> int:
    graph = json.loads(PRM_GRAPH.read_text(encoding="utf-8"))
    diagnostics = json.loads(
        (PR80_ROOT / "scenario_generation/scenario_static_diagnostics.json").read_text(
            encoding="utf-8"
        )
    )
    v1 = json.loads(V1_REGISTRY.read_text(encoding="utf-8"))
    v1_nodes = {int(row["source_node_id"]) for row in v1["scenarios"]}
    node_rows = {int(row["id"]): row for row in graph["nodes"]}
    learned = LearnedEllipsoidMap(CANONICAL_ROOT, SOURCE_ROOT, CONTROLLER_SNAPSHOT)
    evaluator = ShadowEvaluator(learned)
    ordered = sorted(
        diagnostics,
        key=lambda row: (
            abs(float(row["min_map_h"])),
            -int(row["near_active_count"]),
            int(row["node_id"]),
        ),
    )
    records: list[dict] = []
    endpoint_unsafe: list[dict] = []
    tuple_count = 0
    for diagnostic in ordered[:24]:
        node_id = int(diagnostic["node_id"])
        base = np.asarray(diagnostic["point_m"], dtype=np.float64)
        graph_row = node_rows[node_id]
        reference_clearance = float(graph_row.get("reference_clearance_m", diagnostic["reference_clearance_m"]))
        toward = normalized(
            np.asarray(diagnostic["nearest_obstacle_direction"], dtype=np.float64)
        )
        h0 = float(diagnostic["min_map_h"])
        for target in (-0.005, -0.001, 0.0001, 0.0002, 0.0005, 0.0008):
            delta = h0 - target
            if abs(delta) > min(0.20, reference_clearance - 0.25):
                continue
            position = base + delta * toward
            projected = project_start_safe(position, learned.query)
            if not projected["accepted"]:
                continue
            entry = np.asarray(projected["position"], dtype=np.float64)
            query = learned.query(entry)
            critical = int(np.argmin(query["h"]))
            post_direction = normalized(-np.asarray(query["grad"][critical], dtype=np.float64))
            for magnitude in (0.02, 0.04, 0.06, 0.08, 0.10):
                velocity = magnitude * post_direction
                goal = position + 0.12 * post_direction
                tuple_count += 1
                record = evaluator.evaluate(
                    f"PROJECTED_ENTRY_FRAME_{tuple_count:05d}",
                    position,
                    velocity,
                    goal,
                    reference_clearance - abs(delta) - 0.12,
                    "C_CRITICAL_GAUSSIAN_OFFSET_POST_PROJECTION_FRAME_DIAGNOSTIC",
                    [
                        "A_PR80_OR_PR79" if node_id in v1_nodes else "A_PR79_512_NODES",
                        "C_CRITICAL_GAUSSIAN_OFFSET",
                        "POST_PROJECTION_CRITICAL_FRAME_DIAGNOSTIC",
                    ],
                    node_id,
                    stop_after_s3=True,
                )
                compact = {
                    "candidate_id": record["candidate_id"],
                    "node_id": node_id,
                    "target_h": target,
                    "magnitude": magnitude,
                    "projection_classification": record.get("S1", {}).get("classification"),
                    "projection_success": record.get("S1", {}).get("projection_success"),
                    "m2_qp_feasible": record.get("S2", {}).get("m2_qp_feasible"),
                    "current_h": record.get("S3", {}).get("current_h"),
                    "endpoint_h": record.get("S3", {}).get("endpoint_h"),
                    "segment_h": record.get("S3", {}).get("segment_h"),
                    "trigger_type": record.get("S3", {}).get("trigger_type"),
                }
                records.append(compact)
                if (
                    compact["m2_qp_feasible"]
                    and compact["current_h"] is not None
                    and compact["current_h"] >= 0.0005
                    and compact["trigger_type"] == "ENDPOINT_UNSAFE"
                ):
                    endpoint_unsafe.append(compact)
                    if len(endpoint_unsafe) >= 4:
                        break
            if len(endpoint_unsafe) >= 4:
                break
        if len(endpoint_unsafe) >= 4:
            break
    output = {
        "status": "POST_PROJECTION_FRAME_FINDS_ENDPOINT_UNSAFE"
        if len(endpoint_unsafe) >= 4
        else "POST_PROJECTION_FRAME_DOES_NOT_FIND_ENDPOINT_UNSAFE",
        "plant_execution_count": 0,
        "formal_rollout_result_read_count": 0,
        "controller_parameter_change_count": 0,
        "tuple_count": tuple_count,
        "endpoint_unsafe_count": len(endpoint_unsafe),
        "endpoint_unsafe": endpoint_unsafe,
        "diagnostic_records": records,
    }
    atomic_json(TASK_ROOT / "shadow_predicates/projected_entry_frame_diagnostic.json", output)
    print(json.dumps({key: output[key] for key in ("status", "tuple_count", "endpoint_unsafe_count")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
