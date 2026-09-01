#!/usr/bin/env python3
"""Hash raw trial artifacts without interpreting scientific content."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from collection_common import DATA_ROLE, PROTOCOL_SHA256, atomic_write_json, file_sha256, load_json, semantic_sha256


def build(attempt_root: Path, output_csv: Path) -> dict[str, object]:
    identity = load_json(attempt_root / "formal_attempt_identity.json")
    trial_id = int(identity["trial_id"])
    attempt_id = int(identity["attempt_id"])
    run_id = identity["run_id"]
    attempt_prefix = f"formal-v1/trial-{trial_id:03d}/attempt-{attempt_id}"
    rows = []
    for path in sorted(item for item in attempt_root.rglob("*") if item.is_file() and item.resolve() != output_csv.resolve()):
        rows.append({
            "trial_id": trial_id,
            "run_id": run_id,
            "attempt_id": attempt_id,
            "artifact_type": "RAW_JSONL" if path.suffix == ".jsonl" else "LOG" if path.suffix == ".log" else "TASK_RECORD",
            "server_relative_path": f"{attempt_prefix}/{path.relative_to(attempt_root).as_posix()}",
            "size_bytes": path.stat().st_size,
            "sha256": file_sha256(path),
            "protocol_sha": PROTOCOL_SHA256,
            "collection_execution_sha": identity["collection_execution_lock_sha256"],
            "data_role": DATA_ROLE,
            "retention": "SERVER_ONLY_RAW" if path.suffix in {".jsonl", ".log"} else "SERVER_TASK_RECORD",
        })
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=(
            "trial_id", "run_id", "attempt_id", "artifact_type", "server_relative_path", "size_bytes",
            "sha256", "protocol_sha", "collection_execution_sha", "data_role", "retention",
        ), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "schema_version": "L2_H1_RAW_ATTEMPT_ARTIFACT_MANIFEST_V1",
        "artifact_count": len(rows),
        "artifact_manifest_sha256": file_sha256(output_csv),
        "ordered_artifact_commitment_sha256": semantic_sha256(rows),
        "scientific_content_interpreted": False,
    }
    atomic_write_json(output_csv.with_suffix(".summary.json"), summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attempt-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = build(args.attempt_root.resolve(strict=True), args.output.resolve())
    print(f"artifacts={summary['artifact_count']} manifest_sha256={summary['artifact_manifest_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
