import tempfile
import unittest
from pathlib import Path

from reproduction.runtime.active_runtime_assurance_v2.runtime_errors import TraceFinalizedError
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActionRole, TraceStepRecord
from reproduction.runtime.active_runtime_assurance_v2.trace_writer import TraceWriter
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import snapshot


class TraceWriterTests(unittest.TestCase):
    def test_finalize_is_content_addressed_and_immutable(self):
        with tempfile.TemporaryDirectory() as tmp:
            writer=TraceWriter("trial-1",Path(tmp))
            state=snapshot()
            writer.append(TraceStepRecord("trial-1",0,state.identity,ActionRole.ASSURANCE_BOUNDARY_NO_ACTION,None,None,"NO_ACTION",(("reason","test"),)))
            lock=writer.finalize()
            self.assertTrue(lock.locked_before_evaluation)
            with self.assertRaises(TraceFinalizedError): writer.append(TraceStepRecord("trial-1",1,state.identity,ActionRole.ASSURANCE_BOUNDARY_NO_ACTION,None,None,"NO_ACTION",()))

    def test_outcome_fields_forbidden(self):
        writer=TraceWriter("trial-1")
        state=snapshot()
        with self.assertRaises(ValueError): writer.append(TraceStepRecord("trial-1",0,state.identity,ActionRole.ASSURANCE_BOUNDARY_NO_ACTION,None,None,"NO_ACTION",(("collision",False),)))


if __name__ == "__main__": unittest.main()
