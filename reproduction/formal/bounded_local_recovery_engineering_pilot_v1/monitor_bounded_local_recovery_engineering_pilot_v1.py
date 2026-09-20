#!/usr/bin/env python3
"""Read-only human-readable percentage monitor; --json is machine-readable."""
from __future__ import annotations

import argparse, json, subprocess
from pathlib import Path
from validate_bounded_local_recovery_engineering_pilot_v1 import PROTOCOL, read

BAR_WIDTH = 30

def bar(done: int, total: int) -> str:
    ratio = 0.0 if total <= 0 else max(0.0, min(1.0, done / total))
    filled = int(ratio * BAR_WIDTH + 0.5)
    return "[" + "█" * filled + "-" * (BAR_WIDTH - filled) + "]"

def inspect() -> dict:
    protocol = read(PROTOCOL)
    root = Path(protocol["future_result_root"])
    trials = protocol["cohort"]["trial_order"]
    per_trial, completed, current = [], [], None
    keys = ("recovery_eligibility","recovery_scans","recovery_attempts","recovery_selected",
            "recovery_plant_commit","recovery_l2_enter","recovery_l2_result","recovery_l2_pass",
            "recovery_l2_fail","recovery_l2_unknown","recovery_l2_exception",
            "canonical_l2_rewrite_exceptions","identity_mismatches","hard_violations",
            "hard_unknown","process_failures")
    counts = {key: 0 for key in keys}
    for trial in trials:
        raw = root / "raw" / f"trial_{trial}"
        observations = raw / "recovery_cycle_observations.jsonl"
        cycles = 0
        if observations.is_file():
            with observations.open(encoding="utf-8") as stream:
                for line in stream:
                    row = json.loads(line)
                    cycles += 1
                    attempts = row.get("recovery_attempts", [])
                    counts["recovery_attempts"] += sum("candidate_id" in a for a in attempts)
                    scans = {a.get("recovery_scan_id") for a in attempts if a.get("recovery_scan_id")}
                    counts["recovery_scans"] += len(scans)
                    counts["recovery_eligibility"] += bool(attempts)
                    selected = any(a.get("supervisor_selected") is True for a in attempts)
                    counts["recovery_selected"] += selected
                    counts["recovery_plant_commit"] += bool(row.get("committed") and selected)
                    for attempt in attempts:
                        entered = attempt.get("C0_status") == "PASS"
                        status = attempt.get("L2_status")
                        counts["recovery_l2_enter"] += entered
                        counts["recovery_l2_result"] += status in ("PASS","FAIL","UNKNOWN")
                        counts["recovery_l2_pass"] += status == "PASS"
                        counts["recovery_l2_fail"] += status == "FAIL"
                        counts["recovery_l2_unknown"] += status == "UNKNOWN"
                        counts["recovery_l2_exception"] += attempt.get("exception_stage") == "L2"
                    counts["identity_mismatches"] += bool(row.get("selected_action_identity") and
                        row.get("executed_action_identity") and
                        row["selected_action_identity"] != row["executed_action_identity"])
        done = (root / f"trial_{trial}_complete.json").is_file()
        if done:
            completed.append(trial)
            state = "DONE"
        elif raw.exists() and current is None:
            current, state = trial, "RUNNING"
        else:
            state = "PENDING"
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
            counts["canonical_l2_rewrite_exceptions"] += stderr.read_text(
                encoding="utf-8", errors="replace").count("CANONICAL_EVIDENCE_REWRITE_FORBIDDEN:canonical_l2_")
        per_trial.append({"trial_id":trial,"state":state,"cycles":cycles,"maximum_cycles":500,
                          "percent":100.0*min(cycles,500)/500.0})
    tmux_active = subprocess.run(["tmux","has-session","-t",protocol["future_tmux_session"]],
                                 capture_output=True).returncode == 0
    batch = "BATCH COMPLETE" if (root / "BATCH_COMPLETE.json").is_file() else (
            "BATCH STOP" if (root / "BATCH_STOP.json").is_file() else "BATCH RUNNING" if tmux_active else "BATCH NOT STARTED")
    observed = sum(row["cycles"] for row in per_trial)
    return {"schema":"BOUNDED_RECOVERY_ENGINEERING_PILOT_READ_ONLY_PROGRESS_V1",
            "batch_status":batch,"tmux_active":tmux_active,"current_trial":current,
            "completed_trials":completed,"observed_cycles":observed,"maximum_planned_cycles":6000,
            "overall_percent":100.0*min(observed,6000)/6000.0,"per_trial":per_trial,"counts":counts,
            "scientific_decision":"NOT_COMPUTED_BY_MONITOR"}

def render(data: dict) -> str:
    current = "none" if data["current_trial"] is None else str(data["current_trial"])
    lines = ["## BOUNDED LOCAL RECOVERY — ENGINEERING PILOT", "",
             f"TMUX      : {'ACTIVE' if data['tmux_active'] else 'INACTIVE'}",
             f"CURRENT   : trial {current}", "",
             f"OVERALL   : {data['observed_cycles']} / {data['maximum_planned_cycles']}   {data['overall_percent']:.2f}%",
             bar(data["observed_cycles"], data["maximum_planned_cycles"]), ""]
    for row in data["per_trial"]:
        lines += [f"TRIAL {row['trial_id']:02d}  {row['state']:<7}  {row['cycles']} / {row['maximum_cycles']}   {row['percent']:.2f}%",
                  bar(row["cycles"], row["maximum_cycles"]), ""]
    c=data["counts"]
    lines += ["RECOVERY",f"eligibility : {c['recovery_eligibility']}",f"scans       : {c['recovery_scans']}",
              f"attempts    : {c['recovery_attempts']}",f"selected    : {c['recovery_selected']}",
              f"PlantCommit : {c['recovery_plant_commit']}","","RECOVERY L2",
              f"enter       : {c['recovery_l2_enter']}",f"result      : {c['recovery_l2_result']}",
              f"PASS        : {c['recovery_l2_pass']}",f"FAIL        : {c['recovery_l2_fail']}",
              f"UNKNOWN     : {c['recovery_l2_unknown']}",f"exception   : {c['recovery_l2_exception']}","","HEALTH",
              f"canonical rewrite exception : {c['canonical_l2_rewrite_exceptions']}",
              f"identity mismatch            : {c['identity_mismatches']}",
              f"hard violations              : {c['hard_violations']}",
              f"hard unknown                 : {c['hard_unknown']}",
              f"process failures             : {c['process_failures']}","----------------------------------",data["batch_status"]]
    return "\n".join(lines)

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json",action="store_true")
    args=parser.parse_args()
    data=inspect()
    print(json.dumps(data,sort_keys=True) if args.json else render(data))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
