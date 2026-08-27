import unittest
from dataclasses import replace

from fixtures.synthetic_fixtures import sphere_case
from l2_h1_shadow_certifier import l2_h1_shadow_certify
from shadow_contract import load_frozen_robot_margin_contract
from shadow_types import ExpectedMapSnapshot, ShadowL2Status


class MapSnapshotContractTests(unittest.TestCase):
    def test_snapshot_mismatch_is_unknown_not_fail(self):
        state, candidate, _, context = sphere_case("safe")
        expected = ExpectedMapSnapshot("different", "different-hash")
        result = l2_h1_shadow_certify(state, candidate, expected, context, load_frozen_robot_margin_contract())
        self.assertEqual(result.status, ShadowL2Status.UNKNOWN)
        self.assertEqual(result.reason_code, "MAP_SNAPSHOT_MISMATCH")
        self.assertEqual(result.actual_map_snapshot_id, context.actual_map_snapshot_id)

    def test_hash_stale_and_unresolved_are_distinct_unknowns(self):
        state, candidate, expected, context = sphere_case("safe")
        robot = load_frozen_robot_margin_contract()
        cases = [
            (replace(context, actual_map_snapshot_sha256="wrong"), "MAP_HASH_MISMATCH"),
            (replace(context, snapshot_is_stale=True), "MAP_SNAPSHOT_STALE"),
            (replace(context, query_context_resolved=False), "MAP_QUERY_CONTEXT_UNRESOLVED"),
        ]
        for modified, reason in cases:
            result = l2_h1_shadow_certify(state, candidate, expected, modified, robot)
            self.assertEqual(result.status, ShadowL2Status.UNKNOWN)
            self.assertEqual(result.reason_code, reason)


if __name__ == "__main__":
    unittest.main()
