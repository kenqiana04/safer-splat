import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
NON_RUNTIME_SCRIPTS = {"model_check_active_runtime_implementation_v2.py", "validate_active_runtime_assurance_v2.py"}
FORBIDDEN = ("0.11", "0.10 + 0.01", "load_frozen_robot_margin_contract", "legacy task-config authority")


class NoLegacyGeometryAuthorityTests(unittest.TestCase):
    def test_runtime_modules_do_not_load_legacy_geometry_authority(self):
        violations = []
        for path in sorted(path for path in PACKAGE.glob("*.py") if path.name not in NON_RUNTIME_SCRIPTS):
            text = path.read_text(encoding="utf-8")
            for symbol in FORBIDDEN:
                if symbol in text:
                    violations.append(f"{path.name}:{symbol}")
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
