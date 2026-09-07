import unittest

from reproduction.runtime.active_runtime_assurance_v2.runtime_errors import TraceFinalizedError
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActionRole, RuntimeStateSnapshot, TraceStepRecord, make_action
from reproduction.runtime.active_runtime_assurance_v2.trace_writer import TraceWriter
from reproduction.validation.bypass_qa_trace_identity_repair_v2.canonical_trial_identity import make_arm_identity, make_canonical_trial_identity


def record(trial_id):
    snapshot = RuntimeStateSnapshot.create(trial_id, 0, (0, 0, 0, 0, 0, 0), (1, 0, 0, 0, 0, 0), "map:fixture", 0.05)
    action = make_action((0, 0, 0), ActionRole.PRIMARY_NAVIGATION, "fixture")
    return TraceStepRecord(trial_id, 0, snapshot.identity, action.role, action.identity, action.identity, "COMMITTED", ())


class TraceIdentityNegativeCases(unittest.TestCase):
    def test_snapshot_050_writer_030_must_fail(self):
        writer = TraceWriter(make_canonical_trial_identity(30).canonical_trial_id)
        with self.assertRaisesRegex(ValueError, "TRIAL_IDENTITY_MISMATCH"):
            writer.append(record(make_canonical_trial_identity(50).canonical_trial_id))

    def test_arm_encoded_writer_must_fail(self):
        canonical = make_canonical_trial_identity(50).canonical_trial_id
        writer = TraceWriter("BYPASS_050")
        with self.assertRaisesRegex(ValueError, "TRIAL_IDENTITY_MISMATCH"):
            writer.append(record(canonical))

    def test_same_trial_different_arm_metadata_passes(self):
        canonical = make_canonical_trial_identity(50).canonical_trial_id
        self.assertNotEqual(make_arm_identity("REFERENCE_CONTROL_PLANT"), make_arm_identity("ACTIVE_HARNESS_BYPASS"))
        for _arm in ("REFERENCE_CONTROL_PLANT", "ACTIVE_HARNESS_BYPASS"):
            writer = TraceWriter(canonical)
            writer.append(record(canonical))
            self.assertEqual(writer.finalize().trial_id, canonical)

    def test_append_after_finalize_must_fail(self):
        canonical = make_canonical_trial_identity(50).canonical_trial_id
        writer = TraceWriter(canonical)
        item = record(canonical)
        writer.append(item)
        writer.finalize()
        with self.assertRaisesRegex(TraceFinalizedError, "TRACE_ALREADY_FINALIZED"):
            writer.append(item)


if __name__ == "__main__":
    unittest.main()
