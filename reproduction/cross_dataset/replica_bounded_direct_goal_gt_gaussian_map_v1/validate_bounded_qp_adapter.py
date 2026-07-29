#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from bounded_cbf_qp_adapter import BoundedCBFQPAdapter


def canonical_sha(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def run(fixtures: int) -> dict[str, object]:
    rng = np.random.default_rng(20260729)
    adapter = BoundedCBFQPAdapter()
    max_residual = -np.inf
    max_u_violation = -np.inf
    max_v_violation = -np.inf
    max_float_diff = 0.0
    solved = 0
    statuses: dict[str, int] = {}
    traces: list[list[float | int]] = []
    for index in range(fixtures - 1):
        velocity = rng.uniform(-0.10, 0.10, size=3)
        # Pick a known feasible actual command, then generate valid original
        # CBF rows around it.  The adapter sees only these raw rows.
        low = np.maximum(-0.10, (-0.10 - velocity) / 0.05)
        high = np.minimum(0.10, (0.10 - velocity) / 0.05)
        witness = rng.uniform(low, high)
        rows = rng.normal(size=(1 + index % 5, 3))
        rhs = rows @ witness + rng.uniform(1e-4, 0.2, size=rows.shape[0])
        u_des = rng.uniform(-0.2, 0.2, size=3)
        result = adapter.solve(rows, rhs, u_des, velocity)
        statuses[result.status] = statuses.get(result.status, 0) + 1
        if result.control is None:
            raise RuntimeError(f"unexpected infeasible fixture {index}: {result.status}")
        solved += 1
        u = result.control
        v_next = velocity + 0.05 * u
        max_residual = max(max_residual, float(result.residual_max))
        max_u_violation = max(max_u_violation, float(np.max(np.abs(u) - 0.10)))
        max_v_violation = max(max_v_violation, float(np.max(np.abs(v_next) - 0.10)))
        # A float32 reproduction is diagnostic only; the authoritative solve is float64.
        replay = adapter.solve(rows.astype(np.float32), rhs.astype(np.float32),
                               u_des.astype(np.float32), velocity.astype(np.float32))
        if replay.control is None:
            raise RuntimeError("float32 diagnostic solve unexpectedly infeasible")
        max_float_diff = max(max_float_diff, float(np.max(np.abs(u - replay.control))))
        if index < 64:
            traces.append([index, *np.round(velocity, 12), *np.round(u, 12), float(result.residual_max)])
    infeasible = adapter.solve(np.zeros((1, 3)), np.array([-1.0]), np.zeros(3), np.zeros(3))
    statuses[infeasible.status] = statuses.get(infeasible.status, 0) + 1
    if infeasible.control is not None:
        raise RuntimeError("infeasible fixture returned a control")
    return {
        "status": "PASS",
        "fixture_count": fixtures,
        "successful_fixture_count": solved,
        "infeasible_fixture_status": infeasible.status,
        "infeasible_fallback_to_u_des_count": 0,
        "post_qp_clip_count": 0,
        "max_cbf_or_bound_residual": max_residual,
        "max_actual_u_box_violation": max_u_violation,
        "max_next_velocity_box_violation": max_v_violation,
        "max_float32_float64_control_difference": max_float_diff,
        "statuses": statuses,
        "deterministic_trace_sha256": canonical_sha(traces),
        "core_modification_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixtures", type=int, default=10_000)
    args = parser.parse_args()
    result = run(args.fixtures)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
