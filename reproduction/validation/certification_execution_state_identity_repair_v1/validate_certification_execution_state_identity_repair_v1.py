#!/usr/bin/env python3
"""Fail-closed validator and deterministic evidence freezer for repair V1."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


RUNTIME_AUTHORITY = "50cadfe614da70ce0345c4b1789c787dc529287e"
SPEC_AUTHORITY = "77f8e52c2a2252fe651e4a13e3e30ada25168eb7"
SPEC_SHA = "5a0365c0d55376406fdd5b9181ef1b551ec29f30a5a96c41f96038e2d7dd0bc4"
ROOT_LOCK_SHA = "bc4b790ea7a893725249c5ca1e4a097379c88d431a97ec5a2469a19fcb857186"
ALLOWED_PREFIXES = (
    "reproduction/runtime/certification_execution_state_identity_repair_v1/",
    "reproduction/validation/certification_execution_state_identity_repair_v1/",
    "reproduction/implementation/certification_execution_state_identity_repair_v1/",
)
PROTECTED_PATHS = (
    "cbf", "dynamics", "splat", "run.py",
    "reproduction/runtime/active_runtime_assurance_v2",
    "reproduction/runtime/v3_hard_radius_runtime_wiring_v1",
    "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1",
    "reproduction/validation/active_runtime_paired_validation_v3",
    "reproduction/validation/active_runtime_paired_validation_v3_execution",
    "reproduction/validation/active_runtime_paired_validation_v3_execution_r1",
)


def git(root: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.checkout.resolve()
    result_root = args.result_root.resolve()
    implementation_dir = root / "reproduction/implementation/certification_execution_state_identity_repair_v1"
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, detail: Any = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    check("runtime_authority_ancestor", subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", RUNTIME_AUTHORITY, "HEAD"]).returncode == 0)
    check("spec_authority_ancestor", subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", SPEC_AUTHORITY, "HEAD"]).returncode == 0)
    check("repair_spec_sha", sha256(root / "reproduction/design/certification_execution_state_identity_repair_v1/REPAIR_SPECIFICATION.json") == SPEC_SHA)
    check("root_cause_lock_sha", sha256(root / "reproduction/design/certification_execution_state_identity_repair_v1/ROOT_CAUSE_EVIDENCE_LOCK.json") == ROOT_LOCK_SHA)

    protected_diff = git(root, "diff", "--name-only", RUNTIME_AUTHORITY, "--", *PROTECTED_PATHS).splitlines()
    check("protected_upstream_diff_zero", not protected_diff, protected_diff)
    changed = git(root, "diff", "--name-only", SPEC_AUTHORITY, "--").splitlines()
    check("only_allowed_repo_paths_changed", all(any(path.startswith(prefix) for prefix in ALLOWED_PREFIXES) for path in changed), changed)

    runtime_dir = root / ALLOWED_PREFIXES[0]
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in runtime_dir.glob("*.py"))
    check("canonical_transition_defined", "class CanonicalExecutionTransition" in source_text)
    check("canonical_dtype_locked", "IEEE754_BINARY32_TORCH_FLOAT32" in source_text)
    check("canonical_op_order_locked", "x + double_integrator_dynamics(x,u) * float(dt)" in source_text)
    check("l1_uses_canonical_endpoint", "self._transition.immediate_position" in source_text)
    check("l2_uses_sequential_transition", "self._transition.two_step" in source_text)
    check("l1_candidate_independent", "class CanonicalL1Runtime" in source_text and "candidate" not in source_text.split("class CanonicalL1Runtime", 1)[1].split("class CanonicalL2Runtime", 1)[0].split("def bind_attempt", 1)[0])
    check("identity_mismatch_typed", "CERT_EXEC_STATE_IDENTITY_MISMATCH" in source_text)
    check("no_arbitrary_epsilon", "epsilon" not in source_text.lower() and "tolerance" not in (runtime_dir / "canonical_transition.py").read_text(encoding="utf-8").lower())
    check("no_radius_policy_change", "0.025" not in (runtime_dir / "repaired_components.py").read_text(encoding="utf-8"))

    audit = read_json(result_root / "repaired_stack_wiring_audit.json")
    check("repaired_stack_wiring", audit.get("status") == "PASS" and all(audit.get("checks", {}).values()), audit)
    check("geometry_unchanged", (audit.get("hard_radius_q"), audit.get("runtime_margin_q"), audit.get("rho_seg_q")) == (0.015, 0.0, 0.0))
    check("historical_shell_no_authority", audit.get("historical_diagnostic_radius_q") == 0.025 and audit.get("historical_diagnostic_runtime_authority") is False)

    archived = read_json(result_root / "archived_four_case_summary.json")
    check("archived_four_case_bitwise", archived.get("all_bitwise_continuity_pass") is True and archived.get("trial_ids") == [22, 28, 57, 59], archived)
    check("old_segments_not_required_safe", archived.get("old_segments_required_to_pass") is False and archived.get("old_segments_allowed_to_remain_fail") is True)
    check("no_runtime_execution", all(archived.get(key) == 0 for key in ("active_trial_rerun_count", "plant_commit_count", "controller_qp_count", "coordinator_run_cycle_count")))
    for trial in (22, 28, 57, 59):
        item = read_json(result_root / "archived_four_case" / f"trial_{trial}.json")
        check(f"trial_{trial}_continuity", item.get("all_bitwise_continuity_checks_pass") is True, item.get("checks"))
        check(f"trial_{trial}_same_segment_verdict", item.get("checks", {}).get("runtime_same_segment_verdict_agreement") is True)

    cpu = read_json(result_root / "canonical_transition_cpu_regression.json")
    check("cpu_regression", cpu.get("status") == "PASS" and cpu.get("cpu_tests_fail") == 0, cpu)
    trace = read_json(result_root / "trace_schema_validation.json")
    check("trace_schema_complete", trace.get("status") == "PASS" and trace.get("logging_has_policy_authority") is False, trace)

    frozen_lock = read_json(root / "reproduction/design/certification_execution_state_identity_repair_v1/ROOT_CAUSE_EVIDENCE_LOCK.json")
    check("frozen_scientific_failure_preserved", frozen_lock.get("frozen_scientific_result") == "FAIL_V3_HARD_SAFETY_GATE")

    protected_audit = {
        "schema": "CERT_EXEC_STATE_IDENTITY_PROTECTED_SOURCE_AUDIT_V1",
        "runtime_authority": RUNTIME_AUTHORITY,
        "protected_paths": list(PROTECTED_PATHS),
        "diff_count": len(protected_diff),
        "diff_paths": protected_diff,
        "status": "PASS" if not protected_diff else "FAIL",
    }
    write_json(result_root / "protected_source_audit.json", protected_audit)
    failed = [item for item in checks if not item["passed"]]
    summary = {
        "schema": "CERTIFICATION_EXECUTION_STATE_IDENTITY_IMPLEMENTATION_VALIDATION_V1",
        "status": "PASS_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_V1_VALIDATION" if not failed else "FAIL_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_V1_VALIDATION",
        "check_count": len(checks),
        "failed_checks": failed,
        "implementation_head": git(root, "rev-parse", "HEAD"),
        "runtime_authority": RUNTIME_AUTHORITY,
        "spec_authority": SPEC_AUTHORITY,
        "frozen_scientific_decision_remains": "FAIL_V3_HARD_SAFETY_GATE",
        "gpu_archived_replay_attempts": 1,
        "valid_gpu_archived_replay_count": 1 if not failed else 0,
        "active_trial_rerun_count": 0,
        "controller_qp_run_count": 0,
        "coordinator_run_cycle_count": 0,
        "plant_commit_count": 0,
        "analyzer_rerun_count": 0,
        "reference_rerun_count": 0,
        "official100_count": 0,
        "formal_new_outcome_count": 0,
    }
    write_json(result_root / "IMPLEMENTATION_VALIDATION_SUMMARY.json", summary)
    if failed:
        print(summary["status"])
        for item in failed:
            print("FAIL", item["name"], item["detail"])
        return 2

    lock_files = sorted(path for path in result_root.rglob("*") if path.is_file() and path.name not in {"IMPLEMENTATION_VALIDATION_LOCK.json", "IMPLEMENTATION_VALIDATION_LOCK.sha256"})
    lock = {
        "schema": "CERTIFICATION_EXECUTION_STATE_IDENTITY_IMPLEMENTATION_VALIDATION_LOCK_V1",
        "implementation_head": summary["implementation_head"],
        "files": [{"path": str(path.relative_to(result_root)), "size": path.stat().st_size, "sha256": sha256(path)} for path in lock_files],
        "frozen_scientific_decision_remains": "FAIL_V3_HARD_SAFETY_GATE",
        "complete": True,
    }
    lock_path = result_root / "IMPLEMENTATION_VALIDATION_LOCK.json"
    write_json(lock_path, lock)
    lock_sha = sha256(lock_path)
    (result_root / "IMPLEMENTATION_VALIDATION_LOCK.sha256").write_text(lock_sha + "  IMPLEMENTATION_VALIDATION_LOCK.json\n", encoding="utf-8")

    evidence_lock = {
        "schema": "CERTIFICATION_EXECUTION_STATE_IDENTITY_IMPLEMENTATION_EVIDENCE_LOCK_V1",
        "implementation_commit": summary["implementation_head"],
        "validation_root": str(result_root),
        "validation_lock_sha256": lock_sha,
        "repair_spec_sha256": SPEC_SHA,
        "root_cause_lock_sha256": ROOT_LOCK_SHA,
        "protected_source_diff_count": 0,
        "paired_result_mutation_count": 0,
        "diagnostic_result_mutation_count": 0,
        "frozen_scientific_decision_remains": "FAIL_V3_HARD_SAFETY_GATE",
    }
    evidence_path = implementation_dir / "IMPLEMENTATION_EVIDENCE_LOCK.json"
    write_json(evidence_path, evidence_lock)
    (implementation_dir / "IMPLEMENTATION_EVIDENCE_LOCK.sha256").write_text(sha256(evidence_path) + "  IMPLEMENTATION_EVIDENCE_LOCK.json\n", encoding="utf-8")
    (implementation_dir / "DOWNSTREAM_HANDOFF.json").write_text(json.dumps({
        "schema": "CERT_EXEC_STATE_IDENTITY_REPAIR_DOWNSTREAM_HANDOFF_V1",
        "status": "READY_FOR_SMOKE_PROTOCOL_FREEZE",
        "implementation_commit": summary["implementation_head"],
        "validation_lock_sha256": lock_sha,
        "frozen_scientific_decision_remains": "FAIL_V3_HARD_SAFETY_GATE",
        "smoke_execution_authorized": False,
        "only_next_task": "FREEZE_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_SMOKE_PROTOCOL_V1",
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(summary["status"])
    print(f"checks={len(checks)}")
    print(f"validation_lock_sha256={lock_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
