from __future__ import annotations

import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from arm_activation_validator import validate  # noqa: E402
from compare_traces import compare  # noqa: E402


def trace(value: float = 0.1) -> dict:
    return {
        "run_id": "run",
        "trial_id": 0,
        "seed": 0,
        "map_authority_id": "map",
        "steps": [{
            "trial_id": 0, "step_id": 0, "seed": 0,
            "x_k": [0.0] * 6, "u_des": [0.1] * 3, "selected_u_k": [value] * 3,
            "solver_success": True, "controller_branch": "SOLVER_SUCCESS_PLANT",
            "plant_input_x": [0.0] * 6, "plant_input_u": [value] * 3,
            "plant_output_x_next": [0.0, 0.0, 0.0, value, value, value],
            "termination_flag": False, "termination_reason": "CONTINUE",
            "goal": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "goal_terminal_status": "NOT_TERMINAL", "map_authority_id": "map",
        }],
    }


class EquivalenceToolsTest(unittest.TestCase):
    def test_exact_match(self):
        result = compare(trace(), trace(), "A_VS_B")
        self.assertTrue(result["exact_match"])
        self.assertIsNone(result["first_divergence"])

    def test_first_divergence(self):
        result = compare(trace(), trace(0.2), "B_VS_C")
        self.assertFalse(result["exact_match"])
        self.assertEqual(result["first_divergence"]["step_id"], 0)
        self.assertEqual(result["first_divergence"]["field"], "selected_u_k")

    def test_arm_activation_contracts(self):
        base = {
            "controller_authority": False, "controller_intervention_count": 0,
            "selected_candidate_replacement_count": 0, "leftover_shadow_worker_count": 0,
            "intended_state_valid": True,
        }
        a = {**base, "arm": "NATIVE_OFF", "wrapper_loaded": False, "worker_ident_after_start": None, "capture_log_count": 0, "certificate_result_count": 0}
        b = {**base, "arm": "WRAPPER_OFF", "wrapper_loaded": True, "wrapper_factory_trial_count": 1, "observer_enabled": False, "worker_ident_after_start": None, "certificate_result_count": 0}
        c = {**base, "arm": "WRAPPER_ON", "wrapper_loaded": True, "wrapper_factory_trial_count": 1, "observer_enabled": True, "worker_ident_after_start": 123, "capture_log_count": 1, "certificate_result_count": 1, "worker_processed_count": 1, "worker_alive_after_shutdown": False}
        self.assertTrue(validate(a)[0])
        self.assertTrue(validate(b)[0])
        self.assertTrue(validate(c)[0])


if __name__ == "__main__":
    unittest.main()
