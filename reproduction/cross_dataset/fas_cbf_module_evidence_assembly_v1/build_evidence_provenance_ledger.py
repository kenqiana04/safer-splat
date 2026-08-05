#!/usr/bin/env python3
"""Build an auditable source ledger with explicit uncertainty fields."""
from __future__ import annotations

from evidence_common import TASK, load_json, write_csv, write_json

FIELDS = ["evidence_id", "module", "dataset", "scene", "map_role", "source_pr", "branch", "commit", "report_path", "report_sha256", "git_blob_sha", "config_sha", "method_source_sha", "cohort_registry_sha", "sample_unit", "sample_count", "comparator", "result_type", "polarity", "activity", "domain", "allowed_claims", "prohibited_claims", "unresolved_fields"]


def main() -> int:
    sources = load_json("source_inventory/source_inventory.json")["sources"]
    if any(not row["report_sha256"] or not row["report_path"] for row in sources):
        raise RuntimeError("ledger source lacks report identity")
    write_csv(TASK / "evidence_ledger/evidence_provenance_ledger.csv", sources, FIELDS)
    write_json(TASK / "evidence_ledger/evidence_provenance_ledger.json", sources)
    missing = [{"evidence_id": row["evidence_id"], "field": field, "value": row[field], "claim_restriction": "not eligible for a strong cross-configuration claim"} for row in sources for field in ("config_sha", "method_source_sha", "cohort_registry_sha") if row[field].startswith("UNKNOWN")]
    write_json(TASK / "evidence_ledger/missing_or_ambiguous_evidence.json", {"status": "PASS_AMBIGUITY_RETAINED", "items": missing})
    print(f"PASS_EVIDENCE_PROVENANCE_LEDGER count={len(sources)} ambiguous={len(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
