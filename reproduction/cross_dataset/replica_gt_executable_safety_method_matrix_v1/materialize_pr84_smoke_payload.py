"""Materialize byte-identical, task-owned PR #84 adapter payload for generator-only smoke."""
from __future__ import annotations

import subprocess

from common import sha256_bytes, write_json
from task_config import PR84_HEAD, REPO_ROOT, TASK_ROOT

PREFIX = "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/"
FILES = (
    "adapters/__init__.py", "adapters/gaussian_barrier_adapter.py", "certifier/__init__.py",
    "certifier/result_types.py", "certifier/segment_backends/__init__.py",
    "certifier/segment_backends/base.py", "certifier/segment_backends/analytic_primitive.py",
    "map_smoke/replica_smoke_records.json",
)


def main() -> None:
    root = TASK_ROOT / "smoke/pr84_frozen_payload"
    records = []
    for relative in FILES:
        path = PREFIX + relative
        row = subprocess.run(["git", "ls-tree", PR84_HEAD, "--", path], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout.strip()
        left, observed = row.split("\t", 1); mode, kind, oid = left.split()
        if kind != "blob" or observed != path:
            raise SystemExit("INVALID_PR84_SMOKE_PAYLOAD_PATH:" + path)
        payload = subprocess.run(["git", "cat-file", "blob", oid], cwd=REPO_ROOT, check=True, capture_output=True).stdout
        target = root / relative; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(payload)
        records.append({"path": relative, "mode": mode, "git_blob": oid, "sha256": sha256_bytes(payload), "size": len(payload)})
    write_json(TASK_ROOT / "smoke/pr84_frozen_payload_manifest.json", {"pr84_head": PR84_HEAD, "purpose": "EXACT_PR84_FULL_GAUSSIAN_QUERY_ONLY", "forbidden": ["ExecutableSafetyCertifier", "segment_outcome", "backup_witness", "reference_oracle"], "files": records})
    print("PASS_PR84_SMOKE_PAYLOAD_MATERIALIZED", len(records))


if __name__ == "__main__":
    main()
