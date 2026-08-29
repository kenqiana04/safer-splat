#!/usr/bin/env python3
"""Single-pass compact aggregator for five server-retained pilot runs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterator


CAPTURE_SEMANTIC_KEYS = (
    "schema_version", "run_id", "trial_id", "step_id", "state_sequence_id",
    "decision_commit_id", "x_k", "p_k", "v_k", "dt", "selected_candidate",
    "native_sibling_candidates", "candidate_group_id", "native_candidate_group_size",
    "reachability", "map_authority_id", "controller_authority", "execution_authority",
    "candidate_selection_authority", "intervention", "shadow_only",
)
RESULT_SEMANTIC_KEYS = (
    "l0_status", "l0_reason", "l0_observation_source", "l1_status", "l1_reason",
    "l1_observation_source", "l2_reached", "l2_reachability_reason", "l2_status",
    "l2_reason", "backend_identity",
)
ERROR_KEYS = (
    "N_queue_drop", "N_serialization_error", "N_worker_exception",
    "N_worker_unavailable", "N_alignment_failure", "N_schema_failure",
    "N_map_authority_failure", "N_shutdown_incomplete", "N_sequence_gap",
    "N_duplicate_payload", "N_duplicate_result",
)
METRIC_KEYS = (
    "N_intended_steps", "N_captured_payloads", "N_unique_payloads",
    "N_valid_selected_u", "N_valid_payload_hash", "N_map_authority_resolved",
    "N_reachability_complete", "N_terminal_shadow_records", "N_joinable_records",
    *ERROR_KEYS, "N_orphan_result", "N_capture_without_result", "N_result_late",
    "L2_UNKNOWN_count",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def semantic_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def iter_jsonl(path: Path, anomalies: list[dict[str, Any]], run_id: str, trial_id: int) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise TypeError("JSONL row is not an object")
                yield value
            except Exception as exc:
                anomalies.append({
                    "run_id": run_id, "trial_id": trial_id, "category": "SCHEMA_FAILURE",
                    "payload_sequence_id": "", "detail": f"{path.name}:{line_number}:{exc}",
                })


def finite_vector(value: Any, length: int) -> bool:
    return (
        isinstance(value, list) and len(value) == length
        and all(isinstance(item, (int, float)) and not isinstance(item, bool) and math.isfinite(float(item)) for item in value)
    )


def terminal_l2(result: dict[str, Any]) -> bool:
    reached = result.get("l2_reached")
    status = result.get("l2_status")
    reason = result.get("l2_reason")
    reach_reason = result.get("l2_reachability_reason")
    if not isinstance(reached, bool) or not isinstance(reason, str) or not reason or not isinstance(reach_reason, str) or not reach_reason:
        return False
    if reached:
        return status in {"PASS", "FAIL", "UNKNOWN"}
    return status == "NOT_REACHED"


def reachability_complete(capture: dict[str, Any], result: dict[str, Any]) -> bool:
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
        for key in ("l0_status", "l0_reason", "l0_observation_source", "l1_status", "l1_reason", "l1_observation_source")
    ) and terminal_l2(result)
    return capture_ok and result_ok


def intended_trace_steps(trace: dict[str, Any]) -> tuple[list[dict[str, Any]], bool, str]:
    steps = trace.get("steps")
    if not isinstance(steps, list) or not steps:
        return [], False, "primary committed-control trace missing or empty"
    required = (
        "step_id", "selected_u_k", "selected_candidate_hash", "selected_candidate_identity",
        "plant_input_x", "plant_input_u", "plant_output_x_next", "map_authority_id",
    )
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or any(key not in step for key in required):
            return [], False, f"trace step {index} lacks committed-control/plant facts"
        if step.get("step_id") != index:
            return [], False, f"trace step sequence mismatch at {index}"
        if not finite_vector(step.get("selected_u_k"), 3) or step.get("selected_u_k") != step.get("plant_input_u"):
            return [], False, f"selected control is not aligned with plant input at {index}"
        if not finite_vector(step.get("plant_input_x"), 6) or not finite_vector(step.get("plant_output_x_next"), 6):
            return [], False, f"plant state facts invalid at {index}"
    return steps, True, "COMMITTED_CONTROL_AND_PLANT_TRACE"


def empty_metrics() -> dict[str, int]:
    return {key: 0 for key in METRIC_KEYS}


def add_anomaly(anomalies: list[dict[str, Any]], run_id: str, trial_id: int, category: str, sequence: Any, detail: str) -> None:
    anomalies.append({
        "run_id": run_id, "trial_id": trial_id, "category": category,
        "payload_sequence_id": "" if sequence is None else sequence, "detail": detail,
    })


def aggregate_run(run_root: Path, record: dict[str, Any], anomalies: list[dict[str, Any]]) -> dict[str, Any]:
    run_id = str(record["run_id"])
    trial_id = int(record["trial_id"])
    metrics = empty_metrics()
    trace = load_json(run_root / "primary_trace.json")
    intended, denominator_resolved, denominator_source = intended_trace_steps(trace)
    if trace.get("trial_id") != trial_id:
        denominator_resolved = False
        denominator_source = "OFFICIAL_TRIAL_ID_MISMATCH_BETWEEN_MANIFEST_AND_TRACE"
        intended = []
    metrics["N_intended_steps"] = len(intended)

    inst = run_root / "instrumentation"
    map_manifest = load_json(inst / "map_authority_manifest.json")
    map_id = map_manifest.get("map_authority_id")
    map_manifest_valid = (
        isinstance(map_id, str) and len(map_id) == 64
        and map_manifest.get("full_map_hash_call_count_per_run") == 1
        and map_manifest.get("per_step_full_map_hash_count") == 0
        and isinstance(map_manifest.get("artifacts"), list) and bool(map_manifest["artifacts"])
    )

    captures: dict[int, dict[str, Any]] = {}
    capture_line_count = 0
    capture_path = inst / "step_capture_log.jsonl"
    for capture in iter_jsonl(capture_path, anomalies, run_id, trial_id):
        capture_line_count += 1
        sequence = capture.get("payload_sequence_id")
        if not isinstance(sequence, int):
            metrics["N_schema_failure"] += 1
            add_anomaly(anomalies, run_id, trial_id, "SCHEMA_FAILURE", sequence, "capture payload_sequence_id is not integer")
            continue
        if sequence in captures:
            metrics["N_duplicate_payload"] += 1
            add_anomaly(anomalies, run_id, trial_id, "DUPLICATE_PAYLOAD", sequence, "duplicate capture sequence")
        else:
            captures[sequence] = capture
    metrics["N_captured_payloads"] = capture_line_count
    metrics["N_unique_payloads"] = len(captures)

    results: dict[int, dict[str, Any]] = {}
    result_path = inst / "shadow_certificate_result_log.jsonl"
    for result in iter_jsonl(result_path, anomalies, run_id, trial_id):
        sequence = result.get("payload_sequence_id")
        if not isinstance(sequence, int):
            metrics["N_schema_failure"] += 1
            add_anomaly(anomalies, run_id, trial_id, "SCHEMA_FAILURE", sequence, "result payload_sequence_id is not integer")
            continue
        if sequence in results:
            metrics["N_duplicate_result"] += 1
            add_anomaly(anomalies, run_id, trial_id, "DUPLICATE_RESULT", sequence, "duplicate result sequence")
        else:
            results[sequence] = result
        if result.get("l2_reached") is True and result.get("l2_status") == "UNKNOWN":
            metrics["L2_UNKNOWN_count"] += 1

    health_path = inst / "instrumentation_health_log.jsonl"
    for health in iter_jsonl(health_path, anomalies, run_id, trial_id):
        status = health.get("status")
        health_status = health.get("health")
        if status == "DROPPED_QUEUE_FULL":
            metrics["N_queue_drop"] += 1
        if status == "SERIALIZATION_ERROR" or health_status == "SERIALIZATION_ERROR":
            metrics["N_serialization_error"] += 1
        if health_status == "WORKER_EXCEPTION":
            metrics["N_worker_exception"] += 1
        if status == "WORKER_UNAVAILABLE" or health_status == "WORKER_UNAVAILABLE":
            metrics["N_worker_unavailable"] += 1
        if health_status == "PAYLOAD_ALIGNMENT_FAILURE":
            metrics["N_alignment_failure"] += 1
        if health_status == "SCHEMA_VALIDATION_FAILURE":
            metrics["N_schema_failure"] += 1
        if health_status == "MAP_AUTHORITY_FAILURE":
            metrics["N_map_authority_failure"] += 1
        if health_status == "SHUTDOWN_INCOMPLETE":
            metrics["N_shutdown_incomplete"] += 1
        if health_status == "RESULT_LATE":
            metrics["N_result_late"] += 1
        if health.get("classified_as_l2_unknown") is True:
            metrics["N_schema_failure"] += 1
            add_anomaly(anomalies, run_id, trial_id, "HEALTH_MISCLASSIFIED_AS_L2_UNKNOWN", health.get("payload_sequence_id"), str(health.get("detail")))

    activation = load_json(run_root / "arm_activation.json")
    if activation.get("shutdown_status") != "SHUTDOWN_COMPLETE" or activation.get("worker_alive_after_shutdown") is not False:
        metrics["N_shutdown_incomplete"] += 1
        add_anomaly(anomalies, run_id, trial_id, "SHUTDOWN_INCOMPLETE", None, "activation shutdown did not complete")
    if activation.get("worker_exception_count", 0):
        metrics["N_worker_exception"] += int(activation["worker_exception_count"])

    expected_sequences = set(range(len(intended))) if denominator_resolved else set()
    capture_sequences = set(captures)
    result_sequences = set(results)
    gaps = sorted(expected_sequences - capture_sequences)
    metrics["N_sequence_gap"] = len(gaps)
    for sequence in gaps:
        add_anomaly(anomalies, run_id, trial_id, "SEQUENCE_GAP", sequence, "independent intended step has no capture")
    orphan_results = sorted(result_sequences - capture_sequences)
    metrics["N_orphan_result"] = len(orphan_results)
    for sequence in orphan_results:
        add_anomaly(anomalies, run_id, trial_id, "ORPHAN_RESULT", sequence, "result has no capture")
    without_result = sorted(capture_sequences - result_sequences)
    metrics["N_capture_without_result"] = len(without_result)
    for sequence in without_result:
        add_anomaly(anomalies, run_id, trial_id, "CAPTURE_WITHOUT_RESULT", sequence, "capture has no terminal result")

    runtime_trial_tokens = {
        capture.get("trial_id") for capture in captures.values()
        if isinstance(capture.get("trial_id"), str) and capture.get("trial_id")
    }
    for sequence, step in enumerate(intended):
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
            and isinstance(capture.get("decision_commit_id"), str) and bool(capture.get("decision_commit_id"))
        )
        if selected_valid:
            metrics["N_valid_selected_u"] += 1
        else:
            add_anomaly(anomalies, run_id, trial_id, "SELECTED_U_OR_PROVENANCE_INVALID", sequence, "selected executed control is missing, nonnumeric, or misaligned")

        semantic = {key: capture.get(key) for key in CAPTURE_SEMANTIC_KEYS}
        expected_payload_hash = semantic_sha256(semantic)
        payload_hash_valid = (
            capture.get("payload_semantic_hash") == expected_payload_hash
            and capture.get("payload_worker_receive_semantic_hash") == expected_payload_hash
        )
        if payload_hash_valid:
            metrics["N_valid_payload_hash"] += 1
        else:
            metrics["N_alignment_failure"] += 1
            add_anomaly(anomalies, run_id, trial_id, "PAYLOAD_HASH_FAILURE", sequence, "enqueue/receive/recomputed payload hash mismatch")

        if map_manifest_valid and capture.get("map_authority_id") == map_id == step.get("map_authority_id"):
            metrics["N_map_authority_resolved"] += 1
        else:
            metrics["N_map_authority_failure"] += 1
            add_anomaly(anomalies, run_id, trial_id, "MAP_AUTHORITY_FAILURE", sequence, "step map reference does not resolve to immutable run manifest")

        if result is None:
            continue
        if reachability_complete(capture, result):
            metrics["N_reachability_complete"] += 1
        else:
            add_anomaly(anomalies, run_id, trial_id, "REACHABILITY_INCOMPLETE", sequence, "typed L0/L1/L2 reachability or reason missing")
        if terminal_l2(result):
            metrics["N_terminal_shadow_records"] += 1
        else:
            add_anomaly(anomalies, run_id, trial_id, "NONTERMINAL_SHADOW_RESULT", sequence, "result lacks legal final L2 state/reason")

        result_semantic = {key: result.get(key) for key in RESULT_SEMANTIC_KEYS}
        result_hash_valid = result.get("result_semantic_hash") == semantic_sha256(result_semantic)
        trial_token = capture.get("trial_id")
        runtime_trial_token_valid = (
            isinstance(trial_token, str)
            and trial_token.startswith("trial-")
            and len(runtime_trial_tokens) == 1
            and result.get("trial_id") == trial_token
        )
        expected_decision = f"{run_id}:{trial_token}:commit:{sequence:06d}"
        expected_state = f"{run_id}:{trial_token}:state:{sequence:06d}"
        expected_candidate = f"{run_id}:{trial_token}:selected:{sequence:06d}"
        join_valid = all((
            capture.get("run_id") == result.get("run_id") == run_id,
            runtime_trial_token_valid,
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
        if join_valid:
            metrics["N_joinable_records"] += 1
        else:
            add_anomaly(anomalies, run_id, trial_id, "JOIN_FAILURE", sequence, "capture/result IDs or semantic hashes do not join uniquely")

    denominators = {
        "capture_completeness": metrics["N_captured_payloads"] / metrics["N_intended_steps"] if metrics["N_intended_steps"] else None,
        "selected_u_completeness": metrics["N_valid_selected_u"] / metrics["N_intended_steps"] if metrics["N_intended_steps"] else None,
        "map_authority_completeness": metrics["N_map_authority_resolved"] / metrics["N_intended_steps"] if metrics["N_intended_steps"] else None,
        "reachability_completeness": metrics["N_reachability_complete"] / metrics["N_intended_steps"] if metrics["N_intended_steps"] else None,
        "shadow_result_completion": metrics["N_terminal_shadow_records"] / metrics["N_captured_payloads"] if metrics["N_captured_payloads"] else None,
        "join_completeness": metrics["N_joinable_records"] / metrics["N_captured_payloads"] if metrics["N_captured_payloads"] else None,
    }
    return {
        "run_id": run_id,
        "trial_id": trial_id,
        "data_role": "PILOT_QA_ONLY",
        "eligible_for_formal_prospective_cohort": False,
        "denominator_resolved": denominator_resolved,
        "denominator_source": denominator_source,
        "runtime_trial_token": next(iter(runtime_trial_tokens)) if len(runtime_trial_tokens) == 1 else None,
        "map_authority_id": map_id,
        **metrics,
        **denominators,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def aggregate(raw_root: Path, output_dir: Path) -> dict[str, Any]:
    raw_root = raw_root.resolve(strict=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = load_json(raw_root.parent / "pilot_run_manifest.json")
    anomalies: list[dict[str, Any]] = []
    per_trial: list[dict[str, Any]] = []
    for record in manifest.get("runs", []):
        run_root = raw_root / record["run_id"]
        per_trial.append(aggregate_run(run_root, record, anomalies))

    totals = empty_metrics()
    for row in per_trial:
        for key in METRIC_KEYS:
            totals[key] += int(row[key])
    rates = {
        "capture_completeness": totals["N_captured_payloads"] / totals["N_intended_steps"] if totals["N_intended_steps"] else None,
        "selected_u_completeness": totals["N_valid_selected_u"] / totals["N_intended_steps"] if totals["N_intended_steps"] else None,
        "map_authority_completeness": totals["N_map_authority_resolved"] / totals["N_intended_steps"] if totals["N_intended_steps"] else None,
        "reachability_completeness": totals["N_reachability_complete"] / totals["N_intended_steps"] if totals["N_intended_steps"] else None,
        "shadow_result_completion": totals["N_terminal_shadow_records"] / totals["N_captured_payloads"] if totals["N_captured_payloads"] else None,
        "join_completeness": totals["N_joinable_records"] / totals["N_captured_payloads"] if totals["N_captured_payloads"] else None,
    }
    run_valid = (
        len(manifest.get("runs", [])) == 5
        and all(record.get("exit_code") == 0 and record.get("activation_valid") is True for record in manifest["runs"])
    )
    denominator_resolved = len(per_trial) == 5 and all(row["denominator_resolved"] for row in per_trial)
    all_rates_one = all(value == 1.0 for value in rates.values())
    errors_zero = all(totals[key] == 0 for key in ERROR_KEYS) and totals["N_orphan_result"] == 0 and totals["N_capture_without_result"] == 0
    if not denominator_resolved:
        selected_case = "CASE_C"
        final_status = "BLOCKED_L2_H1_SHADOW_LOGGING_PILOT_BY_DENOMINATOR"
        final_decision = "DO_NOT_FREEZE_FORMAL_COHORT_AND_FIX_INTENDED_STEP_ACCOUNTING"
        only_next = "FIX_L2_H1_INTENDED_STEP_ACCOUNTING_V1"
    elif not run_valid:
        selected_case = "CASE_D"
        final_status = "BLOCKED_L2_H1_SHADOW_LOGGING_PILOT_BY_INVALID_RUN"
        final_decision = "DO_NOT_FREEZE_FORMAL_COHORT"
        only_next = "FIX_L2_H1_SHADOW_RUNTIME_ACTIVATION_V1"
    elif all_rates_one and errors_zero and not anomalies:
        selected_case = "CASE_A"
        final_status = "PASS_L2_H1_SHADOW_LOGGING_COMPLETENESS_PILOT_V1"
        final_decision = "FREEZE_LOGGING_PIPELINE_AND_PREPARE_FORMAL_PROSPECTIVE_SHADOW_COHORT"
        only_next = "FREEZE_L2_H1_PROSPECTIVE_SHADOW_COHORT_PROTOCOL_V1"
    else:
        selected_case = "CASE_B"
        final_status = "FAIL_L2_H1_SHADOW_LOGGING_COMPLETENESS_PILOT_V1"
        final_decision = "DO_NOT_FREEZE_FORMAL_COHORT_AND_FIX_LOGGING_PIPELINE"
        only_next = "FIX_L2_H1_SHADOW_LOGGING_COMPLETENESS_V1"

    overall = {
        "schema_version": "L2_H1_SHADOW_LOGGING_COMPLETENESS_PILOT_SUMMARY_V1",
        "data_role": "PILOT_QA_ONLY",
        "eligible_for_formal_prospective_cohort": False,
        "pilot_trial_count": len(per_trial),
        "pilot_navigation_run_count": len(manifest.get("runs", [])),
        "wrapper_on_run_count": sum(record.get("arm") == "WRAPPER_ON" for record in manifest.get("runs", [])),
        "denominator_resolved": denominator_resolved,
        "run_valid": run_valid,
        **totals,
        **rates,
        "instrumentation_health_separate_from_l2_unknown": totals["N_schema_failure"] == 0,
        "controller_mutation_count": 0,
        "instrumentation_mutation_count": 0,
        "controller_intervention_count": sum(int(record.get("activation", {}).get("controller_intervention_count", 0)) for record in manifest.get("runs", [])),
        "candidate_replacement_count": sum(int(record.get("activation", {}).get("selected_candidate_replacement_count", 0)) for record in manifest.get("runs", [])),
        "formal_on_policy_cohort_count": 0,
        "formal_performance_metric_count": 0,
        "formal_runtime_metric_count": 0,
        "selected_case": selected_case,
        "FINAL_STATUS": final_status,
        "FINAL_DECISION": final_decision,
        "Only_next_task": only_next,
    }

    per_fields = [
        "run_id", "trial_id", "data_role", "eligible_for_formal_prospective_cohort",
        "denominator_resolved", "denominator_source", "runtime_trial_token", "map_authority_id", *METRIC_KEYS,
        "capture_completeness", "selected_u_completeness", "map_authority_completeness",
        "reachability_completeness", "shadow_result_completion", "join_completeness",
    ]
    write_csv(output_dir / "pilot_per_trial_summary.csv", per_trial, per_fields)
    write_json(output_dir / "pilot_overall_summary.json", overall)
    anomaly_rows = anomalies or [{"run_id": "", "trial_id": "", "category": "NONE", "payload_sequence_id": "", "detail": "NONE"}]
    write_csv(output_dir / "pilot_anomalies.csv", anomaly_rows, ["run_id", "trial_id", "category", "payload_sequence_id", "detail"])
    write_json(output_dir / "join_integrity.json", {
        "pass": totals["N_joinable_records"] == totals["N_captured_payloads"] and totals["N_orphan_result"] == 0 and totals["N_capture_without_result"] == 0 and totals["N_duplicate_payload"] == 0 and totals["N_duplicate_result"] == 0,
        "N_joinable_records": totals["N_joinable_records"],
        "N_captured_payloads": totals["N_captured_payloads"],
        "N_orphan_result": totals["N_orphan_result"],
        "N_capture_without_result": totals["N_capture_without_result"],
        "N_duplicate_payload": totals["N_duplicate_payload"],
        "N_duplicate_result": totals["N_duplicate_result"],
    })
    write_json(output_dir / "sequence_integrity.json", {
        "pass": totals["N_sequence_gap"] == 0 and totals["N_duplicate_payload"] == 0 and totals["N_duplicate_result"] == 0,
        "N_sequence_gap": totals["N_sequence_gap"],
        "N_duplicate_payload": totals["N_duplicate_payload"],
        "N_duplicate_result": totals["N_duplicate_result"],
        "per_trial_denominator_resolved": {row["run_id"]: row["denominator_resolved"] for row in per_trial},
    })

    raw_rows: list[dict[str, Any]] = []
    for path in sorted(item for item in raw_root.parent.rglob("*") if item.is_file() and output_dir not in item.parents):
        raw_rows.append({
            "relative_path": path.relative_to(raw_root.parent).as_posix(),
            "size": path.stat().st_size,
            "sha256": file_sha256(path),
            "retention": "SERVER_ONLY_RAW" if path.suffix in {".jsonl", ".log"} or "raw_runs" in path.parts else "SERVER_TASK_RECORD",
        })
    write_csv(output_dir / "raw_artifact_manifest.csv", raw_rows, ["relative_path", "size", "sha256", "retention"])
    return overall


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    summary = aggregate(args.raw_root, args.output_dir)
    print(json.dumps(summary, sort_keys=True), flush=True)
    return 0 if summary["selected_case"] == "CASE_A" else 2


if __name__ == "__main__":
    raise SystemExit(main())
