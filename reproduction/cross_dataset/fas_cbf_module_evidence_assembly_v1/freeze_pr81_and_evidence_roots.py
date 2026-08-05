#!/usr/bin/env python3
"""Freeze PR #81 and the permitted compact evidence roots."""
from __future__ import annotations

from evidence_common import (BASE_HEAD, ETH3D_BASELINE_SHA, ETH3D_MAP_SHA, ETH3D_MESH_SHA, ETH3D_METHOD_SHA, ETH3D_TREE_SHA, PR79_HEAD, PR80_HEAD, REPO, TASK, ensure_dirs, git_text, write_json)


def main() -> int:
    ensure_dirs()
    if git_text(["rev-parse", "HEAD"]) != BASE_HEAD:
        raise RuntimeError("task branch is not based on frozen PR #81 head")
    if git_text(["rev-parse", f"{BASE_HEAD}^" ]) != PR80_HEAD:
        raise RuntimeError("PR #81 parent is not frozen PR #80 head")
    identity = {
        "task": "ASSEMBLE_FAS_CBF_MODULE_EVIDENCE_FROM_ETH3D_AND_EXISTING_FROZEN_CASES_V1",
        "branch": "fas-cbf-module-evidence-assembly-v1",
        "pr81_head": BASE_HEAD,
        "pr80_head": PR80_HEAD,
        "pr79_head": PR79_HEAD,
        "frozen_eth3d": {"map_ply_sha256": ETH3D_MAP_SHA, "canonical_tree_sha256": ETH3D_TREE_SHA, "reference_mesh_sha256": ETH3D_MESH_SHA, "method_code_sha256": ETH3D_METHOD_SHA, "baseline_core_sha256": ETH3D_BASELINE_SHA},
        "allowed_operations": ["git/report/compact-artifact read", "sha256", "deterministic compact-statistic recomputation", "claim and configuration audit", "compact tables/figures/report"],
        "forbidden_execution": ["map training", "candidate search", "controller rollout", "parameter tuning", "dataset switch", "map/method mutation"],
    }
    write_json(TASK / "input_freeze/pr81_and_source_identity.json", identity)
    write_json(TASK / "operational_autonomy_actions.json", {"action_count": 0, "actions": [], "note": "No task-owned infrastructure repair or scientific execution was required."})
    print("PASS_PR81_AND_EVIDENCE_ROOTS_FROZEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
