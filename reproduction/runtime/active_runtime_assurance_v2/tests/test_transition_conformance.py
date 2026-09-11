import csv
import json
import unittest
from pathlib import Path

from reproduction.runtime.active_runtime_assurance_v2.supervisor import TransitionTable


ROOT = Path(__file__).resolve().parents[3]
TABLE = ROOT / "specification" / "method_logic_closure_v2" / "STATE_TRANSITION_TABLE_V2.csv"
DESIGN = ROOT / "design" / "active_runtime_public_cycle_composition_v2" / "EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json"


class TransitionConformanceTests(unittest.TestCase):
    def test_44_rules_exactly_once_and_synchronized_with_design(self):
        with TABLE.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        ids = [row["rule_id"] for row in rows]
        design = json.loads(DESIGN.read_text(encoding="utf-8"))
        design_ids = [row["rule_id"] for row in design["rules"]]
        self.assertEqual(len(rows), 44)
        self.assertEqual(len(set(ids)), 44)
        self.assertEqual(design["rule_count"], 44)
        self.assertEqual(ids, design_ids)

    def test_runtime_objects_preserve_normative_mapping(self):
        table = TransitionTable.from_csv(TABLE)
        with TABLE.open(encoding="utf-8", newline="") as handle:
            rows = {row["rule_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(set(table.by_id), set(rows))
        for rule_id, rule in table.by_id.items():
            source = rows[rule_id]
            self.assertEqual(rule.source_phase, source["source_phase"])
            self.assertEqual(rule.destination_phase, source["destination_phase"])
            self.assertEqual(rule.commit_allowed, source["commit_allowed"].lower() == "true")
            self.assertEqual(rule.action_authority, source["action_authority"])
            self.assertEqual(rule.failure_code, source["failure_code_if_any"])


if __name__ == "__main__":
    unittest.main()
