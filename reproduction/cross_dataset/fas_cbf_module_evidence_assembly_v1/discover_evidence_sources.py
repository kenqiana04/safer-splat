#!/usr/bin/env python3
"""Resolve report objects through frozen Git commits without copying source reports."""
from __future__ import annotations

from evidence_common import TASK, ensure_dirs, inventory_sources, write_json


def main() -> int:
    ensure_dirs()
    rows = inventory_sources()
    if len(rows) != 18 or len({row["evidence_id"] for row in rows}) != len(rows):
        raise RuntimeError("evidence source inventory is incomplete or nonunique")
    if any(not row["report_sha256"] or not row["git_blob_sha"] for row in rows):
        raise RuntimeError("a source report identity is missing")
    write_json(TASK / "source_inventory/source_inventory.json", {"source_count": len(rows), "sources": rows})
    print(f"PASS_EVIDENCE_SOURCE_DISCOVERY count={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
