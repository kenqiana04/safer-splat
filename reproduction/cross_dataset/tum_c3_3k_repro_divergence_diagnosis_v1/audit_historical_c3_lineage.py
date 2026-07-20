"""Read-only historical C3/R0 asset and fresh-start lineage audit."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def purpose(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".ckpt"):
        return "checkpoint"
    if name in {"config.yml", "config.yaml"}:
        return "config"
    if "metric" in name or name.endswith(".json"):
        return "metric_or_manifest"
    if name.endswith((".log", ".out", ".err")):
        return "training_log"
    if name.endswith(".py"):
        return "historical_source"
    return "supporting_artifact"


def attempt(path: Path) -> str:
    text = str(path)
    for label in ("screen3000_depth_wrapper_retry2", "screen3000", "seed20260716_10000", "R0_repro3000_retry2", "R0_screen6000_retry1"):
        if label in text:
            return label
    return "unclassified"


def step(path: Path) -> int | None:
    match = re.search(r"step-(\d+)", path.name)
    return int(match.group(1)) if match else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root-cause-root", type=Path, required=True)
    parser.add_argument("--refinement-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    records: list[dict[str, object]] = []
    gaps: list[str] = []
    for root, commit in ((args.root_cause_root, "fe78814ca0b9e7c840aa99214fa6cd41e4021c5e"), (args.refinement_root, "e5a61d58ace537494a7f00839b60b1fae306da01")):
        if not root.is_dir():
            gaps.append(f"missing historical root: {root}")
            continue
        for item in sorted(root.rglob("*")):
            if not item.is_file():
                continue
            readable = os.access(item, os.R_OK)
            stat = item.stat()
            records.append({
                "absolute_path": str(item), "size": stat.st_size,
                "sha256": sha256(item) if readable else None,
                "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "purpose": purpose(item), "associated_attempt": attempt(item),
                "step": step(item), "readable": readable, "source_commit": commit,
                "evidence_strength": "strong" if item.suffix in {".ckpt", ".yml", ".json", ".py"} else "supporting",
            })
    required_tokens = ("screen3000_depth_wrapper_retry2", "step-000002999.ckpt", "seed20260716_10000", "R0_repro3000_retry2")
    names = "\n".join(str(item["absolute_path"]) for item in records)
    gaps.extend(f"required historical evidence not found: {token}" for token in required_tokens if token not in names)
    result = {"records": records, "historical_evidence_gaps": gaps}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"records": len(records), "historical_evidence_gaps": gaps}, sort_keys=True))


if __name__ == "__main__":
    main()
