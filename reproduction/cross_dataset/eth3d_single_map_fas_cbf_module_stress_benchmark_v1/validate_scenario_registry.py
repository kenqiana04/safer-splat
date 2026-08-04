#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from eth3d_controller_core import sha256_json


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("registry", type=Path); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); registry = json.loads(args.registry.read_text(encoding="utf-8"))
    core = {key: value for key, value in registry.items() if key not in {"registry_sha256", "status"}}
    scenarios = registry["scenarios"]; counts = Counter(row["group"] for row in scenarios)
    checks = {
        "identity": sha256_json(core) == registry["registry_sha256"],
        "unique_ids": len({row["scenario_id"] for row in scenarios}) == len(scenarios),
        "method_independent": registry["method_independent"] is True,
        "no_rollout_metric_reads": registry["controller_rollout_result_read_count"] == 0,
        "all_groups_at_least_10": len(counts) == 5 and min(counts.values()) >= 10,
        "count_at_least_70": len(scenarios) >= 70,
        "frozen_dynamics": all(row["dt"] == 0.05 and row["max_steps"] == 200 for row in scenarios),
    }
    result = {"status": "PASS_SCENARIO_REGISTRY_VALIDATION" if all(checks.values()) else "FAIL_SCENARIO_REGISTRY_VALIDATION",
              "checks": checks, "scenario_count": len(scenarios), "group_counts": dict(counts),
              "registry_sha256": registry["registry_sha256"]}
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    if not all(checks.values()): raise RuntimeError(result)
    print(result["status"]); return 0


if __name__ == "__main__": raise SystemExit(main())
