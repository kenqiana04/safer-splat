from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK))

from contract_rules import canonical_scenario, validate_scenario  # noqa: E402


class SelectedControlActuatorAuthorityTests(unittest.TestCase):
    def test_t1_qp_output_equals_execution_passes(self):
        self.assertEqual(validate_scenario(canonical_scenario()), [])

    def test_t2_hidden_clip_detected(self):
        s = copy.deepcopy(canonical_scenario())
        s["post_certification_transform"] = "HIDDEN_CLIP"
        self.assertIn("HIDDEN_POST_CERTIFICATION_TRANSFORM", validate_scenario(s))

    def test_t3_selected_not_executed_rejected(self):
        s = copy.deepcopy(canonical_scenario())
        s["executed_control_vector"] = [0.02, -0.02, 0.0]
        self.assertIn("SELECTED_EXECUTED_MISMATCH", validate_scenario(s))

    def test_t4_backup_actuator_mismatch_rejected(self):
        s = copy.deepcopy(canonical_scenario())
        s["backup_actuator_authority"] = "L3_PRIVATE_AUTHORITY"
        self.assertIn("BACKUP_ACTUATOR_AUTHORITY_MISMATCH", validate_scenario(s))

    def test_t5_terminal_actuator_mismatch_rejected(self):
        s = copy.deepcopy(canonical_scenario())
        s["terminal_actuator_authority"] = "L5_PRIVATE_AUTHORITY"
        self.assertIn("TERMINAL_ACTUATOR_AUTHORITY_MISMATCH", validate_scenario(s))

    def test_t6_unknown_actuator_rejected(self):
        s = copy.deepcopy(canonical_scenario())
        s["actuator_authority_resolved"] = False
        self.assertIn("ACTUATOR_AUTHORITY_UNKNOWN_OR_MISMATCH", validate_scenario(s))

    def test_t7_rate_limit_duplicated_rejected(self):
        s = copy.deepcopy(canonical_scenario())
        s["rate_limit_authorities"] = ["SUPERVISOR_RATE", "PLANT_RATE"]
        self.assertIn("DUPLICATED_RATE_LIMIT_AUTHORITY", validate_scenario(s))

    def test_t8_hidden_delay_rejected(self):
        s = copy.deepcopy(canonical_scenario())
        s["hidden_delay"] = True
        self.assertIn("HIDDEN_ACTUATION_DELAY", validate_scenario(s))

    def test_t9_desired_mistaken_as_certified_rejected(self):
        s = copy.deepcopy(canonical_scenario())
        s["desired_mistaken_as_certified"] = True
        self.assertIn("DESIRED_COMMAND_MISTAKEN_AS_CERTIFIED", validate_scenario(s))

    def test_t10_legacy_controller_path_quarantined(self):
        s = copy.deepcopy(canonical_scenario())
        s["legacy_controller_path_used"] = True
        self.assertIn("LEGACY_CONTROLLER_PATH_NOT_QUARANTINED", validate_scenario(s))


if __name__ == "__main__":
    unittest.main(verbosity=2)
