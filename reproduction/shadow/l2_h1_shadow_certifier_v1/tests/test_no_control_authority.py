import unittest

from fixtures.synthetic_fixtures import sphere_case
from l2_h1_shadow_certifier import l2_h1_shadow_certify
from shadow_contract import load_frozen_robot_margin_contract


class NoControlAuthorityTests(unittest.TestCase):
    def test_all_authorities_false_and_no_command_fields(self):
        result = l2_h1_shadow_certify(*sphere_case("safe"), load_frozen_robot_margin_contract())
        for field in ("controller_authority", "execution_authority", "candidate_selection_authority", "alternative_search_authority", "backup_authority", "terminal_authority", "fail_close_authority", "controller_intervention", "runtime_intervention"):
            self.assertFalse(getattr(result, field))
        payload = result.to_dict()
        for forbidden in ("new_control", "replacement_candidate", "execute", "stop_command", "backup_command"):
            self.assertNotIn(forbidden, payload)


if __name__ == "__main__":
    unittest.main()
