#!/usr/bin/env python3
"""Validate compact ACTIVE_RUNTIME_PILOT_V2 evidence without rerunning arms."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
TRIALS = (5, 15, 25, 35, 45, 55, 65, 75, 85, 95)
ARMS = ("REFERENCE_CBF_QP", "ACTIVE_RUNTIME_V2")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def check(condition: bool, name: str, checks: list[dict]) -> None:
    checks.append({"check": name, "status": "PASS" if condition else "FAIL"})


def main() -> int:
    checks: list[dict] = []
    config = load(ROOT / "PILOT_CONFIG.json")
    lock = load(ROOT / "PILOT_INPUT_LOCK.json")
    check(config["trial_ids"] == list(TRIALS), "frozen trial IDs", checks)
    check(config["arm_order"] == list(ARMS), "frozen arm order", checks)
    check(config["max_steps"] == 500, "frozen horizon", checks)
    check(config["oracle"]["feedback"] is False and config["oracle"]["posthoc_only"] is True, "posthoc zero-feedback oracle", checks)
    check(config["oracle"]["collision_radius_m"] == 0.015 and config["oracle"]["certification_margin_radius_m"] == 0.025, "collision and margin radii separate", checks)
    check(lock["direct_upstream"]["head"] == "2a8fd73cdc660fccbf9522f4d24e9d85f2e03a2c", "PR133 exact head", checks)
    summaries = []
    for trial in TRIALS:
        for arm in ARMS:
            arm_dir = ROOT / "raw" / f"trial_{trial:03d}" / arm.lower()
            path = arm_dir / "summary.json"
            check(path.is_file(), f"summary {trial} {arm}", checks)
            if not path.is_file():
                continue
            row = load(path); summaries.append(row)
            check(row["trial_id"] == trial and row["arm"] == arm, f"arm identity {trial} {arm}", checks)
            check(row["execution_complete"] is True, f"execution complete {trial} {arm}", checks)
            check(row["hard_blocker"] is None, f"no hard blocker {trial} {arm}", checks)
            check(row["integrity_failure_count"] == 0, f"integrity clean {trial} {arm}", checks)
            check(row["evaluation_eligible"] is True, f"oracle eligible {trial} {arm}", checks)
            raw_lock_path = arm_dir / "raw_evidence_lock.json"
            check(raw_lock_path.is_file(), f"raw lock {trial} {arm}", checks)
            if raw_lock_path.is_file():
                raw_lock = load(raw_lock_path)
                for item in raw_lock["files"]:
                    item_path = arm_dir / item["name"]
                    check(item_path.is_file() and item_path.stat().st_size == item["size"] and sha256(item_path) == item["sha256"], f"raw hash {trial} {arm} {item['name']}", checks)
                check(raw_lock["state_count"] == raw_lock["action_count"] + 1, f"state action alignment {trial} {arm}", checks)
            if arm == "ACTIVE_RUNTIME_V2":
                trace = arm_dir / "raw" / f"trial_{trial}" / "runtime_trace.jsonl"
                trace_lock = arm_dir / "raw" / f"trial_{trial}" / "runtime_trace_lock.json"
                check(trace.is_file() and trace_lock.is_file(), f"active trace and lock {trial}", checks)
                check(row.get("trace_record_count") == row.get("trace_lock_record_count"), f"active trace cardinality {trial}", checks)
    check(len(summaries) == 20, "20 arm summaries", checks)
    for name in ("pilot_trials.csv", "pilot_pairs.csv", "pilot_summary.json", "pilot_active_diagnostics.json", "pilot_oracle_audit.json", "REPORT_ACTIVE_RUNTIME_PILOT_V2.md", "downstream_handoff.json"):
        check((ROOT / name).is_file(), f"required artifact {name}", checks)
    if (ROOT / "pilot_summary.json").is_file():
        aggregate = load(ROOT / "pilot_summary.json")
        check(aggregate["pair_count_complete"] == 10 and aggregate["arm_count_complete"] == 20, "10 pairs 20 arms aggregate", checks)
        check(aggregate["p_value_count"] == 0 and aggregate["confidence_interval_count"] == 0, "descriptive analysis only", checks)
    repo = ROOT.parents[2]
    runtime_diff = subprocess.run(["git", "-C", str(repo), "diff", "--name-only", "2a8fd73cdc660fccbf9522f4d24e9d85f2e03a2c", "--", "reproduction/runtime", "run.py", "cbf", "dynamics", "splat"], text=True, capture_output=True, check=True).stdout.strip()
    check(runtime_diff == "", "runtime and production diff zero", checks)
    passed = all(item["status"] == "PASS" for item in checks)
    result = {"schema": "ACTIVE_RUNTIME_PILOT_V2_VALIDATION", "status": "PASS_ACTIVE_RUNTIME_PILOT_V2_VALIDATION" if passed else "FAIL_ACTIVE_RUNTIME_PILOT_V2_VALIDATION", "passed": sum(item["status"] == "PASS" for item in checks), "failed": sum(item["status"] == "FAIL" for item in checks), "checks": checks}
    (ROOT / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
