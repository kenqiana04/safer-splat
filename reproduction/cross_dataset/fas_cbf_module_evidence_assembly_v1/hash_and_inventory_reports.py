#!/usr/bin/env python3
"""Write a compact immutable report-hash inventory from the discovered sources."""
from __future__ import annotations

from evidence_common import TASK, load_json, write_json


def main() -> int:
    data = load_json("source_inventory/source_inventory.json")
    compact = [{key: row[key] for key in ("evidence_id", "source_pr", "branch", "commit", "report_path", "report_sha256", "git_blob_sha", "report_bytes")} for row in data["sources"]]
    write_json(TASK / "source_inventory/report_hash_inventory.json", {"count": len(compact), "reports": compact})
    print(f"PASS_REPORT_HASH_INVENTORY count={len(compact)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
