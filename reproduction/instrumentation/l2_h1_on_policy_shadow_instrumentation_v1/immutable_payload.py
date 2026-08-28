"""Immutable same-decision payload snapshots for asynchronous handoff."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any, Iterable

from canonical_hash import semantic_sha256
from candidate_provenance import (
    CandidateSnapshot,
    make_nominal_reference,
    make_selected,
    validate_native_siblings,
)
from reachability_capture import ReachabilityFacts


SCHEMA_VERSION = "L2_H1_ON_POLICY_SHADOW_STEP_PAYLOAD_V1"


def _device_name(value: Any) -> str:
    device = getattr(value, "device", None)
    return "python_cpu" if device is None else str(device)


def _dtype_name(value: Any) -> str:
    dtype = getattr(value, "dtype", None)
    return type(value).__name__ if dtype is None else str(dtype)


def _materialize(value: Any) -> tuple[float, ...]:
    snapshot = value
    if hasattr(snapshot, "detach"):
        snapshot = snapshot.detach()
    if hasattr(snapshot, "to") and getattr(snapshot, "device", None) is not None:
        snapshot = snapshot.to("cpu")
    elif hasattr(snapshot, "cpu"):
        snapshot = snapshot.cpu()
    if hasattr(snapshot, "contiguous"):
        snapshot = snapshot.contiguous()
    if hasattr(snapshot, "numpy"):
        snapshot = snapshot.numpy()
    if hasattr(snapshot, "copy"):
        snapshot = snapshot.copy()
    if hasattr(snapshot, "tolist"):
        snapshot = snapshot.tolist()
    result = tuple(float(item) for item in snapshot)
    if not all(math.isfinite(item) for item in result):
        raise ValueError("payload vectors must be finite")
    return result


def snapshot_vector(value: Any, expected_length: int) -> tuple[tuple[float, ...], str, str, str, bool]:
    device = _device_name(value)
    dtype = _dtype_name(value)
    vector = _materialize(value)
    if len(vector) != expected_length:
        raise ValueError(f"expected vector length {expected_length}, got {len(vector)}")
    cuda = device.startswith("cuda")
    copy_mode = "DETACH_DEVICE_TO_CPU_CONTIGUOUS_COPY" if cuda else "INDEPENDENT_CPU_COPY"
    return vector, device, dtype, copy_mode, cuda


@dataclass(frozen=True, slots=True)
class ImmutableStepPayload:
    schema_version: str
    run_id: str
    trial_id: str
    step_id: int
    state_sequence_id: str
    decision_commit_id: str
    payload_sequence_id: int
    x_k: tuple[float, ...]
    p_k: tuple[float, float, float]
    v_k: tuple[float, float, float]
    dt: float
    selected_candidate: CandidateSnapshot
    nominal_reference: CandidateSnapshot
    native_sibling_candidates: tuple[CandidateSnapshot, ...]
    candidate_group_id: str
    native_candidate_group_size: int
    reachability: ReachabilityFacts
    map_authority_id: str
    capture_device: str
    capture_dtype: str
    capture_copy_mode: str
    synchronization_required: bool
    controller_authority: bool
    execution_authority: bool
    candidate_selection_authority: bool
    intervention: bool
    shadow_only: bool
    semantic_hash: str

    def semantic_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "run_id": self.run_id,
            "trial_id": self.trial_id,
            "step_id": self.step_id,
            "state_sequence_id": self.state_sequence_id,
            "decision_commit_id": self.decision_commit_id,
            "x_k": self.x_k,
            "p_k": self.p_k,
            "v_k": self.v_k,
            "dt": self.dt,
            "selected_candidate": self.selected_candidate.semantic_dict(),
            "native_sibling_candidates": tuple(item.semantic_dict() for item in self.native_sibling_candidates),
            "candidate_group_id": self.candidate_group_id,
            "native_candidate_group_size": self.native_candidate_group_size,
            "reachability": self.reachability.semantic_dict(),
            "map_authority_id": self.map_authority_id,
            "controller_authority": self.controller_authority,
            "execution_authority": self.execution_authority,
            "candidate_selection_authority": self.candidate_selection_authority,
            "intervention": self.intervention,
            "shadow_only": self.shadow_only,
        }

    def capture_record(self) -> dict:
        record = self.semantic_dict()
        record.update(
            {
                "payload_sequence_id": self.payload_sequence_id,
                "nominal_reference": self.nominal_reference.semantic_dict(),
                "capture_device": self.capture_device,
                "capture_dtype": self.capture_dtype,
                "capture_copy_mode": self.capture_copy_mode,
                "synchronization_required": self.synchronization_required,
                "payload_semantic_hash": self.semantic_hash,
            }
        )
        return record


def build_immutable_payload(
    *,
    run_id: str,
    trial_id: str,
    step_id: int,
    payload_sequence_id: int,
    x_k: Any,
    dt: float,
    selected_u: Any,
    u_des: Any,
    selected_candidate_id: str,
    selected_candidate_source: str,
    map_authority_id: str,
    reachability: ReachabilityFacts,
    native_siblings: Iterable[CandidateSnapshot] = (),
) -> ImmutableStepPayload:
    state, state_device, state_dtype, state_copy, state_sync = snapshot_vector(x_k, 6)
    selected, selected_device, selected_dtype, selected_copy, selected_sync = snapshot_vector(selected_u, 3)
    nominal, _, _, _, nominal_sync = snapshot_vector(u_des, 3)
    if not math.isfinite(float(dt)) or float(dt) <= 0:
        raise ValueError("dt must be positive and finite")
    siblings = validate_native_siblings(native_siblings)
    decision_commit_id = f"{run_id}:{trial_id}:commit:{step_id:06d}"
    candidate_group_id = f"{decision_commit_id}:native-group"
    payload = ImmutableStepPayload(
        schema_version=SCHEMA_VERSION,
        run_id=str(run_id),
        trial_id=str(trial_id),
        step_id=int(step_id),
        state_sequence_id=f"{run_id}:{trial_id}:state:{step_id:06d}",
        decision_commit_id=decision_commit_id,
        payload_sequence_id=int(payload_sequence_id),
        x_k=state,
        p_k=state[:3],  # type: ignore[arg-type]
        v_k=state[3:],  # type: ignore[arg-type]
        dt=float(dt),
        selected_candidate=make_selected(selected_candidate_id, selected_candidate_source, selected),
        nominal_reference=make_nominal_reference(f"{decision_commit_id}:u_des", "FROZEN_PD_NOMINAL_REFERENCE", nominal),
        native_sibling_candidates=siblings,
        candidate_group_id=candidate_group_id,
        native_candidate_group_size=1 + len(siblings),
        reachability=reachability,
        map_authority_id=str(map_authority_id),
        capture_device=state_device if state_device != "python_cpu" else selected_device,
        capture_dtype=f"state={state_dtype};selected={selected_dtype}",
        capture_copy_mode=state_copy if state_copy != "INDEPENDENT_CPU_COPY" else selected_copy,
        synchronization_required=bool(state_sync or selected_sync or nominal_sync),
        controller_authority=False,
        execution_authority=False,
        candidate_selection_authority=False,
        intervention=False,
        shadow_only=True,
        semantic_hash="",
    )
    return replace(payload, semantic_hash=semantic_sha256(payload.semantic_dict()))
