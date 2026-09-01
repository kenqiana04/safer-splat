#!/usr/bin/env python3
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyze_primary_endpoint import primary_summary
from analyze_secondary_endpoints import summarize_multi_candidate
from build_formal_analysis_table import AnalysisIntegrityError, join_trial
from validate_formal_analysis_v1 import prohibited_claim_hits


def fixture(status: str = "PASS", *, data_role: str = "FORMAL_PROSPECTIVE_SHADOW_COHORT_V1"):
    run_id = "formal-v1-trial-000-attempt-0"
    token = "trial-000000"
    map_id = "a" * 64
    selected_id = f"{run_id}:{token}:selected:000000"
    payload_hash = "b" * 64
    capture = {
        "run_id": run_id, "trial_id": token, "step_id": 0, "payload_sequence_id": 0,
        "state_sequence_id": f"{run_id}:{token}:state:000000",
        "decision_commit_id": f"{run_id}:{token}:commit:000000",
        "x_k": [0.0] * 6, "p_k": [0.0] * 3, "v_k": [0.0] * 3, "dt": 0.05,
        "selected_candidate": {"candidate_id": selected_id, "candidate_role": "SELECTED_EXECUTED_CONTROL", "selected_for_execution": True, "created_before_observation": True, "u": [0.1, 0.0, 0.0]},
        "nominal_reference": {"candidate_role": "NOMINAL_REFERENCE", "u": [0.2, 0.0, 0.0]},
        "native_sibling_candidates": [], "candidate_group_id": "g0", "native_candidate_group_size": 1,
        "reachability": {"decision_committed": True}, "map_authority_id": map_id,
        "payload_semantic_hash": payload_hash, "payload_worker_receive_semantic_hash": payload_hash,
    }
    result = {
        "run_id": run_id, "trial_id": token, "step_id": 0, "payload_sequence_id": 0,
        "state_sequence_id": capture["state_sequence_id"], "decision_commit_id": capture["decision_commit_id"],
        "selected_candidate_id": selected_id, "candidate_group_id": "g0", "map_authority_id": map_id,
        "payload_enqueue_semantic_hash": payload_hash, "payload_worker_receive_semantic_hash": payload_hash,
        "l1_observation_source": "SHADOW_RECOMPUTED_FROZEN_CERTIFIER", "l1_status": "PASS",
        "l2_reached": True, "l2_status": status, "l2_reason": status,
        "backend_identity": "CONSERVATIVE_SIGNED_DISTANCE_LIPSCHITZ_INTERVAL",
    }
    trace = {"trial_id": 0, "steps": [{"step_id": 0, "selected_u_k": [0.1, 0.0, 0.0], "plant_input_u": [0.1, 0.0, 0.0], "plant_input_x": [0.0] * 6, "map_authority_id": map_id}]}
    return capture, result, trace, data_role, map_id


class ContractTests(unittest.TestCase):
    def row(self, status="PASS"):
        c, r, t, role, map_id = fixture(status)
        return join_trial([c], [r], t, 0, c["run_id"], role, map_id, True)[0]

    def test_01_primary_eligibility(self):
        self.assertTrue(self.row()["primary_eligible"])

    def test_02_unknown_in_denominator(self):
        summary = primary_summary([self.row("UNKNOWN")], 1)
        self.assertEqual(summary["N_primary"], 1)
        self.assertEqual(summary["N_L2_UNKNOWN"], 1)

    def test_03_tri_state_algebra(self):
        rows = [self.row(x) for x in ("PASS", "FAIL", "UNKNOWN")]
        self.assertTrue(primary_summary(rows, 3)["tri_state_algebra_pass"])

    def test_04_u_des_not_native_alternative(self):
        row = self.row()
        self.assertEqual(row["native_sibling_candidates"], [])
        self.assertEqual(row["nominal_reference_role"], "NOMINAL_REFERENCE")

    def test_05_qa_rows_rejected(self):
        c, r, t, _, map_id = fixture(data_role="QA_EQUIVALENCE_ONLY")
        with self.assertRaises(AnalysisIntegrityError):
            join_trial([c], [r], t, 0, c["run_id"], "QA_EQUIVALENCE_ONLY", map_id, True)

    def test_06_duplicate_join_detection(self):
        c, r, t, role, map_id = fixture()
        with self.assertRaises(AnalysisIntegrityError):
            join_trial([c, c], [r], t, 0, c["run_id"], role, map_id, True)

    def test_11_known_status_secondary_only(self):
        summary = primary_summary([self.row("PASS"), self.row("FAIL"), self.row("UNKNOWN")], 3)
        self.assertEqual(summary["known_status_sensitivity_label"], "SECONDARY_SENSITIVITY_ONLY")
        self.assertEqual(summary["known_status_sensitivity"], 0.5)

    def test_12_claim_prohibited_keyword_audit(self):
        self.assertEqual(prohibited_claim_hits("measured prevalence", ["controller_efficacy"]), [])
        self.assertEqual(prohibited_claim_hits("controller_efficacy", ["controller_efficacy"]), ["controller_efficacy"])

    def test_native_multicandidate_zero_is_not_estimable(self):
        summary = summarize_multi_candidate([self.row()])
        self.assertEqual(summary["status"], "MULTI_CANDIDATE_ANALYSIS_NOT_ESTIMABLE")
        self.assertEqual(summary["synthetic_candidate_generation_count"], 0)


if __name__ == "__main__":
    unittest.main()

