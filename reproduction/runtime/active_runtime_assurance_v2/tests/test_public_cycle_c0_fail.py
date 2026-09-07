import unittest

from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


class PublicCycleC0FailTests(unittest.TestCase):
    def test_c0_fail_never_reaches_l2(self):
        system = build_public_cycle({"primary_vector": (0.2, 0.0, 0.0)})
        _, result = start_and_run(system)
        self.assertEqual(system["counters"]["l2"], 0)
        self.assertFalse(result.committed)
        self.assertTrue(result.boundary)


if __name__ == "__main__":
    unittest.main()
