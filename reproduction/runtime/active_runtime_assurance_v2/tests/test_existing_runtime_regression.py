import hashlib
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = ROOT / "runtime" / "active_runtime_assurance_v2" / "public_cycle_implementation_evidence"


class ExistingRuntimeRegressionTests(unittest.TestCase):
    def test_still_protected_runtime_blobs_match_input_lock(self):
        # The PR121 input lock predates later authorized trace/plant/token edits.
        # Compare still-protected blobs to the exact Gate 0 parent instead.
        lock = json.loads((EVIDENCE / "PUBLIC_CYCLE_IMPLEMENTATION_INPUT_LOCK.json").read_text(encoding="utf-8"))
        repo = ROOT.parent
        for item in lock["must_remain_unchanged"]:
            path = item["path"]
            payload = (repo / path).read_bytes()
            gate0 = subprocess.check_output(
                ["git", "show", f"18ba8ed8aa3b4acc326426e05808bd5abe67561c:{path}"],
                cwd=repo,
            )
            self.assertEqual(hashlib.sha256(payload).hexdigest(), hashlib.sha256(gate0).hexdigest())

    def test_coordinator_has_no_oracle_or_direct_dynamics_edge(self):
        text = (ROOT / "runtime" / "active_runtime_assurance_v2" / "active_cycle.py").read_text(encoding="utf-8").lower()
        self.assertNotIn("import dynamics", text)
        self.assertNotIn("oracle", text)
        for forbidden in ("0.015", "0.010", "0.025", "0.1, 0.1, 0.1"):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
