#!/usr/bin/env python3
"""Extract validated archives into isolated quarantine trees."""

from __future__ import annotations

import collections
import json
import shutil
import subprocess

from archive_common import tree_identity
from task_config import ARCHIVE_CACHE, ASSETS, DISK_LIMIT_BYTES, QUARANTINE, SEVEN_Z, TASK_ROOT


def disk_usage(path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file()) if path.exists() else 0


def main() -> None:
    security = json.loads((TASK_ROOT / "archive_security_audit.json").read_text(encoding="utf-8"))
    if security["status"] != "PASS":
        raise RuntimeError("SECURITY_GATE_NOT_PASS")
    outputs: list[dict] = []
    for name, expected, role in ASSETS:
        if not name.endswith(".7z"):
            raise RuntimeError(f"UNEXPECTED_ARCHIVE_SUFFIX {name}")
        out = QUARANTINE / name[:-3]
        if out.exists():
            resolved = out.resolve()
            if QUARANTINE.resolve() not in resolved.parents:
                raise RuntimeError(f"UNSAFE_DELETE_TARGET {out}")
            shutil.rmtree(out)
        out.mkdir(parents=True)
        result = subprocess.run([str(SEVEN_Z), "x", "-y", f"-o{out}", str(ARCHIVE_CACHE / name)],
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (TASK_ROOT / "logs" / f"extract_{name}.txt").write_text(result.stdout, encoding="utf-8")
        if result.returncode:
            raise RuntimeError(f"EXTRACTION_FAILURE {name}")
        identity = tree_identity(out)
        ext = collections.Counter((p.suffix.lower() or "<none>") for p in out.rglob("*") if p.is_file())
        largest = sorted((p for p in out.rglob("*") if p.is_file()), key=lambda p: p.stat().st_size, reverse=True)[:10]
        outputs.append({"archive": name, "role": role, **{k: identity[k] for k in ("tree_sha256", "file_count", "total_bytes")},
                        "extensions": dict(sorted(ext.items())),
                        "largest_files": [{"path": p.relative_to(out).as_posix(), "size": p.stat().st_size} for p in largest]})
        (TASK_ROOT / "extracted_tree_identity.json").write_text(json.dumps({"status": "IN_PROGRESS", "archives": outputs}, indent=2) + "\n", encoding="utf-8")
        if disk_usage(ARCHIVE_CACHE.parent) + disk_usage(TASK_ROOT) > DISK_LIMIT_BYTES:
            raise RuntimeError("BLOCKED_BY_ETH3D_DISK_BUDGET")
    (TASK_ROOT / "extracted_tree_identity.json").write_text(json.dumps({"status": "PASS", "archives": outputs}, indent=2) + "\n", encoding="utf-8")
    print("PASS_SAFE_EXTRACTION", len(outputs), sum(x["total_bytes"] for x in outputs))


if __name__ == "__main__":
    main()
