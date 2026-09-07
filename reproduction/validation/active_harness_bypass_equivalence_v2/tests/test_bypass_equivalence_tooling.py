from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import tempfile
import unittest


TASK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK))

from compare_bypass_equivalence import compare_trial, max_ulp


class BypassEquivalenceToolingTests(unittest.TestCase):
    def test_frozen_trial_geometry_source_is_locked(self):
        source = (TASK / "reference_trial_adapter.py").read_text(encoding="utf-8")
        required = [
            "t = np.linspace(0, 2 * np.pi, N)",
            "t_z = 10 * np.linspace(0, 2 * np.pi, N)",
            "radius_config = 0.784 / 2",
            "mean_config = np.array([-0.08, -0.03, 0.05])",
            "return x0[trial_id], xf[trial_id]",
        ]
        self.assertTrue(all(item in source for item in required))

    def test_float32_bits(self):
        self.assertEqual(max_ulp(["3f800000"], ["3f800001"]), 1)

    def _fixture(self, root: Path, mismatch: bool = False):
        ref, byp = root / "reference", root / "bypass"
        ref.mkdir(); byp.mkdir()
        common = {
            "trial_id": 50, "cycle_index": 0, "committed": True,
            "pre_state_bits": ["00000000"] * 6, "goal_bits": ["00000000"] * 6,
            "u_des_bits": ["00000000"] * 3, "solver_success": True,
            "reference_action": [0.0, 0.0, 0.0], "reference_action_bits": ["00000000"] * 3,
            "post_state": [0.0] * 6, "post_state_bits": (["3f800000"] + ["00000000"] * 5) if mismatch else ["00000000"] * 6,
            "native_termination_reason": "NOT_MOVING",
        }
        bypass = dict(common)
        bypass.update({
            "post_state_bits": ["00000000"] * 6,
            "supplied_action_bits": ["00000000"] * 3,
            "selected_action_bits": ["00000000"] * 3,
            "executed_action_bits": ["00000000"] * 3,
            "selected_action_id": "a", "executed_action_id": "a",
            "executed_action": [0.0, 0.0, 0.0],
            "bypass_supervisor_reason": "BYPASS_REFERENCE_ACTION_UNCHANGED",
            "commit_status": "COMMITTED",
        })
        (ref / "trial_50.jsonl").write_text(json.dumps(common) + "\n", encoding="utf-8")
        (byp / "trial_50.jsonl").write_text(json.dumps(bypass) + "\n", encoding="utf-8")
        base_summary = {"committed_step_count": 1, "termination_reason": "NOT_MOVING", "termination_step": 0}
        (ref / "trial_50_summary.json").write_text(json.dumps(base_summary), encoding="utf-8")
        byp_summary = dict(base_summary, active_intervention_call_count=0, token_mutation_count=0, plant_commit_count=1, trace_lock={"identity": "x"})
        (byp / "trial_50_summary.json").write_text(json.dumps(byp_summary), encoding="utf-8")
        return ref, byp

    def test_exact_comparator_pass(self):
        with tempfile.TemporaryDirectory() as raw:
            ref, byp = self._fixture(Path(raw))
            summary, _ = compare_trial(ref, byp, 50)
            self.assertEqual(summary["trial_verdict"], "PASS")

    def test_exact_comparator_rejects_one_bit_state_drift(self):
        with tempfile.TemporaryDirectory() as raw:
            ref, byp = self._fixture(Path(raw), mismatch=True)
            summary, _ = compare_trial(ref, byp, 50)
            self.assertEqual(summary["trial_verdict"], "FAIL")
            self.assertEqual(summary["first_mismatch"]["taxonomy"], "M_PLANT_TRANSITION_DIVERGENCE")

    def test_protocol_freeze(self):
        protocol = json.loads((TASK / "BYPASS_EQUIVALENCE_PROTOCOL_V2.json").read_text(encoding="utf-8"))
        self.assertEqual(protocol["execution_order"], [50, 10, 30, 70, 90])
        self.assertTrue(protocol["exact_float32_bit_equivalence_required"])
        self.assertFalse(protocol["active_runtime_on_allowed"])

    def test_reference_adapter_frozen_constants(self):
        source = (TASK / "reference_trial_adapter.py").read_text(encoding="utf-8")
        expected = {"N": "100", "N_STEPS": "500", "DT": "0.05", "ALPHA": "5.0", "BETA": "1.0", "RADIUS": "0.015"}
        for name, value in expected.items():
            self.assertRegex(source, rf"(?m)^{name} = {re.escape(value)}$")
        self.assertIn("TRIAL_IDS = {10, 30, 50, 70, 90}", source)


if __name__ == "__main__":
    unittest.main()
