#!/usr/bin/env python3
"""Synthetic-only A-Y regression matrix; no GPU or formal outcome collection."""
from __future__ import annotations

import math
import unittest

from freeze_authorities import REFERENCE_ROOT, TRIALS, read, sha
from analyze_post_repair_v3_paired_validation_v1 import decide, hard_from_clearance
from run_post_repair_v3_paired_validation_v1 import (BASE, CHECKOUT, ROOT, TASK,
                                                     protocol, smoke_module, verify_authority_manifests,
                                                     verify_protocol, verify_source_and_map)


class FrozenProtocolCPU(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = verify_protocol()
        cls.a = verify_authority_manifests()

    def test_A_exact_order(self): self.assertEqual(self.p['cohort']['trial_order'], list(TRIALS))
    def test_B_unique(self): self.assertEqual(len(set(TRIALS)), 85)
    def test_C_reference_manifest(self): self.assertEqual(self.a['reference']['inventory']['file_count'], 2138)
    def test_D_reference_85(self): self.assertEqual(len(self.a['reference_outcomes']['values']), 85)
    def test_E_repaired_head(self): self.assertEqual(BASE, '0ccec8d5eb2b4adc553767d55ba35172cb890410')
    def test_F_pilot_pass(self): self.assertEqual(self.a['pilot']['status'], 'PASS_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_PILOT_V1')
    def test_G_pilot_hard_zero(self): self.assertTrue(self.a['pilot']['continuity_hard_zero'] and self.a['pilot']['integrity_hard_zero'])
    def test_H_geometry(self): self.assertEqual(self.p['geometry']['hard_radius_q'], .015)
    def test_I_diagnostic_false(self): self.assertFalse(self.p['geometry']['historical_diagnostic_runtime_authority'])
    def test_J_synthetic_ni_pass(self): self.assertTrue(decide(integrity=True, unknown=0, active_hard=0, active_only=0, ni_lower=.01).startswith('PASS_'))
    def test_K_synthetic_ni_fail(self): self.assertEqual(decide(integrity=True, unknown=0, active_hard=0, active_only=0, ni_lower=-.03), 'FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE')
    def test_L_equal_margin_fail(self): self.assertEqual(decide(integrity=True, unknown=0, active_hard=0, active_only=0, ni_lower=-.02), 'FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE')
    def test_M_zero_hard_pass(self): self.assertTrue(decide(integrity=True, unknown=0, active_hard=0, active_only=0, ni_lower=.1).startswith('PASS_'))
    def test_N_one_hard_fail(self): self.assertEqual(decide(integrity=True, unknown=0, active_hard=1, active_only=1, ni_lower=.1), 'FAIL_POST_REPAIR_V3_HARD_SAFETY_GATE')
    def test_O_unknown_block(self): self.assertTrue(decide(integrity=True, unknown=1, active_hard=0, active_only=0, ni_lower=.1).startswith('BLOCK_'))
    def test_P_integrity_block(self): self.assertTrue(decide(integrity=False, unknown=0, active_hard=0, active_only=0, ni_lower=.1).startswith('BLOCK_'))
    def test_Q_negative_not_clamped(self): self.assertEqual(hard_from_clearance(-1e-12), 'UNSAFE')
    def test_R_witnesses(self): self.assertEqual(self.p['historical_witnesses'], [22, 28, 57, 59])
    def test_S_reference_no_rerun(self): self.assertEqual(self.a['reference']['reference_rerun_count_this_task'], 0)
    def test_T_science_not_executed(self): self.assertFalse(self.p['scientific_boundaries']['scientific_analysis_performed_during_freeze'])
    def test_U_future_root_absent(self): self.assertFalse(ROOT.exists())
    def test_V_protected_diff_zero(self): self.assertEqual(verify_source_and_map(require_lock=False, require_absent_root=True)['protected'], 'PROTECTED_RUNTIME_DIFF_ZERO')
    def test_W_map_three(self): self.assertEqual(len(smoke_module().verify_map_artifacts(self.p)), 3)
    def test_X_delegate_boundary(self): self.assertEqual(smoke_module().delegate_runtime_protocol(CHECKOUT)['trial_order'], list(TRIALS))
    def test_Y_no_runtime_side_effects(self): self.assertFalse(ROOT.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
