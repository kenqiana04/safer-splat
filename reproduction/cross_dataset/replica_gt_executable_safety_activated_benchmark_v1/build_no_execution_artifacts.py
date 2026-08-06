"""Create complete compact no-execution evidence after the fairness gate blocks."""
from __future__ import annotations

import csv
import io
import json

from common import canonical_json_bytes, sha256_bytes, write_json, write_text
from task_config import (
    BLOCK_DECISION, BLOCK_NEXT, BLOCK_STATUS, CANDIDATE_SEARCH_LIMIT, DT,
    MAP_SNAPSHOT_ID, MARGIN, NORMATIVE_MODEL, PR84_HEAD, ROBOT_RADIUS, SEED,
    TASK_NAME, TASK_ROOT, U_BOUND, V_BOUND,
)


def empty_csv(path, fields) -> None:
    buffer = io.StringIO(newline="")
    csv.writer(buffer, lineterminator="\n").writerow(fields)
    write_text(path, buffer.getvalue())


def main() -> None:
    fairness = json.loads((TASK_ROOT / "methods/fairness_audit.json").read_text(encoding="utf-8"))
    if fairness["fairness_pass"]:
        raise SystemExit("NO_EXECUTION_ARTIFACT_BUILDER_REQUIRES_BLOCKED_FAIRNESS")
    state = "NOT_EXECUTED_BLOCKED_BY_METHOD_FAIRNESS_CONTRACT_MISMATCH"
    counts = {group: 0 for group in ("G0", "G1", "G2", "G3", "G4", "G5")}
    physical_contract = {
        "status": "FROZEN_NOT_INVOKED_DUE_PRIOR_FAIRNESS_BLOCK",
        "allowed_prelock_checks": ["start outside official mesh", "minimum physical clearance", "goal outside official mesh", "finite state/goal", "velocity bounds", "map query availability"],
        "forbidden_prelock_checks": ["future reference collision", "formal rollout", "progress", "runtime", "method outcome"],
        "robot_radius_m": ROBOT_RADIUS, "map_snapshot_id": MAP_SNAPSHOT_ID,
    }
    search = {"status": state, "seed": SEED, "candidate_search_limit": CANDIDATE_SEARCH_LIMIT,
              "candidate_generation_count": 0, "physical_valid_count": 0,
              "map_query_valid_count": 0, "stage_predicate_evaluation_count": 0,
              "current_feasible_count": 0, "segment_safe_count": 0,
              "segment_unsafe_count": 0, "backup_primary_pass_count": 0,
              "backup_primary_fail_count": 0, "alternative_rescue_count": 0,
              "terminal_count": 0, "current_infeasible_count": 0,
              "duplicate_count": 0, "rejection_reasons": {"METHOD_FAIRNESS_GATE": 1}}
    registry = {"status": "NOT_CREATED_BLOCKED_BEFORE_REGISTRY", "state_count": 0,
                "states": [], "registry_sha256": None, "post_lock_deletion_count": 0,
                "post_lock_replacement_count": 0}
    write_json(TASK_ROOT / "scenario_generation/physical_admissibility_contract.json", physical_contract)
    empty_csv(TASK_ROOT / "scenario_generation/physical_admissibility_audit.csv", ["candidate_id", "status", "reason"])
    write_json(TASK_ROOT / "scenario_generation/candidate_search_summary.json", search)
    write_json(TASK_ROOT / "scenario_generation/group_activation_counts.json", {"status": state, "counts": counts, "quota_case": "NOT_ASSIGNED_PRESEARCH_BLOCK"})
    write_json(TASK_ROOT / "registry/replica_gt_executable_safety_registry_v1.json", registry)
    empty_csv(TASK_ROOT / "registry/replica_gt_executable_safety_registry_v1.csv", ["state_id", "group", "p0", "v0", "goal", "u_nom", "u_filtered"])
    write_json(TASK_ROOT / "registry/registry_lock.json", {"status": "NOT_LOCKED_BLOCKED_BEFORE_REGISTRY", "registry_sha256": None, "future_reference_access_allowed": False})
    write_json(TASK_ROOT / "registry/registry_rebuild_audit.json", {"status": "NOT_RUN_NO_REGISTRY", "fresh_process_rebuild_count": 0, "identical_sha_count": 0})
    write_json(TASK_ROOT / "reference/reference_oracle_contract.json", {"status": "FROZEN_IDENTITY_ONLY_NOT_INVOKED", "online_controller_access": False, "prelock_access_allowed": False, "distance_role": "OFFLINE_EVALUATION_ONLY"})
    write_json(TASK_ROOT / "reference/reference_oracle_validation.json", {"status": "UPSTREAM_VALIDATION_IDENTITY_FROZEN_NOT_REEXECUTED", "query_count": 0, "reason": BLOCK_STATUS})
    write_json(TASK_ROOT / "reference/reference_oracle_access_log.json", {"status": "PASS_ZERO_REFERENCE_ACCESS", "prelock_future_reference_read_count": 0, "reference_online_read_count": 0, "offline_postlock_query_count": 0, "events": []})
    empty_csv(TASK_ROOT / "reference/offline_reference_results.csv", ["state_id", "method", "reference_immediate_swept_collision", "reference_min_clearance_m"])
    empty_csv(TASK_ROOT / "benchmark/one_step_records.csv", ["state_id", "group", "method", "committed", "status", "total_runtime_s", "deadline_miss"])
    empty_csv(TASK_ROOT / "benchmark/rollout_records.csv", ["state_id", "group", "method", "step", "status", "progress"])
    empty_csv(TASK_ROOT / "benchmark/episode_summary.csv", ["state_id", "group", "method", "terminal_reason", "executed_steps", "progress"])
    empty_csv(TASK_ROOT / "benchmark/paired_method_summary.csv", ["group", "method", "state_count", "commit_rate", "fail_closed_rate"])
    write_json(TASK_ROOT / "benchmark/timing_by_method_group.json", {"status": state, "decision_count": 0, "methods": {}})
    write_json(TASK_ROOT / "benchmark/deadline_audit.json", {"status": state, "dt_seconds": DT, "deadline_miss_count": 0, "decision_count": 0, "deadline_miss_rate": None, "real_time_claim": False})
    hypotheses = {"status": "PREREGISTERED_NOT_TESTED", "statistical_unit": "state_or_episode_not_step", "holm_correction": True,
                  "hypotheses": {"H1": "G1 B1 vs B0 segment-risk rejection", "H2": "G2/G3 B2 vs B1 backup noncommit", "H3": "G3 B3 vs B2 certified availability/progress", "H4": "G0 B3 over-rejection audit", "H5": "B3 vs B0 configuration-specific reference outcome"}}
    write_json(TASK_ROOT / "statistics/preregistered_hypotheses.json", hypotheses)
    empty_csv(TASK_ROOT / "statistics/paired_tests.csv", ["hypothesis", "group", "comparison", "test", "n", "raw_p", "holm_p", "status"])
    empty_csv(TASK_ROOT / "statistics/effect_sizes.csv", ["hypothesis", "group", "comparison", "metric", "effect", "status"])
    empty_csv(TASK_ROOT / "statistics/confidence_intervals.csv", ["hypothesis", "group", "comparison", "metric", "lower_95", "upper_95", "status"])
    leakage = {"status": "PASS_NO_SELECTION_OCCURRED", "prelock_future_reference_reads": 0,
               "prelock_formal_rollout_reads": 0, "group_assignment_count": 0,
               "collision_based_selection": False, "progress_based_selection": False,
               "runtime_based_selection": False, "method_winning_selection": False,
               "post_lock_deletion": 0, "replacement": 0, "threshold_change": 0, "map_mutation": 0}
    claim = {"status": "PASS_CLAIM_BOUNDARY_AUDIT", "scientific_results_available": False,
             "allowed_claim": "PR84 method matrix is not executable fairly because the concrete alternative library is not frozen.",
             "forbidden_claims_made": [], "represented_reference_separated": True,
             "fail_closed_not_safe_stop": True, "candidate_exhaustion_not_unrecoverable": True,
             "logical_rollout_not_real_time": True}
    counters = {
        "map_training_count": 0, "map_mutation_count": 0, "dataset_switch_count": 0,
        "protected_source_mutation_count": 0, "controller_parameter_tuning_count": 0,
        "safety_threshold_tuning_count": 0, "candidate_generation_count": 0,
        "physical_valid_count": 0, "stage_predicate_evaluation_count": 0,
        "candidate_search_limit": CANDIDATE_SEARCH_LIMIT, "registry_state_count": 0,
        "registry_rebuild_count": 0, "prelock_future_reference_read_count": 0,
        "prelock_formal_rollout_count": 0, "reference_online_read_count": 0,
        "one_step_method_run_count": 0, "logical_episode_count": 0,
        "logical_control_step_count": 0, "formal_attempt_count": 0,
        "represented_false_safe_count": 0, "map_reference_disagreement_count": 0,
        "alternative_rescue_count": 0, "fail_closed_count": 0,
        "deadline_miss_count": 0, "infrastructure_failure_count": 0,
        "operational_autonomy_action_count": 3, "task_owned_process_cleanup_count": 0,
    }
    write_json(TASK_ROOT / "audits/selection_leakage_audit.json", leakage)
    write_json(TASK_ROOT / "audits/claim_boundary_audit.json", claim)
    write_json(TASK_ROOT / "audits/cohort_overlap_audit.json", {"status": "NOT_APPLICABLE_NO_COHORT", "state_count": 0, "duplicate_count": 0, "mutual_exclusivity_violations": 0})
    write_json(TASK_ROOT / "audits/execution_count_audit.json", {"status": "PASS_ZERO_EXECUTION_BOUNDARY", "counters": counters})
    actions = {"task": TASK_NAME, "action_count": 3, "actions": [
        {"id": "OA-01", "type": "ISOLATED_GIT_WORKTREE", "action": "Created the authorized branch at exact PR84 head without touching the dirty primary worktree.", "scientific_contract_change": False},
        {"id": "OA-02", "type": "FAIL_CLOSED_METHOD_GATE", "action": "Stopped before candidate generation rather than inventing the missing alternative candidate library.", "scientific_contract_change": False},
        {"id": "OA-03", "type": "SERVER_TASK_ROOT_PROVISION", "action": "Created the authorized task-owned maintenance record root for compact evidence synchronization; no scientific input or runtime was changed.", "scientific_contract_change": False},
    ]}
    write_json(TASK_ROOT / "operational_autonomy_actions.json", actions)
    manifest = {"task": TASK_NAME, "branch": "replica-gt-executable-safety-activated-benchmark-v1",
                "base": "fas-cbf-unified-executable-safety-certifier-v1", "base_head": PR84_HEAD,
                "status": BLOCK_STATUS, "decision": BLOCK_DECISION, "only_next_task": BLOCK_NEXT,
                "phase_reached": "PHASE_0_METHOD_FAIRNESS_GATE", "formal_attempt_count": 0,
                "normative_model": NORMATIVE_MODEL, "dt": DT, "u_bound": U_BOUND,
                "v_bound": V_BOUND, "robot_radius": ROBOT_RADIUS, "margin": MARGIN,
                "counters": counters}
    write_json(TASK_ROOT / "report/run_manifest.json", manifest)
    print("PASS_NO_EXECUTION_BLOCKER_ARTIFACTS", sha256_bytes(canonical_json_bytes(counters)))


if __name__ == "__main__":
    main()
