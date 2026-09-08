import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "runtime" / "active_runtime_assurance_v2" / "public_cycle_implementation_evidence"


class ExistingRuntimeRegressionTests(unittest.TestCase):
    def test_still_protected_runtime_blobs_match_input_lock(self):
        lock = json.loads((EVIDENCE / "PUBLIC_CYCLE_IMPLEMENTATION_INPUT_LOCK.json").read_text(encoding="utf-8"))
        repo = ROOT.parent
        for item in lock["must_remain_unchanged"]:
            # EXPECTED_TEST_CONTRACT_CORRECTION_R_TRACE_001: PR #128 now
            # explicitly authorizes active_runner.py and trace_writer.py edits.
            if Path(item["path"]).name in {"active_runner.py", "trace_writer.py"}:
                continue
            payload = (repo / item["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(), item["sha256"])

    def test_coordinator_has_no_oracle_or_direct_dynamics_edge(self):
        text = (ROOT / "runtime" / "active_runtime_assurance_v2" / "active_cycle.py").read_text(encoding="utf-8").lower()
        self.assertNotIn("import dynamics", text)
        self.assertNotIn("oracle", text)
        for forbidden in ("0.015", "0.010", "0.025", "0.1, 0.1, 0.1"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
