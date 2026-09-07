import unittest

from reproduction.runtime.active_runtime_assurance_v2.terminal_runtime import TerminalRuntime
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CertificateStatus
from conformance_support import evidence, registry, snapshot


class TerminalConformance(unittest.TestCase):
    def test_membership_certificate_eligibility_and_goal_hold_boundary(self):
        state = snapshot()
        term = TerminalRuntime(lambda _: True, lambda *_: evidence(), registry())
        result = term.evaluate(state, True)
        self.assertEqual(result.status, CertificateStatus.PASS)
        self.assertTrue(result.eligible)
        self.assertEqual(term.evaluate(state, False).reason, "TERMINAL_CONTEXT_NOT_ELIGIBLE")


if __name__ == "__main__":
    unittest.main()
