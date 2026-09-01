#!/usr/bin/env python3
"""Synthetic-only tests for outcome-blind collection QC and stop semantics."""

from __future__ import annotations

import copy
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from collection_common import CAPTURE_SEMANTIC_KEYS, DATA_ROLE, MAP_AUTHORITY_ID, RESULT_SEMANTIC_KEYS, semantic_sha256  # noqa: E402
from outcome_blind_qc import qc  # noqa: E402


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def valid_fixture(root: Path) -> tuple[dict, dict]:
    run_id = "formal-v1-trial-000-attempt-0"
    token = "trial-000000"
    u = [0.1, 0.2, 0.3]
    candidate_id = f"{run_id}:{token}:selected:000000"
    capture = {
        "schema_version": "STEP", "run_id": run_id, "trial_id": token, "step_id": 0,
        "state_sequence_id": f"{run_id}:{token}:state:000000",
        "decision_commit_id": f"{run_id}:{token}:commit:000000",
        "payload_sequence_id": 0, "x_k": [0.0] * 6, "p_k": [0.0] * 3, "v_k": [0.0] * 3, "dt": 0.05,
        "selected_candidate": {
            "candidate_id": candidate_id, "candidate_role": "SELECTED_EXECUTED_CONTROL",
            "selected_for_execution": True, "created_before_observation": True,
            "candidate_origin": "FROZEN_CONTROLLER", "u": u,
        },
        "native_sibling_candidates": [], "candidate_group_id": "g0", "native_candidate_group_size": 1,
        "reachability": {
            "candidate_preparation_reached": True, "decision_committed": True,
            "l0_observation_source": "runtime", "l1_observation_source": "runtime",
            "l2_reached": True, "l2_reachability_reason": "SELECTED_CANDIDATE_AVAILABLE",
        },
        "map_authority_id": MAP_AUTHORITY_ID,
        "controller_authority": False, "execution_authority": False,
        "candidate_selection_authority": False, "intervention": False, "shadow_only": True,
    }
    capture_hash = semantic_sha256({key: capture.get(key) for key in CAPTURE_SEMANTIC_KEYS})
    capture["payload_semantic_hash"] = capture_hash
    capture["payload_worker_receive_semantic_hash"] = capture_hash
    result = {
        "run_id": run_id, "trial_id": token, "step_id": 0,
        "state_sequence_id": capture["state_sequence_id"], "decision_commit_id": capture["decision_commit_id"],
        "payload_sequence_id": 0, "selected_candidate_id": candidate_id, "map_authority_id": MAP_AUTHORITY_ID,
        "payload_enqueue_semantic_hash": capture_hash, "payload_worker_receive_semantic_hash": capture_hash,
        "l0_status": "PASS", "l0_reason": "runtime", "l0_observation_source": "runtime",
        "l1_status": "PASS", "l1_reason": "runtime", "l1_observation_source": "runtime",
        "l2_reached": True, "l2_reachability_reason": "SELECTED_CANDIDATE_AVAILABLE",
        "l2_status": "PASS", "l2_reason": "synthetic_typed_fixture", "backend_identity": "synthetic",
    }
    result["result_semantic_hash"] = semantic_sha256({key: result.get(key) for key in RESULT_SEMANTIC_KEYS})
    write_json(root / "formal_attempt_identity.json", {
        "trial_id": 0, "attempt_id": 0, "run_id": run_id, "data_role": DATA_ROLE,
        "eligible_for_formal_prospective_cohort": True,
    })
    write_json(root / "process_result.json", {
        "exit_code": 0, "intended_step_count": 1, "capture_count": 1, "result_record_count": 1,
    })
    write_json(root / "run/primary_trace.json", {"trial_id": 0, "steps": [{
        "step_id": 0, "selected_u_k": u, "selected_candidate_hash": "a" * 64,
        "selected_candidate_identity": candidate_id, "plant_input_x": [0.0] * 6,
        "plant_input_u": u, "plant_output_x_next": [0.0] * 6, "map_authority_id": MAP_AUTHORITY_ID,
    }]})
    write_json(root / "run/instrumentation/map_authority_manifest.json", {
        "map_authority_id": MAP_AUTHORITY_ID, "full_map_hash_call_count_per_run": 1,
        "per_step_full_map_hash_count": 0, "artifacts": [{"sha256": "b" * 64}],
    })
    write_jsonl(root / "run/instrumentation/step_capture_log.jsonl", [capture])
    write_jsonl(root / "run/instrumentation/shadow_certificate_result_log.jsonl", [result])
    write_jsonl(root / "run/instrumentation/instrumentation_health_log.jsonl", [])
    write_json(root / "run/arm_activation.json", {
        "shutdown_status": "SHUTDOWN_COMPLETE", "worker_alive_after_shutdown": False,
        "worker_exception_count": 0, "controller_intervention_count": 0,
        "selected_candidate_replacement_count": 0,
    })
    return capture, result


def run_case(name: str, mutation, expected_pass: bool) -> None:
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        capture, result = valid_fixture(root)
        mutation(root, capture, result)
        try:
            actual = qc(root)["pass"]
        except Exception:
            actual = False
        if actual is not expected_pass:
            raise AssertionError(f"{name}: expected {expected_pass}, got {actual}")
        print(f"{name}=PASS")


def main() -> int:
    noop = lambda root, capture, result: None
    run_case("valid", noop, True)
    run_case("missing_capture", lambda r, c, x: write_jsonl(r / "run/instrumentation/step_capture_log.jsonl", []), False)
    run_case("missing_result", lambda r, c, x: write_jsonl(r / "run/instrumentation/shadow_certificate_result_log.jsonl", []), False)
    run_case("duplicate_payload", lambda r, c, x: write_jsonl(r / "run/instrumentation/step_capture_log.jsonl", [c, c]), False)
    orphan = lambda r, c, x: write_jsonl(r / "run/instrumentation/shadow_certificate_result_log.jsonl", [dict(x, payload_sequence_id=1)])
    run_case("orphan_result", orphan, False)
    def bad_u(r, c, x):
        y = copy.deepcopy(c); y["selected_candidate"]["u"] = [9.0, 9.0, 9.0]
        write_jsonl(r / "run/instrumentation/step_capture_log.jsonl", [y])
    run_case("selected_u_mismatch", bad_u, False)
    def bad_map(r, c, x):
        manifest = json.loads((r / "run/instrumentation/map_authority_manifest.json").read_text())
        manifest["map_authority_id"] = "0" * 64; write_json(r / "run/instrumentation/map_authority_manifest.json", manifest)
    run_case("map_identity_mismatch", bad_map, False)
    run_case("queue_drop", lambda r, c, x: write_jsonl(r / "run/instrumentation/instrumentation_health_log.jsonl", [{"status": "DROPPED_QUEUE_FULL"}]), False)
    def bad_hash(r, c, x):
        y = dict(c); y["payload_semantic_hash"] = "0" * 64; write_jsonl(r / "run/instrumentation/step_capture_log.jsonl", [y])
    run_case("payload_hash_mismatch", bad_hash, False)
    def bad_reach(r, c, x):
        y = copy.deepcopy(c); del y["reachability"]["l2_reachability_reason"]
        y["payload_semantic_hash"] = semantic_sha256({key: y.get(key) for key in CAPTURE_SEMANTIC_KEYS})
        y["payload_worker_receive_semantic_hash"] = y["payload_semantic_hash"]
        z = dict(x, payload_enqueue_semantic_hash=y["payload_semantic_hash"], payload_worker_receive_semantic_hash=y["payload_semantic_hash"])
        write_jsonl(r / "run/instrumentation/step_capture_log.jsonl", [y]); write_jsonl(r / "run/instrumentation/shadow_certificate_result_log.jsonl", [z])
    run_case("reachability_missing", bad_reach, False)
    run_case("shutdown_incomplete", lambda r, c, x: write_json(r / "run/arm_activation.json", {"shutdown_status": "INCOMPLETE", "worker_alive_after_shutdown": True, "worker_exception_count": 0, "controller_intervention_count": 0, "selected_candidate_replacement_count": 0}), False)
    def untyped_status(r, c, x):
        y = dict(x); y["l2_status"] = None; y["result_semantic_hash"] = semantic_sha256({key: y.get(key) for key in RESULT_SEMANTIC_KEYS}); write_jsonl(r / "run/instrumentation/shadow_certificate_result_log.jsonl", [y])
    run_case("l2_status_untyped", untyped_status, False)
    print("SYNTHETIC_TEST_COUNT=12")
    print("SCIENTIFIC_OUTCOME_AGGREGATION_COUNT=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
