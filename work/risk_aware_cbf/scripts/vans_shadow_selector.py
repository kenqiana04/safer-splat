#!/usr/bin/env python3
"""Shadow-only nominal action candidate representation and selection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True)
class NominalActionCandidate:
    candidate_id: str
    candidate_name: str
    action: Any
    deviation_from_original: float
    generation_rule: str


@dataclass(frozen=True)
class CandidateEvaluation:
    candidate_id: str
    qp_feasible: bool
    qp_success: bool
    h1_warning: bool
    h2_warning: bool
    h3_warning: bool
    verified_h3: bool
    worst_predicted_h: float
    progress_proxy: float
    progress_delta_vs_original: float
    action_deviation: float
    evaluation_runtime_sec: float
    valid: bool
    notes: str


@dataclass(frozen=True)
class ShadowSelectionDecision:
    selected_candidate_id: str
    original_candidate_id: str
    differs_from_original: bool
    verified_alternative_exists: bool
    progress_nonworse_verified_alternative_exists: bool
    selection_reason: str
    modifies_control: bool
    claim_scope: str


def select_shadow_candidate(
    evaluations: Sequence[CandidateEvaluation],
    *,
    original_candidate_id: str = "N0",
    progress_tolerance: float = 1e-6,
) -> ShadowSelectionDecision:
    """Select a counterfactual candidate without modifying executed control.

    The score intentionally favors feasible and H3-verified candidates, then
    uses barrier-function margin, diagnostic progress proxy, original-action
    proximity, and candidate id as deterministic tie breakers.
    """

    if not evaluations:
        return ShadowSelectionDecision(
            selected_candidate_id=original_candidate_id,
            original_candidate_id=original_candidate_id,
            differs_from_original=False,
            verified_alternative_exists=False,
            progress_nonworse_verified_alternative_exists=False,
            selection_reason="no_valid_candidate_evaluations",
            modifies_control=False,
            claim_scope="shadow_counterfactual_only",
        )

    original = next(
        (item for item in evaluations if item.candidate_id == original_candidate_id),
        None,
    )
    original_progress = original.progress_proxy if original is not None else float("-inf")
    alternatives = [
        item
        for item in evaluations
        if item.candidate_id != original_candidate_id and item.valid
    ]
    verified_alternatives = [
        item for item in alternatives if item.qp_feasible and item.verified_h3
    ]
    progress_nonworse = [
        item
        for item in verified_alternatives
        if item.progress_proxy >= original_progress - progress_tolerance
    ]

    def score(item: CandidateEvaluation) -> tuple[Any, ...]:
        return (
            int(item.valid),
            int(item.qp_feasible),
            int(item.verified_h3),
            -int(item.h3_warning),
            item.worst_predicted_h,
            item.progress_proxy,
            -item.action_deviation,
            item.candidate_id,
        )

    selected = max(evaluations, key=score)
    return ShadowSelectionDecision(
        selected_candidate_id=selected.candidate_id,
        original_candidate_id=original_candidate_id,
        differs_from_original=selected.candidate_id != original_candidate_id,
        verified_alternative_exists=bool(verified_alternatives),
        progress_nonworse_verified_alternative_exists=bool(progress_nonworse),
        selection_reason=(
            "lexicographic_shadow_selection:"
            "valid>qp_feasible>h3_verified>worst_predicted_h>"
            "progress_proxy>low_original_deviation>candidate_id"
        ),
        modifies_control=False,
        claim_scope=(
            "Shadow counterfactual selection only; selected nominal action is "
            "not executed and does not establish closed-loop performance."
        ),
    )
