"""B2 call construction only; PR #84 adds braking internally, never as an external alternative."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    source: str
    acceleration: tuple[float, float, float]


@dataclass(frozen=True)
class CertifierCallSpec:
    nominal_control: CandidateSpec
    external_alternative_controls: tuple[CandidateSpec, ...]
    builtin_braking_role: str = "DETERMINISTIC_BRAKING"


def b2_call_spec(primary: CandidateSpec) -> CertifierCallSpec:
    if primary.candidate_id != "PRIMARY-CBF-FILTERED":
        raise ValueError("B2_FIXED_PRIMARY_IDENTITY_REQUIRED")
    return CertifierCallSpec(primary, ())


def b2_ordered_candidate_roles(primary: CandidateSpec) -> tuple[str, str]:
    return primary.candidate_id, b2_call_spec(primary).builtin_braking_role
