#!/usr/bin/env python3
"""Future post-run engineering acceptance only; never runs Reference or NI."""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import math
import os
from pathlib import Path
import sys

from validate_bounded_local_recovery_smoke_retry2_v1 import PROTOCOL, REPO, read


def lines(path: Path) -> list[dict]:
    if not path.is_file():
        raise RuntimeError("REQUIRED_IMMUTABLE_EVIDENCE_MISSING:" + str(path))
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def frozen_hard_proxy(states_by_trial: dict[int, list[tuple[float, ...]]], p: dict) -> dict:
    """Same represented-map 0.015-q segment proxy as frozen post-repair analysis; no NI."""
    import numpy as np
    import torch
    sys.path[:0] = [str(REPO / "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1"), str(REPO)]
    from splat.gsplat_utils import GSplatLoader
    from adapters.gaussian_barrier_adapter import SourceGaussianBarrierAdapter
    v2_file = REPO / "reproduction/pilot/active_runtime_pilot_v2/run_active_runtime_pilot_v2.py"
    spec = importlib.util.spec_from_file_location("_bounded_smoke_frozen_hard_proxy", v2_file)
    if spec is None or spec.loader is None:
        raise RuntimeError("FROZEN_HARD_PROXY_MODULE_UNAVAILABLE")
    v2 = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = v2
    spec.loader.exec_module(v2)
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("FROZEN_HARD_PROXY_REQUIRES_SINGLE_VISIBLE_GPU")
    loader = GSplatLoader(Path(p["map"]["root"]) / "config.yml", torch.device("cuda:0"))
    radius = p["geometry"]["hard_radius_q"]

    def query(point, **kwargs):
        if not torch.is_tensor(point):
            point = torch.as_tensor(point, device=torch.device("cuda:0"), dtype=torch.float32)
        return loader.query_distance(point, **kwargs)

    provider = SourceGaussianBarrierAdapter(query, p["map"]["identity"], radius, int(loader.means.shape[0]))
    rows = []
    for trial, states in states_by_trial.items():
        violations = unknown = 0
        clearances = []
        for before, after in zip(states[:-1], states[1:]):
            status, value = v2.certify_segment_clearance(provider, np.asarray(before[:3]),
                                                          np.asarray(after[:3]), radius)
            violations += status == "UNSAFE"
            unknown += status not in ("SAFE", "UNSAFE")
            if value is not None and math.isfinite(float(value)):
                clearances.append(float(value))
        rows.append({"trial_id": trial, "hard_violation_segments": violations,
                     "hard_unknown_segments": unknown,
                     "minimum_hard_clearance_q": min(clearances) if clearances else None})
    return {"schema": "BOUNDED_RECOVERY_SMOKE_RETRY2_HARD_SAFETY_AUDIT_V1", "per_trial": rows,
            "hard_violation_trials": sum(x["hard_violation_segments"] > 0 for x in rows),
            "hard_violation_segments": sum(x["hard_violation_segments"] for x in rows),
            "hard_unknown_trials": sum(x["hard_unknown_segments"] > 0 for x in rows),
            "hard_unknown_segments": sum(x["hard_unknown_segments"] for x in rows),
            "global_min_hard_clearance_q": min((x["minimum_hard_clearance_q"] for x in rows
                 if x["minimum_hard_clearance_q"] is not None), default=None),
            "radius_q": radius, "negative_tolerance": None}


def analyze(*, write_outputs: bool) -> dict:
    # Nerfstudio and legacy proxy imports may resolve repository-relative paths.
    # Bind them to the exact checkout rather than the task directory.
    os.chdir(REPO)
    p = read(PROTOCOL)
    root = Path(p["future_result_root"])
    if not (root / "BATCH_COMPLETE.json").is_file():
        raise RuntimeError("THREE_TRIAL_BATCH_COMPLETE_LOCK_REQUIRED")
    if read(root / "BATCH_COMPLETE.json")["trial_order"] != [15, 45, 75]:
        raise RuntimeError("TRIAL_ORDER_DRIFT")
    summaries, cycles, attempts, generations, states = [], [], [], [], {}
    evidence_rows, rank_rows = [], []
    process_failures = integrity = generator_bad = trigger_bad = priority_bad = exhaustion_bad = uncertified = trace_bad = 0
    evidence_missing = evidence_conflict = primary_corruption = rewrite_exceptions = 0
    counts = {"recovery_eligibility_events": 0, "recovery_scan_count": 0,
              "recovery_candidate_attempt_count": 0, "recovery_selected_count": 0,
              "recovery_PlantCommit_count": 0, "public_cycle_count": 0,
              "PlantCommit_count": 0, "main_trace_record_count": 0,
              "trace_lock_record_count": 0, "recovery_candidate_trace_record_count": 0,
              "recovery_l2_enter_count": 0, "recovery_l2_result_count": 0,
              "recovery_l2_pass_count": 0, "recovery_l2_fail_count": 0,
              "recovery_l2_unknown_count": 0, "recovery_l2_exception_count": 0}
    hard_zero_counts = {name: 0 for name in p["hard_zero_integrity_gates"]}
    for trial in p["cohort"]["trial_order"]:
        raw = root / "raw" / f"trial_{trial}"
        completion = read(root / f"trial_{trial}_complete.json")
        summary = read(raw / "trial_summary.json")
        metadata = read(raw / "bounded_recovery_process_metadata.json")
        trace = lines(raw / "runtime_trace.jsonl")
        observations = lines(raw / "recovery_cycle_observations.jsonl")
        generation_path = raw / "recovery_generation.jsonl"
        generated = lines(generation_path) if generation_path.is_file() else []
        trace_lock = read(raw / "runtime_trace_lock.json")
        exit_code = int((raw / "process_exit_code.txt").read_text(encoding="utf-8").strip())
        process_failures += bool(exit_code or completion["process_exit_code"] or metadata["exit_code"])
        if metadata["source_head"] != p["implementation_head"] and metadata["source_head"] != read(root / "BOUNDED_RECOVERY_SMOKE_RETRY2_LAUNCH_AUTHORIZATION.json")["source_head"]:
            raise RuntimeError("TRIAL_SOURCE_HEAD_MISMATCH")
        if metadata["map_identity"] != p["map"]["identity"] or metadata["geometry"] != p["geometry"]:
            raise RuntimeError("TRIAL_MAP_OR_GEOMETRY_AUTHORITY_MISMATCH")
        if summary.get("finalization_status") != "FINALIZED" or not summary.get("trace_lock_identity"):
            integrity += 1
            hard_zero_counts["malformed_or_finalization_error_count"] += 1
        if not (len(trace) == len(observations) == summary["completed_cycles"] ==
                summary["trace_record_count"] == summary["trace_lock_record_count"] ==
                trace_lock["record_count"]):
            trace_bad += 1
        counts["public_cycle_count"] += len(observations)
        counts["main_trace_record_count"] += len(trace)
        counts["trace_lock_record_count"] += summary["trace_lock_record_count"]
        counts["PlantCommit_count"] += summary["plant_commit_count"]
        for key in ("duplicate_plant_commit_count", "duplicate_trace_append_count", "illegal_token_mutation_count",
                    "selected_executed_identity_mismatch_count", "evidence_incomplete_count", "recovery_required_count",
                    "plant_outcome_unknown_count", "nonfinite_count", "action_bound_violation_count",
                    "exception_count", "cuda_oom_count", "unintended_plant_commit_count"):
            integrity += int(summary.get(key, 0))
        summary_hard_zero_map = {
            "trace_write_failure_count": "trace_write_failure_count",
            "trace_commit_atomicity_violation_count": "trace_commit_atomicity_violation_count",
            "cert_exec_identity_mismatch_count": "selected_executed_identity_mismatch_count",
            "canonical_transition_mismatch_count": "canonical_transition_mismatch_count",
            "state_continuity_mismatch_count": "state_continuity_mismatch_count",
            "state_continuity_unknown_count": "state_continuity_unknown_count",
            "routing_ambiguous_count": "routing_ambiguous_count",
            "routing_missing_count": "routing_missing_count",
            "unauthorized_source_execution_count": "unauthorized_source_execution_count",
            "unverified_action_execution_count": "unverified_action_execution_count",
            "stale_backup_execution_count": "stale_backup_execution_count",
            "same_key_duplicate_retry_count": "same_key_duplicate_retry_count",
            "internal_recovery_loop_count": "internal_recovery_loop_count",
            "historical_diagnostic_runtime_authority_count": "historical_diagnostic_runtime_authority_count",
        }
        for gate, source in summary_hard_zero_map.items():
            hard_zero_counts[gate] += int(summary.get(source, 0))
        hard_zero_counts["process_nonzero_exit_count"] += int(bool(exit_code or completion["process_exit_code"] or metadata["exit_code"]))
        stderr = (raw / "stderr.log").read_text(encoding="utf-8", errors="replace") if (raw / "stderr.log").is_file() else ""
        rewrite_exceptions += stderr.count("CANONICAL_EVIDENCE_REWRITE_FORBIDDEN:canonical_l2_")
        evidence_conflict += stderr.count("CANONICAL_SCOPED_EVIDENCE_REWRITE_FORBIDDEN:canonical_l2_candidate_evidence:")
        trial_states = []
        if observations:
            trial_states.append(tuple(observations[0]["pre_state"]))
        by_cycle = {row["cycle_index"]: row for row in observations}
        trace_by_cycle = {row["cycle_index"]: row for row in trace}
        if len(by_cycle) != len(observations) or len(trace_by_cycle) != len(trace):
            trace_bad += 1
        for row in observations:
            cycles.append({"trial_id": trial, **row})
            if row["committed"]:
                if row["post_state"] is None:
                    integrity += 1
                else:
                    trial_states.append(tuple(row["post_state"]))
            if row["selected_action_identity"] != row["executed_action_identity"] and row["committed"]:
                integrity += 1
            if row["l1_status"] not in ("PASS", "FAIL", "UNKNOWN", None):
                integrity += 1
            runtime_attempts = row.get("recovery_attempts", [])
            trace_facts = dict(trace_by_cycle.get(row["cycle_index"], {}).get("facts", []))
            scoped_raw = trace_facts.get("canonical_l2_candidate_evidence", [])
            scope_names = [scope for scope, _payload in scoped_raw]
            scopes = {scope: dict(payload) for scope, payload in scoped_raw}
            deterministic_scopes = scope_names == sorted(scope_names) and all(
                list(dict(payload)) == sorted(dict(payload)) for _scope, payload in scoped_raw
            )
            primary_scopes = [scope for scope, payload in scopes.items() if payload.get("candidate_role") == "PRIMARY"]
            if "PRIMARY_L2" in row.get("phase_history", []):
                flat_required = (
                    "canonical_l2_x_k1_identity", "canonical_l2_p_k1_identity",
                    "canonical_l2_x_k2_identity", "canonical_l2_p_k2_identity",
                    "canonical_l2_segment_identity", "canonical_l2_status",
                    "canonical_l2_reason", "canonical_l2_evidence_identity",
                    "canonical_selected_candidate_identity",
                )
                if (not all(key in trace_facts for key in flat_required) or len(primary_scopes) != 1 or
                        trace_facts.get("canonical_selected_candidate_identity") != (primary_scopes[0] if primary_scopes else None)):
                    primary_corruption += 1
            if len(scope_names) != len(set(scope_names)) or not deterministic_scopes:
                evidence_conflict += 1
            if runtime_attempts:
                counts["recovery_eligibility_events"] += 1
            normative = dict(trace_by_cycle.get(row["cycle_index"], {}).get("facts", [])).get("recovery_attempts", [])
            normative_rows = [dict(item) for item in normative]
            if normative_rows != runtime_attempts:
                trace_bad += 1
            for item in runtime_attempts:
                candidate = "candidate_id" in item
                if candidate:
                    counts["recovery_candidate_attempt_count"] += 1
                    attempts.append({"trial_id": trial, "cycle_index": row["cycle_index"], **item})
                counts["recovery_selected_count"] += bool(item.get("supervisor_selected"))
                counts["recovery_PlantCommit_count"] += bool(candidate and item.get("supervisor_selected") and row["committed"])
                entered_l2 = candidate and item.get("C0_status") == "PASS"
                l2_status = item.get("L2_status")
                l2_result = l2_status in ("PASS", "FAIL", "UNKNOWN")
                counts["recovery_l2_enter_count"] += bool(entered_l2)
                counts["recovery_l2_result_count"] += bool(l2_result)
                counts["recovery_l2_pass_count"] += l2_status == "PASS"
                counts["recovery_l2_fail_count"] += l2_status == "FAIL"
                counts["recovery_l2_unknown_count"] += l2_status == "UNKNOWN"
                counts["recovery_l2_exception_count"] += item.get("exception_stage") == "L2"
                if l2_result:
                    payload = scopes.get(item.get("candidate_id"))
                    if payload is None:
                        evidence_missing += 1
                    elif (payload.get("candidate_identity") != item.get("candidate_id") or
                          payload.get("candidate_source_type") != item.get("candidate_source") or
                          payload.get("candidate_role") != "ALTERNATIVE" or
                          payload.get("status") != l2_status):
                        evidence_missing += 1
                    evidence_rows.append({"trial_id": trial, "cycle_index": row["cycle_index"],
                        "candidate_id": item.get("candidate_id"), "l2_status": l2_status,
                        "scope_present": payload is not None, "scope_payload": payload})
                if candidate and any(not item.get(field) for field in ("candidate_id", "recovery_scan_id", "exhaustion_key",
                        "candidate_source", "source_state_identity", "map_identity", "generator_version", "final_disposition")):
                    trace_bad += 1
                if candidate and item.get("candidate_source") != p["recovery"]["source"]:
                    generator_bad += 1
                if item.get("supervisor_selected") and not (item.get("C0_status") == item.get("L2_status") ==
                        item.get("L3_status") == "PASS" and item.get("plant_commit_authorized") and row["committed"]):
                    uncertified += 1
                if candidate and any(status != "OPEN" for _stage, status in item.get("deadline_at_relevant_gates", [])
                                     if _stage == "RECOVERY_SEARCH"):
                    trigger_bad += 1
            counts["recovery_candidate_trace_record_count"] += sum("candidate_id" in item for item in normative_rows)
            if runtime_attempts and not any(str(rule).startswith("REC_") for rule in row["routing_rule_ids"]):
                priority_bad += 1
            if runtime_attempts and row["l1_status"] != "PASS":
                trigger_bad += 1
        if len(trial_states) != summary["plant_commit_count"] + 1:
            integrity += 1
        states[trial] = trial_states
        for item in generated:
            generations.append({"trial_id": trial, **item})
            cycle = by_cycle.get(item["cycle_index"])
            if cycle is None:
                trace_bad += 1
            else:
                required_routes = {"REC_L3_PREFETCH", "REC_TERMINAL_PASS", "REC_SCAN_ADMIT_OPEN"}
                if (cycle.get("l1_status") != "PASS" or
                    not required_routes.issubset(set(cycle.get("routing_rule_ids", []))) or
                    cycle.get("terminal_status") != "PASS" or
                    not any(x["stage"] == "RECOVERY_CANDIDATE_ADMISSION" and x["status"] == "OPEN"
                            for x in cycle.get("deadline_observations", []))):
                    trigger_bad += 1
            candidates = item["candidates"]
            ranks = [x["candidate_rank"] for x in candidates]
            if len(candidates) > 6 or ranks != sorted(set(ranks)) or not all(0 <= rank < 6 for rank in ranks):
                generator_bad += 1
            expected_vectors = ((0.1, 0, 0), (-0.1, 0, 0), (0, 0.1, 0), (0, -0.1, 0), (0, 0, 0.1), (0, 0, -0.1))
            for x in candidates:
                expected = expected_vectors[x["candidate_rank"]]
                if x["direction"] != p["recovery"]["candidate_order"][x["candidate_rank"]] or any(
                        abs(float(a) - b) > 1e-8 for a, b in zip(x["vector"], expected)):
                    generator_bad += 1
            attempted = sorted(a["candidate_rank"] for a in attempts
                                if a["trial_id"] == trial and a["cycle_index"] == item["cycle_index"])
            rank_rows.append({"trial_id": trial, "cycle_index": item["cycle_index"],
                "candidates_generated": len(candidates), "attempted_ranks": attempted,
                "max_attempted_rank": max(attempted) if attempted else None,
                "duplicate_skipped_ranks": item.get("skipped_duplicate_ranks", [])})
        summaries.append({"trial_id": trial, "cycles": len(observations), "plant_commits": summary["plant_commit_count"],
                          "trace_records": len(trace), "recovery_attempts": sum(x["trial_id"] == trial for x in attempts),
                          "process_exit_code": exit_code, "finalization_status": summary.get("finalization_status")})
    counts["recovery_scan_count"] = len({(x["trial_id"], x["cycle_index"]) for x in generations})
    keys = {}
    for attempt in attempts:
        key = (attempt["trial_id"], attempt["exhaustion_key"])
        entry = keys.setdefault(key, [])
        signature = (attempt["candidate_rank"], attempt["canonical_action_identity"])
        if signature in entry or len(entry) >= 6:
            exhaustion_bad += 1
        entry.append(signature)
    if counts["recovery_candidate_attempt_count"] and not generations:
        generator_bad += 1
    hard = frozen_hard_proxy(states, p)
    hard_zero_counts["canonical_l2_evidence_rewrite_exception_count"] = rewrite_exceptions
    hard_zero_counts["candidate_scoped_l2_evidence_missing_count"] = evidence_missing
    hard_zero_counts["candidate_scoped_l2_scope_conflict_count"] = evidence_conflict
    hard_zero_counts["legacy_primary_l2_flat_evidence_corruption_count"] = primary_corruption
    hard_zero_counts["represented_map_hard_violation_count"] = hard["hard_violation_segments"]
    hard_zero_counts["hard_safety_unknown_count"] = hard["hard_unknown_segments"]
    if rewrite_exceptions:
        status = "FAIL_MULTI_CANDIDATE_L2_EVIDENCE_REGRESSION"
    elif counts["recovery_l2_enter_count"] and not counts["recovery_l2_result_count"] and counts["recovery_l2_exception_count"]:
        status = "FAIL_RECOVERY_L2_RUNTIME_INFRASTRUCTURE"
    elif process_failures:
        status = "FAIL_SMOKE_RUNTIME_PROCESS"
    elif integrity or any(hard_zero_counts.values()):
        status = "FAIL_SMOKE_INTEGRITY"
    elif hard["hard_violation_segments"] or hard["hard_unknown_segments"]:
        status = "FAIL_SMOKE_HARD_SAFETY"
    elif generator_bad:
        status = "FAIL_RECOVERY_GENERATOR_CONTRACT"
    elif trigger_bad:
        status = "FAIL_RECOVERY_TRIGGER_CONTRACT"
    elif priority_bad:
        status = "FAIL_RECOVERY_ROUTING_PRIORITY_CONTRACT"
    elif exhaustion_bad:
        status = "FAIL_RECOVERY_EXHAUSTION_CONTRACT"
    elif uncertified:
        status = "FAIL_UNCERTIFIED_RECOVERY_EXECUTION"
    elif trace_bad:
        status = "FAIL_RECOVERY_TRACE_CONTRACT"
    elif not counts["recovery_eligibility_events"] or not counts["recovery_scan_count"] or not counts["recovery_candidate_attempt_count"]:
        status = "INCONCLUSIVE_RECOVERY_PATH_NOT_EXERCISED"
    elif not counts["recovery_selected_count"] or not counts["recovery_PlantCommit_count"]:
        status = "INCONCLUSIVE_RECOVERY_SEARCH_EXERCISED_BUT_NO_RECOVERY_COMMIT"
    else:
        status = "PASS_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_V1"
    result = {"schema": "BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_ANALYSIS_V1", "status": status,
              "counts": counts, "process_failures": process_failures, "integrity_violations": integrity,
              "generator_violations": generator_bad, "trigger_violations": trigger_bad,
              "priority_violations": priority_bad, "exhaustion_violations": exhaustion_bad,
              "uncertified_execution_violations": uncertified, "trace_violations": trace_bad,
              "hard_zero_counts": hard_zero_counts,
              "multi_candidate_l2_evidence_audit": {"rows": evidence_rows,
                  "missing_count": evidence_missing, "scope_conflict_count": evidence_conflict,
                  "legacy_primary_flat_corruption_count": primary_corruption,
                  "canonical_rewrite_exception_count": rewrite_exceptions},
              "rank_progression": rank_rows,
              "hard_safety": hard, "progress_role": "DIAGNOSTIC_ONLY_NO_NI_NO_REFERENCE_PAIRING", "reference_pairing": False,
              "noninferiority_analysis": False}
    if write_outputs:
        write_json(root / "SMOKE_SUMMARY.json", result)
        write_csv(root / "PER_TRIAL_SMOKE_SUMMARY.csv", summaries, list(summaries[0]))
        write_csv(root / "RECOVERY_SCAN_SUMMARY.csv", generations,
                  ["trial_id", "cycle_index", "state_identity", "grant_identity", "status", "skipped_duplicate_ranks", "candidates"])
        write_csv(root / "RECOVERY_CANDIDATE_ATTEMPTS.csv", attempts,
                  sorted({key for row in attempts for key in row} or {"trial_id", "cycle_index"}))
        write_json(root / "RECOVERY_REJECTION_BREAKDOWN.json", {"by_stage": {
            stage: sum(a.get("rejected_by_stage") == stage for a in attempts)
            for stage in ("C0", "L2", "L3", "IDENTITY", "DEADLINE", "DUPLICATE")}})
        write_json(root / "RECOVERY_ROUTING_AUDIT.json", {"violations": priority_bad,
                   "selected": counts["recovery_selected_count"], "committed": counts["recovery_PlantCommit_count"]})
        write_json(root / "RECOVERY_EXHAUSTION_AUDIT.json", {"violations": exhaustion_bad,
                   "unique_trial_keys": len(keys), "candidate_limit": 6})
        write_json(root / "HARD_SAFETY_SMOKE_AUDIT.json", hard)
        write_json(root / "TRACE_INTEGRITY_AUDIT.json", {"violations": trace_bad,
                   "public_cycles": counts["public_cycle_count"], "plant_commits": counts["PlantCommit_count"],
                   "main_trace_records": counts["main_trace_record_count"],
                   "trace_lock_records": counts["trace_lock_record_count"],
                   "recovery_candidate_records": counts["recovery_candidate_trace_record_count"]})
        write_json(root / "MULTI_CANDIDATE_L2_EVIDENCE_AUDIT.json", result["multi_candidate_l2_evidence_audit"])
        write_json(root / "RECOVERY_L2_REACHABILITY_AUDIT.json", {key: value for key, value in counts.items() if key.startswith("recovery_l2_")})
        write_json(root / "RECOVERY_RANK_PROGRESSION_AUDIT.json", {"scans": rank_rows})
        report = root / "report/REPORT_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_V1.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(f"# Bounded Local Recovery Smoke Retry2 V1\n\nStatus: {status}\n\n"
                          "Engineering-only represented-map smoke. No Reference pairing, NI, efficacy, physical safety, or real-time claim.\n",
                          encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--postrun-authorized", action="store_true")
    args = parser.parse_args()
    if not args.postrun_authorized:
        raise RuntimeError("FUTURE_POSTRUN_AUTHORIZATION_REQUIRED")
    result = analyze(write_outputs=True)
    print(result["status"])
    return 0 if result["status"] == "PASS_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_V1" else 2


if __name__ == "__main__":
    raise SystemExit(main())
