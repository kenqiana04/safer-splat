"""Typed candidate provenance with a hard nominal-reference boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from canonical_hash import semantic_sha256


NOMINAL_REFERENCE = "NOMINAL_REFERENCE"
SELECTED_EXECUTED_CONTROL = "SELECTED_EXECUTED_CONTROL"
NATIVE_SIBLING_CONTROL = "NATIVE_SIBLING_CONTROL"


@dataclass(frozen=True, slots=True)
class CandidateSnapshot:
    candidate_id: str
    candidate_role: str
    candidate_origin: str
    u: tuple[float, float, float]
    candidate_hash: str
    created_before_observation: bool
    selected_for_execution: bool

    def semantic_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "candidate_role": self.candidate_role,
            "candidate_origin": self.candidate_origin,
            "u": self.u,
            "created_before_observation": self.created_before_observation,
            "selected_for_execution": self.selected_for_execution,
        }


def _vector3(values: Iterable[float]) -> tuple[float, float, float]:
    result = tuple(float(value) for value in values)
    if len(result) != 3:
        raise ValueError("candidate control must contain exactly three values")
    return result  # type: ignore[return-value]


def make_selected(candidate_id: str, source: str, u: Iterable[float]) -> CandidateSnapshot:
    vector = _vector3(u)
    semantic = {
        "candidate_id": candidate_id,
        "candidate_role": SELECTED_EXECUTED_CONTROL,
        "candidate_origin": source,
        "u": vector,
        "created_before_observation": True,
        "selected_for_execution": True,
    }
    return CandidateSnapshot(candidate_hash=semantic_sha256(semantic), **semantic)


def make_nominal_reference(reference_id: str, source: str, u_des: Iterable[float]) -> CandidateSnapshot:
    vector = _vector3(u_des)
    semantic = {
        "candidate_id": reference_id,
        "candidate_role": NOMINAL_REFERENCE,
        "candidate_origin": source,
        "u": vector,
        "created_before_observation": True,
        "selected_for_execution": False,
    }
    return CandidateSnapshot(candidate_hash=semantic_sha256(semantic), **semantic)


def make_native_sibling(candidate_id: str, source: str, u: Iterable[float]) -> CandidateSnapshot:
    vector = _vector3(u)
    semantic = {
        "candidate_id": candidate_id,
        "candidate_role": NATIVE_SIBLING_CONTROL,
        "candidate_origin": source,
        "u": vector,
        "created_before_observation": True,
        "selected_for_execution": False,
    }
    return CandidateSnapshot(candidate_hash=semantic_sha256(semantic), **semantic)


def validate_native_siblings(candidates: Iterable[CandidateSnapshot]) -> tuple[CandidateSnapshot, ...]:
    result = tuple(candidates)
    for candidate in result:
        if candidate.candidate_role != NATIVE_SIBLING_CONTROL:
            raise ValueError("only pre-existing native sibling controls belong to the native sibling set")
        if not candidate.created_before_observation or candidate.selected_for_execution:
            raise ValueError("native sibling provenance is inconsistent")
    return result
