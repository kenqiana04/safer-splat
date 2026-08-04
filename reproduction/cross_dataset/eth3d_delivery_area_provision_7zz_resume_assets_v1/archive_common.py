#!/usr/bin/env python3
"""Deterministic hashing and 7zz SLT safety helpers."""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path, PurePosixPath


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tree_identity(root: Path) -> dict:
    rows: list[dict] = []
    digest = hashlib.sha256()
    for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        size = path.stat().st_size
        file_sha = sha256_file(path)
        mode = os.stat(path, follow_symlinks=False).st_mode & 0o777
        digest.update(rel.encode("utf-8") + b"\0" + str(size).encode() + b"\0" + file_sha.encode() + b"\0" + oct(mode).encode() + b"\n")
        rows.append({"path": rel, "size": size, "sha256": file_sha, "mode": oct(mode)})
    return {"tree_sha256": digest.hexdigest(), "file_count": len(rows), "total_bytes": sum(r["size"] for r in rows), "files": rows}


def parse_slt(text: str) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for raw in text.splitlines():
        if not raw.strip():
            if current:
                records.append(current)
                current = {}
            continue
        if " = " in raw:
            key, value = raw.split(" = ", 1)
            current[key] = value
    if current:
        records.append(current)
    return records


def audit_slt(records: list[dict[str, str]], archive_size: int, max_ratio: float = 1000.0) -> dict:
    entries = [r for r in records if "Path" in r and "Type" not in r]
    seen: set[str] = set()
    folded: set[str] = set()
    issues: list[dict] = []
    total_size = 0
    for record in entries:
        raw = record["Path"].replace("\\", "/")
        pure = PurePosixPath(raw)
        parts = pure.parts
        normalized = pure.as_posix()
        attrs = record.get("Attributes", "")
        size = int(record.get("Size", "0") or 0)
        total_size += size
        if raw.startswith("/") or re.match(r"^[A-Za-z]:", raw):
            issues.append({"path": raw, "code": "ABSOLUTE_PATH"})
        if ".." in parts:
            issues.append({"path": raw, "code": "PARENT_TRAVERSAL"})
        if normalized in seen:
            issues.append({"path": raw, "code": "DUPLICATE_NORMALIZED_PATH"})
        if normalized.casefold() in folded:
            issues.append({"path": raw, "code": "CASEFOLD_COLLISION"})
        seen.add(normalized)
        folded.add(normalized.casefold())
        if record.get("Symbolic Link") or attrs.startswith("l") or record.get("Hard Link"):
            issues.append({"path": raw, "code": "LINK_ENTRY"})
        if attrs[:1].lower() in {"b", "c", "p", "s"}:
            issues.append({"path": raw, "code": "SPECIAL_DEVICE_ENTRY"})
        packed = int(record.get("Packed Size", "0") or 0)
        if packed > 0 and size / packed > max_ratio:
            issues.append({"path": raw, "code": "ENTRY_COMPRESSION_RATIO", "ratio": size / packed})
    total_ratio = total_size / max(archive_size, 1)
    if total_ratio > max_ratio:
        issues.append({"path": "<archive>", "code": "TOTAL_COMPRESSION_RATIO", "ratio": total_ratio})
    return {"status": "PASS" if not issues else "FAIL", "entry_count": len(entries), "total_uncompressed_bytes": total_size, "total_ratio": total_ratio, "issues": issues, "entries": entries}
