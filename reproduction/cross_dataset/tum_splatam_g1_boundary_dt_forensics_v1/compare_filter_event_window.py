#!/usr/bin/env python3
"""Record the actual original candidate-filter contract for the event window."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/disk1/zlab/maintenance_records/tum_splatam_g1_boundary_dt_forensics_v1")


def main() -> None:
    rows = json.loads((ROOT / "fullmap_queries" / "event_window_fullmap.json").read_text(encoding="utf-8"))
    records = [{"step": row["step"], "state_label": row["state_label"], "full_h": row["h"], "full_active_index": row["active_index"], "full_candidate_count": row["candidate_count"], "filtered_h": row["h"], "filtered_active_index": row["active_index"], "filtered_candidate_count": row["candidate_count"], "filter_equivalent_to_full_query": True} for row in rows]
    payload = {
        "source_contract": "Frozen cbf/cbf_utils.py calls GSplatLoader.query_distance over the complete map before h_rep_minimal post-query polytope reduction.",
        "prequery_spatial_candidate_filter_exists": False,
        "postquery_reduction": "h_rep_minimal is a QP constraint-polytope reduction; it is not a map-candidate query filter and cannot omit the full-map minimum before query.",
        "filter_miss_count": 0,
        "filter_miss_certified": False,
        "rows": records,
    }
    out = ROOT / "filter_queries"; out.mkdir(parents=True, exist_ok=True)
    (out / "filter_event_window_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
