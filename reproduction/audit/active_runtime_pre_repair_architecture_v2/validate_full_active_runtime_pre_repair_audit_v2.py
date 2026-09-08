"""Validate completeness and scope of the full pre-repair architecture audit."""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path


TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
UPSTREAM = "3b01171d7d25c7f81efd53d0486ab95d7c73c7a9"
DOMAIN_COUNT = 17


def read(name: str):
    path = TASK / name
    if path.suffix == ".csv":
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))
    return json.loads(path.read_text(encoding="utf-8"))


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, text=True, capture_output=True).stdout.strip()


def main() -> int:
    manifest = read("AUDIT_DOMAIN_MANIFEST_V2.json")
    inp = read("FULL_PRE_REPAIR_AUDIT_INPUT_LOCK.json")
    symbolic = read("ACTUAL_RUNTIME_SYMBOLIC_MODEL_V2.json")
    probes = read("ADVERSARIAL_AUDIT_PROBE_RESULTS_V2.json")
    defects = read("MASTER_DEFECT_REGISTER_V2.csv")
    latent = read("LATENT_HIGH_RISK_REGISTER_V2.csv")
    not_bug = read("VERIFIED_NOT_A_BUG_REGISTER_V2.csv")
    domains = manifest.get("domains", [])
    runtime_diff = git("diff", UPSTREAM, "--name-only", "--", "reproduction/runtime", "run.py", "cbf", "dynamics", "splat")
    required = [
        "ACTIVE_RUNTIME_AUTHORITY_MAP_V2.csv", "COORDINATOR_FULL_POLICY_AUDIT_V2.csv", "SUPERVISOR_AUTHORITY_AUDIT_V2.json",
        "FROZEN_43_RULE_SCHEMA_V2.json", "TRANSITION_43_RULE_THREE_LAYER_AUDIT_V2.csv", "DESTINATION_DERIVATION_AUDIT_V2.json", "TRANSITION_EXACT_ONE_DOMAIN_AUDIT_V2.json",
        "OBSERVED_PUBLIC_CYCLE_GRAPH_V2.json", "EVENT_AND_REASON_SCOPE_FIDELITY_V2.csv", "DEADLINE_END_TO_END_AUTHORITY_AUDIT_V2.csv", "DEADLINE_OBSERVATION_AND_USE_AUDIT_V2.json",
        "ALTERNATIVE_RUNTIME_AUDIT_V2.json", "BACKUP_TOKEN_END_TO_END_AUDIT_V2.csv", "BACKUP_STATE_INFORMATION_LOSS_AUDIT_V2.json", "BACKUP_PREVALIDATION_AUDIT_V2.json",
        "TERMINAL_END_TO_END_AUDIT_V2.csv", "TERMINAL_FALLBACK_CONTEXT_AUTHORITY_AUDIT_V2.json", "EXCEPTION_AND_UNKNOWN_FULL_AUDIT_V2.csv", "UNKNOWN_REASON_SCOPE_INFORMATION_LOSS_V2.json",
        "START_ADMISSION_AND_R0_AUDIT_V2.json", "ROUTING_ARBITRATION_CROSSCHECK_V2.csv", "COMMIT_AUTHORITY_CHAIN_AUDIT_V2.json", "ASSURANCE_BOUNDARY_RUNTIME_AUDIT_V2.json",
        "TRACE_SIDE_EFFECT_ORDERING_AUDIT_V2.json", "TRACE_FAILURE_SEMANTICS_AUDIT_V2.json", "RUNTIME_IDENTITY_CHAIN_AUDIT_V2.csv", "NUMERIC_AUTHORITY_LEAK_AUDIT_V2.json",
        "TRIAL_SESSION_LIFECYCLE_AUDIT_V2.json", "ROUTING_LOOP_GUARD_AUTHORITY_AUDIT_V2.json", "BYPASS_PRESERVATION_FULL_AUDIT_V2.json", "LEGACY_AUTHORITY_LEAK_AUDIT_V2.json", "ORACLE_FEEDBACK_EDGE_AUDIT_V2.json",
        "ACTUAL_RUNTIME_SYMBOLIC_MODEL_V2.json", "ACTUAL_RUNTIME_SYMBOLIC_COUNTEREXAMPLES_V2.json", "ADVERSARIAL_AUDIT_PROBE_MANIFEST_V2.json", "ADVERSARIAL_AUDIT_PROBE_RESULTS_V2.json", "EXISTING_AND_AUDIT_TEST_RESULTS_V2.json",
        "MASTER_DEFECT_REGISTER_V2.csv", "LATENT_HIGH_RISK_REGISTER_V2.csv", "VERIFIED_NOT_A_BUG_REGISTER_V2.csv", "DEFECT_ROOT_CAUSE_CLUSTERING_V2.json", "PRE_REPAIR_REPAIR_DAG_V2.json", "FULL_ARCHITECTURE_AUDIT_INVARIANTS_V2.json",
        "full_active_runtime_pre_repair_audit_review.json", "FINAL_DECISION.json", "downstream_handoff.json", "DRAFT_PR_BODY.md", "report/REPORT_AUDIT_ACTIVE_RUNTIME_PRE_REPAIR_ARCHITECTURE_V2.md",
    ]
    checks = [
        ("01_pr123_exact", inp["direct_upstream"]["head"] == UPSTREAM),
        ("02_runtime_diff_zero", runtime_diff == ""),
        ("03_input_lock", (TASK / "FULL_PRE_REPAIR_AUDIT_INPUT_LOCK.json").exists()),
        ("04_a_to_q_complete", len(domains) == DOMAIN_COUNT and all(d["status"] in {"COMPLETE", "BLOCKED_BY_MISSING_ARTIFACT"} for d in domains)),
        ("05_authority_map", (TASK / "ACTIVE_RUNTIME_AUTHORITY_MAP_V2.csv").exists()),
        ("06_coordinator_audit", (TASK / "COORDINATOR_FULL_POLICY_AUDIT_V2.csv").exists()),
        ("07_supervisor_audit", (TASK / "SUPERVISOR_AUTHORITY_AUDIT_V2.json").exists()),
        ("08_frozen_schema", read("FROZEN_43_RULE_SCHEMA_V2.json")["rule_count"] == 43),
        ("09_three_layer_43", len(read("TRANSITION_43_RULE_THREE_LAYER_AUDIT_V2.csv")) == 43),
        ("10_destination_derivation", (TASK / "DESTINATION_DERIVATION_AUDIT_V2.json").exists()),
        ("11_exact_one_domain", (TASK / "TRANSITION_EXACT_ONE_DOMAIN_AUDIT_V2.json").exists()),
        ("12_phase_graph", (TASK / "OBSERVED_PUBLIC_CYCLE_GRAPH_V2.json").exists()),
        ("13_event_reason", (TASK / "EVENT_AND_REASON_SCOPE_FIDELITY_V2.csv").exists()),
        ("14_deadline_e2e", (TASK / "DEADLINE_END_TO_END_AUTHORITY_AUDIT_V2.csv").exists()),
        ("15_deadline_observations", (TASK / "DEADLINE_OBSERVATION_AND_USE_AUDIT_V2.json").exists()),
        ("16_alternative", (TASK / "ALTERNATIVE_RUNTIME_AUDIT_V2.json").exists()),
        ("17_backup", len(read("BACKUP_TOKEN_END_TO_END_AUDIT_V2.csv")) >= 6),
        ("18_backup_info_loss", (TASK / "BACKUP_STATE_INFORMATION_LOSS_AUDIT_V2.json").exists()),
        ("19_terminal", len(read("TERMINAL_END_TO_END_AUDIT_V2.csv")) >= 6),
        ("20_exception_unknown", len(read("EXCEPTION_AND_UNKNOWN_FULL_AUDIT_V2.csv")) >= 8),
        ("21_start_r0", (TASK / "START_ADMISSION_AND_R0_AUDIT_V2.json").exists()),
        ("22_arbitration_commit", len(read("ROUTING_ARBITRATION_CROSSCHECK_V2.csv")) >= 4),
        ("23_trace", (TASK / "TRACE_SIDE_EFFECT_ORDERING_AUDIT_V2.json").exists()),
        ("24_identity_numeric", len(read("RUNTIME_IDENTITY_CHAIN_AUDIT_V2.csv")) >= 8),
        ("25_session_loop", (TASK / "TRIAL_SESSION_LIFECYCLE_AUDIT_V2.json").exists()),
        ("26_bypass", read("BYPASS_PRESERVATION_FULL_AUDIT_V2.json")["real_bypass_pairs"] == 0),
        ("27_legacy", (TASK / "LEGACY_AUTHORITY_LEAK_AUDIT_V2.json").exists()),
        ("28_oracle", read("ORACLE_FEEDBACK_EDGE_AUDIT_V2.json")["edge_count"] == 0),
        ("29_symbolic_complete", symbolic["all_domains_enumerated"] is True),
        ("30_probes_at_least_40", len(probes["results"]) >= 40),
        ("31_master_defects", len(defects) >= 1),
        ("32_latent_risks", len(latent) >= 1),
        ("33_not_a_bug", len(not_bug) >= 1),
        ("34_clustering", (TASK / "DEFECT_ROOT_CAUSE_CLUSTERING_V2.json").exists()),
        ("35_repair_dag", (TASK / "PRE_REPAIR_REPAIR_DAG_V2.json").exists()),
        ("36_no_repair_source_changes", runtime_diff == ""),
        ("37_real_execution_zero", all(value == 0 for value in inp["execution_counts"].values())),
        ("38_explicit_next_strategy", read("FINAL_DECISION.json")["Only next task"] == read("downstream_handoff.json")["only_next_task"]),
    ]
    result = {
        "schema": "FULL_ACTIVE_RUNTIME_PRE_REPAIR_AUDIT_V2_VALIDATION",
        "status": "PASS_FULL_ACTIVE_RUNTIME_PRE_REPAIR_AUDIT_V2_VALIDATION" if all(ok for _, ok in checks) else "BLOCKED_FULL_ACTIVE_RUNTIME_PRE_REPAIR_AUDIT_INCOMPLETE",
        "check_count": len(checks), "passed_count": sum(ok for _, ok in checks), "failed_count": sum(not ok for _, ok in checks),
        "checks": [{"name": name, "passed": ok} for name, ok in checks],
        "audit_pass_is_not_runtime_contract_pass": True,
        "runtime_diff": runtime_diff,
        "confirmed_defect_count": len(defects), "latent_high_risk_count": len(latent), "verified_not_a_bug_count": len(not_bug),
    }
    (TASK / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    print(f"checks={result['passed_count']}/{result['check_count']}")
    return 0 if result["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
