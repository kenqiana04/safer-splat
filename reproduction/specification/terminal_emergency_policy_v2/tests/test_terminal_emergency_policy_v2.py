import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("terminal_policy_checker", ROOT / "model_check_terminal_emergency_policy_v2.py")
CHECKER = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


class TerminalEmergencyPolicyTests(unittest.TestCase):
    def test_01_membership_alone_has_no_action(self):
        state = CHECKER.PolicyState(terminal_membership="TRUE", terminal_certificate="NOT_READY")
        self.assertEqual(CHECKER.arbitrate(state), "ASSURANCE_BOUNDARY")

    def test_02_zero_velocity_start_does_not_preempt_navigation(self):
        state = CHECKER.PolicyState(navigation="CERTIFIED_READY", terminal_certificate="READY", zero_velocity_start=True)
        self.assertEqual(CHECKER.arbitrate(state), "NAVIGATION")

    def test_03_navigation_dominates_backup_and_terminal(self):
        state = CHECKER.PolicyState(navigation="CERTIFIED_READY", backup="VALID", terminal_certificate="READY")
        self.assertEqual(CHECKER.arbitrate(state), "NAVIGATION")

    def test_04_valid_backup_dominates_terminal(self):
        state = CHECKER.PolicyState(backup="VALID", terminal_certificate="READY")
        self.assertEqual(CHECKER.arbitrate(state), "RETAINED_BACKUP")

    def test_05_ready_eligible_terminal_is_selectable(self):
        self.assertEqual(CHECKER.arbitrate(CHECKER.PolicyState(terminal_certificate="READY")), "TERMINAL")

    def test_06_exhausted_backup_does_not_authorize_terminal(self):
        state = CHECKER.PolicyState(backup="EXHAUSTED", terminal_certificate="NOT_READY")
        self.assertEqual(CHECKER.arbitrate(state), "ASSURANCE_BOUNDARY")

    def test_07_stale_terminal_reference_blocks_terminal(self):
        state = CHECKER.PolicyState(backup="EXHAUSTED", terminal_certificate="READY", terminal_reference_valid=False)
        self.assertEqual(CHECKER.arbitrate(state), "ASSURANCE_BOUNDARY")

    def test_08_expired_deadline_forbids_new_certification(self):
        self.assertFalse(CHECKER.terminal_certification_allowed("EXPIRED"))

    def test_09_expired_deadline_allows_already_ready_terminal(self):
        state = CHECKER.PolicyState(terminal_certificate="READY", deadline="EXPIRED", certified_before_guard=True)
        self.assertEqual(CHECKER.arbitrate(state), "TERMINAL")

    def test_10_unknown_certificate_never_commits(self):
        self.assertEqual(CHECKER.arbitrate(CHECKER.PolicyState(terminal_certificate="UNKNOWN")), "ASSURANCE_BOUNDARY")

    def test_11_external_request_does_not_create_certificate(self):
        state = CHECKER.PolicyState(terminal_context="EXTERNAL_REQUEST_ONLY", external_request=True, terminal_certificate="NOT_READY")
        self.assertEqual(CHECKER.arbitrate(state), "ASSURANCE_BOUNDARY")

    def test_12_selected_executed_identity_and_determinism(self):
        state = CHECKER.PolicyState(terminal_certificate="READY")
        selected, executed = CHECKER.terminal_commit_identity(state)
        self.assertEqual(selected, executed)
        self.assertEqual(CHECKER.arbitrate(state), CHECKER.arbitrate(state))


if __name__ == "__main__":
    unittest.main()
