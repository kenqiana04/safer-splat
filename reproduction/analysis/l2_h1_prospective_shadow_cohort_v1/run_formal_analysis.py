#!/usr/bin/env python3
"""One-shot orchestration: canonical join, primary lock, bootstrap, then secondaries."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from analysis_common import (
    COLLECTION_LOCK_SHA256, DATA_ROLE, ORDERED_RESULT_COMMITMENT_SHA256, PROTOCOL_SHA256,
    atomic_write_json, file_sha256, iter_jsonl, load_json,
)
from analyze_primary_endpoint import lock_payload, primary_summary
from analyze_secondary_endpoints import (
    per_trial_rows, summarize_backend, summarize_multi_candidate, summarize_per_trial, summarize_selected_nonselected,
)
from bootstrap_primary_by_trial import bootstrap_by_trial

SECONDARY_IDS = [
    "L2_UNKNOWN_RATE", "L2_SELECTED_REACH_RATE", "FORMAL_LOGGING_COMPLETENESS", "PER_TRIAL_L1_PASS_L2_FAIL_DISTRIBUTION",
    "BACKEND_USAGE_COUNTS", "NATIVE_MULTI_CANDIDATE_OPPORTUNITY_AND_DISAGREEMENT", "SELECTED_VS_NATIVE_NONSELECTED_STATUS",
]


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def choose_case(primary: dict, bootstrap: dict) -> tuple[str, str, str, str]:
    if primary["N_primary"] == 0:
        return "CASE_C_PRIMARY_NOT_ESTIMABLE", "PRIMARY_OPERATIONAL_OPPORTUNITY_NOT_ESTIMABLE", "DIAGNOSE_L2_H1_PRIMARY_REACHABILITY_V1", "Primary cohort was not estimable."
    if primary["N_L2_UNKNOWN"] == primary["N_primary"]:
        return "CASE_E_ALL_PRIMARY_UNKNOWN", "FORMAL_RESULT_DOMINATED_BY_CERTIFIER_UNKNOWN", "DIAGNOSE_L2_H1_FORMAL_CERTIFIER_UNKNOWN_V1", "All primary-eligible outcomes were UNKNOWN."
    if primary["N_L2_FAIL"] == 0:
        return "CASE_B_PRIMARY_ESTIMABLE_ZERO_FAIL_OBSERVED", "NO_FORMAL_L2_FAIL_OBSERVED_AND_DO_NOT_PREMATURELY_BUILD_INTERVENTION", "ASSESS_L2_H1_OPERATIONAL_GENERALIZATION_V1", "No L2 FAIL was observed in this frozen cohort."
    if bootstrap["status"] != "ESTIMABLE":
        return "CASE_D_BOOTSTRAP_NOT_ESTIMABLE", "PRIMARY_POINT_ESTIMATE_AVAILABLE_BUT_CLUSTER_UNCERTAINTY_NOT_ESTIMABLE", "AUDIT_L2_H1_TRIAL_CLUSTER_SUPPORT_V1", "The point estimate was available but cluster uncertainty was not estimable."
    return "CASE_A_PRIMARY_ESTIMABLE_SIGNAL_OBSERVED", "FORMAL_PROSPECTIVE_L2_SIGNAL_OBSERVED_AND_READY_FOR_RECOVERABILITY_DESIGN", "FREEZE_L3_RECOVERABILITY_SPECIFICATION_V1", "A nonzero candidate-dependent future-segment FAIL signal prevalence was observed; this is not controller efficacy."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-root", type=Path, required=True)
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument("--collection-compact-dir", type=Path, required=True)
    args = parser.parse_args()
    table = args.server_root / "analysis_v1/canonical_formal_analysis_table.jsonl"
    manifest = args.task_dir / "formal_analysis_table_manifest.json"
    subprocess.run([sys.executable, str(args.task_dir / "build_formal_analysis_table.py"), "--server-root", str(args.server_root),
                    "--commitment", str(args.collection_compact_dir / "scientific_outcome_artifact_commitment.json"),
                    "--output-table", str(table), "--output-manifest", str(manifest)], check=True)
    rows = list(iter_jsonl(table))
    primary = primary_summary(rows, 14122)
    atomic_write_json(args.task_dir / "primary_result.json", primary)
    execution = load_json(args.task_dir / "ANALYSIS_EXECUTION_LOCK.json")
    primary_lock = lock_payload(primary, protocol_sha256=PROTOCOL_SHA256, collection_lock_sha256=COLLECTION_LOCK_SHA256,
                                analysis_execution_lock_sha256=execution["combined_analysis_execution_sha256"],
                                input_commitment_sha256=ORDERED_RESULT_COMMITMENT_SHA256)
    primary_lock["primary_result_file_sha256"] = file_sha256(args.task_dir / "primary_result.json")
    atomic_write_json(args.task_dir / "PRIMARY_RESULT_LOCK.json", primary_lock)
    write_csv(args.task_dir / "primary_tri_state.csv", [
        {"status": status, "count": primary[f"N_L2_{status}"], "share_of_primary": primary[f"N_L2_{status}"] / primary["N_primary"] if primary["N_primary"] else None}
        for status in ("PASS", "FAIL", "UNKNOWN")], ["status", "count", "share_of_primary"])

    intended_by_trial: dict[int, int] = {}
    with (args.collection_compact_dir / "formal_per_trial_blind_qc.csv").open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle): intended_by_trial[int(row["trial_id"])] = int(row["intended_step_count"])
    per_trial = per_trial_rows(rows, intended_by_trial)
    atomic_write_json(args.task_dir / "_per_trial_bootstrap_input.json", per_trial)
    write_csv(args.task_dir / "per_trial_primary.csv", per_trial, ["trial_id", "N_intended", "N_primary", "N_FAIL", "N_UNKNOWN", "primary_rate_if_denominator_positive"])
    bootstrap = bootstrap_by_trial(per_trial)
    if bootstrap["bootstrap_point_estimate_check"] != primary["prospective_future_safety_signal_rate"]:
        raise RuntimeError("bootstrap point estimate mismatch")
    atomic_write_json(args.task_dir / "primary_bootstrap.json", bootstrap)

    backend = summarize_backend(rows)
    multi = summarize_multi_candidate(rows)
    selected_nonselected = summarize_selected_nonselected(rows)
    write_csv(args.task_dir / "backend_usage.csv", backend, ["backend_class", "count", "share", "N_UNKNOWN"])
    atomic_write_json(args.task_dir / "multi_candidate_summary.json", multi)
    atomic_write_json(args.task_dir / "selected_vs_nonselected_summary.json", selected_nonselected)
    per_trial_summary = summarize_per_trial(per_trial)
    qc = load_json(args.collection_compact_dir / "formal_blind_qc_summary.json")
    n_reached = sum(row["l2_reached"] is True and row["selected_candidate_role"] == "SELECTED_EXECUTED_CONTROL" for row in rows)
    unknown_reasons = Counter(row["l2_reason"] for row in rows if row.get("primary_eligible") and row["l2_status"] == "UNKNOWN")
    secondary = {
        "schema_version": "L2_H1_FORMAL_SECONDARY_ENDPOINTS_V1", "data_role": DATA_ROLE, "secondary_endpoint_ids": SECONDARY_IDS,
        "L2_UNKNOWN_RATE": primary["L2_UNKNOWN_RATE"], "N_L2_UNKNOWN": primary["N_L2_UNKNOWN"], "L2_UNKNOWN_reason_counts": dict(sorted(unknown_reasons.items())),
        "N_l2_reached_selected": n_reached, "N_intended_control_steps": 14122, "L2_SELECTED_REACH_RATE": n_reached / 14122,
        "formal_logging_completeness": qc["rates"], "per_trial_distribution": per_trial_summary,
        "backend_usage": backend, "multi_candidate": multi, "selected_vs_native_nonselected": selected_nonselected,
        "known_status_sensitivity": primary["known_status_sensitivity"], "known_status_sensitivity_label": "SECONDARY_SENSITIVITY_ONLY",
        "u_des_is_native_alternative": False, "synthetic_candidate_generation_count": 0,
        "collision_progress_use": "RUN_CONTEXT_AND_IDENTITY_ONLY", "p_value_or_significance_test": False,
    }
    atomic_write_json(args.task_dir / "secondary_endpoints.json", secondary)
    write_csv(args.task_dir / "analysis_anomalies.csv", [], ["anomaly_type", "run_id", "trial_id", "step_id", "detail"])
    case, decision, next_task, interpretation = choose_case(primary, bootstrap)
    atomic_write_json(args.task_dir / "scientific_interpretation.json", {
        "selected_case": case, "interpretation": interpretation, "shadow_only": True, "controller_authority": False,
        "causal_effect_claim": False, "collision_or_progress_claim": False,
    })
    atomic_write_json(args.task_dir / "FINAL_CASE_DECISION.json", {
        "case": case, "final_status": "PASS_L2_H1_PROSPECTIVE_SHADOW_COHORT_ANALYSIS_V1", "final_decision": decision,
        "only_next_task": next_task, "unresolved_blockers": [],
    })
    print(json.dumps({"primary_result_lock_sha256": file_sha256(args.task_dir / "PRIMARY_RESULT_LOCK.json"), "selected_case": case}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
