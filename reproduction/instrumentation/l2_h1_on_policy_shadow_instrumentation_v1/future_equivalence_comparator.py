"""Future OFF-vs-ON trace comparator; no navigation execution capability."""

from __future__ import annotations

from typing import Any


COMPARISON_FIELDS = (
    "selected_u_k_trace",
    "selected_candidate_hash",
    "solver_success_trace",
    "branch_trace",
    "seed",
    "termination",
    "map_authority",
    "controller_return_value",
)


def compare_traces(observer_off: dict[str, Any], observer_on: dict[str, Any]) -> dict[str, Any]:
    field_results = {field: observer_off.get(field) == observer_on.get(field) for field in COMPARISON_FIELDS}
    return {
        "comparison_fields": COMPARISON_FIELDS,
        "field_equal": field_results,
        "all_equal": all(field_results.values()),
        "performance_claim": False,
        "real_navigation_equivalence": False,
    }
