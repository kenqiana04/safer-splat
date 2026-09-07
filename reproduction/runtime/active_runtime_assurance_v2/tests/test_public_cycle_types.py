import dataclasses
import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActiveCycleResult, PublicCycleEvent, PublicCyclePhase, RoutingDecision


class PublicCycleTypesTests(unittest.TestCase):
    def test_public_types_are_frozen_and_runtime_only(self):
        for item in (RoutingDecision, ActiveCycleResult):
            self.assertTrue(item.__dataclass_params__.frozen)
        fields = {field.name for field in dataclasses.fields(ActiveCycleResult)}
        self.assertFalse(fields & {"collision", "success", "progress", "clearance", "oracle"})
        self.assertIn(PublicCyclePhase.CYCLE_BEGIN, tuple(PublicCyclePhase))
        self.assertIn(PublicCycleEvent.L1_PASS, tuple(PublicCycleEvent))


if __name__ == "__main__":
    unittest.main()
