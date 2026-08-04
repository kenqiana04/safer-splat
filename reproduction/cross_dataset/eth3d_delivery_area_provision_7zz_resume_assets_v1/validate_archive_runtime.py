#!/usr/bin/env python3
"""Synthetic functional qualification for a task-local 7zz."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

from archive_common import audit_slt, parse_slt, tree_identity


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    args = parser.parse_args()
    root = args.task_root / "tmp/archive_runtime_synthetic"
    if root.exists():
        resolved = root.resolve()
        if args.task_root.resolve() not in resolved.parents:
            raise RuntimeError("unsafe synthetic cleanup")
        shutil.rmtree(root)
    source = root / "source"
    extracted = root / "extracted"
    (source / "nested").mkdir(parents=True)
    (source / "unicode_路径").mkdir()
    (source / "normal.txt").write_text("ETH3D archive runtime\n", encoding="utf-8")
    (source / "nested/data.bin").write_bytes(bytes(range(256)))
    (source / "unicode_路径/文件.txt").write_text("可信归档\n", encoding="utf-8")
    archive = root / "synthetic.7z"
    create = subprocess.run([str(args.binary), "a", "-t7z", str(archive), "."], cwd=source, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    test = subprocess.run([str(args.binary), "t", str(archive)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    listing = subprocess.run([str(args.binary), "l", "-slt", str(archive)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    extract = subprocess.run([str(args.binary), "x", "-y", f"-o{extracted}", str(archive)], text=True,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    records = parse_slt(listing.stdout)
    safe = audit_slt(records, archive.stat().st_size)
    before = tree_identity(source)
    after = tree_identity(extracted)
    malicious = root / "traversal.zip"
    with zipfile.ZipFile(malicious, "w") as zf:
        zf.writestr("../escape.txt", "blocked")
    bad_listing = subprocess.check_output([str(args.binary), "l", "-slt", str(malicious)], text=True)
    bad_audit = audit_slt(parse_slt(bad_listing), malicious.stat().st_size)
    result = {
        "status": "PASS" if all(x.returncode == 0 for x in (create, test, listing, extract)) and safe["status"] == "PASS" and before["tree_sha256"] == after["tree_sha256"] and bad_audit["status"] == "FAIL" else "FAIL",
        "create_returncode": create.returncode,
        "test_returncode": test.returncode,
        "list_returncode": listing.returncode,
        "extract_returncode": extract.returncode,
        "unicode_path_present": (extracted / "unicode_路径/文件.txt").is_file(),
        "source_tree_sha256": before["tree_sha256"],
        "extracted_tree_sha256": after["tree_sha256"],
        "safe_archive_audit": {k: v for k, v in safe.items() if k != "entries"},
        "traversal_archive_pre_extract_status": bad_audit["status"],
        "traversal_issue_codes": [x["code"] for x in bad_audit["issues"]],
        "traversal_extracted": False
    }
    (args.task_root / "archive_runtime_synthetic_validation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    (args.task_root / "logs/archive_runtime_synthetic_full.log").write_text("\n".join([create.stdout, test.stdout, listing.stdout, extract.stdout]), encoding="utf-8")
    if result["status"] != "PASS":
        raise SystemExit("SYNTHETIC_RUNTIME_VALIDATION_FAILED")
    print("PASS_TASK_LOCAL_7ZZ_SYNTHETIC_VALIDATION")


if __name__ == "__main__":
    main()
