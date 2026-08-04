#!/usr/bin/env python3
"""Run 7zz CRC and SLT archive security validation."""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

from archive_common import audit_slt, parse_slt
from task_config import ARCHIVE_CACHE, ASSETS, SEVEN_Z, TASK_ROOT


def main() -> None:
    crc_records: list[dict] = []
    security_records: list[dict] = []
    manifest_rows: list[dict] = []
    for name, expected, role in ASSETS:
        archive = ARCHIVE_CACHE / name
        crc = subprocess.run([str(SEVEN_Z), "t", "-y", str(archive)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (TASK_ROOT / "logs" / f"crc_{name}.txt").write_text(crc.stdout, encoding="utf-8")
        crc_records.append({"archive": name, "returncode": crc.returncode, "status": "PASS" if crc.returncode == 0 else "FAIL"})
        if crc.returncode:
            raise RuntimeError(f"CRC_FAILURE {name}")
        listing = subprocess.run([str(SEVEN_Z), "l", "-slt", str(archive)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
        (TASK_ROOT / "archive_listing" / f"{name}.slt.txt").write_text(listing.stdout, encoding="utf-8")
        records = parse_slt(listing.stdout)
        audit = audit_slt(records, archive.stat().st_size)
        audit.update({"archive": name, "role": role, "archive_bytes": archive.stat().st_size})
        security_records.append(audit)
        for entry in audit["entries"]:
            manifest_rows.append({"archive": name, "path": entry.get("Path", ""), "size": entry.get("Size", ""),
                                  "packed_size": entry.get("Packed Size", ""), "attributes": entry.get("Attributes", "")})
        if audit["status"] != "PASS":
            raise RuntimeError(f"ARCHIVE_SECURITY_FAILURE {name}: {audit['issues'][:5]}")
    (TASK_ROOT / "archive_crc_validation.json").write_text(json.dumps({"status": "PASS", "archives": crc_records}, indent=2) + "\n", encoding="utf-8")
    compact = [{k: v for k, v in r.items() if k != "entries"} for r in security_records]
    (TASK_ROOT / "archive_security_audit.json").write_text(json.dumps({"status": "PASS", "archives": compact}, indent=2) + "\n", encoding="utf-8")
    with (TASK_ROOT / "archive_internal_manifest.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["archive", "path", "size", "packed_size", "attributes"])
        writer.writeheader(); writer.writerows(manifest_rows)
    print("PASS_ARCHIVE_CRC_SECURITY", len(crc_records), len(manifest_rows))


if __name__ == "__main__":
    main()
