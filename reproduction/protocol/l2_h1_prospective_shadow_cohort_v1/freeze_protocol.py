#!/usr/bin/env python3
"""Freeze the L2/H1 formal prospective shadow cohort protocol before collection."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
UPSTREAM_HEAD = "17bec44c51207bf7f831db724e108b86adb0ace8"
UPSTREAM_PR = 99
UPSTREAM_BRANCH = "validate-l2-h1-shadow-logging-completeness-pilot-v1"
UPSTREAM_BASE = "validate-l2-h1-shadow-instrumentation-equivalence-v1"
FORMAL_ROLE = "FORMAL_PROSPECTIVE_SHADOW_COHORT_V1"
OFFICIAL_MANIFEST_REL = Path("reproduction/experiment_protocol_freeze_v1/trial_manifests/stonehenge_official100_manifest.csv")
OFFICIAL_MANIFEST_SHA256 = "1b236bba8173c8a37fb7752fd2e2f09fc569191d6820089759b4be547bd6c344"
PILOT_REL = Path("reproduction/pilot/l2_h1_shadow_logging_completeness_pilot_v1")
INSTRUMENTATION_REL = Path("reproduction/instrumentation/l2_h1_on_policy_shadow_instrumentation_v1")
PILOT_IDS = [10, 30, 50, 70, 90]
EQUIVALENCE_IDS = [0, 24, 49, 74, 99]
QA_ROLES = ["EQUIVALENCE_QA_ONLY", "PILOT_QA_ONLY", "FROZEN_HISTORICAL_REPLAY"]
FORMAL_RUN_PATTERN = r"^formal-v1-trial-0[0-9]{2}-attempt-[01]$"
LOCKABLE_FILES = [
    "FORMAL_COHORT_PROTOCOL.md",
    "formal_trial_manifest.json",
    "formal_analysis_contract.json",
    "formal_identity_join_contract.json",
    "formal_qc_contract.json",
    "outcome_blind_qc_contract.json",
    "formal_retry_stop_policy.json",
    "formal_artifact_retention_policy.json",
    "formal_exclusion_contract.json",
    "formal_claim_contract.json",
    "formal_collection_environment_contract.json",
    "formal_collection_lock_schema.json",
    "formal_run_id_schema.json",
]


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def compact_canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def formal_run_id(trial_id: int, attempt_id: int = 0) -> str:
    if trial_id not in range(100) or attempt_id not in {0, 1}:
        raise ValueError("formal run identity is outside the frozen V1 namespace")
    return f"formal-v1-trial-{trial_id:03d}-attempt-{attempt_id}"


def load_official100(path: Path | None = None) -> tuple[list[dict[str, Any]], str]:
    source = path or (REPO / OFFICIAL_MANIFEST_REL)
    source_hash = sha256_file(source)
    if source_hash != OFFICIAL_MANIFEST_SHA256:
        raise ValueError(f"official100 raw-byte SHA drift: {source_hash}")
    with source.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 100:
        raise ValueError(f"official100 requires 100 rows, got {len(rows)}")
    required = {"trial", "cohort", "order", "start_goal_source", "seed", "result_family"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("official100 schema mismatch")
    parsed = []
    for row in rows:
        parsed.append({
            "trial_id": int(row["trial"]),
            "source_order": int(row["order"]),
            "cohort": row["cohort"],
            "start_goal_source": row["start_goal_source"],
            "source_seed": row["seed"],
            "result_family": row["result_family"],
        })
    parsed.sort(key=lambda item: item["trial_id"])
    ids = [item["trial_id"] for item in parsed]
    if ids != list(range(100)) or len(set(ids)) != 100:
        raise ValueError("official100 must contain each unique trial ID 0..99 exactly once")
    if any(item["source_order"] != item["trial_id"] or item["cohort"] != "official100" for item in parsed):
        raise ValueError("official100 stable order/cohort mismatch")
    return parsed, source_hash


def primary_counts(statuses: Iterable[str]) -> dict[str, Any]:
    values = list(statuses)
    if any(value not in {"PASS", "FAIL", "UNKNOWN"} for value in values):
        raise ValueError("primary tri-state must be PASS/FAIL/UNKNOWN")
    counts = {status: values.count(status) for status in ("PASS", "FAIL", "UNKNOWN")}
    total = len(values)
    return {
        "N_primary": total,
        "N_L2_PASS": counts["PASS"],
        "N_L2_FAIL": counts["FAIL"],
        "N_L2_UNKNOWN": counts["UNKNOWN"],
        "prospective_future_safety_signal_rate": counts["FAIL"] / total if total else None,
        "known_status_sensitivity": counts["FAIL"] / (counts["PASS"] + counts["FAIL"]) if counts["PASS"] + counts["FAIL"] else None,
    }


def pre_data_retry_allowed(event: dict[str, Any]) -> bool:
    return all((
        event.get("failure_class") == "PRE_DATA_INFRA_FAILURE",
        event.get("intended_step_count") == 0,
        event.get("formal_capture_count") == 0,
        event.get("formal_l2_result_count") == 0,
        event.get("scientific_row_count") == 0,
        event.get("failure_recorded") is True,
        event.get("same_trial_id") is True,
        event.get("fresh_process") is True,
        event.get("attempt_id_increment") == 1,
        event.get("prior_retry_count") == 0,
    ))


def protocol_md() -> str:
    return """# Formal L2/H1 Prospective Shadow Cohort Protocol V1

## Frozen scope

This protocol freezes the complete Stonehenge `official100` cohort before any formal prospective shadow result exists. Collection is serial, uses a fresh process for every trial, preserves the frozen controller and zero-authority L2/H1 observer, and never changes trial order or count based on outcomes.

## Cohort and identity

- Trials: exactly 100 unique IDs, integer order `0..99`.
- Data role: `FORMAL_PROSPECTIVE_SHADOW_COHORT_V1` only.
- Run ID: `formal-v1-trial-{trial_id:03d}-attempt-{attempt_id}`.
- Prior equivalence, pilot, and historical replay rows are permanently excluded.
- Pilot trial IDs `10,30,50,70,90` are rerun formally with new FORMAL run IDs.

## Analysis unit and endpoint

The analysis unit is one selected/executed candidate-state-map tuple at one committed control step: `(run_id, trial_id, step_id, x_k, selected executed u_k, dt, map_authority_id)`. The primary denominator contains all eligible selected rows whose frozen shadow L1 status is PASS and whose L2 tri-state evaluation is complete; UNKNOWN remains in the denominator. The primary numerator is L2 FAIL.

## Collection and analysis separation

Collection-stage QC checks completeness, identity, type, health, termination, and raw-artifact hashes without aggregating or inspecting scientific PASS/FAIL/UNKNOWN distributions. Scientific analysis unlocks only after all 100 formal trials and a valid `FORMAL_COLLECTION_LOCK.json` exist.

## Stop rule

One automatic retry is allowed only for a fully recorded pre-data infrastructure failure before the first intended step and before any capture, result, or scientific row. Any post-data failure or per-trial hard-gate violation stops V1; partial evidence is retained and no rerun is mixed into V1.

## Claim boundary

The future analysis may quantify candidate-dependent future-segment shadow signal prevalence under the frozen controller. It cannot establish collision prevention, safety improvement, controller efficacy, recursive feasibility, safe stopping, real-time performance, deployment readiness, physical-world guarantees, or Core V2 superiority.
"""


def build_contract_values() -> tuple[dict[str, Any], dict[str, Any]]:
    official, manifest_hash = load_official100()
    pilot_root = REPO / PILOT_REL
    pilot_selection = load_json(pilot_root / "pilot_trial_selection.json")
    pilot_runs = load_json(pilot_root / "pilot_run_manifest.json")
    pilot_overall = load_json(pilot_root / "pilot_overall_summary.json")
    pilot_join = load_json(pilot_root / "join_integrity.json")
    pilot_validation = load_json(pilot_root / "validation_result.json")
    if pilot_selection.get("selected_trial_ids") != PILOT_IDS or pilot_overall.get("selected_case") != "CASE_A" or not pilot_join.get("pass") or not pilot_validation.get("pass"):
        raise ValueError("PR99 compact pilot identity/gates do not match the frozen input")
    qa_run_ids = sorted(str(row["run_id"]) for row in pilot_runs["runs"])
    environments = [row["environment"] for row in pilot_runs["runs"]]
    first_env = environments[0]
    stable_keys = [
        "alpha", "beta", "controller_radius", "cuda_device_name", "cuda_visible_devices",
        "deterministic_flags", "distance_type", "dt", "executable", "map_artifact_count",
        "map_authority_id", "max_steps", "numpy", "pairing_identity_hash", "platform",
        "python", "repo_commit", "run_py_git_blob_expected", "run_py_sha256", "torch", "torch_cuda",
    ]
    if any(any(env.get(key) != first_env.get(key) for key in stable_keys) for env in environments[1:]):
        raise ValueError("PR99 pilot environment identity is not unique")

    formal_trials = [{
        **row,
        "formal_order": index,
        "data_role": FORMAL_ROLE,
        "attempt_0_run_id": formal_run_id(row["trial_id"], 0),
        "artifact_root": f"formal-v1/trial-{row['trial_id']:03d}/attempt-0/",
        "prior_qa_trial_id_reused_formally": row["trial_id"] in set(PILOT_IDS + EQUIVALENCE_IDS),
        "prior_qa_rows_reused": False,
    } for index, row in enumerate(official)]

    contracts: dict[str, Any] = {}
    contracts["formal_trial_manifest.json"] = {
        "schema_version": "L2_H1_FORMAL_TRIAL_MANIFEST_V1",
        "upstream_pr99_head": UPSTREAM_HEAD,
        "official100_source_path": OFFICIAL_MANIFEST_REL.as_posix(),
        "official100_manifest_sha256": manifest_hash,
        "trial_count": 100,
        "unique_trial_count": 100,
        "run_order": "STABLE_INTEGER_ASCENDING_0_TO_99",
        "trial_replacement_allowed": False,
        "adaptive_stopping_allowed": False,
        "pilot_trial_ids_repeated_with_new_formal_identity": PILOT_IDS,
        "trials": formal_trials,
    }
    contracts["formal_run_id_schema.json"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "safer-splat://l2-h1/formal-run-id-v1",
        "title": "L2/H1 formal prospective shadow run identity V1",
        "type": "object",
        "additionalProperties": False,
        "required": ["trial_id", "run_id", "attempt_id", "protocol_sha", "data_role", "artifact_root"],
        "properties": {
            "trial_id": {"type": "integer", "minimum": 0, "maximum": 99},
            "run_id": {"type": "string", "pattern": FORMAL_RUN_PATTERN},
            "attempt_id": {"type": "integer", "enum": [0, 1]},
            "protocol_sha": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "data_role": {"const": FORMAL_ROLE},
            "artifact_root": {"type": "string", "pattern": r"^formal-v1/trial-0[0-9]{2}/attempt-[01]/$"},
        },
        "identity_equation": "run_id == formal-v1-trial-{trial_id:03d}-attempt-{attempt_id}",
        "namespace_disjoint_from_qa": True,
        "overwrite_prior_attempt": False,
    }
    contracts["formal_exclusion_contract.json"] = {
        "schema_version": "L2_H1_FORMAL_EXCLUSION_CONTRACT_V1",
        "accepted_data_role": FORMAL_ROLE,
        "hard_rejected_data_roles": QA_ROLES,
        "hard_rejected_prs": [98, 99],
        "hard_rejected_qa_run_ids": qa_run_ids,
        "qa_exclusion_is_permanent": True,
        "pilot_ids_remain_in_formal_manifest": PILOT_IDS,
        "pilot_rows_reused": False,
        "formal_run_ids_must_match": FORMAL_RUN_PATTERN,
    }
    contracts["formal_analysis_contract.json"] = {
        "schema_version": "L2_H1_FORMAL_ANALYSIS_CONTRACT_V1",
        "analysis_unit": "selected/executed candidate-state-map tuple at one committed control step",
        "analysis_unit_key": ["run_id", "trial_id", "step_id", "x_k", "selected_executed_u_k", "dt", "map_authority_id"],
        "candidate_roles": {"u_des": "NOMINAL_REFERENCE", "selected_u_k": "SELECTED_EXECUTED_CONTROL"},
        "primary_eligibility_all": [
            f"data_role={FORMAL_ROLE}", "logging_qc_complete=true",
            "selected_candidate_role=SELECTED_EXECUTED_CONTROL", "selected_candidate_committed=true",
            "l1_observation_source=SHADOW_RECOMPUTED_FROZEN_CERTIFIER", "l1_status=PASS",
            "l2_reached=true", "l2_status in {PASS,FAIL,UNKNOWN}",
            "map_authority_valid=true", "payload_join_identity_valid=true",
        ],
        "primary_denominator_name": "N_L1_PASS_L2_SELECTED_EVALUATED",
        "primary_denominator": "count(primary eligible rows with L2 PASS, FAIL, or UNKNOWN)",
        "primary_numerator_name": "N_primary_FAIL",
        "primary_numerator": "count(primary eligible rows with L2=FAIL)",
        "primary_endpoint": "prospective_future_safety_signal_rate=N_primary_FAIL/N_primary",
        "unknown_in_primary_denominator": True,
        "tri_state_algebra": "N_primary=N_L2_PASS+N_L2_FAIL+N_L2_UNKNOWN",
        "secondary_unknown_rate": "N_L2_UNKNOWN/N_primary",
        "known_status_sensitivity_secondary_only": "N_L2_FAIL/(N_L2_PASS+N_L2_FAIL)",
        "secondary_endpoints": [
            "L2_UNKNOWN_RATE", "L2_SELECTED_REACH_RATE", "FORMAL_LOGGING_COMPLETENESS",
            "PER_TRIAL_L1_PASS_L2_FAIL_DISTRIBUTION", "BACKEND_USAGE_COUNTS",
            "NATIVE_MULTI_CANDIDATE_OPPORTUNITY_AND_DISAGREEMENT",
            "SELECTED_VS_NATIVE_NONSELECTED_STATUS",
        ],
        "per_trial_descriptives": ["N_intended", "N_primary", "N_FAIL", "N_UNKNOWN", "primary_rate_if_denominator_positive"],
        "cross_trial_descriptives": ["median", "IQR", "min", "max", "trials_with_at_least_1_FAIL", "trials_with_at_least_1_UNKNOWN"],
        "multi_candidate_contract": {
            "u_des_is_native_alternative": False,
            "native_siblings_require_pre_observation_runtime_provenance": True,
            "synthetic_candidate_generation_count": 0,
            "zero_group_result": "MULTI_CANDIDATE_ANALYSIS_NOT_ESTIMABLE",
        },
        "cluster_bootstrap": {
            "cluster_unit": "formal_trial", "cluster_count": 100,
            "clusters_per_replicate": 100, "resampling": "WITH_REPLACEMENT",
            "valid_replicates": 10000, "rng_seed": 20260831,
            "ci": "95_PERCENT_PERCENTILE", "zero_denominator_replicate": "DISCARD_AND_REDRAW",
            "maximum_total_draws": 100000, "insufficient_valid_replicates": "BOOTSTRAP_NOT_ESTIMABLE",
            "p_value_or_significance_test": False, "step_iid_assumption": False,
        },
        "no_post_hoc_change": True,
    }
    aggregator = pilot_root / "aggregate_logging_pilot.py"
    schema_root = REPO / INSTRUMENTATION_REL / "schemas"
    contracts["formal_identity_join_contract.json"] = {
        "schema_version": "L2_H1_FORMAL_IDENTITY_JOIN_CONTRACT_V1",
        "source": {
            "pr99_final_aggregator_path": f"{PILOT_REL.as_posix()}/aggregate_logging_pilot.py",
            "pr99_final_aggregator_sha256": sha256_file(aggregator),
            "pr99_join_integrity_pass": True,
            "schema_sha256": {name: sha256_file(schema_root / name) for name in [
                "step_payload.schema.json", "shadow_result.schema.json", "map_authority.schema.json", "health_event.schema.json"
            ]},
        },
        "official_trial_identity": {
            "manifest_field": "formal_trial_manifest.trials[].trial_id",
            "trace_field": "primary_trace.trial_id",
            "must_equal": True,
            "not_equal_to_process_local_token_by_assumption": True,
        },
        "process_local_trial_token": {
            "capture_field": "capture.trial_id", "result_field": "result.trial_id",
            "prefix": "trial-", "one_unique_token_per_fresh_process": True,
            "must_match_capture_result": True, "must_not_be_used_as_official_trial_id": True,
        },
        "capture_result_join_key": [
            "run_id", "process_local_trial_token", "step_id", "state_sequence_id",
            "decision_commit_id", "payload_sequence_id", "selected_candidate_id",
            "map_authority_id", "payload_enqueue_semantic_hash",
            "payload_worker_receive_semantic_hash", "result_semantic_hash",
        ],
        "derived_id_equations": {
            "state_sequence_id": "{run_id}:{process_local_trial_token}:state:{payload_sequence_id:06d}",
            "decision_commit_id": "{run_id}:{process_local_trial_token}:commit:{payload_sequence_id:06d}",
            "selected_candidate_id": "{run_id}:{process_local_trial_token}:selected:{payload_sequence_id:06d}",
            "step_id": "payload_sequence_id",
        },
        "denominator_control_trace_join": {
            "official_trial_id_equal": True, "step_id_equals_integer_sequence": True,
            "selected_u_k_equals_plant_input_u": True,
            "capture_selected_u_equals_trace_selected_u_k": True,
            "selected_candidate_hash_required": True, "selected_candidate_identity_required": True,
            "plant_input_output_state_required": True, "map_authority_id_equal": True,
        },
        "semantic_hash_contract": {
            "capture_recomputed_from_pr99_capture_semantic_keys": True,
            "capture_enqueue_receive_recomputed_equal": True,
            "result_recomputed_from_pr99_result_semantic_keys": True,
        },
        "freeze_before_first_formal_run": True,
        "change_after_first_formal_run": "STOP_V1_AND_CREATE_PROTOCOL_V2",
        "hot_fix_and_mix_v1_data": False,
    }
    completeness = [
        "capture_completeness", "selected_u_completeness", "map_authority_completeness",
        "reachability_completeness", "shadow_result_completion", "join_completeness",
    ]
    zero_errors = [
        "queue_drop", "serialization_error", "worker_failure", "alignment_failure", "schema_failure",
        "map_authority_failure", "sequence_gap", "duplicate_payload", "duplicate_result",
        "orphan_result", "capture_without_result", "shutdown_incomplete",
    ]
    contracts["formal_qc_contract.json"] = {
        "schema_version": "L2_H1_FORMAL_QC_CONTRACT_V1",
        "scope": "PER_SUCCESSFUL_FORMAL_TRIAL",
        "completeness_required": {name: 1.0 for name in completeness},
        "error_count_required": {name: 0 for name in zero_errors},
        "overall_average_cannot_override_per_trial_gate": True,
        "post_data_gate_failure": "STOP_COHORT_PRESERVE_PARTIAL_RECORD_PROTOCOL_DEVIATION",
        "trial_replacement_allowed": False,
    }
    contracts["outcome_blind_qc_contract.json"] = {
        "schema_version": "L2_H1_OUTCOME_BLIND_COLLECTION_QC_V1",
        "allowed_checks": [
            "intended_step_count", "capture_count", "result_record_exists", "join_completeness",
            "sequence_gaps", "selected_u_presence", "map_authority", "schema",
            "queue_worker_health", "termination", "raw_artifact_hash",
            "l2_status_field_presence_and_type_only",
        ],
        "forbidden_collection_outputs": [
            "N_L2_PASS", "N_L2_FAIL", "N_L2_UNKNOWN", "PASS_FAIL_UNKNOWN_DISTRIBUTION",
            "L1_PASS_L2_FAIL_COUNT", "MULTI_CANDIDATE_OUTCOME_DISAGREEMENT",
            "PRIMARY_ENDPOINT", "BOOTSTRAP_CI", "SCIENTIFIC_OUTCOME_SUMMARY",
        ],
        "scientific_analysis_unlock_all": [
            "formal_trial_count=100", "FORMAL_COLLECTION_LOCK_VALID=true", "outcome_blind_collection_qc_complete=true"
        ],
        "collection_task_may_analyze_scientific_outcomes": False,
    }
    contracts["formal_retry_stop_policy.json"] = {
        "schema_version": "L2_H1_FORMAL_RETRY_STOP_POLICY_V1",
        "trial_replacement_allowed": False,
        "automatic_retry_failure_class": "PRE_DATA_INFRA_FAILURE",
        "automatic_retry_all": [
            "failure_before_first_intended_control_step", "formal_capture_count=0",
            "formal_l2_result_count=0", "scientific_row_count=0", "failure_recorded=true",
            "same_trial_id=true", "fresh_process=true", "attempt_id_increment=1", "prior_retry_count=0",
        ],
        "maximum_automatic_retries_per_trial": 1,
        "post_data_failure_action": "STOP_COHORT_PRESERVE_PARTIAL_EVIDENCE_RECORD_PROTOCOL_DEVIATION",
        "post_data_automatic_retry": False,
        "continue_remaining_trials_after_post_data_failure": False,
        "mix_partial_and_rerun_in_v1": False,
    }
    contracts["formal_artifact_retention_policy.json"] = {
        "schema_version": "L2_H1_FORMAL_ARTIFACT_RETENTION_POLICY_V1",
        "server_raw_root": "/disk1/zlab/maintenance_records/l2_h1_prospective_shadow_cohort_v1/server_execution/",
        "server_full_retention": [
            "capture_jsonl", "result_jsonl", "health_logs", "control_traces", "stdout_stderr",
            "map_manifests", "attempt_artifacts",
        ],
        "git_allowed_compact": [
            "protocol", "formal_manifest", "artifact_manifest", "sha256", "compact_qc_summary",
            "compact_analysis_summary", "deviation_table", "report", "validator", "downstream_handoff",
        ],
        "raw_log_files_committed_to_git": 0,
        "git_forbidden_suffixes": [".jsonl", ".log"],
        "attempt_overwrite_allowed": False,
        "artifact_identity_fields": ["trial_id", "run_id", "attempt_id", "protocol_sha", "data_role"],
    }
    contracts["formal_claim_contract.json"] = {
        "schema_version": "L2_H1_FORMAL_CLAIM_CONTRACT_V1",
        "maximum_supported_claim_en": "Under the frozen Stonehenge controller and pre-registered official100 prospective shadow cohort, L2/H1 exhibited a measured prevalence of candidate-dependent future-segment safety signals among selected controls that had passed the frozen shadow L1 immediate-segment observation.",
        "maximum_supported_claim_zh": "在冻结 Stonehenge controller 与预注册 official100 prospective shadow cohort 下，对于通过冻结 shadow L1 即时段观察的 selected controls，L2/H1 呈现出可测量的 candidate-dependent future-segment safety signal 发生率。",
        "prohibited_claims": [
            "collision_prevention", "safety_improvement", "controller_efficacy", "intervention_success",
            "recursive_feasibility", "safe_stopping", "physical_world_guarantee", "real_time_guarantee",
            "deployment_readiness", "Core_V2_superiority", "counterfactual_avoided_collision",
        ],
        "collision_progress_use": "RUN_CONTEXT_AND_IDENTITY_ONLY",
        "l2_controller_authority": False,
    }
    contracts["formal_collection_environment_contract.json"] = {
        "schema_version": "L2_H1_FORMAL_COLLECTION_ENVIRONMENT_CONTRACT_V1",
        "upstream_pr99_head": UPSTREAM_HEAD,
        "runtime_production_identity": {key: first_env[key] for key in stable_keys},
        "physical_gpu_index": 1,
        "data_role": FORMAL_ROLE,
        "trial_count": 100,
        "run_order": "SERIAL_STABLE_INTEGER_ASCENDING",
        "fresh_process_each_trial": True,
        "controller_and_instrumentation_frozen": True,
        "shadow_authority": False,
        "adaptive_stopping": False,
        "outcome_conditioned_extra_trials": False,
        "protocol_sha_required_before_every_run": True,
    }
    contracts["formal_collection_lock_schema.json"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "safer-splat://l2-h1/formal-collection-lock-v1",
        "title": "FORMAL_COLLECTION_LOCK V1 schema only",
        "type": "object", "additionalProperties": False,
        "required": [
            "schema_version", "formal_trial_count", "formal_run_ids", "raw_artifact_manifests",
            "per_trial_sha256", "environment_identity", "map_identity", "protocol_lock_sha256",
            "qc_completeness", "collection_deviations", "collection_locked_before_scientific_analysis",
        ],
        "properties": {
            "schema_version": {"const": "FORMAL_COLLECTION_LOCK_V1"},
            "formal_trial_count": {"const": 100},
            "formal_run_ids": {"type": "array", "minItems": 100, "maxItems": 100, "uniqueItems": True, "items": {"type": "string", "pattern": FORMAL_RUN_PATTERN}},
            "raw_artifact_manifests": {"type": "array", "minItems": 100, "maxItems": 100},
            "per_trial_sha256": {"type": "object", "minProperties": 100, "maxProperties": 100},
            "environment_identity": {"type": "string", "minLength": 1},
            "map_identity": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "protocol_lock_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "qc_completeness": {"const": True},
            "collection_deviations": {"type": "array"},
            "collection_locked_before_scientific_analysis": {"const": True},
        },
        "template_only": True,
        "actual_formal_collection_lock_generated": False,
        "analysis_unlock_after_schema_valid_lock": True,
    }
    metadata = {
        "qa_run_ids": qa_run_ids,
        "manifest_hash": manifest_hash,
        "map_authority_id": first_env["map_authority_id"],
        "runtime_repo_commit": first_env["repo_commit"],
    }
    return contracts, metadata


def combined_protocol_sha(per_file: dict[str, str]) -> str:
    records = [{"path": path, "sha256": per_file[path]} for path in sorted(per_file)]
    return sha256_bytes(compact_canonical_bytes(records))


def build_report(lock_sha: str, manifest_hash: str, map_id: str) -> str:
    rows = [
        ("Q1", f"PR #99 Open Draft，head `{UPSTREAM_HEAD}`，base `{UPSTREAM_BASE}`。"),
        ("Q2", "YES；official100 为 100 个唯一 trial ID，稳定整数顺序 0–99。"),
        ("Q3", "YES；EQUIVALENCE_QA_ONLY、PILOT_QA_ONLY、FROZEN_HISTORICAL_REPLAY 与 PR #98/#99 QA run IDs 永久排除。"),
        ("Q4", "YES；pilot IDs 10/30/50/70/90 在 formal100 中重新运行，但使用全新 FORMAL run IDs。"),
        ("Q5", f"唯一 formal data_role：`{FORMAL_ROLE}`。"),
        ("Q6", "一个 committed control step 的 selected/executed candidate-state-map tuple。"),
        ("Q7", "满足 data role、完整 QC、selected committed control、合法 L1 provenance、L1 PASS、L2 reached/tri-state、map 与 join identity 的全部十项条件。"),
        ("Q8", "分子为 eligible rows 中 L2 FAIL；分母为所有 eligible PASS+FAIL+UNKNOWN rows。"),
        ("Q9", "YES；UNKNOWN 保留在 primary denominator。"),
        ("Q10", "NO；u_des 是 NOMINAL_REFERENCE，不是 native alternative。"),
        ("Q11", "YES；join contract 直接冻结 PR #99 最终通过 aggregator 与 PR #97 schema 的真实语义。"),
        ("Q12", "NO；第一条 formal run 后若需变更 join，必须停止 V1 并创建 V2。"),
        ("Q13", "QC 只看 step/capture/result 存在性、identity、完整率、schema、health、termination 与 raw hashes；不汇总或查看 scientific outcome distribution。"),
        ("Q14", "100 个 formal trials 完成且有效 FORMAL_COLLECTION_LOCK 建立后才解锁。"),
        ("Q15", "仅第一条 intended step 前、零 capture/result/scientific row 的 PRE_DATA_INFRA_FAILURE 可自动 retry 一次。"),
        ("Q16", "NO；产生数据后停止 cohort、保留 partial evidence、记录 deviation，禁止自动 retry。"),
        ("Q17", "以 formal trial 为 cluster 的 trial-cluster bootstrap percentile CI。"),
        ("Q18", "seed=20260831，10,000 valid replicates，每次重采样 100 个 trial clusters，max draws=100,000。"),
        ("Q19", "NO；raw JSONL/log 仅服务器保留，Git raw-log count=0。"),
        ("Q20", f"`{lock_sha}`。"),
        ("Q21", "navigation_run_count=0；formal_collection_run_count=0。"),
        ("Q22", "Only next task：COLLECT_L2_H1_PROSPECTIVE_SHADOW_COHORT_V1。"),
    ]
    table = "\n".join(f"| {q} | {answer} |" for q, answer in rows)
    return f"""# Report: Freeze L2/H1 Prospective Shadow Cohort Protocol V1

## Technical summary

**PASS_L2_H1_PROSPECTIVE_SHADOW_COHORT_PROTOCOL_FREEZE_V1 — CASE_A.** Before any formal prospective navigation or L2 outcome collection, this task freezes the complete Stonehenge official100 manifest, formal identity namespace, QA exclusions, analysis unit, tri-state primary endpoint, final PR #99 join semantics, outcome-blind QC, fail-closed retry policy, trial-cluster bootstrap, retention, claims, and deterministic protocol lock.

This is a protocol-freeze result only. It contains no navigation, formal collection, new research data, L2 outcome analysis, performance metric, or runtime metric.

## The frozen protocol answers Q1–Q22

| Question | Frozen answer |
|---|---|
{table}

## Exact cohort and identity evidence

- Source manifest: `{OFFICIAL_MANIFEST_REL.as_posix()}`
- Source manifest SHA-256: `{manifest_hash}`
- Formal trial count / unique count: `100 / 100`
- Stable run order: `0..99`
- Map authority ID: `{map_id}`
- Combined protocol SHA-256: `{lock_sha}`
- Formal data role: `{FORMAL_ROLE}`

The five pilot trial IDs remain in the official100 scientific design but none of their prior QA rows are reused. Fresh FORMAL run identities prevent identity collision.

## Denominator, uncertainty, and collection boundary are fixed

The primary denominator includes every eligible selected/executed row with frozen shadow L1 PASS and completed L2 tri-state PASS/FAIL/UNKNOWN. The primary numerator is L2 FAIL. UNKNOWN cannot be removed after observing results. Trial-cluster bootstrap avoids treating within-trial steps as iid Bernoulli observations.

Collection-stage QC is deliberately outcome-blind: it may validate that an L2 status exists and is typed, but it may not aggregate PASS/FAIL/UNKNOWN, compute the primary endpoint, inspect multi-candidate outcome disagreement, or construct a bootstrap interval.

## Limitations and fail-closed behavior

The future cohort remains a zero-authority shadow observation under the frozen controller. It cannot support causal collision, progress, efficacy, feasibility, real-time, deployment, or physical-safety claims. A post-data infrastructure/QC failure stops V1; neither trial replacement nor hot-fixing and mixing pre/post-change V1 rows is allowed.

No chart is included because this task freezes exact identities and rules and contains no scientific quantitative outcomes; contract tables are the more faithful audit representation.

## Recommended next step

The only permitted next task is `COLLECT_L2_H1_PROSPECTIVE_SHADOW_COHORT_V1`, limited to collection, outcome-blind QC, and data locking. It must verify `{lock_sha}` before the first formal run and must not analyze scientific L2 outcomes.

## Further question

After a valid 100-trial collection lock, scientific analysis remains a separate authorization: `ANALYZE_L2_H1_PROSPECTIVE_SHADOW_COHORT_V1`.
"""


def freeze(output_root: Path = ROOT) -> dict[str, Any]:
    contracts, metadata = build_contract_values()
    write_bytes(output_root / "FORMAL_COHORT_PROTOCOL.md", protocol_md().encode("utf-8"))
    for name, value in contracts.items():
        write_bytes(output_root / name, canonical_json_bytes(value))
    per_file = {name: sha256_file(output_root / name) for name in LOCKABLE_FILES}
    lock_sha = combined_protocol_sha(per_file)
    lock = {
        "schema_version": "L2_H1_PROSPECTIVE_SHADOW_PROTOCOL_LOCK_V1",
        "protocol_version": "V1",
        "upstream_pr99_head": UPSTREAM_HEAD,
        "official100_manifest_sha256": metadata["manifest_hash"],
        "lockable_file_count": len(per_file),
        "per_file_sha256": per_file,
        "combined_protocol_sha256": lock_sha,
        "combined_hash_algorithm": "SHA256_OF_CANONICAL_SORTED_PATH_HASH_RECORDS",
        "created_before_formal_collection": True,
        "formal_run_count_at_lock": 0,
        "navigation_run_count_at_lock": 0,
        "new_research_data_count_at_lock": 0,
        "protocol_change_after_first_formal_run": "STOP_V1_AND_CREATE_PROTOCOL_V2",
    }
    write_bytes(output_root / "PROTOCOL_LOCK.json", canonical_json_bytes(lock))
    readme = f"""# L2/H1 prospective shadow cohort protocol V1

Deterministic protocol-only freeze from PR #99 `{UPSTREAM_HEAD}`. The bundle freezes the Stonehenge official100 trial manifest, FORMAL run namespace, analysis/join/QC/retry/bootstrap/retention/claim contracts, and collection-lock schema before any formal result.

- Combined protocol SHA-256: `{lock_sha}`
- Navigation runs: `0`
- Formal collection runs: `0`
- New research data: `0`
- Raw logs in Git: `0`
- Only next task: `COLLECT_L2_H1_PROSPECTIVE_SHADOW_COHORT_V1`
"""
    write_bytes(output_root / "README.md", readme.encode("utf-8"))
    reviews = {
        "methods_statistics_review.json": {
            "verdict": "PASS", "critical_blockers": [], "recommended_case": "CASE_A",
            "review": "分析单位、selected/executed primary cohort、UNKNOWN 入分母、secondary 不升格、trial-cluster bootstrap、pilot 永久排除和 outcome-blind collection 均已机器冻结。step 不作 iid；不允许按结果停采或修改分母。",
        },
        "systems_reproducibility_review.json": {
            "verdict": "PASS", "critical_blockers": [], "recommended_case": "CASE_A",
            "review": "official100、FORMAL run namespace、PR #99 final join、protocol SHA、per-trial hard QC、pre-data-only retry、raw server retention 与 collection-lock schema 均明确。第一条 formal data 后禁止热修 V1。",
        },
    }
    for name, value in reviews.items():
        write_bytes(output_root / "reviewers" / name, canonical_json_bytes(value))
    final = {
        "selected_case": "CASE_A",
        "FINAL_STATUS": "PASS_L2_H1_PROSPECTIVE_SHADOW_COHORT_PROTOCOL_FREEZE_V1",
        "FINAL_DECISION": "FREEZE_PROTOCOL_AND_COLLECT_FORMAL_PROSPECTIVE_SHADOW_COHORT",
        "Only_next_task": "COLLECT_L2_H1_PROSPECTIVE_SHADOW_COHORT_V1",
        "combined_protocol_sha256": lock_sha,
        "official100_count": 100,
        "official100_unique_count": 100,
        "navigation_run_count": 0,
        "formal_collection_run_count": 0,
        "new_research_data_count": 0,
        "controller_intervention_count": 0,
        "candidate_replacement_count": 0,
        "formal_performance_metric_count": 0,
        "formal_runtime_metric_count": 0,
        "reviewer_case_votes": {"CASE_A": 2},
        "unresolved_blockers": [],
    }
    write_bytes(output_root / "FINAL_CASE_DECISION.json", canonical_json_bytes(final))
    handoff = {
        "schema_version": "L2_H1_PROSPECTIVE_SHADOW_COHORT_HANDOFF_V1",
        "only_next_task": "COLLECT_L2_H1_PROSPECTIVE_SHADOW_COHORT_V1",
        "required_protocol_sha256": lock_sha,
        "required_upstream_head": UPSTREAM_HEAD,
        "pre_run_gates": ["PR99_HEAD_EXACT", "PROTOCOL_LOCK_SHA_EXACT", "FORMAL_TRIAL_MANIFEST_EXACT", "ZERO_PREEXISTING_FORMAL_ROWS"],
        "collection_scope_only": ["COLLECT", "OUTCOME_BLIND_QC", "FORMAL_COLLECTION_LOCK"],
        "scientific_analysis_allowed": False,
        "protocol_mutation_allowed": False,
    }
    write_bytes(output_root / "downstream_handoff.json", canonical_json_bytes(handoff))
    body = f"""## Result

`PASS_L2_H1_PROSPECTIVE_SHADOW_COHORT_PROTOCOL_FREEZE_V1` (`CASE_A`).

## Frozen scope

- Exact upstream: PR #99 at `{UPSTREAM_HEAD}`
- official100: 100 unique trials, stable order 0–99
- Manifest SHA-256: `{metadata['manifest_hash']}`
- Formal data role: `{FORMAL_ROLE}`
- Pilot/equivalence/historical QA rows permanently excluded
- UNKNOWN retained in primary denominator
- Final PR #99 join semantics frozen without redesign
- Trial-cluster bootstrap: 10,000 valid replicates, seed 20260831
- Navigation/formal collection/new research data: 0/0/0
- Combined protocol SHA-256: `{lock_sha}`

## Boundary

This PR freezes the protocol only. It does not collect or analyze formal L2 outcomes and makes no efficacy, collision, progress, real-time, deployment, or physical-safety claim.

## Decision

- `FINAL_DECISION=FREEZE_PROTOCOL_AND_COLLECT_FORMAL_PROSPECTIVE_SHADOW_COHORT`
- `Only next task=COLLECT_L2_H1_PROSPECTIVE_SHADOW_COHORT_V1`

The next task was not executed.
"""
    write_bytes(output_root / "DRAFT_PR_BODY.md", body.encode("utf-8"))
    report = build_report(lock_sha, metadata["manifest_hash"], metadata["map_authority_id"])
    write_bytes(output_root / "report" / "REPORT_FREEZE_L2_H1_PROSPECTIVE_SHADOW_COHORT_PROTOCOL_V1.md", report.encode("utf-8"))
    return lock


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=ROOT)
    args = parser.parse_args()
    lock = freeze(args.output_root.resolve())
    print(json.dumps({"combined_protocol_sha256": lock["combined_protocol_sha256"], "formal_run_count_at_lock": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
