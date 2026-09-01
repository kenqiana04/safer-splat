#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analysis_common import semantic_sha256
from analyze_primary_endpoint import lock_payload
from bootstrap_primary_by_trial import bootstrap_by_trial
from freeze_analysis_execution_lock import combined_lock_sha


class BootstrapAndLockTests(unittest.TestCase):
    def test_07_bootstrap_deterministic_seed(self):
        rows = [{"trial_id": i, "N_primary": 2, "N_FAIL": i % 2} for i in range(100)]
        self.assertEqual(bootstrap_by_trial(rows), bootstrap_by_trial(rows))

    def test_08_cluster_by_trial_not_step(self):
        rows = [{"trial_id": i, "N_primary": 10 if i == 0 else 1, "N_FAIL": 10 if i == 0 else 0} for i in range(100)]
        out = bootstrap_by_trial(rows, valid_replicates=20)
        self.assertEqual(out["cluster_unit"], "formal_trial")
        self.assertFalse(out["step_iid_assumption"])

    def test_09_zero_denominator_redraw(self):
        rows = [{"trial_id": i, "N_primary": 0, "N_FAIL": 0} for i in range(99)] + [{"trial_id": 99, "N_primary": 1, "N_FAIL": 1}]
        out = bootstrap_by_trial(rows, valid_replicates=20, maximum_total_draws=10000)
        self.assertGreater(out["bootstrap_zero_denominator_draws"], 0)
        self.assertEqual(out["bootstrap_valid_replicates"], 20)

    def test_10_max_draw_not_estimable(self):
        rows = [{"trial_id": i, "N_primary": 0, "N_FAIL": 0} for i in range(100)]
        out = bootstrap_by_trial(rows, valid_replicates=2, maximum_total_draws=3)
        self.assertEqual(out["status"], "BOOTSTRAP_NOT_ESTIMABLE")

    def test_13_analysis_lock_deterministic(self):
        value = {"a": "1", "b": "2"}
        self.assertEqual(combined_lock_sha(value), combined_lock_sha(value))

    def test_14_primary_result_lock_deterministic(self):
        value = {"N_primary": 3, "N_L2_FAIL": 1}
        self.assertEqual(lock_payload(value), lock_payload(value))
        self.assertEqual(lock_payload(value)["primary_result_sha256"], semantic_sha256(value))


if __name__ == "__main__":
    unittest.main()
