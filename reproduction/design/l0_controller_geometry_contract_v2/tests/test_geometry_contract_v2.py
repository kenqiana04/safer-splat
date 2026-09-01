import copy
import sys
import unittest
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from validate_l0_controller_geometry_contract_v2 import validate_contract_dict  # noqa: E402


def valid_contract():
    return {
        "controller_geometry_authority": "CONTROLLER_GEOMETRY_AUTHORITY",
        "controller_radius_source": {"resolved": True, "unique": True},
        "controller_radius_m": 0.015,
        "certification_margin_policy": "PRESERVE_PREEXISTING_CERTIFICATION_MARGIN",
        "certification_margin_m": 0.01,
        "effective_l0_radius_m": 0.025,
        "composition_rule": "r_L0_eff = r_controller + m_cert",
        "margin_application_count": 1,
        "independent_l0_base_radius_m": None,
        "parameter_selection": {"sentinel_driven": False},
        "V1_reinterpretation_allowed": False,
    }


class GeometryContractV2Tests(unittest.TestCase):
    def test_controller_radius_authority_resolved_passes(self):
        self.assertEqual(validate_contract_dict(valid_contract()), [])

    def test_duplicate_base_radius_fails(self):
        contract = valid_contract()
        contract["independent_l0_base_radius_m"] = 0.10
        self.assertIn("DUPLICATE_BASE_RADIUS", validate_contract_dict(contract))

    def test_margin_double_application_fails(self):
        contract = valid_contract()
        contract["margin_application_count"] = 2
        self.assertIn("MARGIN_APPLICATION_COUNT_NOT_ONE", validate_contract_dict(contract))

    def test_sentinel_derived_parameter_selection_fails(self):
        contract = valid_contract()
        contract["parameter_selection"]["sentinel_driven"] = True
        self.assertIn("SENTINEL_DRIVEN_PARAMETER_SELECTION", validate_contract_dict(contract))

    def test_v1_reinterpretation_fails(self):
        contract = valid_contract()
        contract["V1_reinterpretation_allowed"] = True
        self.assertIn("V1_REINTERPRETATION_ALLOWED", validate_contract_dict(contract))


if __name__ == "__main__":
    unittest.main()
