import unittest

from reproduction.validation.bypass_qa_trace_identity_repair_v2.canonical_trial_identity import (
    FROZEN_NATIVE_TRIAL_INDICES,
    make_arm_identity,
    make_canonical_trial_identity,
)


class ReferenceBypassTrialIdentityPairingTests(unittest.TestCase):
    def test_all_frozen_trials_share_trial_identity_across_arms(self):
        for native_index in FROZEN_NATIVE_TRIAL_INDICES:
            reference = make_canonical_trial_identity(native_index)
            bypass = make_canonical_trial_identity(native_index)
            self.assertEqual(reference.canonical_trial_id, bypass.canonical_trial_id)
            self.assertNotEqual(make_arm_identity("REFERENCE_CONTROL_PLANT"), make_arm_identity("ACTIVE_HARNESS_BYPASS"))
            self.assertEqual(reference.comparison_join_key(7), (reference.canonical_trial_id, 7))
            self.assertNotIn("REFERENCE", reference.canonical_trial_id)
            self.assertNotIn("BYPASS", reference.canonical_trial_id)

    def test_unknown_trial_and_arm_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "TRIAL_ID_NOT_FROZEN"):
            make_canonical_trial_identity(11)
        with self.assertRaisesRegex(ValueError, "ARM_NOT_FROZEN"):
            make_arm_identity("SYNTHETIC")


if __name__ == "__main__":
    unittest.main()
