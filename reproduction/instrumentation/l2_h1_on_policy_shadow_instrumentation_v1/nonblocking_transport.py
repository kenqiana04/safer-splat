"""Bounded one-way transport with no result-return mechanism."""

from __future__ import annotations

import queue
from collections import deque
from typing import Callable

from immutable_payload import ImmutableStepPayload
from observer_health import CaptureReceipt, CaptureReceiptStatus


class NonblockingShadowTransport:
    def __init__(
        self,
        capacity: int,
        *,
        enabled: bool = True,
        worker_available: bool = True,
        pre_enqueue_validator: Callable[[ImmutableStepPayload], None] | None = None,
    ) -> None:
        if capacity < 1:
            raise ValueError("queue capacity must be positive")
        self._queue: queue.Queue[ImmutableStepPayload | object] = queue.Queue(maxsize=capacity)
        self._enabled = bool(enabled)
        self._worker_available = bool(worker_available)
        self._validator = pre_enqueue_validator
        self._receipts: deque[CaptureReceipt] = deque()
        self._sentinel = object()

    @property
    def queue(self) -> queue.Queue[ImmutableStepPayload | object]:
        """Worker-side queue handle; it carries payloads in one direction only."""
        return self._queue

    @property
    def sentinel(self) -> object:
        return self._sentinel

    @property
    def capacity(self) -> int:
        return self._queue.maxsize

    @property
    def receipt_records(self) -> tuple[dict, ...]:
        return tuple(receipt.to_record() for receipt in self._receipts)

    def set_worker_available(self, available: bool) -> None:
        self._worker_available = bool(available)

    def try_capture(self, payload: ImmutableStepPayload) -> CaptureReceipt:
        if not self._enabled:
            return self._record(payload, CaptureReceiptStatus.OBSERVER_DISABLED)
        if not self._worker_available:
            return self._record(payload, CaptureReceiptStatus.WORKER_UNAVAILABLE)
        try:
            if self._validator is not None:
                self._validator(payload)
        except Exception:
            return self._record(payload, CaptureReceiptStatus.SERIALIZATION_ERROR)
        try:
            self._queue.put_nowait(payload)
            return self._record(payload, CaptureReceiptStatus.ENQUEUED)
        except queue.Full:
            return self._record(payload, CaptureReceiptStatus.DROPPED_QUEUE_FULL)

    def request_shutdown_nowait(self) -> bool:
        try:
            self._queue.put_nowait(self._sentinel)
            return True
        except queue.Full:
            return False

    def _record(self, payload: ImmutableStepPayload, status: CaptureReceiptStatus) -> CaptureReceipt:
        receipt = CaptureReceipt(status, payload.payload_sequence_id, payload.decision_commit_id)
        self._receipts.append(receipt)
        return receipt
