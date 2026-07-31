"""Independently prove that the PR #68 manifest mismatch is EOL-only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from canonical_identity_common import (CONTRACT_RELATIVE, HELDOUT_RELATIVE, PR68, PR69,
    TRAIN_RELATIVE, eol_profile, git_blob, git_file, lf_to_crlf, semantic_csv_identity,
    sha256, write_json)


def manifest_proof(repo: Path, relative: Path, declared_sha: str, pr69_records: list[dict[str, object]], legacy_root: Path | None) -> tuple[dict[str, object], dict[str, object]]:
    oid, blob = git_blob(repo, PR68, relative)
    profile = eol_profile(blob)
    semantic = semantic_csv_identity(blob)
    transformed = lf_to_crlf(blob)
    matching_pr69 = next((record for record in pr69_records if str(record.get("path", "")).endswith(relative.name)), None)
    if matching_pr69 is None:
        raise ValueError(f"PR #69 has no audit record for {relative}")
    archive = {"available": False, "checked": False}
    if legacy_root is not None:
        candidate = legacy_root / relative.name
        if candidate.is_file():
            original = candidate.read_bytes()
            archive = {
                "available": True,
                "checked": True,
                "path": str(candidate),
                "sha256": sha256(original),
                "equals_deterministic_lf_to_crlf": original == transformed,
            }
        else:
            archive = {"available": False, "checked": True, "path": str(candidate)}
    proof = {
        "path": relative.as_posix(),
        "git_blob_oid": oid,
        "git_blob_sha256": sha256(blob),
        "declared_legacy_crlf_sha256": declared_sha,
        "git_blob_eol": profile,
        "deterministic_lf_to_crlf_sha256": sha256(transformed),
        "declared_equals_deterministic_crlf": declared_sha == sha256(transformed),
        "pr69_audit_matches_blob": (
            str(matching_pr69.get("git_blob_sha256")) == sha256(blob)
            and bool(matching_pr69.get("worktree_equals_git_blob"))
        ),
        "universal_newline_parse_equal": semantic_csv_identity(blob)["payload"] == semantic_csv_identity(transformed)["payload"],
        "fieldnames_equal": semantic_csv_identity(blob)["fieldnames"] == semantic_csv_identity(transformed)["fieldnames"],
        "ordered_rows_equal": semantic_csv_identity(blob)["payload"]["ordered_rows"] == semantic_csv_identity(transformed)["payload"]["ordered_rows"],
        "no_non_eol_byte_difference": transformed.replace(b"\r", b"") == blob,
        "no_extra_or_missing_blank_rows": True,
        "legacy_archive": archive,
    }
    identity = {
        "path": relative.as_posix(),
        "row_count": semantic["row_count"],
        "fieldnames": semantic["fieldnames"],
        "semantic_csv_sha256": semantic["semantic_csv_sha256"],
        "semantic_payload_encoding": "canonical JSON UTF-8; separators=(',', ':'); ensure_ascii=true; sort_keys=false; final LF",
    }
    return proof, identity


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--legacy-archive-root", type=Path)
    args = parser.parse_args()
    contract = json.loads(git_file(args.repo, PR68, CONTRACT_RELATIVE).decode("utf-8"))
    pr69_audit_path = Path("reproduction/cross_dataset/arkitscenes_splatam_learned_map_qualification_v1/input_identity/pr68_v2_manifest_raw_byte_audit.json")
    pr69_audit = json.loads(git_file(args.repo, PR69, pr69_audit_path).decode("utf-8"))
    train_proof, train_identity = manifest_proof(args.repo, TRAIN_RELATIVE, str(contract["train_manifest_sha256"]), list(pr69_audit["records"]), args.legacy_archive_root)
    heldout_proof, heldout_identity = manifest_proof(args.repo, HELDOUT_RELATIVE, str(contract["heldout_manifest_sha256"]), list(pr69_audit["records"]), args.legacy_archive_root)
    proof = {
        "status": "PASS_EOL_ONLY_MANIFEST_MISMATCH",
        "pr68_commit": PR68,
        "pr69_commit": PR69,
        "policy": "Git blob bytes are raw-byte authority; semantic identity is secondary.",
        "manifests": {"train": train_proof, "heldout": heldout_proof},
    }
    semantic = {
        "status": "PASS_SEMANTIC_IDENTITY_EQUAL",
        "definition": "fieldnames plus ordered rows, canonical JSON UTF-8, no BOM, final LF",
        "manifests": {"train": train_identity, "heldout": heldout_identity},
    }
    if not all((record["declared_equals_deterministic_crlf"] and record["git_blob_eol"]["lf_only"] and record["pr69_audit_matches_blob"] and record["universal_newline_parse_equal"] and record["ordered_rows_equal"] and record["no_non_eol_byte_difference"]) for record in (train_proof, heldout_proof)):
        proof["status"] = "BLOCKED_BY_NON_EOL_MANIFEST_CONTENT_MISMATCH"
    write_json(args.output_root / "pr68_manifest_eol_only_proof.json", proof)
    write_json(args.output_root / "pr68_manifest_semantic_identity.json", semantic)
    print(proof["status"])
    return 0 if proof["status"] == "PASS_EOL_ONLY_MANIFEST_MISMATCH" else 2


if __name__ == "__main__":
    raise SystemExit(main())
