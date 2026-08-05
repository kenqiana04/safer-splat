#!/usr/bin/env python3
"""Register positive, negative, and structural evidence without deletion or relabeling."""
from __future__ import annotations

from evidence_common import TASK, load_json, write_csv


def main() -> int:
    rows = []
    for source in load_json("source_inventory/source_inventory.json")["sources"]:
        rows.append({"evidence_id": source["evidence_id"], "class": source["polarity"], "result_type": source["result_type"], "summary": source["allowed_claims"], "boundary": source["prohibited_claims"]})
    write_csv(TASK / "module_matrices/positive_negative_structural_registry.csv", rows, list(rows[0]))
    print("PASS_POSITIVE_NEGATIVE_STRUCTURAL_REGISTRY")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
