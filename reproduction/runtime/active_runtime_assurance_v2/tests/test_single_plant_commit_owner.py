import ast
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
NON_RUNTIME_SCRIPTS = {"model_check_active_runtime_implementation_v2.py", "validate_active_runtime_assurance_v2.py"}


def runtime_sources():
    return sorted(path for path in PACKAGE.glob("*.py") if path.name not in NON_RUNTIME_SCRIPTS)


class SingleAuthorityOwnerTests(unittest.TestCase):
    def test_only_plant_commit_references_reference_dynamics(self):
        owners = []
        for path in runtime_sources():
            if "double_integrator_dynamics" in path.read_text(encoding="utf-8"):
                owners.append(path.name)
        self.assertEqual(owners, ["plant_commit.py"])

    def test_only_supervisor_defines_final_arbitration(self):
        owners = []
        for path in runtime_sources():
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "arbitrate":
                    owners.append(path.name)
        self.assertEqual(owners, ["supervisor.py"])


if __name__ == "__main__":
    unittest.main()
