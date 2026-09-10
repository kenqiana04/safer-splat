import unittest
import struct

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.c0_admission import C0Admission
from reproduction.runtime.active_runtime_assurance_v2.primary_proposal_adapter import PrimaryProposalAdapter
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CandidateRole, CertificateStatus
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import snapshot


class PrimaryProposalAdapterTests(unittest.TestCase):
    def setUp(self):
        self.state = snapshot()
        self.registry = AuthorityRegistry.frozen(self.state.map_identity, "dt:0.05")

    @staticmethod
    def binary32(value):
        return struct.unpack("!f", struct.pack("!f", value))[0]

    def configured_adapter(self, vector):
        return PrimaryProposalAdapter(
            lambda state, u_des: (True, vector, "SOLVED"),
            "clarabel:cbf",
            actuator_bounds=(self.registry.actuator.u_min, self.registry.actuator.u_max),
            source_scalar_contract="IEEE754_BINARY32",
        )

    def test_successful_finite_solver_result_is_primary(self):
        adapter = PrimaryProposalAdapter(lambda state, u_des: (True, (0.2, 0.0, 0.0), "SOLVED"), "clarabel:cbf")
        result = adapter.propose(snapshot(), (0.0, 0.0, 0.0))
        self.assertIsNotNone(result.candidate)
        self.assertEqual(result.candidate.role, CandidateRole.PRIMARY)
        self.assertEqual(result.candidate.vector[0], 0.2)

    def test_solver_failure_never_returns_u_des(self):
        adapter = PrimaryProposalAdapter(lambda state, u_des: (False, u_des, "FAILED"), "clarabel:cbf")
        result = adapter.propose(snapshot(), (0.08, 0.0, 0.0))
        self.assertIsNone(result.candidate)
        self.assertEqual(result.reason, "QP_SOLVER_FAILED")

    def test_exact_binary32_bound_representations_are_canonicalized(self):
        adapter = self.configured_adapter((self.binary32(-0.1), self.binary32(0.1), 0.0))
        result = adapter.propose(self.state, (0.0, 0.0, 0.0))
        self.assertEqual(result.candidate.vector, (-0.1, 0.1, 0.0))
        self.assertEqual(C0Admission(self.registry).evaluate(result.candidate, self.state).status, CertificateStatus.PASS)

    def test_conceptual_bounds_remain_exact(self):
        adapter = self.configured_adapter((-0.1, 0.1, 0.0))
        result = adapter.propose(self.state, (0.0, 0.0, 0.0))
        self.assertEqual(result.candidate.vector, (-0.1, 0.1, 0.0))

    def test_true_out_of_bounds_are_not_clipped_and_still_fail_c0(self):
        vector = (-0.100001, 0.100001, 0.0)
        result = self.configured_adapter(vector).propose(self.state, (0.0, 0.0, 0.0))
        self.assertEqual(result.candidate.vector, vector)
        c0 = C0Admission(self.registry).evaluate(result.candidate, self.state)
        self.assertEqual(c0.status, CertificateStatus.FAIL)
        self.assertEqual(c0.reason, "F_ACTUATOR_ADMISSIBILITY_LOCAL")

    def test_interior_and_near_bound_nonmatches_remain_unchanged(self):
        vectors = (
            (-0.09999999403953552, 0.09999999403953552, 0.0),
            (-0.02, 0.03, 0.0),
            (0.0, 0.0, 0.0),
            (-0.10000002, 0.10000002, 0.0),
        )
        for vector in vectors:
            with self.subTest(vector=vector):
                result = self.configured_adapter(vector).propose(self.state, (0.0, 0.0, 0.0))
                self.assertEqual(result.candidate.vector, vector)

    def test_unknown_configured_source_scalar_contract_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "SOURCE_SCALAR_CONTRACT_UNSUPPORTED"):
            PrimaryProposalAdapter(
                lambda state, u_des: (True, (0.0, 0.0, 0.0), "SOLVED"),
                "clarabel:cbf",
                actuator_bounds=(self.registry.actuator.u_min, self.registry.actuator.u_max),
                source_scalar_contract="UNKNOWN",
            )


if __name__ == "__main__": unittest.main()
