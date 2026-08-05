#!/usr/bin/env python3
"""Separate official, GT-derived, learned 3DGS, and learned SLAM map roles."""
from __future__ import annotations

from evidence_common import TASK, load_json, write_csv, write_json


def main() -> int:
    sources = load_json("source_inventory/source_inventory.json")["sources"]
    role_text = {
        "OFFICIAL_SAFER_MAP": "In-domain module validation carrier; results remain configuration-specific.",
        "GT_DERIVED_GAUSSIAN": "Clean Replica controller benchmark; deterministic GT-derived safety map, not learned.",
        "LEARNED_3DGS": "External learned-map viability and structural activation-limit carrier; not deployment-certified.",
        "LEARNED_SLAM_MAP": "External TUM case-study carrier using GSplat-overlap proxy; not official mesh collision evidence.",
    }
    rows = []
    for role, role_description in role_text.items():
        selected = [row for row in sources if row["map_role"] == role]
        rows.append({"map_role": role, "datasets": "; ".join(sorted({row["dataset"] for row in selected})), "evidence_count": len(selected), "paper_role": role_description, "superiority_eligible": "NO"})
    fields = list(rows[0])
    write_csv(TASK / "module_matrices/dataset_map_role_matrix.csv", rows, fields)
    write_json(TASK / "module_matrices/dataset_map_role_matrix.json", {"roles": rows})
    print("PASS_DATASET_ROLE_MATRIX")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
