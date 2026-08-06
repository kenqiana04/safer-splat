"""B3 tuple construction only; accepted slots retain frozen identifiers and order."""
from __future__ import annotations

from alternative_library.result_types import CandidateSet
from methods.b2_primary_and_braking_wrapper import CandidateSpec, CertifierCallSpec


def b3_call_spec(primary: CandidateSpec, candidate_set: CandidateSet) -> CertifierCallSpec:
    if primary.candidate_id != "PRIMARY-CBF-FILTERED":
        raise ValueError("B3_PRIMARY_PARITY_REQUIRED")
    directional = tuple(CandidateSpec(slot.candidate_id, slot.source, slot.acceleration) for slot in candidate_set.available_slots)
    return CertifierCallSpec(primary, directional)


def b3_ordered_candidate_roles(primary: CandidateSpec, candidate_set: CandidateSet) -> tuple[str, ...]:
    call = b3_call_spec(primary, candidate_set)
    return (call.nominal_control.candidate_id, *(item.candidate_id for item in call.external_alternative_controls), call.builtin_braking_role)
