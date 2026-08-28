"""Isolated one-way shadow worker. No result is returned to the controller."""

from __future__ import annotations

import queue
import threading

from append_only_logger import AppendOnlyEvidenceLogger
from canonical_hash import semantic_sha256
from frozen_certifier_adapter import ReadOnlyFrozenCertifierAdapter
from immutable_payload import ImmutableStepPayload
from observer_health import HealthEvent, HealthStatus


class ShadowWorker(threading.Thread):
    def __init__(
        self,
        *,
        inbound: queue.Queue[ImmutableStepPayload | object],
        sentinel: object,
        adapter: ReadOnlyFrozenCertifierAdapter,
        logger: AppendOnlyEvidenceLogger,
        crash_before_process: bool = False,
    ) -> None:
        super().__init__(name="l2-h1-shadow-worker-v1", daemon=True)
        self._inbound = inbound
        self._sentinel = sentinel
        self._adapter = adapter
        self._logger = logger
        self._crash_before_process = crash_before_process
        self._processed_count = 0
        self._worker_exception_count = 0

    @property
    def processed_count(self) -> int:
        return self._processed_count

    @property
    def worker_exception_count(self) -> int:
        return self._worker_exception_count

    def run(self) -> None:
        if self._crash_before_process:
            self._worker_exception_count += 1
            self._logger.append_health(
                HealthEvent(HealthStatus.WORKER_EXCEPTION, None, None, "TASK_LOCAL_INJECTED_WORKER_CRASH").to_record()
            )
            return
        while True:
            item = self._inbound.get()
            try:
                if item is self._sentinel:
                    return
                if not isinstance(item, ImmutableStepPayload):
                    raise TypeError("SCHEMA_VALIDATION_FAILURE")
                receive_hash = semantic_sha256(item.semantic_dict())
                if receive_hash != item.semantic_hash:
                    raise ValueError("PAYLOAD_ALIGNMENT_FAILURE")
                capture = item.capture_record()
                capture["payload_worker_receive_semantic_hash"] = receive_hash
                self._logger.append_capture(capture)
                result = self._adapter.evaluate(item).to_record()
                result.update(
                    {
                        "run_id": item.run_id,
                        "trial_id": item.trial_id,
                        "step_id": item.step_id,
                        "state_sequence_id": item.state_sequence_id,
                        "decision_commit_id": item.decision_commit_id,
                        "payload_sequence_id": item.payload_sequence_id,
                        "selected_candidate_id": item.selected_candidate.candidate_id,
                        "candidate_group_id": item.candidate_group_id,
                        "map_authority_id": item.map_authority_id,
                        "payload_enqueue_semantic_hash": item.semantic_hash,
                        "payload_worker_receive_semantic_hash": receive_hash,
                    }
                )
                self._logger.append_result(result)
                self._logger.append_health(
                    HealthEvent(HealthStatus.HEALTHY, item.payload_sequence_id, item.decision_commit_id, "SHADOW_RESULT_APPENDED").to_record()
                )
                self._processed_count += 1
            except Exception as exc:
                self._worker_exception_count += 1
                payload_sequence_id = getattr(item, "payload_sequence_id", None)
                decision_commit_id = getattr(item, "decision_commit_id", None)
                status = HealthStatus.PAYLOAD_ALIGNMENT_FAILURE if "PAYLOAD_ALIGNMENT" in str(exc) else HealthStatus.WORKER_EXCEPTION
                self._logger.append_health(
                    HealthEvent(status, payload_sequence_id, decision_commit_id, f"{type(exc).__name__}:{exc}").to_record()
                )
            finally:
                self._inbound.task_done()
