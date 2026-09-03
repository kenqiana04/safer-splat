import ast
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
NON_RUNTIME_SCRIPTS = {"model_check_active_runtime_implementation_v2.py", "validate_active_runtime_assurance_v2.py"}


class NoOracleFeedbackImportTests(unittest.TestCase):
    def test_runtime_modules_have_no_posthoc_oracle_import(self):
        violations = []
        for path in sorted(path for path in PACKAGE.glob("*.py") if path.name not in NON_RUNTIME_SCRIPTS):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    continue
                if any("evaluation_oracle" in name or "outcome_calculator" in name for name in names):
                    violations.append(f"{path.name}:{node.lineno}")
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
