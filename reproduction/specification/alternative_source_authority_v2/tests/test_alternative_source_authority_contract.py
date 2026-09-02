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


def valid_candidate():
    return {
        "candidate_id": "native-001",
        "source_type": "SOURCE_NATIVE_EXISTING",
        "creation_timestamp": "cycle-4/pre-alt",
        "state_identity": "state-4",
        "map_identity": "map-sha",
        "actuator_authority": "NORMATIVE_COMPONENTWISE_ACCELERATION_AUTHORITY_V2",
        "controller_identity": "controller-sha",
        "existed_before_alternative_request": True,
    }


class AlternativeSourceAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.contract = json.loads((ROOT / "ALTERNATIVE_SOURCE_AUTHORITY_V2.json").read_text(encoding="utf-8"))
        self.taxonomy = json.loads((ROOT / "ALTERNATIVE_SOURCE_TAXONOMY_V2.json").read_text(encoding="utf-8"))
        self.chain = json.loads((ROOT / "ALTERNATIVE_RECERTIFICATION_CHAIN_V2.json").read_text(encoding="utf-8"))

    def test_01_canonical_contract_passes(self):
        self.assertEqual(RULES.validate_contract(self.contract, self.taxonomy, self.chain), [])

    def test_02_single_authority_owner(self):
        bad = copy.deepcopy(self.contract); bad["search_authority_owner_count"] = 2
        self.assertIn("ALTERNATIVE_SEARCH_OWNER_NOT_UNIQUE_SUPERVISOR", RULES.validate_contract(bad, self.taxonomy, self.chain))

    def test_03_provenance_completeness(self):
        candidate = valid_candidate(); del candidate["map_identity"]
        self.assertIn("MISSING_MAP_IDENTITY", RULES.candidate_provenance_errors(candidate))

    def test_04_no_synthetic_or_outcome_conditioned_generation(self):
        bad = copy.deepcopy(self.taxonomy); bad["sources"]["SOURCE_SYNTHETIC"]["authorized_by_default"] = True
        bad["prohibited_generation_methods"].remove("OUTCOME_CONDITIONED_GENERATION")
        errors = RULES.validate_contract(self.contract, bad, self.chain)
        self.assertIn("SYNTHETIC_SOURCE_NOT_FORBIDDEN", errors)
        self.assertIn("OUTCOME_OR_SYNTHETIC_GENERATION_NOT_FULLY_FORBIDDEN", errors)

    def test_05_identity_change_requires_new_candidate_id(self):
        old = valid_candidate(); new = copy.deepcopy(old); new["state_identity"] = "state-5"
        self.assertFalse(RULES.identity_update_is_valid(old, new))
        new["candidate_id"] = "native-002"
        self.assertTrue(RULES.identity_update_is_valid(old, new))

    def test_06_mandatory_fresh_recertification(self):
        bad = copy.deepcopy(self.chain); bad["chain"][1]["fresh_result_required"] = False
        self.assertIn("FRESH_RECERTIFICATION_NOT_MANDATORY", RULES.validate_contract(self.contract, self.taxonomy, bad))

    def test_07_deadline_compatibility(self):
        self.assertTrue(RULES.request_allowed("DEADLINE_OPEN"))
        self.assertFalse(RULES.request_allowed("DEADLINE_WARNING"))
        self.assertFalse(RULES.request_allowed("DEADLINE_EXPIRED"))

    def test_08_actuator_compatibility(self):
        candidate = valid_candidate(); candidate["actuator_authority"] = "LAYER_LOCAL_BOUNDS"
        self.assertIn("ACTUATOR_AUTHORITY_MISMATCH", RULES.candidate_provenance_errors(candidate))

    def test_09_backup_dual_role_compatibility(self):
        record = {"source_type": "SOURCE_NATIVE_EXISTING", "geometry_identity_match": True, "actuator_authority_match": True, "map_authority_match": True, "state_identity_match": True, "fresh_c0_l1_l2_l3": True}
        self.assertTrue(RULES.backup_dual_role_compatible(record))
        record["map_authority_match"] = False
        self.assertFalse(RULES.backup_dual_role_compatible(record))

    def test_10_unknown_source_is_not_success(self):
        self.assertFalse(RULES.ordinary_success_allowed("UNKNOWN_SOURCE"))
        candidate = valid_candidate(); candidate["source_type"] = "UNRECOGNIZED"
        self.assertIn("SOURCE_NOT_AUTHORIZED", RULES.candidate_provenance_errors(candidate))


if __name__ == "__main__":
    unittest.main()
