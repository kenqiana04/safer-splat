"""Capture existing branch facts without adding a controller gate."""

from __future__ import annotations

from dataclasses import dataclass


NOT_OBSERVED_IN_PRODUCTION = "NOT_OBSERVED_IN_PRODUCTION"
SHADOW_RECOMPUTED_FROZEN_CERTIFIER = "SHADOW_RECOMPUTED_FROZEN_CERTIFIER"


@dataclass(frozen=True, slots=True)
class ReachabilityFacts:
    l0_reached: bool
    l0_status_observed: str
    l0_observation_source: str
    candidate_preparation_reached: bool
    solver_success: bool
    decision_committed: bool
    l1_reached_or_observed: bool
    l1_status_observed: str
    l1_observation_source: str
    l2_reached: bool
    l2_reachability_reason: str

    def semantic_dict(self) -> dict:
        return {
            "l0_reached": self.l0_reached,
            "l0_status_observed": self.l0_status_observed,
            "l0_observation_source": self.l0_observation_source,
            "candidate_preparation_reached": self.candidate_preparation_reached,
            "solver_success": self.solver_success,
            "decision_committed": self.decision_committed,
            "l1_reached_or_observed": self.l1_reached_or_observed,
            "l1_status_observed": self.l1_status_observed,
            "l1_observation_source": self.l1_observation_source,
            "l2_reached": self.l2_reached,
            "l2_reachability_reason": self.l2_reachability_reason,
        }


def baseline_commit_facts(solver_success: bool) -> ReachabilityFacts:
    """Facts visible at the protected `run.py` CBF boundary.

    Core V1's primary `run.py` has no PR #84 L0/L1 control gates. Those fields
    therefore remain explicitly unobserved until the isolated worker recomputes
    them. No logging-only gate is invented.
    """

    committed = bool(solver_success)
    return ReachabilityFacts(
        l0_reached=False,
        l0_status_observed=NOT_OBSERVED_IN_PRODUCTION,
        l0_observation_source=NOT_OBSERVED_IN_PRODUCTION,
        candidate_preparation_reached=True,
        solver_success=committed,
        decision_committed=committed,
        l1_reached_or_observed=False,
        l1_status_observed=NOT_OBSERVED_IN_PRODUCTION,
        l1_observation_source=NOT_OBSERVED_IN_PRODUCTION,
        l2_reached=False,
        l2_reachability_reason="PENDING_SHADOW_RECOMPUTATION" if committed else "SOLVER_FAILURE",
    )
