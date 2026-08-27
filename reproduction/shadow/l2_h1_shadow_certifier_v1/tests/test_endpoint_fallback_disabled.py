import unittest

from fixtures.synthetic_fixtures import sphere_case, unsupported_context
from l2_h1_shadow_certifier import l2_h1_shadow_certify
from shadow_contract import load_frozen_robot_margin_contract
from shadow_types import ShadowL2Status


class EndpointFallbackTests(unittest.TestCase):
    def test_unsupported_formal_backend_never_endpoint_passes(self):
        state, candidate, snapshot, _ = sphere_case("safe")
        result = l2_h1_shadow_certify(state, candidate, snapshot, unsupported_context(), load_frozen_robot_margin_contract())
        self.assertEqual(result.status, ShadowL2Status.UNKNOWN)
        self.assertEqual(result.reason_code, "UNSUPPORTED_FORMAL_BACKEND")
        self.assertFalse(result.endpoint_fallback_enabled)


if __name__ == "__main__":
    unittest.main()
