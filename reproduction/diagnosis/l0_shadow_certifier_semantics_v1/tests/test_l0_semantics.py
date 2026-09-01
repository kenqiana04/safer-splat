from __future__ import annotations

import sys
import unittest
from pathlib import Path


TASK_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_DIR))

from aggregate_l0_outcomes import aggregate_records, classify_l0_status, mapping_mismatch


class L0SemanticsTests(unittest.TestCase):
    def test_pass_token_maps_to_pass(self) -> None:
        self.assertEqual(classify_l0_status("PASS"), "PASS")

    def test_fail_token_maps_to_fail(self) -> None:
        self.assertEqual(classify_l0_status("FAIL"), "FAIL")

    def test_unknown_token_maps_to_unknown(self) -> None:
        self.assertEqual(classify_l0_status("UNKNOWN"), "UNKNOWN")

    def test_status_mapping_mismatch_is_detected(self) -> None:
        self.assertTrue(mapping_mismatch(raw_status="SAFE", adapter_status="FAIL", raw_pass_tokens={"SAFE"}))
        self.assertFalse(mapping_mismatch(raw_status="FINITE", adapter_status="PASS", raw_pass_tokens={"FINITE"}))

    def test_absent_l0_outcome_does_not_fabricate_distribution(self) -> None:
        summary = aggregate_records([{"l1_status": "NOT_REACHED", "l2_reachability_reason": "L0_BLOCKED"}])
        self.assertFalse(summary["observable"])
        self.assertIsNone(summary["counts"])
        self.assertEqual(summary["outcome"], "L0_OUTCOME_DISTRIBUTION_NOT_OBSERVABLE_FROM_FROZEN_RESULTS")


if __name__ == "__main__":
    unittest.main()
