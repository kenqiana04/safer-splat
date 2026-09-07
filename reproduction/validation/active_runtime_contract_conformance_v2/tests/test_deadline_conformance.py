import unittest

from reproduction.runtime.active_runtime_assurance_v2.deadline_runtime import DeadlineTracker, DeadlineStatus, FakeClock
from conformance_support import profile


class DeadlineConformance(unittest.TestCase):
    def test_open_warning_expired_are_observations(self):
        clock = FakeClock(0)
        tracker = DeadlineTracker(profile(), clock)
        tracker.start()
        self.assertEqual(tracker.observe("L1").status, DeadlineStatus.OPEN)
        clock.advance(0.81)
        self.assertEqual(tracker.observe("L2").status, DeadlineStatus.WARNING)
        clock.advance(0.1)
        self.assertEqual(tracker.observe("ARB").status, DeadlineStatus.EXPIRED)


if __name__ == "__main__":
    unittest.main()
