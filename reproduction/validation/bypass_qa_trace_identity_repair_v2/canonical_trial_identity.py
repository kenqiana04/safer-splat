"""Single formatting authority for the refrozen BYPASS QA trial identity."""

from __future__ import annotations

from dataclasses import dataclass


FROZEN_NATIVE_TRIAL_INDICES = (10, 30, 50, 70, 90)
CANONICAL_SCHEME = "STONEHENGE_QA_TRIAL_IDENTITY_V2"
CANONICAL_FORMAT = "STONEHENGE_TRIAL_{native_trial_index:03d}"
ARM_IDENTITIES = {
    "REFERENCE_CONTROL_PLANT": "REFERENCE",
    "ACTIVE_HARNESS_BYPASS": "BYPASS",
}


@dataclass(frozen=True)
class CanonicalQATrialIdentity:
    native_trial_index: int
    canonical_trial_id: str
    scheme: str = CANONICAL_SCHEME

    def comparison_join_key(self, cycle_index: int) -> tuple[str, int]:
        cycle = int(cycle_index)
        if cycle < 0:
            raise ValueError("NEGATIVE_CYCLE_INDEX")
        return self.canonical_trial_id, cycle


def make_canonical_trial_identity(native_trial_index: int) -> CanonicalQATrialIdentity:
    """Return the only legal canonical identity for one frozen native trial."""
    index = int(native_trial_index)
    if index not in FROZEN_NATIVE_TRIAL_INDICES:
        raise ValueError("TRIAL_ID_NOT_FROZEN")
    return CanonicalQATrialIdentity(index, CANONICAL_FORMAT.format(native_trial_index=index))


def make_arm_identity(runtime_arm: str) -> str:
    """Map runtime arm names without changing the canonical trial identity."""
    try:
        return ARM_IDENTITIES[str(runtime_arm)]
    except KeyError as exc:
        raise ValueError("ARM_NOT_FROZEN") from exc
