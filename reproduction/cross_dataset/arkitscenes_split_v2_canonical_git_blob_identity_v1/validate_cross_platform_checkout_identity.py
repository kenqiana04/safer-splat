"""Check one checkout platform against the same commit's authoritative blobs."""

from __future__ import annotations

import argparse
from pathlib import Path

from canonical_identity_common import (HELDOUT_RELATIVE, TRAIN_RELATIVE, eol_profile, git_blob,
    sha256, write_json)


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--repo", type=Path, required=True); parser.add_argument("--commit", required=True); parser.add_argument("--platform", required=True); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args()
    entries = []
    for relative in (TRAIN_RELATIVE, HELDOUT_RELATIVE):
        oid, blob = git_blob(args.repo, args.commit, relative); working = (args.repo / relative).read_bytes()
        entries.append({"path": relative.as_posix(), "git_blob_oid": oid, "git_blob_sha256": sha256(blob), "working_tree_sha256": sha256(working), "working_tree_equals_git_blob": working == blob, "eol": eol_profile(working)})
    valid = all(item["working_tree_equals_git_blob"] and item["eol"]["lf_only"] and item["eol"]["final_lf"] for item in entries)
    payload = {"status": "PASS_CROSS_PLATFORM_CHECKOUT_IDENTITY" if valid else "BLOCKED_BY_CROSS_PLATFORM_MANIFEST_IDENTITY_CANONICALIZATION", "platform": args.platform, "commit": args.commit, "entries": entries}
    write_json(args.output, payload); print(payload["status"])
    return 0 if valid else 2


if __name__ == "__main__": raise SystemExit(main())
