import ast
import hashlib
import inspect
import json
import unittest
from pathlib import Path

from reproduction.runtime.active_runtime_assurance_v2.active_runner import ActiveRunner

ROOT = Path(__file__).resolve().parents[3]
LOCK = ROOT / "runtime" / "active_runtime_assurance_v2" / "public_cycle_implementation_evidence" / "PUBLIC_CYCLE_IMPLEMENTATION_INPUT_LOCK.json"
SUPERVISOR = ROOT / "runtime" / "active_runtime_assurance_v2" / "supervisor.py"


def method_hash(method_name):
    source = SUPERVISOR.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Supervisor":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == method_name:
                    segment = ast.get_source_segment(source, item) or ""
                    return {
                        "source_sha256": hashlib.sha256(segment.encode()).hexdigest(),
                        "ast_sha256": hashlib.sha256(ast.dump(item, annotate_fields=True, include_attributes=False).encode()).hexdigest(),
                    }
    raise AssertionError(method_name)


class BypassSemanticsPreservedTests(unittest.TestCase):
    def test_bypass_dependency_methods_are_unchanged(self):
        locked = json.loads(LOCK.read_text(encoding="utf-8"))["supervisor_method_identities"]
        for name in ("bypass_decision", "certify_candidate"):
            self.assertEqual(method_hash(name), locked[name])

    def test_bypass_path_does_not_call_changed_active_routing_or_arbitration(self):
        source = inspect.getsource(ActiveRunner.commit_bypass)
        self.assertIn("self.supervisor.bypass_decision", source)
        self.assertNotIn("route_transition", source)
        self.assertNotIn("arbitrate", source)


if __name__ == "__main__":
    unittest.main()
