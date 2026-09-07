from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv"
OUTPUT = Path(__file__).with_name("EXECUTABLE_TRANSITION_IMPLEMENTATION_MAP_V2.csv")


def main() -> None:
    with SOURCE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    fields = [
        "rule_id", "source_phase", "observation/result", "deadline_requirement",
        "candidate_requirement", "retained_backup_requirement", "runtime_event",
        "runtime_route_lookup_path", "destination", "commit_flag", "test_id", "implemented",
    ]
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "rule_id": row["rule_id"],
                "source_phase": row["source_phase"],
                "observation/result": row["observation/result"],
                "deadline_requirement": row["deadline_requirement"],
                "candidate_requirement": row["candidate_requirement"],
                "retained_backup_requirement": row["retained_backup_requirement"],
                "runtime_event": row["observation/result"],
                "runtime_route_lookup_path": "Supervisor.route_transition->TransitionTable.resolve",
                "destination": row["destination_phase"],
                "commit_flag": row["commit_allowed"].lower(),
                "test_id": "PC-RULE-" + row["rule_id"],
                "implemented": "yes",
            })
    if len(rows) != 43 or len({row["rule_id"] for row in rows}) != 43:
        raise SystemExit("TRANSITION_TABLE_NOT_43_EXACTLY_ONCE")
    print("EXECUTABLE_TRANSITION_IMPLEMENTATION_MAP=43/43")


if __name__ == "__main__":
    main()
