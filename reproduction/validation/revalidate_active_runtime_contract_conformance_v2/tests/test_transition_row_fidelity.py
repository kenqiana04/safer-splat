import dataclasses, json, unittest
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import RoutingDecision
from reproduction.runtime.active_runtime_assurance_v2.supervisor import TransitionRule
from ._support import DESIGN
class TestTransitionFidelity(unittest.TestCase):
    def test_required_frozen_fields_are_not_all_carried(self):
        design=json.loads(DESIGN.read_text(encoding="utf-8"))
        self.assertEqual(43, len(design["rules"]))
        rd={f.name for f in dataclasses.fields(RoutingDecision)}
        tr={f.name for f in dataclasses.fields(TransitionRule)}
        self.assertNotIn("action_authority", rd)
        self.assertNotIn("old_backup_retained", rd)
        self.assertNotIn("new_backup_created", rd)
        self.assertNotIn("theorem_interpretation", rd)
        self.assertNotIn("old_backup_retained", tr)
        self.assertNotIn("new_backup_created", tr)
        self.assertNotIn("theorem_interpretation", tr)
