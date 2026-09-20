#!/usr/bin/env python3
"""Read-only human-readable percentage monitor; --json is machine-readable."""
from __future__ import annotations

import argparse, json, subprocess
from pathlib import Path
from validate_post_repair_v3_bounded_recovery_paired_validation_v1 import PROTOCOL, read

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
            summary_path = raw / "trial_summary.json"
            if summary_path.is_file() and read(summary_path).get("termination_reason") == "ASSURANCE_BOUNDARY":
                state = "DONE-BOUNDARY"
            else:
                state = "DONE-MAX"
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
    maximum = len(trials) * 500
    return {"schema":"POST_REPAIR_V3_BOUNDED_RECOVERY_FORMAL85_READ_ONLY_PROGRESS_V1",
            "batch_status":batch,"tmux_active":tmux_active,"current_trial":current,
            "completed_trials":completed,"observed_cycles":observed,"maximum_planned_cycles":maximum,
            "cycle_budget_percent":100.0*min(observed,maximum)/maximum,"per_trial":per_trial,"counts":counts,
            "scientific_decision":"NOT_COMPUTED_BY_MONITOR"}

def render(data: dict) -> str:
    current = "none" if data["current_trial"] is None else str(data["current_trial"])
    current_row = next((row for row in data["per_trial"] if row["trial_id"] == data["current_trial"]), None)
    done_boundary = sum(row["state"] == "DONE-BOUNDARY" for row in data["per_trial"])
    done_max = sum(row["state"] in ("DONE", "DONE-MAX") for row in data["per_trial"])
    pending = sum(row["state"] == "PENDING" for row in data["per_trial"])
    complete = len(data["completed_trials"])
    total = len(data["per_trial"])
    lines = ["================================================================",
             " POST-REPAIR V3 + BOUNDED RECOVERY — FORMAL85",
             "================================================================", "",
             f"TMUX      : {'ACTIVE' if data['tmux_active'] else 'INACTIVE'}",
             f"CURRENT   : trial {current}", "",
             f"TRIAL COMPLETION : {complete} / {total}   {100.0*complete/total:.2f}%",
             bar(complete, total), "",
             f"CYCLE BUDGET     : {data['observed_cycles']} / {data['maximum_planned_cycles']}   {data['cycle_budget_percent']:.2f}%",
             bar(data["observed_cycles"], data["maximum_planned_cycles"]), ""]
    if current_row:
        lines += [f"CURRENT TRIAL    : {current_row['cycles']} / 500   {current_row['percent']:.2f}%",
                  bar(current_row["cycles"], 500), ""]
    lines += ["COMPLETED", f"  DONE-MAX       : {done_max}", f"  DONE-BOUNDARY  : {done_boundary}",
              f"  RUNNING        : {sum(row['state'] == 'RUNNING' for row in data['per_trial'])}",
              f"  PENDING        : {pending}", ""]
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
              f"process failures             : {c['process_failures']}",
              "================================================================",data["batch_status"]]
    return "\n".join(lines)

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json",action="store_true")
    parser.add_argument("--all-trials",action="store_true")
    args=parser.parse_args()
    data=inspect()
    if args.all_trials and not args.json:
        print(render(data))
        for row in data["per_trial"]:
            print(f"TRIAL {row['trial_id']:02d} {row['state']:<13} {row['cycles']:3d}/500 {row['percent']:6.2f}% {bar(row['cycles'],500)}")
        return 0
    print(json.dumps(data,sort_keys=True) if args.json else render(data))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
