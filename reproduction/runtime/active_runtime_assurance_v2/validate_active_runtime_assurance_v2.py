#!/usr/bin/env python3
"""Standard-library validation for the additive Active Runtime Assurance V2 package."""

from __future__ import annotations

import ast
import csv
import importlib
import json
import subprocess
import sys
from pathlib import Path


PACKAGE = Path(__file__).resolve().parent
REPO = PACKAGE.parents[2]
EVIDENCE = PACKAGE / "implementation_evidence"
PR115_HEAD = "44111d32031409338058e5da2f7e7a1f8d873323"
CORE_MODULES = (
    "authority_registry.py", "runtime_types.py", "start_admission.py", "diagnostic_r0.py",
    "l1_runtime.py", "primary_proposal_adapter.py", "c0_admission.py", "l2_runtime.py",
    "l3_runtime.py", "alternative_provider.py", "backup_token_store.py", "terminal_runtime.py",
    "deadline_runtime.py", "supervisor.py", "plant_commit.py", "trace_writer.py", "active_runner.py",
)
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, text=True, capture_output=True).stdout.strip()


def source_files() -> list[Path]:
    return sorted(PACKAGE / name for name in CORE_MODULES)


def main() -> int:
    checks: list[dict[str, object]] = []

    def check(name: str, condition: bool, evidence: object) -> None:
        checks.append({"check": name, "passed": bool(condition), "evidence": evidence})

    lock = json.loads((EVIDENCE / "ACTIVE_RUNTIME_IMPLEMENTATION_INPUT_LOCK.json").read_text(encoding="utf-8"))
    upstream_ok = lock["direct_upstream"]["head"] == PR115_HEAD and lock["direct_upstream"]["base_sha"] == "c924a959b1aa18b446a1d3c85afbe4f897604a84"
    check("01_exact_pr115_identity_in_input_lock", upstream_ok, lock["direct_upstream"])

    present = [name for name in CORE_MODULES if (PACKAGE / name).is_file()]
    check("02_exactly_17_core_modules_present", len(present) == 17 and set(present) == set(CORE_MODULES), present)

    imported = []
    import_error = None
    try:
        for filename in CORE_MODULES:
            imported.append(importlib.import_module(f"reproduction.runtime.active_runtime_assurance_v2.{Path(filename).stem}").__name__)
    except Exception as exc:
        import_error = f"{type(exc).__name__}:{exc}"
    check("03_package_importable", import_error is None and len(imported) == 17, import_error or len(imported))

    protected = git("diff", "--name-only", PR115_HEAD, "--", "run.py", "cbf", "dynamics", "splat")
    check("04_production_source_diff_zero", protected == "", protected.splitlines() if protected else [])
    frozen_specs = git("diff", "--name-only", PR115_HEAD, "--", "reproduction/specification", "reproduction/design/active_runtime_assurance_implementation_v2")
    check("05_frozen_spec_diff_zero", frozen_specs == "", frozen_specs.splitlines() if frozen_specs else [])

    dynamics_owners = [p.name for p in source_files() if "double_integrator_dynamics" in p.read_text(encoding="utf-8")]
    check("06_single_plant_commit_owner", dynamics_owners == ["plant_commit.py"], dynamics_owners)
    arbitration_owners = []
    oracle_imports = []
    for path in source_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "arbitrate":
                arbitration_owners.append(path.name)
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            if any("evaluation_oracle" in module or "outcome_calculator" in module for module in modules):
                oracle_imports.append(f"{path.name}:{node.lineno}")
    check("07_single_supervisor_selection_owner", arbitration_owners == ["supervisor.py"], arbitration_owners)
    check("08_no_posthoc_oracle_import", not oracle_imports, oracle_imports)

    forbidden = ("0.11", "0.10 + 0.01", "load_frozen_robot_margin_contract")
    legacy = [(p.name, token) for p in source_files() for token in forbidden if token in p.read_text(encoding="utf-8")]
    check("09_no_legacy_geometry_authority", not legacy, legacy)

    from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
    from reproduction.runtime.active_runtime_assurance_v2.backup_token_store import BackupTokenStore
    from reproduction.runtime.active_runtime_assurance_v2.c0_admission import C0Admission
    from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CandidateRole, RuntimeStateSnapshot, make_candidate
    from reproduction.runtime.active_runtime_assurance_v2.terminal_runtime import GOAL_HOLD_RUNTIME_ENABLED
    registry = AuthorityRegistry.frozen("map:test", "dt:test", "deadline:test")
    registry.verify_all(active=True)
    authority_values = (registry.geometry.controller_radius_m, registry.geometry.certification_margin_m, registry.geometry.certification_effective_radius_m, registry.geometry.rho_seg_m, registry.actuator.u_min, registry.actuator.u_max)
    check("10_authority_registry_values_exact", authority_values == (0.015, 0.010, 0.025, 0.0, (-0.1, -0.1, -0.1), (0.1, 0.1, 0.1)), authority_values)
    check("11_goal_hold_disabled", GOAL_HOLD_RUNTIME_ENABLED is False and registry.terminal.goal_hold_enabled is False, GOAL_HOLD_RUNTIME_ENABLED)
    runner_source = (PACKAGE / "active_runner.py").read_text(encoding="utf-8")
    check("12_active_deadline_profile_gate", "DEADLINE_PROFILE_REQUIRED" in runner_source and "ACTIVE_RUNTIME_ON" in runner_source, "explicit startup gate")
    state = RuntimeStateSnapshot.create("trial", 0, (0, 0, 0, 0, 0, 0), (1, 0, 0, 0, 0, 0), "map:test", 0.05)
    c0 = C0Admission(registry)
    inclusive = c0.evaluate(make_candidate((0.1, -0.1, 0), CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "cbf", state), state).status.value
    outside = c0.evaluate(make_candidate((0.10000001, 0, 0), CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "cbf", state), state)
    check("13_c0_bounds_inclusive", inclusive == "PASS" and outside.status.value == "FAIL", {"inclusive": inclusive, "outside": outside.status.value})
    c0_source = (PACKAGE / "c0_admission.py").read_text(encoding="utf-8")
    post_sources = c0_source + (PACKAGE / "plant_commit.py").read_text(encoding="utf-8")
    check("14_no_post_certification_clip", ".clip(" not in post_sources and "clamp(" not in post_sources, "no clip/clamp calls")
    l1_source = (PACKAGE / "l1_runtime.py").read_text(encoding="utf-8")
    check("15_l1_cycle_and_attempt_binding", "self._cache" in l1_source and "bind_attempt" in l1_source and "attempt_index" in l1_source, "cached cycle plus fresh binding")
    supervisor_source = (PACKAGE / "supervisor.py").read_text(encoding="utf-8")
    ordering = [supervisor_source.index(token) for token in ("c0.evaluate", "l2.evaluate", "l3.evaluate")]
    check("16_c0_l2_l3_ordering", ordering == sorted(ordering), ordering)
    alternative_source = (PACKAGE / "alternative_provider.py").read_text(encoding="utf-8")
    check("17_zero_alternative_inventory_supported", "NO_ALTERNATIVE_AVAILABLE" in alternative_source and "SOURCE_NATIVE_EXISTING" in alternative_source, "typed empty inventory")
    store_methods = {name for name in ("current", "validate", "prepare", "activate_after_navigation_commit", "consume_after_backup_commit", "abort_prepared", "invalidate") if hasattr(BackupTokenStore, name)}
    check("18_backup_token_lifecycle_complete", len(store_methods) == 7, sorted(store_methods))
    terminal_source = (PACKAGE / "terminal_runtime.py").read_text(encoding="utf-8")
    check("19_terminal_policy_complete", "STALE_TERMINAL_REFERENCE" in terminal_source and "fallback_context" in terminal_source and "eligible" in terminal_source, "membership/certificate/eligibility separated")
    plant_source = (PACKAGE / "plant_commit.py").read_text(encoding="utf-8")
    check("20_boundary_no_plant_behavior", "ASSURANCE_BOUNDARY_NO_ACTION" not in " ".join(role.value for role in __import__("reproduction.runtime.active_runtime_assurance_v2.plant_commit", fromlist=["LEGAL_ROLES"]).LEGAL_ROLES) and "SUPERVISOR_COMMIT_AUTHORITY_REQUIRED" in plant_source, "boundary excluded")

    transition_path = EVIDENCE / "RUNTIME_TRANSITION_IMPLEMENTATION_MAP_V2.csv"
    with transition_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    check("21_transition_coverage_43_exactly_once", len(rows) == 43 and len({row["rule_id"] for row in rows}) == 43 and all(row["mapping_cardinality"] == "EXACTLY_ONCE" for row in rows), len(rows))
    trace_source = (PACKAGE / "trace_writer.py").read_text(encoding="utf-8")
    check("22_trace_finalize_lock_semantics", "locked_before_evaluation" in (PACKAGE / "runtime_types.py").read_text(encoding="utf-8") and "TRACE_ALREADY_FINALIZED" in trace_source, "immutable content-addressed lock")
    invariants = json.loads((EVIDENCE / "ACTIVE_RUNTIME_IMPLEMENTATION_INVARIANTS_V2.json").read_text(encoding="utf-8"))
    ids = [item["id"] for item in invariants["invariants"]]
    check("23_all_iar_invariants_present", ids == [f"IAR-{index:02d}" for index in range(1, 33)], ids)

    tests = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(PACKAGE / "tests")], cwd=REPO, text=True, capture_output=True)
    combined = tests.stdout + tests.stderr
    check("24_all_unit_tests_pass", tests.returncode == 0 and "OK" in combined, combined.strip().splitlines()[-3:])
    forbidden_artifacts = sorted(str(path.relative_to(PACKAGE)) for pattern in ("*.pt", "*.pth", "*.ckpt", "*.ply", "*.npy", "*.npz") for path in PACKAGE.rglob(pattern))
    check("25_no_gpu_or_rollout_artifacts", not forbidden_artifacts, forbidden_artifacts)
    scientific_outputs = sorted(path.name for path in PACKAGE.rglob("*") if path.is_file() and any(token in path.name.lower() for token in ("trajectory", "collision_result", "success_metric", "progress_metric")))
    check("26_no_scientific_outcome_output", not scientific_outputs, scientific_outputs)

    failures = [item for item in checks if not item["passed"]]
    result = {
        "schema": "ACTIVE_RUNTIME_ASSURANCE_V2_IMPLEMENTATION_VALIDATION",
        "check_count": len(checks),
        "passed_count": len(checks) - len(failures),
        "failed_count": len(failures),
        "checks": checks,
        "rollout_count": 0,
        "gpu_execution_count": 0,
        "scientific_oracle_execution_count": 0,
        "verdict": "PASS_ACTIVE_RUNTIME_ASSURANCE_V2_IMPLEMENTATION_VALIDATION" if not failures else "FAIL_ACTIVE_RUNTIME_ASSURANCE_V2_IMPLEMENTATION_VALIDATION",
    }
    (EVIDENCE / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["verdict"])
    print(f"checks={len(checks)} failed={len(failures)}")
    if failures:
        for failure in failures:
            print(f"FAIL {failure['check']}: {failure['evidence']}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
