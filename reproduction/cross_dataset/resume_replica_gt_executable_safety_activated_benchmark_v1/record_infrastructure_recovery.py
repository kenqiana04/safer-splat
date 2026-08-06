#!/usr/bin/env python3
"""Record the one allowed same-manifest recovery after a task-level interruption."""
from __future__ import annotations

import sys
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TASK_ROOT))

from common import read_json, write_json


def main() -> None:
    marker_path = TASK_ROOT / "benchmark/formal_attempt.json"
    log_path = TASK_ROOT / "benchmark/formal_one_step.log"
    marker = read_json(marker_path)
    log = log_path.read_text(encoding="utf-8")
    if marker.get("status") != "FORMAL_ATTEMPT_STARTED" or marker.get("formal_attempt_count") != 1:
        raise SystemExit("INFRASTRUCTURE_RECOVERY_MARKER_BOUNDARY_VIOLATION")
    if any((TASK_ROOT / name).exists() for name in (
        "benchmark/one_step_records.csv",
        "benchmark/paired_method_summary.csv",
    )):
        raise SystemExit("FORMAL_OUTPUT_EXISTS_RECOVERY_FORBIDDEN")
    forbidden_log_tokens = ("Traceback", "BLOCKED_BY_", "PASS_FORMAL_ONE_STEP")
    if any(token in log for token in forbidden_log_tokens):
        raise SystemExit("LOG_CONTAINS_NON_INFRASTRUCTURE_TERMINAL_SIGNAL")
    marker.update({
        "status": "FORMAL_ATTEMPT_INFRASTRUCTURE_INTERRUPTED",
        "infrastructure_failure_count": int(marker.get("infrastructure_failure_count", 0)) + 1,
        "infrastructure_interruption_reason": "LOCAL_SSH_OBSERVATION_TIMEOUT_CLOSED_STDOUT_PIPE",
        "completed_formal_output_count_before_resume": 0,
        "scientific_result_replacement_count": 0,
    })
    write_json(marker_path, marker)
    actions_path = TASK_ROOT / "operational_autonomy_actions.json"
    actions = {
        "status": "RECORDED_TASK_LEVEL_AUTONOMY_ACTIONS",
        "actions": [
            {"id": "OA-001", "action": "Added canonical dataclass and enum serialization for immutable PR86 DirectionalSlot evidence.", "scientific_contract_changed": False},
            {"id": "OA-002", "action": "Preserved the still-running activated smoke after the local SSH observer timed out; no duplicate smoke was started.", "scientific_contract_changed": False},
            {"id": "OA-003", "action": "Created the task-owned smoke log directory after tee opened it before the smoke script could create it; did not rerun the completed one-step smoke.", "scientific_contract_changed": False},
            {"id": "OA-004", "action": "Recorded and resumed the interrupted formal attempt under the identical manifest after the local SSH observation pipe closed; no completed formal output existed.", "scientific_contract_changed": False},
        ],
    }
    actions["operational_autonomy_action_count"] = len(actions["actions"])
    write_json(actions_path, actions)
    print("PASS_SAME_MANIFEST_INFRASTRUCTURE_RECOVERY_RECORDED", len(actions["actions"]))


if __name__ == "__main__":
    main()
