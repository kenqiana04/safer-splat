from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from inventory_sources import replayability, stored_l1  # noqa: E402


class InventoryContractTests(unittest.TestCase):
    def test_missing_candidate_is_not_replayable_not_unknown(self):
        row = {"p_k": [0, 0, 0], "v_k": [0, 0, 0], "u_k": None, "candidate_id": "id", "map_snapshot_id": "m", "map_content_sha256": "h", "dt": 0.05, "backend_identity": "b"}
        classification, reasons = replayability(row)
        self.assertEqual(classification, "NOT_REPLAYABLE")
        self.assertIn("MISSING_U_K", reasons)

    def test_primary_lower_bound_freezes_stored_l1(self):
        self.assertEqual(stored_l1({"segment_lower_bound": "0.0"}, "PRIMARY-CBF-FILTERED", False)[0], "PASS")
        self.assertEqual(stored_l1({"segment_lower_bound": "-1e-12"}, "PRIMARY-CBF-FILTERED", False)[0], "FAIL")

    def test_logged_but_unevaluated_alternative_is_not_l2_reached(self):
        status, origin = stored_l1({}, "ALT-01-OUTWARD", False, {})
        self.assertEqual(status, "NOT_AVAILABLE")
        self.assertEqual(origin, "CANDIDATE_LOGGED_NOT_EVALUATED")


if __name__ == "__main__":
    unittest.main()
