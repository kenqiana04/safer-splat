#!/usr/bin/env python3
"""Serial parent scheduler; every scientific arm is an independent child."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("/disk1/zlab/maintenance_records/tum_splatam_direct_safe_baseline_gate_v1_1")
REGISTRY = ROOT / "frozen_rollout_registry/frozen_direct_safe_rollout_registry_v1_1.json"
MANIFEST = ROOT / "manifests/run_manifest.json"
LABELS = ("DEVELOPMENT_PAIR", "HELDOUT_PAIR_1", "HELDOUT_PAIR_2", "HELDOUT_PAIR_3")
WATCHDOG_SECONDS = 90 * 60


def write_json(path: Path, value: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if registry.get("status") != "FROZEN" or manifest.get("pair_pool_gate") != "PASS":
        raise RuntimeError("PAIR_POOL_GATE_PASS_AND_FROZEN_REGISTRY_REQUIRED")
    executable = ROOT / "scripts/run_original_safer_baseline_v1_1.py"
    output_root = ROOT / "baseline_rollouts"
    for label in LABELS:
        state = manifest["states"][label]["state"]
        if state != "NOT_STARTED":
            raise RuntimeError(f"UNEXPECTED_NONFRESH_ARM_STATE:{label}:{state}")
        output = output_root / label
        if output.exists():
            raise RuntimeError(f"ROLL_OUT_OUTPUT_ALREADY_EXISTS:{label}")
        manifest["states"][label] = {**manifest["states"][label], "state": "RUNNING", "started_unix": time.time()}
        write_json(MANIFEST, manifest)
        command = [sys.executable, str(executable), "--registry", str(REGISTRY), "--label", label, "--output", str(output)]
        try:
            completed = subprocess.run(command, text=True, capture_output=True, timeout=WATCHDOG_SECONDS, check=False)
        except subprocess.TimeoutExpired as error:
            output.mkdir(parents=True, exist_ok=True)
            write_json(output / "summary.json", {"label": label, "terminal_status": "WATCHDOG_TIMEOUT", "strict_goal_reached": False, "watchdog_timeout": True, "stdout": error.stdout, "stderr": error.stderr})
            completed = None
        summary_path = output / "summary.json"
        if completed is None:
            terminal = "WATCHDOG_TIMEOUT"
        elif completed.returncode != 0 or not summary_path.exists():
            terminal = "INFRASTRUCTURE_FAILURE"
            output.mkdir(parents=True, exist_ok=True)
            write_json(output / "infrastructure_failure.json", {"returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
        else:
            terminal = json.loads(summary_path.read_text(encoding="utf-8"))["terminal_status"]
            (output / "child_stdout.log").write_text(completed.stdout, encoding="utf-8")
            (output / "child_stderr.log").write_text(completed.stderr, encoding="utf-8")
        manifest["states"][label] = {**manifest["states"][label], "state": "TERMINAL", "terminal_status": terminal, "ended_unix": time.time()}
        write_json(MANIFEST, manifest)
        if terminal == "INFRASTRUCTURE_FAILURE":
            raise RuntimeError(f"INFRASTRUCTURE_FAILURE:{label}")


if __name__ == "__main__":
    main()
