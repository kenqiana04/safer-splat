import unittest

from reproduction.runtime.active_runtime_assurance_v2.diagnostic_r0 import DiagnosticR0
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import snapshot


class DiagnosticR0Tests(unittest.TestCase):
    def test_diagnostic_has_no_authority(self):
        result = DiagnosticR0().inspect(snapshot())
        self.assertFalse(result.selection_authority)
        self.assertFalse(result.commit_authority)
        self.assertFalse(result.hard_gate)


if __name__ == "__main__": unittest.main()
