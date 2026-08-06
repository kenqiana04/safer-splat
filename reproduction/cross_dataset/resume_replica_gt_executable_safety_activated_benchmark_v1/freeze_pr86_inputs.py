"""Freeze canonical Git blobs and live PR lineage before any cohort work."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from common import sha256_bytes, sha256_file, sha256_json, write_json
from task_config import (
    LIBRARY_SHA256, MAP_SNAPSHOT_ID, PR84, PR84_HEAD, PR85, PR85_HEAD,
    PR86, PR86_BASE_HEAD, PR86_HEAD, REFERENCE_MESH_SHA256, REPO_ROOT,
    ROUTE_SHA256, START_SHA256, TASK_ROOT,
)


def command(args: list[str], *, text: bool = True):
    result = subprocess.run(args, cwd=REPO_ROOT, check=True, capture_output=True, text=text)
    return result.stdout


def pr_view(number: int) -> dict:
    fields = "number,state,isDraft,mergedAt,mergeable,baseRefName,baseRefOid,headRefName,headRefOid,title,url"
    return json.loads(command(["gh", "pr", "view", str(number), "--json", fields]))


def assert_pr(record: dict, head: str, *, base_head: str | None = None) -> None:
    checks = {
        "state": record["state"] == "OPEN",
        "draft": record["isDraft"] is True,
        "unmerged": record["mergedAt"] is None,
        "mergeable": record["mergeable"] == "MERGEABLE",
        "head": record["headRefOid"] == head,
        "base": base_head is None or record["baseRefOid"] == base_head,
    }
    if not all(checks.values()):
        raise SystemExit("BLOCKED_BY_UPSTREAM_LINEAGE_MISMATCH " + json.dumps(checks, sort_keys=True))


def blob_manifest(commit: str, prefixes: tuple[str, ...]) -> list[dict]:
    raw = command(["git", "ls-tree", "-r", "-z", commit, "--", *prefixes], text=False)
    records = []
    for entry in raw.split(b"\0"):
        if not entry:
            continue
        header, path_raw = entry.split(b"\t", 1)
        mode_raw, kind_raw, blob_raw = header.split(b" ")
        if kind_raw != b"blob":
            continue
        blob = blob_raw.decode("ascii")
        content = command(["git", "cat-file", "blob", blob], text=False)
        records.append({
            "path": path_raw.decode("utf-8"),
            "mode": mode_raw.decode("ascii"),
            "git_blob": blob,
            "size": len(content),
            "sha256": sha256_bytes(content),
        })
    return sorted(records, key=lambda item: item["path"])


def main() -> None:
    pr84, pr85, pr86 = pr_view(PR84), pr_view(PR85), pr_view(PR86)
    assert_pr(pr84, PR84_HEAD)
    assert_pr(pr85, PR85_HEAD, base_head=PR84_HEAD)
    assert_pr(pr86, PR86_HEAD, base_head=PR86_BASE_HEAD)

    pr86_prefix = "reproduction/cross_dataset/replica_gt_executable_safety_method_matrix_v1"
    pr85_prefix = "reproduction/cross_dataset/replica_gt_executable_safety_activated_benchmark_v1"
    pr84_prefix = "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1"
    pr86_manifest = blob_manifest(PR86_HEAD, (pr86_prefix,))
    pr85_manifest = blob_manifest(PR85_HEAD, (pr85_prefix,))
    pr84_manifest = blob_manifest(PR84_HEAD, (pr84_prefix,))

    library_path = REPO_ROOT / pr86_prefix / "alternative_library/alternative_library_identity.json"
    library_identity = json.loads(library_path.read_text(encoding="utf-8"))
    if library_identity["global_library_sha256"] != LIBRARY_SHA256:
        raise SystemExit("BLOCKED_BY_PR86_LIBRARY_IDENTITY_MISMATCH")

    pr86_identity = {
        "status": "PASS_PR86_IDENTITY_FROZEN",
        "pr": pr86,
        "head": PR86_HEAD,
        "artifact_count": len(pr86_manifest),
        "artifact_manifest_sha256": sha256_json(pr86_manifest),
        "library_id": library_identity["library_id"],
        "global_library_sha256": library_identity["global_library_sha256"],
    }
    write_json(TASK_ROOT / "input_freeze/pr86_identity.json", pr86_identity)
    write_json(TASK_ROOT / "input_freeze/pr86_artifact_manifest.json", {"head": PR86_HEAD, "artifacts": pr86_manifest})
    write_json(TASK_ROOT / "input_freeze/pr85_identity.json", {
        "status": "PASS_PR85_HISTORY_PRESERVED",
        "pr": pr85,
        "head": PR85_HEAD,
        "artifact_count": len(pr85_manifest),
        "artifact_manifest_sha256": sha256_json(pr85_manifest),
        "historical_blocker": "BLOCKED_BY_METHOD_FAIRNESS_CONTRACT_MISMATCH",
    })
    write_json(TASK_ROOT / "input_freeze/pr84_identity.json", {
        "status": "PASS_PR84_CERTIFIER_PRESERVED",
        "pr": pr84,
        "head": PR84_HEAD,
        "artifact_count": len(pr84_manifest),
        "artifact_manifest_sha256": sha256_json(pr84_manifest),
    })
    write_json(TASK_ROOT / "input_freeze/protected_source_hashes.json", {
        "status": "PASS_PROTECTED_SOURCE_IDENTITIES_FROZEN",
        "pr84_manifest_sha256": sha256_json(pr84_manifest),
        "pr85_manifest_sha256": sha256_json(pr85_manifest),
        "pr86_manifest_sha256": sha256_json(pr86_manifest),
        "protected_source_mutation_count": 0,
    })

    upstream_map = REPO_ROOT / pr86_prefix / "input_freeze/replica_map_identity.json"
    upstream_reference = REPO_ROOT / pr86_prefix / "input_freeze/reference_mesh_identity.json"
    map_identity = json.loads(upstream_map.read_text(encoding="utf-8"))
    reference_identity = json.loads(upstream_reference.read_text(encoding="utf-8"))
    if map_identity["map_snapshot_id"] != MAP_SNAPSHOT_ID:
        raise SystemExit("BLOCKED_BY_MAP_IDENTITY_MISMATCH")
    if reference_identity["assets"]["reference_mesh"]["sha256"] != REFERENCE_MESH_SHA256:
        raise SystemExit("BLOCKED_BY_REFERENCE_IDENTITY_MISMATCH")
    map_identity.update({"route_registry_sha256": ROUTE_SHA256, "start_registry_sha256": START_SHA256, "verification_role": "REMOTE_READ_ONLY_PREFLIGHT_PENDING"})
    reference_identity.update({"reference_query_count": 0, "prelock_future_reference_read_count": 0, "verification_role": "REMOTE_READ_ONLY_PREFLIGHT_PENDING"})
    write_json(TASK_ROOT / "input_freeze/replica_map_identity.json", map_identity)
    write_json(TASK_ROOT / "input_freeze/reference_mesh_identity.json", reference_identity)
    print("PASS_PR84_PR85_PR86_INPUT_FREEZE", len(pr84_manifest), len(pr85_manifest), len(pr86_manifest))


if __name__ == "__main__":
    main()
