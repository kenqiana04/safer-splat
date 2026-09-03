"""Deadline observation only; Supervisor retains deadline policy authority."""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Protocol

from .runtime_types import DeadlineObservation, DeadlineStatus, canonical_sha256


class Clock(Protocol):
    def now(self) -> float: ...


class MonotonicClock:
    def now(self) -> float:
        return time.monotonic()


class FakeClock:
    def __init__(self, value: float = 0.0) -> None:
        self._value = float(value)

    def now(self) -> float:
        return self._value

    def advance(self, delta: float) -> None:
        self._value += float(delta)


@dataclass(frozen=True)
class RuntimeDeadlineProfile:
    cycle_deadline_duration: float
    stage_budgets: tuple[tuple[str, float], ...]
    warning_reserve: float
    latest_safe_commit: float
    clock_identity: str
    identity: str

    @classmethod
    def create(cls, cycle_deadline_duration: float, stage_budgets: tuple[tuple[str, float], ...], warning_reserve: float, latest_safe_commit: float, clock_identity: str) -> "RuntimeDeadlineProfile":
        values = (float(cycle_deadline_duration), float(warning_reserve), float(latest_safe_commit))
        if not all(math.isfinite(x) and x > 0 for x in values) or latest_safe_commit > cycle_deadline_duration or warning_reserve >= latest_safe_commit or not clock_identity:
            raise ValueError("invalid explicit deadline profile")
        stages = tuple((str(name), float(budget)) for name, budget in stage_budgets)
        if any(not math.isfinite(budget) or budget <= 0 for _, budget in stages):
            raise ValueError("stage budgets must be positive and finite")
        material = {"cycle": values[0], "stages": stages, "warning": values[1], "guard": values[2], "clock": str(clock_identity)}
        return cls(values[0], stages, values[1], values[2], str(clock_identity), "deadline-profile:sha256:" + canonical_sha256(material))


class DeadlineTracker:
    def __init__(self, profile: RuntimeDeadlineProfile, clock: Clock | None = None) -> None:
        self.profile = profile
        self.clock = clock or MonotonicClock()
        self._start: float | None = None

    def start(self) -> None:
        self._start = float(self.clock.now())

    def observe(self, stage: str) -> DeadlineObservation:
        if self._start is None:
            raise RuntimeError("deadline tracker not started")
        elapsed = max(0.0, float(self.clock.now()) - self._start)
        remaining = self.profile.latest_safe_commit - elapsed
        if remaining <= 0.0:
            status = DeadlineStatus.EXPIRED
        elif remaining <= self.profile.warning_reserve:
            status = DeadlineStatus.WARNING
        else:
            status = DeadlineStatus.OPEN
        return DeadlineObservation(status, str(stage), elapsed, remaining, self.profile.identity)
