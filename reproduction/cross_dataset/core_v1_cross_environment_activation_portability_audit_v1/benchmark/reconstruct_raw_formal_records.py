"""Reconstruct the immutable raw formal CSV from its three terminal shards."""
from __future__ import annotations

import csv
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import sha256_file, write_csv


def main() -> None:
    root = Path("/disk1/zlab/maintenance_records/core_v1_cross_environment_activation_portability_audit_v1")
    sources = [root / "runtime_work/formal" / f"{name}.csv" for name in (
        "E1_REPLICA_GT_FINE", "E5_STONEHENGE_SAFER", "E6_FLIGHT_SAFER"
    )]
    rows: list[dict[str, str]] = []
    fields: list[str] = []
    for source in sources:
        with source.open(encoding="utf-8", newline="") as handle:
            rows.extend(csv.DictReader(handle))
    for row in rows:
        fields.extend(key for key in row if key not in fields)
    output = root / "benchmark/one_step_records_raw_formal.csv"
    write_csv(output, rows, fields)
    digest = sha256_file(output)
    if len(rows) != 1440 or digest != "9d13a540edff5e79706d0ae6a905ea6c58ed56020d9a9a8a0e43617b70dc65af":
        raise RuntimeError(f"raw reconstruction mismatch: rows={len(rows)} sha256={digest}")
    print("PASS_RAW_FORMAL_RECORD_RECONSTRUCTION", len(rows), digest)


if __name__ == "__main__":
    main()
