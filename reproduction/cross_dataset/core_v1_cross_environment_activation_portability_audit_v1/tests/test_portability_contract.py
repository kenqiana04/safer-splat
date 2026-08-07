from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
METHODS = {
    "B0_CURRENT_CBF_ONLY",
    "B1_PLUS_SWEPT_SEGMENT",
    "B2_PLUS_TERMINAL_BACKUP",
    "B3_FULL_UNIFIED_WITH_DIRECTIONAL_ALTERNATIVES",
}


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def load_rows(relative: str):
    with (ROOT / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_frozen_method_contract() -> None:
    method = load_json("methods/method_registry.json")
    assert method["normative_model"] == "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1"
    assert (method["dt_s"], method["u_bound_inf"], method["v_bound_inf"]) == (0.05, 0.1, 0.1)
    assert (method["robot_radius_m"], method["effective_radius_m"]) == (0.1, 0.11)
    assert method["h_stop_max"] == 20
    assert set(method["methods"]) == METHODS
    assert method["six_slot_library_sha256"] == "3d491876234161d4e881ec1227c505cb07c0af00d5e881c5289fdf1f1577c6fe"


def test_locked_registries_and_selection() -> None:
    combined = load_json("registry/combined_registry_manifest.json")
    counts = {row["environment"]: row["state_count"] for row in combined["environments"]}
    assert counts == {
        "E1_REPLICA_GT_FINE": 160,
        "E2_ETH3D_LEARNED_GAUSSIAN": 0,
        "E3_TUM_SPLATAM": 0,
        "E4_TUM_GAUSSIAN_SLAM": 0,
        "E5_STONEHENGE_SAFER": 100,
        "E6_FLIGHT_SAFER": 100,
        "E7_TUM_SPLATFACTO_NEGATIVE_CONTROL": 0,
    }
    leakage = load_json("audits/selection_leakage_audit.json")
    assert leakage["prelock_method_run_count"] == 0
    assert leakage["prelock_future_reference_read_count"] == 0
    assert leakage["postlock_replacement_count"] == 0
    assert leakage["outcome_columns_consumed_by_selection"] == []


def test_completed_one_step_pairing_and_zero_incremental_result() -> None:
    rows = load_rows("benchmark/one_step_records.csv")
    assert len(rows) == 1440
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["environment"], row["state_id"])].append(row)
        assert row["unknown"] == "False"
        assert row["nonfinite"] == "False"
        assert row["infrastructure_failure"] == "False"
        assert row["any_incremental_activation"] == "False"
    assert len(grouped) == 360
    assert Counter(environment for environment, _ in grouped) == {
        "E1_REPLICA_GT_FINE": 160,
        "E5_STONEHENGE_SAFER": 100,
        "E6_FLIGHT_SAFER": 100,
    }
    for values in grouped.values():
        assert {row["method"] for row in values} == METHODS
        assert len({row["shared_input_hash"] for row in values}) == 1


def test_case_c_decision_and_no_synthetic_rollout() -> None:
    formal = load_json("benchmark/formal_attempt.json")
    decision = load_json("decision/final_portability_decision.json")
    gate = load_json("statistics/portability_gate_audit.json")
    assert formal["formal_attempt_count"] == 1
    assert formal["same_manifest_resume_count"] == 0
    assert formal["natural_incremental_event_count"] == 0
    assert formal["natural_rollout_episode_count"] == 0
    assert load_rows("benchmark/natural_event_rollout_records.csv") == []
    assert gate["case"] == "CASE_C"
    assert gate["qualified_count"] == 0
    assert gate["e7_in_pass_fail"] is False
    assert gate["cross_tier_pooling"] is False
    assert decision["final_status"] == "NO_CORE_V1_REPRESENTATIVE_PORTABILITY_SIGNAL"
    assert decision["final_decision"] == "UPHOLD_PR88_CASE_D_AND_STOP_CORE_V1_METHOD_EXPANSION"
