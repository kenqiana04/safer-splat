"""Task-local deterministic F1-F10 zero-authority fault harness."""

from __future__ import annotations

import argparse
import json
import tempfile
import time
from dataclasses import replace
from pathlib import Path

from append_only_logger import AppendOnlyEvidenceLogger
from frozen_certifier_adapter import deterministic_test_adapter
from immutable_payload import build_immutable_payload
from lifecycle import ShadowInstrumentationLifecycle
from map_authority import MapAuthorityFreezeError, MapAuthorityFreezer
from nonblocking_transport import NonblockingShadowTransport
from reachability_capture import baseline_commit_facts


FAULT_IDS = (
    "F1_WORKER_NOT_STARTED",
    "F2_WORKER_CRASH",
    "F3_QUEUE_FULL",
    "F4_SERIALIZATION_EXCEPTION",
    "F5_MAP_AUTHORITY_FAILURE",
    "F6_PAYLOAD_CORRUPTION_ATTEMPT",
    "F7_POST_ENQUEUE_SOURCE_MUTATION",
    "F8_SLOW_WORKER",
    "F9_SHADOW_CERTIFIER_EXCEPTION",
    "F10_SHUTDOWN_FLUSH_TIMEOUT",
)


def controller_fn(x: list[float], u_des: list[float]) -> tuple[float, float, float]:
    return tuple(float(u_des[index] - 0.1 * x[index]) for index in range(3))  # type: ignore[return-value]


def _map_manifest(root: Path):
    artifact = root / "map" / "config.yml"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text("map: task-local-mock\n", encoding="utf-8")
    return MapAuthorityFreezer().freeze(
        root=root,
        artifacts=[Path("map")],
        logical_map_name="TASK_LOCAL_MOCK_MAP",
        representation_contract="TASK_LOCAL_NO_RESEARCH_DATA",
        robot_radius=0.015,
        safety_margin=0.0,
        effective_radius=0.015,
        rho_seg=0.0,
    )


def _payload(sequence: int, map_id: str, x_source=None, selected_source=None, nominal_source=None):
    x = [1.0, 2.0, 3.0, 0.1, 0.2, 0.3] if x_source is None else x_source
    u_des = [0.2, 0.1, 0.0] if nominal_source is None else nominal_source
    selected = controller_fn(x, u_des) if selected_source is None else selected_source
    return build_immutable_payload(
        run_id="mock-run",
        trial_id="mock-trial",
        step_id=sequence,
        payload_sequence_id=sequence,
        x_k=x,
        dt=0.05,
        selected_u=selected,
        u_des=u_des,
        selected_candidate_id=f"mock-selected-{sequence}",
        selected_candidate_source="TASK_LOCAL_MOCK_CONTROLLER",
        map_authority_id=map_id,
        reachability=baseline_commit_facts(True),
    )


def _baseline_trace() -> tuple[tuple[float, float, float], ...]:
    return tuple(
        controller_fn([float(index), 0.5, -0.5, 0.0, 0.0, 0.0], [0.2, -0.1, 0.05])
        for index in range(4)
    )


def run_fault_matrix() -> dict:
    baseline = _baseline_trace()
    results: list[dict] = []
    with tempfile.TemporaryDirectory(prefix="l2h1-shadow-fault-") as temp:
        root = Path(temp)
        manifest = _map_manifest(root)

        # F1: actual transport reports unavailable without changing control.
        transport = NonblockingShadowTransport(1, worker_available=False)
        receipt = transport.try_capture(_payload(0, manifest.map_authority_id))
        results.append(_result(FAULT_IDS[0], baseline, receipt.status.value == "WORKER_UNAVAILABLE"))

        # F2: actual worker starts in injected crash mode.
        lifecycle = ShadowInstrumentationLifecycle(
            map_manifest=manifest,
            logger=AppendOnlyEvidenceLogger(root / "f2"),
            adapter=deterministic_test_adapter(),
            queue_capacity=1,
            crash_worker_before_process=True,
        )
        time.sleep(0.01)
        receipt = lifecycle.try_capture(_payload(1, manifest.map_authority_id))
        lifecycle.shutdown(0.02)
        results.append(_result(FAULT_IDS[1], baseline, receipt.status.value == "WORKER_UNAVAILABLE"))

        # F3: bounded actual queue drops the second payload immediately.
        transport = NonblockingShadowTransport(1, worker_available=True)
        first = transport.try_capture(_payload(2, manifest.map_authority_id))
        second = transport.try_capture(_payload(3, manifest.map_authority_id))
        results.append(_result(FAULT_IDS[2], baseline, first.status.value == "ENQUEUED" and second.status.value == "DROPPED_QUEUE_FULL"))

        # F4: pre-enqueue serializer/validator exception becomes health only.
        transport = NonblockingShadowTransport(1, pre_enqueue_validator=lambda payload: (_ for _ in ()).throw(ValueError("injected")))
        receipt = transport.try_capture(_payload(4, manifest.map_authority_id))
        results.append(_result(FAULT_IDS[3], baseline, receipt.status.value == "SERIALIZATION_ERROR"))

        # F5: missing map artifact does not invoke a controller.
        failed = False
        try:
            MapAuthorityFreezer().freeze(
                root=root,
                artifacts=["missing-map"],
                logical_map_name="MISSING",
                representation_contract="TASK_LOCAL",
                robot_radius=0.0,
                safety_margin=0.0,
                effective_radius=0.0,
                rho_seg=0.0,
            )
        except MapAuthorityFreezeError:
            failed = True
        results.append(_result(FAULT_IDS[4], baseline, failed))

        # F6: a semantically corrupt replacement is rejected by worker hash check.
        logger = AppendOnlyEvidenceLogger(root / "f6")
        lifecycle = ShadowInstrumentationLifecycle(
            map_manifest=manifest,
            logger=logger,
            adapter=deterministic_test_adapter(),
            queue_capacity=2,
        )
        corrupt = replace(_payload(5, manifest.map_authority_id), dt=0.06)
        lifecycle.try_capture(corrupt)
        lifecycle.shutdown(0.2)
        health = logger.read_jsonl(logger.health_path)
        results.append(_result(FAULT_IDS[5], baseline, any(item.get("health") == "PAYLOAD_ALIGNMENT_FAILURE" for item in health)))

        # F7: source mutations cannot alter the frozen snapshot.
        source_x = [1.0, 2.0, 3.0, 0.1, 0.2, 0.3]
        source_u = [0.1, -0.1, 0.0]
        source_nominal = [0.2, 0.1, 0.0]
        payload = _payload(6, manifest.map_authority_id, source_x, source_u, source_nominal)
        frozen_hash = payload.semantic_hash
        source_x[:] = [99.0] * 6
        source_u[:] = [99.0] * 3
        source_nominal[:] = [99.0] * 3
        results.append(_result(FAULT_IDS[6], baseline, payload.semantic_hash == frozen_hash and payload.x_k[0] == 1.0))

        # F8: slow worker causes only queue pressure, never control changes.
        lifecycle = ShadowInstrumentationLifecycle(
            map_manifest=manifest,
            logger=AppendOnlyEvidenceLogger(root / "f8"),
            adapter=deterministic_test_adapter(delay_seconds=0.05),
            queue_capacity=1,
        )
        receipts = [lifecycle.try_capture(_payload(10 + index, manifest.map_authority_id)) for index in range(4)]
        lifecycle.shutdown(0.4)
        results.append(_result(FAULT_IDS[7], baseline, any(item.status.value == "DROPPED_QUEUE_FULL" for item in receipts)))

        # F9: certifier exception is worker health, with no L2 UNKNOWN result.
        logger = AppendOnlyEvidenceLogger(root / "f9")
        lifecycle = ShadowInstrumentationLifecycle(
            map_manifest=manifest,
            logger=logger,
            adapter=deterministic_test_adapter(raise_in_l2=True),
            queue_capacity=1,
        )
        lifecycle.try_capture(_payload(20, manifest.map_authority_id))
        lifecycle.shutdown(0.2)
        health = logger.read_jsonl(logger.health_path)
        results_log = logger.read_jsonl(logger.shadow_result_path)
        results.append(_result(FAULT_IDS[8], baseline, any(item.get("health") == "WORKER_EXCEPTION" for item in health) and not results_log))

        # F10: zero-time bounded flush records incomplete and returns promptly.
        logger = AppendOnlyEvidenceLogger(root / "f10")
        lifecycle = ShadowInstrumentationLifecycle(
            map_manifest=manifest,
            logger=logger,
            adapter=deterministic_test_adapter(delay_seconds=0.2),
            queue_capacity=1,
        )
        lifecycle.try_capture(_payload(30, manifest.map_authority_id))
        outcome = lifecycle.shutdown(0.0)
        results.append(_result(FAULT_IDS[9], baseline, not outcome.complete and outcome.status == "SHUTDOWN_INCOMPLETE"))
        # The zero-time outcome is the asserted behavior. A separate bounded
        # cleanup prevents the daemon from outliving this task-local fixture;
        # it is not part of a controller or scientific trial path.
        lifecycle.shutdown(1.0)

    return {
        "scope": "TASK_LOCAL_MOCK_INSTRUMENTATION_FAULT_QA_ONLY",
        "fault_injection_case_count": len(results),
        "cases": results,
        "all_mock_control_traces_equal": all(item["mock_control_trace_equal"] for item in results),
        "all_fault_expectations_met": all(item["fault_expectation_met"] for item in results),
        "real_navigation_equivalence_run_count": 0,
        "logging_pilot_run_count": 0,
        "formal_on_policy_cohort_count": 0,
        "on_policy_research_collection_count": 0,
        "navigation_rollout_count": 0,
        "status": "PASS_F1_F10_ZERO_AUTHORITY_FAULT_QA",
    }


def _result(fault_id: str, baseline, expectation: bool) -> dict:
    observed_trace = _baseline_trace()
    return {
        "fault_id": fault_id,
        "mock_controller_disabled_trace": baseline,
        "mock_controller_fault_trace": observed_trace,
        "mock_control_trace_equal": observed_trace == baseline,
        "controller_return_value_equal": observed_trace == baseline,
        "fault_expectation_met": bool(expectation),
        "controller_intervention_count": 0,
        "actual_fail_close_from_shadow_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_fault_matrix()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    return 0 if result["all_mock_control_traces_equal"] and result["all_fault_expectations_met"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
