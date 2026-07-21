"""Fail closed unless a prior extraction establishes all common-map semantics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--summary", type=Path, required=True); a = p.parse_args()
    summary = json.loads(a.summary.read_text(encoding="utf-8"))
    if summary.get("status") != "COMMON_ADAPTER_VERIFIED":
        print("COMMON_ADAPTER_UNRESOLVED")
        return
    raise RuntimeError("COMMON_ADAPTER_VERIFIED_REQUIRES_SEPARATE_STATIC_AUDIT")


if __name__ == "__main__": main()
