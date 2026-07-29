"""Validate the corrected PR #61 metadata after the one allowed repair."""
from __future__ import annotations

import json
import subprocess

from arkitscenes_handoff_common import LOCAL_ROOT, PR61_HEAD, TASK_ID, write_json


def main() -> None:
    completed = subprocess.run(
        ["gh", "pr", "view", "61", "--repo", "kenqiana04/safer-splat", "--json", "state,isDraft,headRefName,headRefOid,mergeable,mergeStateStatus,body"],
        check=True, capture_output=True, text=True,
    )
    pr = json.loads(completed.stdout)
    assert pr["state"] == "OPEN" and pr["isDraft"] is True
    assert pr["headRefName"] == "local-external-gs-acquisition-handoff-v1"
    assert pr["headRefOid"] == PR61_HEAD
    assert pr["mergeable"] == "MERGEABLE" and pr["mergeStateStatus"] == "CLEAN"
    assert "NO_EXTERNAL_GS_CANDIDATE_QUALIFIED_FOR_DOWNLOAD" in pr["body"]
    assert "DO_NOT_DOWNLOAD_AN_UNQUALIFIABLE_SCENE" in pr["body"]
    assert "SELECT_FREEZE_AND_PACKAGE_ARKITSCENES_GS_WITH_OFFICIAL_RGBD_JOIN_V1" in pr["body"]
    value = {"task_id": TASK_ID, "status": "PASS_PR61_RESOLVED_LINEAGE", "pr61": {key: pr[key] for key in pr if key != "body"}, "body_corrected": True}
    write_json(LOCAL_ROOT / "authority" / "pr61_lineage_audit.json", value)
    print("PR61_LINEAGE_PASS")


if __name__ == "__main__":
    main()
