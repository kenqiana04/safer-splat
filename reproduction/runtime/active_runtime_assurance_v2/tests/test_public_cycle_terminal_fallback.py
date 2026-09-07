import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActionRole, CertificateStatus
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


class PublicCycleTerminalFallbackTests(unittest.TestCase):
    def test_terminal_is_evaluated_only_after_supervisor_route(self):
        system = build_public_cycle({"proposal": "FAIL", "terminal_member": True, "terminal": CertificateStatus.PASS})
        _, result = start_and_run(system)
        self.assertEqual(system["counters"]["terminal"], 1)
        self.assertEqual(result.action_role, ActionRole.CERTIFIED_TERMINAL)
        self.assertEqual(result.final_supervisor_decision.rule_id, "ARB_TERMINAL")

    def test_normal_navigation_never_calls_terminal(self):
        system = build_public_cycle({"terminal_member": True, "terminal": CertificateStatus.PASS})
        _, result = start_and_run(system)
        self.assertEqual(result.action_role, ActionRole.PRIMARY_NAVIGATION)
        self.assertEqual(system["counters"]["terminal"], 0)


if __name__ == "__main__":
    unittest.main()
