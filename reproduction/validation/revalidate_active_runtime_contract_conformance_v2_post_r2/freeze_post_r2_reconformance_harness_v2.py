"""Freeze input and execution locks before substantive post-R2 reconformance."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

from reproduction.validation.revalidate_active_runtime_contract_conformance_v2_post_r2.run_post_r2_reconformance_v2 import scenario_definitions


TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
RUNTIME = REPO / "reproduction/runtime/active_runtime_assurance_v2"
PR107 = REPO / "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def relative_hashes(paths: list[Path]) -> dict[str, str]:
    return {path.relative_to(REPO).as_posix(): sha256(path) for path in paths if path.exists()}


def main() -> int:
    upstream_head = "c38a51310767669e51ef6c87307c831405221277"
    current_head = git("rev-parse", "HEAD")
    if subprocess.run(["git", "merge-base", "--is-ancestor", upstream_head, current_head], cwd=REPO).returncode != 0:
        raise SystemExit(f"PR126 is not an ancestor of current head: {current_head}")

    runtime_modules = sorted(
        path for path in RUNTIME.glob("*.py")
        if path.name not in {
            "freeze_public_cycle_implementation_execution_lock_v2.py",
            "model_check_active_runtime_implementation_v2.py",
            "model_check_public_cycle_implementation_v2.py",
            "validate_active_runtime_assurance_v2.py",
            "validate_active_runtime_public_cycle_composition_v2.py",
        }
    )
    frozen = [
        PR107,
        REPO / "reproduction/audit/active_runtime_pre_repair_architecture_v2/MASTER_DEFECT_REGISTER_V2.csv",
        REPO / "reproduction/audit/active_runtime_pre_repair_architecture_v2/LATENT_HIGH_RISK_REGISTER_V2.csv",
        REPO / "reproduction/audit/active_runtime_pre_repair_architecture_v2/VERIFIED_NOT_A_BUG_REGISTER_V2.csv",
        REPO / "reproduction/audit/active_runtime_pre_repair_architecture_v2/PRE_REPAIR_REPAIR_DAG_V2.json",
        REPO / "reproduction/audit/active_runtime_pre_repair_architecture_v2/ACTUAL_RUNTIME_SYMBOLIC_MODEL_V2.json",
        REPO / "reproduction/audit/active_runtime_pre_repair_architecture_v2/ACTUAL_RUNTIME_SYMBOLIC_COUNTEREXAMPLES_V2.json",
        REPO / "reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/authority_routing_boundary_repair_v2/R1_AUTHORITY_ROUTING_REPAIR_INPUT_LOCK.json",
        REPO / "reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/authority_routing_boundary_repair_v2/R1_AUTHORITY_ROUTING_SOURCE_FREEZE.json",
        REPO / "reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/authority_routing_boundary_repair_v2/R1_43_RULE_ROUND_TRIP_RESULT.json",
        REPO / "reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/exception_unknown_routing_repair_v2/R2_EXCEPTION_UNKNOWN_REPAIR_INPUT_LOCK.json",
        REPO / "reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/exception_unknown_routing_repair_v2/R2_EXCEPTION_UNKNOWN_SOURCE_FREEZE.json",
        REPO / "reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/exception_unknown_routing_repair_v2/R2_STAGE_EXCEPTION_ROUTE_MATRIX_V2.json",
        REPO / "reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/exception_unknown_routing_repair_v2/R2_REASON_SCOPE_MAPPING_V2.json",
        REPO / "reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/exception_unknown_routing_repair_v2/R2_ALTERNATIVE_STATUS_FIDELITY_V2.json",
        REPO / "reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/exception_unknown_routing_repair_v2/R2_EXCEPTION_UNKNOWN_MODEL_CHECK_V2.json",
        REPO / "reproduction/runtime/active_runtime_assurance_v2/implementation_evidence/exception_unknown_routing_repair_v2/validation_result.json",
        REPO / "reproduction/runtime/active_runtime_assurance_v2/public_cycle_implementation_evidence/BYPASS_REVALIDATION_GATE_V2.json",
        REPO / "reproduction/validation/execute_refrozen_bypass_equivalence_v2r1/BYPASS_EQUIVALENCE_V2R1_EXECUTION_LOCK.json",
        REPO / "reproduction/design/active_runtime_public_cycle_composition_v2/EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json",
        REPO / "reproduction/design/active_runtime_public_cycle_composition_v2/PUBLIC_CYCLE_COMPOSITION_INVARIANTS_V2.json",
        REPO / "reproduction/design/active_runtime_public_cycle_composition_v2/PUBLIC_CYCLE_DESIGN_SCENARIOS_V2.json",
    ]
    input_lock = {
        "schema": "POST_R2_ACTIVE_RECONFORMANCE_INPUT_LOCK_V2",
        "pr126": {
            "number": 126,
            "head": upstream_head,
            "base": "303aa01c08e82d1d77a5f5cabf5127344109a996",
            "branch": "repair-active-runtime-exception-and-unknown-routing-v2",
            "state": "OPEN_DRAFT",
        },
        "task_type": "POST_R2_FULL_ACTIVE_CONTRACT_RECONFORMANCE_CPU_ONLY",
        "runtime_package_blob_manifest": {path.relative_to(REPO).as_posix(): git("hash-object", str(path)) for path in runtime_modules},
        "runtime_package_sha256_manifest": relative_hashes(runtime_modules),
        "frozen_artifact_sha256": relative_hashes(frozen),
        "r1_source_freeze_sha256": sha256(frozen[8]),
        "r2_source_freeze_sha256": sha256(frozen[11]),
        "bypass_evidence_identity": relative_hashes([path for path in frozen if "BYPASS" in path.name]),
        "execution_counts": {"runtime_correction": 0, "real_active": 0, "gpu": 0, "smoke": 0, "scientific_oracle": 0, "official100": 0, "real_bypass": 0},
    }
    input_path = TASK / "POST_R2_ACTIVE_RECONFORMANCE_INPUT_LOCK.json"
    write_json(input_path, input_lock)

    with PR107.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    expected_path = TASK / "POST_R2_TRANSITION_43_EXPECTED_MATRIX_V2.csv"
    with expected_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) + ["row_sha256"])
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "row_sha256": hashlib.sha256(json.dumps(row, sort_keys=True, separators=(",", ":")).encode()).hexdigest()})

    manifest = {
        "schema": "POST_R2_CONFORMANCE_SCENARIO_MANIFEST_V2",
        "sweep_mode": "COMPLETE_INDEPENDENT_MATRIX",
        "scenario_count": len(scenario_definitions()),
        "minimum_required": 60,
        "runtime_correction_quota": 0,
        "test_expectation_correction_quota": 0,
        "scenarios": [{"scenario_id": item[0], "domain": item[1], "fresh_isolated": True} for item in scenario_definitions()],
    }
    manifest_path = TASK / "POST_R2_CONFORMANCE_SCENARIO_MANIFEST_V2.json"
    write_json(manifest_path, manifest)

    diff = git("diff", "--name-only", upstream_head, "--", "reproduction/runtime/active_runtime_assurance_v2")
    write_json(TASK / "POST_R2_RUNTIME_DIFF_AUDIT_V2.json", {
        "schema": "POST_R2_RUNTIME_DIFF_AUDIT_V2",
        "baseline": upstream_head,
        "runtime_changed_paths": [line for line in diff.splitlines() if line],
        "runtime_source_diff_count": 0 if not diff else len(diff.splitlines()),
        "production_source_diff_count": 0,
        "status": "PASS_RUNTIME_IMMUTABLE" if not diff else "FAIL_RUNTIME_DIFF",
    })

    sources = [
        TASK / "IMPLEMENTATION_PLAN.md",
        TASK / "run_post_r2_reconformance_v2.py",
        TASK / "freeze_post_r2_reconformance_harness_v2.py",
        TASK / "model_check_post_r2_active_runtime_conformance_v2.py",
        TASK / "validate_post_r2_active_runtime_contract_conformance_v2.py",
        TASK / "build_post_r2_reconformance_evidence_v2.py",
        TASK / "tests/_support.py",
        TASK / "tests/test_post_r2_reconformance.py",
        input_path,
        expected_path,
        manifest_path,
    ]
    lock = {
        "schema": "POST_R2_ACTIVE_RECONFORMANCE_EXECUTION_LOCK_V2",
        "pr126_head": upstream_head,
        "input_lock_sha256": sha256(input_path),
        "sweep_mode": "COMPLETE_INDEPENDENT_MATRIX",
        "runtime_correction_quota": 0,
        "test_expectation_correction_quota": 0,
        "pre_substantive_harness_correction_count": 2,
        "pre_substantive_harness_correction_scope": [
            "fixture field-name adaptation",
            "FakeClock advancement placement",
            "synthetic ambiguity fixture construction",
        ],
        "substantive_execution_started": False,
        "locked_source_sha256": relative_hashes(sources),
        "expected_transition_matrix_sha256": sha256(expected_path),
        "scenario_manifest_sha256": sha256(manifest_path),
    }
    write_json(TASK / "POST_R2_ACTIVE_RECONFORMANCE_EXECUTION_LOCK.json", lock)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
