from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.backup_token_store import BackupTokenStore
from reproduction.runtime.active_runtime_assurance_v2.deadline_runtime import FakeClock, RuntimeDeadlineProfile
from reproduction.runtime.active_runtime_assurance_v2.plant_commit import PlantCommitAdapter
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole,
    CertificateStatus,
    EvidenceResult,
    RuntimeMode,
    RuntimeStateSnapshot,
    make_action,
    make_candidate,
    CandidateRole,
)
from reproduction.runtime.active_runtime_assurance_v2.supervisor import Supervisor
from reproduction.runtime.active_runtime_assurance_v2.trace_writer import TraceWriter
from reproduction.runtime.active_runtime_assurance_v2.active_runner import ActiveRunner


MAP_ID = "map:cpu-conformance"


def snapshot(cycle: int = 0, state=(0.0, 0.0, 0.0, 0.1, 0.0, 0.0)):
    return RuntimeStateSnapshot.create("cpu-conformance", cycle, state, (1.0, 0.0, 0.0, 0.0, 0.0, 0.0), MAP_ID, 0.05)


def registry(profile_id: str | None = "deadline:test"):
    return AuthorityRegistry.frozen(MAP_ID, "dt:0.05", profile_id)


def profile():
    return RuntimeDeadlineProfile.create(1.0, (("L1", 0.1), ("L2", 0.1)), 0.1, 0.9, "fake-clock")


def transition(state, control, dt):
    return tuple(state[i] + dt * (state[i + 3] if i < 3 else control[i - 3]) for i in range(6))


def runner(mode=RuntimeMode.ACTIVE_RUNTIME_ON, with_profile=True):
    snap = snapshot()
    reg = registry(None if not with_profile else profile().identity)
    return ActiveRunner(mode, reg, Supervisor(reg), PlantCommitAdapter(reg, transition), BackupTokenStore(), TraceWriter("cpu-conformance"), profile() if with_profile else None)


def candidate(snap=None, vector=(0.01, 0.0, 0.0), role=CandidateRole.PRIMARY, source="PRIMARY_NATIVE_CBF_QP"):
    return make_candidate(vector, role, source, "controller:cpu", snap or snapshot())


def evidence(status=CertificateStatus.PASS, reason="CPU_FIXTURE", identity="evidence:cpu"):
    return EvidenceResult(status, reason, identity)


def action(role=ActionRole.PRIMARY_NAVIGATION, vector=(0.01, 0.0, 0.0), source="cpu"):
    return make_action(vector, role, source)
