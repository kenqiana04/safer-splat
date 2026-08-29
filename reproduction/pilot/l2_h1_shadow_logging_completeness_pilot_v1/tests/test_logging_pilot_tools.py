from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest


TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK))

from aggregate_logging_pilot import (  # noqa: E402
    CAPTURE_SEMANTIC_KEYS,
    RESULT_SEMANTIC_KEYS,
    aggregate,
    intended_trace_steps,
    semantic_sha256,
)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


class LoggingPilotToolsTest(unittest.TestCase):
    def build_fixture(self, root: Path, *, unknown: bool = False, duplicate: bool = False, omit_result: bool = False) -> tuple[Path, Path]:
        task_root = root / "server_task"
        raw_root = task_root / "raw_runs"
        run_id = "pilot_c_trial010"
        # The frozen wrapper assigns a process-local trial token even when the
        # official manifest trial selected for this one-trial process is 10.
        trial_token = "trial-000000"
        run_root = raw_root / run_id
        inst = run_root / "instrumentation"
        map_id = "a" * 64
        selected = {
            "candidate_id": f"{run_id}:{trial_token}:selected:000000",
            "candidate_origin": "FROZEN_CBF_SOLVE_QP_SUCCESS_OUTPUT",
            "candidate_role": "SELECTED_EXECUTED_CONTROL",
            "created_before_observation": True,
            "selected_for_execution": True,
            "u": [0.1, 0.0, 0.0],
        }
        capture = {
            "schema_version": "L2_H1_ON_POLICY_SHADOW_STEP_PAYLOAD_V1",
            "run_id": run_id,
            "trial_id": trial_token,
            "step_id": 0,
            "state_sequence_id": f"{run_id}:{trial_token}:state:000000",
            "decision_commit_id": f"{run_id}:{trial_token}:commit:000000",
            "payload_sequence_id": 0,
            "x_k": [0.0] * 6,
            "p_k": [0.0] * 3,
            "v_k": [0.0] * 3,
            "dt": 0.05,
            "selected_candidate": selected,
            "nominal_reference": {"candidate_role": "NOMINAL_REFERENCE", "u": [0.1, 0.0, 0.0]},
            "native_sibling_candidates": [],
            "candidate_group_id": f"{run_id}:{trial_token}:commit:000000:native-group",
            "native_candidate_group_size": 1,
            "reachability": {
                "candidate_preparation_reached": True,
                "decision_committed": True,
                "l0_observation_source": "NOT_OBSERVED_IN_PRODUCTION",
                "l1_observation_source": "NOT_OBSERVED_IN_PRODUCTION",
                "l2_reached": False,
                "l2_reachability_reason": "PENDING_SHADOW_RECOMPUTATION",
            },
            "map_authority_id": map_id,
            "controller_authority": False,
            "execution_authority": False,
            "candidate_selection_authority": False,
            "intervention": False,
            "shadow_only": True,
            "capture_device": "cuda:0",
            "capture_dtype": "state=torch.float32;selected=torch.float32",
            "capture_copy_mode": "DETACH_DEVICE_TO_CPU_CONTIGUOUS_COPY",
            "synchronization_required": True,
        }
        payload_hash = semantic_sha256({key: capture.get(key) for key in CAPTURE_SEMANTIC_KEYS})
        capture["payload_semantic_hash"] = payload_hash
        capture["payload_worker_receive_semantic_hash"] = payload_hash
        result = {
            "run_id": run_id,
            "trial_id": trial_token,
            "step_id": 0,
            "state_sequence_id": capture["state_sequence_id"],
            "decision_commit_id": capture["decision_commit_id"],
            "payload_sequence_id": 0,
            "selected_candidate_id": selected["candidate_id"],
            "candidate_group_id": capture["candidate_group_id"],
            "map_authority_id": map_id,
            "payload_enqueue_semantic_hash": payload_hash,
            "payload_worker_receive_semantic_hash": payload_hash,
            "l0_status": "PASS",
            "l0_reason": "FINITE",
            "l0_observation_source": "SHADOW_RECOMPUTED_FROZEN_CERTIFIER",
            "l1_status": "PASS",
            "l1_reason": "FINITE",
            "l1_observation_source": "SHADOW_RECOMPUTED_FROZEN_CERTIFIER",
            "l2_reached": True,
            "l2_reachability_reason": "UNKNOWN_REASON" if unknown else "CERTIFIED_SAFE",
            "l2_status": "UNKNOWN" if unknown else "PASS",
            "l2_reason": "UNKNOWN_REASON" if unknown else "CERTIFIED_SAFE",
            "backend_identity": "FIXTURE_BACKEND",
            "controller_authority": False,
            "candidate_selection_authority": False,
            "intervention": False,
            "shadow_only": True,
        }
        result["result_semantic_hash"] = semantic_sha256({key: result.get(key) for key in RESULT_SEMANTIC_KEYS})
        trace = {
            "trial_id": 10,
            "steps": [{
                "step_id": 0,
                "selected_u_k": [0.1, 0.0, 0.0],
                "selected_candidate_hash": "b" * 64,
                "selected_candidate_identity": "FROZEN_SOLVE_QP_RETURN",
                "plant_input_x": [0.0] * 6,
                "plant_input_u": [0.1, 0.0, 0.0],
                "plant_output_x_next": [0.0] * 6,
                "map_authority_id": map_id,
            }],
        }
        write_json(run_root / "primary_trace.json", trace)
        write_json(inst / "map_authority_manifest.json", {
            "map_authority_id": map_id,
            "full_map_hash_call_count_per_run": 1,
            "per_step_full_map_hash_count": 0,
            "artifacts": [{"relative_path": "map", "size": 1, "sha256": "c" * 64}],
        })
        captures = [capture, capture] if duplicate else [capture]
        write_jsonl(inst / "step_capture_log.jsonl", captures)
        write_jsonl(inst / "shadow_certificate_result_log.jsonl", [] if omit_result else [result])
        write_jsonl(inst / "instrumentation_health_log.jsonl", [
            {"event_type": "CAPTURE_RECEIPT", "status": "ENQUEUED", "payload_sequence_id": 0},
            {"event_type": "INSTRUMENTATION_HEALTH", "health": "HEALTHY", "payload_sequence_id": 0, "classified_as_l2_unknown": False},
        ])
        write_json(run_root / "arm_activation.json", {
            "shutdown_status": "SHUTDOWN_COMPLETE",
            "worker_alive_after_shutdown": False,
            "worker_exception_count": 0,
        })
        write_json(task_root / "pilot_run_manifest.json", {
            "runs": [{"run_id": run_id, "trial_id": 10, "arm": "WRAPPER_ON", "exit_code": 0, "activation_valid": True}],
        })
        return raw_root, task_root / "compact"

    def test_intended_denominator_uses_plant_trace(self) -> None:
        steps, resolved, source = intended_trace_steps({"steps": [{
            "step_id": 0, "selected_u_k": [0.1, 0.0, 0.0], "selected_candidate_hash": "a" * 64,
            "selected_candidate_identity": "FROZEN_SOLVE_QP_RETURN", "plant_input_x": [0.0] * 6,
            "plant_input_u": [0.1, 0.0, 0.0], "plant_output_x_next": [0.0] * 6, "map_authority_id": "m",
        }]})
        self.assertTrue(resolved)
        self.assertEqual(len(steps), 1)
        self.assertEqual(source, "COMMITTED_CONTROL_AND_PLANT_TRACE")

    def test_clean_aggregator_fixture_is_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            raw, compact = self.build_fixture(Path(temp))
            summary = aggregate(raw, compact)
            self.assertEqual(summary["capture_completeness"], 1.0)
            self.assertEqual(summary["join_completeness"], 1.0)
            self.assertEqual(summary["N_joinable_records"], 1)

    def test_duplicate_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            raw, compact = self.build_fixture(Path(temp), duplicate=True)
            summary = aggregate(raw, compact)
            self.assertEqual(summary["N_duplicate_payload"], 1)
            self.assertNotEqual(summary["selected_case"], "CASE_A")

    def test_orphan_or_missing_result_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            raw, compact = self.build_fixture(Path(temp), omit_result=True)
            summary = aggregate(raw, compact)
            self.assertEqual(summary["N_capture_without_result"], 1)
            self.assertEqual(summary["shadow_result_completion"], 0.0)

    def test_legal_l2_unknown_is_not_instrumentation_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            raw, compact = self.build_fixture(Path(temp), unknown=True)
            summary = aggregate(raw, compact)
            self.assertEqual(summary["L2_UNKNOWN_count"], 1)
            self.assertEqual(summary["N_schema_failure"], 0)
            self.assertEqual(summary["reachability_completeness"], 1.0)

    def test_raw_manifest_hashes_and_exclusion_label(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            raw, compact = self.build_fixture(Path(temp))
            aggregate(raw, compact)
            with (compact / "raw_artifact_manifest.csv").open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertTrue(rows)
            self.assertTrue(all(len(row["sha256"]) == 64 for row in rows))
        exclusion = json.loads((TASK / "formal_cohort_exclusion.json").read_text(encoding="utf-8"))
        self.assertEqual(exclusion["data_role"], "PILOT_QA_ONLY")
        self.assertFalse(exclusion["eligible_for_formal_prospective_cohort"])


if __name__ == "__main__":
    unittest.main()
