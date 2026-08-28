from __future__ import annotations

import inspect
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from append_only_logger import AppendOnlyEvidenceLogger  # noqa: E402
from frozen_certifier_adapter import deterministic_test_adapter  # noqa: E402
from immutable_payload import build_immutable_payload  # noqa: E402
from instrumented_cbf_wrapper import InstrumentedCBFFactory, InstrumentedCBFWrapper  # noqa: E402
from lifecycle import ShadowInstrumentationLifecycle  # noqa: E402
from map_authority import MapAuthorityFreezer  # noqa: E402
from nonblocking_transport import NonblockingShadowTransport  # noqa: E402
from reachability_capture import baseline_commit_facts  # noqa: E402
from shadow_worker import ShadowWorker  # noqa: E402


def make_map(root: Path):
    (root / "map.bin").write_bytes(b"unit-map")
    return MapAuthorityFreezer().freeze(
        root=root, artifacts=["map.bin"], logical_map_name="UNIT_MAP",
        representation_contract="UNIT_ONLY", robot_radius=0.015,
        safety_margin=0.0, effective_radius=0.015, rho_seg=0.0,
    )


def make_payload(map_id: str, step: int = 0):
    return build_immutable_payload(
        run_id="unit", trial_id="trial", step_id=step, payload_sequence_id=step,
        x_k=[1, 2, 3, 0.1, 0.2, 0.3], dt=0.05,
        selected_u=[0.2, -0.1, 0.0], u_des=[0.3, -0.2, 0.1],
        selected_candidate_id=f"selected-{step}",
        selected_candidate_source="FROZEN_CBF_SOLVE_QP_SUCCESS_OUTPUT",
        map_authority_id=map_id, reachability=baseline_commit_facts(True),
    )


class DummyLifecycle:
    def __init__(self):
        self.map_manifest = SimpleNamespace(map_authority_id="map-id")
        self.payloads = []

    def try_capture(self, payload):
        self.payloads.append(payload)


class DummyCBF:
    def __init__(self, success=True):
        self.solver_success = success
        self.selected = [0.2, -0.1, 0.0]

    def solve_QP(self, x, u_des):
        return self.selected


class TransportWorkerAndWrapperTests(unittest.TestCase):
    def test_queue_full_is_immediate_drop_and_receipts_never_carry_l2(self):
        transport = NonblockingShadowTransport(1)
        first = transport.try_capture(make_payload("map", 0))
        second = transport.try_capture(make_payload("map", 1))
        self.assertEqual(first.status.value, "ENQUEUED")
        self.assertEqual(second.status.value, "DROPPED_QUEUE_FULL")
        self.assertTrue(all(not row["contains_l2_status"] for row in transport.receipt_records))

    def test_worker_logs_equal_payload_hashes_with_no_return_channel(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = make_map(root)
            logger = AppendOnlyEvidenceLogger(root / "log")
            lifecycle = ShadowInstrumentationLifecycle(
                map_manifest=manifest, logger=logger, adapter=deterministic_test_adapter(), queue_capacity=2,
            )
            lifecycle.try_capture(make_payload(manifest.map_authority_id))
            outcome = lifecycle.shutdown(1.0)
            self.assertTrue(outcome.complete)
            capture = logger.read_jsonl(logger.step_capture_path)[0]
            result = logger.read_jsonl(logger.shadow_result_path)[0]
            self.assertEqual(capture["payload_semantic_hash"], capture["payload_worker_receive_semantic_hash"])
            self.assertEqual(result["payload_enqueue_semantic_hash"], result["payload_worker_receive_semantic_hash"])
            self.assertFalse(hasattr(lifecycle.worker, "result"))
            source = inspect.getsource(ShadowWorker)
            self.assertNotIn("controller_callback", source)

    def test_shadow_exception_is_health_not_l2_unknown(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = make_map(root)
            logger = AppendOnlyEvidenceLogger(root / "log")
            lifecycle = ShadowInstrumentationLifecycle(
                map_manifest=manifest, logger=logger,
                adapter=deterministic_test_adapter(raise_in_l2=True), queue_capacity=1,
            )
            lifecycle.try_capture(make_payload(manifest.map_authority_id))
            lifecycle.shutdown(1.0)
            self.assertEqual(logger.read_jsonl(logger.shadow_result_path), [])
            health = logger.read_jsonl(logger.health_path)
            self.assertTrue(any(row.get("health") == "WORKER_EXCEPTION" for row in health))
            self.assertTrue(all(not row.get("classified_as_l2_unknown", False) for row in health))

    def test_wrapper_returns_exact_controller_object_then_captures_at_pre_plant(self):
        inner = DummyCBF(True)
        lifecycle = DummyLifecycle()
        wrapper = InstrumentedCBFWrapper(
            inner, lifecycle=lifecycle, run_id="unit", trial_id="trial", dt=0.05,
            next_payload_sequence=lambda: 0,
        )
        x = [1, 2, 3, 0.1, 0.2, 0.3]
        selected = wrapper.solve_QP(x, [0.3, -0.2, 0.1])
        self.assertIs(selected, inner.selected)
        self.assertEqual(lifecycle.payloads, [])
        wrapper.capture_committed_pre_plant(x, selected)
        self.assertEqual(len(lifecycle.payloads), 1)
        self.assertTrue(lifecycle.payloads[0].reachability.decision_committed)
        x[0] = 999
        self.assertEqual(lifecycle.payloads[0].x_k[0], 1.0)

    def test_failed_solver_is_not_captured_and_return_is_unchanged(self):
        inner = DummyCBF(False)
        lifecycle = DummyLifecycle()
        wrapper = InstrumentedCBFWrapper(
            inner, lifecycle=lifecycle, run_id="unit", trial_id="trial", dt=0.05,
            next_payload_sequence=lambda: 0,
        )
        selected = wrapper.solve_QP([1, 2, 3, 0.1, 0.2, 0.3], [0.3, -0.2, 0.1])
        self.assertIs(selected, inner.selected)
        self.assertEqual(lifecycle.payloads, [])

    def test_plant_decorator_captures_before_exact_plant_delegate(self):
        lifecycle = DummyLifecycle()
        factory = InstrumentedCBFFactory(DummyCBF, lifecycle=lifecycle, run_id="unit", dt=0.05)
        wrapped = factory(True)
        x = [1, 2, 3, 0.1, 0.2, 0.3]
        selected = wrapped.solve_QP(x, [0.3, -0.2, 0.1])
        observed_capture_counts = []

        def exact_plant(state, control):
            observed_capture_counts.append(len(lifecycle.payloads))
            return (state, control, "exact-plant")

        result = factory.decorate_plant(exact_plant)(x, selected)
        self.assertEqual(observed_capture_counts, [1])
        self.assertIs(result[0], x)
        self.assertIs(result[1], selected)
        self.assertEqual(result[2], "exact-plant")

    def test_nominal_snapshot_failure_never_changes_controller_return(self):
        inner = DummyCBF(True)
        lifecycle = DummyLifecycle()
        wrapper = InstrumentedCBFWrapper(
            inner, lifecycle=lifecycle, run_id="unit", trial_id="trial", dt=0.05,
            next_payload_sequence=lambda: 0,
        )
        selected = wrapper.solve_QP([1, 2, 3, 0.1, 0.2, 0.3], object())
        self.assertIs(selected, inner.selected)
        self.assertEqual(lifecycle.payloads, [])


if __name__ == "__main__":
    unittest.main()
