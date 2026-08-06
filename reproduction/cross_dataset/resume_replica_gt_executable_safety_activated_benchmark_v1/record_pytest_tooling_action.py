#!/usr/bin/env python3
"""Record the task-private pytest tool installation without changing science."""
from pathlib import Path
import sys

TASK_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TASK_ROOT))
from common import read_json, write_json


def main() -> None:
    path = TASK_ROOT / "operational_autonomy_actions.json"
    payload = read_json(path)
    action = {
        "id": "OA-005",
        "action": "Installed pytest 8.3.5 into task-owned runtime_work after the configured mirror failed TLS; used official PyPI through the preserved loopback proxy and did not modify the frozen Conda environment.",
        "scientific_contract_changed": False,
    }
    if not any(item["id"] == action["id"] for item in payload["actions"]):
        payload["actions"].append(action)
    payload["operational_autonomy_action_count"] = len(payload["actions"])
    write_json(path, payload)
    print("PASS_PYTEST_TOOLING_ACTION_RECORDED", len(payload["actions"]))


if __name__ == "__main__":
    main()
