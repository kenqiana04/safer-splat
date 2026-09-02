from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("logic_model", ROOT / "model_check_method_logic_v2.py")
MODEL = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODEL
SPEC.loader.exec_module(MODEL)


class MethodLogicClosureTests(unittest.TestCase):
    def test_state_totality_and_determinism(self):
        states, edges, errors = MODEL.explore()
        self.assertFalse(errors)
        keys = [(s, o) for s, o, _ in edges]
        self.assertEqual(len(keys), len(set(keys)))

    def test_all_adversarial_scenarios(self):
        results, failures = MODEL.run_scenarios()
        self.assertEqual(22, len(results))
        self.assertFalse(failures)

    def test_l1_fail_never_searches_alternatives(self):
        s = MODEL.State(phase="L1", lifecycle="RUNTIME", backup="VALID", alternatives="AVAILABLE")
        self.assertNotEqual("ALT_SEARCH", MODEL.step(s, "L1_FAIL").phase)

    def test_global_unknown_never_searches_alternatives(self):
        for phase, observation in (("C0", "C0_UNKNOWN_GLOBAL"), ("L2", "L2_UNKNOWN_GLOBAL"), ("L3", "L3_UNKNOWN_GLOBAL")):
            s = MODEL.State(phase=phase, lifecycle="RUNTIME", backup="VALID", alternatives="AVAILABLE", candidate_role="PRIMARY")
            self.assertEqual("ARBITRATION", MODEL.step(s, observation).phase)

    def test_alternative_commit_has_full_recertification(self):
        manifest = json.loads((ROOT / "ADVERSARIAL_SCENARIOS_V2.json").read_text(encoding="utf-8"))
        scenario = next(x for x in manifest["scenarios"] if x["id"] == "S04")
        state = MODEL.scenario_state(scenario["initial"])
        for obs in scenario["observations"]:
            state = MODEL.step(state, obs)
        self.assertEqual("ALTERNATIVE", state.candidate_role)
        self.assertEqual(("C0", "L2", "L3"), state.checks)
        self.assertEqual("CERTIFIED_NAVIGATION", state.action_authority)

    def test_atomic_handoff_and_recursive_token(self):
        s = MODEL.State(phase="ARBITRATION", lifecycle="RUNTIME", candidate_role="PRIMARY", c0="PASS", l1="PASS", l2="PASS", l3="WITNESS_FOUND", backup="VALID", deadline="OPEN", navigation_ready=True, new_backup_created=True, checks=("C0", "L2", "L3"), old_backup_retained=True)
        out = MODEL.step(s, "ARBITRATE")
        self.assertEqual("VALID", out.backup)
        self.assertTrue(out.old_backup_retained)
        self.assertTrue(out.new_backup_created)

    def test_guard_closes_without_new_search(self):
        s = MODEL.State(phase="ARBITRATION", lifecycle="RUNTIME", backup="NONE", deadline="GUARD_REACHED", terminal="NOT_EVALUATED")
        out = MODEL.step(s, "ARBITRATE")
        self.assertEqual("ASSURANCE_BOUNDARY", out.phase)
        self.assertEqual("OUTSIDE_METHOD", out.action_authority)

    def test_runtime_projection_is_absent(self):
        states, _, _ = MODEL.explore()
        self.assertFalse(any(s.lifecycle == "RUNTIME" and s.projection_repair for s in states))


if __name__ == "__main__":
    unittest.main()
