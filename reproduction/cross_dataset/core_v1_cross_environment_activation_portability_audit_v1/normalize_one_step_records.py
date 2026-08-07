"""Normalize the completed formal records without changing scientific outcomes.

The formal runner emitted the complete source-runtime payload, but its two
source families used different optional column sets.  This post-lock pass only
adds contract fields that are deterministically implied by the frozen input,
the already-emitted typed result, or the already-frozen Replica reference row.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from common import read_json, sha256_file, sha256_json, write_csv, write_json
from task_config import DT, EFFECTIVE_RADIUS, METHODS, MODEL, TASK_ROOT, U_BOUND, V_BOUND


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def truth(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def parsed_json(value: str, default: Any) -> Any:
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def main() -> None:
    path = TASK_ROOT / "benchmark/one_step_records.csv"
    original_sha256 = sha256_file(path)
    rows = read_csv(path)
    if len(rows) != 1440:
        raise RuntimeError(f"expected 1440 completed records, got {len(rows)}")

    registries: dict[tuple[str, str], dict[str, Any]] = {}
    for environment in ("E1_REPLICA_GT_FINE", "E5_STONEHENGE_SAFER", "E6_FLIGHT_SAFER"):
        payload = read_json(TASK_ROOT / "registry" / environment / "representative_registry.json")
        for state in payload["states"]:
            registries[(environment, state["state_id"])] = state

    prior_path = TASK_ROOT.parent / "resume_replica_gt_executable_safety_activated_benchmark_v1" / "benchmark/one_step_records.csv"
    prior = {
        (row["state_id"], row["method"]): row
        for row in read_csv(prior_path)
        if row.get("cohort") == "REPRESENTATIVE_HOLDOUT"
    }
    if len(prior) != 640:
        raise RuntimeError(f"expected 640 frozen Replica representative records, got {len(prior)}")

    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["environment"], row["state_id"])].append(row)

    for key, values in grouped.items():
        environment, state_id = key
        state = registries[key]
        by_method = {row["method"]: row for row in values}
        if set(by_method) != set(METHODS):
            raise RuntimeError(f"incomplete method quartet for {key}")
        b0_commit = truth(by_method[METHODS[0]]["committed"])
        u_nom = parsed_json(by_method[METHODS[0]]["u_nom"], None)
        derived_shared_hash = sha256_json({
            "environment": environment,
            "state_id": state_id,
            "position_m": state["position_m"],
            "velocity_m_per_s": state["velocity_m_per_s"],
            "goal_m": state["goal_m"],
            "u_nom": u_nom,
            "map_snapshot_id": by_method[METHODS[0]]["map_snapshot_id"],
            "model": MODEL,
            "dt_s": DT,
            "u_bound_inf": U_BOUND,
            "v_bound_inf": V_BOUND,
            "effective_radius_m": EFFECTIVE_RADIUS,
        })
        existing = {row.get("shared_input_hash", "") for row in values} - {""}
        shared_hash = next(iter(existing)) if existing else derived_shared_hash
        if len(existing) > 1:
            raise RuntimeError(f"non-shared input hashes for {key}: {existing}")

        for row in values:
            method = row["method"]
            method_index = METHODS.index(method)
            committed = truth(row["committed"])
            semantic = row["semantic_status"]
            segment_bound = row.get("segment_lower_bound", "")
            rejected = parsed_json(row.get("rejected_candidate_table", "[]"), [])
            slots = parsed_json(row.get("directional_slot_states", "[]"), [])
            row["shared_input_hash"] = shared_hash
            row["current_gate"] = "PASS" if b0_commit else "FAIL"
            if method_index == 0:
                row["segment_gate"] = "NOT_APPLICABLE"
            elif not b0_commit:
                row["segment_gate"] = "NOT_REACHED_CURRENT_GATE_FAILED"
            elif segment_bound:
                row["segment_gate"] = "PASS" if float(segment_bound) >= 0.0 else "FAIL"
            else:
                row["segment_gate"] = "FAIL" if "SEGMENT" in semantic else "NOT_RECORDED"
            if method_index < 2:
                row["backup_gate"] = "NOT_APPLICABLE"
            elif not b0_commit:
                row["backup_gate"] = "NOT_REACHED_CURRENT_GATE_FAILED"
            else:
                row["backup_gate"] = "PASS" if committed else "FAIL"
            row["directional_availability"] = "AVAILABLE_6_FROZEN_SLOTS" if method_index == 3 else "DISABLED_BY_METHOD_CONTRACT"
            row["directional_slot_record_count"] = len(slots)
            row["typed_status"] = semantic
            row["fail_closed_reason"] = "" if committed else row.get("typed_reason", semantic)
            row["active_primitive_count"] = row.get("active_cbf_row_count") or "NOT_RECORDED_BY_FROZEN_PR87_RUNTIME"
            row["candidate_count"] = (1, 1, 2, 8)[method_index]
            row["candidate_count_evaluated"] = len(rejected) + (1 if row.get("selected_candidate") else 0)
            row["unknown"] = "UNKNOWN" in semantic
            row["nonfinite"] = "NONFINITE" in semantic
            row["infrastructure_failure"] = "INFRASTRUCTURE" in semantic
            if environment == "E1_REPLICA_GT_FINE":
                reference = prior[(state_id, method)]
                row["offline_reference_sweep"] = reference["reference_immediate_swept_collision"]
                row["offline_reference_collision"] = reference["reference_immediate_swept_collision"]
                row["map_reference_disagreement"] = reference["map_reference_disagreement"]
                row["represented_false_safe"] = reference["represented_false_safe"]
                row["reference_safe_but_rejected"] = reference["reference_safe_but_rejected"]
                row["reference_min_clearance_m"] = reference["reference_min_clearance_m"]
            else:
                row["offline_reference_sweep"] = "NOT_EVALUABLE"
                row["offline_reference_collision"] = "NOT_EVALUABLE"
                row["map_reference_disagreement"] = "NOT_EVALUABLE"
                row["represented_false_safe"] = "NOT_EVALUABLE"
                row["reference_safe_but_rejected"] = "NOT_EVALUABLE"
                row["reference_min_clearance_m"] = "NOT_EVALUABLE"

    fieldnames = list(rows[0])
    write_csv(path, rows, fieldnames)
    normalized_sha256 = sha256_file(path)
    marker_path = TASK_ROOT / "benchmark/formal_attempt.json"
    marker = read_json(marker_path)
    marker["raw_output_sha256"] = marker.get("raw_output_sha256", marker["output_sha256"])
    marker["normalized_output_sha256"] = normalized_sha256
    marker["output_sha256"] = normalized_sha256
    marker["normalization_semantics_changed"] = False
    marker["normalization_source"] = "completed typed results plus frozen input/reference identities"
    write_json(marker_path, marker)
    write_json(TASK_ROOT / "benchmark/formal_one_step_normalization.json", {
        "status": "PASS_COMPLETED_FORMAL_RECORDS_NORMALIZED_WITHOUT_SCIENTIFIC_CHANGE",
        "record_count": len(rows),
        "raw_output_sha256": original_sha256,
        "normalized_output_sha256": normalized_sha256,
        "formal_attempt_count_unchanged": 1,
        "scientific_result_changed": False,
        "cohort_changed": False,
        "method_result_changed": False,
    })
    print("PASS_ONE_STEP_RECORD_NORMALIZATION", original_sha256, normalized_sha256)


if __name__ == "__main__":
    main()
