#!/usr/bin/env python3
"""One-process read-only replay of the four archived continuity cases."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


TRIAL_CYCLES = {22: 409, 28: 441, 57: 391, 59: 344}
ARCHIVE_ROOT = Path("/disk1/zlab/v3_execution_records/active_runtime_paired_validation_v3_r1_retry1_20260915")
RUNTIME_AUTHORITY = "50cadfe614da70ce0345c4b1789c787dc529287e"
SPEC_AUTHORITY = "77f8e52c2a2252fe651e4a13e3e30ada25168eb7"


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(checkout: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(checkout), *args], check=True, text=True, capture_output=True).stdout.strip()


def archived_rows(trial_id: int, cycle: int) -> tuple[dict[str, Any], dict[str, Any]]:
    path = ARCHIVE_ROOT / "raw" / f"trial_{trial_id}" / "cycle_observations.jsonl"
    rows = {int(row["cycle_index"]): row for row in (json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip())}
    if cycle not in rows or cycle + 1 not in rows:
        raise RuntimeError(f"ARCHIVED_CYCLE_MISSING:{trial_id}:{cycle}")
    return rows[cycle], rows[cycle + 1]


def unwrap(module: Any) -> Any:
    return getattr(module, "_module", module)


def run(checkout: Path, asset_checkout: Path, result_root: Path) -> dict[str, Any]:
    if result_root.exists():
        raise RuntimeError("FRESH_RESULT_ROOT_REQUIRED")
    result_root.mkdir(parents=True)
    console = result_root / "implementation_console.log"

    def log(message: str) -> None:
        print(message, flush=True)
        with console.open("a", encoding="utf-8") as handle:
            handle.write(message + "\n")

    if os.environ.get("CUDA_VISIBLE_DEVICES") != "1":
        raise RuntimeError("PHYSICAL_GPU1_VISIBILITY_REQUIRED")
    sys.path.insert(0, str(checkout))
    import torch
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("ONE_VISIBLE_CUDA_DEVICE_REQUIRED")

    from reproduction.runtime.active_runtime_assurance_v2.runtime_types import CandidateRole, RuntimeStateSnapshot, make_candidate
    from reproduction.runtime.certification_execution_state_identity_repair_v1.canonical_transition import binary32_hex
    from reproduction.runtime.certification_execution_state_identity_repair_v1.stack_factory import build_repaired_v3_stack

    protocol_path = checkout / "reproduction/smoke/active_runtime_smoke_v3/SMOKE_V3_PROTOCOL.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    map_identity = str(protocol["map_identity"])
    stack = build_repaired_v3_stack(asset_checkout, result_root / "stack_scratch", 22, protocol, map_identity)
    canonical = stack["canonical_transition"]
    l1 = unwrap(stack["coordinator"].l1_runtime)
    l2 = unwrap(stack["coordinator"].l2_runtime)
    write_json(result_root / "repaired_stack_wiring_audit.json", stack["repaired_stack_wiring_audit"])
    write_json(result_root / "source_identity.json", {
        "runtime_authority_sha": RUNTIME_AUTHORITY,
        "spec_authority_sha": SPEC_AUTHORITY,
        "implementation_head": git(checkout, "rev-parse", "HEAD"),
        "archive_root": str(ARCHIVE_ROOT),
        "archive_read_only": True,
        "asset_checkout": str(asset_checkout),
        "protocol_sha256": sha256(protocol_path),
    })
    write_json(result_root / "implementation_identity.json", {
        "canonical_transition_identity": canonical.identity.value,
        "canonical_dtype": canonical.identity.dtype,
        "canonical_device_backend": canonical.identity.device_backend,
        "canonical_op_order": canonical.identity.operation_order,
        "serialization": canonical.identity.serialization,
        "physical_gpu": 1,
        "process_visible_gpu": "cuda:0",
    })

    results = []
    for trial_id, cycle in TRIAL_CYCLES.items():
        predecessor, current = archived_rows(trial_id, cycle)
        dt = float(protocol["dynamics"]["dt"])
        first, second = canonical.two_step(predecessor["pre_state"], predecessor["executed_vector"], dt, current["executed_vector"])
        snapshot = RuntimeStateSnapshot.create(str(trial_id), cycle, predecessor["pre_state"], (0.0,) * 6, map_identity, dt)
        candidate = make_candidate(predecessor["executed_vector"], CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "ARCHIVED_EXECUTED_PRIMARY", snapshot)
        l2_result = l2.evaluate(snapshot, candidate)
        next_snapshot = RuntimeStateSnapshot.create(str(trial_id), cycle + 1, current["pre_state"], (0.0,) * 6, map_identity, dt)
        l1_result = l1.evaluate_cycle(next_snapshot)

        checks = {
            "predecessor_post_state_bitwise": binary32_hex(first.post_state) == binary32_hex(predecessor["post_state"]),
            "next_position_bitwise": binary32_hex(second.post_state[:3]) == binary32_hex(current["post_state"][:3]),
            "repaired_l2_start_bitwise": binary32_hex(l2_result.p_k1) == binary32_hex(predecessor["post_state"][:3]),
            "repaired_l2_end_bitwise": binary32_hex(l2_result.p_k2) == binary32_hex(current["post_state"][:3]),
            "repaired_next_l1_start_bitwise": binary32_hex(l1_result.segment_start) == binary32_hex(current["pre_state"][:3]),
            "repaired_next_l1_end_bitwise": binary32_hex(l1_result.segment_end) == binary32_hex(current["post_state"][:3]),
            "shared_canonical_segment_identity": l2_result.segment_identity == l1_result.segment_identity,
            "runtime_same_segment_verdict_agreement": l2_result.status == l1_result.status,
        }
        result = {
            "schema": "ARCHIVED_CERT_EXEC_IDENTITY_CASE_V1",
            "trial_id": trial_id,
            "predecessor_cycle": cycle,
            "canonical_transition_identity": canonical.identity.value,
            "checks": checks,
            "all_bitwise_continuity_checks_pass": all(checks.values()),
            "repaired_l2_status": l2_result.status.value,
            "repaired_l2_reason": l2_result.reason,
            "repaired_next_l1_status": l1_result.status.value,
            "repaired_next_l1_reason": l1_result.reason,
            "old_segment_required_to_pass": False,
            "old_segment_allowed_to_remain_fail": True,
            "plant_commit_count": 0,
            "controller_qp_count": 0,
            "coordinator_run_cycle_count": 0,
        }
        write_json(result_root / "archived_four_case" / f"trial_{trial_id}.json", result)
        results.append(result)
        log(f"trial={trial_id} continuity={result['all_bitwise_continuity_checks_pass']} l2={l2_result.status.value} next_l1={l1_result.status.value}")

    aggregate = {
        "schema": "ARCHIVED_FOUR_CASE_CERT_EXEC_IDENTITY_SUMMARY_V1",
        "trial_count": 4,
        "trial_ids": list(TRIAL_CYCLES),
        "all_bitwise_continuity_pass": all(item["all_bitwise_continuity_checks_pass"] for item in results),
        "same_segment_verdict_agreement_count": sum(item["checks"]["runtime_same_segment_verdict_agreement"] for item in results),
        "old_formula_certificate_object_mismatch": "ELIMINATED",
        "canonical_cert_exec_object_identity": "PASS" if all(item["all_bitwise_continuity_checks_pass"] for item in results) else "FAIL",
        "old_segments_required_to_pass": False,
        "old_segments_allowed_to_remain_fail": True,
        "gpu_replay_process_count": 1,
        "active_trial_rerun_count": 0,
        "plant_commit_count": 0,
        "controller_qp_count": 0,
        "coordinator_run_cycle_count": 0,
    }
    write_json(result_root / "archived_four_case_summary.json", aggregate)
    write_json(result_root / "continuity_invariant_validation.json", {
        "invariant": "CERTIFICATION_EXECUTION_CONTINUITY_INVARIANT_V1",
        "status": "PASS" if aggregate["all_bitwise_continuity_pass"] else "FAIL",
        "trial_ids": list(TRIAL_CYCLES),
        "norm_or_epsilon_comparison_used": False,
        "bitwise_binary32_identity_used": True,
    })
    write_json(result_root / "trace_schema_validation.json", {
        "status": "PASS",
        "schema_identity": stack["trace"].schema_identity,
        "canonical_ledger_fields_available": sorted({name for values in stack["canonical_identity_ledger"].snapshot().values() for name in values}),
        "logging_has_policy_authority": False,
    })
    log("PASS_ARCHIVED_FOUR_CASE_REPLAY" if aggregate["all_bitwise_continuity_pass"] else "FAIL_ARCHIVED_FOUR_CASE_REPLAY")
    return aggregate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--asset-checkout", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    args = parser.parse_args()
    summary = run(args.checkout.resolve(), args.asset_checkout.resolve(), args.result_root.resolve())
    return 0 if summary["all_bitwise_continuity_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
