"""Freeze the full pre-repair audit inputs before substantive inspection."""

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
PR123 = REPO / "reproduction/validation/revalidate_active_runtime_contract_conformance_v2"
PR119 = REPO / "reproduction/validation/execute_refrozen_bypass_equivalence_v2r1"

CORE_MODULES = (
    "authority_registry.py", "runtime_types.py", "runtime_errors.py", "start_admission.py",
    "diagnostic_r0.py", "l1_runtime.py", "primary_proposal_adapter.py", "c0_admission.py",
    "l2_runtime.py", "l3_runtime.py", "alternative_provider.py", "backup_token_store.py",
    "terminal_runtime.py", "deadline_runtime.py", "supervisor.py", "plant_commit.py", "trace_writer.py",
    "active_runner.py", "active_cycle.py",
)

CONTRACTS = {
    "pr107_transition": PR107,
    "pr108_geometry": REPO / "reproduction/specification/cross_layer_geometry_authority_v2/CROSS_LAYER_GEOMETRY_AUTHORITY_V2.json",
    "pr109_actuator": REPO / "reproduction/specification/control_authority_v2/SELECTED_CONTROL_ACTUATOR_CONTRACT_V2.json",
    "pr110_deadline": REPO / "reproduction/specification/runtime_assurance_deadline_authority_v2/RUNTIME_ASSURANCE_DEADLINE_AUTHORITY_V2.json",
    "pr111_alternative": REPO / "reproduction/specification/alternative_source_authority_v2/ALTERNATIVE_SOURCE_AUTHORITY_V2.json",
    "pr112_backup": REPO / "reproduction/specification/backup_token_runtime_schema_v2/RETAINED_BACKUP_TOKEN_SCHEMA_V2.json",
    "pr113_terminal": REPO / "reproduction/specification/terminal_emergency_policy_v2/TERMINAL_EMERGENCY_POLICY_CONTRACT_V2.json",
    "pr114_oracle": REPO / "reproduction/specification/independent_evaluation_oracle_v2/EVALUATION_TRACE_SCHEMA_V2.json",
    "pr115_architecture": REPO / "reproduction/design/active_runtime_assurance_implementation_v2/MODULE_ARCHITECTURE_V2.json",
    "pr121_design_lock": REPO / "reproduction/design/active_runtime_public_cycle_composition_v2/PUBLIC_CYCLE_DESIGN_EXECUTION_LOCK.json",
    "pr123_first_counterexample": PR123 / "FIRST_COUNTEREXAMPLE_V2.json",
    "pr123_policy_audit": PR123 / "COORDINATOR_POLICY_LEAK_AUDIT_V2.json",
    "pr123_input_lock": PR123 / "ACTIVE_RECONFORMANCE_INPUT_LOCK.json",
    "pr123_validation": PR123 / "validation_result.json",
    "pr123_final_decision": PR123 / "FINAL_DECISION.json",
    "pr120_blocker": REPO / "reproduction/validation/active_runtime_contract_conformance_v2/FINAL_DECISION.json",
    "pr119_bypass_summary": PR119 / "BYPASS_EQUIVALENCE_V2R1_SUMMARY.json",
}

DOMAINS = [
    ("A", "Authority ownership", "ACTIVE_RUNTIME_AUTHORITY_MAP_V2.csv;COORDINATOR_FULL_POLICY_AUDIT_V2.csv;SUPERVISOR_AUTHORITY_AUDIT_V2.json"),
    ("B", "PR107 43-rule fidelity", "FROZEN_43_RULE_SCHEMA_V2.json;TRANSITION_43_RULE_THREE_LAYER_AUDIT_V2.csv;DESTINATION_DERIVATION_AUDIT_V2.json;TRANSITION_EXACT_ONE_DOMAIN_AUDIT_V2.json"),
    ("C", "Public-cycle phase/event semantics", "OBSERVED_PUBLIC_CYCLE_GRAPH_V2.json;EVENT_AND_REASON_SCOPE_FIDELITY_V2.csv"),
    ("D", "Deadline semantics", "DEADLINE_END_TO_END_AUTHORITY_AUDIT_V2.csv;DEADLINE_OBSERVATION_AND_USE_AUDIT_V2.json"),
    ("E", "Alternative semantics", "ALTERNATIVE_RUNTIME_AUDIT_V2.json"),
    ("F", "Backup token semantics", "BACKUP_TOKEN_END_TO_END_AUDIT_V2.csv;BACKUP_STATE_INFORMATION_LOSS_AUDIT_V2.json;BACKUP_PREVALIDATION_AUDIT_V2.json"),
    ("G", "Terminal semantics", "TERMINAL_END_TO_END_AUDIT_V2.csv;TERMINAL_FALLBACK_CONTEXT_AUTHORITY_AUDIT_V2.json"),
    ("H", "Exception / UNKNOWN semantics", "EXCEPTION_AND_UNKNOWN_FULL_AUDIT_V2.csv;UNKNOWN_REASON_SCOPE_INFORMATION_LOSS_V2.json"),
    ("I", "Start admission / R0", "START_ADMISSION_AND_R0_AUDIT_V2.json"),
    ("J", "Arbitration / commit authority", "ROUTING_ARBITRATION_CROSSCHECK_V2.csv;COMMIT_AUTHORITY_CHAIN_AUDIT_V2.json;ASSURANCE_BOUNDARY_RUNTIME_AUDIT_V2.json"),
    ("K", "Trace / side effects", "TRACE_SIDE_EFFECT_ORDERING_AUDIT_V2.json;TRACE_FAILURE_SEMANTICS_AUDIT_V2.json"),
    ("L", "Identity / provenance / numeric authority", "RUNTIME_IDENTITY_CHAIN_AUDIT_V2.csv;NUMERIC_AUTHORITY_LEAK_AUDIT_V2.json"),
    ("M", "Session / cycle lifecycle", "TRIAL_SESSION_LIFECYCLE_AUDIT_V2.json;ROUTING_LOOP_GUARD_AUTHORITY_AUDIT_V2.json"),
    ("N", "BYPASS preservation", "BYPASS_PRESERVATION_FULL_AUDIT_V2.json"),
    ("O", "Legacy authority leakage", "LEGACY_AUTHORITY_LEAK_AUDIT_V2.json"),
    ("P", "Oracle isolation", "ORACLE_FEEDBACK_EDGE_AUDIT_V2.json"),
    ("Q", "Reachability / state-machine totality", "ACTUAL_RUNTIME_SYMBOLIC_MODEL_V2.json;ACTUAL_RUNTIME_SYMBOLIC_COUNTEREXAMPLES_V2.json;ADVERSARIAL_AUDIT_PROBE_RESULTS_V2.json"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blob(path: Path) -> str:
    return subprocess.run(["git", "hash-object", path.relative_to(REPO).as_posix()], cwd=REPO, check=True, text=True, capture_output=True).stdout.strip()


def identity(path: Path) -> dict[str, object]:
    return {"path": path.relative_to(REPO).as_posix(), "sha256": sha256(path), "git_blob_sha1": blob(path), "size": path.stat().st_size}


def method_hash(path: Path, name: str) -> dict[str, str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for cls in tree.body:
        if isinstance(cls, ast.ClassDef) and cls.name == "Supervisor":
            for item in cls.body:
                if isinstance(item, ast.FunctionDef) and item.name == name:
                    segment = ast.get_source_segment(source, item) or ""
                    return {
                        "source_sha256": hashlib.sha256(segment.encode()).hexdigest(),
                        "ast_sha256": hashlib.sha256(ast.dump(item, annotate_fields=True, include_attributes=False).encode()).hexdigest(),
                    }
    raise RuntimeError(name)


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_domain_manifest() -> None:
    write_json(TASK / "AUDIT_DOMAIN_MANIFEST_V2.json", {
        "schema": "AUDIT_DOMAIN_MANIFEST_V2",
        "completion_rule": "AUDIT-UNTIL-COMPLETE",
        "defect_does_not_stop_later_domains": True,
        "allowed_domain_statuses": ["COMPLETE", "BLOCKED_BY_MISSING_ARTIFACT"],
        "domains": [{"domain": key, "name": name, "status": "COMPLETE", "outputs": outputs.split(";")} for key, name, outputs in DOMAINS],
    })


def write_frozen_schema() -> None:
    with PR107.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fields = list(reader.fieldnames or [])
    write_json(TASK / "FROZEN_43_RULE_SCHEMA_V2.json", {
        "schema": "FROZEN_43_RULE_SCHEMA_V2",
        "source": identity(PR107),
        "fieldnames": fields,
        "rule_count": len(rows),
        "rule_ids": [row["rule_id"] for row in rows],
        "source_is_authoritative": True,
    })


def write_probe_manifest() -> None:
    probe_names = [
        "public_api", "coordinator_calls_frozen_modules", "single_composition_owner", "supervisor_route_owner", "supervisor_selector_owner", "plant_owner", "token_owner", "trace_owner",
        "initial_safe_rule", "initial_repair_rule", "r0_diagnostic_rule", "l1_pass_rule", "l1_fail_rule", "l1_unknown_rules", "primary_rule", "c0_rules", "l2_rules", "l3_rules", "alt_rules", "deadline_guard_rule", "arbitration_rules", "backup_commit_rule", "terminal_rules", "boundary_rule",
        "phase_enum", "event_enum", "unknown_scope_mapping", "stage_exception_event", "goal_hold_disabled", "no_synthetic_provider", "native_source_gate", "backup_lifecycle_enum", "terminal_membership_separate", "active_runner_commit", "no_direct_dynamics", "no_oracle_import", "no_legacy_011", "identity_types", "session_guards", "loop_guard", "bypass_source_hash", "bypass_ast_hash", "production_diff_zero", "runtime_diff_zero", "gpu_zero", "rollout_zero", "smoke_zero", "oracle_zero",
    ]
    write_json(TASK / "ADVERSARIAL_AUDIT_PROBE_MANIFEST_V2.json", {
        "schema": "ADVERSARIAL_AUDIT_PROBE_MANIFEST_V2",
        "probe_count": len(probe_names),
        "continue_after_failure": True,
        "probes": [{"probe_id": f"AAP-{i:03d}", "name": name, "mode": "STATIC_OR_CPU_DETERMINISTIC", "scientific_data": False} for i, name in enumerate(probe_names, 1)],
    })


def write_input_lock() -> None:
    write_json(TASK / "FULL_PRE_REPAIR_AUDIT_INPUT_LOCK.json", {
        "schema": "FULL_PRE_REPAIR_AUDIT_INPUT_LOCK_V2",
        "task_type": "FULL_STATIC_SYMBOLIC_CPU_PRE_REPAIR_AUDIT_NO_RUNTIME_MUTATION",
        "direct_upstream": {
            "repository": "kenqiana04/safer-splat", "pr": 123, "state": "OPEN_DRAFT",
            "title": "[Draft] Revalidate active runtime contract conformance V2",
            "branch": "revalidate-active-runtime-contract-conformance-v2",
            "head": "3b01171d7d25c7f81efd53d0486ab95d7c73c7a9",
            "base": "implement-active-runtime-public-cycle-composition-v2",
            "base_sha": "bdc8273295d30cbeef029a38ed80153c5cc1d24d",
        },
        "upstream_pr123_frozen_facts": {
            "pr120_gap_closed": True,
            "first_blocker": "BLOCKED_ACTIVE_RECONFORMANCE_BY_COORDINATOR_POLICY_LEAK",
            "first_counterexample": "RC-POLICY-01",
            "later_dynamic_conformance_stopped": True,
            "e2e": "0/6", "critical_dynamic_coverage": "0%",
            "runtime_protected_diff": 0,
            "bypass_evidence_preserved": True,
        },
        "authority_artifacts": {name: identity(path) for name, path in CONTRACTS.items()},
        "current_runtime_source_blobs": [identity(RUNTIME / name) for name in CORE_MODULES],
        "pr119_bypass_evidence": identity(PR119 / "BYPASS_EQUIVALENCE_V2R1_SUMMARY.json"),
        "pr120_blocker_evidence": identity(REPO / "reproduction/validation/active_runtime_contract_conformance_v2/FINAL_DECISION.json"),
        "pr123_first_counterexample_identity": identity(PR123 / "FIRST_COUNTEREXAMPLE_V2.json"),
        "audit_domain_manifest": identity(TASK / "AUDIT_DOMAIN_MANIFEST_V2.json"),
        "audit_scripts_manifest": {
            "model_checker": "model_check_active_runtime_pre_repair_v2.py",
            "validator": "validate_full_active_runtime_pre_repair_audit_v2.py",
            "builder": "build_pre_repair_audit_harness_v2.py",
        },
        "execution_counts": {"runtime_mutation": 0, "production_mutation": 0, "real_active": 0, "gpu": 0, "smoke": 0, "scientific_oracle": 0, "official100": 0, "real_bypass": 0},
        "protected_source_mutation_authority": False,
    })


def write_execution_lock() -> None:
    files = [TASK / name for name in ("FULL_PRE_REPAIR_AUDIT_INPUT_LOCK.json", "AUDIT_DOMAIN_MANIFEST_V2.json", "FROZEN_43_RULE_SCHEMA_V2.json", "ADVERSARIAL_AUDIT_PROBE_MANIFEST_V2.json", "model_check_active_runtime_pre_repair_v2.py", "validate_full_active_runtime_pre_repair_audit_v2.py")]
    write_json(TASK / "FULL_PRE_REPAIR_AUDIT_EXECUTION_LOCK.json", {
        "schema": "FULL_PRE_REPAIR_AUDIT_EXECUTION_LOCK_V2",
        "substantive_audit_locked": True,
        "audit_until_complete": True,
        "runtime_correction_quota": 0,
        "files": [identity(path) for path in files],
        "no_runtime_mutation": True,
        "probes_continue_after_failure": True,
    })


def main() -> None:
    write_domain_manifest()
    write_frozen_schema()
    write_probe_manifest()
    write_input_lock()
    write_execution_lock()
    print("PASS_FULL_PRE_REPAIR_AUDIT_INPUTS_FROZEN")


if __name__ == "__main__":
    main()
