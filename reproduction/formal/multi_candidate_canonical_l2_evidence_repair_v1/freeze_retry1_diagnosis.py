#!/usr/bin/env python3
"""Read-only freeze of Retry1 hashes and three diagnostic witness rows."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
RETRY1 = Path("/disk1/zlab/v3_repair_records/bounded_local_recovery_smoke_v1_retry1_20260918")
ATTEMPT0 = Path("/disk1/zlab/v3_repair_records/bounded_local_recovery_smoke_v1_20260918")
WITNESSES = ((15, 202), (45, 168), (75, 281))
TOP = ("SMOKE_SUMMARY.json", "RECOVERY_CANDIDATE_ATTEMPTS.csv", "RECOVERY_SCAN_SUMMARY.csv",
       "RECOVERY_REJECTION_BREAKDOWN.json", "RECOVERY_ROUTING_AUDIT.json", "RECOVERY_EXHAUSTION_AUDIT.json")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write(name: str, value) -> None:
    target = TASK / "results_cpu_validation" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def root_snapshot(root: Path) -> dict:
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        files.append({"path": path.relative_to(root).as_posix(), "size": path.stat().st_size, "sha256": sha(path)})
    digest = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"root": str(root), "file_count": len(files), "content_manifest_sha256": digest, "files": files}


def jsonl_row(path: Path, cycle: int) -> dict:
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if int(row["cycle_index"]) == cycle:
            return row
    raise RuntimeError(f"WITNESS_CYCLE_MISSING:{path}:{cycle}")


def main() -> int:
    for root in (RETRY1, ATTEMPT0):
        if not root.is_dir():
            raise RuntimeError("FROZEN_RESULT_ROOT_MISSING:" + str(root))
    inputs = {name: {"path": str(RETRY1 / name), "sha256": sha(RETRY1 / name),
                     "size": (RETRY1 / name).stat().st_size} for name in TOP}
    witnesses = []
    for trial, cycle in WITNESSES:
        raw = RETRY1 / "raw" / f"trial_{trial}"
        observation_file = raw / "recovery_cycle_observations.jsonl"
        trace_file = raw / "runtime_trace.jsonl"
        observation = jsonl_row(observation_file, cycle)
        trace = jsonl_row(trace_file, cycle)
        attempt = observation["recovery_attempts"]
        facts = dict(trace.get("facts", []))
        witness = {
            "trial_id": trial, "cycle_index": cycle,
            "observation_source_sha256": sha(observation_file), "trace_source_sha256": sha(trace_file),
            "primary_l2_pass": "L2_PASS" in observation["routing_rule_ids"],
            "recovery_candidate_available": "REC_CANDIDATE_AVAILABLE" in observation["routing_rule_ids"],
            "recovery_c0_pass": bool(attempt) and attempt[0]["C0_status"] == "PASS",
            "recovery_l2_not_reached": bool(attempt) and attempt[0]["L2_status"] == "NOT_REACHED",
            "runtime_error_at_l2": any(row["reason"] == "STAGE_EXCEPTION:L2:RuntimeError" for row in observation["stage_failures"]),
            "candidate_rank": attempt[0]["candidate_rank"], "candidate_source": attempt[0]["candidate_source"],
            "final_disposition": attempt[0]["final_disposition"], "exception_stage": attempt[0]["exception_stage"],
            "fallback_rule_present": "ARB_TERMINAL" in observation["routing_rule_ids"],
            "final_action_role": observation["action_role"],
            "trace_has_legacy_primary_l2": all(name in facts for name in (
                "canonical_l2_x_k1_identity", "canonical_l2_p_k1_identity", "canonical_l2_x_k2_identity",
                "canonical_l2_p_k2_identity", "canonical_l2_segment_identity", "canonical_l2_status",
                "canonical_l2_reason", "canonical_l2_evidence_identity")),
        }
        if not all((witness["primary_l2_pass"], witness["recovery_candidate_available"], witness["recovery_c0_pass"],
                    witness["recovery_l2_not_reached"], witness["runtime_error_at_l2"], witness["fallback_rule_present"],
                    witness["trace_has_legacy_primary_l2"])):
            raise RuntimeError("FROZEN_WITNESS_PATTERN_MISMATCH:" + str(trial))
        witnesses.append(witness)
    with (RETRY1 / "RECOVERY_CANDIDATE_ATTEMPTS.csv").open(encoding="utf-8", newline="") as stream:
        attempts = list(csv.DictReader(stream))
    with (RETRY1 / "RECOVERY_SCAN_SUMMARY.csv").open(encoding="utf-8", newline="") as stream:
        scans = list(csv.DictReader(stream))
    summary = json.loads((RETRY1 / "SMOKE_SUMMARY.json").read_text(encoding="utf-8"))
    write("frozen_retry1_input_authority.json", {
        "schema": "MULTI_CANDIDATE_L2_REPAIR_RETRY1_INPUT_AUTHORITY_V1", "read_only": True,
        "requested_input_files": inputs, "summary_status": summary["status"],
        "candidate_attempt_rows": len(attempts), "scan_rows": len(scans), "witnesses": witnesses,
    })
    write("frozen_witness_audit.json", {
        "schema": "MULTI_CANDIDATE_L2_REPAIR_FROZEN_WITNESS_AUDIT_V1", "witnesses": witnesses,
        "interpretation": "STRUCTURAL_RUNTIME_EVIDENCE_ONLY_NO_GEOMETRIC_RECERTIFICATION",
        "root_cause_hypothesis": "H1_PENDING_SEPARATE_CPU_REPRODUCTION",
    })
    write("result_root_snapshots_before.json", {
        "schema": "MULTI_CANDIDATE_L2_REPAIR_RESULT_ROOT_SNAPSHOT_V1",
        "retry1": root_snapshot(RETRY1), "attempt0": root_snapshot(ATTEMPT0),
    })
    print(json.dumps({"status": "PASS_READ_ONLY_RETRY1_DIAGNOSIS_FREEZE", "witness_count": len(witnesses),
                      "retry1_status": summary["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
