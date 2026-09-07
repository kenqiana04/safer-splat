import unittest
from ._support import RUNTIME, class_methods
class TestBlockerClosure(unittest.TestCase):
    def test_public_owner_and_api_exist(self):
        methods=class_methods(RUNTIME/"active_cycle.py", "ActiveCycleCoordinator")
        self.assertTrue({"start_trial","run_cycle","finalize_trial"} <= methods)
        source=(RUNTIME/"active_cycle.py").read_text(encoding="utf-8")
        for token in ("self.l1_runtime", "self.primary_adapter", "self.c0", "self.l2", "self.l3", "self.supervisor.route_transition", "self.supervisor.arbitrate", "self.active_runner.commit_active_decision"):
            self.assertIn(token, source)
