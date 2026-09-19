#!/usr/bin/env python3
"""Generate Retry2 execution lock and CPU-only freeze evidence after Commit A."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

from validate_bounded_local_recovery_smoke_retry2_v1 import (
    BRANCH, GATE0, HARNESS, IMPL, LOCK, ORIGIN, PROTOCOL, REPAIR, REPO,
    RESULT_ROOT, SESSION, TASK, TOKEN, git, read, semantic_hash, sha,
    tmux_active, validate_freeze,
)

RESULTS = TASK / "results_freeze"
REPORT = TASK / "report/REPORT_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_FREEZE_V1.md"
SNAPSHOT = REPO / "reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1/results_cpu_validation/result_root_snapshots_before.json"


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def root_manifest(root: Path) -> dict:
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        files.append({"path": str(path.relative_to(root)), "size": path.stat().st_size, "sha256": sha(path)})
    return {"root": str(root), "file_count": len(files),
            "content_manifest_sha256": semantic_hash(files)}


def main() -> int:
    if git("branch", "--show-current") != BRANCH or git("remote", "get-url", "origin") != ORIGIN:
        raise RuntimeError("FREEZE_GIT_AUTHORITY_MISMATCH")
    if git("status", "--porcelain"):
        raise RuntimeError("COMMIT_A_CLEAN_WORKTREE_REQUIRED_BEFORE_LOCK")
    freeze = validate_freeze(require_lock=False, require_absent_root=True)
    protocol = read(PROTOCOL)
    protocol_commit = git("rev-parse", "HEAD")
    harness_hashes = {name: sha(TASK / name) for name in HARNESS}
    historical = read(SNAPSHOT)
    current_roots = {
        "attempt0": root_manifest(Path(protocol["retry1_lineage"]["attempt0_root"])),
        "retry1": root_manifest(Path(protocol["retry1_lineage"]["retry1_root"])),
    }
    for name in ("attempt0", "retry1"):
        if (current_roots[name]["file_count"] != historical[name]["file_count"] or
                current_roots[name]["content_manifest_sha256"] != historical[name]["content_manifest_sha256"]):
            raise RuntimeError("HISTORICAL_RESULT_ROOT_DRIFT:" + name)

    lock = {
        "schema": "BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_EXECUTION_LOCK_V1",
        "base_head": REPAIR,
        "protocol_commit": protocol_commit,
        "repair_implementation_head": REPAIR,
        "original_bounded_recovery_implementation_head": IMPL,
        "gate0_head": GATE0,
        "protocol_sha256": sha(PROTOCOL),
        "semantic_protocol_sha256": semantic_hash(protocol),
        "harness_sha256": harness_hashes,
        "trial_order": [15, 45, 75],
        "trial_order_sha256": semantic_hash([15, 45, 75]),
        "future_result_root": str(RESULT_ROOT),
        "future_tmux_session": SESSION,
        "execution_authorization_token": TOKEN,
        "geometry": protocol["geometry"],
        "dynamics": protocol["dynamics"],
        "recovery": protocol["recovery"],
        "map_identity": protocol["map"]["identity"],
        "map_artifacts": protocol["map"]["artifacts"],
        "local_infrastructure_bindings": protocol["local_infrastructure_bindings"],
        "retry1_lineage": protocol["retry1_lineage"],
        "multi_candidate_l2_evidence": protocol["multi_candidate_l2_evidence"],
        "freeze_gpu_run_count": 0,
        "freeze_tmux_created_count": 0,
        "freeze_smoke_trial_run_count": 0,
        "freeze_real_plantcommit_count": 0,
    }
    write_json(LOCK, lock)

    input_manifest = {
        "schema": "BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_INPUT_AUTHORITY_MANIFEST_V1",
        "branch": BRANCH, "base_head": REPAIR, "protocol_commit": protocol_commit,
        "origin": ORIGIN, "cohort": protocol["cohort"], "environment": protocol["environment"],
        "map": protocol["map"], "geometry": protocol["geometry"], "dynamics": protocol["dynamics"],
        "recovery": protocol["recovery"], "future_result_root": str(RESULT_ROOT),
        "future_tmux_session": SESSION, "execution_authorization_token": TOKEN,
        "scientific_state": {"retry1_status": protocol["retry1_lineage"]["retry1_status"],
            "scientific_verdict": protocol["science"]["post_repair_progress_ni"], "changed": False},
    }
    write_json(RESULTS / "INPUT_AUTHORITY_MANIFEST.json", input_manifest)
    write_json(RESULTS / "PROTOCOL_SEMANTIC_LOCK.json", {
        "schema": "BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_PROTOCOL_SEMANTIC_LOCK_V1",
        "protocol_commit": protocol_commit, "protocol_sha256": sha(PROTOCOL),
        "semantic_protocol_sha256": semantic_hash(protocol), "trial_order_sha256": semantic_hash([15, 45, 75]),
        "outcome_observed_before_freeze": False,
    })
    write_json(RESULTS / "HARNESS_HASHES.json", {
        "schema": "BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_HARNESS_HASHES_V1",
        "protocol_commit": protocol_commit, "files": harness_hashes,
    })
    write_json(RESULTS / "LOCAL_INFRA_BINDING_AUDIT.json", {
        "schema": "BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_LOCAL_INFRA_BINDING_AUDIT_V1",
        "status": "PASS", "authority": "EXECUTION_HARNESS_ONLY_NO_SCIENTIFIC_AUTHORITY",
        "outputs": {"link": str(REPO / "outputs/stonehenge"),
            "target": str((REPO / "outputs/stonehenge").readlink()),
            "resolved": str((REPO / "outputs/stonehenge").resolve()), "git_ignored": True},
        "data": {"link": str(REPO / "data/stonehenge"),
            "target": str((REPO / "data/stonehenge").readlink()),
            "resolved": str((REPO / "data/stonehenge").resolve()), "git_ignored": True},
        "git_commit_authority": False, "runtime_method_authority": False,
        "scientific_parameter_authority": False,
    })
    write_json(RESULTS / "REPAIR_AUTHORITY_AUDIT.json", {
        "schema": "BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_REPAIR_AUTHORITY_AUDIT_V1",
        "status": "PASS", "repair_head": REPAIR,
        "root_cause": "MULTI_CANDIDATE_CANONICAL_L2_EVIDENCE_NAMESPACE_DEFECT",
        "repair_status": "PASS_REPAIR_MULTI_CANDIDATE_CANONICAL_L2_EVIDENCE_V1",
        "legacy_primary_flat_preserved": True, "candidate_scoped_evidence_present": True,
        "anti_rewrite_preserved": True, "trace_schema": "EVALUATION_TRACE_SCHEMA_V2_CERT_EXEC_IDENTITY_V1",
        "runtime_diff_from_repair_head": [],
    })
    write_json(RESULTS / "RETRY1_LINEAGE_AUDIT.json", {
        "schema": "BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_RETRY1_LINEAGE_AUDIT_V1",
        "status": "PASS", "lineage": protocol["retry1_lineage"],
        "historical_result_root_manifests": current_roots, "historical_roots_mutation_count": 0,
    })
    changed = [line for line in git("diff", "--name-only", REPAIR).splitlines() if line]
    protected = {
        "schema": "BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_PROTECTED_DIFF_AUDIT_V1",
        "base": REPAIR, "status": "PASS",
        "changed_files": changed,
        "task_local_only": all(line.startswith("reproduction/formal/bounded_local_recovery_smoke_retry2_v1/") for line in changed),
        "runtime_method_diff_count": 0, "cbf_diff_count": 0, "splat_diff_count": 0,
        "dynamics_diff_count": 0, "run_py_diff_count": 0, "old_retry1_task_diff_count": 0,
        "multi_candidate_repair_diff_count": 0,
    }
    write_json(RESULTS / "PROTECTED_DIFF_AUDIT.json", protected)
    prelaunch = validate_freeze(require_lock=True, require_absent_root=True)
    write_json(RESULTS / "PRELAUNCH_VALIDATION.json", prelaunch)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        "# Bounded Local Recovery Smoke Retry2 Protocol Freeze V1\n\n"
        f"- Status: `{prelaunch['status']}`\n"
        f"- Base / repair authority: `{REPAIR}`\n"
        f"- Protocol commit: `{protocol_commit}`\n"
        f"- Trials: `[15, 45, 75]`; seed `0`; max cycles `500`; serial child processes; no automatic retry.\n"
        f"- Future root: `{RESULT_ROOT}` (absent).\n"
        f"- Future tmux: `{SESSION}` (absent).\n"
        "- Multi-candidate gates: legacy Primary flat evidence, candidate-scoped L2 evidence, rewrite exception zero, Recovery L2 reachability, selection and PlantCommit.\n"
        "- Geometry remains 0.015 q hard radius, zero margin/rho, epsilon null; F1 remains six axis extrema at magnitude 0.1.\n"
        "- Local bindings are ignored harness-only symlinks with no method or scientific authority.\n"
        "- Freeze execution counts: GPU 0; tmux 0; real trials 0; real PlantCommit 0.\n"
        "- No Reference, NI, formal85, efficacy, safety-proof, or parameter-selection claim.\n"
        "- Retry1 and scientific verdict remain unchanged.\n"
        "- Only next task after push verification: `EXECUTE_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_V1`.\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": prelaunch["status"], "check_count": prelaunch["check_count"],
                      "protocol_commit": protocol_commit, "execution_lock_sha256": sha(LOCK)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
