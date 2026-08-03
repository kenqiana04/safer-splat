#!/usr/bin/env python3
"""Validate frozen HEAD-only metadata without touching archive bodies."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.task_root.resolve()
    head = json.loads((root / "asset_manifest/http_head_validation.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "asset_manifest/official_asset_manifest.json").read_text(encoding="utf-8"))
    checks = {
        "head_status_pass": head["status"] == "PASS",
        "fourteen_unique_archives": head["head_count"] == 14 == len(manifest),
        "head_only": head["method"] == "HEAD_ONLY" and all(x["method"] == "HEAD" for x in head["records"]),
        "zero_body_bytes": head["response_body_bytes"] == 0 and all(x["response_body_bytes"] == 0 for x in head["records"]),
        "http_200": all(x["http_status"] == 200 for x in head["records"]),
        "content_lengths_positive": all((x["content_length"] or "").isdigit() and int(x["content_length"]) > 0 for x in head["records"]),
        "official_page_matches": all(x["official_page_match"] for x in manifest),
        "archive_mime": all(x["mime"] == "application/x-7z-compressed" for x in manifest),
        "no_archive_file_in_task_root": not any(root.rglob("*.7z")),
    }
    result = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
