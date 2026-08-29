#!/usr/bin/env python3
"""Run exactly five preregistered WRAPPER_ON pilot trials without retry."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
from typing import Any


UPSTREAM_HEAD = "b47b0e924804e3e446b1f9c184ee5ea5d268d613"
SELECTION = (10, 30, 50, 70, 90)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def diagnostic(task_root: Path) -> dict[str, Any]:
    commands = {
        "gpu": ["nvidia-smi", "-i", "1", "--query-gpu=index,name,memory.used,utilization.gpu", "--format=csv,noheader"],
        "compute": ["nvidia-smi", "-i", "1", "--query-compute-apps=pid,process_name,used_gpu_memory", "--format=csv,noheader"],
        "task_process": ["pgrep", "-af", str(task_root)],
    }
    result: dict[str, Any] = {}
    for name, command in commands.items():
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        result[name] = {
            "returncode": completed.returncode,
            "stdout": completed.stdout.strip(),
            "stderr": completed.stderr.strip(),
        }
    return result


def valid_activation(activation: dict[str, Any]) -> bool:
    return all((
        activation.get("arm") == "WRAPPER_ON",
        activation.get("wrapper_loaded") is True,
        activation.get("observer_enabled") is True,
        activation.get("worker_start_requested") is True,
        activation.get("intended_state_valid") is True,
        activation.get("worker_alive_after_shutdown") is False,
        activation.get("leftover_shadow_worker_count") == 0,
        activation.get("shutdown_status") == "SHUTDOWN_COMPLETE",
        activation.get("controller_authority") is False,
        activation.get("controller_intervention_count") == 0,
        activation.get("selected_candidate_replacement_count") == 0,
    ))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--task-code", type=Path, required=True)
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--python", type=Path, required=True)
    args = parser.parse_args()

    checkout = args.checkout.resolve(strict=True)
    task_code = args.task_code.resolve(strict=True)
    python = args.python.resolve(strict=True)
    task_root = args.task_root.resolve()
    if task_root.exists():
        raise FileExistsError(f"task root already exists: {task_root}")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=checkout, text=True, capture_output=True, check=True,
    ).stdout.strip()
    if head != UPSTREAM_HEAD:
        raise RuntimeError(f"UPSTREAM_HEAD_MISMATCH:{head}")
    selection = load_json(task_code / "pilot_trial_selection.json")
    if tuple(selection.get("selected_trial_ids", ())) != SELECTION:
        raise RuntimeError("PILOT_SELECTION_MISMATCH")
    if selection.get("frozen_before_any_pilot_navigation_run") is not True:
        raise RuntimeError("PILOT_SELECTION_NOT_FROZEN")

    raw_root = task_root / "raw_runs"
    raw_root.mkdir(parents=True)
    (task_root / "compact").mkdir()
    run_records: list[dict[str, Any]] = []
    runner = checkout / "reproduction/equivalence/l2_h1_shadow_instrumentation_off_vs_on_v1/server_run_one.py"
    if not runner.is_file():
        raise FileNotFoundError(runner)

    for trial_id in SELECTION:
        run_id = f"pilot_c_trial{trial_id:03d}"
        run_dir = raw_root / run_id
        command = [
            str(python), "-B", str(runner),
            "--arm", "C", "--trial-id", str(trial_id), "--seed", "0",
            "--run-id", run_id, "--checkout", str(checkout), "--run-dir", str(run_dir),
            "--queue-capacity", "8", "--shutdown-timeout", "120",
        ]
        env = os.environ.copy()
        env.update({
            "CUDA_VISIBLE_DEVICES": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "CUBLAS_WORKSPACE_CONFIG": ":4096:8",
        })
        before = diagnostic(task_root)
        completed = subprocess.run(command, cwd=checkout, env=env, text=True, capture_output=True, check=False)
        (task_root / f"{run_id}.stdout.log").write_text(completed.stdout, encoding="utf-8", newline="\n")
        (task_root / f"{run_id}.stderr.log").write_text(completed.stderr, encoding="utf-8", newline="\n")
        after = diagnostic(task_root)
        record: dict[str, Any] = {
            "run_id": run_id,
            "trial_id": trial_id,
            "arm": "WRAPPER_ON",
            "fresh_process": True,
            "retry_count": 0,
            "data_role": "PILOT_QA_ONLY",
            "eligible_for_formal_prospective_cohort": False,
            "exit_code": completed.returncode,
            "run_relative_path": f"raw_runs/{run_id}",
            "gpu_process_before": before,
            "gpu_process_after": after,
        }
        metadata_path = run_dir / "run_metadata.json"
        activation_path = run_dir / "arm_activation.json"
        environment_path = run_dir / "environment_identity.json"
        if metadata_path.is_file() and activation_path.is_file() and environment_path.is_file():
            record["metadata"] = load_json(metadata_path)
            record["activation"] = load_json(activation_path)
            record["environment"] = load_json(environment_path)
            record["activation_valid"] = valid_activation(record["activation"])
        else:
            record["activation_valid"] = False
        run_records.append(record)
        manifest = {
            "schema_version": "L2_H1_SHADOW_LOGGING_COMPLETENESS_PILOT_RUN_MANIFEST_V1",
            "upstream_head": UPSTREAM_HEAD,
            "data_role": "PILOT_QA_ONLY",
            "eligible_for_formal_prospective_cohort": False,
            "selected_trial_ids": list(SELECTION),
            "replacement_count": 0,
            "retry_count": 0,
            "runs": run_records,
        }
        write_json(task_root / "pilot_run_manifest.json", manifest)
        if completed.returncode != 0 or record["activation_valid"] is not True:
            write_json(task_root / "pipeline_result.json", {
                "status": "BLOCKED_L2_H1_SHADOW_LOGGING_PILOT_BY_INVALID_RUN",
                "failed_run_id": run_id,
                "completed_run_count": len(run_records),
                "no_retry": True,
            })
            return 2

    write_json(task_root / "pipeline_result.json", {
        "status": "FIVE_PILOT_RUNS_COMPLETE_PENDING_AGGREGATION",
        "completed_run_count": len(run_records),
        "selected_trial_ids": list(SELECTION),
        "no_retry": True,
    })
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
