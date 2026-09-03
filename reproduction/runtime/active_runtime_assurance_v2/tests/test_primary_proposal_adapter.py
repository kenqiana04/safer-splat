import unittest

from reproduction.runtime.active_runtime_assurance_v2.primary_proposal_adapter import PrimaryProposalAdapter
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CandidateRole
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import snapshot


class PrimaryProposalAdapterTests(unittest.TestCase):
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


if __name__ == "__main__": unittest.main()
