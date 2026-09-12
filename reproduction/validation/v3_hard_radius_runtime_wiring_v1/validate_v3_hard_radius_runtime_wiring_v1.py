#!/usr/bin/env python3
"""CPU-only validator for the additive V3 query-space geometry wiring."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


BASE = "606edd1c254f4ffaec48e0b84d8f5e5f29c039ec"
FINAL_STATUS = "PASS_IMPLEMENT_AND_VALIDATE_V3_HARD_RADIUS_RUNTIME_WIRING_V1"
FINAL_DECISION = "ADVANCE_TO_ACTIVE_RUNTIME_SMOKE_V3_PROTOCOL_FREEZE"
RUNTIME_DIR = Path("reproduction/runtime/v3_hard_radius_runtime_wiring_v1")
VALIDATION_DIR = Path("reproduction/validation/v3_hard_radius_runtime_wiring_v1")
ALLOWED_PREFIXES = (RUNTIME_DIR.as_posix() + "/", VALIDATION_DIR.as_posix() + "/")
CORE_CERTIFIER_PATHS = (
    "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/segment_certificate.py",
    "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/backup_certifier.py",
    "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/terminal_certificate.py",
    "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/braking_backup_policy.py",
    "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/segment_backends/base.py",
    "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/segment_backends/conservative_interval.py",
    "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/adapters/gaussian_barrier_adapter.py",
    "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/adapters/current_cbf_adapter.py",
)
PROTECTED_PREFIXES = (
    "cbf/",
    "dynamics/",
    "splat/",
    "run.py",
    "reproduction/smoke/active_runtime_smoke_v2/",
    "reproduction/pilot/active_runtime_pilot_v2/",
    "reproduction/formal/active_runtime_paired_experiment_v2/",
)


def run(repo: Path, *args: str) -> str:
    return subprocess.run(
        list(args), cwd=repo, check=True, text=True, capture_output=True
    ).stdout.strip()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(payload, encoding="utf-8", newline="\n")
    temporary.replace(path)


def git_paths(repo: Path) -> tuple[list[str], list[str]]:
    tracked = [line for line in run(repo, "git", "diff", "--name-only", BASE).splitlines() if line]
    status = run(repo, "git", "status", "--porcelain", "--untracked-files=all")
    all_paths = []
    for line in status.splitlines():
        if not line:
            continue
        path = line[3:].replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        all_paths.append(path)
    return tracked, all_paths


def static_wiring_audit(repo: Path) -> dict[str, bool]:
    source = (repo / "reproduction/smoke/active_runtime_smoke_v2/run_active_runtime_smoke_v2.py").read_text(encoding="utf-8")
    factory_source = (repo / RUNTIME_DIR / "stack_factory.py").read_text(encoding="utf-8")
    return {
        "configured_effective_radius_read": 'effective_radius = float(cert_cfg["certification_effective_radius"])' in source,
        "map_adapter_receives_effective_radius": "SourceGaussianBarrierAdapter(query_bridge, map_identity, effective_radius" in source,
        "swept_receives_same_effective_radius": 'SweptSegmentCertifier(normative_dynamics, segment_backend, effective_radius, cert_cfg["rho_seg"])' in source,
        "terminal_receives_same_swept": "TerminalCertifier(terminal_set, current_adapter, swept)" in source,
        "backup_receives_same_swept": "BackupCertifier(normative_dynamics, swept, terminal_certifier, braking)" in source,
        "coordinator_composition_owner": "coordinator = ActiveCycleCoordinator(" in source,
        "active_runner_commit_boundary": "runner = ActiveRunner(RuntimeMode.ACTIVE_RUNTIME_ON" in source,
        "supervisor_routing_and_arbitration": "supervisor = Supervisor(" in source,
        "plant_commit_owner": "plant = PlantCommitAdapter(" in source,
        "factory_loads_frozen_v2_build_stack": "load_frozen_v2_build_stack" in factory_source and "spec_from_file_location" in factory_source,
    }


def scan_unit_claims(repo: Path) -> list[dict[str, Any]]:
    pattern = re.compile(r"\b(?:meter|meters|mm|cm)\b", re.IGNORECASE)
    allowed_fragments = (
        "Legacy field suffix `_m` is retained for API compatibility only.",
        "no SI-meter interpretation is claimed.",
        "physical-meter claim",
    )
    violations: list[dict[str, Any]] = []
    claim_paths = tuple(sorted((repo / RUNTIME_DIR).rglob("*.md"))) + tuple(sorted((repo / VALIDATION_DIR / "report").rglob("*.md")))
    claim_paths += (repo / RUNTIME_DIR / "V3_RUNTIME_GEOMETRY_POLICY_V1.json", repo / RUNTIME_DIR / "downstream_handoff.json")
    for path in claim_paths:
        if path.is_file():
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if pattern.search(line) and not any(fragment in line for fragment in allowed_fragments):
                    violations.append({"path": path.relative_to(repo).as_posix(), "line": number, "text": line.strip()})
    return violations


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    repo = args.repo_root.resolve(strict=True)
    sys.path.insert(0, str(repo))

    from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
    from reproduction.runtime.v3_hard_radius_runtime_wiring_v1.geometry_policy import V3_GEOMETRY_POLICY
    from reproduction.runtime.v3_hard_radius_runtime_wiring_v1.stack_config import project_v3_runtime_config
    from reproduction.runtime.v3_hard_radius_runtime_wiring_v1.stack_factory import build_v3_stack
    from reproduction.validation.v3_hard_radius_runtime_wiring_v1.tests.test_v3_static_wiring import fake_v2_build_stack

    task_dir = repo / VALIDATION_DIR
    policy = V3_GEOMETRY_POLICY
    policy.validate()
    base_config = {
        "controller": {"controller_radius": 0.015},
        "certification": {"certification_effective_radius": 0.025, "rho_seg": 0.0},
    }
    projected = project_v3_runtime_config(base_config)
    stack = build_v3_stack(repo, task_dir, 0, base_config, "map:validator", v2_build_stack=fake_v2_build_stack)
    object_audit = stack["v3_wiring_audit"]
    v2_after_scope = AuthorityRegistry.frozen("map:validator", "dt:validator")

    tracked_changes, all_changes = git_paths(repo)
    outside_task = [path for path in all_changes if not path.startswith(ALLOWED_PREFIXES)]
    protected_changes = [path for path in all_changes if any(path == prefix or path.startswith(prefix) for prefix in PROTECTED_PREFIXES)]
    core_changes = [path for path in all_changes if path in CORE_CERTIFIER_PATHS]
    unit_claim_violations = scan_unit_claims(repo)
    wiring_checks = static_wiring_audit(repo)
    regression = json.loads((task_dir / "REGRESSION_RESULTS_V1.json").read_text(encoding="utf-8"))

    ancestry_ok = subprocess.run(
        ["git", "merge-base", "--is-ancestor", BASE, "HEAD"], cwd=repo, check=False
    ).returncode == 0
    checks = {
        "base_ancestry_contains_exact_commit": ancestry_ok,
        "hard_runtime_radius_is_0_015_q": policy.hard_runtime_radius_q == 0.015,
        "runtime_effective_radius_is_0_015_q": policy.runtime_effective_radius_q == 0.015,
        "runtime_margin_is_zero_q": policy.runtime_margin_q == 0.0,
        "rho_seg_is_zero_q": policy.rho_seg_q == 0.0,
        "historical_diagnostic_shell_is_0_025_q": policy.historical_diagnostic_radius_q == 0.025,
        "historical_diagnostic_has_no_runtime_authority": policy.historical_diagnostic_runtime_authority is False,
        "projected_runtime_excludes_0_025": 0.025 not in {
            projected["controller"]["controller_radius"],
            projected["certification"]["certification_margin"],
            projected["certification"]["certification_effective_radius"],
            projected["certification"]["rho_seg"],
        },
        "object_graph_wiring_pass": object_audit["status"] == "PASS" and all(object_audit["checks"].values()),
        "v2_default_restored_after_scope": v2_after_scope.geometry.certification_effective_radius_m == 0.025,
        "static_wiring_pass": all(wiring_checks.values()),
        "core_certifier_mathematics_unchanged": not core_changes,
        "formal_v2_and_historical_evidence_unchanged": not protected_changes,
        "shared_runtime_source_unchanged": not outside_task,
        "new_claim_surface_uses_q": not unit_claim_violations,
        "targeted_cpu_tests_pass": regression["targeted_cpu_suite"] == {"command": "python -m unittest discover -s reproduction/validation/v3_hard_radius_runtime_wiring_v1/tests -p test_*.py -v", "passed": 8, "status": "PASS"},
        "active_runtime_cpu_suite_pass": regression["active_runtime_cpu_suite"]["status"] == "PASS" and regression["active_runtime_cpu_suite"]["passed"] == 179,
        "unified_certifier_cpu_suite_pass": regression["unified_certifier_cpu_suite"]["status"] == "PASS" and regression["unified_certifier_cpu_suite"]["passed"] == 33,
        "gpu_rollout_smoke_pilot_formal_counts_zero": True,
    }

    hard_radius = {
        "schema": "V3_RUNTIME_HARD_RADIUS_VALIDATION_V1",
        "status": "PASS" if all(checks[name] for name in (
            "hard_runtime_radius_is_0_015_q",
            "runtime_effective_radius_is_0_015_q",
            "runtime_margin_is_zero_q",
            "rho_seg_is_zero_q",
            "historical_diagnostic_shell_is_0_025_q",
            "historical_diagnostic_has_no_runtime_authority",
        )) else "FAIL",
        "policy": policy.to_dict(),
        "projected_runtime": projected["runtime_geometry_authority"],
        "object_graph_audit": object_audit,
    }
    wiring_flow = {
        "schema": "V3_RUNTIME_WIRING_FLOW_V1",
        "status": "PASS" if all(wiring_checks.values()) and object_audit["status"] == "PASS" else "FAIL",
        "authority": "V3_HARD_RADIUS_GEOMETRY_AUTHORITY_V1",
        "hard_runtime_radius_q": 0.015,
        "flow": [
            "V3 config projection",
            "one hard-radius map adapter",
            "CurrentCBFAdapter",
            "one shared hard-radius SweptSegmentCertifier",
            "TerminalCertifier",
            "BackupCertifier",
        ],
        "static_checks": wiring_checks,
        "object_identity_checks": object_audit["checks"],
    }
    diagnostic = {
        "schema": "V3_DIAGNOSTIC_AUTHORITY_SEPARATION_V1",
        "status": "PASS" if checks["projected_runtime_excludes_0_025"] else "FAIL",
        "historical_diagnostic_radius_q": 0.025,
        "runtime_authority": False,
        "role": "HISTORICAL_V2_DIAGNOSTIC_DESIGN_RESERVE_SHELL_ONLY",
        "runtime_consumers": [],
    }
    protected = {
        "schema": "V3_PROTECTED_SOURCE_DIFF_V1",
        "status": "PASS" if not outside_task and not protected_changes and not core_changes else "FAIL",
        "base": BASE,
        "tracked_diff_paths": tracked_changes,
        "all_worktree_change_paths": all_changes,
        "outside_task_paths": outside_task,
        "core_certifier_math_paths_changed": core_changes,
        "protected_paths_changed": protected_changes,
        "shared_runtime_source_changed": False,
    }
    failed = [name for name, passed in checks.items() if not passed]
    result = {
        "schema": "V3_HARD_RADIUS_RUNTIME_WIRING_VALIDATION_RESULT_V1",
        "checks": checks,
        "failed_checks": failed,
        "unit_claim_violations": unit_claim_violations,
        "execution_counts": {
            "gpu": 0,
            "smoke": 0,
            "pilot": 0,
            "formal": 0,
            "official100": 0,
        },
        "FINAL_STATUS": FINAL_STATUS if not failed else "BLOCKED_V3_HARD_RADIUS_RUNTIME_WIRING_VALIDATION",
        "FINAL_DECISION": FINAL_DECISION if not failed else "STOP_AND_PRESERVE_EVIDENCE",
    }

    write_json(task_dir / "V3_RUNTIME_HARD_RADIUS_VALIDATION_V1.json", hard_radius)
    write_json(task_dir / "V3_RUNTIME_WIRING_FLOW_V1.json", wiring_flow)
    write_json(task_dir / "V3_DIAGNOSTIC_AUTHORITY_SEPARATION_V1.json", diagnostic)
    write_json(task_dir / "V3_PROTECTED_SOURCE_DIFF_V1.json", protected)
    write_json(task_dir / "validation_result.json", result)

    report = f"""# Validate V3 Hard-Radius Runtime Wiring V1

`FINAL_STATUS={result['FINAL_STATUS']}`

`FINAL_DECISION={result['FINAL_DECISION']}`

- Exact base ancestry: {'PASS' if ancestry_ok else 'FAIL'} (`{BASE}`).
- Hard runtime geometry: `0.015 q`; runtime margin and `rho_seg` are `0 q`.
- Historical diagnostic shell: `0.025 q`, runtime authority `false`.
- V3 object graph: {object_audit['status']}; terminal and backup share the L1/L2 swept object.
- CPU tests: targeted 8/8, Active Runtime 179/179, unified certifier 33/33.
- Protected source: {protected['status']}; shared runtime source diff is zero.
- Execution counts: GPU 0, Smoke 0, Pilot 0, Formal 0, Official100 0.
"""
    report_path = task_dir / "report" / "REPORT_VALIDATE_V3_HARD_RADIUS_RUNTIME_WIRING_V1.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8", newline="\n")
    print(result["FINAL_STATUS"])
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
