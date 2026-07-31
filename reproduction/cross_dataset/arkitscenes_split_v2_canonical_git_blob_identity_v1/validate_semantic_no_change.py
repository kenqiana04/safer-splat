"""Verify that corrected manifests retain every PR #68 CSV field and row."""

from __future__ import annotations

import argparse
from pathlib import Path

from canonical_identity_common import (HELDOUT_RELATIVE, PR68, TRAIN_RELATIVE, git_blob,
    semantic_csv_identity, write_json)


def compare(repo: Path, relative: Path) -> dict[str, object]:
    _, original = git_blob(repo, PR68, relative)
    corrected = (repo / relative).read_bytes()
    before, after = semantic_csv_identity(original), semantic_csv_identity(corrected)
    return {
        "path": relative.as_posix(),
        "old_semantic_csv_sha256": before["semantic_csv_sha256"],
        "new_semantic_csv_sha256": after["semantic_csv_sha256"],
        "fieldnames_equal": before["fieldnames"] == after["fieldnames"],
        "ordered_rows_equal": before["payload"]["ordered_rows"] == after["payload"]["ordered_rows"],
        "row_count_before": before["row_count"],
        "row_count_after": after["row_count"],
        "semantic_change_count": sum(a != b for a, b in zip(before["payload"]["ordered_rows"], after["payload"]["ordered_rows"])) + abs(before["row_count"] - after["row_count"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--repo", type=Path, required=True); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args()
    results = [compare(args.repo, TRAIN_RELATIVE), compare(args.repo, HELDOUT_RELATIVE)]
    valid = all(item["fieldnames_equal"] and item["ordered_rows_equal"] and item["semantic_change_count"] == 0 for item in results)
    payload = {"status": "PASS_SEMANTIC_NO_CHANGE" if valid else "BLOCKED_BY_NON_EOL_MANIFEST_CONTENT_MISMATCH", "pr68_commit": PR68, "semantic_change_count": sum(int(item["semantic_change_count"]) for item in results), "manifests": results}
    write_json(args.output, payload); print(payload["status"])
    return 0 if valid else 2


if __name__ == "__main__": raise SystemExit(main())
