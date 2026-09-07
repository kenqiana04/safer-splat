import unittest

from reproduction.runtime.active_runtime_assurance_v2.trace_writer import TraceWriter
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActionRole, TraceStepRecord
from conformance_support import snapshot, action


class ActiveTraceConformance(unittest.TestCase):
    def test_trace_is_immutable_and_has_no_outcome_fields(self):
        state = snapshot()
        writer = TraceWriter("cpu-conformance")
        act = action()
        writer.append(TraceStepRecord("cpu-conformance", 0, state.identity, act.role, act.identity, act.identity, "COMMITTED", (("runtime_reason", "CPU"),)))
        lock = writer.finalize()
        self.assertTrue(lock.locked_before_evaluation)
        with self.assertRaises(Exception):
            writer.append(TraceStepRecord("cpu-conformance", 1, state.identity, ActionRole.ASSURANCE_BOUNDARY_NO_ACTION, None, None, "NO_ACTION", (("outcome", "forbidden"),)))


if __name__ == "__main__":
    unittest.main()
