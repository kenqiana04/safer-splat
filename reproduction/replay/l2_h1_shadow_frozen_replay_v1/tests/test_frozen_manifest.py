from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FrozenManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.freeze = json.loads((ROOT / "source_universe_freeze.json").read_text(encoding="utf-8"))
        cls.rows = [json.loads(line) for line in (ROOT / "frozen_replay_manifest.jsonl").read_text(encoding="utf-8").splitlines() if line]

    def test_universe_was_frozen_before_results(self):
        self.assertFalse(self.freeze["replay_execution_started"])
        self.assertEqual(self.freeze["l2_result_field_count"], 0)
        self.assertEqual(self.freeze["N_all"], len(self.rows))

    def test_not_replayable_is_never_l2_unknown(self):
        for row in self.rows:
            self.assertNotIn("l2_status", row)
            if row["replayability_class"] == "NOT_REPLAYABLE":
                self.assertFalse(row["primary_analysis_eligible"])

    def test_primary_eligibility_requires_reached_formal_row(self):
        for row in self.rows:
            if row["primary_analysis_eligible"]:
                self.assertEqual(row["replayability_class"], "FORMAL_REPLAYABLE")
                self.assertIs(row["l2_reached"], True)


if __name__ == "__main__":
    unittest.main()
