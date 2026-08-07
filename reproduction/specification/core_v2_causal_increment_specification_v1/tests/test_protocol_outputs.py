"""Protocol-level tests for the specification artifacts."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parents[1]


class CoreV2SpecificationTests(unittest.TestCase):
    def test_validator_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", str(TASK_ROOT / "validate_core_v2_causal_increment_spec.py")],
            cwd=TASK_ROOT.parents[2],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS_CORE_V2_CAUSAL_INCREMENT_SPECIFICATION_VALIDATION", result.stdout)


if __name__ == "__main__":
    unittest.main()
