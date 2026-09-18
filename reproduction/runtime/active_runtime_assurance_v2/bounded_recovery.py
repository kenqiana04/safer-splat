"""Gate 0 F1 proposal source and trial-local search-suppression facts.

No geometry query, controller selection, PlantCommit, or scientific outcome code.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass, replace
from enum import Enum

from .authority_registry import AuthorityRegistry
from .runtime_types import (
    Candidate, CandidateIdentity, CandidateProvenance, CandidateRole,
    RuntimeStateSnapshot, canonical_sha256,
)


SOURCE = "SOURCE_BOUNDED_LOCAL_RECOVERY_V1"
GENERATOR = "AXIS_EXTREMA_F32_V1"
DIRECTIONS = ("+x", "-x", "+y", "-y", "+z", "-z")


def has_gate0_geometry(registry: AuthorityRegistry) -> bool:
    """Check the already-frozen V3 hard geometry; never project or tune it."""
    geometry = registry.geometry
    return (geometry.certification_effective_radius_m == 0.015 and
            geometry.certification_margin_m == 0.0 and geometry.rho_seg_m == 0.0)


def _f32_bits(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("RECOVERY_NONFINITE_SCALAR")
    return struct.pack("!f", 0.0 if value == 0.0 else float(value)).hex()


def numeric_bits_identity(values: tuple[float, ...]) -> str:
    return "f32bits:sha256:" + canonical_sha256(tuple(_f32_bits(v) for v in values))


def canonical_control_identity(vector: tuple[float, float, float], actuator_identity: str, transition_identity: str) -> str:
    if len(vector) != 3 or not actuator_identity or not transition_identity:
        raise ValueError("RECOVERY_CONTROL_IDENTITY_INCOMPLETE")
    return "control-f32:sha256:" + canonical_sha256({
        "dimension": 3, "bits": tuple(_f32_bits(v) for v in vector),
        "actuator": actuator_identity, "transition": transition_identity,
    })


@dataclass(frozen=True)
class RecoverySourceGrant:
    identity: str
    trial_id: str
    cycle_index: int
    state_identity: str
    map_identity: str
    actuator_identity: str
    transition_identity: str
    source: str = SOURCE
    generator_version: str = GENERATOR

    @classmethod
    def create(cls, snapshot: RuntimeStateSnapshot, actuator_identity: str, transition_identity: str) -> "RecoverySourceGrant":
        if not actuator_identity or not transition_identity:
            raise ValueError("RECOVERY_AUTHORITY_IDENTITY_MISSING")
        material = (snapshot.trial_id, snapshot.cycle_index, snapshot.identity.value,
                    snapshot.map_identity, actuator_identity, transition_identity, SOURCE, GENERATOR)
        return cls("recovery-grant:sha256:" + canonical_sha256(material), snapshot.trial_id,
                   snapshot.cycle_index, snapshot.identity.value, snapshot.map_identity,
                   actuator_identity, transition_identity)

    def matches(self, snapshot: RuntimeStateSnapshot, registry: AuthorityRegistry) -> bool:
        return (self.source == SOURCE and self.generator_version == GENERATOR and
                self.trial_id == snapshot.trial_id and self.cycle_index == snapshot.cycle_index and
                self.state_identity == snapshot.identity.value and self.map_identity == snapshot.map_identity == registry.map_identity and
                self.actuator_identity == registry.actuator.identity.value and
                self.identity == self.create(snapshot, self.actuator_identity, self.transition_identity).identity)


@dataclass(frozen=True)
class RecoveryCandidate:
    candidate: Candidate
    generation_rank: int
    direction: str
    canonical_control_identity: str


@dataclass(frozen=True)
class RecoveryInventory:
    status: str
    candidates: tuple[RecoveryCandidate, ...]
    skipped_duplicate_ranks: tuple[int, ...]


class BoundedRecoveryProvider:
    def __init__(self, registry: AuthorityRegistry, transition_identity: str, backend_identity: str) -> None:
        if not transition_identity or not backend_identity:
            raise ValueError("RECOVERY_AUTHORITY_IDENTITY_MISSING")
        self.registry = registry
        self.transition_identity = str(transition_identity)
        self.backend_identity = str(backend_identity)

    def enumerate(self, snapshot: RuntimeStateSnapshot, grant: RecoverySourceGrant,
                  primary: Candidate | None = None) -> RecoveryInventory:
        if not grant.matches(snapshot, self.registry) or grant.transition_identity != self.transition_identity:
            return RecoveryInventory("RECOVERY_SOURCE_UNAUTHORIZED", (), ())
        low, high = self.registry.actuator.u_min, self.registry.actuator.u_max
        if len(low) != 3 or len(high) != 3 or any(not (math.isfinite(lo) and math.isfinite(hi) and lo < 0.0 < hi)
                                                  for lo, hi in zip(low, high)):
            return RecoveryInventory("RECOVERY_SOURCE_AUTHORITY_UNSUPPORTED", (), ())
        raw = ((high[0], 0.0, 0.0), (low[0], 0.0, 0.0),
               (0.0, high[1], 0.0), (0.0, low[1], 0.0),
               (0.0, 0.0, high[2]), (0.0, 0.0, low[2]))
        seen = set()
        if primary is not None:
            if primary.provenance.state_identity != snapshot.identity or primary.provenance.map_identity != snapshot.map_identity:
                return RecoveryInventory("RECOVERY_IDENTITY_MISMATCH", (), ())
            seen.add(canonical_control_identity(primary.vector, grant.actuator_identity, grant.transition_identity))
        out: list[RecoveryCandidate] = []
        skipped: list[int] = []
        for rank, vector in enumerate(raw):
            control_id = canonical_control_identity(vector, grant.actuator_identity, grant.transition_identity)
            if control_id in seen or all(_f32_bits(v) == _f32_bits(0.0) for v in vector):
                skipped.append(rank)
                continue
            seen.add(control_id)
            provenance = CandidateProvenance(SOURCE, grant.identity,
                                             f"logical-cycle:{snapshot.cycle_index}:recovery-rank:{rank}:generator:{GENERATOR}",
                                             snapshot.identity, snapshot.map_identity, True)
            material = {"vector": vector, "role": CandidateRole.ALTERNATIVE, "provenance": provenance}
            candidate = Candidate(CandidateIdentity("candidate:sha256:" + canonical_sha256(material)),
                                  vector, CandidateRole.ALTERNATIVE, provenance)
            out.append(RecoveryCandidate(candidate, rank, DIRECTIONS[rank], control_id))
        assert len(out) <= 6
        return RecoveryInventory("RECOVERY_AVAILABLE" if out else "RECOVERY_SCAN_EXHAUSTED", tuple(out), tuple(skipped))


def exhaustion_key(snapshot: RuntimeStateSnapshot, *, actuator_identity: str, geometry_identity: str,
                   transition_identity: str, backend_identity: str, backup_routing_class: str) -> str:
    if backup_routing_class not in {"NONE", "INVALID", "EXHAUSTED"}:
        raise ValueError("RECOVERY_BACKUP_CLASS_NOT_ELIGIBLE")
    if not all((actuator_identity, geometry_identity, transition_identity, backend_identity, snapshot.map_identity)):
        raise ValueError("RECOVERY_EXHAUSTION_IDENTITY_UNKNOWN")
    material = {"numeric_state": numeric_bits_identity(snapshot.state),
                "goal": numeric_bits_identity(snapshot.goal), "dt": _f32_bits(snapshot.dt),
                "map": snapshot.map_identity, "source": SOURCE, "generator": GENERATOR,
                "actuator": actuator_identity, "geometry": geometry_identity,
                "transition": transition_identity, "backend": backend_identity,
                "backup_routing_class": backup_routing_class}
    return "recovery-key:sha256:" + canonical_sha256(material)


class ScanStatus(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    EXHAUSTED = "EXHAUSTED"
    SELECTED = "SELECTED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class RecoveryScanRecord:
    trial_id: str
    key: str
    scan_id: str
    status: ScanStatus
    cursor: int = 0
    tried_control_ids: tuple[str, ...] = ()
    selected_candidate_id: str | None = None
    terminal_disposition: str | None = None


class RecoveryExhaustionRegister:
    """Owned by one trial coordinator; never grants execution authority."""

    def __init__(self) -> None:
        self._trial_id: str | None = None
        self._records: dict[str, RecoveryScanRecord] = {}

    def start_trial(self, trial_id: str) -> None:
        if self._trial_id is not None:
            raise RuntimeError("RECOVERY_REGISTER_TRIAL_ALREADY_STARTED")
        self._trial_id = str(trial_id)
        self._records = {}

    def finalize_trial(self) -> None:
        self._trial_id = None
        self._records = {}

    def lookup(self, trial_id: str, key: str) -> RecoveryScanRecord | None:
        if self._trial_id != trial_id:
            raise RuntimeError("RECOVERY_REGISTER_TRIAL_MISMATCH")
        return self._records.get(key)

    def begin(self, trial_id: str, key: str) -> RecoveryScanRecord:
        old = self.lookup(trial_id, key)
        if old is not None:
            if old.status != ScanStatus.PAUSED:
                raise RuntimeError("RECOVERY_KEY_NOT_RESCANNABLE")
            new = replace(old, status=ScanStatus.ACTIVE)
        else:
            new = RecoveryScanRecord(trial_id, key,
                                     "recovery-scan:sha256:" + canonical_sha256((trial_id, key)),
                                     ScanStatus.ACTIVE)
        self._records[key] = new
        return new

    def attempted(self, trial_id: str, key: str, rank: int, control_id: str) -> RecoveryScanRecord:
        old = self.lookup(trial_id, key)
        if old is None or old.status != ScanStatus.ACTIVE or rank < old.cursor or control_id in old.tried_control_ids:
            raise RuntimeError("RECOVERY_ATTEMPT_RETRY_OR_ORDER_VIOLATION")
        new = replace(old, cursor=rank + 1, tried_control_ids=old.tried_control_ids + (control_id,))
        self._records[key] = new
        return new

    def close(self, trial_id: str, key: str, status: ScanStatus,
              selected_candidate_id: str | None = None, terminal_disposition: str | None = None) -> RecoveryScanRecord:
        old = self.lookup(trial_id, key)
        if old is None or old.status != ScanStatus.ACTIVE or status not in {ScanStatus.PAUSED, ScanStatus.EXHAUSTED, ScanStatus.SELECTED, ScanStatus.BLOCKED}:
            raise RuntimeError("RECOVERY_SCAN_LIFECYCLE_VIOLATION")
        if status == ScanStatus.SELECTED and not selected_candidate_id:
            raise RuntimeError("RECOVERY_SELECTED_ID_MISSING")
        new = replace(old, status=status, selected_candidate_id=selected_candidate_id,
                      terminal_disposition=terminal_disposition)
        self._records[key] = new
        return new
