#!/usr/bin/env python3
"""Small, deterministic helpers for the frozen ARKitScenes qualification."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def run(command: list[str], *, cwd: Path | None = None, timeout: int = 60) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, text=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, timeout=timeout, check=False)
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }


def git_head(repo: Path) -> str:
    result = run(["git", "rev-parse", "HEAD"], cwd=repo)
    if result["returncode"] != 0:
        raise RuntimeError(f"git head unavailable: {result['stderr_tail']}")
    return str(result["stdout_tail"]).strip()


def tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(rel).to_bytes(8, "big"))
        digest.update(rel)
        digest.update(path.stat().st_size.to_bytes(8, "big"))
        digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()
