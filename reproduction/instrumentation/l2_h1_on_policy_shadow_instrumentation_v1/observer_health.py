"""Instrumentation health types, intentionally disjoint from L2 status."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class HealthStatus(str, Enum):
    HEALTHY = "HEALTHY"
    QUEUE_BACKPRESSURE = "QUEUE_BACKPRESSURE"
    SERIALIZATION_ERROR = "SERIALIZATION_ERROR"
    WORKER_EXCEPTION = "WORKER_EXCEPTION"
    WORKER_UNAVAILABLE = "WORKER_UNAVAILABLE"
    RESULT_LATE = "RESULT_LATE"
    SHUTDOWN_INCOMPLETE = "SHUTDOWN_INCOMPLETE"
    MAP_AUTHORITY_FAILURE = "MAP_AUTHORITY_FAILURE"
    PAYLOAD_ALIGNMENT_FAILURE = "PAYLOAD_ALIGNMENT_FAILURE"
    SCHEMA_VALIDATION_FAILURE = "SCHEMA_VALIDATION_FAILURE"


class CaptureReceiptStatus(str, Enum):
    ENQUEUED = "ENQUEUED"
    DROPPED_QUEUE_FULL = "DROPPED_QUEUE_FULL"
    SERIALIZATION_ERROR = "SERIALIZATION_ERROR"
    OBSERVER_DISABLED = "OBSERVER_DISABLED"
    WORKER_UNAVAILABLE = "WORKER_UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class CaptureReceipt:
    status: CaptureReceiptStatus
    payload_sequence_id: int
    decision_commit_id: str
    controller_intervention: bool = False
    contains_l2_status: bool = False

    def to_record(self) -> dict:
        return {
            "event_type": "CAPTURE_RECEIPT",
            "status": self.status.value,
            "payload_sequence_id": self.payload_sequence_id,
            "decision_commit_id": self.decision_commit_id,
            "controller_intervention": self.controller_intervention,
            "contains_l2_status": self.contains_l2_status,
        }


@dataclass(frozen=True, slots=True)
class HealthEvent:
    health: HealthStatus
    payload_sequence_id: int | None
    decision_commit_id: str | None
    detail: str
    controller_intervention: bool = False
    classified_as_l2_unknown: bool = False

    def to_record(self) -> dict:
        return {
            "event_type": "INSTRUMENTATION_HEALTH",
            "health": self.health.value,
            "payload_sequence_id": self.payload_sequence_id,
            "decision_commit_id": self.decision_commit_id,
            "detail": self.detail,
            "controller_intervention": self.controller_intervention,
            "classified_as_l2_unknown": self.classified_as_l2_unknown,
        }
