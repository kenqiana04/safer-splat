from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK))

from contract_rules import canonical_scenario, validate_scenario  # noqa: E402


class GeometryAuthorityContractTests(unittest.TestCase):
    def test_t1_canonical_pass(self):
        self.assertEqual(validate_scenario(canonical_scenario()), [])

    def test_t2_l2_legacy_011_fails(self):
        s = copy.deepcopy(canonical_scenario())
        s["layer_effective_radius_m"]["L2_H1_SEGMENT"] = 0.11
        self.assertIn("L2_H1_SEGMENT_RADIUS_MISMATCH", validate_scenario(s))

    def test_t3_l3_backup_legacy_011_fails(self):
        s = copy.deepcopy(canonical_scenario())
        s["layer_effective_radius_m"]["L3_BACKUP_SEGMENTS"] = 0.11
        self.assertIn("L3_BACKUP_SEGMENTS_RADIUS_MISMATCH", validate_scenario(s))

    def test_t4_terminal_mixed_0025_011_fails(self):
        s = copy.deepcopy(canonical_scenario())
        s["layer_effective_radius_m"]["L3_TERMINAL_ZERO_HOLD"] = 0.11
        self.assertIn("L3_TERMINAL_ZERO_HOLD_RADIUS_MISMATCH", validate_scenario(s))

    def test_t5_controller_changed_to_0025_fails(self):
        s = copy.deepcopy(canonical_scenario())
        s["controller_radius_m"] = 0.025
        s["layer_effective_radius_m"]["CONTROLLER_ACTIVE_CBF"] = 0.025
        errors = validate_scenario(s)
        self.assertIn("CONTROLLER_RADIUS_MUTATION", errors)
        self.assertIn("ACTIVE_CONTROLLER_RADIUS_MISMATCH", errors)

    def test_t6_margin_double_application_fails(self):
        s = copy.deepcopy(canonical_scenario())
        s["margin_application_count"] = 2
        s["certification_effective_radius_m"] = 0.035
        self.assertIn("MARGIN_APPLICATION_COUNT_NOT_ONE", validate_scenario(s))

    def test_t7_rho_silently_001_fails(self):
        s = copy.deepcopy(canonical_scenario())
        s["rho_seg_m"] = 0.01
        s["layer_rho_seg_m"]["L1_IMMEDIATE_CLOSED_SEGMENT"] = 0.01
        self.assertIn("SEGMENT_RESERVE_MISMATCH", validate_scenario(s))

    def test_t8_layer_margin_without_source_fails(self):
        s = copy.deepcopy(canonical_scenario())
        s["layer_local_margin_without_source"] = True
        self.assertIn("LAYER_LOCAL_MARGIN_WITHOUT_SOURCE", validate_scenario(s))

    def test_t9_unresolved_controller_fallback_010_fails(self):
        s = copy.deepcopy(canonical_scenario())
        s["controller_radius_m"] = None
        s["fallback_value_m"] = 0.10
        errors = validate_scenario(s)
        self.assertIn("G0_UNRESOLVED", errors)
        self.assertIn("HISTORICAL_V1_FALLBACK", errors)

    def test_t10_v1_historical_011_invalidated_fails(self):
        s = copy.deepcopy(canonical_scenario())
        s["v1_historical_valid"] = False
        self.assertIn("V1_HISTORICAL_EVIDENCE_INVALIDATED", validate_scenario(s))


if __name__ == "__main__":
    unittest.main(verbosity=2)
