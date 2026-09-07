from __future__ import annotations

from pathlib import Path

from reproduction.runtime.active_runtime_assurance_v2.active_cycle import ActiveCycleCoordinator
from reproduction.runtime.active_runtime_assurance_v2.active_runner import ActiveRunner
from reproduction.runtime.active_runtime_assurance_v2.alternative_provider import NativeExistingAlternativeProvider
from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.backup_token_store import BackupTokenStore
from reproduction.runtime.active_runtime_assurance_v2.c0_admission import C0Admission
from reproduction.runtime.active_runtime_assurance_v2.deadline_runtime import DeadlineTracker, FakeClock, RuntimeDeadlineProfile
from reproduction.runtime.active_runtime_assurance_v2.diagnostic_r0 import DiagnosticR0
from reproduction.runtime.active_runtime_assurance_v2.l1_runtime import L1Runtime
from reproduction.runtime.active_runtime_assurance_v2.l2_runtime import L2Runtime
from reproduction.runtime.active_runtime_assurance_v2.l3_runtime import L3Runtime
from reproduction.runtime.active_runtime_assurance_v2.plant_commit import PlantCommitAdapter
from reproduction.runtime.active_runtime_assurance_v2.primary_proposal_adapter import PrimaryProposalAdapter
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActiveCycleRequest,
    ActiveTrialContext,
    CandidateRole,
    CertificateStatus,
    EvidenceResult,
    RuntimeMode,
    make_candidate,
)
from reproduction.runtime.active_runtime_assurance_v2.start_admission import StartAdmission
from reproduction.runtime.active_runtime_assurance_v2.supervisor import Supervisor, TransitionTable
from reproduction.runtime.active_runtime_assurance_v2.terminal_runtime import TerminalRuntime
from reproduction.runtime.active_runtime_assurance_v2.trace_writer import TraceWriter
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import snapshot


TRANSITION_TABLE = Path(__file__).resolve().parents[3] / "specification" / "method_logic_closure_v2" / "STATE_TRANSITION_TABLE_V2.csv"


def transition(state, control, dt):
    return tuple(state[index] + dt * (state[index + 3] if index < 3 else control[index - 3]) for index in range(6))


def build_public_cycle(config: dict | None = None):
    cfg = {
        "start": CertificateStatus.PASS,
        "l1": CertificateStatus.PASS,
        "proposal": "PASS",
        "primary_vector": (0.0, 0.0, 0.0),
        "l2": CertificateStatus.PASS,
        "l3": CertificateStatus.PASS,
        "terminal_member": False,
        "terminal": CertificateStatus.FAIL,
        "alternatives": (),
        "l1_advance": 0.0,
    }
    if config:
        cfg.update(config)
    state = snapshot()
    clock = FakeClock()
    profile = RuntimeDeadlineProfile.create(10.0, (), 1.0, 9.0, "TEST_FIXTURE_ONLY_NOT_RUNTIME_AUTHORITY")
    registry = AuthorityRegistry.frozen(state.map_identity, "dt:0.05", profile.identity)
    counters = {"l1": 0, "bind": 0, "proposal": 0, "l2": 0, "l3": 0, "alternative": 0, "terminal": 0}

    def evidence(status, reason):
        return EvidenceResult(status, reason, "evidence:" + reason.lower())

    def start_backend(*_args):
        return evidence(cfg["start"], "START_" + cfg["start"].value)

    def l1_backend(*_args):
        counters["l1"] += 1
        clock.advance(float(cfg["l1_advance"]))
        return evidence(cfg["l1"], "L1_" + cfg["l1"].value)

    def proposal_backend(_snapshot, _reference):
        counters["proposal"] += 1
        if cfg["proposal"] == "EXCEPTION":
            raise RuntimeError("proposal fixture")
        return cfg["proposal"] == "PASS", cfg["primary_vector"] if cfg["proposal"] == "PASS" else None, "PRIMARY_FIXTURE"

    def l2_backend(*_args):
        counters["l2"] += 1
        return evidence(cfg["l2"], "L2_" + cfg["l2"].value)

    def l3_backend(_snapshot, _candidate):
        counters["l3"] += 1
        status = cfg["l3"]
        return status, ((((0.0, 0.0, 0.0), "backup:0"), ((0.0, 0.0, 0.0), "backup:1")) if status == CertificateStatus.PASS else ()), "terminal:fixture", "L3_" + status.value

    def alternative_supplier(current):
        counters["alternative"] += 1
        return tuple(
            make_candidate(vector, CandidateRole.ALTERNATIVE, "SOURCE_NATIVE_EXISTING", "native-controller", current)
            for vector in cfg["alternatives"]
        )

    def terminal_backend(*_args):
        counters["terminal"] += 1
        return evidence(cfg["terminal"], "TERMINAL_" + cfg["terminal"].value)

    class CountingL1Runtime(L1Runtime):
        def bind_attempt(self, cycle_result, candidate, attempt_index):
            counters["bind"] += 1
            return super().bind_attempt(cycle_result, candidate, attempt_index)

    start_admission = StartAdmission(start_backend, registry)
    l1_runtime = CountingL1Runtime(l1_backend, registry)
    supervisor = Supervisor(registry, TransitionTable.from_csv(TRANSITION_TABLE))
    token_store = BackupTokenStore()
    trace_writer = TraceWriter(state.trial_id)
    plant = PlantCommitAdapter(registry, transition)
    runner = ActiveRunner(RuntimeMode.ACTIVE_RUNTIME_ON, registry, supervisor, plant, token_store, trace_writer, profile)
    coordinator = ActiveCycleCoordinator(
        registry,
        start_admission,
        DiagnosticR0(),
        l1_runtime,
        PrimaryProposalAdapter(proposal_backend, "controller:fixture"),
        C0Admission(registry),
        L2Runtime(l2_backend, registry),
        L3Runtime(l3_backend, registry),
        NativeExistingAlternativeProvider(alternative_supplier),
        token_store,
        TerminalRuntime(lambda _snapshot: bool(cfg["terminal_member"]), terminal_backend, registry),
        DeadlineTracker(profile, clock),
        supervisor,
        runner,
    )
    return {
        "coordinator": coordinator,
        "state": state,
        "trial": ActiveTrialContext(state.trial_id, state.map_identity),
        "request": ActiveCycleRequest(state.trial_id, 0, (1.0, 0.0, 0.0), None),
        "config": cfg,
        "counters": counters,
        "clock": clock,
        "runner": runner,
        "supervisor": supervisor,
        "token_store": token_store,
        "trace_writer": trace_writer,
        "plant": plant,
        "registry": registry,
    }


def start_and_run(system):
    start = system["coordinator"].start_trial(system["state"], system["trial"])
    result = system["coordinator"].run_cycle(system["state"], system["request"])
    return start, result
