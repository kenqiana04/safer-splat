import unittest

from fixtures.synthetic_fixtures import candidate_sensitivity_case
from l2_h1_shadow_certifier import l2_h1_shadow_certify
from shadow_contract import load_frozen_robot_margin_contract


class CandidateSensitivityTests(unittest.TestCase):
    def test_candidate_changes_formal_query_segment(self):
        state, a, b, snapshot, context = candidate_sensitivity_case()
        robot = load_frozen_robot_margin_contract()
        ra = l2_h1_shadow_certify(state, a, snapshot, context, robot)
        rb = l2_h1_shadow_certify(state, b, snapshot, context, robot)
        self.assertEqual(ra.segment_start, rb.segment_start)
        self.assertNotEqual(ra.segment_end, rb.segment_end)
        self.assertEqual((ra.candidate_id, rb.candidate_id), ("candidate-a", "candidate-b"))


if __name__ == "__main__":
    unittest.main()
