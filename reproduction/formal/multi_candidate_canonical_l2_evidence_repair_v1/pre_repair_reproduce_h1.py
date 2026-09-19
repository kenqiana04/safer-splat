#!/usr/bin/env python3
"""Deterministic CPU-only reproduction of the pre-repair flat L2 collision."""
from __future__ import annotations

import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    Candidate,
    CandidateIdentity,
    CandidateProvenance,
    CandidateRole,
    CertificateStatus,
    EvidenceResult,
    RuntimeStateSnapshot,
    canonical_sha256,
    make_candidate,
)
from reproduction.runtime.certification_execution_state_identity_repair_v1.canonical_transition import CanonicalExecutionTransition
from reproduction.runtime.certification_execution_state_identity_repair_v1.evidence import CanonicalIdentityLedger
from reproduction.runtime.certification_execution_state_identity_repair_v1.repaired_components import CanonicalL2Runtime
from reproduction.runtime.v3_hard_radius_runtime_wiring_v1.stack_factory import make_v3_authority_registry


def backend(start, end, map_identity, radius, rho):
    identity = "evidence:sha256:" + canonical_sha256({"start": start, "end": end, "map": map_identity, "radius": radius, "rho": rho})
    return EvidenceResult(CertificateStatus.PASS, "CPU_SYNTHETIC_PASS", identity)


def main() -> int:
    registry = make_v3_authority_registry("map", "dt", "deadline")
    transition = CanonicalExecutionTransition("cpu", backend_label="CPU_SYNTHETIC_H1_REPRODUCTION")
    ledger = CanonicalIdentityLedger()
    runtime = CanonicalL2Runtime(backend, registry, transition, ledger)
    snapshot = RuntimeStateSnapshot.create("H1_TRIAL", 17, (0.1, -0.2, 0.3, 0.01, -0.02, 0.03), (0.0,) * 6, "map", 0.05)
    primary = make_candidate((0.02, -0.03, 0.04), CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "controller", snapshot)
    provenance = CandidateProvenance("SOURCE_BOUNDED_LOCAL_RECOVERY_V1", "recovery-grant:synthetic",
                                     "logical-cycle:17:recovery-rank:0", snapshot.identity, snapshot.map_identity, True)
    material = {"vector": (0.1, 0.0, 0.0), "role": CandidateRole.ALTERNATIVE, "provenance": provenance}
    recovery = Candidate(CandidateIdentity("candidate:sha256:" + canonical_sha256(material)),
                         (0.1, 0.0, 0.0), CandidateRole.ALTERNATIVE, provenance)
    first = runtime.evaluate(snapshot, primary)
    output = {"status": "H1_NOT_CONFIRMED", "first_status": first.status.value,
              "exception_type": None, "exception_message": None, "colliding_key": None,
              "first_candidate_identity": primary.identity.value,
              "second_candidate_identity": recovery.identity.value,
              "trial_id": snapshot.trial_id, "cycle_index": snapshot.cycle_index,
              "gpu_used": False}
    try:
        runtime.evaluate(snapshot, recovery)
    except RuntimeError as exc:
        message = str(exc)
        output.update({"status": "H1_CONFIRMED_FLAT_CANONICAL_L2_COLLISION",
                       "exception_type": type(exc).__name__, "exception_message": message,
                       "colliding_key": message.split(":", 1)[1] if message.startswith("CANONICAL_EVIDENCE_REWRITE_FORBIDDEN:") else None})
    target = Path(__file__).resolve().parent / "results_cpu_validation/pre_repair_h1_reproduction.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(output, sort_keys=True))
    return 0 if output["status"] == "H1_CONFIRMED_FLAT_CANONICAL_L2_COLLISION" else 2


if __name__ == "__main__":
    raise SystemExit(main())
