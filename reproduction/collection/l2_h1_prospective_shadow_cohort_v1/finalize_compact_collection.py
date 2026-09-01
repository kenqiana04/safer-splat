#!/usr/bin/env python3
"""Create compact, outcome-blind server manifests after the collection lock."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from collection_common import DATA_ROLE, atomic_write_json, file_sha256, load_json, semantic_sha256


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.server_root.resolve(strict=True)
    progress = load_json(root / "formal_collection_progress.json")
    if progress.get("state") != "LOCKED" or progress.get("completed_trial_count") != 100:
        raise RuntimeError("formal collection is not locked at 100/100")
    passed = sorted(
        (row for row in progress["trials"] if row.get("state") == "PASSED_OUTCOME_BLIND_QC"),
        key=lambda row: int(row["trial_id"]),
    )
    if [int(row["trial_id"]) for row in passed] != list(range(100)):
        raise RuntimeError("formal trial coverage/order mismatch")

    combined_rows = []
    per_attempt = []
    for record in passed:
        path = Path(record["raw_artifact_manifest_path"])
        if not path.is_file():
            raise RuntimeError(f"missing raw artifact manifest: {path}")
        with path.open("r", encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        for row in rows:
            if row.get("data_role") != DATA_ROLE or int(row["trial_id"]) != int(record["trial_id"]) or row.get("run_id") != record["run_id"]:
                raise RuntimeError(f"raw manifest identity mismatch: {path}")
            artifact = root / row["server_relative_path"]
            if not artifact.is_file() or artifact.stat().st_size != int(row["size_bytes"]) or file_sha256(artifact) != row["sha256"]:
                raise RuntimeError(f"raw artifact resolution/hash mismatch: {artifact}")
        combined_rows.extend(rows)
        per_attempt.append({
            "trial_id": int(record["trial_id"]), "attempt_id": int(record["attempt_id"]), "run_id": record["run_id"],
            "manifest_server_path": str(path), "manifest_sha256": file_sha256(path), "artifact_count": len(rows),
        })

    output = root / "raw_artifact_manifest.csv"
    fieldnames = (
        "trial_id", "run_id", "attempt_id", "artifact_type", "server_relative_path", "size_bytes",
        "sha256", "protocol_sha", "collection_execution_sha", "data_role", "retention",
    )
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(combined_rows)
    (root / "raw_artifact_manifest.sha256").write_text(file_sha256(output) + "\n", encoding="ascii", newline="\n")
    index = {
        "schema_version": "L2_H1_FORMAL_RAW_ARTIFACT_INDEX_V1",
        "data_role": DATA_ROLE,
        "formal_trial_count": 100,
        "raw_artifact_count": len(combined_rows),
        "per_attempt_manifest_count": len(per_attempt),
        "per_attempt_manifests": per_attempt,
        "combined_raw_artifact_manifest_sha256": file_sha256(output),
        "ordered_raw_artifact_commitment_sha256": semantic_sha256(combined_rows),
        "scientific_content_interpreted": False,
    }
    atomic_write_json(root / "raw_artifact_manifest_index.json", index)

    lock = load_json(root / "FORMAL_COLLECTION_LOCK.json")
    execution = load_json(root / "COLLECTION_EXECUTION_LOCK.json")
    summary = load_json(root / "collection_qc_summary.json")
    result_commitment = load_json(root / "scientific_outcome_artifact_commitment.json")
    metadata = {
        "schema_version": "L2_H1_FORMAL_COLLECTION_LOCK_METADATA_V1",
        "collection_version": "V1",
        "data_role": DATA_ROLE,
        "upstream_PR100_head": execution["upstream_head"],
        "protocol_lock_sha": execution["protocol_sha256"],
        "collection_execution_lock_sha": execution["combined_collection_execution_sha256"],
        "official100_manifest_sha": execution["official100_sha256"],
        "formal_trial_count": 100, "unique_trial_count": 100, "completed_trial_count": 100,
        "ordered_formal_run_ids": lock["formal_run_ids"],
        "attempt_ids": [int(record["attempt_id"]) for record in passed],
        "pre_data_retry_count": summary["pre_data_retry_count"],
        "post_data_deviation_count": summary["post_data_failure_count"],
        "environment_identity_sha256": execution["environment_identity_sha256"],
        "map_authority_id": execution["map_authority_id"],
        "raw_artifact_manifest_sha": index["combined_raw_artifact_manifest_sha256"],
        "combined_raw_artifact_commitment": index["ordered_raw_artifact_commitment_sha256"],
        "combined_result_artifact_commitment": result_commitment["ordered_result_commitment_sha256"],
        "per_trial_blind_qc_pass_count": 100,
        "collection_deviation_count": len(lock["collection_deviations"]),
        "controller_intervention_count": 0, "candidate_replacement_count": 0,
        "scientific_analysis_performed": False, "outcome_distribution_exposed": False,
        "formal_collection_lock_sha256": file_sha256(root / "FORMAL_COLLECTION_LOCK.json"),
    }
    metadata["combined_formal_collection_lock_metadata_sha256"] = semantic_sha256(metadata)
    atomic_write_json(root / "FORMAL_COLLECTION_LOCK_METADATA.json", metadata)
    print(json.dumps({
        "status": "PASS_COMPACT_OUTCOME_BLIND_FINALIZATION",
        "formal_trial_count": 100,
        "raw_artifact_count": len(combined_rows),
        "raw_artifact_manifest_sha256": index["combined_raw_artifact_manifest_sha256"],
        "scientific_analysis_performed": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
