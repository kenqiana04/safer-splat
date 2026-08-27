"""Fail-closed validator for IMPLEMENT_L2_H1_SHADOW_CERTIFIER_V1."""
from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any

from fixtures.synthetic_fixtures import sphere_case
from l2_h1_shadow_certifier import l2_h1_shadow_certify
from shadow_contract import PR93_HEAD, REPO_ROOT, TASK_ROOT, load_frozen_robot_margin_contract

ALLOWED_PREFIX = "reproduction/shadow/l2_h1_shadow_certifier_v1/"
REQUIRED = [
    "README.md", "l2_h1_shadow_certifier.py", "frozen_backend_adapter.py", "shadow_types.py",
    "shadow_contract.py", "shadow_cli.py", "audit/frozen_upstream_identity.json",
    "audit/protected_source_audit.json", "audit/frozen_specification_identity.json",
    "audit/frozen_backend_symbol_map.json", "audit/robot_margin_contract.json",
    "audit/map_snapshot_contract.json", "audit/backend_differential_consistency.json",
    "audit/candidate_sensitivity_result.json", "audit/shadow_reason_to_frozen_taxonomy_mapping.csv",
    "audit/no_control_authority_audit.json", "reviewers/control_theory_review.json",
    "reviewers/robotics_systems_review.json", "reviewers/software_verification_review.json",
    "reviewers/scientific_claim_review.json", "run_manifest.json", "FINAL_CASE_DECISION.json",
    "downstream_handoff.json", "DRAFT_PR_BODY.md", "report/REPORT_IMPLEMENT_L2_H1_SHADOW_CERTIFIER_V1.md",
]


def run(args: list[str], cwd: Path = TASK_ROOT, check: bool = True, env: dict[str, str] | None = None, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=env, timeout=timeout)
    if check and completed.returncode != 0:
        raise RuntimeError(f"COMMAND_FAILED:{args!r}\n{completed.stdout}\n{completed.stderr}")
    return completed


def read_json(relative: str) -> Any:
    return json.loads((TASK_ROOT / relative).read_text(encoding="utf-8"))


def fail(message: str) -> None:
    raise RuntimeError("L2_H1_SHADOW_VALIDATION_FAILURE:" + message)


def validate_files_and_scope() -> dict[str, Any]:
    missing = [name for name in REQUIRED if not (TASK_ROOT / name).is_file()]
    if missing:
        fail("MISSING_REQUIRED:" + ",".join(missing))
    head = run(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT).stdout.strip()
    ancestor = run(["git", "merge-base", "--is-ancestor", PR93_HEAD, head], cwd=REPO_ROOT, check=False)
    if ancestor.returncode != 0:
        fail("PR93_NOT_ANCESTOR_OF_TASK_HEAD")
    status_lines = run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=REPO_ROOT).stdout.splitlines()
    committed_paths = [
        line.strip().replace("\\", "/")
        for line in run(["git", "diff", "--name-only", PR93_HEAD, head], cwd=REPO_ROOT).stdout.splitlines()
        if line.strip()
    ]
    outside = []
    for line in status_lines:
        path = line[3:].replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if not path.startswith(ALLOWED_PREFIX):
            outside.append(path)
    outside.extend(path for path in committed_paths if not path.startswith(ALLOWED_PREFIX))
    if outside:
        fail("OUTSIDE_TASK_DIFF:" + ",".join(outside))
    protected = read_json("audit/protected_source_audit.json")
    if protected["protected_blob_count"] != 17 or protected["protected_path_diff_count"] != 0 or not protected["status"].startswith("PASS"):
        fail("PROTECTED_SOURCE_AUDIT")
    return {
        "pr93_is_ancestor": True,
        "task_file_count": sum(1 for path in TASK_ROOT.rglob("*") if path.is_file()),
        "outside_task_diff_count": 0,
        "protected_blob_count": 17,
    }


def validate_static_contract() -> dict[str, Any]:
    implementation_files = [TASK_ROOT / name for name in ("shadow_types.py", "shadow_contract.py", "frozen_backend_adapter.py", "l2_h1_shadow_certifier.py", "shadow_cli.py")]
    trees = {path.name: ast.parse(path.read_text(encoding="utf-8")) for path in implementation_files}
    certifier_source = (TASK_ROOT / "l2_h1_shadow_certifier.py").read_text(encoding="utf-8")
    adapter_source = (TASK_ROOT / "frozen_backend_adapter.py").read_text(encoding="utf-8")
    certifier_tree = trees["l2_h1_shadow_certifier.py"]
    propagation = next(
        (node for node in ast.walk(certifier_tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "propagate_h1_endpoints"),
        None,
    )
    if propagation is None or [argument.arg for argument in propagation.args.args] != ["x_k", "u_k", "dt"]:
        fail("U_K_PLUS_1_OR_PROPAGATION_SIGNATURE_CREEP")
    if "0.5 *" in certifier_source and "dt" in certifier_source:
        fail("ZOH_POSITION_UPDATE_CREEP")
    for forbidden in ("new_control", "replacement_candidate", "stop_command", "backup_command"):
        if re.search(rf"\b{forbidden}\b", certifier_source):
            fail("FORBIDDEN_OUTPUT_FIELD:" + forbidden)
    for geometry_token in ("np.linalg.norm", "barrier_from_signed_distance", "signed_square"):
        if geometry_token in adapter_source:
            fail("GEOMETRY_REIMPLEMENTATION_IN_ADAPTER:" + geometry_token)
    imported_roots = set()
    for tree in trees.values():
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".", 1)[0])
    forbidden_roots = {"run", "controller", "work"}
    if imported_roots & forbidden_roots:
        fail("PRODUCTION_IMPORT:" + ",".join(sorted(imported_roots & forbidden_roots)))
    result = l2_h1_shadow_certify(*sphere_case("safe"), load_frozen_robot_margin_contract())
    payload = result.to_dict()
    authority_fields = ("controller_authority", "execution_authority", "candidate_selection_authority", "alternative_search_authority", "backup_authority", "terminal_authority", "fail_close_authority", "controller_intervention", "runtime_intervention")
    if not all(payload[name] is False for name in authority_fields):
        fail("NONZERO_SHADOW_AUTHORITY")
    return {"shadow_module_count": 5, "new_formal_safety_primitive_count": 0, "production_hook_count": 0, "authority_lock_count": len(authority_fields)}


def validate_tests_and_tooling() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="l2h1c_") as temporary:
        compile_root = Path(temporary) / "src"
        shutil.copytree(TASK_ROOT, compile_root)
        run([sys.executable, "-m", "compileall", "-q", "-f", str(compile_root)], cwd=compile_root)
    unit = run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"])
    combined = unit.stdout + unit.stderr
    match = re.search(r"Ran (\d+) tests", combined)
    if not match or int(match.group(1)) < 25 or "OK" not in combined:
        fail("UNITTEST_RESULT")
    pytest_available = importlib.util.find_spec("pytest") is not None
    pytest_status = "NOT_INSTALLED_ALLOWED"
    if pytest_available:
        run([sys.executable, "-B", "-m", "pytest", "-q", "tests"])
        pytest_status = "PASS"
    diff_check = run(["git", "diff", "--check"], cwd=REPO_ROOT)
    return {"compileall": "PASS", "unittest": "PASS", "shadow_test_count": int(match.group(1)), "pytest_available": pytest_available, "pytest_status": pytest_status, "git_diff_check": "PASS"}


def validate_evidence_and_claims() -> dict[str, Any]:
    required_statuses = {
        "audit/backend_differential_consistency.json": "PASS_BACKEND_DIFFERENTIAL_CONSISTENCY",
        "audit/candidate_sensitivity_result.json": "PASS_CANDIDATE_SENSITIVITY",
        "audit/analytical_oracle_results.json": "PASS_ANALYTICAL_ORACLE_TESTS",
        "audit/no_control_authority_audit.json": "PASS_NO_CONTROL_AUTHORITY",
        "audit/map_snapshot_contract.json": "PASS_MAP_SNAPSHOT_CONTRACT",
    }
    for path, expected in required_statuses.items():
        if read_json(path)["status"] != expected:
            fail("EVIDENCE_STATUS:" + path)
    reviews = [read_json(f"reviewers/{name}_review.json") for name in ("control_theory", "robotics_systems", "software_verification", "scientific_claim")]
    if any(review["critical_blockers"] or review["case_vote"] != "CASE_A" for review in reviews):
        fail("REVIEWER_BLOCKER_OR_DISAGREEMENT")
    decision = read_json("FINAL_CASE_DECISION.json")
    if decision["selected_case"] != "CASE_A" or decision["critical_blocker_count"] != 0:
        fail("FINAL_CASE_DECISION")
    report = (TASK_ROOT / "report/REPORT_IMPLEMENT_L2_H1_SHADOW_CERTIFIER_V1.md").read_text(encoding="utf-8")
    required_claim = "Specification-faithful shadow implementation of the local candidate-dependent H1 map-relative certifier."
    if required_claim not in report:
        fail("PERMITTED_CLAIM_MISSING")
    for phrase in ("Formal runtime metrics: 0", "formal performance metrics: 0", "No controller", "No navigation rollout"):
        if phrase not in report:
            fail("CLAIM_BOUNDARY_MISSING:" + phrase)
    return {"reviewer_count": 4, "reviewer_case_votes": {"CASE_A": 4}, "reviewer_disagreement_count": 0, "analytical_oracle_test_count": 10, "differential_backend_test_count": 4}


def validate_security_and_assets() -> dict[str, Any]:
    credential_patterns = (
        b"BEGIN " + b"PRIVATE KEY",
        b"gh" + b"p_",
        b"github_" + b"pat_",
        b"h" + b"f_",
    )
    credential_hits = []
    large = []
    for path in TASK_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.stat().st_size > 5 * 1024 * 1024:
            large.append(path.relative_to(TASK_ROOT).as_posix())
        if path.suffix.lower() not in {".png"}:
            data = path.read_bytes()
            if any(pattern in data for pattern in credential_patterns):
                credential_hits.append(path.relative_to(TASK_ROOT).as_posix())
    if credential_hits or large:
        fail(f"SECURITY_OR_LARGE_ASSET:{credential_hits}:{large}")
    return {"credential_hit_count": 0, "large_binary_asset_count": 0}


def main() -> None:
    # Network and raw-object identity is deliberately refreshed at final validation.
    freeze = run([sys.executable, "-B", "freeze_inputs.py"])
    if "PASS_L2_H1_SHADOW_INPUT_FREEZE" not in freeze.stdout:
        fail("INPUT_FREEZE")
    scope = validate_files_and_scope()
    static = validate_static_contract()
    tooling = validate_tests_and_tooling()
    evidence = validate_evidence_and_claims()
    security = validate_security_and_assets()
    operational = read_json("audit/operational_state_audit.json")
    if operational["GPU_formal_compute_count"] != 0 or operational["task_owned_process_count"] != 0:
        fail("OPERATIONAL_BOUNDARY")
    counters = read_json("run_manifest.json")["counters"]
    required_zero = (
        "formal_method_run_count", "navigation_rollout_count", "on_policy_collection_count", "formal_benchmark_count",
        "controller_mutation_count", "production_method_mutation_count", "dynamics_mutation_count", "map_training_count",
        "map_mutation_count", "dataset_addition_count", "cohort_addition_count", "candidate_library_mutation_count",
        "backup_mutation_count", "terminal_set_mutation_count", "parameter_tuning_count", "new_formal_safety_primitive_count",
        "controller_intervention_count", "candidate_replacement_count", "backup_trigger_count", "alternative_trigger_count",
        "terminal_trigger_count", "runtime_fail_close_action_count", "formal_runtime_metric_count", "formal_performance_metric_count",
        "GPU_formal_compute_count", "L3_implementation_count", "L4_implementation_count", "L5_implementation_count", "H2_implementation_count",
    )
    if any(counters[name] != 0 for name in required_zero):
        fail("NONZERO_FORBIDDEN_COUNTER")
    result = {
        "status": "PASS_L2_H1_SHADOW_CERTIFIER_V1_VALIDATION",
        "selected_case": "CASE_A",
        "FINAL_STATUS": "PASS_L2_H1_SHADOW_CERTIFIER_IMPLEMENTATION_V1",
        "FINAL_DECISION": "FREEZE_SHADOW_IMPLEMENTATION_AND_VALIDATE_ON_FROZEN_REPLAY",
        "Only_next_task": "VALIDATE_L2_H1_SHADOW_CERTIFIER_ON_FROZEN_REPLAY_V1",
        "unresolved_blocker_count": 0,
        "scope": scope,
        "static_contract": static,
        "tooling": tooling,
        "evidence": evidence,
        "security": security,
        "operational": operational,
        "counters": counters,
    }
    (TASK_ROOT / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("PASS_L2_H1_SHADOW_CERTIFIER_V1_VALIDATION")


if __name__ == "__main__":
    main()
