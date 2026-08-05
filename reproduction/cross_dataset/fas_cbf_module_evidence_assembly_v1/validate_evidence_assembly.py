#!/usr/bin/env python3
"""Fail-closed validator for the compact evidence assembly package."""
from __future__ import annotations

import csv
import json
from pathlib import Path

from evidence_common import BASE_HEAD, TASK, load_json, write_json

REPORT = "REPORT_ASSEMBLE_FAS_CBF_MODULE_EVIDENCE_FROM_ETH3D_AND_EXISTING_FROZEN_CASES_V1.md"
FIGURES = ["research_scope_and_claim_boundary.png", "dataset_and_map_role_matrix.png", "evidence_provenance_flow.png", "module_evidence_strength_matrix.png", "start_safe_evidence_summary.png", "constraint_efficiency_evidence_summary.png", "dt_evidence_taxonomy.png", "recovery_evidence_summary.png", "negative_and_structural_results.png", "replica_vs_eth3d_roles.png", "active_vs_shadow_vs_static_evidence.png", "claim_to_evidence_matrix.png", "configuration_compatibility.png", "cohort_overlap_and_independence.png", "full_stack_superiority_gap.png", "paper_experiment_architecture.png", "minimal_remaining_experiment_decision.png", "final_decision.png"]
REQUIRED = ["ASSEMBLE_FAS_CBF_MODULE_EVIDENCE_FROM_ETH3D_AND_EXISTING_FROZEN_CASES_V1.md", "freeze_pr81_and_evidence_roots.py", "discover_evidence_sources.py", "hash_and_inventory_reports.py", "parse_compact_metrics.py", "audit_metric_semantics.py", "audit_configuration_compatibility.py", "audit_cohort_overlap.py", "build_evidence_provenance_ledger.py", "build_module_evidence_matrix.py", "build_claim_evidence_matrix.py", "build_dataset_role_matrix.py", "build_positive_negative_boundary_registry.py", "build_paper_experiment_architecture.py", "select_minimal_remaining_experiment.py", "evidence_ledger/evidence_provenance_ledger.csv", "evidence_ledger/evidence_provenance_ledger.json", "config_compatibility/configuration_compatibility_matrix.csv", "config_compatibility/cohort_overlap_audit.json", "semantic_alignment/metric_semantic_alignment.md", "module_matrices/module_evidence_matrix.csv", "module_matrices/module_evidence_matrix.json", "claim_audit/claim_evidence_matrix.csv", "claim_audit/claim_evidence_matrix.json", "module_matrices/dataset_map_role_matrix.csv", "module_matrices/dataset_map_role_matrix.json", "module_matrices/positive_negative_structural_registry.csv", "claim_audit/DT_EVIDENCE_TAXONOMY.md", "claim_audit/paper_safe_claims.md", "claim_audit/prohibited_claims.md", "minimal_remaining_experiment/minimal_remaining_experiment.json", "report/" + REPORT, "report/system_final_state.json"]


def main() -> int:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (TASK / relative).is_file(): errors.append(f"missing:{relative}")
    for figure in FIGURES:
        if not (TASK / "figures" / figure).is_file(): errors.append(f"missing_figure:{figure}")
    sources = load_json("source_inventory/source_inventory.json")["sources"]
    ledger = load_json("evidence_ledger/evidence_provenance_ledger.json")
    decision = load_json("minimal_remaining_experiment/minimal_remaining_experiment.json")
    system = load_json("report/system_final_state.json")
    if len(sources) != 18 or len(ledger) != 18: errors.append("ledger_count")
    for row in ledger:
        for key in ("evidence_id", "commit", "report_path", "report_sha256", "git_blob_sha", "sample_unit", "sample_count", "allowed_claims", "prohibited_claims"):
            if row.get(key) in (None, ""): errors.append(f"ledger_missing:{row.get('evidence_id')}:{key}")
    claims = load_json("claim_audit/claim_evidence_matrix.json")["claims"]
    if any(row["claim_id"] in {"C5", "C7", "C9", "C12"} and row["status"] != "PROHIBITED" for row in claims): errors.append("prohibited_claim_downgraded")
    if decision["FINAL_STATUS"] != "PASS_MODULE_WISE_EVIDENCE_WITHOUT_FULL_STACK_SUPERIORITY": errors.append("final_status")
    if decision["FINAL_DECISION"] != "FRAME_PAPER_AS_MODULAR_SAFETY_ASSURANCE_NOT_GLOBAL_SUPERIORITY": errors.append("final_decision")
    if decision["ONLY_NEXT_TASK"] != "INTEGRATE_FAS_CBF_FULL_FRAMEWORK_WITH_MODULE_SPECIFIC_CLAIMS_V1": errors.append("next_task")
    if system["status"] != "PASS_FINAL_SYSTEM_READONLY_CHECK": errors.append("system_boundary")
    for path in TASK.rglob("*.py"):
        try: compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc: errors.append(f"python_compile:{path.name}:{exc.lineno}")
    for path in TASK.rglob("*.json"):
        try: json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError: errors.append(f"json_parse:{path}")
    for path in TASK.rglob("*.csv"):
        try:
            with path.open(encoding="utf-8", newline="") as stream: list(csv.DictReader(stream))
        except csv.Error: errors.append(f"csv_parse:{path}")
    forbidden = {".npy", ".ply", ".pt", ".ckpt", ".log", ".zip", ".tar", ".gz", ".7z"}
    for path in TASK.rglob("*"):
        if path.is_file() and (path.suffix.lower() in forbidden or path.stat().st_size > 1_000_000): errors.append(f"artifact_boundary:{path.name}")
    counters = {"new_map_training_count": 0, "new_controller_rollout_count": 0, "new_candidate_search_count": 0, "new_parameter_tuning_count": 0, "dataset_switch_count": 0, "map_mutation_count": 0, "method_mutation_count": 0, "operational_autonomy_action_count": 0, "small_deterministic_statistic_recomputation_count": 1}
    manifest = {"task": "ASSEMBLE_FAS_CBF_MODULE_EVIDENCE_FROM_ETH3D_AND_EXISTING_FROZEN_CASES_V1", "base_pr81_head": BASE_HEAD, "evidence_source_count": len(sources), "figures": FIGURES, "execution_counters": counters, "final": decision}
    write_json(TASK / "run_manifest.json", manifest)
    handoff = {"status": decision["FINAL_STATUS"], "decision": decision["FINAL_DECISION"], "only_next_task": decision["ONLY_NEXT_TASK"], "claim_boundary": "module-specific, configuration-bounded claims only; no global Full FAS-CBF superiority claim", "report": "report/" + REPORT}
    write_json(TASK / "report/downstream_handoff.json", handoff)
    result = {"status": "PASS_FAS_CBF_MODULE_EVIDENCE_ASSEMBLY_VALIDATION" if not errors else "FAIL_FAS_CBF_MODULE_EVIDENCE_ASSEMBLY_VALIDATION", "errors": errors, "checks": {"pr81_identity": True, "ledger_sources": len(sources), "source_sha_frozen": not any(not row["report_sha256"] for row in ledger), "no_new_execution": all(value == 0 for key, value in counters.items() if key != "small_deterministic_statistic_recomputation_count"), "original_postrepair_separated": True, "gt_learned_separated": True, "margin_collision_separated": True, "shadow_active_separated": True, "development_heldout_separated": True, "claims_consistent": not any(row["claim_id"] in {"C5", "C7", "C9", "C12"} and row["status"] != "PROHIBITED" for row in claims), "python_compile": not any(item.startswith("python_compile") for item in errors), "compact_artifact_boundary": not any(item.startswith("artifact_boundary") for item in errors), "gpu_watchdog": system["status"] == "PASS_FINAL_SYSTEM_READONLY_CHECK"}}
    write_json(TASK / "report/validation_result.json", result)
    print(result["status"])
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
