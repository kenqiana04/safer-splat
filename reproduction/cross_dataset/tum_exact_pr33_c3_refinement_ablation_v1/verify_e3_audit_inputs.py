"""Small raw-byte identity helpers for the E3 static SAFER audit."""
from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_identity(path: Path) -> dict[str, object]:
    stat = path.stat()
    return {"path": str(path), "exists": path.is_file(), "sha256": sha256_file(path), "size": stat.st_size, "mtime_ns": stat.st_mtime_ns}
