import importlib.util
import sys
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "validate_case_c_erratum.py"
SPEC = importlib.util.spec_from_file_location("validate_case_c_erratum", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def frozen_contract():
    return {
        "cluster_bootstrap": {
            "valid_replicates": 10000,
            "maximum_total_draws": 100000,
            "zero_denominator_replicate": "DISCARD_AND_REDRAW",
            "insufficient_valid_replicates": "BOOTSTRAP_NOT_ESTIMABLE",
            "cluster_unit": "formal_trial",
            "cluster_count": 100,
            "clusters_per_replicate": 100,
            "resampling": "WITH_REPLACEMENT",
            "rng_seed": 20260831,
            "step_iid_assumption": False,
            "p_value_or_significance_test": False,
        }
    }


def primary(n_primary):
    return {"N_primary": n_primary}


class CaseCAwareBootstrapTests(unittest.TestCase):
    def test_path_a_exact_target_is_accepted(self):
        bootstrap = {
            "bootstrap_valid_replicates": 10000,
            "bootstrap_total_draws": 10000,
            "bootstrap_zero_denominator_draws": 0,
            "bootstrap_ci_low": 0.01,
            "bootstrap_ci_high": 0.04,
            "bootstrap_point_estimate_check": 0.02,
            "status": "BOOTSTRAP_ESTIMABLE",
        }
        self.assertEqual(
            MODULE.evaluate_bootstrap_terminal(frozen_contract(), bootstrap, primary(12)),
            "PATH_A_ESTIMABLE",
        )

    def test_path_a_allows_redraws_before_exact_target(self):
        bootstrap = {
            "bootstrap_valid_replicates": 10000,
            "bootstrap_total_draws": 10025,
            "bootstrap_zero_denominator_draws": 25,
            "bootstrap_ci_low": 0.0,
            "bootstrap_ci_high": 0.03,
            "bootstrap_point_estimate_check": 0.01,
            "status": "BOOTSTRAP_ESTIMABLE",
        }
        self.assertEqual(
            MODULE.evaluate_bootstrap_terminal(frozen_contract(), bootstrap, primary(12)),
            "PATH_A_ESTIMABLE",
        )

    def test_path_b_is_accepted_at_max_draws(self):
        bootstrap = {
            "bootstrap_valid_replicates": 9000,
            "bootstrap_total_draws": 100000,
            "bootstrap_zero_denominator_draws": 91000,
            "bootstrap_ci_low": None,
            "bootstrap_ci_high": None,
            "bootstrap_point_estimate_check": None,
            "status": "BOOTSTRAP_NOT_ESTIMABLE",
        }
        self.assertEqual(
            MODULE.evaluate_bootstrap_terminal(frozen_contract(), bootstrap, primary(0)),
            "PATH_B_NOT_ESTIMABLE",
        )

    def test_path_b_rejects_premature_not_estimable(self):
        bootstrap = {
            "bootstrap_valid_replicates": 9000,
            "bootstrap_total_draws": 99999,
            "bootstrap_zero_denominator_draws": 90999,
            "bootstrap_ci_low": None,
            "bootstrap_ci_high": None,
            "bootstrap_point_estimate_check": None,
            "status": "BOOTSTRAP_NOT_ESTIMABLE",
        }
        with self.assertRaises(MODULE.ErratumValidationError):
            MODULE.evaluate_bootstrap_terminal(frozen_contract(), bootstrap, primary(0))


if __name__ == "__main__":
    unittest.main()
