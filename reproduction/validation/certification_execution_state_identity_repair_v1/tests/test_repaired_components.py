from __future__ import annotations

from types import SimpleNamespace
import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_errors import CommitAuthorityViolation
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole,
    CandidateRole,
    CertificateStatus,
    EvidenceResult,
    RuntimeStateSnapshot,
    SupervisorDecision,
    make_action,
    make_candidate,
)
from reproduction.runtime.certification_execution_state_identity_repair_v1.canonical_transition import CanonicalExecutionTransition, binary32_hex
from reproduction.runtime.certification_execution_state_identity_repair_v1.evidence import CanonicalIdentityLedger
from reproduction.runtime.certification_execution_state_identity_repair_v1.repaired_components import (
    CanonicalL1Runtime,
    CanonicalL2Runtime,
    ContinuityGuardedPlantCommitAdapter,
)
from reproduction.runtime.v3_hard_radius_runtime_wiring_v1.stack_factory import make_v3_authority_registry


def safe_backend(start, end, map_identity, radius, rho):
    return EvidenceResult(CertificateStatus.PASS, "TEST_SAFE", f"evidence:{start}:{end}:{map_identity}:{radius}:{rho}")


class RepairedComponentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = make_v3_authority_registry("map", "dt", "deadline")
        self.transition = CanonicalExecutionTransition("cpu", backend_label="TEST_FIXTURE_ONLY_NOT_RUNTIME_AUTHORITY")
        self.ledger = CanonicalIdentityLedger()
        self.snapshot = RuntimeStateSnapshot.create("t", 4, (0.1, -0.2, 0.3, 0.01, -0.02, 0.03), (0.0,) * 6, "map", 0.05)
        self.candidate = make_candidate((0.1, -0.1, 0.05), CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "controller", self.snapshot)

    def test_l1_and_l2_share_cross_cycle_segment_bits(self) -> None:
        l1 = CanonicalL1Runtime(safe_backend, self.registry, self.transition, self.ledger)
        l2 = CanonicalL2Runtime(safe_backend, self.registry, self.transition, self.ledger)
        l2_result = l2.evaluate(self.snapshot, self.candidate)
        x1 = self.transition.transition(self.snapshot.state, self.candidate.vector, self.snapshot.dt)
        next_snapshot = RuntimeStateSnapshot.create("t", 5, x1, self.snapshot.goal, "map", 0.05)
        next_l1 = l1.evaluate_cycle(next_snapshot)
        self.assertEqual(binary32_hex(l2_result.p_k1), binary32_hex(next_l1.segment_start))
        self.assertEqual(binary32_hex(l2_result.p_k2), binary32_hex(next_l1.segment_end))
        self.assertEqual(l2_result.segment_identity, next_l1.segment_identity)

    def test_identity_mismatch_blocks_before_plant_commit(self) -> None:
        plant = ContinuityGuardedPlantCommitAdapter(self.registry, self.transition, self.ledger)
        action = make_action(self.candidate.vector, ActionRole.PRIMARY_NAVIGATION, self.candidate.identity.value)
        wrong = RuntimeStateSnapshot.create("t", 5, (0.0,) * 6, self.snapshot.goal, "map", 0.05).identity
        decision = SupervisorDecision(4, self.snapshot.identity, action, True, "TEST", "ARB_NAV", SimpleNamespace(expected_activation_state_identity=wrong))
        with self.assertRaisesRegex(CommitAuthorityViolation, "CERT_EXEC_STATE_IDENTITY_MISMATCH"):
            plant.commit(decision, self.snapshot, action)
        self.assertEqual(plant.commit_count, 0)


if __name__ == "__main__":
    unittest.main()
