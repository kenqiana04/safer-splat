import csv
import unittest
from pathlib import Path


class TransitionDynamicConformance(unittest.TestCase):
    def test_table_has_43_unique_runtime_rules(self):
        path = Path(__file__).resolve().parents[4] / "reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/RUNTIME_TRANSITION_IMPLEMENTATION_MAP_V2.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 43)
        self.assertEqual(len({row["rule_id"] for row in rows}), 43)
        self.assertTrue(all(row["mapping_cardinality"] == "EXACTLY_ONCE" for row in rows))


if __name__ == "__main__":
    unittest.main()
