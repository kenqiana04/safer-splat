import unittest

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CertificateStatus, EvidenceResult
from reproduction.runtime.active_runtime_assurance_v2.terminal_runtime import GOAL_HOLD_RUNTIME_ENABLED, TerminalRuntime
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import snapshot


class TerminalRuntimeTests(unittest.TestCase):
    def test_goal_hold_disabled(self):
        self.assertFalse(GOAL_HOLD_RUNTIME_ENABLED)

    def test_certificate_and_eligibility_separate_from_selection(self):
        state=snapshot(); registry=AuthorityRegistry.frozen(state.map_identity,"dt:0.05")
        terminal=TerminalRuntime(lambda s: True, lambda s,m,r: EvidenceResult(CertificateStatus.PASS,"TERMINAL_CERTIFIED","term:e"), registry)
        result=terminal.evaluate(state, fallback_context=True)
        self.assertTrue(result.eligible)
        self.assertIsNone(result.action)

    def test_stale_reference_is_unknown(self):
        state=snapshot(); registry=AuthorityRegistry.frozen(state.map_identity,"dt:0.05")
        terminal=TerminalRuntime(lambda s: True, lambda *a: EvidenceResult(CertificateStatus.PASS,"OK","e"), registry)
        self.assertEqual(terminal.evaluate(state, True, expected_terminal_ref="stale").status, CertificateStatus.UNKNOWN)


if __name__ == "__main__": unittest.main()
