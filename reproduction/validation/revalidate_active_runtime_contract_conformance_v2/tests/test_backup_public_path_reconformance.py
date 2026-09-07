import unittest
from ._support import stop_after_first
class TestDeferredAfterCounterexample(unittest.TestCase):
    def test_deferred_by_fail_closed_protocol(self):
        stop_after_first(self)
        self.fail("must not execute before first-counterexample gate")
