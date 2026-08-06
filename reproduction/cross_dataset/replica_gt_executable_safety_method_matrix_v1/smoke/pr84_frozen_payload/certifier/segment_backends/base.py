"""Backend protocol and geometry helpers for swept-segment certification."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from certifier.result_types import SegmentCertificate


def signed_square(value: float) -> float:
    return float(np.copysign(value * value, value))


def barrier_from_signed_distance(signed_distance: float, effective_radius: float) -> float:
    return signed_square(float(signed_distance)) - float(effective_radius) ** 2


class SegmentBackend(Protocol):
    method: str

    def certify(self, start: np.ndarray, end: np.ndarray, map_snapshot_id: str, expected_snapshot_id: str, effective_radius: float, rho_seg: float = 0.0) -> SegmentCertificate:
        ...


class SignedDistanceProvider(Protocol):
    map_snapshot_id: str

    def minimum_signed_distance(self, point: np.ndarray) -> tuple[str, float | None, int]:
        """Return status, exact minimum signed distance, evaluated primitive count."""
        ...
