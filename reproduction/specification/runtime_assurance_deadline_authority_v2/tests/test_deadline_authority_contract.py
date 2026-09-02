import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("contract_rules", ROOT / "contract_rules.py")
RULES = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(RULES)


class DeadlineAuthorityContractTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((ROOT / "RUNTIME_ASSURANCE_DEADLINE_AUTHORITY_V2.json").read_text(encoding="utf-8"))

    def test_01_canonical_contract_passes(self):
        self.assertEqual(RULES.validate_contract(self.contract), [])

    def test_02_duplicate_owner_is_rejected(self):
        bad = copy.deepcopy(self.contract); bad["authority_owner_count"] = 2
        self.assertIn("GLOBAL_DEADLINE_OWNER_NOT_UNIQUE_SUPERVISOR", RULES.validate_contract(bad))

    def test_03_search_after_expiry_is_rejected(self):
        bad = copy.deepcopy(self.contract); bad["states"]["DEADLINE_EXPIRED"]["continue_search"] = True
        self.assertIn("SEARCH_AFTER_EXPIRY", RULES.validate_contract(bad))

    def test_04_warning_new_search_is_rejected(self):
        bad = copy.deepcopy(self.contract); bad["states"]["DEADLINE_WARNING"]["start_high_cost_search"] = True
        self.assertIn("HIGH_COST_SEARCH_AFTER_WARNING", RULES.validate_contract(bad))

    def test_05_uncertified_fallback_is_rejected(self):
        bad = copy.deepcopy(self.contract); bad["post_expiry_forbidden_choices"].remove("UNCERTIFIED_CANDIDATE")
        self.assertIn("UNCERTIFIED_FALLBACK_NOT_FORBIDDEN", RULES.validate_contract(bad))

    def test_06_partial_or_expired_backup_is_invalid(self):
        base = {key: True for key in ("geometry_identity_match", "actuator_authority_match", "state_identity_match", "map_authority_match", "temporal_validity", "completed_before_expiry")}
        self.assertTrue(RULES.backup_is_valid(base))
        base["completed_before_expiry"] = False
        self.assertFalse(RULES.backup_is_valid(base))

    def test_07_expiry_does_not_make_terminal_safe(self):
        self.assertFalse(RULES.terminal_is_executable({"status": "DEADLINE_EXPIRED", "completed_before_expiry": True}))
        self.assertTrue(RULES.terminal_is_executable({"status": "CERTIFIED_TERMINAL_READY", "completed_before_expiry": True}))

    def test_08_global_unknown_cannot_pass(self):
        self.assertFalse(RULES.ordinary_success_allowed("GLOBAL_DEADLINE_UNKNOWN"))

    def test_09_local_timeout_cannot_pass(self):
        self.assertFalse(RULES.ordinary_success_allowed("LOCAL_CERTIFICATE_TIMEOUT"))

    def test_10_certificate_layer_cannot_claim_owner(self):
        bad = copy.deepcopy(self.contract); bad["certificate_layer_deadline_owners"]["L2"] = True
        self.assertIn("CERTIFICATE_LAYER_CLAIMS_GLOBAL_DEADLINE", RULES.validate_contract(bad))


if __name__ == "__main__":
    unittest.main()
