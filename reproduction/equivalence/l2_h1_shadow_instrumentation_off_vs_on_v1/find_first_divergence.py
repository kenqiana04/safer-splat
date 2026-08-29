"""Locate and quantify the first exact semantic trace divergence."""

from __future__ import annotations

from typing import Any

from canonical_trace_hash import PRIMARY_STEP_FIELDS, canonicalize


def _numeric_difference(left: Any, right: Any) -> dict[str, Any]:
    if isinstance(left, (int, float)) and not isinstance(left, bool) and isinstance(right, (int, float)) and not isinstance(right, bool):
        absolute = abs(float(left) - float(right))
        scale = max(abs(float(left)), abs(float(right)))
        return {"absolute_difference": absolute, "relative_difference": None if scale == 0.0 else absolute / scale}
    if isinstance(left, list) and isinstance(right, list) and len(left) == len(right):
        differences = [abs(float(a) - float(b)) for a, b in zip(left, right) if isinstance(a, (int, float)) and isinstance(b, (int, float))]
        if len(differences) == len(left) and differences:
            scale = max(max(abs(float(item)) for item in left), max(abs(float(item)) for item in right))
            maximum = max(differences)
            return {"absolute_difference_max": maximum, "relative_difference_max": None if scale == 0.0 else maximum / scale}
    return {"absolute_difference": "NOT_NUMERIC", "relative_difference": "NOT_NUMERIC"}


def first_divergence(left: dict[str, Any], right: dict[str, Any], *, pair_label: str) -> dict[str, Any] | None:
    for header in ("trial_id", "seed", "map_authority_id"):
        if canonicalize(left.get(header)) != canonicalize(right.get(header)):
            return {
                "pair": pair_label, "trial_id": left.get("trial_id"), "step_id": None,
                "field": header, "left": left.get(header), "right": right.get(header),
                **_numeric_difference(left.get(header), right.get(header)),
            }
    left_steps, right_steps = left.get("steps", []), right.get("steps", [])
    if len(left_steps) != len(right_steps):
        step = min(len(left_steps), len(right_steps))
        return {
            "pair": pair_label, "trial_id": left.get("trial_id"), "step_id": step,
            "field": "trace_length", "left": len(left_steps), "right": len(right_steps),
            **_numeric_difference(len(left_steps), len(right_steps)),
        }
    for index, (left_step, right_step) in enumerate(zip(left_steps, right_steps)):
        for field in PRIMARY_STEP_FIELDS:
            if canonicalize(left_step.get(field)) != canonicalize(right_step.get(field)):
                context = {
                    "pair": pair_label,
                    "trial_id": left.get("trial_id"),
                    "step_id": index,
                    "field": field,
                    "left": left_step.get(field),
                    "right": right_step.get(field),
                    "previous_left_step": None if index == 0 else left_steps[index - 1],
                    "previous_right_step": None if index == 0 else right_steps[index - 1],
                }
                context.update(_numeric_difference(left_step.get(field), right_step.get(field)))
                return context
    return None
