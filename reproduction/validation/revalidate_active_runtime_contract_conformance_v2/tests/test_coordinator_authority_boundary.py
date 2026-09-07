import ast, unittest
from ._support import RUNTIME
class TestCoordinatorBoundary(unittest.TestCase):
    def test_no_direct_plant_or_action_construction(self):
        source=(RUNTIME/"active_cycle.py").read_text(encoding="utf-8")
        self.assertNotIn("PlantCommitAdapter", source)
        self.assertNotIn("make_action(", source)
        self.assertNotIn("SelectedAction(", source)
        self.assertNotIn("dynamics", source)
