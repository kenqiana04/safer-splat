from __future__ import annotations

import ast
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
EVIDENCE = PACKAGE / "public_cycle_implementation_evidence"
DESIGN = REPO / "reproduction/design/active_runtime_public_cycle_composition_v2"
UPSTREAM = "4148e671128444d357ea33f6e5c15d0dd2928411"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*command: str) -> str:
    return subprocess.check_output(command, cwd=REPO, text=True, stderr=subprocess.STDOUT)


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
                        "ast_sha256": hashlib.sha256(ast.dump(item, annotate_fields=True, include_attributes=False).encode()).hexdigest(),
                    }
    raise RuntimeError(method_name)


def main() -> None:
    input_lock = json.loads((EVIDENCE / "PUBLIC_CYCLE_IMPLEMENTATION_INPUT_LOCK.json").read_text(encoding="utf-8"))
    execution_lock = json.loads((EVIDENCE / "PUBLIC_CYCLE_IMPLEMENTATION_EXECUTION_LOCK.json").read_text(encoding="utf-8"))
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: object = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    direct = input_lock["direct_upstream"]
    check("01_pr121_exact_identity", direct == {
        "repository": "kenqiana04/safer-splat", "pr": 121, "state": "OPEN_DRAFT",
        "title": "[Draft] Design active runtime public cycle composition V2",
        "branch": "design-active-runtime-public-cycle-composition-v2", "head": UPSTREAM,
        "base": "validate-active-runtime-contract-conformance-v2", "base_sha": "6c5c59dd083dc83661e56c4ddd3e62fa12497652",
    })
    check("02_upstream_is_exact_ancestor", run("git", "merge-base", UPSTREAM, "HEAD").strip() == UPSTREAM)
    check("03_pr121_design_unchanged", all(sha(REPO / item["path"]) == item["sha256"] for item in input_lock["pr121_design_artifacts"]))
    changed = set(run("git", "diff", "--name-only", UPSTREAM, "HEAD").splitlines())
    allowed = all(path.startswith("reproduction/runtime/active_runtime_assurance_v2/") for path in changed)
    check("04_only_allowed_runtime_task_tree_changed", allowed, sorted(changed))
    check("05_active_cycle_exists", (PACKAGE / "active_cycle.py").is_file())
    numstat = run("git", "diff", "--numstat", UPSTREAM, "HEAD", "--", "reproduction/runtime/active_runtime_assurance_v2/runtime_types.py").split()
    check("06_runtime_types_additive_only", bool(numstat) and int(numstat[1]) == 0, numstat)
    locked_methods = input_lock["supervisor_method_identities"]
    current_methods = {name: method_identity(PACKAGE / "supervisor.py", "Supervisor", name) for name in locked_methods}
    check("07_supervisor_existing_methods_preserved", current_methods == locked_methods)
    unchanged = {item["path"]: sha(REPO / item["path"]) == item["sha256"] for item in input_lock["must_remain_unchanged"]}
    check("08_active_runner_unchanged", unchanged[next(path for path in unchanged if path.endswith("active_runner.py"))])
    check("09_plant_commit_unchanged", unchanged[next(path for path in unchanged if path.endswith("plant_commit.py"))])
    check("10_backup_store_unchanged", unchanged[next(path for path in unchanged if path.endswith("backup_token_store.py"))])
    check("11_terminal_runtime_unchanged", unchanged[next(path for path in unchanged if path.endswith("terminal_runtime.py"))])
    check("12_trace_writer_unchanged", unchanged[next(path for path in unchanged if path.endswith("trace_writer.py"))])

    active_source = (PACKAGE / "active_cycle.py").read_text(encoding="utf-8")
    supervisor_source = (PACKAGE / "supervisor.py").read_text(encoding="utf-8")
    types_source = (PACKAGE / "runtime_types.py").read_text(encoding="utf-8")
    check("13_public_api_start_trial", "def start_trial(" in active_source)
    check("14_public_api_run_cycle", "def run_cycle(" in active_source)
    check("15_public_api_finalize_trial", "def finalize_trial(" in active_source)
    check("16_coordinator_no_selection_authority", "make_action" not in active_source and "SupervisorDecision(" not in active_source)
    check("17_supervisor_route_transition_present", "def route_transition(" in supervisor_source)
    check("18_supervisor_arbitrate_preserved", current_methods["arbitrate"] == locked_methods["arbitrate"])
    check("19_exact_one_resolution", "len(matches) != 1" in supervisor_source)
    check("20_missing_ambiguous_typed", all(token in supervisor_source for token in ("BLOCKED_MISSING", "BLOCKED_AMBIGUOUS")))
    with (EVIDENCE / "EXECUTABLE_TRANSITION_IMPLEMENTATION_MAP_V2.csv").open(encoding="utf-8", newline="") as handle:
        mapping = list(csv.DictReader(handle))
    check("21_transition_map_43_of_43", len(mapping) == 43 and len({row["rule_id"] for row in mapping}) == 43 and all(row["implemented"] == "yes" for row in mapping))
    check("22_canonical_order", all(active_source.find(token) >= 0 for token in ("L1_IMMEDIATE_CERTIFICATION", "PRIMARY_PROPOSAL", "PRIMARY_C0", "PRIMARY_L2", "PRIMARY_L3", "ARBITRATION", "COMMIT")))
    check("23_l1_once_test_present", "self.assertEqual(system[\"counters\"][\"l1\"], 1)" in (PACKAGE / "tests/test_public_cycle_normal_primary.py").read_text(encoding="utf-8"))
    check("24_no_synthetic_alternative", all(token not in active_source.lower() for token in ("random", "perturb", "interpolat")))
    check("25_deadline_only_supervisor_interprets", "if deadline ==" not in active_source and "route_transition" in active_source)
    check("26_backup_priority_only_supervisor", "backup outranks" not in active_source.lower() and "self.supervisor.arbitrate" in active_source)
    check("27_terminal_route_only", "destination == RuntimePhase.TERMINAL_EVALUATION" in active_source)
    check("28_boundary_no_plant", "commit_active_decision" in active_source and "plant_commit.commit" not in active_source)
    check("29_active_runner_commit_token_trace_reused", "self.active_runner.commit_active_decision" in active_source)
    check("30_no_duplicate_token_logic", all(token not in active_source for token in ("activate_after_navigation_commit", "consume_after_backup_commit", ".prepare(")))
    check("31_no_duplicate_trace_logic", "trace_writer.append" not in active_source)
    check("32_no_u_des_fallback", "u_des" not in active_source)
    check("33_no_direct_dynamics", "import dynamics" not in active_source.lower())
    check("34_no_oracle", "oracle" not in active_source.lower() and "oracle" not in types_source.lower())
    check("35_session_state_guards", all(token in active_source for token in ("TRIAL_NOT_STARTED", "TRIAL_ALREADY_STARTED", "TRIAL_NOT_READY", "CYCLE_OR_SNAPSHOT_IDENTITY_MISMATCH")))

    suite = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(PACKAGE / "tests"), "-v"], cwd=REPO, text=True, capture_output=True)
    test_count = suite.stderr.count(" ... ok") + suite.stdout.count(" ... ok")
    check("36_cpu_scenarios_and_regressions_pass", suite.returncode == 0 and test_count >= 110, {"tests": test_count, "returncode": suite.returncode})
    model = subprocess.run([sys.executable, "-B", str(PACKAGE / "model_check_public_cycle_implementation_v2.py")], cwd=REPO, text=True, capture_output=True)
    model_payload = json.loads((EVIDENCE / "public_cycle_implementation_model_check.json").read_text(encoding="utf-8"))
    check("37_model_counterexamples_zero", model.returncode == 0 and model_payload["counterexample_count"] == 0)
    check("38_pr116_regression_pass", input_lock["baseline_regression"] == {"status": "PASS", "suite": "PR116_RUNTIME_CPU_UNIT_TESTS", "tests": 78} and suite.returncode == 0)
    production_protected = [path for path in changed if not path.startswith("reproduction/runtime/active_runtime_assurance_v2/")]
    check("39_production_protected_diff_zero", not production_protected, production_protected)
    counts = execution_lock["counts"]
    check("40_real_execution_counts_zero", all(value == 0 for value in counts.values()), counts)
    check("41_execution_lock_current", all(sha(REPO / item["path"]) == item["sha256"] for item in execution_lock["locked_files"]))
    check("42_cycle_result_has_no_scientific_fields", not ({"collision", "success", "progress", "clearance", "oracle"} & set(ast.literal_eval("[]") if False else [])) and all(token not in types_source[types_source.index("class ActiveCycleResult"):types_source.index("class CoordinatorSession")] for token in ("collision", "success", "progress", "clearance", "oracle")))

    failed = [item for item in checks if not item["passed"]]
    result = {
        "schema": "ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2_IMPLEMENTATION_VALIDATION",
        "checks": checks,
        "check_count": len(checks),
        "failed_count": len(failed),
        "cpu_test_count": test_count,
        "model_counterexample_count": model_payload["counterexample_count"],
        "counts": counts,
        "status": "PASS_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2_IMPLEMENTATION_VALIDATION" if not failed else "BLOCKED_ACTIVE_RUNTIME_PUBLIC_CYCLE_COMPOSITION_V2_IMPLEMENTATION_VALIDATION",
    }
    (EVIDENCE / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    if failed:
        for item in failed:
            print(item["name"], item["detail"])
        raise SystemExit(1)


if __name__ == "__main__":
    main()
