from __future__ import annotations

import sys
import unittest
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from future_equivalence_comparator import COMPARISON_FIELDS, compare_traces  # noqa: E402
from future_equivalence_runner import build_dry_run_manifest  # noqa: E402
from mock_zero_authority_harness import FAULT_IDS, run_fault_matrix  # noqa: E402


class FaultsAndFutureBoundaryTests(unittest.TestCase):
    def test_all_ten_faults_preserve_mock_control_and_zero_real_execution(self):
        result = run_fault_matrix()
        self.assertEqual(tuple(row["fault_id"] for row in result["cases"]), FAULT_IDS)
        self.assertEqual(result["fault_injection_case_count"], 10)
        self.assertTrue(result["all_mock_control_traces_equal"])
        self.assertTrue(result["all_fault_expectations_met"])
        self.assertEqual(result["real_navigation_equivalence_run_count"], 0)
        self.assertEqual(result["logging_pilot_run_count"], 0)
        self.assertEqual(result["formal_on_policy_cohort_count"], 0)
        self.assertEqual(result["navigation_rollout_count"], 0)

    def test_future_equivalence_tool_is_dry_run_only(self):
        manifest = build_dry_run_manifest()
        self.assertTrue(manifest["dry_run_only"])
        self.assertEqual(manifest["observer_off_trace"], "NOT_RUN")
        self.assertEqual(manifest["observer_on_trace"], "NOT_RUN")
        self.assertEqual(manifest["real_navigation_equivalence_run_count"], 0)
        empty = {field: "NOT_RUN" for field in COMPARISON_FIELDS}
        comparison = compare_traces(empty, empty)
        self.assertTrue(comparison["all_equal"])
        self.assertFalse(comparison["real_navigation_equivalence"])
        self.assertFalse(comparison["performance_claim"])


if __name__ == "__main__":
    unittest.main()
