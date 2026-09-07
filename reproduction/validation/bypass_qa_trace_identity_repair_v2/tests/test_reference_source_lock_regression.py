import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
ADAPTER = ROOT / "reproduction/validation/active_harness_bypass_equivalence_v2/reference_trial_adapter.py"


class ReferenceSourceLockRegressionTests(unittest.TestCase):
    def test_control_plant_termination_anchors_unchanged(self):
        source = ADAPTER.read_text(encoding="utf-8")
        for anchor in (
            "vel_des = 5.0 * (goal[:3] - x[:3])",
            "vel_des = torch.clamp(vel_des, -0.1, 0.1)",
            "u_des = 1.0 * (vel_des - x[3:])",
            "u = cbf.solve_QP(x, u_des)",
            "x = double_integrator_dynamics(x, u) * DT + x",
            "if torch.norm(x - pre) < 0.001:",
            "if cycle >= N_STEPS - 1:",
        ):
            self.assertIn(anchor, source)

    def test_single_canonical_formatter_authority(self):
        source = ADAPTER.read_text(encoding="utf-8")
        self.assertNotIn('f"stonehenge-trial-{trial_id}"', source)
        self.assertNotIn('f"stonehenge-{trial_id}"', source)
        tree = ast.parse(source)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "make_canonical_trial_identity"]
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
