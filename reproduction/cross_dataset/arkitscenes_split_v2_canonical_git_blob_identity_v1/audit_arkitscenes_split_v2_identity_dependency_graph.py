"""Classify old manifest-hash references without changing historical PR #69 evidence."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from canonical_identity_common import PR69, V2_ROOT, git_file, write_json


OLD = {"b2d66720fbb0bc7acc998a81e073a9e4774ece7e3ce2900651ff28bf921c2404", "670255f2e00f04a0e462e1a83cd4c4d0344e92906604aba9312aa7baabb3b78e"}
PR69_ROOT = Path("reproduction/cross_dataset/arkitscenes_splatam_learned_map_qualification_v1")


def classify(relative: Path) -> str:
    if relative.is_relative_to(PR69_ROOT): return "D_HISTORICAL_PR69_IMMUTABLE"
    if relative.is_relative_to(V2_ROOT):
        if relative in {
            V2_ROOT / "v2_split/arkitscenes_spatial_group_split_contract_v2.json",
            V2_ROOT / "v2_split/selected_arkitscenes_mapping_scene_v2.json",
            V2_ROOT / "validation/fresh_process_reproducibility.json",
            V2_ROOT / "run_manifest.json",
            V2_ROOT / "downstream_handoff.json",
        }:
            return "A_RAW_BYTE_IDENTITY_DEPENDENT"
        return "D_LEGACY_OR_AUDIT_EVIDENCE"
    if "arkitscenes_split_v2_canonical_git_blob_identity_v1" in relative.as_posix(): return "D_CORRECTION_EVIDENCE"
    return "UNCLASSIFIED"


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--repo", type=Path, required=True); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args()
    findings = []
    for path in sorted(args.repo.rglob("*")):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts: continue
        try: text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError: continue
        matched = sorted(token for token in OLD if token in text)
        if matched: findings.append({"path": path.relative_to(args.repo).as_posix(), "old_hashes": matched, "classification": classify(path.relative_to(args.repo))})
    pr69_paths = [item["path"] for item in findings if item["classification"] == "D_HISTORICAL_PR69_IMMUTABLE"]
    pr69_unchanged = subprocess.run(["git", "-C", str(args.repo), "diff", "--quiet", PR69, "--", str(PR69_ROOT)], check=False).returncode == 0
    valid = not any(item["classification"] == "UNCLASSIFIED" for item in findings) and pr69_unchanged
    payload = {"status": "PASS_IDENTITY_DEPENDENCY_GRAPH" if valid else "BLOCKED_BY_CROSS_PLATFORM_MANIFEST_IDENTITY_CANONICALIZATION", "old_hashes": sorted(OLD), "findings": findings, "dependency_paths_updated_or_reviewed": [str(V2_ROOT / item) for item in ("v2_split/arkitscenes_spatial_group_split_contract_v2.json", "v2_split/selected_arkitscenes_mapping_scene_v2.json", "validation/fresh_process_reproducibility.json", "run_manifest.json", "downstream_handoff.json", "REPORT_REVISE_ARKITSCENES_SPATIAL_GROUP_SPLIT_CONTRACT_V2.md")], "pr69_paths_byte_identical_to_pr69_commit": pr69_unchanged, "update_rule": "Only raw-byte identity dependents are updated; semantic and selection identities remain unchanged."}
    write_json(args.output, payload); print(payload["status"])
    return 0 if valid else 2


if __name__ == "__main__": raise SystemExit(main())
