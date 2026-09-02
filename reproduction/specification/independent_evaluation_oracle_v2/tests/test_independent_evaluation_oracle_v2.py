#!/usr/bin/env python3
"""Six compact unit/static checks; no runtime or scientific data."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class OracleFreezeTests(unittest.TestCase):
    def test_owner_and_feedback(self):
        x = load("EVALUATION_ORACLE_AUTHORITY_V2.json")
        self.assertEqual(x["unique_owner"], "POSTHOC_EVALUATION_ORACLE")
        self.assertFalse(x["ORACLE_FEEDBACK_AUTHORITY"])

    def test_collision_margin_separation(self):
        text = (ROOT / "COLLISION_VS_MARGIN_ORACLE_V2.md").read_text(encoding="utf-8")
        self.assertIn("0.015 m", text)
        self.assertIn("0.025 m", text)
        self.assertIn("swept-segment", text)

    def test_goal_and_timeout(self):
        x = load("GOAL_COMPLETION_ORACLE_V2.json")
        self.assertEqual(x["tolerance"], 0.001)
        self.assertFalse(x["timeout_alone_is_success"])

    def test_unknown_not_safe(self):
        x = load("EVALUATION_UNKNOWN_POLICY_V2.json")
        self.assertFalse(x["EVAL_UNKNOWN_IS_SAFE"])
        self.assertTrue(x["unknown_trials_retained_in_accounting"])

    def test_invariants_complete(self):
        inv = load("INDEPENDENT_EVALUATION_ORACLE_INVARIANTS_V2.json")["invariants"]
        self.assertEqual([x["id"] for x in inv], [f"EO-{i:02d}" for i in range(1, 27)])

    def test_no_physical_claim_without_gt(self):
        x = load("EXTERNAL_GROUND_TRUTH_ORACLE_AUDIT_V2.json")
        self.assertFalse(x["physical_collision_claim_authorized"])
        self.assertIn("UNAVAILABLE", x["EXTERNAL_GT_COLLISION_ORACLE"])


if __name__ == "__main__":
    unittest.main()
