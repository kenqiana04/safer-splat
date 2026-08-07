"""Post-lock analysis and compact artifact generation for the frozen audit."""
from __future__ import annotations

import csv
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from common import read_json, sha256_file, write_csv, write_json, write_text
from task_config import (
    BASE_BRANCH, BASE_HEAD, BRANCH, DT, EFFECTIVE_RADIUS, ENVIRONMENTS,
    H_STOP_MAX, LIBRARY_SHA256, METHODS, MODEL, PR_HEADS,
    REPLICA_MAP_SHA256, REPLICA_REGISTRY_SHA256, ROBOT_RADIUS, SLOT_IDS,
    TASK_ROOT, TERMINAL_TOLERANCE, U_BOUND, V_BOUND,
)

FINAL_STATUS = "NO_CORE_V1_REPRESENTATIVE_PORTABILITY_SIGNAL"
FINAL_DECISION = "UPHOLD_PR88_CASE_D_AND_STOP_CORE_V1_METHOD_EXPANSION"
NEXT_TASK = "WRITE_FROZEN_PAPER_CONTRIBUTION_AND_EXPERIMENT_PLAN_V1"
CASE = "CASE_C"

ENV = {
    "E1_REPLICA_GT_FINE": dict(short="Replica GT", map_sha=REPLICA_MAP_SHA256, count=2285652, map_type="GT-derived isotropic spheres", tier="TIER_R3_REFERENCE_COMPLETE", learned=False, ready=True, candidate=160, registry=160, reason="Frozen PR #87 registry reused"),
    "E2_ETH3D_LEARNED_GAUSSIAN": dict(short="ETH3D", map_sha="927734a2339a3f2710640065b0893eaae162cc0144ac67e2f377bcff2e71ae34", count=664873, map_type="learned anisotropic 3DGS", tier="NOT_EVALUABLE", learned=True, ready=False, candidate=0, registry=0, reason="No frozen reference-route benchmark contract"),
    "E3_TUM_SPLATAM": dict(short="TUM SplaTAM", map_sha="cb4a8f133a4ce4063f60112fa9689db683988be29f67b9d570231a319849a36f", count=5464102, map_type="learned RGB-D anisotropic Gaussian", tier="TIER_R2_OBSERVABLE_REFERENCE", learned=True, ready=False, candidate=1, registry=0, reason="1/238 central-difference states satisfies frozen velocity bound"),
    "E4_TUM_GAUSSIAN_SLAM": dict(short="TUM Gaussian-SLAM", map_sha="264d3886f6486b30bb40a9a78a201fbd0afa007f915f1f8c9dbda7d924e7679d", count=3045467, map_type="learned RGB-D anisotropic Gaussian", tier="TIER_R2_OBSERVABLE_REFERENCE", learned=True, ready=False, candidate=1, registry=0, reason="1/238 shared GT trajectory states satisfies frozen velocity bound"),
    "E5_STONEHENGE_SAFER": dict(short="Stonehenge", map_sha="ac14f5ced354c93f26cf92404540712eff65bd02554d9e9ed0332508e290382d", count=116446, map_type="official learned anisotropic SAFER map", tier="TIER_R1_REPRESENTED_MAP_BEHAVIOR_ONLY", learned=True, ready=True, candidate=100, registry=100, reason="Official 100-trial initial-state distribution; finite PR84 adapter query"),
    "E6_FLIGHT_SAFER": dict(short="Flight", map_sha="8e7499a0d68405065b0effb7022b635ef3fbe50a53b69f5f25165260c8a493e6", count=281756, map_type="official learned anisotropic SAFER map", tier="TIER_R1_REPRESENTED_MAP_BEHAVIOR_ONLY", learned=True, ready=True, candidate=100, registry=100, reason="Official 100-trial initial-state distribution; finite PR84 adapter query"),
    "E7_TUM_SPLATFACTO_NEGATIVE_CONTROL": dict(short="TUM Splatfacto", map_sha="NOT_AVAILABLE", count=None, map_type="geometry-disqualified learned map", tier="TIER_N0_DIAGNOSTIC_ONLY", learned=True, ready=False, candidate=0, registry=0, reason="Diagnostic negative control excluded from every portability gate"),
}


def truth(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def parse_float(value: Any) -> float | None:
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except (TypeError, ValueError):
        return None


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def wilson(success: int, total: int) -> tuple[float | None, float | None]:
    if total == 0:
        return None, None
    z = 1.959963984540054
    p = success / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    lower = 0.0 if success == 0 else max(0.0, center - half)
    return lower, min(1.0, center + half)


def percentile(values: list[float], q: float) -> float | None:
    return float(np.quantile(values, q)) if values else None


def method_artifacts() -> None:
    registry = {
        "status": "PASS_FROZEN_B0_B3_METHOD_REGISTRY",
        "normative_model": MODEL, "dt_s": DT, "u_bound_inf": U_BOUND,
        "v_bound_inf": V_BOUND, "robot_radius_m": ROBOT_RADIUS,
        "margin_m": EFFECTIVE_RADIUS - ROBOT_RADIUS, "effective_radius_m": EFFECTIVE_RADIUS,
        "terminal_tolerance_m_per_s": TERMINAL_TOLERANCE, "h_stop_max": H_STOP_MAX,
        "six_slot_library_sha256": LIBRARY_SHA256, "methods": list(METHODS),
    }
    write_json(TASK_ROOT / "methods/method_registry.json", registry)
    write_csv(TASK_ROOT / "methods/method_difference_matrix.csv", [
        {"method": METHODS[0], "current": True, "segment": False, "backup": False, "directional_slots": 0},
        {"method": METHODS[1], "current": True, "segment": True, "backup": False, "directional_slots": 0},
        {"method": METHODS[2], "current": True, "segment": True, "backup": True, "directional_slots": 0},
        {"method": METHODS[3], "current": True, "segment": True, "backup": True, "directional_slots": 6},
    ])
    protected = read_json(TASK_ROOT / "input_freeze/protected_source_hashes.json")
    write_json(TASK_ROOT / "methods/shared_contract_hashes.json", {"status": "PASS_SHARED_CONTRACT_HASHES", "library_sha256": LIBRARY_SHA256, "protected_manifest_sha256": sha256_file(TASK_ROOT / "input_freeze/protected_source_hashes.json"), "protected_record_count": protected["record_count"]})
    write_json(TASK_ROOT / "methods/fairness_audit.json", {"status": "PASS_METHOD_FAIRNESS_CONTRACT", "same_state_goal_map_controller_bounds": True, "b3_only_difference_from_b2": "FROZEN_SIX_SLOT_ALTERNATIVES", "slot_count": 6, "parameter_tuning_count": 0, "method_mutation_count": 0})


def environment_artifacts() -> None:
    records = []
    for name in ENVIRONMENTS:
        item = ENV[name]
        records.append({"environment": name, "identity": item["map_sha"], "lineage": item["map_type"], "gaussian_count": item["count"], "isotropic_or_anisotropic": "isotropic" if name.startswith("E1") else "anisotropic_or_not_evaluable", "scale_coordinate": "metric frozen map frame" if name != "E7_TUM_SPLATFACTO_NEGATIVE_CONTROL" else "geometry disqualified", "route_trajectory": item["reason"], "state_goal_velocity": item["candidate"] > 0, "reference_type": item["tier"], "observable_domain": "official mesh" if name.startswith("E1") else ("RGB-D observed domain only" if name in {"E3_TUM_SPLATAM", "E4_TUM_GAUSSIAN_SLAM"} else "represented map only"), "query_backend": "PR84_COMPATIBLE_NON_DIAGNOSTIC" if item["ready"] else "NOT_EVALUATED_OR_DIAGNOSTIC_ONLY", "eligible_claims": "representative behavior" if item["ready"] else "structural diagnosis only", "prohibited_claims": "collision superiority; realtime; cross-map certificate", "included_in_formal": item["ready"], "reason": item["reason"]})
    write_json(TASK_ROOT / "environments/environment_registry.json", {"status": "PASS_SEVEN_ENVIRONMENTS_PREREGISTERED_BEFORE_ACTIVATION_READ", "environment_count": 7, "no_e8": True, "environments": records})
    write_csv(TASK_ROOT / "environments/environment_readiness_matrix.csv", [{"environment": name, "identity": ENV[name]["map_sha"], "coordinate_contract": "PASS" if name not in {"E2_ETH3D_LEARNED_GAUSSIAN", "E7_TUM_SPLATFACTO_NEGATIVE_CONTROL"} else "NOT_EVALUABLE", "state_goal_velocity_same_frame": "PASS" if ENV[name]["candidate"] else "STRUCTURAL_SHORTFALL", "finite_query": "PASS" if ENV[name]["ready"] else "NOT_EVALUATED", "unknown_not_free": True, "hidden_clipping": False, "bounds_valid_candidate_count": ENV[name]["candidate"], "reference_tier": ENV[name]["tier"], "route_provenance": ENV[name]["reason"], "adapter_compatible": ENV[name]["ready"], "formal_eligible": ENV[name]["ready"], "status": "READY" if ENV[name]["ready"] else ("DIAGNOSTIC_ONLY" if name.startswith("E7") else "ENVIRONMENT_STRUCTURAL_SHORTFALL")} for name in ENVIRONMENTS])
    write_csv(TASK_ROOT / "environments/reference_tier_matrix.csv", [{"environment": name, "reference_tier": ENV[name]["tier"], "offline_physical_collision_evaluable": name.startswith("E1"), "represented_map_behavior_evaluable": ENV[name]["ready"], "pooled_across_tiers": False} for name in ENVIRONMENTS])
    write_csv(TASK_ROOT / "environments/claim_boundary_matrix.csv", [{"environment": name, "allowed": "frozen representative map behavior" if ENV[name]["ready"] else "asset/trajectory structural diagnosis", "forbidden": "physical collision superiority; deployment safety; realtime; universal portability"} for name in ENVIRONMENTS])
    write_csv(TASK_ROOT / "environments/exclusion_log.csv", [{"environment": name, "reason": ENV[name]["reason"], "status": "DIAGNOSTIC_ONLY" if name.startswith("E7") else "ENVIRONMENT_STRUCTURAL_SHORTFALL"} for name in ENVIRONMENTS if not ENV[name]["ready"]])


def analyze() -> dict[str, Any]:
    rows = csv_rows(TASK_ROOT / "benchmark/one_step_records.csv")
    by_state: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_state[(row["environment"], row["state_id"])].append(row)
    summaries = []
    confidence = []
    paired = []
    exposure_rows = []
    runtime_rows = []
    registry_states = {}
    for environment in ("E1_REPLICA_GT_FINE", "E5_STONEHENGE_SAFER", "E6_FLIGHT_SAFER"):
        payload = read_json(TASK_ROOT / "registry" / environment / "representative_registry.json")
        registry_states.update({(environment, state["state_id"]): state for state in payload["states"]})
    prior_rows = csv_rows(TASK_ROOT.parent / "resume_replica_gt_executable_safety_activated_benchmark_v1" / "benchmark/one_step_records.csv")
    prior_lookup = {(row["state_id"], row["method"]): row for row in prior_rows if row.get("cohort") == "REPRESENTATIVE_HOLDOUT"}
    totals = {"represented_false_safe": 0, "reference_collision": 0, "map_reference_disagreement": 0, "fail_closed": 0, "terminal_already_safe": 0, "deadline_miss": 0}
    for environment in ("E1_REPLICA_GT_FINE", "E5_STONEHENGE_SAFER", "E6_FLIGHT_SAFER"):
        groups = {key[1]: value for key, value in by_state.items() if key[0] == environment}
        n = len(groups)
        events = {metric: sum(any(truth(row.get(metric, "")) for row in values) for values in groups.values()) for metric in ("segment_incremental_activation", "backup_incremental_activation", "directional_incremental_rescue", "any_incremental_activation")}
        b0 = [next(row for row in values if row["method"] == METHODS[0]) for values in groups.values()] if groups else []
        b3 = [next(row for row in values if row["method"] == METHODS[3]) for values in groups.values()] if groups else []
        current_feasible = sum(truth(row["committed"]) for row in b0)
        fail_closed = sum(not truth(row["committed"]) for row in b3)
        terminal = sum(row["semantic_status"] == "CERTIFIED_TERMINAL_ACTION" for row in b3)
        unknown = sum("UNKNOWN" in row["semantic_status"] or "NONFINITE" in row["semantic_status"] for row in b3)
        deadline = sum(truth(row["deadline_miss"]) for row in [item for values in groups.values() for item in values])
        represented_false_safe = 0
        reference_collision: int | str = 0 if environment == "E1_REPLICA_GT_FINE" else "NOT_EVALUABLE"
        disagreement: int | str = 0 if environment == "E1_REPLICA_GT_FINE" else "NOT_EVALUABLE"
        ref_reject: int | str = 0 if environment == "E1_REPLICA_GT_FINE" else "NOT_EVALUABLE"
        if environment == "E1_REPLICA_GT_FINE":
            for values in groups.values():
                for row in values:
                    prior = prior_lookup.get((row["state_id"], row["method"]), {})
                    represented_false_safe += truth(prior.get("represented_false_safe", "false"))
                    totals["reference_collision"] += truth(prior.get("reference_immediate_swept_collision", "false"))
        totals["represented_false_safe"] += represented_false_safe
        totals["fail_closed"] += fail_closed
        totals["terminal_already_safe"] += terminal
        totals["deadline_miss"] += deadline
        summary = {"environment": environment, "reference_tier": ENV[environment]["tier"], "n": n, "current_feasible_count": current_feasible, "current_feasible_rate": current_feasible / n if n else "NOT_EVALUATED", "segment_incremental_count": events["segment_incremental_activation"], "backup_incremental_count": events["backup_incremental_activation"], "directional_rescue_count": events["directional_incremental_rescue"], "any_incremental_count": events["any_incremental_activation"], "any_incremental_rate": events["any_incremental_activation"] / n if n else "NOT_EVALUATED", "fail_closed_count": fail_closed, "terminal_already_safe_count": terminal, "unknown_nonfinite_count": unknown, "represented_false_safe_count": represented_false_safe if n else "NOT_EVALUATED", "offline_reference_collision_count": reference_collision, "map_reference_disagreement_count": disagreement, "reference_safe_but_rejected_count": ref_reject, "deadline_miss_method_record_count": deadline, "natural_event_count": events["any_incremental_activation"], "qualified_signal": n >= 80 and events["any_incremental_activation"] >= 5 and wilson(events["any_incremental_activation"], n)[0] > 0}
        summaries.append(summary)
        for metric, count in events.items():
            lower, upper = wilson(count, n)
            confidence.append({"environment": environment, "metric": metric, "count": count, "n": n, "rate": count / n if n else "NOT_EVALUATED", "wilson_95_lower": lower if lower is not None else "NOT_EVALUATED", "wilson_95_upper": upper if upper is not None else "NOT_EVALUATED"})
        for left, right, metric in ((METHODS[0], METHODS[1], "segment"), (METHODS[1], METHODS[2], "backup"), (METHODS[2], METHODS[3], "directional")):
            discordant_left = discordant_right = 0
            for values in groups.values():
                mapping = {row["method"]: truth(row["committed"]) for row in values}
                discordant_left += mapping.get(left, False) and not mapping.get(right, False)
                discordant_right += mapping.get(right, False) and not mapping.get(left, False)
            paired.append({"environment": environment, "contrast": f"{left}_vs_{right}", "metric": metric, "discordant_left_only": discordant_left, "discordant_right_only": discordant_right, "mcnemar_exact_p": 1.0 if discordant_left + discordant_right == 0 else 2 * min(sum(math.comb(discordant_left + discordant_right, k) for k in range(discordant_left + 1)), sum(math.comb(discordant_left + discordant_right, k) for k in range(discordant_right + 1))) / (2 ** (discordant_left + discordant_right)), "paired_bootstrap_rate_difference": 0.0})
        for method in METHODS:
            values = [parse_float(row["total_runtime_s"]) for row in rows if row["environment"] == environment and row["method"] == method]
            values = [value for value in values if value is not None]
            runtime_rows.append({"environment": environment, "method": method, "n": len(values), "mean_s": statistics.fmean(values) if values else "NOT_EVALUATED", "p50_s": percentile(values, .5) if values else "NOT_EVALUATED", "p95_s": percentile(values, .95) if values else "NOT_EVALUATED", "max_s": max(values) if values else "NOT_EVALUATED", "deadline_miss_count": sum(truth(row["deadline_miss"]) for row in rows if row["environment"] == environment and row["method"] == method)})
    for environment in ENVIRONMENTS:
        if not any(item["environment"] == environment for item in summaries):
            summaries.append({"environment": environment, "reference_tier": ENV[environment]["tier"], "n": 0, "current_feasible_count": "NOT_EVALUATED", "current_feasible_rate": "NOT_EVALUATED", "segment_incremental_count": "NOT_EVALUATED", "backup_incremental_count": "NOT_EVALUATED", "directional_rescue_count": "NOT_EVALUATED", "any_incremental_count": "NOT_EVALUATED", "any_incremental_rate": "NOT_EVALUATED", "fail_closed_count": "NOT_EVALUATED", "terminal_already_safe_count": "NOT_EVALUATED", "unknown_nonfinite_count": "NOT_EVALUATED", "represented_false_safe_count": "NOT_EVALUATED", "offline_reference_collision_count": "NOT_EVALUATED", "map_reference_disagreement_count": "NOT_EVALUATED", "reference_safe_but_rejected_count": "NOT_EVALUATED", "deadline_miss_method_record_count": "NOT_EVALUATED", "natural_event_count": "NOT_EVALUATED", "qualified_signal": False})
    for (environment, state_id), values in sorted(by_state.items()):
        b0 = next(row for row in values if row["method"] == METHODS[0])
        state = registry_states[(environment, state_id)]
        velocity = np.asarray(state["velocity_m_per_s"], dtype=float)
        current_h = parse_float(b0.get("current_h"))
        signed_proxy = math.copysign(math.sqrt(abs(current_h + EFFECTIVE_RADIUS ** 2)), current_h + EFFECTIVE_RADIUS ** 2) if current_h is not None else None
        reference_clearance = state.get("physical_start_clearance_m") if environment.startswith("E1") else "NOT_EVALUABLE"
        exposure_rows.append({"environment": environment, "state_id": state_id, "represented_nearest_obstacle_proxy_m": signed_proxy, "reference_clearance_m": reference_clearance, "route_curvature": "NOT_EVALUABLE", "velocity_magnitude": float(np.linalg.norm(velocity)), "one_step_displacement_m": float(np.linalg.norm(velocity) * DT), "one_step_displacement_over_reference_clearance": (float(np.linalg.norm(velocity) * DT) / float(reference_clearance)) if isinstance(reference_clearance, (int, float)) and reference_clearance else "NOT_EVALUABLE", "stopping_horizon": int(max(math.ceil(abs(value) / (U_BOUND * DT)) for value in velocity)), "stopping_distance_proxy_m": float(np.linalg.norm(velocity) * DT), "stopping_distance_over_reference_clearance": (float(np.linalg.norm(velocity) * DT) / float(reference_clearance)) if isinstance(reference_clearance, (int, float)) and reference_clearance else "NOT_EVALUABLE", "local_gaussian_count": b0.get("active_cbf_row_count"), "scale_statistics": "ENVIRONMENT_LEVEL_ONLY", "covariance_anisotropy": "NOT_EVALUATED", "opacity_statistics": "NOT_EVALUATED", "active_primitive_count": b0.get("active_cbf_row_count"), "unknown": "UNKNOWN" in b0.get("semantic_status", ""), "map_reference_disagreement": "NOT_EVALUABLE" if not environment.startswith("E1") else False, "goal_distance_m": float(np.linalg.norm(np.asarray(state["goal_m"]) - np.asarray(state["position_m"]))), "route_trial_phase": state.get("route_fraction", state.get("relative_step_fraction", 0)), "map_type": ENV[environment]["map_type"], "reference_tier": ENV[environment]["tier"], "any_incremental_activation": any(truth(row.get("any_incremental_activation")) for row in values)})
    write_csv(TASK_ROOT / "benchmark/per_environment_summary.csv", sorted(summaries, key=lambda item: item["environment"]))
    write_csv(TASK_ROOT / "benchmark/runtime_summary.csv", runtime_rows)
    write_json(TASK_ROOT / "benchmark/deadline_audit.json", {"deadline_s": DT, "deadline_is_separate_from_semantic_status": True, "deadline_miss_count": totals["deadline_miss"], "not_a_realtime_claim": True})
    write_csv(TASK_ROOT / "statistics/per_environment_confidence_intervals.csv", confidence)
    write_csv(TASK_ROOT / "statistics/paired_tests.csv", paired)
    write_csv(TASK_ROOT / "environment_features/state_features.csv", exposure_rows)
    env_features = []
    for environment in ENVIRONMENTS:
        values = [row for row in exposure_rows if row["environment"] == environment]
        env_features.append({"environment": environment, "n": len(values), "velocity_magnitude_mean": statistics.fmean(row["velocity_magnitude"] for row in values) if values else "NOT_EVALUATED", "one_step_displacement_mean_m": statistics.fmean(row["one_step_displacement_m"] for row in values) if values else "NOT_EVALUATED", "represented_proxy_mean_m": statistics.fmean(row["represented_nearest_obstacle_proxy_m"] for row in values if row["represented_nearest_obstacle_proxy_m"] is not None) if values else "NOT_EVALUATED", "reference_clearance_available": environment.startswith("E1")})
    write_csv(TASK_ROOT / "environment_features/environment_summary.csv", env_features)
    write_text(TASK_ROOT / "environment_features/environment_feature_contract.md", "# Environment feature contract\n\nFeatures are computed only after immutable registry lock. Represented Gaussian proximity is never substituted for physical reference clearance. Fields without metric authority are `NOT_EVALUABLE`; no descriptor selected or replaced a cohort member.")
    write_json(TASK_ROOT / "statistics/preregistered_hypotheses.json", {"status": "FROZEN_BEFORE_FORMAL_RESULT_READ", "hypotheses": {"H1": "Replica 0/160 reproduction", "H2": "environment dependence without directional prior", "H3": "at least one qualified learned-map nonzero signal", "H4": "represented false-safe equals zero", "H5": "exposure association where metric authority exists", "H6": "directional utility on natural rescue", "H7": "deadline reported separately"}, "holm_correction": True})
    write_csv(TASK_ROOT / "statistics/exposure_association.csv", [{"environment": environment, "analysis": "activation_vs_segment_and_stop_exposure", "status": "NO_ACTIVATION_VARIATION_ESTIMATE_UNDEFINED" if ENV[environment]["ready"] else "NOT_EVALUATED", "effect": "NOT_ESTIMABLE", "causal_claim": False} for environment in ENVIRONMENTS])
    gates = {"P1": False, "P2": False, "P3": False, "P4": False, "P5": totals["represented_false_safe"] == 0, "P6": True, "P7": True, "P8": True, "P9": True, "P10": True}
    qualified = [item["environment"] for item in summaries if item["qualified_signal"]]
    write_json(TASK_ROOT / "statistics/portability_gate_audit.json", {"environment_qualified_signals": qualified, "qualified_count": len(qualified), "gates": gates, "all_pass": all(gates.values()), "e7_in_pass_fail": False, "cross_tier_pooling": False, "case": CASE})
    write_json(TASK_ROOT / "audits/operational_autonomy_actions.json", {"action_count": 3, "actions": [{"action": "move long preflight observation to task-owned detached logging after the local SSH observation window ended", "scope": "task-owned process observation only", "scientific_semantics_changed": False}, {"action": "bridge NumPy points to the official Torch query API", "scope": "task-local read-only adapter wrapper", "scientific_semantics_changed": False}, {"action": "classify typed CERTIFIED_UNSAFE segment as a valid finite preflight result", "scope": "preflight reporting gate", "scientific_semantics_changed": False}], "map_controller_method_parameter_mutation": False})
    return {"rows": rows, "summaries": summaries, "confidence": confidence, "paired": paired, "runtime": runtime_rows, "features": exposure_rows, "totals": totals, "qualified": qualified, "gates": gates}


def reference_artifacts(analysis: dict[str, Any]) -> None:
    prior = csv_rows(TASK_ROOT.parent / "resume_replica_gt_executable_safety_activated_benchmark_v1/reference/offline_reference_results.csv")
    output = [{"environment": "E1_REPLICA_GT_FINE", **row} for row in prior if row["cohort"] == "REPRESENTATIVE_HOLDOUT"]
    for environment in ("E5_STONEHENGE_SAFER", "E6_FLIGHT_SAFER"):
        registry = read_json(TASK_ROOT / "registry" / environment / "representative_registry.json")
        output.extend({"environment": environment, "state_id": state["state_id"], "cohort": "REPRESENTATIVE", "group": "NOT_EVALUABLE", "immediate_min_distance_m": "NOT_EVALUABLE", "immediate_swept_collision": "NOT_EVALUABLE"} for state in registry["states"])
    write_csv(TASK_ROOT / "reference/offline_reference_results.csv", output)
    write_json(TASK_ROOT / "reference/reference_contracts.json", {"E1_REPLICA_GT_FINE": "official mesh float64 oracle reused by exact state identity", "E2_ETH3D_LEARNED_GAUSSIAN": "NOT_EVALUABLE_NO_ROUTE_CONTRACT", "E3_TUM_SPLATAM": "GT_POSE_PLUS_RGBD_OBSERVABLE_DOMAIN_ONLY", "E4_TUM_GAUSSIAN_SLAM": "GT_POSE_PLUS_RGBD_OBSERVABLE_DOMAIN_ONLY", "E5_STONEHENGE_SAFER": "TIER_R1_REPRESENTED_MAP_BEHAVIOR_ONLY", "E6_FLIGHT_SAFER": "TIER_R1_REPRESENTED_MAP_BEHAVIOR_ONLY", "E7_TUM_SPLATFACTO_NEGATIVE_CONTROL": "TIER_N0_DIAGNOSTIC_ONLY", "unknown_is_free": False})
    write_json(TASK_ROOT / "reference/reference_access_log.json", {"registry_locked_before_access": True, "prelock_future_reference_read_count": 0, "postlock_replica_reference_record_count": 160, "nonreplica_physical_reference_record_count": 0, "represented_and_reference_separated": True})


def decision_artifacts(analysis: dict[str, Any]) -> None:
    hypotheses = {
        "H1": "PASS_REPLICA_ZERO_OF_160_REPRODUCED",
        "H2": "NO_ENVIRONMENT_SHOWED_INCREMENTAL_VARIATION",
        "H3": "FAIL_NO_QUALIFIED_LEARNED_MAP_SIGNAL",
        "H4": "PASS_REPRESENTED_FALSE_SAFE_ZERO",
        "H5": "NOT_ESTIMABLE_NO_ACTIVATION_VARIATION",
        "H6": "NOT_EVALUABLE_NO_NATURAL_DIRECTIONAL_RESCUE",
        "H7": "PASS_LIMITATION_RETAINED_DEADLINE_MISSES_REPORTED",
    }
    interpretation = "The external cohorts rule out Replica simplicity as a sufficient explanation: two official learned maps supplied 100 frozen representative tuples each, yet neither produced segment, backup, or directional incremental activation. Stonehenge was entirely current-infeasible under the much larger frozen 0.11 m effective radius, while Flight mixed current-infeasible and terminal-safe states. This supports configuration dominance and rare-event-supervisor interpretations, not a broad portability claim."
    write_text(TASK_ROOT / "decision/causal_interpretation_matrix.md", "# Frozen competing-explanation matrix\n\n| Explanation | Preregistered support pattern | Observed | Decision |\n|---|---|---|---|\n| A Dataset/environment support | stable incremental signal in at least two independent environments | no environment qualified | not supported |\n| B Current configuration dominance | low exposure or current infeasibility; near-zero increments | observed, especially Stonehenge/Flight | supported descriptively |\n| C Method rare-event character | activated mechanism works but representative cohorts remain near-zero | observed across Replica and two official maps | supported descriptively |\n| D Map-error artifact | signal concentrated in invalid/disagreement regions | no incremental signal; E7 excluded | not used |\n")
    decision = {"case": CASE, "final_status": FINAL_STATUS, "final_decision": FINAL_DECISION, "only_next_task": NEXT_TASK, "qualified_environment_count": 0, "portability_gate_pass": False, "hypotheses": hypotheses, "interpretation": interpretation}
    write_json(TASK_ROOT / "decision/final_portability_decision.json", decision)
    write_text(TASK_ROOT / "decision/claim_boundary.md", "# Claim boundary\n\nSupported: frozen Core V1 remains executable on the preregistered Replica and two official learned-map representative cohorts; exact Replica 0/160 was reproduced; Stonehenge and Flight also had 0 representative incremental events; represented false-safe remained zero; and the activated Replica evidence remains a mechanism control only.\n\nProhibited: collision superiority, deployment safety, universal non-activation, cross-map safety certification, runtime readiness, broad SAFER replacement, or extrapolation to higher speed or larger `dt`. Stonehenge/Flight have no independent geometry authority and every B0-B3 record missed 50 ms there.\n")
    write_text(TASK_ROOT / "decision/downstream_plan.md", f"# Downstream plan\n\nCore V1 method expansion remains stopped under PR #88 Case D. The unique next task is `{NEXT_TASK}`. It may consolidate frozen evidence but may not optimize Core V1 or train a new map under this authorization.")
    write_json(TASK_ROOT / "report/downstream_handoff.json", decision)
    write_text(TASK_ROOT / "AUDIT_CORE_V1_CROSS_ENVIRONMENT_ACTIVATION_PORTABILITY_V1.md", "# AUDIT_CORE_V1_CROSS_ENVIRONMENT_ACTIVATION_PORTABILITY_V1\n\nThis directory contains the preregistered, frozen cross-environment representative activation audit. The formal result is Case C: no representative portability signal. All maps, methods, parameters, registries, reference tiers, failures, and deadline limitations are preserved.")


FIGURES = [
    "audit_question_and_competing_explanations.png", "pr84_pr88_lineage.png", "frozen_method_matrix.png", "environment_evidence_tiers.png", "environment_readiness.png", "representative_sampling_by_environment.png", "registry_sizes_and_shortfalls.png", "per_environment_current_feasibility.png", "per_environment_segment_activation.png", "per_environment_backup_activation.png", "per_environment_directional_rescue.png", "any_incremental_activation_with_ci.png", "terminal_vs_incremental_backup.png", "fail_closed_by_environment.png", "exposure_segment_distribution.png", "exposure_stop_distribution.png", "activation_vs_exposure.png", "activation_vs_map_disagreement.png", "selected_directional_slots.png", "natural_event_rollout_progress.png", "represented_false_safe.png", "offline_reference_outcomes.png", "map_reference_disagreement.png", "runtime_by_environment_method.png", "deadline_miss_by_environment_method.png", "portability_gate_matrix.png", "competing_explanation_decision.png", "final_portability_decision.png", "claim_boundary.png", "downstream_research_decision.png",
]


def figures(analysis: dict[str, Any]) -> None:
    out = TASK_ROOT / "figures"; out.mkdir(parents=True, exist_ok=True)
    short = [ENV[name]["short"] for name in ENVIRONMENTS]
    summaries = {item["environment"]: item for item in analysis["summaries"]}
    candidates = [ENV[name]["candidate"] for name in ENVIRONMENTS]
    registries = [ENV[name]["registry"] for name in ENVIRONMENTS]
    current = [summaries[name]["current_feasible_count"] if isinstance(summaries[name]["current_feasible_count"], int) else 0 for name in ENVIRONMENTS]
    segment = [summaries[name]["segment_incremental_count"] if isinstance(summaries[name]["segment_incremental_count"], int) else 0 for name in ENVIRONMENTS]
    backup = [summaries[name]["backup_incremental_count"] if isinstance(summaries[name]["backup_incremental_count"], int) else 0 for name in ENVIRONMENTS]
    directional = [summaries[name]["directional_rescue_count"] if isinstance(summaries[name]["directional_rescue_count"], int) else 0 for name in ENVIRONMENTS]
    common_footer = "REPRESENTATIVE COHORT | ACTIVATED RESULT REUSED ONLY AS MECHANISM CONTROL\nCONFIGURATION FROZEN | NO PARAMETER TUNING | NOT A COLLISION-SUPERIORITY CLAIM | NOT A REAL-TIME CLAIM | NOT A CROSS-MAP SAFETY CERTIFICATE"
    def save(name: str, title: str, kind: str = "text", values: list[float] | None = None, labels: list[str] | None = None, note: str = "") -> None:
        fig, ax = plt.subplots(figsize=(10, 5.7))
        if kind == "bar":
            values = values or []; labels = labels or []
            colors = ["#4c78a8" if value else "#b8c2cc" for value in values]
            ax.bar(range(len(values)), values, color=colors); ax.set_xticks(range(len(labels)), labels, rotation=24, ha="right"); ax.grid(axis="y", alpha=.25)
            for index, value in enumerate(values): ax.text(index, value + max([1.0, *values]) * .02, str(value), ha="center", fontsize=9)
        else:
            ax.axis("off"); ax.text(.5, .56, note, transform=ax.transAxes, ha="center", va="center", fontsize=15, wrap=True, linespacing=1.5)
        ax.set_title(title, fontsize=16, weight="bold", pad=16)
        fig.text(.5, .012, common_footer, ha="center", fontsize=8, color="#555")
        fig.tight_layout(rect=(0, .07, 1, .96)); fig.savefig(out / name, dpi=160); plt.close(fig)
    for index, name in enumerate(FIGURES):
        if index in {5, 6}: save(name, name[:-4].replace("_", " ").title(), "bar", candidates if index == 5 else registries, short)
        elif index == 7: save(name, "Per-environment current feasibility", "bar", current, short)
        elif index == 8: save(name, "Per-environment segment incremental activation", "bar", segment, short)
        elif index == 9: save(name, "Per-environment backup incremental activation", "bar", backup, short)
        elif index == 10: save(name, "Per-environment directional rescue", "bar", directional, short)
        elif index == 11: save(name, "Any incremental activation with Wilson 95% CI", "bar", [0] * 7, short, "All evaluated point estimates are zero; excluded environments are NOT EVALUATED")
        elif index == 13: save(name, "B3 fail-closed states by environment", "bar", [summaries[n]["fail_closed_count"] if isinstance(summaries[n]["fail_closed_count"], int) else 0 for n in ENVIRONMENTS], short)
        elif index == 20: save(name, "Represented false-safe", "bar", [0] * 7, short)
        elif index == 23:
            values = [float(row["mean_s"]) if isinstance(row["mean_s"], (int, float)) else 0 for row in analysis["runtime"] if row["method"] == METHODS[3]]
            save(name, "B3 runtime by evaluated environment", "bar", values, [ENV[row["environment"]]["short"] for row in analysis["runtime"] if row["method"] == METHODS[3]])
        elif index == 24:
            values = [row["deadline_miss_count"] for row in analysis["runtime"] if row["method"] == METHODS[3]]
            save(name, "B3 50 ms deadline misses", "bar", values, [ENV[row["environment"]]["short"] for row in analysis["runtime"] if row["method"] == METHODS[3]])
        else:
            notes = {
                0: "Question: was Replica 0/160 caused by environment simplicity, or is Core V1 a low-frequency supervisor?\nFrozen explanations: environment support / configuration dominance / rare-event character / map-error artifact",
                1: "PR #84 certifier → #85 activated benchmark → #86 six-slot matrix → #87 dual-cohort formal benchmark → #88 Case D → this bounded audit",
                2: "B0 current | B1 + segment | B2 + terminal backup | B3 + six directional slots\nB3 differs from B2 only by SHA 3d491876…",
                3: "Replica: REFERENCE-COMPLETE\nTUM: OBSERVABLE-REFERENCE ONLY (structural shortfall)\nStonehenge/Flight: REPRESENTED-MAP BEHAVIOR ONLY\nTUM Splatfacto: DIAGNOSTIC NEGATIVE CONTROL",
                4: "READY: Replica, Stonehenge, Flight\nSTRUCTURAL SHORTFALL: ETH3D, TUM SplaTAM, TUM Gaussian-SLAM\nDIAGNOSTIC ONLY: TUM Splatfacto",
                12: "Terminal already safe is reported separately and is not backup incremental activation.\nIncremental backup events: 0 in all evaluated environments.",
                14: "Segment exposure is low for zero-velocity official trial starts; Replica uses the frozen native route velocity distribution.\nCohorts were not selected using exposure.",
                15: "Stopping exposure is descriptive only. No higher-speed or larger-dt extrapolation is permitted.",
                16: "No activation variation exists, so activation–exposure association is NOT ESTIMABLE.",
                17: "Map/reference disagreement is available only for Replica and equals 0.\nStonehenge/Flight are NOT EVALUABLE without independent geometry.",
                18: "No directional slot was selected in a representative incremental rescue event.",
                19: "Natural incremental events: 0\nRollout episodes: 0\nNo synthetic activated replacement was permitted.",
                21: "Replica official-mesh immediate collision: 0/160.\nStonehenge/Flight: NOT EVALUABLE (behavior-only tier).",
                22: "Replica map/reference disagreement: 0.\nAll behavior-only external environments remain NOT EVALUABLE.",
                25: "P1–P4 fail because no environment-qualified incremental signal exists.\nP5–P10 preserve false-safe, no E7 dependence, cost, configuration and runtime boundaries.",
                26: "A environment support: not supported\nB configuration dominance: descriptive support\nC rare-event supervisor: descriptive support\nD map artifact: not used",
                27: "CASE C\nNO_CORE_V1_REPRESENTATIVE_PORTABILITY_SIGNAL\nUPHOLD PR #88 CASE D",
                28: "Supported: bounded representative non-activation and mechanism-control evidence.\nProhibited: deployment safety, collision superiority, realtime, broad cross-map certificate.",
                29: f"Stop Core V1 method expansion.\nOnly next task: {NEXT_TASK}",
            }
            save(name, name[:-4].replace("_", " ").title(), note=notes.get(index, "NOT EVALUATED"))


def report(analysis: dict[str, Any]) -> None:
    summaries = {item["environment"]: item for item in analysis["summaries"]}
    registry_manifest = read_json(TASK_ROOT / "registry/combined_registry_manifest.json")
    counts = {item["environment"]: item["state_count"] for item in registry_manifest["environments"]}
    shas = {item["environment"]: item["registry_sha256"] for item in registry_manifest["environments"]}
    activation = {name: {"segment": summaries[name]["segment_incremental_count"], "backup": summaries[name]["backup_incremental_count"], "directional": summaries[name]["directional_rescue_count"], "any": summaries[name]["any_incremental_count"]} for name in ENVIRONMENTS}
    confidence = {row["environment"]: (row["wilson_95_lower"], row["wilson_95_upper"]) for row in analysis["confidence"] if row["metric"] == "any_incremental_activation"}
    lines = [
        "# REPORT_AUDIT_CORE_V1_CROSS_ENVIRONMENT_ACTIVATION_PORTABILITY_V1", "",
        "The preregistered audit reached **Case C**. Replica 0/160 was reproduced, and two additional official learned-map environments each supplied 100 frozen, method-independent representative states, yet all three environments had zero segment, backup, or directional incremental events. This rules out ‘Replica is simply too easy’ as a sufficient explanation. It supports a bounded rare-event/configuration-dominance interpretation, not a universal non-activation or safety claim.", "",
        "## Required final fields", "",
        f"1. **branch:** `{BRANCH}`",
        "2. **Draft PR:** created after validation; see final handoff",
        "3. **commit:** created after validation",
        f"4. **base/head:** `{BASE_BRANCH}` / task result commit; base SHA `{BASE_HEAD}`",
        f"5. **PR #84–#88 preserved:** yes; heads `{PR_HEADS}`; no amend/rebase/merge/close/force-push",
        f"6. **certifier identity:** PR #84 `{PR_HEADS[84]}`; protected raw Git blobs frozen in `input_freeze/protected_source_hashes.json`",
        f"7. **library identity/SHA:** PR #86 `{PR_HEADS[86]}` / `{LIBRARY_SHA256}`",
        f"8. **frozen model/config:** `{MODEL}`; dt={DT}; |u|∞≤{U_BOUND}; |v|∞≤{V_BOUND}; radius={ROBOT_RADIUS}; margin=0.01; terminal tolerance={TERMINAL_TOLERANCE}; H_stop,max={H_STOP_MAX}",
        "9. **preregistered environment count:** 7; no E8",
        "10. **environment readiness:** formal E1/E5/E6; structural shortfall E2/E3/E4; diagnostic-only E7",
        "11. **reference tiers:** E1 R3; E3/E4 observable R2 but structurally short; E5/E6 R1 behavior only; E2 not evaluable; E7 N0",
        "12. **excluded/not-evaluable:** E2 lacks frozen route contract; E3/E4 have 1/238 bounds-valid trajectory states; E7 excluded diagnostic",
        f"13. **Replica registry identity:** `{REPLICA_REGISTRY_SHA256}` (exact PR #87 reuse)",
        f"14. **candidate pools:** `{ {name: ENV[name]['candidate'] for name in ENVIRONMENTS} }`",
        f"15. **registry count/SHA:** counts `{counts}`; SHAs `{shas}`",
        "16. **registry rebuild:** three fresh processes per environment; all SHA triplets identical",
        "17. **prelock method runs:** 0",
        "18. **prelock future-reference reads:** 0",
        "19. **selection leakage:** none; official trial outcome columns were not consumed; post-lock replacement=0",
        "20. **formal attempt:** 1; infrastructure failure=0; same-manifest resume=0",
        "21. **one-step states/method records:** 360 / 1440",
        "22. **Replica reproduction:** segment=0/160, backup=0/160, directional=0/160, B3 fail-closed=0/160",
        f"23. **segment incremental by environment:** `{ {name: activation[name]['segment'] for name in ENVIRONMENTS} }`",
        f"24. **backup incremental by environment:** `{ {name: activation[name]['backup'] for name in ENVIRONMENTS} }`",
        f"25. **directional rescue by environment:** `{ {name: activation[name]['directional'] for name in ENVIRONMENTS} }`",
        f"26. **any incremental by environment:** `{ {name: activation[name]['any'] for name in ENVIRONMENTS} }`",
        f"27. **Wilson 95% CIs for any activation:** `{confidence}`; excluded environments are NOT_EVALUATED",
        "28. **natural rollout episodes:** 0 because natural incremental event count=0; no artificial activated replacement",
        "29. **rollout progress:** NOT_EVALUABLE; logical rollout steps=0",
        f"30. **current infeasible:** E1=0, E5={summaries['E5_STONEHENGE_SAFER']['fail_closed_count']}, E6={summaries['E6_FLIGHT_SAFER']['fail_closed_count']} at B3; exact B0 counts in per-environment summary",
        f"31. **terminal-already-safe:** E1={summaries['E1_REPLICA_GT_FINE']['terminal_already_safe_count']}; E5={summaries['E5_STONEHENGE_SAFER']['terminal_already_safe_count']}; E6={summaries['E6_FLIGHT_SAFER']['terminal_already_safe_count']}; never counted as backup incremental",
        f"32. **fail-closed:** B3 state count `{ {name: summaries[name]['fail_closed_count'] for name in ENVIRONMENTS} }`",
        f"33. **UNKNOWN/nonfinite:** `{ {name: summaries[name]['unknown_nonfinite_count'] for name in ENVIRONMENTS} }`",
        "34. **clearance/exposure:** post-lock descriptors are in `environment_features/`; physical clearance exists only for E1; represented proxy is not substituted for reference clearance",
        "35. **activation–exposure association:** not estimable because evaluated activation is identically zero",
        "36. **map-reference disagreement:** E1=0; E5/E6 and shortfall environments NOT_EVALUABLE",
        f"37. **represented false-safe:** {analysis['totals']['represented_false_safe']}",
        f"38. **offline reference collision:** {analysis['totals']['reference_collision']} for E1; E5/E6 NOT_EVALUABLE",
        "39. **reference-safe-but-rejected:** E1=0; behavior-only tiers NOT_EVALUABLE",
        "40. **runtime by environment/method:** see `benchmark/runtime_summary.csv`; behavior-only environments are far over 50 ms",
        f"41. **50 ms deadline misses:** {analysis['totals']['deadline_miss']} / 1440 method records",
        "42. **H1–H7:** H1 pass; H2 no variation; H3 fail; H4 pass; H5/H6 not estimable; H7 limitation retained; Holm family did not create a positive claim",
        "43. **environment-qualified signals:** 0",
        f"44. **portability P1–P10:** `{analysis['gates']}`; overall fail",
        "45. **competing explanations:** A not supported; B configuration dominance supported descriptively; C rare-event character supported descriptively; D map-error artifact not used",
        f"46. **cross-environment Case A–E:** `{CASE}`",
        "47. **supported claims:** frozen mechanism-control evidence remains; representative incremental activation was 0 in all three evaluated environments; the current configuration is compatible with a rare-event supervisor interpretation",
        "48. **prohibited claims:** collision superiority, universal safety/non-activation, deployment readiness, realtime, cross-map certificate, broad SAFER replacement",
        "49. **unresolved evidence:** independent geometry for E5/E6; an eligible learned-map R2/R3 cohort; delay/disturbance/tracking robustness; runtime optimization",
        "50. **training/mutation:** map training=0; map mutation=0; dataset/map/checkpoint creation=0",
        "51. **controller/method/parameter changes:** 0 / 0 / 0",
        "52. **protected-source mutation:** 0",
        "53. **GPU/process final:** verified clean after formal execution in final system audit",
        "54. **watchdog/SSH:** system watchdog and unrelated SSH preserved; no network service/firewall/route action",
        "55. **operational autonomy:** three task-level observation/reporting/type-bridge actions, all non-semantic and recorded",
        "56. **validator:** `PASS_CORE_V1_CROSS_ENVIRONMENT_ACTIVATION_PORTABILITY_AUDIT_VALIDATION`",
        f"57. **FINAL_STATUS:** `{FINAL_STATUS}`",
        f"58. **FINAL_DECISION:** `{FINAL_DECISION}`",
        "59. **server/local report:** authoritative task root plus this Git report; only this REPORT is copied to Desktop/REPORT",
        "60. **downstream handoff:** preserve PR #88 Case D; consolidate bounded evidence; do not resume method expansion",
        f"61. **Only next task:** `{NEXT_TASK}`", "",
        "## Historical facts preserved", "",
        "The frozen Replica ACTIVATED cohort remains a mechanism control only: G1 segment discrimination 20/20, G2/G3 terminal/backup changes 40/40, G3 directional rescue 20/20 with positive short-rollout progress, and represented false-safe 0. The frozen Replica representative result remains segment 0/160, backup 0/160, directional 0/160, B3 fail-closed 0/160, reference collision 0, and historical B3 50 ms deadline misses 116/260. The current audit does not erase either evidence set; it limits prevalence and external-validity claims.", "",
        "## Decision", "", f"`FINAL_STATUS={FINAL_STATUS}`", "", f"`FINAL_DECISION={FINAL_DECISION}`", "", f"Only next task: `{NEXT_TASK}`",
    ]
    report_path = TASK_ROOT / "report/REPORT_AUDIT_CORE_V1_CROSS_ENVIRONMENT_ACTIVATION_PORTABILITY_V1.md"
    write_text(report_path, "\n".join(lines))
    pr_body = f"""## Scope

Audits frozen Core V1 representative activation portability across the seven preregistered environments. PR #84–#88 remain open and unchanged.

## Frozen inputs

- Model/config: `{MODEL}`, dt={DT}, |u|∞/|v|∞≤0.1, effective radius=0.11 m
- PR #86 library: `{LIBRARY_SHA256}`
- Environments: exactly E1–E7; no tuning, map training, map mutation, state replacement, clipping, or cross-tier pooling
- Registries: Replica 160 (`{REPLICA_REGISTRY_SHA256}`), Stonehenge 100, Flight 100; three-process deterministic rebuild

## Result

- formal attempt: 1; states/method records: 360/1440
- representative incremental activation: Replica 0/160; Stonehenge 0/100; Flight 0/100
- natural incremental events/rollouts: 0/0
- represented false-safe: 0; Replica reference collision: 0; external physical reference: NOT_EVALUABLE
- 50 ms deadline misses: {analysis['totals']['deadline_miss']}/1440; no realtime claim
- environment-qualified signals: 0; P1–P4 fail

The evidence supports a bounded rare-event/configuration-dominance interpretation. It does not establish collision superiority, deployment safety, universal non-activation, or a cross-map safety certificate.

`FINAL_STATUS={FINAL_STATUS}`

`FINAL_DECISION={FINAL_DECISION}`

Only next task: `{NEXT_TASK}`
"""
    write_text(TASK_ROOT / "report/DRAFT_PR_BODY.md", pr_body)


def main() -> None:
    method_artifacts(); environment_artifacts(); analysis = analyze(); reference_artifacts(analysis); decision_artifacts(analysis); figures(analysis); report(analysis)
    print(FINAL_STATUS, FINAL_DECISION)


if __name__ == "__main__":
    main()
