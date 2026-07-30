#!/usr/bin/env python3
"""Freeze official ScanNet++ authority only after access preflight passes."""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--access-record", type=Path, required=True)
    parser.add_argument("--authority-root", type=Path, required=True)
    args = parser.parse_args()
    access = json.loads(args.access_record.read_text(encoding="utf-8"))
    if access["status"] != "PASS":
        raise RuntimeError("BLOCKED_BY_SCANNETPP_OFFICIAL_ACCESS:do_not_clone_or_substitute_authority")
    args.authority_root.mkdir(parents=True, exist_ok=False)
    for name, url in (("scannetpp", access["official_urls"]["toolbox"]), ("3DGS-demo", access["official_urls"]["demo"])):
        subprocess.run(["git", "clone", "--recurse-submodules", url, str(args.authority_root / name)], check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
