from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def csv_rows(relative: str):
    with (ROOT / relative).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def test_candidate_and_scoring_freeze() -> None:
    registry = load_json("candidates/candidate_direction_registry.json")
    contract = load_json("scoring/scoring_contract.json")
    assert registry["candidate_count"] == 9
    assert [c["id"] for c in registry["candidates"]] == [f"D{i}" for i in range(9)]
    assert sum(contract["positive_weights"].values()) == 100
    assert sum(contract["risk_weights"].values()) == 100
    assert contract["frozen_before_results"] is True


def test_event_audit_uses_only_representative_holdout() -> None:
    rows = csv_rows("data/query_event_rate_records.csv")
    assert len(rows) == 320
    assert {r["cohort"] for r in rows} == {"REPRESENTATIVE_HOLDOUT"}
    assert sum(r["query_type"] == "point" for r in rows) == 160
    assert sum(r["query_type"] == "short_segment" for r in rows) == 160
    assert not any(r["false_free"].lower() == "true" for r in rows)
    assert not any(r["reference_collision"].lower() == "true" for r in rows)


def test_new_method_gates_not_relaxed() -> None:
    rows = csv_rows("scoring/fatal_gate_audit.csv")
    for direction in [f"D{i}" for i in range(1, 9)]:
        own = [r for r in rows if r["direction"] == direction]
        assert len(own) == 10
        assert any(r["result"] == "FAIL" for r in own)


def test_decision_is_case_d_without_new_method() -> None:
    decision = load_json("decision/final_direction_decision.json")
    handoff = load_json("report/downstream_handoff.json")
    assert decision["case"] == "D"
    assert decision["selected_direction"] == "D0"
    assert decision["directions_passing_all_new_method_gates"] == []
    assert decision["no_threshold_relaxation"] is True
    assert handoff["new_method_authorized"] is False
    assert handoff["training_authorized"] is False


def test_required_review_and_figure_counts() -> None:
    assert len(list((ROOT / "literature" / "competitor_cards").glob("*.md"))) == 15
    assert len(list((ROOT / "reviews").glob("D*/*_review.md"))) == 12
    assert len(list((ROOT / "figures").glob("*.png"))) == 24


def test_claim_boundary_contains_nonclaims() -> None:
    rows = csv_rows("history/claim_boundary_registry.csv")
    prohibited = {r["claim"] for r in rows if r["status"] == "PROHIBITED"}
    assert any("broadly replaces SAFER" in claim for claim in prohibited)
    assert any("50 ms" in claim for claim in prohibited)
    assert any("collision superiority" in claim for claim in prohibited)
