#!/usr/bin/env python3
"""Verify all immutable Replica V3 inputs before protocol candidate generation."""
from __future__ import annotations

import argparse
from pathlib import Path

from _v3_common import EXPECTED, MESH, NAVMESH, ROOT, V1_MANIFEST, V1_STAGING, atomic_json, ensure_server_root, sha256_path, tree_hash


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr53-head", required=True)
    parser.add_argument("--bvh-source", type=Path, required=True)
    parser.add_argument("--bvh-origin-blob", required=True)
    args = parser.parse_args()
    ensure_server_root()
    observed = {
        "mesh_sha256": sha256_path(MESH),
        "navmesh_sha256": sha256_path(NAVMESH),
        "v1_manifest_sha256": sha256_path(V1_MANIFEST),
        "v1_staging_tree_sha256": tree_hash(V1_STAGING),
    }
    checks = {name: observed[name] == EXPECTED[name] for name in observed}
    payload = {
        "status": "PASS_FROZEN_REPLICA_V3_INPUT_IDENTITY" if all(checks.values()) else "BLOCKED_BY_REPLICA_V3_INPUT_IDENTITY_MISMATCH",
        "pr53_head": args.pr53_head,
        "expected": {key: EXPECTED[key] for key in observed},
        "observed": observed,
        "checks": checks,
        "paths": {"mesh": str(MESH), "navmesh": str(NAVMESH), "v1_manifest": str(V1_MANIFEST), "v1_staging": str(V1_STAGING)},
        "bvh_source_sha256": sha256_path(args.bvh_source),
        "bvh_origin_git_blob": args.bvh_origin_blob,
        "formal_render_count": 0,
        "publication_count": 0,
        "gaussian_training_count": 0,
        "safer_execution_count": 0,
        "tum_rollout_count": 0,
    }
    atomic_json(ROOT / "input_identity" / "upstream_replica_v3_identity.json", payload)
    if not all(checks.values()):
        raise SystemExit(payload["status"])


if __name__ == "__main__":
    main()
