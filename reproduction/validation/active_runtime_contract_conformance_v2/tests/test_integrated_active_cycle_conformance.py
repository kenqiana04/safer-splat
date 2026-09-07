import unittest

from reproduction.runtime.active_runtime_assurance_v2.active_runner import ActiveRunner
from conformance_support import runner


class IntegratedActiveCycleConformance(unittest.TestCase):
    def test_public_runtime_has_no_full_cycle_composition_entrypoint(self):
        # Positive detection of the integration boundary: this must not be
        # converted into a task-local fake orchestration or a conformance PASS.
        api = {name for name in dir(ActiveRunner) if not name.startswith("_")}
        self.assertIn("commit_active_decision", api)
        self.assertNotIn("run_cycle", api)
        self.assertNotIn("step", api)
        self.assertNotIn("execute_cycle", api)
        instance = runner()
        instance.startup()
        self.assertTrue(instance.started)


if __name__ == "__main__":
    unittest.main()
