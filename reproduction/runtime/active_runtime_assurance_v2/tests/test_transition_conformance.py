import csv
import unittest
from pathlib import Path

from reproduction.runtime.active_runtime_assurance_v2.supervisor import TransitionTable


PACKAGE = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[4]
LOCAL = PACKAGE / "implementation_evidence" / "RUNTIME_TRANSITION_IMPLEMENTATION_MAP_V2.csv"
UPSTREAM = REPO / "reproduction" / "design" / "active_runtime_assurance_implementation_v2" / "RUNTIME_TRANSITION_IMPLEMENTATION_MANIFEST_V2.csv"


class TransitionConformanceTests(unittest.TestCase):
    def test_43_rules_exactly_once_and_byte_identical(self):
        self.assertEqual(LOCAL.read_bytes(), UPSTREAM.read_bytes())
        with LOCAL.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        ids = [row["rule_id"] for row in rows]
        self.assertEqual(len(rows), 43)
        self.assertEqual(len(set(ids)), 43)
        self.assertTrue(all(row["mapping_cardinality"] == "EXACTLY_ONCE" for row in rows))

    def test_runtime_objects_preserve_normative_mapping(self):
        table = TransitionTable.from_csv(LOCAL)
        with LOCAL.open(encoding="utf-8", newline="") as handle:
            rows = {row["rule_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(set(table.by_id), set(rows))
        for rule_id, rule in table.by_id.items():
            source = rows[rule_id]
            self.assertEqual(rule.source_phase, source["source_phase"])
            self.assertEqual(rule.destination_phase, source["runtime_destination"])
            self.assertEqual(rule.commit_allowed, source["commit_allowed"].lower() == "true")
            self.assertEqual(rule.action_authority, source["commit_authority"])
            self.assertEqual(rule.failure_code, source["failure_mapping"])


if __name__ == "__main__":
    unittest.main()
