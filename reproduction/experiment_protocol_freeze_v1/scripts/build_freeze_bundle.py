#!/usr/bin/env python3
"""Write a deterministic SHA-256 manifest for the protocol-freeze bundle."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parents[1]
MANIFEST = OUT / "freeze_bundle_sha256.json"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    rows = []
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and path != MANIFEST and "__pycache__" not in path.parts:
            rows.append({"path": path.relative_to(OUT).as_posix(), "sha256": digest(path), "size_bytes": path.stat().st_size})
    MANIFEST.write_text(json.dumps({"algorithm": "sha256", "files": rows}, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
