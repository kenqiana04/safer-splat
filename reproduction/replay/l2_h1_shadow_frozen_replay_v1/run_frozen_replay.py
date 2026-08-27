"""Execute PR #94 on the frozen, architecture-eligible historical manifest only."""
from __future__ import annotations

from collections import Counter, defaultdict
import csv
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
from typing import Any

import numpy as np

from replay_common import TASK_ROOT, canonical_bytes, read_json, sha256_bytes, sha256_file, write_csv, write_json, write_jsonl


REPO_ROOT = TASK_ROOT.parents[2]
SHADOW_ROOT = REPO_ROOT / "reproduction/shadow/l2_h1_shadow_certifier_v1"
if str(SHADOW_ROOT) not in sys.path:
    sys.path.insert(0, str(SHADOW_ROOT))

from frozen_backend_adapter import ExactSphereSegmentBackend  # noqa: E402
from l2_h1_shadow_certifier import l2_h1_shadow_certify, propagate_h1_endpoints  # noqa: E402
from shadow_contract import (  # noqa: E402
    CONSERVATIVE_ELLIPSOID_IDENTITY, EXACT_SPHERE_IDENTITY,
    load_frozen_robot_margin_contract,
)
from shadow_types import (  # noqa: E402
    ExpectedMapSnapshot, FrozenMapQueryContext, ShadowCandidate, ShadowState,
)


REMOTE_PR89 = Path("/disk1/zlab/maintenance_records/core_v1_cross_environment_activation_portability_audit_v1")
REPLICA_MAP = Path("/disk1/zlab/cross_dataset_assets/qualified_replica_gaussian_safety_maps_v1/bounded_direct_goal_v1")
SCENES = {
    "E5_STONEHENGE_SAFER": (
        Path("/disk1/zlab/projects/safer-splat/outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml"),
        "ac14f5ced354c93f26cf92404540712eff65bd02554d9e9ed0332508e290382d",
    ),
    "E6_FLIGHT_SAFER": (
        Path("/disk1/zlab/projects/safer-splat/outputs/flight/splatfacto/2024-09-12_172434/config.yml"),
        "8e7499a0d68405065b0effb7022b635ef3fbe50a53b69f5f25165260c8a493e6",
    ),
}


def read_manifest() -> list[dict[str, Any]]:
    freeze = read_json(TASK_ROOT / "source_universe_freeze.json")
    manifest = TASK_ROOT / "frozen_replay_manifest.jsonl"
    if freeze["status"] != "PASS_SOURCE_UNIVERSE_FROZEN_BEFORE_REPLAY" or freeze["replay_execution_started"] is not False:
        raise RuntimeError("SOURCE_UNIVERSE_NOT_FROZEN_PRE_REPLAY")
    if sha256_file(manifest) != freeze["manifest_sha256"]:
        raise RuntimeError("FROZEN_MANIFEST_IDENTITY_MISMATCH")
    rows = [json.loads(line) for line in manifest.read_text(encoding="utf-8").splitlines() if line]
    if len(rows) != freeze["N_all"]:
        raise RuntimeError("FROZEN_N_ALL_MISMATCH")
    return rows


def load_source_runtime_class():
    benchmark = REMOTE_PR89 / "benchmark"
    sys.path.insert(0, str(REMOTE_PR89))
    sys.path.insert(0, str(benchmark))
    spec = importlib.util.spec_from_file_location("frozen_pr89_source_runtime", benchmark / "source_runtime.py")
    if spec is None or spec.loader is None:
        raise RuntimeError("PR89_RUNTIME_SPEC_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    # dataclasses resolves forward annotations through sys.modules while the
    # frozen PR #89 module is executing, so register the exact source module
    # before exec_module without altering any scientific runtime behavior.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.SourceRuntime


def make_contexts(eligible: list[dict[str, Any]]) -> dict[str, FrozenMapQueryContext]:
    contexts: dict[str, FrozenMapQueryContext] = {}
    if any(row["environment"] == "E1_REPLICA_GT_FINE" for row in eligible):
        centers = np.load(REPLICA_MAP / "means_world_m.npy", mmap_mode="r")
        scales = np.load(REPLICA_MAP / "scales_linear_m.npy", mmap_mode="r")
        if scales.ndim != 2 or scales.shape[1] != 3 or not np.allclose(scales[:, 0], scales[:, 1]) or not np.allclose(scales[:, 0], scales[:, 2]):
            raise RuntimeError("REPLICA_MAP_NOT_FROZEN_ISOTROPIC_SPHERES")
        snapshot = "3b318a98a454ec5c36410b3c41dfb3dd4a25b7b5a1899f1f2c939fbf24ad0e55"
        backend = ExactSphereSegmentBackend(centers, scales[:, 0], snapshot)
        contexts["E1_REPLICA_GT_FINE"] = FrozenMapQueryContext(
            backend, snapshot, EXACT_SPHERE_IDENTITY, "EXACT_ANALYTIC", None,
            "ISOTROPIC_SPHERE", snapshot,
        )
    needed = [environment for environment in SCENES if any(row["environment"] == environment for row in eligible)]
    if needed:
        SourceRuntime = load_source_runtime_class()
        for environment in needed:
            config, snapshot = SCENES[environment]
            runtime = SourceRuntime(config, snapshot)
            backend = runtime.map_adapter.segment_backend
            contexts[environment] = FrozenMapQueryContext(
                backend, snapshot, CONSERVATIVE_ELLIPSOID_IDENTITY,
                "CONSERVATIVE_LOWER_BOUND", None, "ANISOTROPIC_ELLIPSOID", snapshot,
            )
    return contexts


def evaluate(row: dict[str, Any], context: FrozenMapQueryContext, robot) -> dict[str, Any]:
    state = ShadowState(tuple(row["p_k"]), tuple(row["v_k"]), row["state_id"], float(row["dt"]))
    candidate = ShadowCandidate(tuple(row["u_k"]), row["candidate_id"])
    expected = ExpectedMapSnapshot(row["map_snapshot_id"], row["map_content_sha256"])
    result = l2_h1_shadow_certify(state, candidate, expected, context, robot).to_dict()
    return {
        **result,
        "row_id": row["row_id"],
        "source_kind": row["source_kind"],
        "source_run_id": row["source_run_id"],
        "trial_id": row["trial_id"],
        "step_id": row["step_id"],
        "environment": row["environment"],
        "cohort": row["cohort"],
        "method": row["method"],
        "candidate_role": row["candidate_role"],
        "stored_l1_status": row["stored_l1_status"],
        "l2_reached": row["l2_reached"],
        "primary_analysis_eligible": row["primary_analysis_eligible"],
    }


def semantic_payload(result: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if key not in {"operational_wall_clock_s"}}


def direct_check(row: dict[str, Any], result: dict[str, Any], context: FrozenMapQueryContext, robot) -> dict[str, Any]:
    state = ShadowState(tuple(row["p_k"]), tuple(row["v_k"]), row["state_id"], float(row["dt"]))
    candidate = ShadowCandidate(tuple(row["u_k"]), row["candidate_id"])
    propagation = propagate_h1_endpoints(state, candidate, state.dt)
    certificate = context.formal_backend.certify(
        np.asarray(propagation.p_k1), np.asarray(propagation.p_k2),
        row["map_snapshot_id"], row["map_snapshot_id"],
        robot.effective_radius_m, robot.rho_seg,
    )
    direct_status = {
        "CERTIFIED_SAFE": "PASS", "CERTIFIED_UNSAFE": "FAIL",
    }.get(certificate.status.value, "UNKNOWN")
    value_match = (certificate.lower_bound is None and result["formal_value_or_bound"] is None) or (
        certificate.lower_bound is not None and result["formal_value_or_bound"] is not None and
        abs(float(certificate.lower_bound) - float(result["formal_value_or_bound"])) <= 1.0e-12
    )
    return {
        "row_id": row["row_id"], "environment": row["environment"],
        "backend_identity": row["backend_identity"],
        "independent_p_k1": list(propagation.p_k1),
        "independent_p_k2": list(propagation.p_k2),
        "endpoint_match": np.allclose(propagation.p_k1, result["p_k1"], rtol=0.0, atol=1.0e-15) and np.allclose(propagation.p_k2, result["p_k2"], rtol=0.0, atol=1.0e-15),
        "direct_status": direct_status, "shadow_status": result["status"],
        "status_match": direct_status == result["status"],
        "value_match": value_match,
        "direct_reason": certificate.reason_code,
        "shadow_formal_reason": result["formal_backend_reason"],
        "reason_match": certificate.reason_code == result["formal_backend_reason"],
        "candidate_hash_match": row["candidate_numeric_hash"] == sha256_bytes(canonical_bytes(row["u_k"])),
    }


def main() -> None:
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "1":
        raise RuntimeError("CUDA_VISIBLE_DEVICES_MUST_BE_PHYSICAL_GPU_1")
    manifest = read_manifest()
    eligible = [row for row in manifest if row["replayability_class"] == "FORMAL_REPLAYABLE" and row["primary_analysis_eligible"] is True]
    contexts = make_contexts(eligible)
    robot = load_frozen_robot_margin_contract()
    started = time.monotonic()
    first = [evaluate(row, contexts[row["environment"]], robot) for row in eligible]
    second = [evaluate(row, contexts[row["environment"]], robot) for row in eligible]
    elapsed = time.monotonic() - started
    if len(first) != len(second):
        raise RuntimeError("DETERMINISM_COUNT_MISMATCH")
    mismatches = []
    for left, right in zip(first, second):
        if canonical_bytes(semantic_payload(left)) != canonical_bytes(semantic_payload(right)):
            mismatches.append(left["row_id"])
    write_jsonl(TASK_ROOT / "replay_results.jsonl", first)
    flat = []
    for row in first:
        flat.append({
            "row_id": row["row_id"], "source_kind": row["source_kind"],
            "source_run_id": row["source_run_id"], "trial_id": row["trial_id"],
            "step_id": row["step_id"], "environment": row["environment"],
            "cohort": row["cohort"], "method": row["method"],
            "candidate_id": row["candidate_id"], "candidate_role": row["candidate_role"],
            "stored_l1_status": row["stored_l1_status"], "l2_reached": row["l2_reached"],
            "l2_status": row["status"], "reason_code": row["reason_code"],
            "p_k1": json.dumps(row["p_k1"], separators=(",", ":")),
            "p_k2": json.dumps(row["p_k2"], separators=(",", ":")),
            "formal_value_or_bound": row["formal_value_or_bound"],
            "formal_backend_status": row["formal_backend_status"],
            "formal_backend_reason": row["formal_backend_reason"],
            "backend_identity": row["backend_identity"],
            "backend_class": row["backend_class"],
            "map_snapshot_id": row["actual_map_snapshot_id"],
            "controller_authority": row["controller_authority"],
            "controller_intervention": row["controller_intervention"],
        })
    write_csv(TASK_ROOT / "replay_results.csv", flat)
    selected = []
    by_backend: dict[str, list[dict[str, Any]]] = defaultdict(list)
    result_by_id = {row["row_id"]: row for row in first}
    for row in eligible:
        by_backend[row["backend_identity"]].append(row)
    for backend, rows in sorted(by_backend.items()):
        selected.extend(sorted(rows, key=lambda item: item["row_id"])[:8])
    direct = [direct_check(row, result_by_id[row["row_id"]], contexts[row["environment"]], robot) for row in selected]
    differential_pass = all(item["endpoint_match"] and item["status_match"] and item["value_match"] and item["reason_match"] and item["candidate_hash_match"] for item in direct)
    write_json(TASK_ROOT / "replay_differential_integrity_audit.json", {
        "status": "PASS_REPLAY_DIFFERENTIAL_INTEGRITY" if differential_pass else "FAIL_REPLAY_DIFFERENTIAL_INTEGRITY",
        "selection_rule": "first 8 primary-analysis-eligible rows per backend identity after stable sort by row_id",
        "sample_count": len(direct), "checks": direct,
    })
    semantic_hash = sha256_bytes(canonical_bytes([semantic_payload(row) for row in first]))
    write_json(TASK_ROOT / "replay_determinism_audit.json", {
        "status": "PASS_REPLAY_DETERMINISM" if not mismatches else "FAIL_REPLAY_DETERMINISM",
        "complete_pass_count": 2, "candidate_count_per_pass": len(first),
        "semantic_result_sha256_pass_1": semantic_hash,
        "semantic_result_sha256_pass_2": sha256_bytes(canonical_bytes([semantic_payload(row) for row in second])),
        "mismatch_count": len(mismatches), "mismatch_row_ids": mismatches,
    })
    counts = Counter(row["status"] for row in first)
    reason_counts = Counter(row["reason_code"] for row in first if row["status"] == "UNKNOWN")
    write_json(TASK_ROOT / "replay_summary.json", {
        "status": "PASS_OFFLINE_SHADOW_REPLAY_EXECUTION" if not mismatches and differential_pass else "FAIL_OFFLINE_SHADOW_REPLAY_EXECUTION",
        "device_used": "CPU_AND_PHYSICAL_GPU_1" if any(row["environment"] in SCENES for row in eligible) else "CPU",
        "operational_wall_clock_s": elapsed,
        "formal_runtime_metric_count": 0,
        "offline_shadow_replay_run_count": 2,
        "shadow_candidate_evaluation_count": len(first),
        "N_L2_candidate_evaluated": len(first),
        "N_L2_PASS": counts["PASS"], "N_L2_FAIL": counts["FAIL"], "N_L2_UNKNOWN": counts["UNKNOWN"],
        "L2_UNKNOWN_reasons": dict(sorted(reason_counts.items())),
        "replay_results_sha256": sha256_file(TASK_ROOT / "replay_results.jsonl"),
        "manifest_sha256": sha256_file(TASK_ROOT / "frozen_replay_manifest.jsonl"),
        "controller_authority": False, "controller_intervention_count": 0,
        "formal_navigation_rollout_count": 0, "on_policy_collection_count": 0,
    })
    if mismatches or not differential_pass:
        raise RuntimeError("REPLAY_FIDELITY_OR_DETERMINISM_FAILURE")
    print("PASS_OFFLINE_SHADOW_REPLAY_EXECUTION", len(first), dict(counts), elapsed)


if __name__ == "__main__":
    main()
