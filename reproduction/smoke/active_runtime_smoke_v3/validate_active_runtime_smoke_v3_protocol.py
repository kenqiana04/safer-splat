#!/usr/bin/env python3
"""CPU-only protocol/evidence validator for Active Runtime Smoke V3."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import py_compile
import subprocess
from typing import Any


UPSTREAM = "47bd12f1f8efca059775ab294211ed21f7b39d77"
TASK = Path("reproduction/smoke/active_runtime_smoke_v3")
PROTECTED = (
    "cbf",
    "dynamics",
    "splat",
    "run.py",
    "reproduction/runtime/active_runtime_assurance_v2",
    "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1",
    "reproduction/smoke/active_runtime_smoke_v2",
    "reproduction/pilot/active_runtime_pilot_v2",
    "reproduction/formal",
    "reproduction/runtime/v3_hard_radius_runtime_wiring_v1",
    "reproduction/validation/v3_hard_radius_runtime_wiring_v1",
)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, text=True, capture_output=True).stdout.rstrip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def check(checks: dict[str, bool], name: str, condition: bool) -> None:
    checks[name] = bool(condition)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--phase", choices=("protocol", "sealed", "evidence"), default="protocol")
    args = parser.parse_args()
    repo = args.repo_root.resolve(strict=True)
    task = repo / TASK
    protocol_path = task / "SMOKE_V3_PROTOCOL.json"
    input_lock_path = task / "SMOKE_V3_INPUT_LOCK.json"
    runner_path = task / "run_active_runtime_smoke_v3.py"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    input_lock = json.loads(input_lock_path.read_text(encoding="utf-8"))
    runner_source = runner_path.read_text(encoding="utf-8")
    tree = ast.parse(runner_source)
    checks: dict[str, bool] = {}

    check(checks, "upstream_commit_in_ancestry", subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", UPSTREAM, "HEAD"], check=False).returncode == 0)
    check(checks, "input_lock_exact_upstream", input_lock.get("upstream_commit") == UPSTREAM)
    upstream_validation = json.loads((repo / "reproduction/validation/v3_hard_radius_runtime_wiring_v1/validation_result.json").read_text(encoding="utf-8"))
    check(checks, "v3_upstream_validation_pass", upstream_validation.get("FINAL_STATUS") == "PASS_IMPLEMENT_AND_VALIDATE_V3_HARD_RADIUS_RUNTIME_WIRING_V1")
    check(checks, "trial_ids_exact", protocol.get("trial_ids") == [10, 50, 90])
    check(checks, "trial_order_exact", protocol.get("trial_order") == [10, 50, 90])
    check(checks, "serial_execution", protocol.get("serial_execution") is True)
    check(checks, "separate_process_per_trial", protocol.get("separate_process_per_trial") is True)
    check(checks, "max_cycles_exact", protocol.get("maximum_completed_cycles_per_trial") == 200)
    check(checks, "seed_exact", protocol.get("seed") == 0)
    check(checks, "gpu_exact", protocol.get("environment", {}).get("CUDA_VISIBLE_DEVICES") == "1")
    check(checks, "official_python_exact", protocol.get("environment", {}).get("python") == "/disk1/zlab/conda_envs/safer_splat_official/bin/python")
    geometry = protocol.get("v3_geometry", {})
    check(checks, "v3_geometry_exact", tuple(geometry.get(key) for key in ("hard_runtime_radius_q", "runtime_margin_q", "runtime_effective_radius_q", "rho_seg_q")) == (0.015, 0.0, 0.015, 0.0))
    check(checks, "diagnostic_geometry_exact", geometry.get("historical_diagnostic_radius_q") == 0.025 and geometry.get("historical_diagnostic_runtime_authority") is False)
    check(checks, "coordinate_unit_q", geometry.get("coordinate_unit") == "q")
    cert = protocol.get("certification", {})
    check(checks, "certification_exact", (cert.get("certification_margin"), cert.get("certification_effective_radius"), cert.get("rho_seg"), cert.get("terminal_velocity_tolerance")) == (0.0, 0.015, 0.0, 1e-12))
    controller = protocol.get("controller", {})
    check(checks, "controller_exact", (controller.get("proposal_source"), controller.get("alpha"), controller.get("beta"), controller.get("controller_radius"), controller.get("distance_method"), controller.get("actuator_bounds")) == ("CURRENT_PRIMARY_CBF_QP", 5.0, 1.0, 0.015, "ball-to-ellipsoid", [-0.1, 0.1]))
    dynamics = protocol.get("dynamics", {})
    check(checks, "dynamics_exact", (dynamics.get("identity"), dynamics.get("dt"), dynamics.get("velocity_bounds")) == ("POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1", 0.05, [-0.1, 0.1]))
    deadline = protocol.get("deadline_profile", {})
    check(checks, "deadline_exact", (deadline.get("cycle_deadline_duration"), deadline.get("latest_safe_commit"), deadline.get("warning_reserve"), deadline.get("stage_budgets"), deadline.get("clock_identity")) == (1.0, 0.8, 0.2, [], "MONOTONIC_CLOCK_ACTIVE_SMOKE_V3"))
    switches = protocol.get("execution_switches", {})
    check(checks, "all_scientific_switches_disabled", switches and all(value is False for value in switches.values()))
    expected_map = [
        ("config.yml", 6933, "cd6ea45ad01553f0ce1531ad08cfaf8359e95041b39c77291d94e75f2d2f2f8e"),
        ("dataparser_transforms.json", 312, "92a1af2f195be3b32e0422418aff40cbd426c1cf9d8f7d5da87629519f5a0f8e"),
        ("nerfstudio_models/step-000029999.ckpt", 92344786, "ac14f5ced354c93f26cf92404540712eff65bd02554d9e9ed0332508e290382d"),
    ]
    actual_map = [(item.get("relative_path"), item.get("size"), item.get("sha256")) for item in protocol.get("map_artifacts", [])]
    check(checks, "map_contract_exact", protocol.get("map_identity") == "c9eade9ca89b741768a0ca33b3a755b2656402864f121aefdceaed4b0174f7c8" and actual_map == expected_map)
    check(checks, "runner_uses_v3_stack_factory", "build_v3_stack_from_frozen_v2" in runner_source)
    check(checks, "runner_has_required_modes", all(token in runner_source for token in ('"--preflight"', '"--one"', '"--all"', '"--summarize"')))
    imported_modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_modules.append(node.module or "")
    check(checks, "runner_has_no_oracle_import", not any("oracle" in name.lower() for name in imported_modules))
    check(checks, "runner_does_not_define_geometry_policy", not any(isinstance(node, ast.ClassDef) and "Geometry" in node.name for node in ast.walk(tree)))
    check(checks, "runner_separate_process", "subprocess.Popen" in runner_source)
    py_compile.compile(str(runner_path), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)
    check(checks, "python_syntax", True)
    protected_diff = git(repo, "diff", "--name-only", UPSTREAM, "--", *PROTECTED)
    check(checks, "protected_diff_zero", protected_diff == "")
    all_changed = [line for line in git(repo, "status", "--porcelain", "--untracked-files=all").splitlines() if line]
    outside = []
    for line in all_changed:
        path = line[3:].replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        if not path.startswith(TASK.as_posix() + "/"):
            outside.append(path)
    check(checks, "worktree_changes_task_local", not outside)

    if args.phase in {"sealed", "evidence"}:
        lock_path = task / "SMOKE_V3_EXECUTION_LOCK.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        check(checks, "execution_lock_protocol_hash", lock.get("protocol_sha256") == sha256(protocol_path))
        protocol_commit = str(lock.get("protocol_git_commit", ""))
        check(checks, "execution_lock_protocol_commit", len(protocol_commit) == 40 and subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", protocol_commit, "HEAD"], check=False).returncode == 0)
        check(checks, "execution_lock_trials", lock.get("trial_ids") == [10, 50, 90] and lock.get("trial_order") == [10, 50, 90])
        check(checks, "execution_lock_switches", all(lock.get(name) is False for name in ("scientific_oracle_enabled", "pilot_enabled", "official100_enabled", "formal_comparison_enabled", "parameter_selection_enabled")))

    if args.phase == "protocol":
        raw = task / "raw"
        check(checks, "no_gpu_outcome_before_protocol_freeze", not raw.exists() or not any(raw.rglob("runtime_trace.jsonl")))
    if args.phase == "evidence":
        execution = json.loads((task / "SMOKE_V3_EXECUTION_SUMMARY.json").read_text(encoding="utf-8"))
        trace = json.loads((task / "SMOKE_V3_TRACE_AUDIT.json").read_text(encoding="utf-8"))
        check(checks, "three_trials_pass", execution.get("trial_pass_count") == 3)
        check(checks, "three_finalizations_pass", execution.get("finalization_pass_count") == 3)
        check(checks, "trace_cardinality_pass", trace.get("status") == "PASS")
        check(checks, "hard_geometry_observed", execution.get("hard_runtime_radius_observed_q") == 0.015 and execution.get("historical_0_025_runtime_authority_observed") is False)
        totals = execution.get("totals", {})
        check(checks, "zero_integrity_failures", all(totals.get(name) == 0 for name in ("selected_executed_identity_mismatch_count", "nonfinite_count", "action_bound_violation_count", "evidence_incomplete_count", "recovery_required_count", "plant_outcome_unknown_count", "exception_count")))
        check(checks, "no_gpu_trial_rerun", execution.get("gpu_trial_rerun_count") == 0)
        check(checks, "no_scientific_execution", all(execution.get(name) == 0 for name in ("formal_scientific_arm_count", "pilot_count", "official100_count", "scientific_oracle_count")))
        check(checks, "final_status_pass", execution.get("FINAL_STATUS") == "PASS_ACTIVE_RUNTIME_SMOKE_V3")

    failed = [name for name, passed in checks.items() if not passed]
    if args.phase == "evidence":
        status = "PASS_ACTIVE_RUNTIME_SMOKE_V3" if not failed else "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_CORE_RUNTIME"
    else:
        status = "PASS_ACTIVE_RUNTIME_SMOKE_V3_PROTOCOL_VALIDATION" if not failed else "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_PROTOCOL_VALIDATION"
    result = {
        "schema": "ACTIVE_RUNTIME_SMOKE_V3_VALIDATION_RESULT_V1",
        "phase": args.phase,
        "protocol_sha256": sha256(protocol_path),
        "checks": checks,
        "failed_checks": failed,
        "outside_task_changes": outside,
        "protected_diff_paths": protected_diff.splitlines() if protected_diff else [],
        "status": status,
    }
    write_json(task / "SMOKE_V3_PROTOCOL_VALIDATION.json", result)
    print(status)
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
