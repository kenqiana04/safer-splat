import unittest

from reproduction.validation.revalidate_active_runtime_contract_conformance_v2_post_r2.run_post_r2_reconformance_v2 import scenario_definitions


class CompleteIndependentPostR2ReconformanceTests(unittest.TestCase):
    def test_complete_independent_matrix(self):
        for scenario_id, _domain, function in scenario_definitions():
            with self.subTest(scenario=scenario_id):
                detail = function()
                self.assertTrue(detail.pop("passed"), detail)


if __name__ == "__main__":
    unittest.main(failfast=False)

