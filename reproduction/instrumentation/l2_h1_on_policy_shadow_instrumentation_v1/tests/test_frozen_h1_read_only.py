from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
SHADOW = REPO / "reproduction" / "shadow" / "l2_h1_shadow_certifier_v1"
sys.path.insert(0, str(SHADOW))

from l2_h1_shadow_certifier import propagate_h1_endpoints  # noqa: E402
from shadow_types import ShadowCandidate, ShadowState  # noqa: E402


class FrozenH1ReadOnlyTests(unittest.TestCase):
    def test_frozen_h1_is_pure_and_matches_contract(self):
        state = ShadowState((1.0, 2.0, 3.0), (0.1, 0.2, 0.3), "state", 0.05)
        candidate = ShadowCandidate((0.2, -0.1, 0.0), "selected")
        before_state = state.to_json()
        before_candidate = candidate.to_json()
        result = propagate_h1_endpoints(state, candidate, 0.05)
        self.assertEqual(state.to_json(), before_state)
        self.assertEqual(candidate.to_json(), before_candidate)
        self.assertEqual(result.p_k1, (1.005, 2.01, 3.015))
        expected_p2 = (1.0 + 0.01 + 0.0005, 2.0 + 0.02 - 0.00025, 3.0 + 0.03)
        for actual, expected in zip(result.p_k2, expected_p2):
            self.assertAlmostEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
