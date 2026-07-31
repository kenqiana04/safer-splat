"""Run the frozen V2 producer in three fresh processes and compare exact semantics."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from canonical_identity_common import (HELDOUT_RELATIVE, PR68, TRAIN_RELATIVE, V2_ROOT,
    eol_profile, file_tree_sha256, git_blob, semantic_csv_identity, sha256, write_json)


def run_once(repo: Path, script_root: Path, v1_root: Path) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="arkitscenes_v2_lf_regen_") as temporary:
        root = Path(temporary)
        shutil.copytree(script_root / "feasibility", root / "feasibility")
        shutil.copytree(script_root / "group_reconstruction/48018874", root / "group_reconstruction/48018874")
        command = [sys.executable, "-B", str(script_root / "freeze_arkitscenes_spatial_group_split_v2.py"), "--task-root", str(root), "--v1-root", str(v1_root)]
        result = subprocess.run(command, cwd=repo, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"fresh producer failed: {result.stdout}\n{result.stderr}")
        split = root / "v2_split"
        train, heldout = split / TRAIN_RELATIVE.name, split / HELDOUT_RELATIVE.name
        return {
            "stdout": result.stdout.strip(),
            "train_sha256": sha256(train.read_bytes()),
            "heldout_sha256": sha256(heldout.read_bytes()),
            "train_eol": eol_profile(train.read_bytes()),
            "heldout_eol": eol_profile(heldout.read_bytes()),
            "train_semantic_sha256": semantic_csv_identity(train.read_bytes())["semantic_csv_sha256"],
            "heldout_semantic_sha256": semantic_csv_identity(heldout.read_bytes())["semantic_csv_sha256"],
            "tree_sha256": file_tree_sha256([train, heldout], split),
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    script_root = args.repo / V2_ROOT
    v1_root = args.repo / "reproduction/cross_dataset/arkitscenes_raw_splatam_learned_3dgs_qualification_v1"
    _, old_train = git_blob(args.repo, PR68, TRAIN_RELATIVE)
    _, old_heldout = git_blob(args.repo, PR68, HELDOUT_RELATIVE)
    expected = {
        "train_semantic_sha256": semantic_csv_identity(old_train)["semantic_csv_sha256"],
        "heldout_semantic_sha256": semantic_csv_identity(old_heldout)["semantic_csv_sha256"],
    }
    runs = [run_once(args.repo, script_root, v1_root) for _ in range(3)]
    valid = all(run["train_eol"]["lf_only"] and run["heldout_eol"]["lf_only"] and run["train_eol"]["final_lf"] and run["heldout_eol"]["final_lf"] for run in runs)
    valid &= len({str(run["train_sha256"]) for run in runs}) == 1 and len({str(run["heldout_sha256"]) for run in runs}) == 1 and len({str(run["tree_sha256"]) for run in runs}) == 1
    valid &= all(run["train_semantic_sha256"] == expected["train_semantic_sha256"] and run["heldout_semantic_sha256"] == expected["heldout_semantic_sha256"] for run in runs)
    payload = {"status": "PASS_FRESH_LF_REGENERATION" if valid else "BLOCKED_BY_CROSS_PLATFORM_MANIFEST_IDENTITY_CANONICALIZATION", "fresh_process_count": 3, "expected_pr68_semantic_identity": expected, "runs": [{"run": index + 1, **run} for index, run in enumerate(runs)], "precommit_note": "PRECOMMIT_GENERATED_SHA_IS_NOT_YET_GIT_BLOB_AUTHORITY"}
    write_json(args.output, payload)
    print(payload["status"])
    return 0 if valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
