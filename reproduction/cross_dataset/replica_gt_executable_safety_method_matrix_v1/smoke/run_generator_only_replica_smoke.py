"""Run only PR #84 full represented-map queries plus six-slot generation on frozen smoke states."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

TASK_ROOT = Path(__file__).resolve().parents[1]
PAYLOAD_ROOT = TASK_ROOT / "smoke/pr84_frozen_payload"
if str(TASK_ROOT) not in sys.path:
    sys.path.insert(0, str(TASK_ROOT))
if str(PAYLOAD_ROOT) not in sys.path:
    sys.path.insert(0, str(PAYLOAD_ROOT))

from adapters.gaussian_barrier_adapter import AnalyticSphereGaussianMapAdapter
from alternative_library.canonical_serialization import canonical_sha256
from alternative_library.directional_library import build_directional_library
from task_config import MAP_SNAPSHOT_ID, ROBOT_RADIUS, MARGIN, ROUTE_SHA256, SLOT_IDS, START_SHA256, SMOKE_STATE_COUNT


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def identity_record(record, generated):
    slots = [{"candidate_id": slot.candidate_id, "availability": slot.availability.value, "acceleration": slot.acceleration, "duplicate_of": slot.duplicate_of} for slot in generated.slots]
    payload = {
        "state": record["state"], "goal": generated.goal_position, "map_snapshot": MAP_SNAPSHOT_ID,
        "active_primitive_id": generated.active_primitive_id, "represented_normal": generated.represented_normal,
        "goal_tangent": generated.goal_tangent, "auxiliary_tangent": generated.auxiliary_tangent,
        "braking_control": generated.braking_control, "slots": slots,
    }
    return {**payload, "ordered_tuple_sha256": canonical_sha256(slots), "state_candidate_set_sha256": canonical_sha256(payload)}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--map-root", type=Path, required=True); parser.add_argument("--route-registry", type=Path, required=True); parser.add_argument("--start-registry", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if sha256_file(args.route_registry) != ROUTE_SHA256 or sha256_file(args.start_registry) != START_SHA256:
        raise SystemExit("FROZEN_SMOKE_REGISTRY_IDENTITY_MISMATCH")
    smoke = json.loads((PAYLOAD_ROOT / "map_smoke/replica_smoke_records.json").read_text(encoding="utf-8"))
    records = smoke["records"]
    if len(records) != SMOKE_STATE_COUNT:
        raise SystemExit("FROZEN_SMOKE_STATE_COUNT_MISMATCH")
    routes = {item["route_id"]: item for item in json.loads(args.route_registry.read_text(encoding="utf-8"))["routes"]}
    adapter = AnalyticSphereGaussianMapAdapter.from_canonical_arrays(args.map_root, MAP_SNAPSHOT_ID, ROBOT_RADIUS + MARGIN)
    outputs, availability = [], {"AVAILABLE": 0, "DUPLICATE": 0, "DEGENERATE": 0, "MAP_UNAVAILABLE": 0, "GOAL_UNAVAILABLE": 0}
    started = time.perf_counter(); map_query_count = 0
    for source in records:
        route_id = source.get("extra", {}).get("route_id")
        if route_id is None or route_id not in routes:
            outputs.append({"label": source["label"], "state": source["state"], "status": "FROZEN_SMOKE_GOAL_UNAVAILABLE", "reference_query_count": 0, "formal_method_run_count": 0, "slots": [{"candidate_id": identifier, "availability": "DIRECTION_ZERO"} for identifier in SLOT_IDS]})
            availability["GOAL_UNAVAILABLE"] += 6
            continue
        state, route = source["state"], routes[route_id]
        query = adapter.query(np.asarray(state["position"], dtype=np.float64), MAP_SNAPSHOT_ID, "FULL")
        map_query_count += 1
        generated = build_directional_library(state["position"], state["velocity"], route["goal_m"], query.status.value, query.active_gaussian_ids, adapter.centers)
        slots = [{"candidate_id": slot.candidate_id, "availability": slot.availability.value, "acceleration": slot.acceleration, "duplicate_of": slot.duplicate_of} for slot in generated.slots]
        for slot in generated.slots:
            if slot.available: availability["AVAILABLE"] += 1
            elif slot.availability.value == "DUPLICATE_OF_EARLIER_SLOT": availability["DUPLICATE"] += 1
            elif slot.availability.value == "MAP_QUERY_UNAVAILABLE": availability["MAP_UNAVAILABLE"] += 1
            else: availability["DEGENERATE"] += 1
        outputs.append({"label": source["label"], "route_id": route_id, "state": state, "map_query": {"status": query.status.value, "active_gaussian_ids": list(query.active_gaussian_ids), "scope": query.query_scope, "reason": query.reason_code}, "candidate_identity": identity_record(source, generated), "slots": slots, "reference_query_count": 0, "formal_method_run_count": 0, "benchmark_registry_count": 0, "logical_rollout_count": 0})
    identity_rows = [{"label": item["label"], "status": item.get("status", "GENERATED"), "candidate_identity": item.get("candidate_identity"), "slots": item["slots"]} for item in outputs]
    output = {"status": "GENERATOR_ONLY_REPLICA_SMOKE_PASS", "input": "PR84_25_PLANT_FREE_SMOKE_STATES", "state_count": len(outputs), "map_query_count": map_query_count, "reference_query_count": 0, "formal_method_run_count": 0, "benchmark_candidate_search_count": 0, "benchmark_registry_count": 0, "logical_rollout_count": 0, "availability_counts": availability, "state_candidate_identity_aggregate_sha256": canonical_sha256(identity_rows), "runtime_seconds_engineering_only": time.perf_counter() - started, "records": outputs}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(output["status"], output["state_count"], "REFERENCE_QUERY_COUNT=0", "FORMAL_METHOD_RUN_COUNT=0")


if __name__ == "__main__":
    main()
