import unittest

from _support import TASK_ROOT
from fixtures.synthetic_fixtures import exploding_context, sphere_case, spoofed_context
from l2_h1_shadow_certifier import l2_h1_shadow_certify
from shadow_contract import load_frozen_robot_margin_contract
from shadow_types import ShadowL2Status


class ShadowTriStateTests(unittest.TestCase):
    def test_pass_and_fail_are_formal_only(self):
        safe = sphere_case("safe")
        unsafe = sphere_case("intersection")
        robot = load_frozen_robot_margin_contract()
        self.assertEqual(l2_h1_shadow_certify(*safe, robot).status, ShadowL2Status.PASS)
        self.assertEqual(l2_h1_shadow_certify(*unsafe, robot).status, ShadowL2Status.FAIL)

    def test_backend_exception_is_unknown(self):
        state, candidate, snapshot, _ = sphere_case("safe")
        result = l2_h1_shadow_certify(state, candidate, snapshot, exploding_context(), load_frozen_robot_margin_contract())
        self.assertEqual(result.status, ShadowL2Status.UNKNOWN)
        self.assertEqual(result.reason_code, "BACKEND_EXCEPTION")
        self.assertTrue(result.semantic_fail_closed)
        self.assertFalse(result.runtime_intervention)

    def test_spoofed_backend_identity_is_unknown(self):
        state, candidate, snapshot, _ = sphere_case("safe")
        result = l2_h1_shadow_certify(state, candidate, snapshot, spoofed_context(), load_frozen_robot_margin_contract())
        self.assertEqual(result.status, ShadowL2Status.UNKNOWN)
        self.assertEqual(result.reason_code, "FROZEN_BACKEND_SYMBOL_MISMATCH")


if __name__ == "__main__":
    unittest.main()
