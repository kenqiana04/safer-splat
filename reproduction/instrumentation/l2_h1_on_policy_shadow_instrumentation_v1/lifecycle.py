"""Run-level map/log/transport/worker lifecycle with bounded shutdown."""

from __future__ import annotations

import time
from dataclasses import dataclass

from append_only_logger import AppendOnlyEvidenceLogger
from frozen_certifier_adapter import ReadOnlyFrozenCertifierAdapter
from immutable_payload import ImmutableStepPayload
from map_authority import MapAuthorityManifest
from nonblocking_transport import NonblockingShadowTransport
from observer_health import CaptureReceipt, HealthEvent, HealthStatus
from shadow_worker import ShadowWorker


@dataclass(frozen=True, slots=True)
class ShutdownOutcome:
    complete: bool
    status: str
    processed_count: int
    worker_exception_count: int


class ShadowInstrumentationLifecycle:
    def __init__(
        self,
        *,
        map_manifest: MapAuthorityManifest,
        logger: AppendOnlyEvidenceLogger,
        adapter: ReadOnlyFrozenCertifierAdapter,
        queue_capacity: int,
        enabled: bool = True,
        start_worker: bool = True,
        crash_worker_before_process: bool = False,
        pre_enqueue_validator=None,
    ) -> None:
        self.map_manifest = map_manifest
        self.logger = logger
        self.transport = NonblockingShadowTransport(
            queue_capacity,
            enabled=enabled,
            worker_available=start_worker,
            pre_enqueue_validator=pre_enqueue_validator,
        )
        self.worker = ShadowWorker(
            inbound=self.transport.queue,
            sentinel=self.transport.sentinel,
            adapter=adapter,
            logger=logger,
            crash_before_process=crash_worker_before_process,
        )
        self.logger.write_map_manifest_once(map_manifest.to_record())
        if start_worker:
            self.worker.start()

    def try_capture(self, payload: ImmutableStepPayload) -> CaptureReceipt:
        if self.worker.ident is not None and not self.worker.is_alive():
            self.transport.set_worker_available(False)
        return self.transport.try_capture(payload)

    def shutdown(self, timeout_seconds: float) -> ShutdownOutcome:
        deadline = time.monotonic() + max(float(timeout_seconds), 0.0)
        while time.monotonic() <= deadline and not self.transport.request_shutdown_nowait():
            time.sleep(min(0.001, max(0.0, deadline - time.monotonic())))
        remaining = max(0.0, deadline - time.monotonic())
        if self.worker.ident is not None:
            self.worker.join(timeout=remaining)
        complete = self.worker.ident is None or not self.worker.is_alive()
        for receipt in self.transport.receipt_records:
            self.logger.append_health(receipt)
        status = "SHUTDOWN_COMPLETE" if complete else HealthStatus.SHUTDOWN_INCOMPLETE.value
        if not complete:
            self.logger.append_health(
                HealthEvent(HealthStatus.SHUTDOWN_INCOMPLETE, None, None, "BOUNDED_FLUSH_TIMEOUT").to_record()
            )
        return ShutdownOutcome(complete, status, self.worker.processed_count, self.worker.worker_exception_count)
