from __future__ import annotations

import importlib.util
import json
import re
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("freeze_protocol", ROOT / "freeze_protocol.py")
freeze_protocol = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(freeze_protocol)


class ProtocolContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        freeze_protocol.freeze(ROOT)
        cls.manifest = json.loads((ROOT / "formal_trial_manifest.json").read_text(encoding="utf-8"))
        cls.analysis = json.loads((ROOT / "formal_analysis_contract.json").read_text(encoding="utf-8"))
        cls.join = json.loads((ROOT / "formal_identity_join_contract.json").read_text(encoding="utf-8"))
        cls.exclusion = json.loads((ROOT / "formal_exclusion_contract.json").read_text(encoding="utf-8"))

    def test_official100_exactly_100_unique_ids(self) -> None:
        rows, source_hash = freeze_protocol.load_official100()
        self.assertEqual(source_hash, freeze_protocol.OFFICIAL_MANIFEST_SHA256)
        self.assertEqual([row["trial_id"] for row in rows], list(range(100)))
        self.assertEqual(self.manifest["trial_count"], 100)

    def test_qa_data_roles_are_hard_excluded(self) -> None:
        self.assertEqual(set(self.exclusion["hard_rejected_data_roles"]), set(freeze_protocol.QA_ROLES))
        self.assertTrue(self.exclusion["qa_exclusion_is_permanent"])

    def test_formal_run_ids_are_unique_and_disjoint_from_qa(self) -> None:
        formal_ids = [row["attempt_0_run_id"] for row in self.manifest["trials"]]
        self.assertEqual(len(formal_ids), len(set(formal_ids)) == 100 and 100)
        self.assertTrue(all(re.fullmatch(freeze_protocol.FORMAL_RUN_PATTERN, value) for value in formal_ids))
        self.assertFalse(set(formal_ids) & set(self.exclusion["hard_rejected_qa_run_ids"]))
        for trial_id in freeze_protocol.PILOT_IDS:
            self.assertEqual(formal_ids[trial_id], f"formal-v1-trial-{trial_id:03d}-attempt-0")

    def test_primary_algebra(self) -> None:
        counts = freeze_protocol.primary_counts(["PASS", "FAIL", "UNKNOWN", "FAIL"])
        self.assertEqual(counts["N_primary"], counts["N_L2_PASS"] + counts["N_L2_FAIL"] + counts["N_L2_UNKNOWN"])
        self.assertEqual(counts["prospective_future_safety_signal_rate"], 0.5)

    def test_unknown_is_in_primary_denominator(self) -> None:
        counts = freeze_protocol.primary_counts(["PASS", "UNKNOWN"])
        self.assertEqual(counts["N_primary"], 2)
        self.assertEqual(counts["N_L2_UNKNOWN"], 1)
        self.assertTrue(self.analysis["unknown_in_primary_denominator"])

    def test_u_des_is_not_native_alternative(self) -> None:
        self.assertEqual(self.analysis["candidate_roles"]["u_des"], "NOMINAL_REFERENCE")
        self.assertFalse(self.analysis["multi_candidate_contract"]["u_des_is_native_alternative"])
        self.assertEqual(self.analysis["multi_candidate_contract"]["synthetic_candidate_generation_count"], 0)

    def test_join_key_is_frozen_from_pr99_semantics(self) -> None:
        required = {"run_id", "process_local_trial_token", "step_id", "state_sequence_id", "decision_commit_id", "payload_sequence_id", "selected_candidate_id", "map_authority_id"}
        self.assertTrue(required.issubset(self.join["capture_result_join_key"]))
        self.assertTrue(self.join["official_trial_identity"]["not_equal_to_process_local_token_by_assumption"])
        self.assertEqual(self.join["change_after_first_formal_run"], "STOP_V1_AND_CREATE_PROTOCOL_V2")

    def test_protocol_bundle_sha_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            lock_a = freeze_protocol.freeze(Path(first))
            lock_b = freeze_protocol.freeze(Path(second))
            self.assertEqual(lock_a["combined_protocol_sha256"], lock_b["combined_protocol_sha256"])
            for name in freeze_protocol.LOCKABLE_FILES:
                self.assertEqual((Path(first) / name).read_bytes(), (Path(second) / name).read_bytes())

    def test_outcome_blind_qc_does_not_expose_scientific_summary(self) -> None:
        contract = json.loads((ROOT / "outcome_blind_qc_contract.json").read_text(encoding="utf-8"))
        self.assertIn("l2_status_field_presence_and_type_only", contract["allowed_checks"])
        self.assertIn("PASS_FAIL_UNKNOWN_DISTRIBUTION", contract["forbidden_collection_outputs"])
        self.assertFalse(contract["collection_task_may_analyze_scientific_outcomes"])

    def test_retry_only_before_data(self) -> None:
        legal = {
            "failure_class": "PRE_DATA_INFRA_FAILURE", "intended_step_count": 0,
            "formal_capture_count": 0, "formal_l2_result_count": 0, "scientific_row_count": 0,
            "failure_recorded": True, "same_trial_id": True, "fresh_process": True,
            "attempt_id_increment": 1, "prior_retry_count": 0,
        }
        self.assertTrue(freeze_protocol.pre_data_retry_allowed(legal))
        illegal = dict(legal, intended_step_count=1)
        self.assertFalse(freeze_protocol.pre_data_retry_allowed(illegal))

    def test_raw_log_git_exclusion(self) -> None:
        retention = json.loads((ROOT / "formal_artifact_retention_policy.json").read_text(encoding="utf-8"))
        self.assertEqual(retention["raw_log_files_committed_to_git"], 0)
        self.assertEqual(set(retention["git_forbidden_suffixes"]), {".jsonl", ".log"})

    def test_bootstrap_configuration_is_frozen(self) -> None:
        config = self.analysis["cluster_bootstrap"]
        self.assertEqual(config["cluster_count"], 100)
        self.assertEqual(config["valid_replicates"], 10000)
        self.assertEqual(config["rng_seed"], 20260831)
        self.assertFalse(config["step_iid_assumption"])


if __name__ == "__main__":
    unittest.main()
