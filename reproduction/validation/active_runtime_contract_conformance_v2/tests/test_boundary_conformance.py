import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CertificateStatus, DeadlineObservation, DeadlineStatus
from reproduction.runtime.active_runtime_assurance_v2.supervisor import Supervisor
from conformance_support import registry, snapshot


class BoundaryConformance(unittest.TestCase):
    def test_boundary_has_no_selected_action(self):
        reg = registry()
        decision = Supervisor(reg).arbitrate(snapshot(), None, None, None, False, None, DeadlineObservation(DeadlineStatus.OPEN, "ARB", 0, 1, "deadline:test"))
        self.assertFalse(decision.allows_commit)
        self.assertIsNone(decision.selected_action)
        self.assertEqual(decision.rule_id, "ARB_BOUNDARY")


if __name__ == "__main__":
    unittest.main()
