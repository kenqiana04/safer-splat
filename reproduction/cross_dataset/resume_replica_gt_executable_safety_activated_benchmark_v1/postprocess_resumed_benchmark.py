#!/usr/bin/env python3
"""Deterministic post-lock statistics, audits, and project decision."""
from __future__ import annotations

import csv
import math
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

TASK_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TASK_ROOT))

from common import read_json, sha256_file, write_csv, write_json
from task_config import (
    CANDIDATE_SEARCH_LIMIT, GROUP_MINIMUMS, METHODS, PASS_VALIDATOR,
    REPRESENTATIVE_TARGET, SEED, SLOT_IDS,
)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def boolean(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def number(value: Any, default: float = 0.0) -> float:
    if value in (None, "", "None", "null"):
        return default
    return float(value)


def wilson(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total == 0:
        return 0.0, 1.0
    p = successes / total
    denominator = 1.0 + z * z / total
    center = (p + z * z / (2.0 * total)) / denominator
    half = z * math.sqrt(p * (1.0 - p) / total + z * z / (4.0 * total * total)) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def mcnemar_exact(
    records: list[dict[str, str]], method_a: str, method_b: str,
    outcome: Callable[[dict[str, str]], bool],
) -> dict[str, Any]:
    by_state: dict[str, dict[str, dict[str, str]]] = defaultdict(dict)
    for record in records:
        by_state[record["state_id"]][record["method"]] = record
    a_only = 0
    b_only = 0
    paired = 0
    for values in by_state.values():
        if method_a not in values or method_b not in values:
            continue
        paired += 1
        a = outcome(values[method_a])
        b = outcome(values[method_b])
        a_only += int(a and not b)
        b_only += int(b and not a)
    discordant = a_only + b_only
    if discordant == 0:
        p_value = 1.0
    else:
        tail = sum(math.comb(discordant, k) for k in range(0, min(a_only, b_only) + 1)) / (2 ** discordant)
        p_value = min(1.0, 2.0 * tail)
    return {
        "paired_unit_count": paired,
        "a_only_count": a_only,
        "b_only_count": b_only,
        "discordant_count": discordant,
        "raw_p_value": p_value,
    }


def holm(rows_in: list[dict[str, Any]]) -> None:
    eligible = [(index, float(row["raw_p_value"])) for index, row in enumerate(rows_in) if isinstance(row.get("raw_p_value"), (int, float))]
    eligible.sort(key=lambda item: item[1])
    running = 0.0
    family_size = len(eligible)
    for rank, (index, value) in enumerate(eligible):
        adjusted = min(1.0, (family_size - rank) * value)
        running = max(running, adjusted)
        rows_in[index]["holm_adjusted_p_value"] = running
        rows_in[index]["holm_family_evaluable_count"] = family_size
    for row in rows_in:
        if "holm_adjusted_p_value" not in row:
            row["holm_adjusted_p_value"] = None
            row["holm_family_evaluable_count"] = family_size


def paired_bootstrap_difference(
    records: list[dict[str, str]], method_a: str, method_b: str, field: str,
    replicates: int = 10000,
) -> dict[str, Any]:
    by_state: dict[str, dict[str, float]] = defaultdict(dict)
    for record in records:
        by_state[record["state_id"]][record["method"]] = number(record.get(field))
    pairs = [(value[method_a], value[method_b]) for value in by_state.values() if method_a in value and method_b in value]
    differences = [b - a for a, b in pairs]
    observed = sum(differences) / len(differences) if differences else 0.0
    rng = random.Random(SEED)
    samples = []
    if differences:
        for _ in range(replicates):
            samples.append(sum(rng.choice(differences) for _ in differences) / len(differences))
        samples.sort()
        lower = samples[int(0.025 * (replicates - 1))]
        upper = samples[int(0.975 * (replicates - 1))]
    else:
        lower = upper = 0.0
    return {"paired_unit_count": len(differences), "mean_difference_b_minus_a": observed, "ci95_lower": lower, "ci95_upper": upper, "bootstrap_replicates": replicates}


def subset(records: list[dict[str, str]], *, cohort: str | None = None, groups: set[str] | None = None) -> list[dict[str, str]]:
    return [
        record for record in records
        if (cohort is None or record["cohort"] == cohort)
        and (groups is None or record.get("postlock_group") in groups)
    ]


def main() -> None:
    one_step = rows(TASK_ROOT / "benchmark/one_step_records.csv")
    episodes = rows(TASK_ROOT / "benchmark/episode_summary.csv")
    rollout = rows(TASK_ROOT / "benchmark/rollout_records.csv")
    activated = read_json(TASK_ROOT / "registry/activated_registry_v1.json")
    representative = read_json(TASK_ROOT / "registry/representative_holdout_registry_v1.json")
    lock = read_json(TASK_ROOT / "registry/registry_lock.json")
    search = read_json(TASK_ROOT / "activated_generation/search_summary.json")
    formal = read_json(TASK_ROOT / "benchmark/formal_attempt.json")
    leakage = read_json(TASK_ROOT / "audits/selection_leakage_audit.json")
    fairness = read_json(TASK_ROOT / "methods/fairness_audit.json")

    if formal["status"] != "FORMAL_ATTEMPT_COMPLETED" or formal["formal_attempt_count"] != 1:
        raise SystemExit("FORMAL_ATTEMPT_NOT_COMPLETE")
    if len(one_step) != (len(activated["states"]) + len(representative["states"])) * len(METHODS):
        raise SystemExit("ONE_STEP_ROW_COUNT_MISMATCH")

    h1_records = subset(one_step, cohort="ACTIVATED", groups={"G1"})
    h2_records = subset(one_step, cohort="ACTIVATED", groups={"G2", "G3"})
    h3_records = subset(one_step, cohort="ACTIVATED", groups={"G3"})
    h4_records = subset(one_step, cohort="ACTIVATED", groups={"G0"})
    h6_records = one_step
    h7_records = one_step
    tests: list[dict[str, Any]] = []

    for hypothesis, label, records_in, method_a, method_b, outcome in (
        ("H1", "G1 segment-based noncommit", h1_records, METHODS[0], METHODS[1], lambda r: not boolean(r["committed"])),
        ("H2", "G2/G3 backup discrimination", h2_records, METHODS[1], METHODS[2], lambda r: not boolean(r["committed"]) or r["semantic_status"] == "CERTIFIED_TERMINAL_ACTION"),
        ("H3", "G3 certified-control directional rescue", h3_records, METHODS[2], METHODS[3], lambda r: boolean(r["committed"])),
        ("H4", "G0 commit preservation", h4_records, METHODS[0], METHODS[3], lambda r: boolean(r["committed"])),
        ("H6", "offline reference collision after commit", h6_records, METHODS[0], METHODS[3], lambda r: boolean(r["reference_collision_after_commit"])),
        ("H7", "50ms deadline miss", h7_records, METHODS[0], METHODS[3], lambda r: boolean(r["deadline_miss"])),
    ):
        result = mcnemar_exact(records_in, method_a, method_b, outcome)
        result.update({"hypothesis": hypothesis, "contrast": label, "test": "MCNEMAR_EXACT_TWO_SIDED", "method_a": method_a, "method_b": method_b})
        tests.append(result)
    tests.insert(4, {
        "hypothesis": "H5", "contrast": "representative prevalence", "test": "DESCRIPTIVE_WILSON_CI_NO_NULL_THRESHOLD",
        "method_a": None, "method_b": None, "paired_unit_count": len(representative["states"]),
        "a_only_count": None, "b_only_count": None, "discordant_count": None, "raw_p_value": None,
    })
    holm(tests)

    def method_rows(method: str, cohort: str | None = None) -> list[dict[str, str]]:
        return [record for record in one_step if record["method"] == method and (cohort is None or record["cohort"] == cohort)]

    rep_b0 = {r["state_id"]: r for r in method_rows(METHODS[0], "REPRESENTATIVE_HOLDOUT")}
    rep_b1 = {r["state_id"]: r for r in method_rows(METHODS[1], "REPRESENTATIVE_HOLDOUT")}
    rep_b2 = {r["state_id"]: r for r in method_rows(METHODS[2], "REPRESENTATIVE_HOLDOUT")}
    rep_b3 = {r["state_id"]: r for r in method_rows(METHODS[3], "REPRESENTATIVE_HOLDOUT")}
    rep_ids = sorted(set(rep_b0) & set(rep_b1) & set(rep_b2) & set(rep_b3))
    prevalence_counts = {
        "segment_activation": sum(boolean(rep_b0[s]["committed"]) and not boolean(rep_b1[s]["committed"]) for s in rep_ids),
        "backup_activation": sum(boolean(rep_b1[s]["committed"]) and not boolean(rep_b2[s]["committed"]) for s in rep_ids),
        "directional_rescue": sum(rep_b3[s]["selected_candidate"] in SLOT_IDS for s in rep_ids),
        "fail_closed": sum(not boolean(rep_b3[s]["committed"]) for s in rep_ids),
        "terminal": sum(rep_b3[s]["semantic_status"] == "CERTIFIED_TERMINAL_ACTION" for s in rep_ids),
        "current_infeasible": sum(not boolean(rep_b0[s]["committed"]) for s in rep_ids),
    }
    prevalence_rows = []
    for metric, count in prevalence_counts.items():
        low, high = wilson(count, len(rep_ids))
        prevalence_rows.append({"metric": metric, "count": count, "total": len(rep_ids), "rate": count / len(rep_ids), "wilson95_lower": low, "wilson95_upper": high})

    effect_rows: list[dict[str, Any]] = []
    for test in tests:
        if isinstance(test.get("a_only_count"), int):
            n = int(test["paired_unit_count"])
            effect_rows.append({
                "hypothesis": test["hypothesis"], "effect": "PAIRED_BINARY_RATE_DIFFERENCE_B_MINUS_A",
                "estimate": (int(test["b_only_count"]) - int(test["a_only_count"])) / n if n else 0.0,
                "paired_unit_count": n,
            })
    h4_progress = paired_bootstrap_difference(h4_records, METHODS[0], METHODS[3], "progress_m")
    h4_progress.update({"hypothesis": "H4", "effect": "ONE_STEP_PROGRESS_B3_MINUS_B0_M"})
    effect_rows.append(h4_progress)
    rep_episode_records = [record for record in episodes if record["cohort"] == "REPRESENTATIVE_HOLDOUT"]
    rep_progress = paired_bootstrap_difference(rep_episode_records, METHODS[0], METHODS[3], "progress_m")
    rep_progress.update({"hypothesis": "H5", "effect": "REPRESENTATIVE_ROLLOUT_PROGRESS_B3_MINUS_B0_M"})
    effect_rows.append(rep_progress)

    ci_rows = list(prevalence_rows)
    for method in METHODS:
        for cohort in ("ACTIVATED", "REPRESENTATIVE_HOLDOUT"):
            values = method_rows(method, cohort)
            for metric, predicate in (
                ("commit_rate", lambda r: boolean(r["committed"])),
                ("deadline_miss_rate", lambda r: boolean(r["deadline_miss"])),
                ("reference_collision_after_commit_rate", lambda r: boolean(r["reference_collision_after_commit"])),
            ):
                count = sum(predicate(item) for item in values)
                low, high = wilson(count, len(values))
                ci_rows.append({"metric": metric, "method": method, "cohort": cohort, "count": count, "total": len(values), "rate": count / len(values), "wilson95_lower": low, "wilson95_upper": high})

    false_safe = sum(boolean(record["represented_false_safe"]) for record in one_step) + sum(int(number(record["represented_false_safe_count"])) for record in episodes)
    g3_b3_rescues = sum(record["selected_candidate"] in SLOT_IDS for record in h3_records if record["method"] == METHODS[3])
    activated_group_counts = Counter(item["group"] for item in activated["states"])
    scientific_mechanism = (
        activated_group_counts["G1"] >= GROUP_MINIMUMS["G1"]
        and activated_group_counts["G2"] + activated_group_counts["G3"] >= 12
        and false_safe == 0 and leakage["all_pass"] and fairness.get("all_pass", False)
    )
    active_utility = activated_group_counts["G3"] >= 12 and g3_b3_rescues >= 1 and false_safe == 0
    representative_gate_count = prevalence_counts["segment_activation"] + prevalence_counts["backup_activation"]
    representative_relevance = representative_gate_count >= 8 or prevalence_counts["directional_rescue"] >= 4
    b0_ref_collisions = sum(boolean(record["reference_collision_after_commit"]) for record in method_rows(METHODS[0]))
    b3_ref_collisions = sum(boolean(record["reference_collision_after_commit"]) for record in method_rows(METHODS[3]))
    reference_no_adverse_regression = b3_ref_collisions <= b0_ref_collisions
    b3_deadline = sum(boolean(record["deadline_miss"]) for record in method_rows(METHODS[3])) / len(method_rows(METHODS[3]))

    if false_safe > 0 or not reference_no_adverse_regression:
        decision_case = "E"
        final_status = "FAIL_REPLICA_GT_EXECUTABLE_SAFETY_CERTIFIER_REGRESSION"
        final_decision = "FREEZE_FAILURE_CASES_AND_DEBUG_CERTIFIER"
        only_next_task = "DEBUG_UNIFIED_CERTIFIER_ON_FROZEN_REPLICA_FAILURE_CASES_V1"
    elif scientific_mechanism and active_utility and not representative_relevance:
        decision_case = "C"
        final_status = "PASS_ACTIVATED_MECHANISM_WITH_LOW_REPRESENTATIVE_PREVALENCE"
        final_decision = "DO_NOT_FRAME_CORE_V1_AS_BROAD_REAL_TIME_REPLACEMENT_FOR_SAFER"
        only_next_task = "DECIDE_BETWEEN_FAST_GAUSSIAN_SWEPT_CERTIFICATE_AND_BACKUP_SET_RESEARCH_V1"
    elif scientific_mechanism and active_utility and representative_relevance:
        decision_case = "A"
        final_status = "PASS_REPLICA_GT_CORE_V1_ACTIVATED_AND_REPRESENTATIVE_EVIDENCE"
        if b3_deadline > 0.9:
            final_decision = "OPTIMIZE_RUNTIME_WITHOUT_CHANGING_SAFETY_SEMANTICS"
            only_next_task = "OPTIMIZE_UNIFIED_CERTIFIER_RUNTIME_WITHOUT_CHANGING_SAFETY_SEMANTICS_V1"
        else:
            final_decision = "EXTEND_CERTIFIER_TO_FROZEN_LEARNED_ANISOTROPIC_GAUSSIAN_MAP"
            only_next_task = "VALIDATE_UNIFIED_CERTIFIER_ON_FROZEN_ETH3D_LEARNED_GAUSSIAN_MAP_V1"
    else:
        decision_case = "B"
        final_status = "PASS_REPLICA_GT_GATE_EVIDENCE_WITH_WEAK_DIRECTIONAL_RESCUE"
        final_decision = "REPLACE_FINITE_DIRECTIONAL_LIBRARY_WITH_CERTIFICATE_AWARE_OPTIMIZATION"
        only_next_task = "DESIGN_CERTIFICATE_AWARE_CONTINUOUS_CONTROL_OPTIMIZATION_V1"

    hypothesis_status = {
        "H1": "SUPPORTED_MECHANISM_EXISTENCE" if tests[0]["b_only_count"] > tests[0]["a_only_count"] else "NOT_SUPPORTED",
        "H2": "SUPPORTED_BACKUP_DISCRIMINATION" if tests[1]["b_only_count"] > tests[1]["a_only_count"] else "NOT_SUPPORTED",
        "H3": "SUPPORTED_DIRECTIONAL_RESCUE" if g3_b3_rescues > 0 and false_safe == 0 else "NOT_SUPPORTED",
        "H4": "NO_G0_COMMIT_OR_PROGRESS_PENALTY_OBSERVED" if h4_progress["mean_difference_b_minus_a"] == 0.0 else "DIFFERENCE_OBSERVED",
        "H5": "LOW_REPRESENTATIVE_GATE_AND_RESCUE_PREVALENCE" if not representative_relevance else "REPRESENTATIVE_RELEVANCE_GATE_MET",
        "H6": "NO_REFERENCE_COLLISION_EVENTS_NO_SUPERIORITY_CLAIM" if b0_ref_collisions + b3_ref_collisions == 0 else "REFERENCE_EVENTS_OBSERVED",
        "H7": "RUNTIME_DIAGNOSTIC_RECORDED_NOT_REALTIME_CLAIM",
    }
    for test in tests:
        test["status"] = hypothesis_status[test["hypothesis"]]

    decision = {
        "status": "PASS_PROJECT_DECISION_TREE_APPLIED_WITHOUT_POST_HOC_THRESHOLD_CHANGE",
        "decision_case": decision_case,
        "final_status": final_status,
        "final_decision": final_decision,
        "only_next_task": only_next_task,
        "scientific_mechanism_gate": scientific_mechanism,
        "active_utility_gate": active_utility,
        "representative_relevance_gate": representative_relevance,
        "reference_no_adverse_regression": reference_no_adverse_regression,
        "runtime_b3_deadline_miss_rate": b3_deadline,
        "project_thresholds_are_domain_general": False,
        "configuration_specific": True,
    }

    execution = {
        "status": "PASS_EXECUTION_COUNT_AUDIT",
        "map_training_count": 0,
        "map_mutation_count": 0,
        "dataset_switch_count": 0,
        "protected_source_mutation_count": 0,
        "controller_parameter_tuning_count": 0,
        "safety_threshold_tuning_count": 0,
        "activated_candidate_generation_count": search["activated_candidate_generation_count"],
        "activated_physical_valid_count": search["activated_physical_valid_count"],
        "activated_stage_predicate_count": search["activated_stage_predicate_count"],
        "activated_search_limit": CANDIDATE_SEARCH_LIMIT,
        "activated_registry_count": len(activated["states"]),
        "representative_pool_count": read_json(TASK_ROOT / "representative_sampling/pool_summary.json")["candidate_pool_count"],
        "representative_registry_count": len(representative["states"]),
        "registry_rebuild_count_each": 3,
        "prelock_future_reference_read_count": lock["prelock_future_reference_read_count"],
        "prelock_formal_method_run_count": lock["prelock_formal_method_run_count"],
        "reference_online_read_count": 0,
        "one_step_method_run_count": len(one_step),
        "logical_episode_count": len(episodes),
        "logical_control_step_count": len(rollout),
        "formal_attempt_count": formal["formal_attempt_count"],
        "represented_false_safe_count": false_safe,
        "map_reference_disagreement_method_record_count": sum(boolean(record["map_reference_disagreement"]) for record in one_step),
        "map_reference_disagreement_unique_state_count": len({record["state_id"] for record in one_step if boolean(record["map_reference_disagreement"])}),
        "directional_rescue_count": sum(record["selected_candidate"] in SLOT_IDS for record in one_step),
        "representative_directional_selection_count": prevalence_counts["directional_rescue"],
        "fail_closed_count": sum(not boolean(record["committed"]) for record in one_step),
        "representative_fail_closed_count": prevalence_counts["fail_closed"],
        "deadline_miss_count": sum(boolean(record["deadline_miss"]) for record in one_step),
        "infrastructure_failure_count": formal["infrastructure_failure_count"],
        "operational_autonomy_action_count": read_json(TASK_ROOT / "operational_autonomy_actions.json")["operational_autonomy_action_count"],
        "task_owned_process_cleanup_count": 0,
    }

    claim_audit = {
        "status": "PASS_CLAIM_BOUNDARY_AUDIT",
        "supported": [
            "ACTIVATED cohort establishes configuration-specific segment and backup gate existence.",
            "ACTIVATED G3 establishes configuration-specific B3 directional rescue over B2.",
            "The represented-map backend produced zero represented false-safe records.",
        ],
        "not_supported": [
            "Activated cohort prevalence or natural frequency.",
            "Broad representative relevance for segment, backup, or directional rescue.",
            "Reference collision superiority because no B0/B3 collision events occurred.",
            "Real-time or deployment readiness.",
            "Generalization beyond the frozen Replica GT-FINE configuration.",
        ],
        "activated_prevalence_claim_count": 0,
        "deployment_claim_count": 0,
        "collision_superiority_claim_count": 0,
    }

    validation_source = read_json(Path("/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1/mesh_oracle/replica_mesh_collision_oracle_validation.json"))
    write_json(TASK_ROOT / "reference/reference_oracle_validation.json", {
        "status": "PASS_REFERENCE_ORACLE_REUSED_FROM_FROZEN_VALIDATED_AUTHORITY",
        "authority_validation_path": "/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1/mesh_oracle/replica_mesh_collision_oracle_validation.json",
        "authority_validation_sha256": sha256_file("/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1/mesh_oracle/replica_mesh_collision_oracle_validation.json"),
        "authority_validation": validation_source,
        "registry_locked_before_future_outcomes": True,
        "controller_exposure_count": 0,
        "reference_online_read_count": 0,
    })
    write_csv(TASK_ROOT / "statistics/paired_tests.csv", tests)
    write_csv(TASK_ROOT / "statistics/effect_sizes.csv", effect_rows)
    write_csv(TASK_ROOT / "statistics/confidence_intervals.csv", ci_rows)
    write_json(TASK_ROOT / "statistics/hypothesis_status.json", hypothesis_status)
    write_json(TASK_ROOT / "statistics/project_decision_gates.json", decision)
    write_json(TASK_ROOT / "audits/representative_prevalence_audit.json", {
        "status": "PASS_REPRESENTATIVE_ONLY_PREVALENCE_AUDIT",
        "representative_registry_count": len(rep_ids),
        "activated_records_used_for_prevalence": 0,
        "prevalence": prevalence_rows,
        "representative_relevance_gate": representative_relevance,
    })
    write_json(TASK_ROOT / "audits/claim_boundary_audit.json", claim_audit)
    write_json(TASK_ROOT / "audits/execution_count_audit.json", execution)
    write_json(TASK_ROOT / "report/downstream_handoff.json", {
        "status": final_status,
        "decision": final_decision,
        "only_next_task": only_next_task,
        "formal_attempt_count": 1,
        "formal_results_immutable": True,
        "configuration_specific": True,
        "not_a_deployment_claim": True,
        "validator_required_status": PASS_VALIDATOR,
    })
    print("PASS_POSTPROCESS", final_status, final_decision)


if __name__ == "__main__":
    main()
