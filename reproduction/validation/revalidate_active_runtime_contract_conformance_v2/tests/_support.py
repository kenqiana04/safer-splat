from __future__ import annotations
import ast, dataclasses, json, unittest
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
REPO = TASK.parents[2]
RUNTIME = REPO / "reproduction/runtime/active_runtime_assurance_v2"
DESIGN = REPO / "reproduction/design/active_runtime_public_cycle_composition_v2/EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json"

def frozen_counterexample():
    path = TASK / "FIRST_COUNTEREXAMPLE_V2.json"
    return json.loads(path.read_text()) if path.exists() else None

def stop_after_first(testcase: unittest.TestCase):
    counterexample = frozen_counterexample()
    if counterexample and counterexample.get("critical", False):
        testcase.skipTest("frozen first critical counterexample stops later dynamic scenarios")

def class_methods(path: Path, class_name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {item.name for item in node.body if isinstance(item, ast.FunctionDef)}
    return set()
