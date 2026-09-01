import math
import sys
import unittest
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from validate_l0_start_safe_failure_diagnosis_v1 import (  # noqa: E402
    barrier_from_signed_squared_clearance,
    effective_radius,
    local_coordinates,
    path_is_task_local,
    sentinel_indices,
    status_from_h,
)


class DiagnosisContractTests(unittest.TestCase):
    def test_barrier_sign_contract(self):
        self.assertLess(barrier_from_signed_squared_clearance(-0.002, 0.11), 0.0)
        self.assertEqual(barrier_from_signed_squared_clearance(0.0121, 0.11), 0.0)
        self.assertGreater(barrier_from_signed_squared_clearance(0.02, 0.11), 0.0)

    def test_radius_margin_accounting(self):
        self.assertAlmostEqual(effective_radius(0.10, 0.01), 0.11)
        self.assertAlmostEqual(effective_radius(0.10, 0.01) ** 2, 0.0121)

    def test_frame_transform_direction_identity_fixture(self):
        identity = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0))
        self.assertEqual(local_coordinates((3, 4, 5), (1, 1, 1), identity), (2.0, 3.0, 4.0))

    def test_sentinel_selection_deterministic(self):
        self.assertEqual(sentinel_indices(318), (0, 158, 317))
        self.assertEqual(sentinel_indices(43), (0, 21, 42))

    def test_sentinel_status_equals_h_sign(self):
        self.assertEqual(status_from_h(-1e-6), "FAIL")
        self.assertEqual(status_from_h(0.0), "PASS")
        self.assertEqual(status_from_h(math.nan), "UNKNOWN")

    def test_no_scientific_v1_mutation_path(self):
        self.assertTrue(path_is_task_local("reproduction/diagnosis/l0_start_safe_failure_semantics_v1/README.md"))
        self.assertFalse(path_is_task_local("run.py"))


if __name__ == "__main__":
    unittest.main()
