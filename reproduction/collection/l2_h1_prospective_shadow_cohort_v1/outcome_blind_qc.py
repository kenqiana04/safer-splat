#!/usr/bin/env python3
"""Strict per-trial QC that never aggregates scientific L2 outcomes."""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

from collection_common import (
    CAPTURE_SEMANTIC_KEYS, DATA_ROLE, MAP_AUTHORITY_ID, RESULT_SEMANTIC_KEYS,
    atomic_write_json, iter_jsonl, load_json, semantic_sha256,
)

ERROR_FIELDS = (
    "queue_drop", "serialization_error", "worker_failure", "worker_unavailable",
    "alignment_failure", "schema_failure", "map_authority_failure", "shutdown_incomplete",
    "sequence_gap", "duplicate_payload", "duplicate_result", "orphan_result", "capture_without_result",
)
RATE_FIELDS = (
    "capture_completeness", "selected_u_completeness", "map_authority_completeness",
    "reachability_completeness", "shadow_result_completion", "join_completeness",
)


def finite_vector(value: Any, length: int) -> bool:
    return isinstance(value, list) and len(value) == length and all(
        isinstance(item, (int, float)) and not isinstance(item, bool) and math.isfinite(float(item)) for item in value
    )


def intended_steps(trace: dict[str, Any]) -> list[dict[str, Any]]:
    steps = trace.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("independent committed-control trace missing or empty")
    required = (
        "step_id", "selected_u_k", "selected_candidate_hash", "selected_candidate_identity",
        "plant_input_x", "plant_input_u", "plant_output_x_next", "map_authority_id",
    )
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or any(key not in step for key in required):
            raise ValueError(f"trace step {index} lacks required committed-control facts")
        if step["step_id"] != index:
            raise ValueError(f"trace sequence mismatch at {index}")
        if not finite_vector(step["selected_u_k"], 3) or step["selected_u_k"] != step["plant_input_u"]:
            raise ValueError(f"selected control/plant input mismatch at {index}")
        if not finite_vector(step["plant_input_x"], 6) or not finite_vector(step["plant_output_x_next"], 6):
            raise ValueError(f"invalid plant state at {index}")
    return steps


def terminal_status_typed(result: dict[str, Any]) -> bool:
    reached = result.get("l2_reached")
    status = result.get("l2_status")
    if not isinstance(reached, bool) or not isinstance(status, str):
        return False
    return status in ({"PASS", "FAIL", "UNKNOWN"} if reached else {"NOT_REACHED"})


def reachability_typed(capture: dict[str, Any], result: dict[str, Any]) -> bool:
    reach = capture.get("reachability")
    if not isinstance(reach, dict):
        return False
    capture_ok = (
        reach.get("candidate_preparation_reached") is True
        and reach.get("decision_committed") is True
        and isinstance(reach.get("l0_observation_source"), str)
        and isinstance(reach.get("l1_observation_source"), str)
        and isinstance(reach.get("l2_reached"), bool)
        and isinstance(reach.get("l2_reachability_reason"), str)
    )
    result_ok = all(
        isinstance(result.get(key), str) and bool(result.get(key))
        for key in ("l0_status", "l0_reason", "l0_observation_source", "l1_status", "l1_reason", "l1_observation_source", "l2_reason", "l2_reachability_reason")
    )
    return capture_ok and result_ok and terminal_status_typed(result)


def qc(attempt_root: Path) -> dict[str, Any]:
    identity = load_json(attempt_root / "formal_attempt_identity.json")
    process = load_json(attempt_root / "process_result.json")
    run_root = attempt_root / "run"
    run_id = identity["run_id"]
    trial_id = identity["trial_id"]
    errors = {name: 0 for name in ERROR_FIELDS}
    anomalies: list[dict[str, Any]] = []

    if identity.get("data_role") != DATA_ROLE or identity.get("eligible_for_formal_prospective_cohort") is not True:
        errors["schema_failure"] += 1
        anomalies.append({"category": "FORMAL_IDENTITY_INVALID"})
    trace = load_json(run_root / "primary_trace.json")
    try:
        steps = intended_steps(trace)
    except Exception as exc:
        steps = []
        errors["schema_failure"] += 1
        anomalies.append({"category": "DENOMINATOR_INVALID", "detail": str(exc)})
    if trace.get("trial_id") != trial_id:
        errors["alignment_failure"] += 1
        anomalies.append({"category": "OFFICIAL_TRIAL_ID_MISMATCH"})

    map_manifest = load_json(run_root / "instrumentation/map_authority_manifest.json")
    map_id = map_manifest.get("map_authority_id")
    map_valid = (
        map_id == MAP_AUTHORITY_ID
        and map_manifest.get("full_map_hash_call_count_per_run") == 1
        and map_manifest.get("per_step_full_map_hash_count") == 0
        and isinstance(map_manifest.get("artifacts"), list) and bool(map_manifest["artifacts"])
    )
    if not map_valid:
        errors["map_authority_failure"] += 1
        anomalies.append({"category": "MAP_MANIFEST_INVALID"})

    captures: dict[int, dict[str, Any]] = {}
    capture_rows = list(iter_jsonl(run_root / "instrumentation/step_capture_log.jsonl"))
    for row in capture_rows:
        sequence = row.get("payload_sequence_id")
        if not isinstance(sequence, int):
            errors["schema_failure"] += 1
            anomalies.append({"category": "CAPTURE_SEQUENCE_NOT_INTEGER"})
        elif sequence in captures:
            errors["duplicate_payload"] += 1
            anomalies.append({"category": "DUPLICATE_PAYLOAD", "sequence": sequence})
        else:
            captures[sequence] = row

    results: dict[int, dict[str, Any]] = {}
    result_rows = list(iter_jsonl(run_root / "instrumentation/shadow_certificate_result_log.jsonl"))
    for row in result_rows:
        sequence = row.get("payload_sequence_id")
        if not isinstance(sequence, int):
            errors["schema_failure"] += 1
            anomalies.append({"category": "RESULT_SEQUENCE_NOT_INTEGER"})
        elif sequence in results:
            errors["duplicate_result"] += 1
            anomalies.append({"category": "DUPLICATE_RESULT", "sequence": sequence})
        else:
            results[sequence] = row
        if not terminal_status_typed(row):
            errors["schema_failure"] += 1
            anomalies.append({"category": "L2_STATUS_FIELD_MISSING_OR_UNTYPED", "sequence": sequence})

    for health in iter_jsonl(run_root / "instrumentation/instrumentation_health_log.jsonl"):
        status = health.get("status")
        state = health.get("health")
        if status == "DROPPED_QUEUE_FULL": errors["queue_drop"] += 1
        if status == "SERIALIZATION_ERROR" or state == "SERIALIZATION_ERROR": errors["serialization_error"] += 1
        if state == "WORKER_EXCEPTION": errors["worker_failure"] += 1
        if status == "WORKER_UNAVAILABLE" or state == "WORKER_UNAVAILABLE": errors["worker_unavailable"] += 1
        if state == "PAYLOAD_ALIGNMENT_FAILURE": errors["alignment_failure"] += 1
        if state == "SCHEMA_VALIDATION_FAILURE": errors["schema_failure"] += 1
        if state == "MAP_AUTHORITY_FAILURE": errors["map_authority_failure"] += 1
        if state == "SHUTDOWN_INCOMPLETE": errors["shutdown_incomplete"] += 1
        if health.get("classified_as_l2_unknown") is True:
            errors["schema_failure"] += 1
            anomalies.append({"category": "HEALTH_MISCLASSIFIED_AS_L2_UNKNOWN"})

    activation = load_json(run_root / "arm_activation.json")
    if activation.get("shutdown_status") != "SHUTDOWN_COMPLETE" or activation.get("worker_alive_after_shutdown") is not False:
        errors["shutdown_incomplete"] += 1
    errors["worker_failure"] += int(activation.get("worker_exception_count", 0))

    expected = set(range(len(steps)))
    capture_sequences = set(captures)
    result_sequences = set(results)
    errors["sequence_gap"] += len(expected - capture_sequences)
    errors["orphan_result"] += len(result_sequences - capture_sequences)
    errors["capture_without_result"] += len(capture_sequences - result_sequences)

    valid_u = valid_map = valid_reach = terminal_results = joinable = 0
    runtime_trial_tokens = {row.get("trial_id") for row in captures.values() if isinstance(row.get("trial_id"), str)}
    for sequence, step in enumerate(steps):
        capture = captures.get(sequence)
        result = results.get(sequence)
        if capture is None:
            continue
        selected = capture.get("selected_candidate")
        selected_valid = (
            isinstance(selected, dict)
            and selected.get("candidate_role") == "SELECTED_EXECUTED_CONTROL"
            and selected.get("selected_for_execution") is True
            and selected.get("created_before_observation") is True
            and isinstance(selected.get("candidate_origin"), str) and bool(selected.get("candidate_origin"))
            and finite_vector(selected.get("u"), 3)
            and selected.get("u") == step.get("selected_u_k")
            and isinstance(step.get("selected_candidate_hash"), str) and len(step["selected_candidate_hash"]) == 64
            and isinstance(capture.get("decision_commit_id"), str)
        )
        if selected_valid: valid_u += 1
        else: anomalies.append({"category": "SELECTED_U_OR_PROVENANCE_INVALID", "sequence": sequence})
        capture_semantic = {key: capture.get(key) for key in CAPTURE_SEMANTIC_KEYS}
        expected_capture_hash = semantic_sha256(capture_semantic)
        payload_hash_valid = (
            capture.get("payload_semantic_hash") == expected_capture_hash
            and capture.get("payload_worker_receive_semantic_hash") == expected_capture_hash
        )
        if not payload_hash_valid:
            errors["alignment_failure"] += 1
            anomalies.append({"category": "PAYLOAD_HASH_FAILURE", "sequence": sequence})
        if map_valid and capture.get("map_authority_id") == map_id == step.get("map_authority_id"):
            valid_map += 1
        else:
            errors["map_authority_failure"] += 1
        if result is None:
            continue
        if reachability_typed(capture, result): valid_reach += 1
        else: anomalies.append({"category": "REACHABILITY_INCOMPLETE", "sequence": sequence})
        if terminal_status_typed(result): terminal_results += 1
        result_hash_valid = result.get("result_semantic_hash") == semantic_sha256({key: result.get(key) for key in RESULT_SEMANTIC_KEYS})
        token = capture.get("trial_id")
        token_valid = isinstance(token, str) and token.startswith("trial-") and len(runtime_trial_tokens) == 1 and result.get("trial_id") == token
        expected_decision = f"{run_id}:{token}:commit:{sequence:06d}"
        expected_state = f"{run_id}:{token}:state:{sequence:06d}"
        expected_candidate = f"{run_id}:{token}:selected:{sequence:06d}"
        joined = all((
            capture.get("run_id") == result.get("run_id") == run_id,
            token_valid,
            capture.get("step_id") == result.get("step_id") == sequence,
            capture.get("state_sequence_id") == result.get("state_sequence_id") == expected_state,
            capture.get("decision_commit_id") == result.get("decision_commit_id") == expected_decision,
            capture.get("payload_sequence_id") == result.get("payload_sequence_id") == sequence,
            isinstance(selected, dict) and selected.get("candidate_id") == result.get("selected_candidate_id") == expected_candidate,
            capture.get("map_authority_id") == result.get("map_authority_id") == map_id,
            capture.get("payload_semantic_hash") == result.get("payload_enqueue_semantic_hash"),
            capture.get("payload_worker_receive_semantic_hash") == result.get("payload_worker_receive_semantic_hash"),
            result_hash_valid,
        ))
        if joined: joinable += 1
        else: anomalies.append({"category": "JOIN_FAILURE", "sequence": sequence})

    intended_count = len(steps)
    capture_count = len(capture_rows)
    rates = {
        "capture_completeness": capture_count / intended_count if intended_count else None,
        "selected_u_completeness": valid_u / intended_count if intended_count else None,
        "map_authority_completeness": valid_map / intended_count if intended_count else None,
        "reachability_completeness": valid_reach / intended_count if intended_count else None,
        "shadow_result_completion": terminal_results / capture_count if capture_count else None,
        "join_completeness": joinable / capture_count if capture_count else None,
    }
    passed = (
        process.get("exit_code") == 0
        and process.get("intended_step_count") == intended_count
        and process.get("capture_count") == capture_count
        and process.get("result_record_count") == len(result_rows)
        and intended_count > 0
        and all(value == 1.0 for value in rates.values())
        and all(value == 0 for value in errors.values())
        and not anomalies
        and activation.get("controller_intervention_count") == 0
        and activation.get("selected_candidate_replacement_count") == 0
    )
    return {
        "schema_version": "L2_H1_FORMAL_OUTCOME_BLIND_QC_V1",
        "trial_id": trial_id, "attempt_id": identity["attempt_id"], "run_id": run_id,
        "data_role": DATA_ROLE, "outcome_blind": True, "scientific_outcome_aggregation_count": 0,
        "l2_status_field_presence_and_type_checked": True,
        "intended_step_count": intended_count, "capture_count": capture_count,
        "result_record_count": len(result_rows), "joinable_record_count": joinable,
        "map_authority_id": map_id, "rates": rates, "errors": errors,
        "anomalies": anomalies, "pass": passed,
        "validator": "PASS_FORMAL_TRIAL_OUTCOME_BLIND_QC" if passed else "FAIL_FORMAL_TRIAL_OUTCOME_BLIND_QC",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = qc(args.attempt_root.resolve(strict=True))
    atomic_write_json(args.output, result)
    print(
        f"trial={result['trial_id']:03d} pass={str(result['pass']).lower()} intended={result['intended_step_count']} "
        f"capture={result['capture_count']} result={result['result_record_count']} joinable={result['joinable_record_count']}",
        flush=True,
    )
    return 0 if result["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
