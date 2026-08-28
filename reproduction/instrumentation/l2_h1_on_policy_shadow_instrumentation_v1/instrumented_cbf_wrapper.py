"""Protected-source wrapper seam for successful CBF decisions.

This module never reimplements `solve_QP`; it delegates to the exact frozen
instance, observes the completed success flag, snapshots evidence, and returns
the exact selected object/value unchanged.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Callable, Iterable

from candidate_provenance import CandidateSnapshot
from immutable_payload import build_immutable_payload, snapshot_vector
from lifecycle import ShadowInstrumentationLifecycle
from observer_health import HealthEvent, HealthStatus
from reachability_capture import baseline_commit_facts


@dataclass(slots=True)
class _PendingDecision:
    step_id: int
    x_identity: int
    selected_u_identity: int
    u_des_snapshot: tuple[float, ...]


class InstrumentedCBFWrapper:
    def __init__(
        self,
        inner,
        *,
        lifecycle: ShadowInstrumentationLifecycle,
        run_id: str,
        trial_id: str,
        dt: float,
        next_payload_sequence: Callable[[], int],
        native_sibling_supplier: Callable[[object, object, object], Iterable[CandidateSnapshot]] | None = None,
        error_sink: Callable[[HealthEvent], None] | None = None,
    ) -> None:
        self._inner = inner
        self._lifecycle = lifecycle
        self._run_id = str(run_id)
        self._trial_id = str(trial_id)
        self._dt = float(dt)
        self._next_payload_sequence = next_payload_sequence
        self._native_sibling_supplier = native_sibling_supplier
        self._error_sink = error_sink
        self._step_id = 0
        self._pending: _PendingDecision | None = None

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def solve_QP(self, x_k, u_des):
        selected_u = self._inner.solve_QP(x_k, u_des)
        solver_success = bool(getattr(self._inner, "solver_success", False))
        step_id = self._step_id
        self._step_id += 1
        if solver_success:
            try:
                nominal, _, _, _, _ = snapshot_vector(u_des, 3)
                self._pending = _PendingDecision(step_id, id(x_k), id(selected_u), nominal)
            except Exception as exc:
                self._pending = None
                if self._error_sink is not None:
                    self._error_sink(
                        HealthEvent(
                            HealthStatus.SERIALIZATION_ERROR,
                            None,
                            f"{self._run_id}:{self._trial_id}:commit:{step_id:06d}",
                            f"{type(exc).__name__}:{exc}",
                        )
                    )
        else:
            self._pending = None
        return selected_u

    def capture_committed_pre_plant(self, x_k, selected_u) -> None:
        """Capture only after the protected caller has passed its success guard.

        The outer decorator invokes this at entry to the exact frozen plant
        function and before delegating that function. Live references exist
        only synchronously until this method creates the immutable snapshot;
        no mutable object enters the async queue.
        """
        pending = self._pending
        self._pending = None
        if pending is None:
            return
        try:
            if id(x_k) != pending.x_identity or id(selected_u) != pending.selected_u_identity:
                raise ValueError("STATE_ACTION_ALIGNMENT_FAILURE")
            sequence = self._next_payload_sequence()
            siblings = () if self._native_sibling_supplier is None else tuple(
                self._native_sibling_supplier(self._inner, x_k, selected_u)
            )
            payload = build_immutable_payload(
                run_id=self._run_id,
                trial_id=self._trial_id,
                step_id=pending.step_id,
                payload_sequence_id=sequence,
                x_k=x_k,
                dt=self._dt,
                selected_u=selected_u,
                u_des=pending.u_des_snapshot,
                selected_candidate_id=f"{self._run_id}:{self._trial_id}:selected:{pending.step_id:06d}",
                selected_candidate_source="FROZEN_CBF_SOLVE_QP_SUCCESS_OUTPUT",
                map_authority_id=self._lifecycle.map_manifest.map_authority_id,
                reachability=baseline_commit_facts(True),
                native_siblings=siblings,
            )
            self._lifecycle.try_capture(payload)
        except Exception as exc:
            if self._error_sink is not None:
                self._error_sink(
                    HealthEvent(
                        HealthStatus.SERIALIZATION_ERROR,
                        None,
                        f"{self._run_id}:{self._trial_id}:commit:{pending.step_id:06d}",
                        f"{type(exc).__name__}:{exc}",
                    )
                )


class InstrumentedCBFFactory:
    """Drop-in factory used by the outer `runpy` decorator."""

    def __init__(
        self,
        original_cbf_class,
        *,
        lifecycle: ShadowInstrumentationLifecycle,
        run_id: str,
        dt: float,
        native_sibling_supplier=None,
    ) -> None:
        self._original = original_cbf_class
        self._lifecycle = lifecycle
        self._run_id = str(run_id)
        self._dt = float(dt)
        self._trial_counter = 0
        self._payload_counter = 0
        self._native_sibling_supplier = native_sibling_supplier
        self._errors: deque[HealthEvent] = deque()
        self._active_wrapper: InstrumentedCBFWrapper | None = None

    def __call__(self, *args, **kwargs) -> InstrumentedCBFWrapper:
        inner = self._original(*args, **kwargs)
        trial_id = f"trial-{self._trial_counter:06d}"
        self._trial_counter += 1
        wrapper = InstrumentedCBFWrapper(
            inner,
            lifecycle=self._lifecycle,
            run_id=self._run_id,
            trial_id=trial_id,
            dt=self._dt,
            next_payload_sequence=self._next_sequence,
            native_sibling_supplier=self._native_sibling_supplier,
            error_sink=self._errors.append,
        )
        self._active_wrapper = wrapper
        return wrapper

    def capture_committed_pre_plant(self, x_k, selected_u) -> None:
        if self._active_wrapper is not None:
            self._active_wrapper.capture_committed_pre_plant(x_k, selected_u)

    def decorate_plant(self, original_plant):
        def post_guard_pre_plant(x_k, selected_u, *args, **kwargs):
            self.capture_committed_pre_plant(x_k, selected_u)
            return original_plant(x_k, selected_u, *args, **kwargs)

        return post_guard_pre_plant

    def _next_sequence(self) -> int:
        value = self._payload_counter
        self._payload_counter += 1
        return value

    def flush_capture_errors(self) -> None:
        while self._errors:
            self._lifecycle.logger.append_health(self._errors.popleft().to_record())

    @property
    def approved_instrumentation_hook_count(self) -> int:
        return 1
