"""Run only naturally observed incremental events from the formal one-step output."""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "benchmark/one_step_records.csv"
OUTPUT = ROOT / "benchmark/natural_event_rollout_records.csv"
MARKER = ROOT / "benchmark/formal_attempt.json"


def truth(value: str) -> bool:
    return str(value).lower() == "true"


def main() -> None:
    rows = list(csv.DictReader(SOURCE.open(encoding="utf-8")))
    states = {}
    for row in rows:
        key = (row["environment"], row["state_id"])
        states.setdefault(key, any(truth(row.get(field, "")) for field in ("segment_incremental_activation", "backup_incremental_activation", "directional_incremental_rescue")))
    events = [key for key, active in states.items() if active]
    if events:
        raise SystemExit("NATURAL_EVENTS_REQUIRE_FROZEN_ROLLOUT_EXECUTION")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerow(["environment", "state_id", "event_type", "step", "positive_progress", "terminal_reason", "represented_violation", "reference_collision", "selected_candidate", "deadline_miss"])
    marker = json.loads(MARKER.read_text(encoding="utf-8"))
    if marker["status"] != "FORMAL_ONE_STEP_COMPLETED" or marker["formal_attempt_count"] != 1:
        raise SystemExit("FORMAL_MARKER_BOUNDARY_VIOLATION")
    marker.update({"status": "FORMAL_ATTEMPT_COMPLETED", "natural_incremental_event_count": 0, "natural_rollout_episode_count": 0, "logical_rollout_step_count": 0})
    temporary = MARKER.with_suffix(".tmp")
    temporary.write_text(json.dumps(marker, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, MARKER)
    print("PASS_NO_NATURAL_INCREMENTAL_EVENTS_NO_ROLLOUT_STARTED")


if __name__ == "__main__":
    main()
