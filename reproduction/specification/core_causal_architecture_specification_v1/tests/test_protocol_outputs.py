from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProtocolOutputTests(unittest.TestCase):
    def test_validator_passes(self):
        result = subprocess.run(
            [sys.executable, "-B", str(ROOT / "validate_core_causal_architecture_spec.py")],
            cwd=ROOT.parents[2], text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS_CORE_CAUSAL_ARCHITECTURE_SPECIFICATION_VALIDATION", result.stdout)


if __name__ == "__main__":
    unittest.main()
