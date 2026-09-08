import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    ActionRole,
    ActiveCycleRequest,
    CertificateStatus,
    StageFailureKind,
)
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


def boom(*_args, **_kwargs):
    raise RuntimeError("r2 injected stage exception")


class R2StageExceptionRoutingTests(unittest.TestCase):
    def _with_valid_backup(self):
        system = build_public_cycle()
        _, first = start_and_run(system)
        request = ActiveCycleRequest(first.next_state.trial_id, 1, (1.0, 0.0, 0.0), None)
        return system, first.next_state, request

    def test_stage_exception_matrix(self):
        cases = (
            ("l1_runtime", "evaluate_cycle", {}),
            ("primary_proposal", "propose", {}),
            ("c0_admission", "evaluate", {}),
            ("l2_runtime", "evaluate", {}),
            ("l3_runtime", "evaluate", {}),
            ("alternative_provider", "enumerate", {"primary_vector": (0.2, 0.0, 0.0)}),
        )
        for attr, method, update in cases:
            with self.subTest(stage=attr):
                system, state, request = self._with_valid_backup()
                system["config"].update(update)
                setattr(getattr(system["coordinator"], attr), method, boom)
                result = system["coordinator"].run_cycle(state, request)
                self.assertEqual(result.action_role, ActionRole.RETAINED_BACKUP)
                self.assertTrue(result.stage_failures)
                self.assertEqual(result.stage_failures[-1].failure_kind, StageFailureKind.STAGE_EXCEPTION)
                self.assertEqual(system["plant"].commit_count, 2)

    def test_terminal_exception_routes_to_boundary(self):
        system = build_public_cycle({"proposal": "FAIL"})
        system["coordinator"].terminal_runtime.evaluate = boom
        _, result = start_and_run(system)
        self.assertTrue(result.boundary)
        self.assertFalse(result.committed)
        self.assertEqual(system["plant"].commit_count, 0)
        self.assertEqual(result.stage_failures[-1].source_phase.value, "TERMINAL_EVALUATION")

    def test_exception_with_eligible_terminal_reaches_terminal_fallback(self):
        system = build_public_cycle({"terminal_member": True, "terminal": CertificateStatus.PASS})
        system["coordinator"].primary_proposal.propose = boom
        _, result = start_and_run(system)
        self.assertEqual(result.action_role, ActionRole.CERTIFIED_TERMINAL)
        self.assertTrue(result.committed)
        self.assertEqual(system["plant"].commit_count, 1)

    def test_exception_without_fallback_reaches_boundary(self):
        system = build_public_cycle()
        system["coordinator"].primary_proposal.propose = boom
        _, result = start_and_run(system)
        self.assertTrue(result.boundary)
        self.assertFalse(result.committed)
        self.assertEqual(system["plant"].commit_count, 0)

    def test_expired_exception_still_reaches_valid_backup(self):
        system, state, request = self._with_valid_backup()
        system["clock"].advance(10.0)
        system["coordinator"].l1_runtime.evaluate_cycle = boom
        result = system["coordinator"].run_cycle(state, request)
        self.assertEqual(result.action_role, ActionRole.RETAINED_BACKUP)
        self.assertTrue(result.committed)

    def test_arbitration_exception_is_typed_block_without_action(self):
        system = build_public_cycle({"proposal": "FAIL"})
        system["supervisor"].arbitrate = boom
        _, result = start_and_run(system)
        self.assertTrue(result.boundary)
        self.assertFalse(result.committed)
        self.assertIsNone(result.action_role)
        self.assertEqual(system["plant"].commit_count, 0)
        self.assertEqual(result.stage_failures[-1].source_phase.value, "ARBITRATION")


if __name__ == "__main__":
    unittest.main()
