"""Freeze PR #85, PR #84, and external read-only identities before design work."""
from __future__ import annotations

import json
from pathlib import Path
import shlex
import subprocess

from common import canonical_json_bytes, sha256_bytes, write_json
from task_config import (
    EXPECTED_MAP, MAP_ROOT, MAP_SNAPSHOT_ID, PR84, PR84_HEAD, PR85, PR85_BASE,
    PR85_HEAD, PR85_REPORT_SHA256, REFERENCE_MESH, REFERENCE_MESH_SHA256,
    REPO_ROOT, ROUTE_REGISTRY, ROUTE_SHA256, SERVER, START_REGISTRY,
    START_SHA256, TASK_ROOT,
)

PR85_PREFIX = "reproduction/cross_dataset/replica_gt_executable_safety_activated_benchmark_v1/"
PR84_PREFIX = "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/"
PR85_ARTIFACTS = (
    "report/REPORT_BUILD_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md",
    "report/validation_result.json", "report/downstream_handoff.json",
    "methods/fairness_audit.json", "methods/method_registry.json",
    "input_freeze/pr84_identity.json", "input_freeze/pr84_artifact_manifest.json",
    "input_freeze/replica_map_identity.json", "input_freeze/reference_mesh_identity.json",
    "audits/execution_count_audit.json",
)
PR84_ARTIFACTS = (
    "report/REPORT_IMPLEMENT_ACTUATOR_BOUNDED_SWEPT_SEGMENT_TERMINAL_BACKUP_CERTIFIER_V1.md",
    "actuator_contract.json", "adapters/gaussian_barrier_adapter.py",
    "adapters/normative_dynamics_adapter.py", "certifier/candidate_library.py",
    "certifier/executable_safety_certifier.py", "certifier/result_types.py",
    "certifier/braking_backup_policy.py", "certifier/segment_certificate.py",
    "certifier/terminal_certificate.py", "certifier/terminal_set.py",
    "certifier/backup_certifier.py", "certifier/segment_backends/analytic_primitive.py",
    "certifier/segment_backends/conservative_interval.py",
    "proof_artifacts/normative_execution_model.json",
    "proof_artifacts/terminal_set_contract.md", "proof_artifacts/proof_status_registry.json",
    "input_freeze/protected_source_hashes.json", "map_smoke/replica_smoke_records.json",
)
PROTECTED_SOURCE_PATHS = (
    "run.py", "cbf/cbf_utils.py", "splat/gsplat_utils.py", "ellipsoids/covariance_utils.py",
    "dynamics/systems.py", "reproduction/cross_dataset/replica_bounded_direct_goal_safer_fas_cbf_benchmark_v1/benchmark_core.py",
)


def git_stdout(arguments: list[str]) -> bytes:
    return subprocess.run(arguments, cwd=REPO_ROOT, check=True, capture_output=True).stdout


def git_blob(commit: str, path: str) -> dict[str, object]:
    line = git_stdout(["git", "ls-tree", commit, "--", path]).decode("utf-8").strip()
    if not line:
        raise SystemExit(f"MISSING_FROZEN_GIT_PATH:{commit}:{path}")
    left, observed_path = line.split("\t", 1)
    mode, kind, oid = left.split()
    if kind != "blob" or observed_path != path:
        raise SystemExit(f"INVALID_FROZEN_GIT_OBJECT:{path}")
    payload = git_stdout(["git", "cat-file", "blob", oid])
    return {"path": path, "mode": mode, "git_blob": oid, "size": len(payload), "sha256": sha256_bytes(payload)}


def remote_hashes() -> dict[str, dict[str, object]]:
    locations = {**{key: f"{MAP_ROOT}/{key}" for key in EXPECTED_MAP}, "route_registry": ROUTE_REGISTRY,
                 "start_registry": START_REGISTRY, "reference_mesh": REFERENCE_MESH}
    statements = [f"test -r {shlex.quote(path)}; printf '%s\\t%s\\t%s\\n' {shlex.quote(label)} \"$(sha256sum {shlex.quote(path)} | cut -d' ' -f1)\" \"$(stat -c %s {shlex.quote(path)})\"" for label, path in locations.items()]
    completed = subprocess.run(["ssh", SERVER, "set -eu; " + "; ".join(statements)], check=True, capture_output=True, text=True)
    results: dict[str, dict[str, object]] = {}
    for line in completed.stdout.splitlines():
        label, digest, size = line.split("\t")
        results[label] = {"path": locations[label], "sha256": digest, "size": int(size)}
    if set(results) != set(locations):
        raise SystemExit("REMOTE_IDENTITY_OUTPUT_SHAPE_MISMATCH")
    return results


def pr_identity(number: int) -> dict[str, object]:
    return json.loads(subprocess.run(
        ["gh", "pr", "view", str(number), "--json", "number,state,isDraft,mergeable,mergedAt,baseRefName,baseRefOid,headRefName,headRefOid,url,title"],
        cwd=REPO_ROOT, check=True, capture_output=True, text=True,
    ).stdout)


def main() -> None:
    pr85 = pr_identity(PR85)
    pr84 = pr_identity(PR84)
    checks = {
        "pr85_open": pr85["state"] == "OPEN", "pr85_draft": pr85["isDraft"] is True,
        "pr85_unmerged": pr85["mergedAt"] is None, "pr85_mergeable": pr85["mergeable"] == "MERGEABLE",
        "pr85_base": pr85["baseRefName"] == "fas-cbf-unified-executable-safety-certifier-v1" and pr85["baseRefOid"] == PR85_BASE,
        "pr85_head": pr85["headRefName"] == "replica-gt-executable-safety-activated-benchmark-v1" and pr85["headRefOid"] == PR85_HEAD,
        "pr84_open": pr84["state"] == "OPEN", "pr84_draft": pr84["isDraft"] is True,
        "pr84_unmerged": pr84["mergedAt"] is None, "pr84_mergeable": pr84["mergeable"] == "MERGEABLE",
        "pr84_head": pr84["headRefOid"] == PR84_HEAD,
    }
    pr85_blobs = [git_blob(PR85_HEAD, PR85_PREFIX + item) for item in PR85_ARTIFACTS]
    pr84_blobs = [git_blob(PR84_HEAD, PR84_PREFIX + item) for item in PR84_ARTIFACTS]
    report = next(item for item in pr85_blobs if str(item["path"]).endswith("REPORT_BUILD_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md"))
    checks["pr85_report"] = report["sha256"] == PR85_REPORT_SHA256
    remote = remote_hashes()
    map_checks = {name: remote[name]["sha256"] == expected for name, expected in EXPECTED_MAP.items()}
    map_checks.update({"route_registry": remote["route_registry"]["sha256"] == ROUTE_SHA256, "start_registry": remote["start_registry"]["sha256"] == START_SHA256})
    checks["map_identity"] = all(map_checks.values())
    checks["reference_identity"] = remote["reference_mesh"]["sha256"] == REFERENCE_MESH_SHA256
    protected = [git_blob(PR85_HEAD, path) for path in PROTECTED_SOURCE_PATHS]
    status = "PASS_PR85_PR84_AND_EXTERNAL_INPUT_FREEZE" if all(checks.values()) else "BLOCKED_BY_FROZEN_INPUT_IDENTITY_MISMATCH"
    write_json(TASK_ROOT / "input_freeze/pr85_identity.json", {"status": status, "checks": checks, "pr85": pr85, "artifact_count": len(pr85_blobs), "artifact_manifest_sha256": sha256_bytes(canonical_json_bytes(pr85_blobs))})
    write_json(TASK_ROOT / "input_freeze/pr85_artifact_manifest.json", {"head": PR85_HEAD, "artifacts": pr85_blobs})
    write_json(TASK_ROOT / "input_freeze/pr84_certifier_identity.json", {"head": PR84_HEAD, "pr84": pr84, "artifact_count": len(pr84_blobs), "artifact_manifest_sha256": sha256_bytes(canonical_json_bytes(pr84_blobs)), "artifacts": pr84_blobs})
    write_json(TASK_ROOT / "input_freeze/protected_source_hashes.json", {"head": PR85_HEAD, "mutation_count": 0, "sources": protected})
    write_json(TASK_ROOT / "input_freeze/replica_map_identity.json", {"status": "PASS_REPLICA_GT_FINE_IDENTITY" if all(map_checks.values()) else "FAIL_REPLICA_GT_FINE_IDENTITY", "map_snapshot_id": MAP_SNAPSHOT_ID, "checks": map_checks, "assets": {name: remote[name] for name in (*EXPECTED_MAP, "route_registry", "start_registry")}})
    write_json(TASK_ROOT / "input_freeze/reference_mesh_identity.json", {"status": "PASS_OFFICIAL_REPLICA_REFERENCE_IDENTITY" if checks["reference_identity"] else "FAIL_OFFICIAL_REPLICA_REFERENCE_IDENTITY", "reference_query_count": 0, "assets": {"reference_mesh": remote["reference_mesh"]}})
    if status != "PASS_PR85_PR84_AND_EXTERNAL_INPUT_FREEZE":
        raise SystemExit(status)
    print(status, len(pr85_blobs), len(pr84_blobs), len(protected))


if __name__ == "__main__":
    main()
