"""Additive V3 stack rewiring for certification/execution state identity."""

from __future__ import annotations

import inspect
from pathlib import Path
import sys
from typing import Any, Mapping

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    CertificateStatus,
    EvidenceResult,
    RuntimeStateSnapshot,
    canonical_sha256,
)
from reproduction.runtime.active_runtime_assurance_v2.terminal_runtime import TerminalRuntime
from reproduction.runtime.v3_hard_radius_runtime_wiring_v1 import build_v3_stack_from_frozen_v2

from .canonical_transition import CanonicalExecutionTransition
from .evidence import CanonicalEvidenceTraceWriter, CanonicalIdentityLedger
from .repaired_components import (
    CanonicalBackupTokenStore,
    CanonicalL1Runtime,
    CanonicalL2Runtime,
    CanonicalL3Runtime,
    CanonicalPositionFirstForwardEulerDoubleIntegrator,
    CanonicalStartAdmission,
    CanonicalWitnessMaterial,
    ContinuityGuardedPlantCommitAdapter,
)


def _unwrap(module: Any) -> Any:
    return getattr(module, "_module", module)


def _replace_wrapped_module(wrapper: Any, replacement: Any) -> Any:
    if hasattr(wrapper, "_module"):
        wrapper._module = replacement
        return wrapper
    return replacement


def _closure(function: Any, name: str) -> Any:
    values = inspect.getclosurevars(function).nonlocals
    if name not in values:
        raise RuntimeError(f"REPAIR_WIRING_CLOSURE_MISSING:{name}")
    return values[name]


def validate_repaired_stack_wiring(stack: Mapping[str, Any]) -> dict[str, Any]:
    coordinator = stack["coordinator"]
    canonical = stack["canonical_transition"]
    l1 = _unwrap(coordinator.l1_runtime)
    l2 = _unwrap(coordinator.l2_runtime)
    l3 = _unwrap(coordinator.l3_runtime)
    token_store = getattr(stack["tokens"], "_store", stack["tokens"])
    terminal = _unwrap(coordinator.terminal_runtime)
    checks = {
        "canonical_transition_is_shared_by_l1": l1._transition is canonical,
        "canonical_transition_is_shared_by_l2": l2._transition is canonical,
        "canonical_transition_is_shared_by_l3": l3._transition is canonical,
        "canonical_transition_is_shared_by_token_store": token_store._transition is canonical,
        "canonical_transition_is_plant_arithmetic": stack["plant"].canonical_transition is canonical,
        "canonical_trace_writer_installed": stack["trace"].schema_identity == "EVALUATION_TRACE_SCHEMA_V2_CERT_EXEC_IDENTITY_V1",
        "terminal_runtime_policy_class_unchanged": isinstance(terminal, TerminalRuntime),
        "geometry_hard_radius_q": stack["registry"].geometry.certification_effective_radius_m == 0.015,
        "geometry_margin_q": stack["registry"].geometry.certification_margin_m == 0.0,
        "geometry_rho_seg_q": stack["registry"].geometry.rho_seg_m == 0.0,
        "historical_0p025_runtime_authority": stack["v3_geometry_policy"].historical_diagnostic_runtime_authority is False,
        "supervisor_identity_preserved": coordinator.supervisor is coordinator.active_runner.supervisor,
        "controller_adapter_preserved": coordinator.primary_proposal is stack["frozen_primary_proposal"],
        "dynamics_mathematical_identity_preserved": stack["registry"].dynamics.model == "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1",
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise RuntimeError("REPAIRED_STACK_WIRING_INVALID:" + ",".join(failed))
    return {
        "schema": "CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIRED_STACK_WIRING_AUDIT_V1",
        "status": "PASS",
        "canonical_transition_identity": canonical.identity.value,
        "canonical_dtype": canonical.identity.dtype,
        "canonical_device_backend": canonical.identity.device_backend,
        "canonical_op_order": canonical.identity.operation_order,
        "hard_radius_q": 0.015,
        "runtime_margin_q": 0.0,
        "rho_seg_q": 0.0,
        "historical_diagnostic_radius_q": 0.025,
        "historical_diagnostic_runtime_authority": False,
        "checks": checks,
    }


def build_repaired_v3_stack(
    checkout: Path,
    output_dir: Path,
    trial_id: int,
    base_config: Mapping[str, Any],
    map_identity: str,
) -> dict[str, Any]:
    """Build frozen V3 then replace only numerical-prediction components."""

    root = Path(checkout).resolve(strict=True)
    sys.path[:0] = [str(root / "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1"), str(root)]
    stack = build_v3_stack_from_frozen_v2(root, output_dir, int(trial_id), base_config, str(map_identity))
    coordinator = stack["coordinator"]
    registry = stack["registry"]

    old_l1 = _unwrap(coordinator.l1_runtime)
    old_l3 = _unwrap(coordinator.l3_runtime)
    old_terminal_runtime = _unwrap(coordinator.terminal_runtime)
    old_backup_certifier = _closure(old_l3._builder, "backup_certifier")
    segment_backend = _closure(old_l1._backend, "segment_backend")
    plant_device = _closure(stack["plant"]._transition, "device")

    canonical = CanonicalExecutionTransition(plant_device)
    ledger = CanonicalIdentityLedger()
    l1 = CanonicalL1Runtime(old_l1._backend, registry, canonical, ledger)
    l2 = CanonicalL2Runtime(_unwrap(coordinator.l2_runtime)._backend, registry, canonical, ledger)

    from certifier.backup_certifier import BackupCertifier
    from certifier.result_types import Control, SegmentStatus, State
    from certifier.segment_certificate import SweptSegmentCertifier
    from certifier.terminal_certificate import TerminalCertifier

    repaired_dynamics = CanonicalPositionFirstForwardEulerDoubleIntegrator(old_backup_certifier.dynamics.bounds, canonical)
    repaired_swept = SweptSegmentCertifier(
        repaired_dynamics,
        segment_backend,
        registry.geometry.certification_effective_radius_m,
        registry.geometry.rho_seg_m,
    )
    repaired_terminal_certifier = TerminalCertifier(
        old_backup_certifier.terminal_certifier.terminal_set,
        old_backup_certifier.terminal_certifier.current_adapter,
        repaired_swept,
    )
    repaired_backup_certifier = BackupCertifier(
        repaired_dynamics,
        repaired_swept,
        repaired_terminal_certifier,
        old_backup_certifier.braking_policy,
    )

    def to_certifier_state(snapshot: RuntimeStateSnapshot) -> Any:
        return State(tuple(snapshot.position), tuple(snapshot.velocity), snapshot.cycle_index * snapshot.dt, snapshot.map_identity)

    def witness_builder(snapshot: RuntimeStateSnapshot, candidate: Any) -> CanonicalWitnessMaterial:
        state = to_certifier_state(snapshot)
        control = Control(tuple(candidate.vector), candidate.provenance.source_type, candidate.identity.value)
        witness = repaired_backup_certifier.certify(state, control, snapshot.map_identity, None)
        if not witness.certified:
            return CanonicalWitnessMaterial(CertificateStatus.FAIL, (), None, witness.reason_code, tuple((*item.position, *item.velocity) for item in witness.states), ())
        tail = tuple((item.acceleration, f"{candidate.identity.value}:backup:{index}:{item.candidate_id}") for index, item in enumerate(witness.backup_controls))
        terminal_ref = "terminal-evidence:sha256:" + canonical_sha256(witness.terminal_certificate.to_dict())
        predicted = tuple((*item.position, *item.velocity) for item in witness.states)
        segment_ids = tuple(
            "canonical-certified-segment:sha256:" + canonical_sha256({"index": index, "certificate": certificate.to_dict(), "transition": canonical.identity.value})
            for index, certificate in enumerate(witness.per_segment_certificates)
        )
        return CanonicalWitnessMaterial(CertificateStatus.PASS, tail, terminal_ref, witness.reason_code, predicted, segment_ids)

    l3 = CanonicalL3Runtime(witness_builder, registry, canonical, ledger)

    def terminal_backend(snapshot: RuntimeStateSnapshot, expected_map: str, radius: float) -> EvidenceResult:
        if radius != registry.geometry.certification_effective_radius_m or expected_map != registry.map_identity:
            return EvidenceResult(CertificateStatus.UNKNOWN, "TERMINAL_AUTHORITY_MISMATCH", "none")
        certificate = repaired_terminal_certifier.certify(to_certifier_state(snapshot), expected_map)
        status = CertificateStatus.PASS if certificate.certified else CertificateStatus.FAIL
        evidence_identity = "terminal-evidence:sha256:" + canonical_sha256(certificate.to_dict())
        ledger.record(
            snapshot.trial_id,
            snapshot.cycle_index,
            canonical_terminal_transition_identity=canonical.identity.value,
            canonical_terminal_status=status.value,
            canonical_terminal_evidence_identity=evidence_identity,
        )
        return EvidenceResult(status, certificate.reason_code, evidence_identity)

    terminal = TerminalRuntime(old_terminal_runtime._membership, terminal_backend, registry)
    start = CanonicalStartAdmission(coordinator.start_admission, canonical, ledger)

    observed_tokens = stack["tokens"]
    if not hasattr(observed_tokens, "_store"):
        raise RuntimeError("REPAIRED_STACK_OBSERVED_TOKEN_STORE_REQUIRED")
    repaired_token_store = CanonicalBackupTokenStore(canonical, ledger)
    observed_tokens._store = repaired_token_store

    old_trace = stack["trace"]
    repaired_trace = CanonicalEvidenceTraceWriter(old_trace.trial_id, old_trace.output_directory, ledger)
    repaired_plant = ContinuityGuardedPlantCommitAdapter(registry, canonical, ledger)
    runner = coordinator.active_runner
    runner.plant_commit = repaired_plant
    runner.trace_writer = repaired_trace
    runner._active_commit_transaction.plant_commit = repaired_plant
    runner._active_commit_transaction.trace_writer = repaired_trace

    stack["frozen_primary_proposal"] = coordinator.primary_proposal
    coordinator.start_admission = start
    coordinator.l1_runtime = _replace_wrapped_module(coordinator.l1_runtime, l1)
    coordinator.l2_runtime = _replace_wrapped_module(coordinator.l2_runtime, l2)
    coordinator.l3_runtime = _replace_wrapped_module(coordinator.l3_runtime, l3)
    coordinator.terminal_runtime = _replace_wrapped_module(coordinator.terminal_runtime, terminal)

    stack.update({
        "plant": repaired_plant,
        "trace": repaired_trace,
        "canonical_transition": canonical,
        "canonical_identity_ledger": ledger,
        "canonical_dynamics": repaired_dynamics,
        "canonical_swept_certifier": repaired_swept,
        "canonical_terminal_certifier": repaired_terminal_certifier,
        "canonical_backup_certifier": repaired_backup_certifier,
    })
    stack["repaired_stack_wiring_audit"] = validate_repaired_stack_wiring(stack)
    return stack
