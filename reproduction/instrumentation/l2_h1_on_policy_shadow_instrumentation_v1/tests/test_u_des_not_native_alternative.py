"""Dedicated hard gate required by the frozen instrumentation protocol."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TASK_ROOT))

from candidate_provenance import NOMINAL_REFERENCE, SELECTED_EXECUTED_CONTROL  # noqa: E402
from immutable_payload import build_immutable_payload  # noqa: E402
from reachability_capture import baseline_commit_facts  # noqa: E402


class UDesRoleGate(unittest.TestCase):
    def test_u_des_never_inflates_native_candidate_count(self):
        payload = build_immutable_payload(
            run_id="gate", trial_id="gate", step_id=0, payload_sequence_id=0,
            x_k=(0, 0, 0, 0, 0, 0), dt=0.05,
            selected_u=(0.1, 0, 0), u_des=(0.2, 0, 0),
            selected_candidate_id="selected", selected_candidate_source="FROZEN_QP",
            map_authority_id="map", reachability=baseline_commit_facts(True),
        )
        self.assertEqual(payload.nominal_reference.candidate_role, NOMINAL_REFERENCE)
        self.assertEqual(payload.selected_candidate.candidate_role, SELECTED_EXECUTED_CONTROL)
        self.assertEqual(payload.native_candidate_group_size, 1)
        self.assertNotIn(payload.nominal_reference, payload.native_sibling_candidates)


if __name__ == "__main__":
    unittest.main()
