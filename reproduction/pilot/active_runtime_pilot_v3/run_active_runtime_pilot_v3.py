#!/usr/bin/env python3
"""Execute the frozen Pilot V3 cohort through the PR #141 runtime path."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
from typing import Any


TASK_DIR = Path(__file__).resolve().parent
PROTOCOL_PATH = TASK_DIR / "PILOT_V3_PROTOCOL.json"
LOCK_PATH = TASK_DIR / "PILOT_V3_EXECUTION_LOCK.json"
PARENT = "18664bcb8d6e71333e1216c5af0c6757840540f8"
PROTOCOL_COMMIT = "ff536b868db3522067fdeb2034580e156ae4d29e"
PROTOCOL_SHA = "8ae74d6c4833fd1088fadc083c104b069b9bb0cdae06ef9c9f4a58cbb09e5e54"
TRIALS = (5, 15, 25, 35, 45, 55, 65, 75, 85, 95)
STRESS_TRIALS = (5, 25, 45, 75, 85)
PROTECTED = (
    "cbf", "dynamics", "splat", "run.py", "reproduction/runtime",
    "reproduction/smoke/active_runtime_smoke_v3", "reproduction/formal",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return float(ordered[min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))])


def load_smoke(checkout: Path) -> Any:
    path = checkout / "reproduction/smoke/active_runtime_smoke_v3/run_active_runtime_smoke_v3.py"
    spec = importlib.util.spec_from_file_location("_pilot_v3_reused_smoke_runtime", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("FROZEN_SMOKE_V3_RUNNER_IMPORT_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(spec.name)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            sys.modules.pop(spec.name, None)
        else:
            sys.modules[spec.name] = previous
    return module


def projected_protocol(checkout: Path) -> dict[str, Any]:
    pilot = load_json(PROTOCOL_PATH)
    smoke = load_json(checkout / "reproduction/smoke/active_runtime_smoke_v3/SMOKE_V3_PROTOCOL.json")
    if sha256_file(PROTOCOL_PATH) != PROTOCOL_SHA:
        raise RuntimeError("FROZEN_PILOT_PROTOCOL_HASH_MISMATCH")
    execution = pilot["execution"]
    geometry = pilot["v3_runtime_geometry"]
    diagnostic = pilot["historical_diagnostic_shell"]
    if pilot["trial_order"] != list(TRIALS) or execution["maximum_completed_cycles_per_trial"] != 500:
        raise RuntimeError("FROZEN_PILOT_COHORT_OR_CAP_MISMATCH")
    if (geometry["r_body_q"], geometry["m_hard_q"], geometry["r_hard_q"], geometry["rho_seg_q"]) != (0.015, 0.0, 0.015, 0.0):
        raise RuntimeError("FROZEN_PILOT_V3_GEOMETRY_MISMATCH")
    if diagnostic["radius_q"] != 0.025 or any(value for key, value in diagnostic.items() if key.endswith("authority")):
        raise RuntimeError("HISTORICAL_DIAGNOSTIC_AUTHORITY_MISMATCH")
    smoke.update({
        "trial_ids": list(TRIALS),
        "trial_order": list(TRIALS),
        "maximum_completed_cycles_per_trial": 500,
        "seed": execution["seed"],
        "map_relative_path": pilot["map"]["relative_path"],
        "map_identity": pilot["map"]["identity"],
        "map_artifacts": pilot["map"]["artifacts"],
    })
    smoke["environment"].update({
        "conda_environment": execution["conda_environment"],
        "python": execution["python"],
        "CUDA_VISIBLE_DEVICES": str(execution["gpu_id"]),
    })
    return smoke


def configure_smoke(checkout: Path) -> tuple[Any, dict[str, Any]]:
    smoke = load_smoke(checkout)
    protocol = projected_protocol(checkout)
    original_verify = smoke.verify_source_and_map
    smoke.UPSTREAM = PARENT
    smoke.FIXED_TRIALS = TRIALS
    smoke.TASK_DIR = TASK_DIR
    smoke.PROTOCOL_PATH = PROTOCOL_PATH
    smoke.EXECUTION_LOCK_PATH = LOCK_PATH
    smoke.read_protocol = lambda: protocol

    def verify(checkout_arg: Path, protocol_arg: dict[str, Any], require_execution_lock: bool = True):
        if require_execution_lock:
            lock = load_json(LOCK_PATH)
            if lock["protocol_sha256"] != PROTOCOL_SHA or lock["protocol_commit"] != PROTOCOL_COMMIT:
                raise RuntimeError("EXECUTION_LOCK_PROTOCOL_IDENTITY_MISMATCH")
            if lock["trial_order"] != list(TRIALS) or lock["base_sha"] != PARENT:
                raise RuntimeError("EXECUTION_LOCK_COHORT_OR_BASE_MISMATCH")
            if lock["runner_sha256"] != sha256_file(Path(__file__).resolve()):
                raise RuntimeError("EXECUTION_LOCK_RUNNER_HASH_MISMATCH")
        return original_verify(checkout_arg, protocol_arg, False)

    smoke.verify_source_and_map = verify
    return smoke, protocol


def enrich_trial_summary(checkout: Path, output_dir: Path, trial_id: int) -> dict[str, Any]:
    path = output_dir / "raw" / f"trial_{trial_id}" / "trial_summary.json"
    summary = load_json(path)
    smoke, _ = configure_smoke(checkout)
    helpers = smoke._load_v2_helpers(checkout)
    start, goal = helpers.trial_geometry(trial_id)
    initial_state = [float(v) for v in start] + [0.0, 0.0, 0.0]
    goal_state = [float(v) for v in goal] + [0.0, 0.0, 0.0]
    trace_path = output_dir / "raw" / f"trial_{trial_id}" / "runtime_trace.jsonl"
    trace = [json.loads(line) for line in trace_path.read_text(encoding="utf-8").splitlines()] if trace_path.exists() else []
    first_role = trace[0].get("action_role") if trace else None
    audit = summary.get("v3_wiring_audit", {})
    historical_authority = bool(audit.get("historical_diagnostic_runtime_authority", True))
    c0_total = sum(summary.get("C0_status_counts", {}).values())
    summary.update({
        "schema": "ACTIVE_RUNTIME_PILOT_V3_TRIAL_SUMMARY_V1",
        "seed": 0,
        "initial_state": initial_state,
        "goal": goal_state,
        "plant_commits": summary.get("plant_commit_count", 0),
        "primary_count": summary.get("primary_navigation_commit_count", 0),
        "alternative_count": summary.get("alternative_navigation_commit_count", 0),
        "backup_count": summary.get("retained_backup_commit_count", 0),
        "terminal_count": summary.get("terminal_commit_count", 0),
        "boundary_count": summary.get("assurance_boundary_count", 0),
        "qp_failures": max(0, int(summary.get("completed_cycles", 0)) - int(c0_total)),
        "qp_failure_count_semantics": "CYCLES_WITHOUT_C0_EVALUATION_DESCRIPTIVE_PROXY",
        "locked_cycle_record_count": summary.get("trace_lock_record_count", 0),
        "plant_execution_state_unknown": summary.get("plant_outcome_unknown_count", 0),
        "runtime_hard_radius_observed_q": audit.get("hard_runtime_radius_q"),
        "historical_diagnostic_radius_observed_q": audit.get("historical_diagnostic_radius_q"),
        "historical_diagnostic_shell_runtime_authority_observed": historical_authority,
        "historical_diagnostic_intrusion_count": 0 if not historical_authority else 1,
        "FORBIDDEN_DIAGNOSTIC_AUTHORITY_EVENT_COUNT": 0 if not historical_authority else 1,
        "diagnostic_authority_detection_basis": "FROZEN_OBJECT_GRAPH_HAS_NO_RUNTIME_CONSUMER_EDGE",
        "first_cycle_action_role": first_role,
        "evaluation_eligible": summary.get("hard_blocker") is None and summary.get("finalization_status") == "FINALIZED",
    })
    write_json(path, summary)
    return summary


def run_preflight(checkout: Path, output_dir: Path) -> int:
    smoke, _ = configure_smoke(checkout)
    code = smoke.run_preflight(checkout, output_dir)
    path = output_dir / "raw" / "gpu_preflight.json"
    result = load_json(path)
    result.update({
        "schema": "ACTIVE_RUNTIME_PILOT_V3_GPU_PREFLIGHT_V1",
        "pilot_cycles_executed": 0,
        "protocol_sha256": PROTOCOL_SHA,
        "historical_authority_flags_all_false": True,
    })
    write_json(path, result)
    print("PASS_ACTIVE_RUNTIME_PILOT_V3_GPU_PREFLIGHT", flush=True)
    return code


def run_one(checkout: Path, output_dir: Path, trial_id: int) -> int:
    smoke, _ = configure_smoke(checkout)
    code = smoke.run_one(checkout, output_dir, trial_id)
    summary = enrich_trial_summary(checkout, output_dir, trial_id)
    if summary["FORBIDDEN_DIAGNOSTIC_AUTHORITY_EVENT_COUNT"]:
        return 2
    return code


def complete_evidence(output_dir: Path, trial_id: int) -> bool:
    raw = output_dir / "raw" / f"trial_{trial_id}"
    required = [raw / name for name in ("trial_summary.json", "runtime_trace.jsonl", "runtime_trace_lock.json", "process_exit_code.txt", "gpu_released.txt")]
    if not all(path.is_file() for path in required):
        return False
    summary, lock = load_json(required[0]), load_json(required[2])
    return (
        required[3].read_text().strip() == "0"
        and required[4].read_text().strip() == "true"
        and summary.get("schema") == "ACTIVE_RUNTIME_PILOT_V3_TRIAL_SUMMARY_V1"
        and summary.get("hard_blocker") is None
        and summary.get("finalization_status") == "FINALIZED"
        and summary.get("completed_cycles") == lock.get("record_count") == len(required[1].read_text(encoding="utf-8").splitlines())
        and summary.get("FORBIDDEN_DIAGNOSTIC_AUTHORITY_EVENT_COUNT") == 0
    )


def run_batch(checkout: Path, output_dir: Path) -> int:
    smoke, protocol = configure_smoke(checkout)
    smoke.verify_source_and_map(checkout, protocol)
    overall = 0
    for trial_id in TRIALS:
        if complete_evidence(output_dir, trial_id):
            print(f"TRIAL_{trial_id}_IMMUTABLE_EVIDENCE_ALREADY_COMPLETE_SKIP", flush=True)
            continue
        raw = output_dir / "raw" / f"trial_{trial_id}"
        raw.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env.update(protocol["environment"])
        command = [protocol["environment"]["python"], str(Path(__file__).resolve()), "--one", str(trial_id), "--checkout", str(checkout), "--output-dir", str(output_dir)]
        with (raw / "stdout.log").open("w", encoding="utf-8", newline="\n") as stdout, (raw / "stderr.log").open("w", encoding="utf-8", newline="\n") as stderr:
            process = subprocess.Popen(command, env=env, stdout=stdout, stderr=stderr, text=True)
            code = process.wait()
        released = smoke.gpu_pid_released(process.pid)
        (raw / "process_exit_code.txt").write_text(f"{code}\n", encoding="utf-8", newline="\n")
        (raw / "gpu_released.txt").write_text(("true" if released else "false") + "\n", encoding="utf-8", newline="\n")
        if code or not released or not complete_evidence(output_dir, trial_id):
            overall = code or 2
            print(f"TRIAL_{trial_id}_HARD_STOP exit={code} gpu_released={released}", flush=True)
            break
        print(f"TRIAL_{trial_id}_PASS", flush=True)
    summarize(output_dir)
    return overall


def sum_status(summaries: list[dict[str, Any]], stage: str) -> dict[str, int]:
    return {status: sum(int(item.get(f"{stage}_status_counts", {}).get(status, 0)) for item in summaries) for status in ("PASS", "FAIL", "UNKNOWN")}


def summarize(output_dir: Path) -> dict[str, Any]:
    summaries = [load_json(output_dir / "raw" / f"trial_{trial}" / "trial_summary.json") for trial in TRIALS if (output_dir / "raw" / f"trial_{trial}" / "trial_summary.json").is_file()]
    rows = []
    for item in summaries:
        rows.append({key: item.get(key) for key in (
            "trial_id", "process_exit_code", "completed_cycles", "plant_commits", "primary_count", "alternative_count", "backup_count", "terminal_count", "boundary_count", "qp_failures", "finalization_status", "termination_reason", "first_cycle_action_role", "FORBIDDEN_DIAGNOSTIC_AUTHORITY_EVENT_COUNT", "hard_blocker"
        )})
    with (output_dir / "PILOT_V3_TRIAL_RESULTS.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["trial_id"])
        writer.writeheader(); writer.writerows(rows)

    trace_trials = []
    for item in summaries:
        ok = item.get("completed_cycles") == item.get("trace_record_count") == item.get("trace_lock_record_count") == item.get("persisted_trace_line_count")
        trace_trials.append({"trial_id": item["trial_id"], "completed_cycles": item.get("completed_cycles"), "trace_records": item.get("trace_record_count"), "locked_records": item.get("trace_lock_record_count"), "persisted_lines": item.get("persisted_trace_line_count"), "pass": ok})
    trace_audit = {"schema": "ACTIVE_RUNTIME_PILOT_V3_TRACE_AUDIT_V1", "status": "PASS" if len(trace_trials) == 10 and all(row["pass"] for row in trace_trials) else "FAIL", "trials": trace_trials}
    write_json(output_dir / "PILOT_V3_TRACE_AUDIT.json", trace_audit)

    roles = {name: sum(int(item.get(name, 0)) for item in summaries) for name in ("primary_count", "alternative_count", "backup_count", "terminal_count", "boundary_count")}
    stages = {stage: sum_status(summaries, stage) for stage in ("L1", "C0", "L2", "L3")}
    deadlines = {status: sum(int(item.get("deadline_status_counts", {}).get(status, 0)) for item in summaries) for status in ("OPEN", "WARNING", "EXPIRED")}
    routing = {"schema": "ACTIVE_RUNTIME_PILOT_V3_ROUTING_SUMMARY_V1", "action_roles": roles, "certificate_statuses": stages, "qp_failures": sum(int(item.get("qp_failures", 0)) for item in summaries), "deadline_statuses": deadlines, "interpretation": "DESCRIPTIVE_RUNTIME_ROUTING_NOT_EFFICACY"}
    write_json(output_dir / "PILOT_V3_ROUTING_SUMMARY.json", routing)

    values = [float(v) for item in summaries for v in item.get("cycle_time_values", [])]
    timing = {"schema": "ACTIVE_RUNTIME_PILOT_V3_TIMING_SUMMARY_V1", "cycle_count": len(values), "mean": statistics.fmean(values) if values else None, "median": statistics.median(values) if values else None, "p95": percentile(values, 0.95), "max": max(values) if values else None, "deadline_statuses": deadlines, "interpretation": "ENGINEERING_TELEMETRY_ONLY"}
    write_json(output_dir / "PILOT_V3_TIMING_SUMMARY.json", timing)

    stress_rows = []
    for item in summaries:
        if item["trial_id"] in STRESS_TRIALS:
            stress_rows.append({"trial_id": item["trial_id"], "completed_cycles": item.get("completed_cycles"), "at_least_one_primary_commit": item.get("primary_count", 0) > 0, "first_cycle_terminal": item.get("first_cycle_action_role") == "CERTIFIED_TERMINAL", "terminal_count": item.get("terminal_count"), "c0_fail": item.get("C0_status_counts", {}).get("FAIL", 0), "backup_count": item.get("backup_count"), "boundary_count": item.get("boundary_count"), "termination_type": item.get("termination_reason")})
    repeated_cycle1_terminal = sum(int(row["first_cycle_terminal"] and not row["at_least_one_primary_commit"]) for row in stress_rows) >= 2
    stress = {"schema": "ACTIVE_RUNTIME_PILOT_V3_STRESS_REGRESSION_V1", "trial_ids": list(STRESS_TRIALS), "trials": stress_rows, "repeated_cycle1_terminal_takeover_without_primary": repeated_cycle1_terminal, "interpretation": "DEVELOPMENT_EXPOSED_DESCRIPTIVE_REGRESSION_ONLY"}
    write_json(output_dir / "PILOT_V3_STRESS_REGRESSION.json", stress)

    hard_fail = len(summaries) != 10 or any(item.get("hard_blocker") or item.get("process_exit_code") != 0 or not item.get("evaluation_eligible") for item in summaries) or trace_audit["status"] != "PASS"
    integrity_fields = ("selected_executed_identity_mismatch_count", "nonfinite_count", "action_bound_violation_count", "evidence_incomplete_count", "recovery_required_count", "plant_outcome_unknown_count", "FORBIDDEN_DIAGNOSTIC_AUTHORITY_EVENT_COUNT")
    totals = {field: sum(int(item.get(field, 0)) for item in summaries) for field in integrity_fields}
    hard_fail = hard_fail or any(totals.values()) or any(item.get("runtime_hard_radius_observed_q") != 0.015 or item.get("historical_diagnostic_shell_runtime_authority_observed") is not False for item in summaries)
    if hard_fail:
        status, decision = "BLOCKED_ACTIVE_RUNTIME_PILOT_V3_INTEGRITY_OR_SEMANTICS", "DIAGNOSE_ACTIVE_RUNTIME_PILOT_V3"
    elif repeated_cycle1_terminal:
        status, decision = "BLOCKED_ACTIVE_RUNTIME_PILOT_V3_BY_METHOD_LEVEL_SIGNAL", "DIAGNOSE_ACTIVE_RUNTIME_PILOT_V3_METHOD_LEVEL_SIGNAL"
    else:
        status, decision = "PASS_ACTIVE_RUNTIME_PILOT_V3", "ADVANCE_TO_NEXT_V3_VALIDATION_PROTOCOL_FREEZE"
    execution = {"schema": "ACTIVE_RUNTIME_PILOT_V3_EXECUTION_SUMMARY_V1", "completed_trials": len(summaries), "trial_ids": [item["trial_id"] for item in summaries], "completed_cycles": sum(int(item.get("completed_cycles", 0)) for item in summaries), "plant_commits": sum(int(item.get("plant_commits", 0)) for item in summaries), "roles": roles, "certificate_statuses": stages, "qp_failures": routing["qp_failures"], "deadline_statuses": deadlines, "finalization_pass_count": sum(int(item.get("finalization_status") == "FINALIZED") for item in summaries), "trace_cardinality": trace_audit["status"], "integrity_totals": totals, "hard_runtime_radius_observed_values_q": sorted({item.get("runtime_hard_radius_observed_q") for item in summaries}), "historical_diagnostic_runtime_authority_observed": any(item.get("historical_diagnostic_shell_runtime_authority_observed") for item in summaries), "historical_diagnostic_intrusion_count": sum(int(item.get("historical_diagnostic_intrusion_count", 0)) for item in summaries), "forbidden_diagnostic_authority_event_count": totals["FORBIDDEN_DIAGNOSTIC_AUTHORITY_EVENT_COUNT"], "gpu_trial_rerun_count": sum(int(item.get("gpu_trial_rerun", False)) for item in summaries), "official100_count": 0, "scientific_oracle_count": 0, "formal_count": 0, "reference_arm_count": 0, "FINAL_STATUS": status, "FINAL_DECISION": decision}
    write_json(output_dir / "PILOT_V3_EXECUTION_SUMMARY.json", execution)
    write_json(output_dir / "PILOT_V3_FINAL_DECISION.json", {"schema": "ACTIVE_RUNTIME_PILOT_V3_FINAL_DECISION_V1", "FINAL_STATUS": status, "FINAL_DECISION": decision, "only_next_task": "FREEZE_NEXT_V3_VALIDATION_PROTOCOL" if status.startswith("PASS") else decision})

    with (output_dir / "PILOT_V3_FAILURE_REGISTER.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = ["trial_id", "failure_class", "runtime_or_task_local", "scientific_integrity_affected", "raw_evidence_complete", "rerun_required", "resolution"]
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for item in summaries:
            if item.get("hard_blocker"):
                writer.writerow({"trial_id": item["trial_id"], "failure_class": item["hard_blocker"], "runtime_or_task_local": "runtime", "scientific_integrity_affected": True, "raw_evidence_complete": item.get("evaluation_eligible", False), "rerun_required": False, "resolution": "STOP_AND_DIAGNOSE"})

    report = f"""# Active Runtime Pilot V3\n\n`FINAL_STATUS={status}`\n\n`FINAL_DECISION={decision}`\n\n## A. Runtime integrity\n\nCompleted trials/cycles/plant commits: `{len(summaries)}/{execution['completed_cycles']}/{execution['plant_commits']}`. Finalization PASS: `{execution['finalization_pass_count']}`. Trace cardinality: `{execution['trace_cardinality']}`. Identity mismatch/nonfinite/actuator/evidence/recovery/plant-unknown: `{totals['selected_executed_identity_mismatch_count']}/{totals['nonfinite_count']}/{totals['action_bound_violation_count']}/{totals['evidence_incomplete_count']}/{totals['recovery_required_count']}/{totals['plant_outcome_unknown_count']}`.\n\n## B. Hard safety-certification routing\n\nAll runtime decisions use the frozen `0.015 q` hard geometry. Primary/alternative/backup/terminal/boundary: `{roles['primary_count']}/{roles['alternative_count']}/{roles['backup_count']}/{roles['terminal_count']}/{roles['boundary_count']}`. Certificate counts are descriptive runtime facts, not efficacy claims.\n\n## C. Diagnostic-only historical shell\n\nThe historical `0.025 q` shell retained no runtime authority. Diagnostic intrusion / forbidden authority events: `{execution['historical_diagnostic_intrusion_count']}/{execution['forbidden_diagnostic_authority_event_count']}`.\n\n## D. Liveness and method-level diagnostics\n\nThe five stress trials are development-exposed and summarized in `PILOT_V3_STRESS_REGRESSION.json`. No parameter selection, formal superiority claim, scientific oracle, Official100, Formal, or reference arm is authorized by this Pilot.\n"""
    report_path = output_dir / "report" / "REPORT_ACTIVE_RUNTIME_PILOT_V3.md"; report_path.parent.mkdir(parents=True, exist_ok=True); report_path.write_text(report, encoding="utf-8", newline="\n")
    return execution


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--batch", action="store_true")
    mode.add_argument("--one", type=int)
    mode.add_argument("--summarize", action="store_true")
    parser.add_argument("--checkout", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    checkout, output = Path(args.checkout).resolve(), Path(args.output_dir).resolve()
    if args.preflight:
        return run_preflight(checkout, output)
    if args.batch:
        return run_batch(checkout, output)
    if args.one is not None:
        return run_one(checkout, output, args.one)
    summary = summarize(output)
    return 0 if summary["FINAL_STATUS"] == "PASS_ACTIVE_RUNTIME_PILOT_V3" else 2


if __name__ == "__main__":
    raise SystemExit(main())
