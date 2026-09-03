from __future__ import annotations
import csv, json, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def load(name): return json.loads((ROOT / name).read_text(encoding="utf-8"))

class ActiveRuntimeDesignTests(unittest.TestCase):
    def test_single_authorities(self):
        a=load("MODULE_ARCHITECTURE_V2.json")
        self.assertEqual(sum(m["owns_selection"] for m in a["modules"]),1)
        self.assertEqual(sum(m["writes_plant"] for m in a["modules"]),1)
    def test_geometry_constants_and_V1_ban(self):
        text=(ROOT/"CANDIDATE_CERTIFICATION_PIPELINE_V2.md").read_text(encoding="utf-8")
        self.assertIn("0.025 m",text); self.assertIn("cannot import",text)
    def test_transition_totality(self):
        with (ROOT/"RUNTIME_TRANSITION_IMPLEMENTATION_MANIFEST_V2.csv").open(encoding="utf-8",newline="") as handle:
            rows=list(csv.DictReader(handle))
        self.assertEqual(len(rows),43); self.assertEqual(len({r["rule_id"] for r in rows}),43)
    def test_first_cycle_no_escape(self):
        text=(ROOT/"FIRST_CYCLE_AND_START_ADMISSION_V2.md").read_text(encoding="utf-8")
        self.assertIn("There is no uncertified first-cycle escape",text)
    def test_deadline_and_goal_hold_gates(self):
        g=load("ACTIVE_RUNTIME_PARAMETERIZATION_GATES_V2.json")
        self.assertFalse(g["numeric_deadline_profile"]["values_selected"]); self.assertEqual(g["goal_hold_runtime_authority"]["status"],"DISABLED")
    def test_no_runtime_outputs(self):
        self.assertFalse((ROOT.parents[1]/"runtime/active_runtime_assurance_v2").exists())

if __name__ == "__main__": unittest.main()
