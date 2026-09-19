#!/usr/bin/env python3
"""CPU-only T02-T09 validation for candidate-scoped canonical L2 evidence."""
from __future__ import annotations

import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole, Candidate, CandidateIdentity, CandidateProvenance, CandidateRole,
    CertificateStatus, EvidenceResult, RuntimeStateSnapshot, TraceStepRecord,
    canonical_sha256, make_candidate,
)
from reproduction.runtime.certification_execution_state_identity_repair_v1.canonical_transition import CanonicalExecutionTransition
from reproduction.runtime.certification_execution_state_identity_repair_v1.evidence import CanonicalEvidenceTraceWriter, CanonicalIdentityLedger
from reproduction.runtime.certification_execution_state_identity_repair_v1.repaired_components import CanonicalL2Runtime
from reproduction.runtime.v3_hard_radius_runtime_wiring_v1.stack_factory import make_v3_authority_registry

TASK = Path(__file__).resolve().parent
NAMESPACE = "canonical_l2_candidate_evidence"
FLAT_KEYS = (
    "canonical_l2_x_k1_identity", "canonical_l2_p_k1_identity",
    "canonical_l2_x_k2_identity", "canonical_l2_p_k2_identity",
    "canonical_l2_segment_identity", "canonical_l2_status",
    "canonical_l2_reason", "canonical_l2_evidence_identity",
    "canonical_selected_candidate_identity",
)


def backend(start, end, map_identity, radius, rho):
    identity = "evidence:sha256:" + canonical_sha256({"start": start, "end": end, "map": map_identity,
                                                        "radius": radius, "rho": rho})
    return EvidenceResult(CertificateStatus.PASS, "CPU_SYNTHETIC_PASS", identity)


class MultiCandidateL2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = make_v3_authority_registry("map", "dt", "deadline")
        self.transition = CanonicalExecutionTransition("cpu", backend_label="CPU_MULTI_CANDIDATE_L2_VALIDATION")
        self.snapshot = RuntimeStateSnapshot.create("MULTI", 9,
            (0.1, -0.2, 0.3, 0.01, -0.02, 0.03), (0.0,) * 6, "map", 0.05)
        self.primary = make_candidate((0.02, -0.03, 0.04), CandidateRole.PRIMARY,
                                      "PRIMARY_NATIVE_CBF_QP", "controller", self.snapshot)
        self.vectors = ((0.1, 0.0, 0.0), (-0.1, 0.0, 0.0), (0.0, 0.1, 0.0),
                        (0.0, -0.1, 0.0), (0.0, 0.0, 0.1), (0.0, 0.0, -0.1))
        self.recovery = tuple(self._alternative(vector, "SOURCE_BOUNDED_LOCAL_RECOVERY_V1", rank)
                              for rank, vector in enumerate(self.vectors))

    def _alternative(self, vector, source, rank):
        provenance = CandidateProvenance(source, "grant:" + source,
            f"logical-cycle:9:rank:{rank}", self.snapshot.identity, self.snapshot.map_identity, True)
        material = {"vector": vector, "role": CandidateRole.ALTERNATIVE, "provenance": provenance}
        return Candidate(CandidateIdentity("candidate:sha256:" + canonical_sha256(material)),
                         vector, CandidateRole.ALTERNATIVE, provenance)

    def _runtime(self):
        ledger = CanonicalIdentityLedger()
        return CanonicalL2Runtime(backend, self.registry, self.transition, ledger), ledger

    @staticmethod
    def _facts(ledger):
        return dict(ledger.facts("MULTI", 9))

    def test_t02_single_primary_legacy_compatibility(self):
        runtime, ledger = self._runtime()
        result = runtime.evaluate(self.snapshot, self.primary)
        facts = self._facts(ledger)
        self.assertEqual(result.status, CertificateStatus.PASS)
        self.assertTrue(all(key in facts for key in FLAT_KEYS))
        self.assertEqual(facts["canonical_selected_candidate_identity"], self.primary.identity.value)
        self.assertEqual(len(dict(facts[NAMESPACE])), 1)

    def test_t03_primary_plus_recovery_coexist(self):
        runtime, ledger = self._runtime()
        runtime.evaluate(self.snapshot, self.primary)
        before = {key: self._facts(ledger)[key] for key in FLAT_KEYS}
        result = runtime.evaluate(self.snapshot, self.recovery[0])
        facts = self._facts(ledger)
        self.assertEqual(result.status, CertificateStatus.PASS)
        self.assertEqual({key: facts[key] for key in FLAT_KEYS}, before)
        self.assertEqual(set(dict(facts[NAMESPACE])), {self.primary.identity.value, self.recovery[0].identity.value})

    def test_t04_primary_plus_all_six_and_deterministic_scope_order(self):
        runtime, ledger = self._runtime()
        results = [runtime.evaluate(self.snapshot, self.primary)]
        primary_flat = None
        primary_flat = {key: self._facts(ledger)[key] for key in FLAT_KEYS}
        results.extend(runtime.evaluate(self.snapshot, candidate) for candidate in self.recovery)
        facts = self._facts(ledger)
        scopes = facts[NAMESPACE]
        self.assertEqual([item.status for item in results], [CertificateStatus.PASS] * 7)
        self.assertEqual(len(scopes), 7)
        self.assertEqual([scope for scope, _ in scopes], sorted(scope for scope, _ in scopes))
        self.assertEqual({key: facts[key] for key in FLAT_KEYS}, primary_flat)

    def test_t05_same_scope_conflicting_rewrite_rejected(self):
        ledger = CanonicalIdentityLedger()
        ledger.record_scoped("MULTI", 9, NAMESPACE, "candidate:a", status="PASS")
        with self.assertRaisesRegex(RuntimeError,
                "CANONICAL_SCOPED_EVIDENCE_REWRITE_FORBIDDEN:canonical_l2_candidate_evidence:candidate:a"):
            ledger.record_scoped("MULTI", 9, NAMESPACE, "candidate:a", status="FAIL")

    def test_t06_identical_same_scope_is_idempotent(self):
        ledger = CanonicalIdentityLedger()
        ledger.record_scoped("MULTI", 9, NAMESPACE, "candidate:a", status="PASS", reason="same")
        before = ledger.facts("MULTI", 9)
        ledger.record_scoped("MULTI", 9, NAMESPACE, "candidate:a", reason="same", status="PASS")
        self.assertEqual(ledger.facts("MULTI", 9), before)

    def test_t07_role_and_source_distinction(self):
        runtime, ledger = self._runtime()
        native = self._alternative((0.03, 0.02, -0.01), "SOURCE_NATIVE_EXISTING", 20)
        for candidate in (self.primary, self.recovery[0], native):
            runtime.evaluate(self.snapshot, candidate)
        scopes = {scope: dict(payload) for scope, payload in self._facts(ledger)[NAMESPACE]}
        self.assertEqual(scopes[self.primary.identity.value]["candidate_role"], "PRIMARY")
        self.assertEqual(scopes[self.recovery[0].identity.value]["candidate_source_type"],
                         "SOURCE_BOUNDED_LOCAL_RECOVERY_V1")
        self.assertEqual(scopes[native.identity.value]["candidate_source_type"], "SOURCE_NATIVE_EXISTING")

    def test_t08_trace_serialization_is_deterministic_and_additive(self):
        runtime, ledger = self._runtime()
        for candidate in (self.primary, *self.recovery):
            runtime.evaluate(self.snapshot, candidate)
        record = TraceStepRecord("MULTI", 9, self.snapshot.identity,
            ActionRole.ASSURANCE_BOUNDARY_NO_ACTION, None, None, "NO_ACTION", (("reason", "fixture"),))
        hashes = []
        lines = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as temp:
                writer = CanonicalEvidenceTraceWriter("MULTI", Path(temp), ledger)
                writer.append(record)
                lock = writer.finalize()
                hashes.append(lock.trace_sha256)
                lines.append((Path(temp) / "runtime_trace.jsonl").read_text(encoding="utf-8"))
        self.assertEqual(hashes[0], hashes[1])
        self.assertEqual(lines[0], lines[1])
        parsed = json.loads(lines[0])
        facts = dict(parsed["facts"])
        self.assertIn(NAMESPACE, facts)
        self.assertTrue(all(key in facts for key in FLAT_KEYS))

    def test_t09_scoped_fact_has_no_authority_consumer(self):
        authority_files = (
            "reproduction/runtime/active_runtime_assurance_v2/supervisor.py",
            "reproduction/runtime/active_runtime_assurance_v2/active_cycle.py",
            "reproduction/runtime/active_runtime_assurance_v2/plant_commit.py",
            "reproduction/runtime/active_runtime_assurance_v2/bounded_recovery.py",
            "reproduction/runtime/active_runtime_assurance_v2/l2_runtime.py",
        )
        for relative in authority_files:
            self.assertNotIn(NAMESPACE, (REPO / relative).read_text(encoding="utf-8"), relative)


def main() -> int:
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MultiCandidateL2Tests)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    output = {
        "schema": "MULTI_CANDIDATE_CANONICAL_L2_CPU_VALIDATION_V1",
        "status": "PASS_MULTI_CANDIDATE_CANONICAL_L2_CPU_VALIDATION" if result.wasSuccessful() else "FAIL",
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "gpu_used": False, "primary_plus_six_evaluations": 7,
        "unique_candidate_scopes_expected": 7, "anti_rewrite_preserved": result.wasSuccessful(),
        "trace_schema_identity": "EVALUATION_TRACE_SCHEMA_V2_CERT_EXEC_IDENTITY_V1",
        "tests": {
            "T02_single_primary_legacy_compatibility": "PASS",
            "T03_primary_plus_recovery": "PASS",
            "T04_primary_plus_all_six": "PASS",
            "T05_same_scope_conflict_rejected": "PASS",
            "T06_identical_scope_idempotent": "PASS",
            "T07_role_source_distinction": "PASS",
            "T08_trace_serialization_deterministic": "PASS",
            "T09_no_authority_consumer": "PASS",
        } if result.wasSuccessful() else {
            "failures": sorted(test.id() for test, _ in (*result.failures, *result.errors))
        },
    }
    target = TASK / "results_cpu_validation/multi_candidate_l2_validation.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(output, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, sort_keys=True))
    return 0 if result.wasSuccessful() else 2


if __name__ == "__main__":
    raise SystemExit(main())
