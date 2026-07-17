#!/usr/bin/env python3
"""Hash compact execution evidence only; checkpoints/logs/renders stay remote."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    excluded = {"execution_bundle_sha256.json"}
    files = {
        str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path)
        for path in sorted(ROOT.rglob("*"))
        if path.is_file() and path.name not in excluded and "__pycache__" not in path.parts
    }
    payload = {"status": "BLOCKED_BY_PROTOCOL_HASH_MISMATCH", "files": files, "excluded": sorted(excluded), "large_artifacts_in_git": False}
    (ROOT / "execution_bundle_sha256.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("bundle_files=" + str(len(files)))


if __name__ == "__main__":
    main()
