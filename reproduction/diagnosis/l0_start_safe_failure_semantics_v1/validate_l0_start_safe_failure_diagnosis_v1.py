#!/usr/bin/env python3
"""Task-local validator for the bounded L0 Start-Safe diagnosis."""

from __future__ import annotations

import csv
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence


EXPECTED_UPSTREAM = "14c844adeda8a0e8eb418abcdbaac62c701e2910"
TASK_RELATIVE = Path("reproduction/diagnosis/l0_start_safe_failure_semantics_v1")
EXPECTED_VALIDATOR_STATUS = "PASS_L0_START_SAFE_FAILURE_SEMANTICS_DIAGNOSIS_V1_VALIDATION"


def barrier_from_signed_squared_clearance(signed_squared_clearance: float, effective_radius: float) -> float:
    return signed_squared_clearance - effective_radius * effective_radius


def effective_radius(robot_radius: float, safety_margin: float) -> float:
    return robot_radius + safety_margin


def local_coordinates(
    point: Sequence[float], mean: Sequence[float], rotation: Sequence[Sequence[float]]
) -> tuple[float, float, float]:
    delta = tuple(float(p) - float(m) for p, m in zip(point, mean))
    return tuple(sum(float(rotation[row][col]) * delta[row] for row in range(3)) for col in range(3))  # type: ignore[return-value]


def sentinel_indices(n: int) -> tuple[int, int, int]:
    if n < 3:
        raise ValueError("at least three committed steps required")
    return 0, (n - 1) // 2, n - 1


def status_from_h(h: float) -> str:
    if not math.isfinite(h):
        return "UNKNOWN"
    return "PASS" if h >= 0.0 else "FAIL"


def path_is_task_local(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.startswith(str(TASK_RELATIVE).replace("\\", "/") + "/")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def git_lines(repo: Path, *args: str) -> list[str]:
    output = subprocess.check_output(["git", *args], cwd=repo, text=True, encoding="utf-8")
    return [line for line in output.splitlines() if line]


def validate(repo: Path) -> list[str]:
    task = repo / TASK_RELATIVE
    failures: list[str] = []
    required = [
        "README.md", "START_SAFE_FAILURE_DIAGNOSIS_INPUT_LOCK.json", "l0_barrier_math_contract.md",
        "barrier_formula_audit.json", "frame_scale_state_audit.json", "map_obstacle_semantics_audit.json",
        "controller_l0_geometry_contract_comparison.json", "SENTINEL_SAMPLE_LOCK.json", "sentinel_l0_h.csv",
        "sentinel_h_summary.json", "requery_l0_sentinels.py", "root_cause_diagnosis.json",
        "l0_start_safe_failure_review.json", "FINAL_CASE_DECISION.json", "downstream_handoff.json",
        "DRAFT_PR_BODY.md", "validation_result.json", "report/REPORT_DIAGNOSE_L0_START_SAFE_FAILURE_SEMANTICS_V1.md",
    ]
    for relative in required:
        require((task / relative).is_file(), f"missing artifact: {relative}", failures)

    lock = load_json(task / "START_SAFE_FAILURE_DIAGNOSIS_INPUT_LOCK.json")
    require(lock["pr104_head_sha"] == EXPECTED_UPSTREAM, "PR104 head mismatch in input lock", failures)
    require(lock["formal_row_count"] == 14122, "formal row count drift", failures)
    require(lock["frozen_L0_FAIL"] == 14122, "L0 FAIL count drift", failures)
    require(lock["frozen_L0_UNKNOWN"] == 0, "L0 UNKNOWN count drift", failures)
    require(lock["raw_h_logged"] is False, "raw_h_logged boundary drift", failures)
    require(lock["runtime_mutation_authority"] is False, "runtime mutation authority present", failures)
    require(lock["scientific_result_mutation_authority"] is False, "scientific mutation authority present", failures)

    remote_ref = git_lines(repo, "rev-parse", "refs/remotes/origin/diagnose-l0-shadow-certifier-semantics-v1")[0]
    require(remote_ref == EXPECTED_UPSTREAM, "local remote-tracking PR104 identity drift", failures)

    formula = load_json(task / "barrier_formula_audit.json")
    frame = load_json(task / "frame_scale_state_audit.json")
    map_audit = load_json(task / "map_obstacle_semantics_audit.json")
    comparison = load_json(task / "controller_l0_geometry_contract_comparison.json")
    for name, value in (("formula", formula), ("frame", frame), ("map", map_audit), ("comparison", comparison)):
        require(bool(value.get("source_evidence")), f"{name} audit lacks source evidence", failures)

    require(formula["classification"] == "FORMULA_CONSISTENT", "formula classification drift", failures)
    require(frame["frame_verdict"] == "CONSISTENT", "frame verdict drift", failures)
    require(frame["scale_verdict"] == "CONSISTENT", "scale verdict drift", failures)
    require(comparison["verdict"] == "PARTIALLY_EQUIVALENT", "controller/L0 verdict drift", failures)

    sentinel_lock = load_json(task / "SENTINEL_SAMPLE_LOCK.json")
    sentinel_summary = load_json(task / "sentinel_h_summary.json")
    root = load_json(task / "root_cause_diagnosis.json")
    require(root["static_root_cause_established"] is False, "sentinel gate not justified", failures)
    require(root["sentinel_executed"] is True, "sentinel execution not declared", failures)
    require(sentinel_lock["selection_rule_fixed_before_h_read"] is True, "sentinel selected after h read", failures)
    require(sentinel_lock["raw_h_read_count_at_lock_creation"] == 0, "h read before sentinel lock", failures)
    require(sentinel_lock["sample_count"] <= 15, "sentinel exceeded 15 states", failures)
    require(sentinel_summary["n"] <= 15 and sentinel_summary["query_count"] <= 15, "more than 15 h values reconstructed", failures)
    require(sentinel_summary["rollout_count"] == 0, "rollout was executed", failures)

    with (task / "sentinel_l0_h.csv").open("r", encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    require(len(rows) == 15, "sentinel CSV cardinality mismatch", failures)
    require(all(status_from_h(float(row["h"])) == row["status_from_h"] for row in rows), "sentinel status/sign mismatch", failures)
    require(all(float(row["raw_clearance_component"]) > 0.015 ** 2 for row in rows), "sentinel does not clear controller radius", failures)
    require(all(float(row["raw_clearance_component"]) < 0.11 ** 2 for row in rows), "sentinel does not lie inside L0 inflation", failures)

    status_paths = []
    for line in git_lines(repo, "status", "--porcelain"):
        status_paths.append(line[3:])
    require(all(path_is_task_local(path) for path in status_paths), "mutation exists outside task-local path", failures)
    require(not any(p.stat().st_size > 1_000_000 for p in task.rglob("*") if p.is_file()), "raw or oversized artifact committed", failures)

    forbidden = ("V1_RESULT_CHANGED", "14122 h values reconstructed")
    text = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in task.rglob("*") if p.is_file() and p.suffix in {".md", ".json", ".csv"})
    require(not any(token in text for token in forbidden), "V1 reinterpretation or forbidden reconstruction language found", failures)
    return failures


def main() -> int:
    repo = Path(__file__).resolve().parents[3]
    failures = validate(repo)
    if failures:
        print("FAIL_L0_START_SAFE_FAILURE_SEMANTICS_DIAGNOSIS_V1_VALIDATION")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(EXPECTED_VALIDATOR_STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
