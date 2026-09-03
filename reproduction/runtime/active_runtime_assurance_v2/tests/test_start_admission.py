import unittest

from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CertificateStatus, EvidenceResult
from reproduction.runtime.active_runtime_assurance_v2.start_admission import StartAdmission
from reproduction.runtime.active_runtime_assurance_v2.tests.helpers import snapshot


class StartAdmissionTests(unittest.TestCase):
    def test_full_query_pass(self):
        calls = []
        def query(position, map_id, radius):
            calls.append((position, map_id, radius))
            return EvidenceResult(CertificateStatus.PASS, "FULL_QUERY_SAFE", "q:1")
        result = StartAdmission(query, AuthorityRegistry.frozen("map:g3:abc", "dt:0.05")).evaluate(snapshot())
        self.assertEqual(result.status, CertificateStatus.PASS)
        self.assertEqual(calls[0][2], 0.025)

    def test_fail_has_no_repair(self):
        query = lambda *a: EvidenceResult(CertificateStatus.FAIL, "FULL_QUERY_UNSAFE", "q:2")
        result = StartAdmission(query, AuthorityRegistry.frozen("map:g3:abc", "dt:0.05")).evaluate(snapshot())
        self.assertFalse(result.repair_available)


if __name__ == "__main__": unittest.main()
