from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def csv_rows(path: str):
    with (ROOT / path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_frozen_lineage():
    assert load("input_freeze/pr84_identity.json")["head"] == "04ebca2b1b35124ad0e61ebed96e491c9edae4bb"
    assert load("input_freeze/pr85_identity.json")["head"] == "7afef38392bec36d9d9811e5a22c816da5faf1ff"
    assert load("input_freeze/pr86_identity.json")["head"] == "d4f20f44a810afc2d6379853a286a3e18b175221"


def test_nested_method_matrix_and_fairness():
    matrix = load("methods/method_registry.json")
    methods = matrix["methods"]
    assert [item["method"].split("_")[0] for item in methods] == ["B0", "B1", "B2", "B3"]
    assert methods[2]["directional_slots"] == []
    assert len(methods[3]["directional_slots"]) == 6
    assert load("methods/fairness_audit.json")["all_pass"] is True


def test_locked_dual_registries():
    activated = load("registry/activated_registry_v1.json")
    representative = load("registry/representative_holdout_registry_v1.json")
    lock = load("registry/registry_lock.json")
    assert activated["selection_locked"] is True and len(activated["states"]) == 100
    assert representative["selection_locked"] is True and len(representative["states"]) == 160
    assert lock["prelock_future_reference_read_count"] == 0
    assert load("registry/registry_rebuild_audit.json")["rebuild_count_each"] == 3


def test_one_step_pairing_and_shared_inputs():
    records = csv_rows("benchmark/one_step_records.csv")
    assert len(records) == 1040
    by_state = defaultdict(list)
    for record in records:
        by_state[record["state_id"]].append(record)
    assert len(by_state) == 260
    assert all(len(values) == 4 for values in by_state.values())
    assert all(len({item["shared_input_hash"] for item in values}) == 1 for values in by_state.values())


def test_mechanism_and_false_safe():
    records = csv_rows("benchmark/one_step_records.csv")
    g3_b2 = [r for r in records if r["cohort"] == "ACTIVATED" and r["postlock_group"] == "G3" and r["method"].startswith("B2_")]
    g3_b3 = [r for r in records if r["cohort"] == "ACTIVATED" and r["postlock_group"] == "G3" and r["method"].startswith("B3_")]
    assert sum(r["committed"] == "True" for r in g3_b2) == 0
    assert sum(r["committed"] == "True" for r in g3_b3) == 20
    assert sum(r["represented_false_safe"] == "True" for r in records) == 0


def test_representative_selection_and_prevalence_separation():
    audit = load("audits/selection_leakage_audit.json")
    prevalence = load("audits/representative_prevalence_audit.json")
    assert audit["all_pass"] is True
    assert prevalence["activated_records_used_for_prevalence"] == 0
    assert prevalence["representative_registry_count"] == 160


def test_single_formal_attempt_and_rollout():
    marker = load("benchmark/formal_attempt.json")
    assert marker["formal_attempt_count"] == 1
    assert marker["status"] == "FORMAL_ATTEMPT_COMPLETED"
    assert len(csv_rows("benchmark/episode_summary.csv")) == 640
    assert len(csv_rows("benchmark/rollout_records.csv")) == 3603


def test_preregistered_case_c_decision():
    decision = load("statistics/project_decision_gates.json")
    assert decision["decision_case"] == "C"
    assert decision["scientific_mechanism_gate"] is True
    assert decision["active_utility_gate"] is True
    assert decision["representative_relevance_gate"] is False
    assert decision["final_status"] == "PASS_ACTIVATED_MECHANISM_WITH_LOW_REPRESENTATIVE_PREVALENCE"
