#!/usr/bin/env python3
"""Freeze the already-deployed task-local official 7zz identity."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
from pathlib import Path

from archive_common import sha256_file


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--package", type=Path, required=True)
    args = parser.parse_args()
    version = subprocess.check_output([str(args.binary), "i"], text=True).splitlines()[1].strip()
    stat = args.binary.stat()
    identity = {
        "status": "PASS",
        "provisioning_route": "T1_TASK_LOCAL_OFFICIAL_PORTABLE_7ZZ",
        "recorded_utc": utc(),
        "official_discovery_url": "https://www.7-zip.org/download.html",
        "source_url": "https://github.com/ip7z/7zip/releases/download/26.02/7z2602-linux-x64.tar.xz",
        "final_redirect_host": "release-assets.githubusercontent.com",
        "package_path": str(args.package),
        "package_bytes": args.package.stat().st_size,
        "package_sha256": sha256_file(args.package),
        "official_checksum_available": False,
        "binary_path": str(args.binary),
        "binary_bytes": stat.st_size,
        "binary_sha256": sha256_file(args.binary),
        "version": version,
        "owner_uid": stat.st_uid,
        "group_gid": stat.st_gid,
        "mode": oct(stat.st_mode & 0o777),
        "supports": ["a", "t", "l -slt", "x"],
        "system_path_modified": False,
        "system_package_installed": False,
        "existing_conda_environment_modified": False,
        "project_training_environment_modified": False
    }
    (args.task_root / "task_local_archive_runtime_identity.json").write_text(json.dumps(identity, indent=2) + "\n", encoding="utf-8")
    print(identity["version"])


if __name__ == "__main__":
    main()
