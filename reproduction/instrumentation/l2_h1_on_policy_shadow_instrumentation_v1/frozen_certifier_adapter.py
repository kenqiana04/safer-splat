"""Read-only worker adapter for frozen L0/L1/L2 observation callables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from canonical_hash import semantic_sha256
from immutable_payload import ImmutableStepPayload
from reachability_capture import SHADOW_RECOMPUTED_FROZEN_CERTIFIER


L2_STATUSES = frozenset({"PASS", "FAIL", "UNKNOWN"})


@dataclass(frozen=True, slots=True)
class ShadowObservationResult:
    l0_status: str
    l0_reason: str
    l0_observation_source: str
    l1_status: str
    l1_reason: str
    l1_observation_source: str
    l2_reached: bool
    l2_reachability_reason: str
    l2_status: str
    l2_reason: str
    backend_identity: str
    result_semantic_hash: str

    def to_record(self) -> dict:
        return {
            "l0_status": self.l0_status,
            "l0_reason": self.l0_reason,
            "l0_observation_source": self.l0_observation_source,
            "l1_status": self.l1_status,
            "l1_reason": self.l1_reason,
            "l1_observation_source": self.l1_observation_source,
            "l2_reached": self.l2_reached,
            "l2_reachability_reason": self.l2_reachability_reason,
            "l2_status": self.l2_status,
            "l2_reason": self.l2_reason,
            "backend_identity": self.backend_identity,
            "result_semantic_hash": self.result_semantic_hash,
            "controller_authority": False,
            "candidate_selection_authority": False,
            "intervention": False,
            "shadow_only": True,
        }


class ReadOnlyFrozenCertifierAdapter:
    """Dependency-injected adapter executed only by the shadow worker.

    Each callable accepts an immutable payload and returns a new dictionary.
    The adapter verifies that payload semantics are unchanged across all calls.
    """

    def __init__(
        self,
        l0_certifier: Callable[[ImmutableStepPayload], dict],
        l1_certifier: Callable[[ImmutableStepPayload], dict],
        l2_certifier: Callable[[ImmutableStepPayload], dict],
        *,
        backend_identity: str,
    ) -> None:
        self._l0 = l0_certifier
        self._l1 = l1_certifier
        self._l2 = l2_certifier
        self.backend_identity = str(backend_identity)

    def evaluate(self, payload: ImmutableStepPayload) -> ShadowObservationResult:
        before = semantic_sha256(payload.semantic_dict())
        if before != payload.semantic_hash:
            raise ValueError("PAYLOAD_ALIGNMENT_FAILURE")
        l0 = dict(self._l0(payload))
        if l0.get("status") not in {"PASS", "FAIL", "UNKNOWN"}:
            raise ValueError("INVALID_L0_STATUS")
        if l0["status"] != "PASS":
            l1 = {"status": "NOT_REACHED", "reason": "L0_BLOCKED"}
            l2 = {"status": "NOT_REACHED", "reason": "L0_BLOCKED", "reached": False}
        else:
            l1 = dict(self._l1(payload))
            if l1.get("status") not in {"PASS", "FAIL", "UNKNOWN"}:
                raise ValueError("INVALID_L1_STATUS")
            if l1["status"] != "PASS":
                reason = "L1_FAIL" if l1["status"] == "FAIL" else "L1_UNKNOWN"
                l2 = {"status": "NOT_REACHED", "reason": reason, "reached": False}
            else:
                l2 = dict(self._l2(payload))
                if l2.get("status") not in L2_STATUSES:
                    raise ValueError("INVALID_L2_STATUS")
                l2["reached"] = True
        after = semantic_sha256(payload.semantic_dict())
        if after != before:
            raise RuntimeError("CERTIFIER_MUTATED_IMMUTABLE_PAYLOAD")
        semantic = {
            "l0_status": l0["status"],
            "l0_reason": str(l0.get("reason", l0["status"])),
            "l0_observation_source": SHADOW_RECOMPUTED_FROZEN_CERTIFIER,
            "l1_status": l1["status"],
            "l1_reason": str(l1.get("reason", l1["status"])),
            "l1_observation_source": SHADOW_RECOMPUTED_FROZEN_CERTIFIER,
            "l2_reached": bool(l2.get("reached", False)),
            "l2_reachability_reason": str(l2.get("reason", "SELECTED_CANDIDATE_AVAILABLE")),
            "l2_status": str(l2["status"]),
            "l2_reason": str(l2.get("reason", l2["status"])),
            "backend_identity": self.backend_identity,
        }
        return ShadowObservationResult(result_semantic_hash=semantic_sha256(semantic), **semantic)


def deterministic_test_adapter(
    *,
    delay_seconds: float = 0.0,
    raise_in_l2: bool = False,
) -> ReadOnlyFrozenCertifierAdapter:
    """Pure deterministic adapter for task-local structural QA, not research."""

    import time

    def l0(payload: ImmutableStepPayload) -> dict:
        return {"status": "PASS", "reason": "TASK_LOCAL_MOCK_L0_PASS"}

    def l1(payload: ImmutableStepPayload) -> dict:
        return {"status": "PASS", "reason": "TASK_LOCAL_MOCK_L1_PASS"}

    def l2(payload: ImmutableStepPayload) -> dict:
        if delay_seconds:
            time.sleep(delay_seconds)
        if raise_in_l2:
            raise RuntimeError("TASK_LOCAL_INJECTED_CERTIFIER_EXCEPTION")
        return {"status": "PASS", "reason": "TASK_LOCAL_MOCK_L2_PASS"}

    return ReadOnlyFrozenCertifierAdapter(l0, l1, l2, backend_identity="TASK_LOCAL_PURE_MOCK_ADAPTER")
