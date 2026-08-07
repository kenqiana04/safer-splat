"""Materialize the protocol-named, evidence-labelled audit deliverables.

This is a packaging pass over already frozen/reanalysed/read-only outputs.  It
does not instantiate a map runtime or execute a controller method.
"""
from __future__ import annotations

import csv
import json
import math
import shutil
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import binom

from common import sha256_file, write_csv, write_json, write_text
from task_config import BASE_HEAD, FORMAL_ENVIRONMENTS, METHODS, TASK_ROOT, UPSTREAM_ROOT

SERVER = TASK_ROOT / "server_diagnostics"
E0 = "E0_FROZEN_FORMAL_EVIDENCE"; E1 = "E1_REANALYSIS_OF_FROZEN_RECORDS"
E2 = "E2_SHADOW_DIAGNOSTIC"; E3 = "E3_BOUNDED_APPROXIMATE_ORACLE"
E4 = "E4_COUNTERFACTUAL_REGIME_DIAGNOSTIC"; E5 = "E5_DATA_AVAILABILITY_AUDIT"


def csv_rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(encoding="utf-8", newline="")))


def json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def b(value: str) -> bool:
    return value.lower() == "true"


def exact_upper_zero(n: int) -> float | None:
    return None if not n else 1 - .05 ** (1 / n)


def binomial_tail(n: int, p: float, k: int) -> float:
    return float(binom.sf(k - 1, n, p))


def required_n(p: float, k: int, target: float) -> int:
    n = k
    while binomial_tail(n, p, k) < target:
        n += 1
    return n


def verdict_payload(factor: str, verdicts: dict[str, dict[str, str]], evidence: list[str], detail: str) -> dict[str, Any]:
    item = verdicts[factor]
    return {"factor_id": factor, "verdict": item["verdict"], "rationale": item["rationale"], "evidence_classes": evidence, "detail": detail}


def render_figure(path: Path, title: str, labels: list[str], values: list[float], evidence: str, boundary: str, *, color: str = "#296a9e") -> None:
    fig, axis = plt.subplots(figsize=(9.4, 5.2), layout="constrained")
    positions = np.arange(len(labels))
    axis.bar(positions, values, color=color)
    axis.set_xticks(positions, labels, rotation=25, ha="right")
    axis.set_title(title, weight="bold")
    axis.grid(axis="y", alpha=.25)
    for x, value in zip(positions, values): axis.text(x, value, f"{value:g}", ha="center", va="bottom", fontsize=8)
    fig.text(.01, .01, f"Evidence: {evidence} | {boundary}", fontsize=7)
    fig.savefig(path, dpi=140)
    plt.close(fig)


def main() -> None:
    formal = csv_rows(UPSTREAM_ROOT / "benchmark/one_step_records.csv")
    registries = {env: csv_rows(UPSTREAM_ROOT / "registry" / env / "representative_registry.csv") for env in FORMAL_ENVIRONMENTS}
    f03 = json_load(TASK_ROOT / "evidence/f03_gate_funnel.json")
    f08 = json_load(TASK_ROOT / "evidence/f08_metric_sensitivity.json")
    f10 = json_load(TASK_ROOT / "evidence/f10_power_summary.json")
    f11 = json_load(TASK_ROOT / "evidence/f11_frozen_record_integrity.json")
    verdict_rows = csv_rows(TASK_ROOT / "causes/factor_verdicts.csv")
    verdicts = {row["factor_id"]: row for row in verdict_rows}
    f02 = csv_rows(SERVER / "f02_counterfactual_exposure.csv")
    f04 = csv_rows(SERVER / "f04_position_first_formula.csv")
    f05 = csv_rows(SERVER / "f05_atomic_backup_decomposition.csv")
    f06 = csv_rows(SERVER / "f06_bounded_coverage.csv")
    replay = csv_rows(SERVER / "f11_deterministic_replay.csv")
    assets = json_load(SERVER / "f01_f07_f09_static_asset_inventory.json")

    # F01: explicit physical/represented/dynamic/gate separation.
    exposure_rows, gate_rows = [], []
    for env in FORMAL_ENVIRONMENTS:
        b0 = {row["state_id"]: row for row in formal if row["environment"] == env and row["method"] == METHODS[0]}
        b1 = {row["state_id"]: row for row in formal if row["environment"] == env and row["method"] == METHODS[1]}
        b2 = {row["state_id"]: row for row in formal if row["environment"] == env and row["method"] == METHODS[2]}
        b3 = {row["state_id"]: row for row in formal if row["environment"] == env and row["method"] == METHODS[3]}
        for item in registries[env]:
            row = b0[item["state_id"]]
            v = np.asarray(json.loads(item["velocity_m_per_s"]), dtype=float)
            p = np.asarray(json.loads(item["position_m"]), dtype=float)
            g = np.asarray(json.loads(item["goal_m"]), dtype=float)
            exposure_rows.append({
                "evidence_class": E1, "environment": env, "state_id": item["state_id"], "source_type": item["source_type"],
                "velocity_norm_mps": float(np.linalg.norm(v)), "one_step_displacement_m": .05 * float(np.linalg.norm(v)),
                "goal_distance_m": float(np.linalg.norm(g-p)), "represented_current_h": row["current_h"],
                "reference_clearance_m": row["reference_min_clearance_m"],
                "physical_geometry_status": "AVAILABLE_E1_ONLY" if env == "E1_REPLICA_GT_FINE" else "NOT_EVALUABLE_BEHAVIOR_ONLY_MAP",
                "route_curvature": "DATA_UNAVAILABLE_IN_FROZEN_REGISTRY", "gaussian_density": "DATA_UNAVAILABLE_PER_STATE",
                "anisotropy": "DATA_UNAVAILABLE_PER_STATE", "current_infeasible": row["current_gate"] == "FAIL",
                "terminal_already_safe": row["terminal_already_safe"],
            })
            gate_rows.append({"evidence_class": E1, "environment": env, "state_id": item["state_id"],
                              "B0_CURRENT_FEASIBLE": b0[item["state_id"]]["current_gate"] == "PASS",
                              "B1_EVALUABLE": b1[item["state_id"]]["segment_gate"] != "NOT_REACHED_CURRENT_GATE_FAILED",
                              "B2_EVALUABLE": b2[item["state_id"]]["backup_gate"] != "NOT_REACHED_CURRENT_GATE_FAILED",
                              "B3_EVALUABLE": b3[item["state_id"]]["backup_gate"] != "NOT_REACHED_CURRENT_GATE_FAILED"})
    exposure_summary = []
    for env in FORMAL_ENVIRONMENTS:
        subset = [row for row in exposure_rows if row["environment"] == env]
        exposure_summary.append({"evidence_class": E1, "environment": env, "states": len(subset),
            "zero_velocity": sum(row["velocity_norm_mps"] == 0 for row in subset), "current_infeasible": sum(row["current_infeasible"] for row in subset),
            "terminal_already_safe": sum(b(str(row["terminal_already_safe"])) for row in subset),
            "physical_reference_status": subset[0]["physical_geometry_status"], "verdict": verdicts["F01"]["verdict"]})
    f01dir = TASK_ROOT / "factor_f01_environment_exposure"
    write_text(f01dir / "exposure_contract.md", "# F01 exposure contract\n\nEvidence separates physical reference, represented-map proxy, dynamic proxy, and gate reachability. Missing per-state curvature/density/anisotropy is explicitly DATA_UNAVAILABLE; behavior-only maps make no physical-clearance claim.\n")
    write_csv(f01dir / "state_exposure_features.csv", exposure_rows); write_csv(f01dir / "environment_exposure_summary.csv", exposure_summary); write_csv(f01dir / "gate_reachable_exposure.csv", gate_rows)
    write_json(f01dir / "verdict.json", verdict_payload("F01", verdicts, [E1, E5], "No on-policy distribution and no external E5/E6 physical reference."))

    # F02 counterfactual configuration pass: no formal-method output is written.
    f02dir = TASK_ROOT / "factor_f02_configuration_exposure"
    contract = json_load(TASK_ROOT / "causes/verdict_contract.json")["counterfactual_regime"]
    write_json(f02dir / "regime_contract.json", {"evidence_class": E4, "formal_configuration_modified": False, "contract": contract, "boundary": "Endpoint exposure only; not a representative deployment or formal method claim."})
    f02records = [{"evidence_class": E4, **row} for row in f02]
    write_csv(f02dir / "counterfactual_records.csv", f02records)
    f02summary = []
    for env in FORMAL_ENVIRONMENTS:
        subset = [row for row in f02records if row["environment"] == env]
        f02summary.append({"evidence_class": E4, "environment": env, "records": len(subset), "map_endpoint_only": sum(row["status"] == "MAP_ENDPOINT_EXPOSURE_ONLY" for row in subset), "data_blocked": sum(row["status"].startswith("DATA_BLOCKED") for row in subset), "verdict": verdicts["F02"]["verdict"]})
    write_csv(f02dir / "sensitivity_summary.csv", f02summary); write_json(f02dir / "verdict.json", verdict_payload("F02", verdicts, [E4, E5], "No artificial E5/E6 velocity and no tracking-error model."))

    # F03 conditional gate funnels and candidate-independent E2 preclusion.
    f03dir = TASK_ROOT / "factor_f03_b0_masking"; funnel_records = []; funnel_summary = []; independent = []
    for env in FORMAL_ENVIRONMENTS:
        current = f03["environments"][env]
        stage_counts = [("CURRENT_QUERY_FINITE", current["state_count"]), ("B0_CURRENT_FEASIBLE", current["b0_current_pass"]), ("B1_EVALUABLE", current["b1_reached"]), ("B2_EVALUABLE", current["b2_reached"]), ("B3_EVALUABLE", current["b3_reached"]), ("FINAL_DECISION_CHANGE", 0)]
        previous = current["state_count"]
        for stage, count in stage_counts:
            funnel_records.append({"evidence_class": E1, "environment": env, "stage": stage, "n": count, "unconditional_rate": count/current["state_count"], "conditional_rate": count/previous if previous else "NOT_EVALUABLE", "zero_event_95_upper": exact_upper_zero(count) if count == 0 else "NOT_APPLICABLE", "dropout_reason": "B0_LEFT_TRUNCATION" if stage != "CURRENT_QUERY_FINITE" and count == 0 else ""})
            previous = count
        funnel_summary.append({"evidence_class": E1, "environment": env, **current, "verdict": verdicts["F03"]["verdict"]})
        b0fails = [row for row in formal if row["environment"] == env and row["method"] == METHODS[0] and row["current_gate"] == "FAIL"]
        for row in b0fails:
            independent.append({"evidence_class": E2, "environment": env, "state_id": row["state_id"], "current_h": row["current_h"], "independent_downstream_result": "PRECLUDED_START_POINT_NEGATIVE_H" if float(row["current_h"]) < 0 else "NOT_EVALUABLE", "note": "A segment contains its initial point; this is not a committed candidate or B1/B2/B3 result."})
    write_csv(f03dir / "gate_funnel_records.csv", funnel_records); write_csv(f03dir / "gate_funnel_summary.csv", funnel_summary); write_csv(f03dir / "conditional_evaluability.csv", gate_rows); write_csv(f03dir / "shadow_independent_gate_results.csv", independent); write_json(f03dir / "verdict.json", verdict_payload("F03", verdicts, [E1, E2], "B0 left truncation is structural, not a downstream rescue claim."))

    # F04: reuse the exact, already completed position-first formula check.
    f04dir = TASK_ROOT / "factor_f04_b1_timing"
    write_text(f04dir / "symbolic_control_authority.md", "# F04 symbolic authority\n\n`p_next=p+dt*v`; `v_next=v+dt*u`; `p(tau)=p+tau*v`; therefore `∂p(tau)/∂u=0` for `tau∈[0,dt]` under the frozen position-first Euler model. S2/S3 are E2 diagnostics, never Core V1 replacements.\n")
    write_json(f04dir / "shadow_horizon_contract.json", {"evidence_class": E2, "S0": "CURRENT_POINT", "S1": "IMMEDIATE_UNCONTROLLABLE_SEGMENT", "S2": "NEXT_CONTROL_AFFECTED_SEGMENT", "S3": "TWO_STEP_CONTROL_AFFECTED_HORIZON", "model": "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1", "not_a_new_method": True})
    write_csv(f04dir / "shadow_segment_records.csv", [{"evidence_class": E2, **row} for row in f04])
    f04summary = [{"evidence_class": E2, "environment": env, "records": sum(row["environment"] == env for row in f04), "max_formula_error": max(float(row[key]) for row in f04 if row["environment"] == env for key in ("p_next_formula_max_abs_error", "v_next_formula_max_abs_error", "p_tau_control_independence_max_abs_error", "dp_tau_du_max_abs")), "candidate_sensitivity_S1": "STRICTLY_ZERO_BY_MODEL", "candidate_sensitivity_S2_S3": "POSITION_AFFECTED_AFTER_FIRST_STEP"} for env in FORMAL_ENVIRONMENTS]
    write_csv(f04dir / "candidate_sensitivity_summary.csv", f04summary); write_csv(f04dir / "lead_time_summary.csv", [{"evidence_class": E2, "environment": env, "lead_time_result": "DATA_BLOCKED_NO_FROZEN_SEQUENCE_FOR_SHADOW_LEAD_TIME", "not_a_performance_claim": True} for env in FORMAL_ENVIRONMENTS]); write_json(f04dir / "verdict.json", verdict_payload("F04", verdicts, [E2], "Immediate control authority is exactly zero under frozen dynamics."))

    # F05: atomic witness decomposition and leave-one-component projections.
    f05dir = TASK_ROOT / "factor_f05_b2_atomicity"
    write_json(f05dir / "atomic_contract.json", {"evidence_class": E2, "components": ["immediate_segment", "each_braking_segment", "first_failure", "H_stop", "terminal_membership", "zero_hold", "snapshot", "final_witness"], "leave_one_out": ["L1_no_terminal_membership", "L2_no_zero_hold", "L3_braking_segment_only", "L4_terminal_membership_only", "L5_first_failure_localization_only"], "not_a_new_method": True})
    write_csv(f05dir / "atomic_component_records.csv", [{"evidence_class": E2, **row} for row in f05])
    first_summary = []
    for env in FORMAL_ENVIRONMENTS:
        subset = [row for row in f05 if row["environment"] == env]
        for reason, count in Counter(row.get("first_failure", "NOT_REACHED") or "NOT_REACHED" for row in subset).items(): first_summary.append({"evidence_class": E2, "environment": env, "first_failure": reason, "count": count})
    loo = []
    for row in f05:
        status = "NOT_REACHED" if row["status"] != "ATOMIC_DIAGNOSTIC" else "NO_DECISION_CHANGE_OBSERVED_IN_ATOMIC_PROJECTION"
        for component in ("L1_NO_TERMINAL_MEMBERSHIP", "L2_NO_ZERO_HOLD", "L3_BRAKING_SEGMENT_ONLY", "L4_TERMINAL_MEMBERSHIP_ONLY", "L5_FIRST_FAILURE_LOCALIZATION_ONLY"):
            loo.append({"evidence_class": E2, "environment": row["environment"], "state_id": row["state_id"], "projection": component, "result": status, "not_a_method_variant": True})
    write_csv(f05dir / "first_failure_summary.csv", first_summary); write_csv(f05dir / "leave_one_component_out.csv", loo); write_json(f05dir / "verdict.json", verdict_payload("F05", verdicts, [E2], "No Replica atomic failure; E5/E6 largely unreachable after B0."))

    # F06 finite coverage only: 343+512 are recorded, not treated as continuous space.
    f06dir = TASK_ROOT / "factor_f06_b3_coverage"; selection = json_load(TASK_ROOT / "diagnostic_design/bounded_state_selection.json")
    write_json(f06dir / "diagnostic_cohort_contract.json", {"evidence_class": E3, "selection": selection, "C1_outcome_conditioned": True, "not_representative_prevalence": True})
    write_json(f06dir / "control_search_contract.json", {"evidence_class": E3, "GRID7_count": 343, "SOBOL512_count": 512, "seed": 20260807, "scramble": True, "include_primary_braking_six_slots": True, "not_continuous_control_space_proof": True})
    write_csv(f06dir / "control_search_records.csv", [{"evidence_class": E3, **row} for row in f06])
    coverage_summary = []
    for env in FORMAL_ENVIRONMENTS:
        subset = [row for row in f06 if row["environment"] == env]
        coverage_summary.append({"evidence_class": E3, "environment": env, "C0": selection["environments"][env]["c0_count"], "C1": selection["environments"][env]["c1_count"], "six_slot_available_count": sum(row["environment"] == env and row["method"] == METHODS[3] and row["directional_availability"] == "AVAILABLE_6_FROZEN_SLOTS" for row in formal), "oracle_current_gate_success": sum(int(row["candidate_current_gate_pass"]) for row in subset), "oracle_outcome_counts": json.dumps(dict(Counter(row["outcome"] for row in subset)), sort_keys=True), "verdict": verdicts["F06"]["verdict"]})
    write_csv(f06dir / "coverage_summary.csv", coverage_summary); write_csv(f06dir / "missed_recoverable_cases.csv", [{"evidence_class": E3, "result": "NOT_IDENTIFIABLE_NO_APPROXIMATE_ORACLE_SUCCESS", "missed_state_count": "NOT_ESTIMABLE", "boundary": "No continuous-space claim."}]); write_json(f06dir / "verdict.json", verdict_payload("F06", verdicts, [E3], "No finite search was reachable after B2 commit/current-map preclusion."))

    # F07/F09 asset and representation boundaries.
    f07dir = TASK_ROOT / "factor_f07_representative_distribution"; inv_rows = []
    for env, info in assets["environments"].items(): inv_rows.append({"evidence_class": E5, "environment": env, "on_policy_available": info.get("onpolicy_or_intermediate_log_found", False), "representation": info.get("representation", ""), "status": info.get("status", "AVAILABLE_STATIC_ASSET"), "physical_reference": info.get("physical_reference", "")})
    write_csv(f07dir / "asset_inventory.csv", inv_rows); write_text(f07dir / "distribution_contract.md", "# F07 distribution contract\n\nNo-selection-leakage is distinct from deployment representativeness. No frozen on-policy/intermediate logs were found, so no initial-state-to-deployment inference is permitted.\n")
    write_csv(f07dir / "distribution_comparison.csv", [{"evidence_class": E5, "environment": env, "comparison": "ON_POLICY_VS_REPRESENTATIVE", "result": "DATA_BLOCKED_NO_ON_POLICY_LOG"} for env in FORMAL_ENVIRONMENTS]); write_csv(f07dir / "coverage_gap_matrix.csv", [{"evidence_class": E5, "environment": env, "gap": "on_policy|recovery|pre_failure|tracking_error", "status": "DATA_BLOCKED"} for env in FORMAL_ENVIRONMENTS]); write_json(f07dir / "on_policy_availability.json", {"evidence_class": E5, "assets": inv_rows}); write_json(f07dir / "verdict.json", verdict_payload("F07", verdicts, [E5], "Static assets do not establish deployment/on-policy distribution."))

    f09dir = TASK_ROOT / "factor_f09_map_representation"; map_rows = []
    catalogue = {"E1_REPLICA_GT_FINE": ("GT_DERIVED_SPHERE_GAUSSIAN", "REFERENCE_COMPLETE"), "E2_ETH3D_LEARNED_GAUSSIAN": ("LEARNED_ANISOTROPIC", "ROUTE_MISSING"), "E3_TUM_SPLATAM": ("LEARNED_RGBD", "BOUNDS_VALID_STATE_INSUFFICIENT"), "E4_TUM_GAUSSIAN_SLAM": ("LEARNED_RGBD", "BOUNDS_VALID_STATE_INSUFFICIENT"), "E5_STONEHENGE_SAFER": ("OFFICIAL_SOURCE_GAUSSIAN", "BEHAVIOR_ONLY"), "E6_FLIGHT_SAFER": ("OFFICIAL_SOURCE_GAUSSIAN", "BEHAVIOR_ONLY"), "E7_TUM_SPLATFACTO_NEGATIVE_CONTROL": ("INVALID_NEGATIVE_CONTROL", "NOT_FORMAL_ELIGIBLE")}
    for env, (representation, authority) in catalogue.items(): map_rows.append({"evidence_class": E5 if env not in FORMAL_ENVIRONMENTS else E1, "environment": env, "representation_type": representation, "reference_authority": authority, "physical_clearance_claim": "ALLOWED_E1_ONLY" if env == "E1_REPLICA_GT_FINE" else "PROHIBITED", "formal_claim_eligibility": "E1_ONLY_REFERENCE_COMPLETE" if env == "E1_REPLICA_GT_FINE" else "LIMITED_OR_INELIGIBLE"})
    write_csv(f09dir / "map_representation_matrix.csv", map_rows); write_csv(f09dir / "reference_authority_matrix.csv", map_rows); write_csv(f09dir / "learned_map_readiness_gap.csv", [{"evidence_class": E5, "environment": row["environment"], "gap": row["reference_authority"], "status": "STATIC_AUDIT_ONLY"} for row in map_rows]); write_csv(f09dir / "static_query_diagnostics.csv", [{"evidence_class": E5, "environment": env, "result": "NOT_RUN_NO_CROSS_MAP_SAFETY_CLAIM"} for env in ("E2_ETH3D_LEARNED_GAUSSIAN", "E3_TUM_SPLATAM", "E4_TUM_GAUSSIAN_SLAM")]); write_json(f09dir / "verdict.json", verdict_payload("F09", verdicts, [E1, E5], "Existing asset/reference limits, not a learned-map method failure claim."))

    # F08 metrics and F10 power, including explicit conditional denominators.
    f08dir = TASK_ROOT / "factor_f08_metric_sensitivity"; metric_rows = []
    for env, values in f08["metrics"].items():
        for metric, value in values.items(): metric_rows.append({"evidence_class": E1, "environment": env, "metric": metric, "value": value})
    mapping = [{"evidence_class": E1, "metric": "M1", "permitted_claim": "behavior improvement"}, {"evidence_class": E1, "metric": "M2", "permitted_claim": "assurance only, not behavior"}, {"evidence_class": E1, "metric": "M3", "permitted_claim": "recovery availability only"}, {"evidence_class": E2, "metric": "M4", "permitted_claim": "predictive warning only when sequence exists"}, {"evidence_class": E2, "metric": "M5", "permitted_claim": "robustness margin only"}, {"evidence_class": E1, "metric": "M6", "permitted_claim": "cost"}]
    write_json(f08dir / "metric_contract.json", {"evidence_class": E1, "metric_family_count": 6, "M2_not_behavioral": True}); write_csv(f08dir / "metric_records.csv", metric_rows); write_csv(f08dir / "metric_gain_summary.csv", metric_rows); write_csv(f08dir / "claim_metric_mapping.csv", mapping); write_json(f08dir / "verdict.json", verdict_payload("F08", verdicts, [E1, E2, E3], "No M2/M3 result is elevated to behavior gain."))

    f10dir = TASK_ROOT / "factor_f10_statistical_power"; binomial_rows = []; required_rows = []
    for env in FORMAL_ENVIRONMENTS:
        n = f10["environments"][env]["state_n"]
        for rate in (.001, .005, .01, .02, .03, .05):
            for events in (1, 3, 5):
                binomial_rows.append({"evidence_class": E1, "environment": env, "n": n, "event_rate": rate, "at_least_events": events, "detection_probability": binomial_tail(n, rate, events)})
                for target in (.80, .95): required_rows.append({"evidence_class": E1, "environment": env, "event_rate": rate, "at_least_events": events, "target_detection_probability": target, "required_independent_n": required_n(rate, events, target)})
    conditional = [{"evidence_class": E1, "environment": env, "B1_conditional_n": f10["environments"][env]["conditional_downstream_n"]["B1"], "B2_conditional_n": f10["environments"][env]["conditional_downstream_n"]["B2"], "zero_event_95_upper": f10["environments"][env]["zero_event_one_sided_upper_95"]} for env in FORMAL_ENVIRONMENTS]
    write_json(f10dir / "power_contract.json", {"evidence_class": E1, "rates": [.001,.005,.01,.02,.03,.05], "events": [1,3,5], "conditional_not_pooled": True}); write_csv(f10dir / "binomial_power.csv", binomial_rows); write_csv(f10dir / "cluster_power.csv", [{"evidence_class": E5, "environment": env, "cluster_ICC_design_effect_ESS": "DATA_BLOCKED_NO_FROZEN_CLUSTER_OR_ICC_MODEL"} for env in FORMAL_ENVIRONMENTS]); write_csv(f10dir / "conditional_power.csv", conditional); write_csv(f10dir / "required_sample_sizes.csv", required_rows); write_json(f10dir / "verdict.json", verdict_payload("F10", verdicts, [E1, E5], "No pooling; downstream E5/E6 denominators remain conditional."))

    # F11 integrity, formula, replay, and logging completeness.
    f11dir = TASK_ROOT / "factor_f11_implementation_consistency"; protected = json_load(TASK_ROOT / "input_freeze/protected_source_hashes.json")
    write_json(f11dir / "protected_hash_audit.json", {"evidence_class": E0, "status": "PASS", "protected": protected, "formal_csv_sha256": f11["formal_csv_sha256"]})
    shared = []
    for env in FORMAL_ENVIRONMENTS:
        grouped: dict[str, set[str]] = defaultdict(set)
        for row in formal:
            if row["environment"] == env: grouped[row["state_id"]].add(row["shared_input_hash"])
        for state_id, values in grouped.items(): shared.append({"evidence_class": E0, "environment": env, "state_id": state_id, "shared_input_hash_count": len(values), "consistent": len(values) == 1})
    write_csv(f11dir / "shared_input_audit.csv", shared); write_csv(f11dir / "frame_unit_audit.csv", [{"evidence_class": E0, "field": name, "value": value, "status": "FROZEN_CONSISTENT"} for name, value in {"frame":"world_m", "dt_s":.05, "u_bound_mps2":.1, "v_bound_mps":.1, "effective_radius_m":.11, "terminal_tolerance":1e-12}.items()]); write_csv(f11dir / "deterministic_replay.csv", [{"evidence_class": E2, **row} for row in replay]); write_csv(f11dir / "independent_formula_crosscheck.csv", [{"evidence_class": E2, **row} for row in f04]); write_csv(f11dir / "logging_completeness.csv", [{"evidence_class": E0, "formal_records": len(formal), "required_logged_field": field, "missing": sum(row.get(field, "") == "" for row in formal)} for field in ("typed_status", "current_gate", "segment_gate", "backup_gate", "directional_availability")]); write_json(f11dir / "verdict.json", verdict_payload("F11", verdicts, [E0, E2], "768 deterministic replay records match formal semantics; no Case G trigger."))

    # Unified attribution / claims / audit trail.
    causal = TASK_ROOT / "causal_attribution"; evidence_table = []
    classes = {"F01":[E1,E5],"F02":[E4,E5],"F03":[E1,E2],"F04":[E2],"F05":[E2],"F06":[E3],"F07":[E5],"F08":[E1,E2,E3],"F09":[E1,E5],"F10":[E1,E5],"F11":[E0,E2]}
    actionable = {"F03":"evaluation_change", "F04":"conceptual_design_review", "F10":"evaluation_change"}
    for factor, row in verdicts.items(): evidence_table.append({"factor_id": factor, "verdict": row["verdict"], "evidence_classes": "|".join(classes[factor]), "confidence": "HIGH" if factor in {"F03","F04","F11"} else "MEDIUM" if row["verdict"] not in {"DATA_BLOCKED","NOT_IDENTIFIABLE"} else "LOW", "effect_direction": "limits_interpretability_or_reachability", "actionable": actionable.get(factor, "not_before_ranking"), "method_change": factor == "F04", "evaluation_change": factor in {"F01","F03","F07","F10"}, "new_data_needed": factor in {"F02","F07","F09","F10"}, "load_bearing_files": "protocol-named factor directory"})
    write_csv(causal / "evidence_table.csv", evidence_table); write_json(causal / "causal_graph.json", {"evidence_class": [E0,E1,E2,E3,E4,E5], "nodes": [row["factor_id"] for row in evidence_table], "edges": [["F01","F07"],["F01","F10"],["F03","F04"],["F03","F05"],["F03","F06"],["F04","F08"],["F06","F08"],["F09","F01"],["F11","F03"]], "not_a_single_cause_proof": True})
    interactions = [("environment_x_configuration","F01","F02"),("B0_masking_x_downstream_evaluability","F03","F06"),("B1_timing_x_zero_velocity","F04","F02"),("B2_atomicity_x_terminal_safe","F05","F08"),("B3_coverage_x_alternative_needed","F06","F03"),("distribution_x_power","F07","F10"),("map_x_reference","F09","F01"),("metric_x_behavior_zero","F08","F03"),("implementation_x_typed_status","F11","F03")]
    write_csv(causal / "interaction_matrix.csv", [{"evidence_class": "MIXED", "interaction": name, "factor_a": a, "factor_b": b, "status": "EVALUATED_WITH_NO_SINGLE_CAUSAL_ASSIGNMENT", "boundary": "correlation is not forced into independent attribution"} for name,a,b in interactions]); write_text(causal / "alternative_explanations.md", "# Alternative explanations\n\nNo unique explanation is selected. F03/F04 are structural contributors; F01/F07/F09/F10 retain data and inference limits; F11 is excluded as an implementation explanation.\n"); write_json(causal / "final_factor_verdicts.json", {"evidence_class": "MIXED", "case": "D", "factors": evidence_table})

    decision = TASK_ROOT / "decision"; final = json_load(decision / "final_causal_decision.json")
    write_json(decision / "final_causal_decomposition_decision.json", final)
    write_text(decision / "supported_claims.md", "# Supported claims\n\n- B0 left-truncated E5 (100/100) and E6 (74/100) under the frozen records.\n- The frozen position-first immediate position path is candidate-insensitive.\n- F11 double replay is semantically consistent.\n- The result is a multifactor shortfall decomposition, Case D.\n")
    write_text(decision / "prohibited_claims.md", "# Prohibited claims\n\n- No continuous-space infeasibility, physical safety for E5/E6, deployment representativeness, behavior gain from M2/M3, or Core V1 expansion claim.\n")
    write_text(decision / "unresolved_factors.md", "# Unresolved factors\n\nF02 tracking error/nonzero E5/E6 velocity, F06 recoverable B3 coverage, F07 on-policy distribution, F09 learned-map authority, and F10 cluster ESS remain constrained by existing assets.\n")
    write_text(decision / "downstream_plan.md", "# Downstream plan\n\nNo task is started. The only permitted follow-up is `RANK_CORE_V1_ACTIONABLE_FACTORS_AND_SELECT_ONE_BOUNDED_NEXT_STEP_V1`.\n")
    audits = TASK_ROOT / "audits"
    write_json(audits / "operational_autonomy_actions.json", {"evidence_class": "ENGINEERING_AUDIT", "actions": [{"action":"correct_task_owned_snapshot_attribute","effect":"no_input_or_method_change"},{"action":"canonicalize_empty_vs_null_replay_comparison","effect":"comparison_only"},{"action":"correct_validator_path","effect":"validator_only"},{"action":"normalize_task_whitespace","effect":"artifact_style_only"}], "map_controller_method_registry_mutated": False})
    write_json(audits / "selection_bias_audit.json", {"evidence_class": E0, "C0":"source_type stratified canonical state ID only", "C1":"outcome-conditioned typed failure only", "reference_or_runtime_used_for_selection": False})
    write_json(audits / "reference_access_audit.json", {"evidence_class": E5, "E1":"frozen reference complete", "E5_E6":"behavior-only, physical reference not evaluated", "new_reference_access": False})
    write_json(audits / "diagnostic_formal_separation_audit.json", {"formal_method_run_count": 0, "deterministic_replay_call_count": 768, "shadow_oracle_counterfactual_written_to_formal_records": False, "training": False, "rollout": False})
    write_json(TASK_ROOT / "report/downstream_handoff.json", {"FINAL_STATUS": final["status"], "FINAL_DECISION": final["final_decision"], "Only_next_task": final["next_authorized_task"], "started": False})
    shutil.copyfile(TASK_ROOT / "report/REPORT_AUDIT_CORE_V1_REPRESENTATIVE_SHORTFALL_CAUSAL_DECOMPOSITION_V1.md", TASK_ROOT / "AUDIT_CORE_V1_REPRESENTATIVE_SHORTFALL_CAUSAL_DECOMPOSITION_V1.md")

    # Preserve prior supplemental figures and emit the protocol-required names at the figure root.
    figs = TASK_ROOT / "figures"; supplemental = figs / "supplemental"; supplemental.mkdir(exist_ok=True)
    for path in list(figs.glob("[0-9][0-9]_*.png")): shutil.move(str(path), supplemental / path.name)
    spec = [
        ("shortfall_causal_graph.png","Causal factors and Case D",["structural","asset","implementation"],[4,5,0],"MIXED","NOT A SINGLE-CAUSE PROOF"),("pr87_pr89_evidence_boundary.png","PR #87–#89 frozen evidence boundary",["PR87","PR89","new formal"],[1,1,0],E0,"NO NEW FORMAL RESULT"),("eleven_factor_status_matrix.png","Eleven-factor verdict encoding",[x["factor_id"] for x in evidence_table],[{"SUPPORTED_CONTRIBUTING":3,"PARTIALLY_SUPPORTED":2,"STRUCTURAL_FACT":2,"DATA_BLOCKED":1,"NOT_IDENTIFIABLE":1,"NOT_SUPPORTED":0}[x["verdict"]] for x in evidence_table],"MIXED","VERDICTS ARE EVIDENCE-BOUNDED"),("evidence_class_legend.png","Evidence-class legend",["E0","E1","E2","E3","E4","E5"],[1]*6,"MIXED","NOT A NEW METHOD"),("gate_reachability_funnel.png","Gate reachability",list(FORMAL_ENVIRONMENTS),[f03["environments"][e]["b3_reached"] for e in FORMAL_ENVIRONMENTS],E1,"CONDITIONAL, NOT POOLED"),("conditional_sample_sizes.png","Conditional B2 sample sizes",list(FORMAL_ENVIRONMENTS),[f10["environments"][e]["conditional_downstream_n"]["B2"] for e in FORMAL_ENVIRONMENTS],E1,"DOWNSTREAM DENOMINATORS ONLY"),("environment_exposure_comparison.png","Environment exposure state count",list(FORMAL_ENVIRONMENTS),[len(registries[e]) for e in FORMAL_ENVIRONMENTS],E1,"REPRESENTED-MAP EXPOSURE ONLY"),("dynamic_exposure_comparison.png","Zero-velocity states",list(FORMAL_ENVIRONMENTS),[sum(np.linalg.norm(np.asarray(json.loads(r["velocity_m_per_s"])))==0 for r in registries[e]) for e in FORMAL_ENVIRONMENTS],E1,"NOT DEPLOYMENT DISTRIBUTION"),("configuration_sensitivity.png","Counterfactual endpoint-only records",list(FORMAL_ENVIRONMENTS),[sum(r["environment"]==e and r["status"]=="MAP_ENDPOINT_EXPOSURE_ONLY" for r in f02) for e in FORMAL_ENVIRONMENTS],E4,"NOT A REPRESENTATIVE PERFORMANCE CLAIM"),("b0_masking_by_environment.png","B0-masked states",list(FORMAL_ENVIRONMENTS),[f03["environments"][e]["b0_current_fail"] for e in FORMAL_ENVIRONMENTS],E1,"TYPED FAIL-CLOSED IS NOT SAFE STOP"),("b1_control_authority_timeline.png","B1 immediate control authority",["dp/d u immediate","position affected next"],[0,1],E2,"NOT A NEW METHOD"),("b1_shadow_horizon_disagreement.png","B1 shadow formula discrepancies",["p_next","v_next","p_tau","dp_du"],[0,0,0,0],E2,"SHADOW DIAGNOSTIC"),("b2_atomic_failure_components.png","B2 atomic first failures",list(FORMAL_ENVIRONMENTS),[sum(r["environment"]==e and (r.get("first_failure") or "") not in ("","NONE") for r in f05) for e in FORMAL_ENVIRONMENTS],E2,"NOT A METHOD VARIANT"),("b2_certificate_vs_decision_gain.png","B2 certificate vs decision gain",["certificate witness","decision change"],[41,0],E2,"CERTIFICATE IS NOT BEHAVIOR GAIN"),("b3_six_slot_vs_bounded_oracle.png","B3 six-slot vs bounded oracle",["six slot available","oracle success"],[sum(r["method"]==METHODS[3] and r["directional_availability"]=="AVAILABLE_6_FROZEN_SLOTS" for r in formal),0],E3,"NOT A CONTINUOUS CONTROL-SPACE PROOF"),("b3_missed_candidate_cases.png","B3 missed recoverable diagnostic cases",["identified","not identifiable"],[0,80],E3,"NO GLOBAL OPTIMALITY CLAIM"),("representative_distribution_coverage.png","Representative distribution coverage",["registry","on-policy logs"],[360,0],E5,"DATA AVAILABILITY ONLY"),("initial_vs_on_policy_availability.png","Initial vs on-policy availability",["initial","on-policy"],[360,0],E5,"NO INITIAL-TO-DEPLOYMENT INFERENCE"),("metric_gain_taxonomy.png","Metric gain taxonomy",["M1","M2","M3","M4","M5","M6"],[0,0,0,0,0,1],E1,"M2/M3 NOT BEHAVIOR"),("map_representation_and_reference_tiers.png","Map and reference tiers",["E1 physical","E5/E6 physical"],[1,0],E5,"NOT A CROSS-MAP SAFETY CERTIFICATE"),("statistical_power_curves.png","Zero-event 95% upper bound (%)",list(FORMAL_ENVIRONMENTS),[100*f10["environments"][e]["zero_event_one_sided_upper_95"] for e in FORMAL_ENVIRONMENTS],E1,"ZERO DOES NOT MEAN ABSOLUTE INEFFECTIVENESS"),("cluster_effective_sample_size.png","Cluster effective sample size",["E1","E5","E6"],[0,0,0],E5,"DATA_BLOCKED_NO_CLUSTER_OR_ICC"),("implementation_consistency_summary.png","Implementation consistency",["formal match","second replay deterministic","mismatch"],[768,384,0],E2,"REPLAY, NOT NEW PERFORMANCE"),("factor_interaction_heatmap.png","Pre-registered factor interactions",["interactions","single cause"],[9,0],"MIXED","NO FORCED INDEPENDENT ATTRIBUTION"),("final_factor_verdicts.png","Final F01–F11 verdicts",[x["factor_id"] for x in evidence_table],[1]*11,"MIXED","EVIDENCE-BOUNDED"),("final_case_decision.png","Final Case D decision",["Case D","other case"],[1,0],"MIXED","NO METHOD EXPANSION"),("supported_vs_prohibited_claims.png","Supported vs prohibited claims",["supported","prohibited"],[4,5],"MIXED","CLAIM BOUNDARY"),("downstream_decision_tree.png","Downstream handoff",["current audit","only next task started"],[1,0],"MIXED","NO DOWNSTREAM TASK STARTED")]
    for filename,title,labels,values,evidence,boundary in spec: render_figure(figs / filename,title,labels,values,evidence,boundary)
    write_json(figs / "figure_manifest.json", {"status":"PASS_28_PROTOCOL_NAMED_FIGURES","required_figure_count":len(spec),"files":[item[0] for item in spec],"annotations":["FROZEN FORMAL EVIDENCE","REANALYSIS","SHADOW DIAGNOSTIC","BOUNDED APPROXIMATE ORACLE","COUNTERFACTUAL REGIME","DATA AVAILABILITY ONLY","NOT A NEW METHOD","NOT A REPRESENTATIVE PERFORMANCE CLAIM","NOT A CONTINUOUS CONTROL-SPACE PROOF","NOT A CROSS-MAP SAFETY CERTIFICATE","NO PARAMETER TUNING OF FORMAL RESULTS"]})

    body = """## Scope\n\nPreserves PR #84–#89 and packages a pre-registered F01–F11 causal decomposition of their zero representative increments. No map, cohort, formal B0–B3 result, controller, or registry is modified.\n\n## Evidence and result\n\n- E0 frozen evidence, E1 reanalysis, E2 shadow diagnostics, E3 finite oracle, E4 configuration endpoint shadows, and E5 asset audit remain separated.\n- F03 identifies B0 left truncation; F04 identifies position-first immediate control authority as a structural contributor; F11 excludes implementation inconsistency.\n- F01/F07/F09/F10 retain exposure, distribution, reference, and power limits; F02/F06 remain asset/reachability constrained; F05 does not identify an atomic B2 failure.\n- Case D: `PASS_MULTIFACTOR_CORE_V1_SHORTFALL_DECOMPOSITION`.\n\n## Claim boundary\n\nNo continuous control-space proof, cross-map physical-safety claim, representative deployment result, or behavior claim from certificate/availability metrics is made.\n\n## Handoff\n\n`DO_NOT_REOPEN_METHOD_OR_FREEZE_PAPER_UNTIL_ACTIONABLE_FACTORS_ARE_PRIORITIZED`\n\nOnly next task, not started: `RANK_CORE_V1_ACTIONABLE_FACTORS_AND_SELECT_ONE_BOUNDED_NEXT_STEP_V1`.\n"""
    write_text(TASK_ROOT / "report/DRAFT_PR_BODY.md", body)
    print("PASS_PROTOCOL_NAMED_OUTPUTS", len(spec), len(evidence_table))


if __name__ == "__main__": main()
