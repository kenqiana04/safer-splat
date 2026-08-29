"""Canonical exact hashing for control-trace equivalence evidence."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


def canonicalize(value: Any) -> Any:
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("nonfinite value in canonical trace")
        return {"__float_hex__": value.hex()}
    if isinstance(value, dict):
        return {str(key): canonicalize(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [canonicalize(item) for item in value]
    if hasattr(value, "item"):
        return canonicalize(value.item())
    raise TypeError(f"unsupported canonical value: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        canonicalize(value), ensure_ascii=False, allow_nan=False,
        sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def semantic_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


PRIMARY_STEP_FIELDS = (
    "trial_id", "step_id", "seed", "x_k", "u_des", "selected_u_k",
    "solver_success", "controller_branch", "plant_input_x", "plant_input_u",
    "plant_output_x_next", "termination_flag", "termination_reason",
    "goal", "goal_terminal_status", "map_authority_id",
)


def primary_step(step: dict[str, Any]) -> dict[str, Any]:
    return {field: step.get(field) for field in PRIMARY_STEP_FIELDS}


def primary_trace(trace: dict[str, Any]) -> dict[str, Any]:
    return {
        "trial_id": trace["trial_id"],
        "seed": trace["seed"],
        "map_authority_id": trace["map_authority_id"],
        "steps": [primary_step(step) for step in trace["steps"]],
    }
