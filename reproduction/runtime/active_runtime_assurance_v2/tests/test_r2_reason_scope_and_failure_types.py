import dataclasses
import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    AlternativeInventoryStatus,
    CertificateStatus,
    PublicCycleEvent,
    ReasonScope,
    StageFailureEvidence,
    StageFailureKind,
)
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run


class R2ReasonScopeAndFailureTypeTests(unittest.TestCase):
    def test_failure_and_inventory_types_are_distinct_and_immutable(self):
        self.assertEqual(ReasonScope.UNRESOLVED_SCOPE.value, "UNRESOLVED_SCOPE")
        self.assertEqual(StageFailureKind.STAGE_EXCEPTION.value, "STAGE_EXCEPTION")
        self.assertNotEqual(AlternativeInventoryStatus.SOURCE_INVALID.value, PublicCycleEvent.ALT_EXHAUSTED.value)
        self.assertNotEqual(AlternativeInventoryStatus.PROVENANCE_MISSING.value, PublicCycleEvent.ALT_EXHAUSTED.value)
        self.assertTrue(dataclasses.is_dataclass(StageFailureEvidence))
        self.assertTrue(StageFailureEvidence.__dataclass_params__.frozen)

    def test_reason_scope_uses_exact_codes_not_substrings(self):
        supervisor = build_public_cycle()["supervisor"]
        cases = {
            ("L1", "MAP_IDENTITY_MISMATCH"): ReasonScope.GLOBAL_AUTHORITY_OR_EVIDENCE,
            ("L2", "L2_BACKEND_EXCEPTION:RuntimeError"): ReasonScope.INFRASTRUCTURE_HEALTH,
            ("C0", "CANDIDATE_NONFINITE_OR_WRONG_DIMENSION"): ReasonScope.CANDIDATE_LOCAL_COMPUTATION,
            ("L3", "opaque missing token"): ReasonScope.UNRESOLVED_SCOPE,
            ("L2", "opaque timeout token"): ReasonScope.UNRESOLVED_SCOPE,
        }
        for (stage, reason), expected in cases.items():
            with self.subTest(stage=stage, reason=reason):
                self.assertEqual(supervisor.classify_reason_scope(stage, reason), expected)

    def test_no_semantic_collapse(self):
        self.assertNotEqual(StageFailureKind.STAGE_EXCEPTION.value, "FAIL")
        self.assertNotEqual(PublicCycleEvent.TERMINAL_UNKNOWN, PublicCycleEvent.TERMINAL_MEMBER_NOT_ELIGIBLE)
        self.assertNotEqual(ReasonScope.UNRESOLVED_SCOPE, ReasonScope.CANDIDATE_LOCAL_COMPUTATION)

    def test_returned_unknown_is_preserved_as_typed_evidence(self):
        system = build_public_cycle({"l1": CertificateStatus.UNKNOWN})
        _, result = start_and_run(system)
        self.assertTrue(result.stage_failures)
        self.assertEqual(result.stage_failures[0].failure_kind, StageFailureKind.STAGE_UNKNOWN)
        self.assertEqual(result.stage_failures[0].reason_scope, ReasonScope.UNRESOLVED_SCOPE)


if __name__ == "__main__":
    unittest.main()
