import unittest

from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


class PublicCycleTraceTests(unittest.TestCase):
    def test_exactly_one_trace_for_each_resolved_cycle(self):
        for config in ({}, {"proposal": "FAIL"}):
            system = build_public_cycle(config)
            _, result = start_and_run(system)
            self.assertEqual(len(system["trace_writer"].records), 1)
            self.assertIsNotNone(result.trace_ref)

    def test_finalize_returns_immutable_trace_lock(self):
        system = build_public_cycle()
        start_and_run(system)
        first = system["coordinator"].finalize_trial()
        with self.assertRaises(Exception):
            system["coordinator"].finalize_trial()
        self.assertEqual(first.record_count, 1)


if __name__ == "__main__":
    unittest.main()
