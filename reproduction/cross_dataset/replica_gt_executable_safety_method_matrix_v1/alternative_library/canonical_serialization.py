"""Strict float64 canonical bytes; signed zero is normalized to positive zero."""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any

import numpy as np


def canonical_float(value: float) -> str:
    scalar = float(value)
    if not math.isfinite(scalar):
        raise ValueError("NONFINITE_CANONICAL_FLOAT")
    return "0x0.0p+0" if scalar == 0.0 else scalar.hex()


def canonical_value(value: Any) -> Any:
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float):
        return {"$float64": canonical_float(value)}
    if isinstance(value, dict):
        return {str(key): canonical_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [canonical_value(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    return value


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(canonical_value(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()
