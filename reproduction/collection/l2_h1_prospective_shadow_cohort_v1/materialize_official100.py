#!/usr/bin/env python3
"""Materialize PR #100's frozen cross-platform official100 byte identity."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path

from collection_common import EXPECTED_UPSTREAM_HEAD, OFFICIAL100_SHA256

RELATIVE = Path("reproduction/experiment_protocol_freeze_v1/trial_manifests/stonehenge_official100_manifest.csv")
RAW_GIT_BLOB_SHA256 = "3ab8169266d6c401491fcebaa81d9c352f9c5f8556dee439476ded30311eb3a3"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    args = parser.parse_args()
    checkout = args.checkout.resolve(strict=True)
    raw = subprocess.check_output([
        "git", "-C", str(checkout), "cat-file", "blob", f"{EXPECTED_UPSTREAM_HEAD}:{RELATIVE.as_posix()}"
    ])
    if hashlib.sha256(raw).hexdigest() != RAW_GIT_BLOB_SHA256 or b"\r\n" in raw:
        raise RuntimeError("official100 raw Git blob identity is not the frozen LF source")
    materialized = raw.replace(b"\n", b"\r\n")
    if hashlib.sha256(materialized).hexdigest() != OFFICIAL100_SHA256:
        raise RuntimeError("deterministic CRLF materialization does not match PR100 official100 lock")
    destination = checkout / RELATIVE
    destination.write_bytes(materialized)
    print(f"OFFICIAL100_MATERIALIZATION=PASS sha256={OFFICIAL100_SHA256} semantic_content_changed=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
