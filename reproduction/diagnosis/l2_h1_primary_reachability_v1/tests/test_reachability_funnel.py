import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "diagnose_reachability_funnel.py"
SPEC = importlib.util.spec_from_file_location("diagnose_reachability_funnel", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def eligible_row(**overrides):
    row = {
        "data_role": "FORMAL_PROSPECTIVE_SHADOW_COHORT_V1",
        "logging_qc_complete": True,
        "selected_candidate_role": "SELECTED_EXECUTED_CONTROL",
        "selected_candidate_committed": True,
        "l1_observation_source": "SHADOW_RECOMPUTED_FROZEN_CERTIFIER",
        "l1_status": "PASS",
        "l2_reached": True,
        "l2_status": "PASS",
        "map_authority_valid": True,
        "payload_join_identity_valid": True,
        "trial_id": 0,
    }
    row.update(overrides)
    return row


class ReachabilityFunnelTests(unittest.TestCase):
    def test_g6_universal_block(self):
        rows = [eligible_row(l1_status="FAIL", l2_reached=False, l2_status="NOT_REACHED") for _ in range(3)]
        result = MODULE.diagnose_rows(rows)
        self.assertEqual(result["data_only"]["earliest_universal_blocking_gate"], "G6")
        self.assertEqual(result["first_failures"]["G6"], 3)
        self.assertEqual(result["l1_status"]["FAIL"], 3)

    def test_g7_universal_block(self):
        rows = [eligible_row(l2_reached=False, l2_status="NOT_REACHED") for _ in range(2)]
        result = MODULE.diagnose_rows(rows)
        self.assertEqual(result["data_only"]["earliest_universal_blocking_gate"], "G7")
        self.assertEqual(result["first_failures"]["G7"], 2)

    def test_g8_universal_block(self):
        rows = [eligible_row(l2_status="NOT_TYPED") for _ in range(2)]
        result = MODULE.diagnose_rows(rows)
        self.assertEqual(result["data_only"]["earliest_universal_blocking_gate"], "G8")
        self.assertEqual(result["first_failures"]["G8"], 2)

    def test_first_failure_accounting_with_overlapping_failures(self):
        rows = [eligible_row(logging_qc_complete=False, l1_status="FAIL")]
        result = MODULE.diagnose_rows(rows)
        self.assertEqual(result["overlapping_unmet"]["G2"], 1)
        self.assertEqual(result["overlapping_unmet"]["G6"], 1)
        self.assertEqual(result["first_failures"]["G2"], 1)
        self.assertEqual(sum(result["first_failures"].values()) + result["N_primary"], 1)

    def test_contradiction_detection(self):
        rows = [eligible_row(l1_status="FAIL", l2_reached=False, l2_status="NOT_REACHED")]
        with self.assertRaises(MODULE.DiagnosisContradictionError):
            MODULE.diagnose_rows(rows, expected={"row_count": 1, "N_primary": 1, "N_l2_reached_true": 0})


if __name__ == "__main__":
    unittest.main()
