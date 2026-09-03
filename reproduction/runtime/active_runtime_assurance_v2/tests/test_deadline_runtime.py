import unittest

from reproduction.runtime.active_runtime_assurance_v2.deadline_runtime import DeadlineTracker, FakeClock, RuntimeDeadlineProfile
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import DeadlineStatus


class DeadlineRuntimeTests(unittest.TestCase):
    def test_open_warning_expired(self):
        profile = RuntimeDeadlineProfile.create(10.0, (("L2", 2.0),), 2.0, 9.0, "fake-clock")
        clock = FakeClock(100.0)
        tracker = DeadlineTracker(profile, clock)
        tracker.start()
        self.assertEqual(tracker.observe("C0").status, DeadlineStatus.OPEN)
        clock.advance(7.5)
        self.assertEqual(tracker.observe("L2").status, DeadlineStatus.WARNING)
        clock.advance(1.5)
        self.assertEqual(tracker.observe("ARBITRATION").status, DeadlineStatus.EXPIRED)

    def test_profile_is_explicit_not_dt_derived(self):
        profile = RuntimeDeadlineProfile.create(1.0, (), 0.1, 0.9, "fake")
        self.assertEqual(profile.cycle_deadline_duration, 1.0)


if __name__ == "__main__": unittest.main()
