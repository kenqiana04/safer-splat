#!/usr/bin/env python3
"""Sequentially acquire the nine frozen ETH3D archives through the managed proxy."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from archive_common import sha256_file
from task_config import ARCHIVE_CACHE, ASSETS, DENYLIST, OFFICIAL_BASE, PROXY_WRAPPER, TASK_ROOT, ensure_roots


def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_curl(args: list[str], capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run([str(PROXY_WRAPPER), "curl", *args], text=True, stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.STDOUT if capture else None, check=False)


def head(url: str) -> dict:
    result = run_curl(["--fail", "--location", "--head", "--silent", "--show-error",
                       "--connect-timeout", "30", "--write-out", "\nEFFECTIVE_URL=%{url_effective}\nHTTP_CODE=%{http_code}\n", url], capture=True)
    if result.returncode:
        raise RuntimeError(f"HEAD failed rc={result.returncode}: {result.stdout}")
    lengths = [int(x) for x in re.findall(r"(?im)^content-length:\s*(\d+)\s*$", result.stdout)]
    effective = re.findall(r"(?m)^EFFECTIVE_URL=(.+)$", result.stdout)[-1].strip()
    code = int(re.findall(r"(?m)^HTTP_CODE=(\d+)$", result.stdout)[-1])
    host = (urlparse(effective).hostname or "").lower()
    return {"http_code": code, "content_length": lengths[-1] if lengths else None,
            "effective_url": effective, "effective_host": host, "raw": result.stdout}


def main() -> None:
    ensure_roots()
    registry_path = TASK_ROOT / "download_attempt_registry.json"
    identity_path = TASK_ROOT / "downloaded_archive_identity.json"
    attempts: list[dict] = []
    identities: list[dict] = []
    for name, expected, role in ASSETS:
        url = f"{OFFICIAL_BASE}/{name}"
        meta = head(url)
        (TASK_ROOT / "logs" / f"head_{name}.txt").write_text(meta.pop("raw"), encoding="utf-8")
        if meta["http_code"] != 200 or meta["content_length"] != expected:
            raise RuntimeError(f"FROZEN_METADATA_DRIFT {name}: {meta}")
        if meta["effective_host"] not in {"www.eth3d.net", "eth3d.net"}:
            raise RuntimeError(f"NON_OFFICIAL_REDIRECT {name}: {meta['effective_url']}")
        final = ARCHIVE_CACHE / name
        partial = ARCHIVE_CACHE / f"{name}.partial"
        if final.exists():
            if final.stat().st_size != expected:
                raise RuntimeError(f"EXISTING_SIZE_MISMATCH {name}")
            status = "REUSED_VERIFIED_EXISTING"
        else:
            if partial.exists() and partial.stat().st_size > expected:
                partial.unlink()
            started = utc()
            result = run_curl(["--fail", "--location", "--continue-at", "-", "--retry", "3",
                               "--retry-delay", "5", "--connect-timeout", "30", "--output", str(partial), url])
            attempt = {"archive": name, "started_utc": started, "ended_utc": utc(), "returncode": result.returncode,
                       "partial_bytes": partial.stat().st_size if partial.exists() else 0}
            attempts.append(attempt)
            registry_path.write_text(json.dumps({"attempts": attempts}, indent=2) + "\n", encoding="utf-8")
            if result.returncode or not partial.exists() or partial.stat().st_size != expected:
                raise RuntimeError(f"DOWNLOAD_FAILURE {name}: {attempt}")
            os.replace(partial, final)
            status = "DOWNLOADED"
        identities.append({"archive": name, "url": url, "role": role, "expected_bytes": expected,
                           "actual_bytes": final.stat().st_size, "sha256": sha256_file(final),
                           "head": meta, "status": status})
        identity_path.write_text(json.dumps({"status": "IN_PROGRESS", "archives": identities}, indent=2) + "\n", encoding="utf-8")
    present_names = {p.name for p in ARCHIVE_CACHE.glob("*.7z")}
    if present_names != {a[0] for a in ASSETS} or present_names.intersection(DENYLIST):
        raise RuntimeError(f"ARCHIVE_CACHE_BOUNDARY_FAILURE: {sorted(present_names)}")
    identity_path.write_text(json.dumps({"status": "PASS", "downloaded_payload_bytes": sum(p.stat().st_size for p in ARCHIVE_CACHE.glob("*.7z")),
                                         "archives": identities}, indent=2) + "\n", encoding="utf-8")
    print("PASS_FROZEN_DOWNLOADS", len(identities), sum(i["actual_bytes"] for i in identities))


if __name__ == "__main__":
    main()
