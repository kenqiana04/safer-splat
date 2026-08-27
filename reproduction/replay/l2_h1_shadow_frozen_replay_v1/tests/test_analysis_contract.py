import csv
import json
from pathlib import Path
import unittest


TASK_ROOT = Path(__file__).resolve().parents[1]


class AnalysisContractTests(unittest.TestCase):
    def read(self, name):
        return json.loads((TASK_ROOT / name).read_text(encoding="utf-8"))

    def test_denominator_partition_and_status_partition(self):
        value = self.read("denominator_audit.json")
        self.assertEqual(value["N_all"], value["N_formal_replayable"] + value["N_diagnostic_reconstructable"] + value["N_not_replayable"])
        self.assertEqual(value["N_L2_candidate_evaluated"], value["N_L2_PASS"] + value["N_L2_FAIL"] + value["N_L2_UNKNOWN"])

    def test_increment_selects_case_a_without_performance_claim(self):
        increment = self.read("l2_information_increment_summary.json")
        case = self.read("FINAL_CASE_DECISION.json")
        self.assertGreater(increment["N_L1_PASS_L2_FAIL"], 0)
        self.assertFalse(increment["collision_prevention_claim_authorized"])
        self.assertEqual(case["selected_case"], "CASE_A")

    def test_multi_candidate_uses_only_historical_rows(self):
        value = self.read("multi_candidate_summary.json")
        self.assertEqual(value["synthetic_candidate_count"], 0)
        self.assertEqual(value["N_multi_candidate_state_groups"], 20)
        with (TASK_ROOT / "multi_candidate_group_analysis.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 20)

    def test_no_unknown_rows_when_not_replayable_rows_exist(self):
        value = self.read("denominator_audit.json")
        self.assertGreater(value["N_not_replayable"], 0)
        self.assertEqual(value["N_L2_UNKNOWN"], 0)
        self.assertEqual(value["identity_checks"]["not_replayable_counted_as_L2_unknown"], 0)


if __name__ == "__main__":
    unittest.main()
