#!/usr/bin/env python3
"""Freeze the formal controller benchmark after unit and smoke gates pass."""
from __future__ import annotations

import argparse
import glob
import json
from collections import Counter
from pathlib import Path

from eth3d_controller_core import METHODS, atomic_json, sha256_file, sha256_json
from fas_cbf_modules import DT_MARGIN, RECOVERY_HORIZON


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--task-root", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); root = args.task_root
    registry = json.loads((root/"scenario_generation/scenario_registry.json").read_text())
    smoke = json.loads((root/"smoke_controller/run_manifest.json").read_text())
    results = [json.loads(Path(path).read_text()) for path in glob.glob(str(root/"smoke_controller/results/*.json")) if not path.endswith(".complete.json")]
    unit = {}
    for path in sorted((root/"unit_tests").glob("*.json")):
        unit[path.stem] = json.loads(path.read_text())["status"]
    scripts = ["fas_cbf_modules.py", "eth3d_controller_core.py",
               "run_formal_paired_controller_benchmark.py",
               "generate_eth3d_fas_cbf_stress_scenarios.py"]
    checks = {
        "registry_100": len(registry["scenarios"]) == 100,
        "registry_five_by_twenty": sorted(registry["group_counts"].values()) == [20]*5,
        "smoke_complete_50": smoke["state"] == "COMPLETED" and smoke["terminal_run_count"] == 50,
        "smoke_no_numerical_failure": all(row["status"] != "NUMERICAL_FAILURE" for row in results),
        "smoke_reference_not_controller_input": sum(row.get("reference_oracle_controller_input_count",0) for row in results) == 0,
        "smoke_map_unmodified": smoke["map_sha_after"] == smoke["identity"]["map_ply_sha256"],
        "all_unit_tests_pass": len(unit) == 4 and all(value.startswith("PASS_") for value in unit.values()),
        "formal_result_count_zero": not any((root/"formal_controller/results").glob("*.json")) if (root/"formal_controller/results").exists() else True,
    }
    if not all(checks.values()): raise RuntimeError(checks)
    lock_core = {
        "task": "ETH3D_LOCAL_SAFETY_CONTROLLER_STRESS_BENCHMARK_V1",
        "methods": list(METHODS), "scenario_registry_sha256": registry["registry_sha256"],
        "scenario_count": 100, "dt": 0.05, "runtime_dt_samples": 5,
        "dt_margin": DT_MARGIN, "recovery_horizon": RECOVERY_HORIZON,
        "control_bound_component": 0.10, "velocity_bound_component": 0.10,
        "robot_radius_m": 0.10, "epsilon_m": 0.01, "alpha": 5.0, "beta": 1.0,
        "candidate_budget": 2000, "max_steps": 200,
        "map_ply_sha256": smoke["identity"]["map_ply_sha256"],
        "canonical_tree_sha256": smoke["identity"]["canonical_tree_sha256"],
        "source_commit": smoke["identity"]["source_commit"],
        "script_sha256": {name: sha256_file(root/name) for name in scripts},
        "unit_test_statuses": unit, "smoke_status_counts": dict(Counter(row["status"] for row in results)),
        "checks": checks, "reference_oracle_controller_input_count": 0,
        "post_lock_parameter_change_count": 0,
    }
    lock = dict(lock_core); lock["execution_lock_sha256"] = sha256_json(lock_core)
    lock["status"] = "PASS_FORMAL_CONTROLLER_EXECUTION_LOCK"
    atomic_json(args.output, lock); print(json.dumps({"status":lock["status"],"sha256":lock["execution_lock_sha256"]},sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())
