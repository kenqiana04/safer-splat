#!/usr/bin/env python3
"""Read-only compact monitor for a future bounded recovery Retry2 run."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess

from validate_bounded_local_recovery_smoke_retry2_v1 import PROTOCOL, read


def inspect() -> dict:
    p = read(PROTOCOL)
    root = Path(p["future_result_root"])
    session = p["future_tmux_session"]
    tmux = subprocess.run(["tmux", "has-session", "-t", session], capture_output=True).returncode == 0
    counts = {key: 0 for key in ("cycles", "recovery_eligibility", "recovery_scans", "recovery_attempts",
             "recovery_selected", "recovery_plant_commit", "primary", "backup", "terminal", "boundary",
             "recovery_l2_enter", "recovery_l2_result", "recovery_l2_pass", "recovery_l2_fail",
             "recovery_l2_unknown", "recovery_l2_exception", "canonical_l2_rewrite_exceptions",
             "hard_violations", "hard_unknown", "identity_mismatches", "process_failures")}
    completed = []
    current = None
    if root.is_dir():
        for trial in p["cohort"]["trial_order"]:
            raw = root / "raw" / f"trial_{trial}"
            if (root / f"trial_{trial}_complete.json").is_file():
                completed.append(trial)
            elif raw.exists() and current is None:
                current = trial
            observations = raw / "recovery_cycle_observations.jsonl"
            if observations.is_file():
                with observations.open(encoding="utf-8") as stream:
                    for line in stream:
                        row = json.loads(line)
                        counts["cycles"] += 1
                        attempts = row.get("recovery_attempts", [])
                        counts["recovery_attempts"] += sum("candidate_id" in a for a in attempts)
                        counts["recovery_scans"] += len({a.get("recovery_scan_id") for a in attempts if a.get("recovery_scan_id")})
                        counts["recovery_eligibility"] += bool(attempts)
                        counts["recovery_selected"] += sum(a.get("supervisor_selected") is True for a in attempts)
                        counts["recovery_plant_commit"] += bool(row.get("committed") and any(a.get("supervisor_selected") for a in attempts))
                        for attempt in attempts:
                            entered = attempt.get("C0_status") == "PASS"
                            status = attempt.get("L2_status")
                            counts["recovery_l2_enter"] += entered
                            counts["recovery_l2_result"] += status in ("PASS", "FAIL", "UNKNOWN")
                            counts["recovery_l2_pass"] += status == "PASS"
                            counts["recovery_l2_fail"] += status == "FAIL"
                            counts["recovery_l2_unknown"] += status == "UNKNOWN"
                            counts["recovery_l2_exception"] += attempt.get("exception_stage") == "L2"
                        role = str(row.get("action_role") or "").upper()
                        counts["primary"] += "PRIMARY" in role
                        counts["backup"] += "BACKUP" in role
                        counts["terminal"] += "TERMINAL" in role
                        counts["boundary"] += bool(row.get("boundary"))
                        counts["identity_mismatches"] += bool(row.get("selected_action_identity") and row.get("executed_action_identity") and row["selected_action_identity"] != row["executed_action_identity"])
            summary = raw / "trial_summary.json"
            if summary.is_file():
                data = read(summary)
                counts["hard_violations"] += int(data.get("hard_violation_segments", 0))
                counts["hard_unknown"] += int(data.get("hard_unknown_segments", 0))
            exit_file = raw / "process_exit_code.txt"
            if exit_file.is_file():
                counts["process_failures"] += int(exit_file.read_text(encoding="utf-8").strip() != "0")
            stderr = raw / "stderr.log"
            if stderr.is_file():
                text = stderr.read_text(encoding="utf-8", errors="replace")
                counts["canonical_l2_rewrite_exceptions"] += text.count(
                    "CANONICAL_EVIDENCE_REWRITE_FORBIDDEN:canonical_l2_"
                )
        counts["process_failures"] += int((root / "BATCH_STOP.json").is_file())
    return {"schema": "BOUNDED_RECOVERY_SMOKE_RETRY2_READ_ONLY_PROGRESS_V1", "tmux_session": session,
            "tmux_active": tmux, "current_trial": current, "completed_trials": completed,
            "completed_trial_count": len(completed), "planned_trial_count": 3,
            "observed_cycles": counts.pop("cycles"), "maximum_planned_cycles": 1500,
            "counts": counts, "scientific_decision": "NOT_COMPUTED_BY_MONITOR"}


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    print(json.dumps(inspect(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
