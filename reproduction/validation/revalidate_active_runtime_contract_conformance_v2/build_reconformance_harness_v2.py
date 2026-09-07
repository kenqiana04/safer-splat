"""Build the frozen CPU-only Active Runtime V2 reconformance harness.

This script writes only task-local manifests and tests.  It never mutates runtime
or production source and never performs a rollout.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
from pathlib import Path


TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
RUNTIME = REPO / "reproduction/runtime/active_runtime_assurance_v2"
PR107 = REPO / "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv"
PR120 = REPO / "reproduction/validation/active_runtime_contract_conformance_v2"
PR121 = REPO / "reproduction/design/active_runtime_public_cycle_composition_v2"
PR122 = RUNTIME / "public_cycle_implementation_evidence"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    rel = path.relative_to(REPO).as_posix()
    return subprocess.run(
        ["git", "hash-object", rel], cwd=REPO, check=True, text=True, capture_output=True
    ).stdout.strip()


def identity(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(REPO).as_posix(),
        "sha256": sha256(path),
        "git_blob_sha1": git_blob(path),
        "size": path.stat().st_size,
    }


def method_identity(path: Path, class_name: str, method_name: str) -> dict[str, str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == method_name:
                    segment = ast.get_source_segment(source, item) or ""
                    return {
                        "source_sha256": hashlib.sha256(segment.encode()).hexdigest(),
                        "ast_sha256": hashlib.sha256(
                            ast.dump(item, annotate_fields=True, include_attributes=False).encode()
                        ).hexdigest(),
                    }
    raise RuntimeError(f"missing {class_name}.{method_name}")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def build_input_lock() -> None:
    old_lock = json.loads((PR120 / "ACTIVE_CONFORMANCE_INPUT_LOCK.json").read_text(encoding="utf-8"))
    implementation_lock = json.loads((PR122 / "PUBLIC_CYCLE_IMPLEMENTATION_INPUT_LOCK.json").read_text(encoding="utf-8"))
    contract_paths = {
        "pr107_transition": PR107,
        "pr108_geometry": REPO / "reproduction/specification/cross_layer_geometry_authority_v2/CROSS_LAYER_GEOMETRY_AUTHORITY_V2.json",
        "pr109_actuator": REPO / "reproduction/specification/control_authority_v2/SELECTED_CONTROL_ACTUATOR_CONTRACT_V2.json",
        "pr110_deadline": REPO / "reproduction/specification/runtime_assurance_deadline_authority_v2/RUNTIME_ASSURANCE_DEADLINE_AUTHORITY_V2.json",
        "pr111_alternative": REPO / "reproduction/specification/alternative_source_authority_v2/ALTERNATIVE_SOURCE_AUTHORITY_V2.json",
        "pr112_backup": REPO / "reproduction/specification/backup_token_runtime_schema_v2/RETAINED_BACKUP_TOKEN_SCHEMA_V2.json",
        "pr113_terminal": REPO / "reproduction/specification/terminal_emergency_policy_v2/TERMINAL_EMERGENCY_POLICY_CONTRACT_V2.json",
        "pr114_oracle": REPO / "reproduction/specification/independent_evaluation_oracle_v2/EVALUATION_TRACE_SCHEMA_V2.json",
        "pr115_architecture": REPO / "reproduction/design/active_runtime_assurance_implementation_v2/MODULE_ARCHITECTURE_V2.json",
        "pr119_bypass_evidence": REPO / "reproduction/validation/execute_refrozen_bypass_equivalence_v2r1/BYPASS_EQUIVALENCE_V2R1_SUMMARY.json",
        "pr120_blocker": PR120 / "FINAL_DECISION.json",
        "pr121_design": PR121 / "PUBLIC_CYCLE_DESIGN_EXECUTION_LOCK.json",
        "pr122_implementation": PR122 / "PUBLIC_CYCLE_IMPLEMENTATION_EXECUTION_LOCK.json",
    }
    runtime_names = (
        "active_cycle.py", "runtime_types.py", "supervisor.py", "active_runner.py",
        "plant_commit.py", "backup_token_store.py", "terminal_runtime.py", "trace_writer.py",
    )
    lock = {
        "schema": "ACTIVE_RECONFORMANCE_INPUT_LOCK_V2",
        "task_type": "ACTIVE_PUBLIC_CYCLE_RECONFORMANCE_CPU_ONLY",
        "runtime_correction_quota": 0,
        "direct_upstream": {
            "repository": "kenqiana04/safer-splat",
            "pr": 122,
            "state": "OPEN_DRAFT",
            "title": "[Draft] Implement active runtime public cycle composition V2",
            "branch": "implement-active-runtime-public-cycle-composition-v2",
            "head": "bdc8273295d30cbeef029a38ed80153c5cc1d24d",
            "base": "design-active-runtime-public-cycle-composition-v2",
            "base_sha": "4148e671128444d357ea33f6e5c15d0dd2928411",
        },
        "frozen_authorities": {name: identity(path) for name, path in contract_paths.items()},
        "pr116_runtime_identities": old_lock["runtime_modules_17"],
        "pr122_runtime_identities": {name: identity(RUNTIME / name) for name in runtime_names},
        "must_remain_unchanged": implementation_lock["must_remain_unchanged"],
        "preserved_method_identities": {
            name: method_identity(RUNTIME / "supervisor.py", "Supervisor", name)
            for name in ("bypass_decision", "arbitrate", "certify_candidate")
        },
        "execution_counts": {
            "runtime_correction": 0, "real_active": 0, "gpu": 0, "smoke": 0,
            "scientific_oracle": 0, "official100": 0, "real_bypass_pair": 0,
        },
        "source_mutation_authority": False,
    }
    write_json(TASK / "ACTIVE_RECONFORMANCE_INPUT_LOCK.json", lock)


SCENARIOS = [
    ("RC-BLOCKER-01", "PR120 public-orchestration blocker closure", "STATIC_AND_CPU"),
    ("RC-POLICY-01", "Coordinator authority/policy leak", "STATIC"),
    ("RC-TR-FIDELITY-001", "43-row TransitionRule and RoutingDecision fidelity", "CRITICAL_STATIC"),
    ("RC-EXACT-01", "exact-one lookup for all legal contexts", "CRITICAL_DYNAMIC"),
    ("RC-START-01", "I0a PASS then R0 then ready", "CRITICAL_DYNAMIC"),
    ("RC-START-02", "I0a FAIL no plant", "CRITICAL_DYNAMIC"),
    ("RC-START-03", "I0a UNKNOWN no plant", "CRITICAL_DYNAMIC"),
    ("RC-START-04", "R0 anomaly remains diagnostic", "CRITICAL_DYNAMIC"),
    ("RC-START-05", "identity mismatch typed block", "CRITICAL_DYNAMIC"),
    ("RC-L1-PASS", "L1 PASS", "CRITICAL_DYNAMIC"),
    ("RC-L1-FAIL", "L1 FAIL no ordinary alternative", "CRITICAL_DYNAMIC"),
    ("RC-L1-UNKNOWN-GLOBAL", "L1 global unknown", "CRITICAL_DYNAMIC"),
    ("RC-L1-UNKNOWN-HEALTH", "L1 health unknown", "CRITICAL_DYNAMIC"),
    ("RC-L1-UNKNOWN-UNRESOLVED", "L1 unresolved unknown", "CRITICAL_DYNAMIC"),
    ("RC-P0-C0", "primary and C0 boundary", "CRITICAL_DYNAMIC"),
    ("RC-L2-L3", "L2/L3 order and authority", "CRITICAL_DYNAMIC"),
    ("RC-EXCEPTION", "stage exception Supervisor routing", "CRITICAL_DYNAMIC"),
    ("RC-DEADLINE", "deadline public path", "CRITICAL_DYNAMIC"),
    ("RC-ALT", "native alternative only", "CRITICAL_DYNAMIC"),
    ("RC-BACKUP", "backup prevalidation/lifecycle", "CRITICAL_DYNAMIC"),
    ("RC-TERMINAL", "terminal route-only", "CRITICAL_DYNAMIC"),
    ("RC-COMMIT", "routing/arbitration/commit authority", "CRITICAL_DYNAMIC"),
    ("RC-TRACE", "trace exactly once and fault semantics", "CRITICAL_DYNAMIC"),
    ("E2E-RC-01", "certified navigation", "CRITICAL_DYNAMIC"),
    ("E2E-RC-02", "primary rejected and valid backup", "CRITICAL_DYNAMIC"),
    ("E2E-RC-03", "eligible terminal", "CRITICAL_DYNAMIC"),
    ("E2E-RC-04", "assurance boundary", "CRITICAL_DYNAMIC"),
    ("E2E-RC-05", "expired with valid backup", "CRITICAL_DYNAMIC"),
    ("E2E-RC-06", "global unknown legal fallback/boundary", "CRITICAL_DYNAMIC"),
    ("RC-BYPASS", "BYPASS upstream evidence preservation", "STATIC"),
]


def build_scenarios_and_matrix() -> None:
    write_json(TASK / "scenario_manifest.json", {
        "schema": "ACTIVE_RECONFORMANCE_SCENARIO_MANIFEST_V2",
        "frozen_before_substantive_execution": True,
        "runtime_correction_quota": 0,
        "scenarios": [{"scenario_id": a, "purpose": b, "class": c} for a, b, c in SCENARIOS],
    })
    with PR107.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    design = json.loads((PR121 / "EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json").read_text(encoding="utf-8"))
    design_by_id = {row["rule_id"]: row for row in design["rules"]}
    fields = [
        "rule_id", "source_phase", "observation/result", "destination_phase", "guard",
        "deadline_requirement", "candidate_requirement", "retained_backup_requirement",
        "reason_scope", "failure_code_if_any", "commit_allowed", "action_authority",
        "may_start_next_stage", "may_start_new_search", "requires_arbitration",
        "old_backup_retained", "new_backup_created", "theorem_interpretation",
    ]
    with (TASK / "TRANSITION_43_RULE_EXPECTED_MATRIX_V2.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields + ["row_sha256"])
        writer.writeheader()
        for row in rows:
            merged = dict(row)
            merged.update({k: design_by_id[row["rule_id"]].get(k, "") for k in fields if k not in row})
            normalized = {k: merged.get(k, "") for k in fields}
            normalized["row_sha256"] = hashlib.sha256(
                json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            writer.writerow(normalized)


TEST_NAMES = (
    "test_pr120_blocker_closure.py", "test_coordinator_authority_boundary.py",
    "test_transition_row_fidelity.py", "test_transition_exact_one_revalidation.py",
    "test_public_cycle_call_order.py", "test_start_trial_reconformance.py",
    "test_l1_reconformance.py", "test_primary_c0_reconformance.py",
    "test_l2_l3_reconformance.py", "test_exception_routing_reconformance.py",
    "test_deadline_public_path_reconformance.py", "test_alternative_reconformance.py",
    "test_backup_public_path_reconformance.py", "test_terminal_public_path_reconformance.py",
    "test_routing_arbitration_consistency.py", "test_commit_authority_reconformance.py",
    "test_trace_public_path_reconformance.py", "test_genuine_public_e2e_reconformance.py",
    "test_transition_dynamic_coverage.py", "test_bypass_preservation_reconformance.py",
)


def build_tests() -> None:
    tests = TASK / "tests"
    tests.mkdir(exist_ok=True)
    (tests / "__init__.py").write_text("", encoding="utf-8")
    support = '''from __future__ import annotations
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
'''
    (tests / "_support.py").write_text(support, encoding="utf-8", newline="\n")
    explicit = {
        "test_pr120_blocker_closure.py": '''import unittest
from ._support import RUNTIME, class_methods
class TestBlockerClosure(unittest.TestCase):
    def test_public_owner_and_api_exist(self):
        methods=class_methods(RUNTIME/"active_cycle.py", "ActiveCycleCoordinator")
        self.assertTrue({"start_trial","run_cycle","finalize_trial"} <= methods)
        source=(RUNTIME/"active_cycle.py").read_text(encoding="utf-8")
        for token in ("self.l1_runtime", "self.primary_adapter", "self.c0", "self.l2", "self.l3", "self.supervisor.route_transition", "self.supervisor.arbitrate", "self.active_runner.commit_active_decision"):
            self.assertIn(token, source)
''',
        "test_coordinator_authority_boundary.py": '''import ast, unittest
from ._support import RUNTIME
class TestCoordinatorBoundary(unittest.TestCase):
    def test_no_direct_plant_or_action_construction(self):
        source=(RUNTIME/"active_cycle.py").read_text(encoding="utf-8")
        self.assertNotIn("PlantCommitAdapter", source)
        self.assertNotIn("make_action(", source)
        self.assertNotIn("SelectedAction(", source)
        self.assertNotIn("dynamics", source)
''',
        "test_transition_row_fidelity.py": '''import dataclasses, json, unittest
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import RoutingDecision
from reproduction.runtime.active_runtime_assurance_v2.supervisor import TransitionRule
from ._support import DESIGN
class TestTransitionFidelity(unittest.TestCase):
    def test_required_frozen_fields_are_not_all_carried(self):
        design=json.loads(DESIGN.read_text(encoding="utf-8"))
        self.assertEqual(43, len(design["rules"]))
        rd={f.name for f in dataclasses.fields(RoutingDecision)}
        tr={f.name for f in dataclasses.fields(TransitionRule)}
        self.assertNotIn("action_authority", rd)
        self.assertNotIn("old_backup_retained", rd)
        self.assertNotIn("new_backup_created", rd)
        self.assertNotIn("theorem_interpretation", rd)
        self.assertNotIn("old_backup_retained", tr)
        self.assertNotIn("new_backup_created", tr)
        self.assertNotIn("theorem_interpretation", tr)
''',
    }
    generic = '''import unittest
from ._support import stop_after_first
class TestDeferredAfterCounterexample(unittest.TestCase):
    def test_deferred_by_fail_closed_protocol(self):
        stop_after_first(self)
        self.fail("must not execute before first-counterexample gate")
'''
    for name in TEST_NAMES:
        (tests / name).write_text(explicit.get(name, generic), encoding="utf-8", newline="\n")


def build_execution_lock() -> None:
    inputs = [
        TASK / "ACTIVE_RECONFORMANCE_INPUT_LOCK.json",
        TASK / "scenario_manifest.json",
        TASK / "TRANSITION_43_RULE_EXPECTED_MATRIX_V2.csv",
        TASK / "model_check_active_public_cycle_reconformance_v2.py",
        TASK / "validate_revalidated_active_runtime_contract_conformance_v2.py",
        *sorted((TASK / "tests").glob("*.py")),
    ]
    write_json(TASK / "ACTIVE_RECONFORMANCE_EXECUTION_LOCK.json", {
        "schema": "ACTIVE_RECONFORMANCE_EXECUTION_LOCK_V2",
        "frozen_before_substantive_execution": True,
        "runtime_correction_quota": 0,
        "files": [identity(path) for path in inputs],
        "execution_authority": "CPU_DETERMINISTIC_TARGETED_CONFORMANCE_ONLY",
    })


def main() -> None:
    build_input_lock()
    build_scenarios_and_matrix()
    build_tests()
    build_execution_lock()
    print("PASS_ACTIVE_RECONFORMANCE_HARNESS_FROZEN")


if __name__ == "__main__":
    main()
