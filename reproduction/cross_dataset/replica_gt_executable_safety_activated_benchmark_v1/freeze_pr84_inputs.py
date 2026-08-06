"""Freeze PR #84 Git blobs and read-only Replica/map/reference identities."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from common import canonical_json_bytes, sha256_bytes, write_json
from task_config import (
    EXPECTED_MAP, MAP_ROOT, MAP_SNAPSHOT_ID, MESH_ORACLE, MESH_ORACLE_VALIDATION,
    PR84, PR84_BASE, PR84_HEAD, PR84_REPORT_SHA256, REFERENCE_MESH,
    REFERENCE_MESH_SHA256, REPO_ROOT, ROUTE_REGISTRY, ROUTE_SHA256, SERVER,
    START_REGISTRY, START_SHA256, TASK_ROOT,
)

PREFIX = "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/"
FROZEN_ARTIFACTS = (
    "report/REPORT_IMPLEMENT_ACTUATOR_BOUNDED_SWEPT_SEGMENT_TERMINAL_BACKUP_CERTIFIER_V1.md",
    "report/validation_result.json",
    "report/downstream_handoff.json",
    "proof_artifacts/normative_execution_model.json",
    "actuator_contract.json",
    "proof_artifacts/swept_segment_derivation.md",
    "certifier/segment_backends/analytic_primitive.py",
    "certifier/segment_backends/conservative_interval.py",
    "proof_artifacts/terminal_set_contract.md",
    "certifier/braking_backup_policy.py",
    "certifier/result_types.py",
    "certifier/candidate_library.py",
    "certifier/executable_safety_certifier.py",
    "proof_artifacts/proof_status_registry.json",
    "input_freeze/protected_source_hashes.json",
)
ADDITIONAL_PROTECTED = (
    "run.py",
    "reproduction/cross_dataset/replica_bounded_direct_goal_safer_fas_cbf_benchmark_v1/benchmark_core.py",
    "reproduction/cross_dataset/replica_bounded_direct_goal_safer_fas_cbf_benchmark_v1/frozen_bounded_qp_adapter.py",
    "reproduction/cross_dataset/replica_bounded_direct_goal_safer_fas_cbf_benchmark_v1/run_trial.py",
    "reproduction/cross_dataset/replica_bounded_direct_goal_safer_fas_cbf_benchmark_v1/run_benchmark.py",
    "reproduction/cross_dataset/replica_render_protocol_v3_coverage_qualification_v1/_v3_common.py",
)


def run(command: list[str]) -> bytes:
    return subprocess.run(command, cwd=REPO_ROOT, check=True, capture_output=True).stdout


def blob(path: str) -> dict[str, object]:
    row = run(["git", "ls-tree", PR84_HEAD, "--", path]).decode("utf-8").strip()
    if not row:
        raise SystemExit(f"MISSING_FROZEN_GIT_PATH:{path}")
    left, observed_path = row.split("\t", 1)
    mode, object_type, oid = left.split()
    if object_type != "blob" or observed_path != path:
        raise SystemExit(f"INVALID_FROZEN_GIT_OBJECT:{path}")
    payload = run(["git", "cat-file", "blob", oid])
    return {"path": path, "mode": mode, "git_blob": oid, "size": len(payload), "sha256": sha256_bytes(payload)}


def remote_identities() -> dict[str, dict[str, object]]:
    paths = {**{name: f"{MAP_ROOT}/{name}" for name in EXPECTED_MAP},
             "route_registry": ROUTE_REGISTRY, "start_registry": START_REGISTRY,
             "reference_mesh": REFERENCE_MESH, "mesh_oracle": MESH_ORACLE,
             "mesh_oracle_validation": MESH_ORACLE_VALIDATION}
    script = "set -eu; " + "; ".join(
        f"test -r '{path}'; printf '%s\\t' '{label}'; sha256sum '{path}' | awk '{{print $1}}'; stat -c '%s' '{path}'"
        for label, path in paths.items()
    )
    lines = subprocess.run(["ssh", SERVER, script], check=True, capture_output=True, text=True).stdout.splitlines()
    if len(lines) != 2 * len(paths):
        raise SystemExit("REMOTE_IDENTITY_OUTPUT_SHAPE_MISMATCH")
    result: dict[str, dict[str, object]] = {}
    for index, (label, path) in enumerate(paths.items()):
        observed_label, digest = lines[2 * index].split("\t", 1)
        if observed_label != label:
            raise SystemExit("REMOTE_IDENTITY_LABEL_MISMATCH")
        result[label] = {"path": path, "sha256": digest, "size": int(lines[2 * index + 1])}
    return result


def main() -> None:
    pr = json.loads(subprocess.run(
        ["gh", "pr", "view", str(PR84), "--json", "number,state,isDraft,mergeable,mergedAt,baseRefName,baseRefOid,headRefName,headRefOid,url,title"],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    ).stdout)
    checks = {
        "state_open": pr["state"] == "OPEN",
        "draft_true": pr["isDraft"] is True,
        "unmerged": pr["mergedAt"] is None,
        "mergeable": pr["mergeable"] == "MERGEABLE",
        "base": pr["baseRefName"] == "fas-cbf-core-v1-conceptual-closure" and pr["baseRefOid"] == PR84_BASE,
        "head": pr["headRefName"] == "fas-cbf-unified-executable-safety-certifier-v1" and pr["headRefOid"] == PR84_HEAD,
    }
    artifacts = [blob(PREFIX + relative) for relative in FROZEN_ARTIFACTS]
    report = next(item for item in artifacts if str(item["path"]).endswith("REPORT_IMPLEMENT_ACTUATOR_BOUNDED_SWEPT_SEGMENT_TERMINAL_BACKUP_CERTIFIER_V1.md"))
    checks["report_sha256"] = report["sha256"] == PR84_REPORT_SHA256
    remote = remote_identities()
    map_checks = {name: remote[name]["sha256"] == digest for name, digest in EXPECTED_MAP.items()}
    map_checks.update({"route_registry": remote["route_registry"]["sha256"] == ROUTE_SHA256,
                       "start_registry": remote["start_registry"]["sha256"] == START_SHA256})
    reference_checks = {"official_mesh": remote["reference_mesh"]["sha256"] == REFERENCE_MESH_SHA256,
                        "oracle_readable": remote["mesh_oracle"]["size"] > 0,
                        "oracle_validation_readable": remote["mesh_oracle_validation"]["size"] > 0}
    checks["map_identity"] = all(map_checks.values())
    checks["reference_identity"] = all(reference_checks.values())
    protected = [blob(path) for path in ADDITIONAL_PROTECTED]
    identity = {"status": "PASS_PR84_AND_EXTERNAL_INPUT_FREEZE" if all(checks.values()) else "BLOCKED_BY_FROZEN_INPUT_IDENTITY_MISMATCH",
                "pr84": pr, "checks": checks, "artifact_count": len(artifacts),
                "artifact_manifest_sha256": sha256_bytes(canonical_json_bytes(artifacts))}
    write_json(TASK_ROOT / "input_freeze/pr84_identity.json", identity)
    write_json(TASK_ROOT / "input_freeze/pr84_artifact_manifest.json", {"head": PR84_HEAD, "artifacts": artifacts})
    write_json(TASK_ROOT / "input_freeze/protected_source_hashes.json", {"head": PR84_HEAD, "mutation_count": 0, "sources": protected})
    write_json(TASK_ROOT / "input_freeze/replica_map_identity.json", {"status": "PASS_REPLICA_GT_FINE_IDENTITY" if all(map_checks.values()) else "FAIL_REPLICA_GT_FINE_IDENTITY", "map_snapshot_id": MAP_SNAPSHOT_ID, "checks": map_checks, "assets": {key: remote[key] for key in (*EXPECTED_MAP.keys(), "route_registry", "start_registry")}})
    write_json(TASK_ROOT / "input_freeze/reference_mesh_identity.json", {"status": "PASS_OFFICIAL_REPLICA_REFERENCE_IDENTITY" if all(reference_checks.values()) else "FAIL_OFFICIAL_REPLICA_REFERENCE_IDENTITY", "checks": reference_checks, "assets": {key: remote[key] for key in ("reference_mesh", "mesh_oracle", "mesh_oracle_validation")}})
    if not all(checks.values()):
        raise SystemExit(identity["status"])
    print(identity["status"], len(artifacts), len(protected))


if __name__ == "__main__":
    main()
