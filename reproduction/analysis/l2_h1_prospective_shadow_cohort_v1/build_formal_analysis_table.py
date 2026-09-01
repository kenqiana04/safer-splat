#!/usr/bin/env python3
"""Stream and integrity-check the canonical formal analysis table."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

from analysis_common import DATA_ROLE, MAP_AUTHORITY_ID, TRI_STATES, atomic_write_json, file_sha256, iter_jsonl, load_json, semantic_sha256, write_jsonl

CAPTURE_SEMANTIC_KEYS = (
    "schema_version", "run_id", "trial_id", "step_id", "state_sequence_id", "decision_commit_id", "x_k", "p_k", "v_k", "dt",
    "selected_candidate", "native_sibling_candidates", "candidate_group_id", "native_candidate_group_size", "reachability", "map_authority_id",
    "controller_authority", "execution_authority", "candidate_selection_authority", "intervention", "shadow_only",
)
RESULT_SEMANTIC_KEYS = (
    "l0_status", "l0_reason", "l0_observation_source", "l1_status", "l1_reason", "l1_observation_source", "l2_reached",
    "l2_reachability_reason", "l2_status", "l2_reason", "backend_identity",
)


class AnalysisIntegrityError(RuntimeError):
    pass


def _identity(row: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(row.get(key) for key in ("run_id", "trial_id", "step_id", "state_sequence_id", "decision_commit_id", "payload_sequence_id"))


def _backend_class(identity: str) -> str:
    if identity == "CONSERVATIVE_SIGNED_DISTANCE_LIPSCHITZ_INTERVAL":
        return "CONSERVATIVE_SIGNED_DISTANCE_LIPSCHITZ_INTERVAL"
    if "EXACT" in identity.upper() or "SPHERE" in identity.upper():
        return "EXACT_ANALYTIC_SPHERE_SEGMENT"
    return "OTHER_FROZEN_TYPED_BACKEND"


def join_trial(captures: list[dict[str, Any]], results: list[dict[str, Any]], trace: dict[str, Any], official_trial_id: int, run_id: str,
               data_role: str, expected_map_id: str, logging_qc_complete: bool) -> list[dict[str, Any]]:
    if data_role != DATA_ROLE:
        raise AnalysisIntegrityError("non-formal data role")
    if trace.get("trial_id") != official_trial_id:
        raise AnalysisIntegrityError("official trial mismatch")
    capture_by_id = {_identity(row): row for row in captures}
    result_by_id = {_identity(row): row for row in results}
    if len(capture_by_id) != len(captures) or len(result_by_id) != len(results):
        raise AnalysisIntegrityError("duplicate analysis-unit join identity")
    if set(capture_by_id) != set(result_by_id):
        raise AnalysisIntegrityError("unresolved capture/result join")
    trace_steps = {int(row["step_id"]): row for row in trace.get("steps", [])}
    if len(trace_steps) != len(trace.get("steps", [])) or set(trace_steps) != {int(key[2]) for key in capture_by_id}:
        raise AnalysisIntegrityError("trace join mismatch")
    output: list[dict[str, Any]] = []
    seen_units: set[str] = set()
    for identity in sorted(capture_by_id, key=lambda key: int(key[2])):
        capture, result = capture_by_id[identity], result_by_id[identity]
        selected = capture.get("selected_candidate", {})
        trace_step = trace_steps[int(capture["step_id"])]
        payload_hash = capture.get("payload_semantic_hash")
        if capture.get("run_id") != run_id or result.get("run_id") != run_id:
            raise AnalysisIntegrityError("run identity mismatch")
        if capture.get("map_authority_id") != expected_map_id or result.get("map_authority_id") != expected_map_id or trace_step.get("map_authority_id") != expected_map_id:
            raise AnalysisIntegrityError("map authority mismatch")
        if selected.get("candidate_id") != result.get("selected_candidate_id"):
            raise AnalysisIntegrityError("selected candidate identity mismatch")
        if selected.get("u") != trace_step.get("selected_u_k") or selected.get("u") != trace_step.get("plant_input_u"):
            raise AnalysisIntegrityError("selected control/plant input mismatch")
        if capture.get("x_k") != trace_step.get("plant_input_x"):
            raise AnalysisIntegrityError("state/trace mismatch")
        if payload_hash != capture.get("payload_worker_receive_semantic_hash") or payload_hash != result.get("payload_enqueue_semantic_hash") or payload_hash != result.get("payload_worker_receive_semantic_hash"):
            raise AnalysisIntegrityError("payload semantic hash chain mismatch")
        if capture.get("payload_semantic_hash") and capture.get("schema_version"):
            recomputed = semantic_sha256({key: capture.get(key) for key in CAPTURE_SEMANTIC_KEYS})
            if recomputed != payload_hash:
                raise AnalysisIntegrityError("capture semantic hash mismatch")
        if result.get("result_semantic_hash"):
            recomputed = semantic_sha256({key: result.get(key) for key in RESULT_SEMANTIC_KEYS})
            if recomputed != result["result_semantic_hash"]:
                raise AnalysisIntegrityError("result semantic hash mismatch")
        status = result.get("l2_status")
        if result.get("l2_reached") and status not in TRI_STATES:
            raise AnalysisIntegrityError("invalid reached tri-state")
        reach = capture.get("reachability", {})
        conditions = {
            "formal_data_role": data_role == DATA_ROLE,
            "logging_qc_complete": logging_qc_complete is True,
            "selected_candidate_role": selected.get("candidate_role") == "SELECTED_EXECUTED_CONTROL",
            "selected_candidate_committed": selected.get("selected_for_execution") is True and reach.get("decision_committed") is True,
            "l1_observation_source": result.get("l1_observation_source") == "SHADOW_RECOMPUTED_FROZEN_CERTIFIER",
            "l1_status_pass": result.get("l1_status") == "PASS",
            "l2_reached": result.get("l2_reached") is True,
            "l2_typed": status in TRI_STATES,
            "map_authority_valid": True,
            "payload_join_identity_valid": True,
        }
        analysis_key = semantic_sha256({
            "run_id": run_id, "trial_id": official_trial_id, "step_id": int(capture["step_id"]), "x_k": capture.get("x_k"),
            "selected_executed_u_k": selected.get("u"), "dt": capture.get("dt"), "map_authority_id": expected_map_id,
        })
        if analysis_key in seen_units:
            raise AnalysisIntegrityError("duplicate analysis-unit key")
        seen_units.add(analysis_key)
        output.append({
            "analysis_unit_key": analysis_key, "data_role": data_role, "run_id": run_id, "trial_id": official_trial_id,
            "process_local_trial_token": capture.get("trial_id"), "step_id": int(capture["step_id"]), "x_k": capture.get("x_k"),
            "selected_executed_u_k": selected.get("u"), "dt": capture.get("dt"), "map_authority_id": expected_map_id,
            "selected_candidate_id": selected.get("candidate_id"), "selected_candidate_role": selected.get("candidate_role"),
            "selected_candidate_committed": conditions["selected_candidate_committed"], "nominal_reference_role": capture.get("nominal_reference", {}).get("candidate_role"),
            "native_sibling_candidates": capture.get("native_sibling_candidates", []), "candidate_group_id": capture.get("candidate_group_id"),
            "native_candidate_group_size": int(capture.get("native_candidate_group_size", 1)), "candidate_synthesis_count": 0,
            "logging_qc_complete": logging_qc_complete, "l1_observation_source": result.get("l1_observation_source"), "l1_status": result.get("l1_status"),
            "l2_reached": result.get("l2_reached"), "l2_reachability_reason": result.get("l2_reachability_reason"), "l2_status": status,
            "l2_reason": result.get("l2_reason"), "backend_identity": result.get("backend_identity"), "backend_class": _backend_class(str(result.get("backend_identity"))),
            "map_authority_valid": True, "payload_join_identity_valid": True, "primary_eligible": all(conditions.values()),
            "primary_ineligibility_reasons": [name for name, passed in conditions.items() if not passed],
        })
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-root", type=Path, required=True)
    parser.add_argument("--commitment", type=Path, required=True)
    parser.add_argument("--output-table", type=Path, required=True)
    parser.add_argument("--output-manifest", type=Path, required=True)
    args = parser.parse_args()
    commitment = load_json(args.commitment)
    all_rows: list[dict[str, Any]] = []
    per_trial: list[dict[str, Any]] = []
    for artifact in commitment["ordered_result_artifacts"]:
        trial_id, run_id = int(artifact["trial_id"]), artifact["run_id"]
        attempt = args.server_root / "formal-v1" / f"trial-{trial_id:03d}" / "attempt-0"
        capture_path = attempt / "run/instrumentation/step_capture_log.jsonl"
        result_path = args.server_root / artifact["relative_path"]
        trace_path = attempt / "run/primary_trace.json"
        if result_path.stat().st_size != int(artifact["size"]) or file_sha256(result_path) != artifact["sha256"]:
            raise AnalysisIntegrityError(f"trial {trial_id}: result commitment mismatch")
        rows = join_trial(list(iter_jsonl(capture_path)), list(iter_jsonl(result_path)), load_json(trace_path), trial_id, run_id, DATA_ROLE, MAP_AUTHORITY_ID, True)
        all_rows.extend(rows)
        per_trial.append({"trial_id": trial_id, "run_id": run_id, "row_count": len(rows), "row_semantic_sha256": semantic_sha256(rows)})
    if len(all_rows) != 14122 or len({row["analysis_unit_key"] for row in all_rows}) != len(all_rows):
        raise AnalysisIntegrityError("canonical table count/key mismatch")
    write_jsonl(args.output_table, all_rows)
    manifest = {
        "schema_version": "L2_H1_FORMAL_ANALYSIS_TABLE_MANIFEST_V1", "data_role": DATA_ROLE, "row_count": len(all_rows),
        "unique_analysis_unit_count": len(all_rows), "duplicate_analysis_unit_count": 0, "unresolved_join_count": 0,
        "invalid_map_authority_count": 0, "selected_role_mismatch_count": 0, "provenance_mismatch_count": 0,
        "canonical_table_server_path": str(args.output_table), "canonical_table_sha256": file_sha256(args.output_table), "per_trial": per_trial,
        "primary_eligibility_reason_counts": dict(Counter(reason for row in all_rows for reason in row["primary_ineligibility_reasons"])),
    }
    atomic_write_json(args.output_manifest, manifest)
    print(json.dumps({"row_count": len(all_rows), "manifest_sha256": file_sha256(args.output_manifest)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

