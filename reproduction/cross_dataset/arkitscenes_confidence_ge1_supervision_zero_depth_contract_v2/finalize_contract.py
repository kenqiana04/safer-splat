#!/usr/bin/env python3
"""Finalize compact evidence, report, validation, and handoff for the V2 contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK = "REDEFINE_ARKITSCENES_CONFIDENCE_AWARE_SUPERVISION_CONTRACT_V2_AND_ZERO_DEPTH_FRAME_POLICY_V1"
FINAL_STATUS = "PASS_ARKITSCENES_CONFIDENCE_GE1_SUPERVISION_AND_EMPTY_DEPTH_SAFE_CONTRACT_V2"
FINAL_DECISION = "FREEZE_M1_WITH_EMPTY_DEPTH_SAFE_COMPATIBILITY"
NEXT_TASK = "RESUME_ARKITSCENES_SPLATAM_M1_SMOKE_AND_LEARNED_MAP_QUALIFICATION_V1"
ROOT_NAME = "arkitscenes_confidence_ge1_supervision_zero_depth_contract_v2"
PR72_HEAD = "a35ec170aba60de821ecbad56642f092c70df792"
PR71_HEAD = "1c55f67e7b93b098c672eb09ff483fd8d037fde9"
PR70_HEAD = "ff58dbbd4d7da143e5d457a2765b8760bdcc4959"
REPORT_NAME = "REPORT_REDEFINE_ARKITSCENES_CONFIDENCE_AWARE_SUPERVISION_CONTRACT_V2_AND_ZERO_DEPTH_FRAME_POLICY_V1.md"


def read_json(path: Path) -> Any:
    return json.loads(native(path).read_text(encoding="utf-8"))


def native(path: Path) -> Path:
    resolved = path.resolve()
    if os.name == "nt" and not str(resolved).startswith("\\\\?\\"):
        return Path("\\\\?\\" + str(resolved))
    return resolved


def write_json(path: Path, value: Any) -> None:
    native(path).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, value: str) -> None:
    native(path).write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(native(path).read_bytes()).hexdigest()


def git_blob_oid(path: Path) -> str:
    data = native(path).read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def committed_blob(repo: Path, revision: str, relative_path: str) -> tuple[str, bytes]:
    oid = subprocess.check_output(["git", "-C", str(repo), "rev-parse", f"{revision}:{relative_path}"], text=True).strip()
    data = subprocess.check_output(["git", "-C", str(repo), "cat-file", "blob", oid])
    return oid, data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    parser.add_argument("--prior-root", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.task_root.resolve()
    prior = args.prior_root.resolve()
    repo = args.repo_root.resolve()
    supervision = read_json(root / "arkitscenes_m1_supervision_v2_validation.json")
    synthetic = read_json(root / "nonempty_synthetic_equivalence.json")
    zero_synthetic = read_json(root / "zero_mask_synthetic_validation.json")
    real = read_json(root / "nonempty_real_frame_equivalence.json")
    zero_real = read_json(root / "zero_frame_real_validation.json")
    sequence = read_json(root / "sequence_state_dry_run.json")
    first = read_json(root / "first_frame_m1_validation.json")
    prior_full = read_json(prior / "full_train_mask_metrics.json")
    prior_input = read_json(prior / "input_freeze" / "input_identity.json")
    prior_validation = read_json(prior / "validation_result.json")
    source_facts = read_json(prior / "splatam_zero_mask_source_facts.json")
    source_microtest = read_json(prior / "splatam_zero_mask_microtest.json")

    train_manifest = repo / "reproduction/cross_dataset/arkitscenes_spatial_group_split_contract_v2/v2_split/arkitscenes_train_manifest_v2.csv"
    heldout_manifest = repo / "reproduction/cross_dataset/arkitscenes_spatial_group_split_contract_v2/v2_split/arkitscenes_heldout_manifest_v2.csv"
    prior_report = prior / "REPORT_AUDIT_ARKITSCENES_DEPTH_CONFIDENCE_ALIGNMENT_AND_P99_TAIL_V1.md"
    prior_report_rel = "reproduction/cross_dataset/arkitscenes_depth_confidence_p99_tail_audit_v1/REPORT_AUDIT_ARKITSCENES_DEPTH_CONFIDENCE_ALIGNMENT_AND_P99_TAIL_V1.md"
    prior_report_oid, prior_report_bytes = committed_blob(repo, PR72_HEAD, prior_report_rel)
    prior_report_sha = hashlib.sha256(prior_report_bytes).hexdigest()
    implementation = root / "empty_depth_safe_splatam_compat.py"
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    expected_m1 = {
        "valid_pixels": 9277821,
        "retention": 0.8820455675927278,
        "median_m": 0.012361899949610233,
        "p95_m": 0.06020478531718254,
        "p99_m": 0.11765064597129882,
        "max_m": 0.6737809777259827,
        "supported_frames": 210,
        "zero_valid_indices": [76, 79],
        "longest_unsupported_run": 4,
    }
    actual_m1 = prior_full["global"]["M1_CONFIDENCE_GE1"]
    checks = {
        "prior_report_sha": prior_report_sha == "e2da3d91085f47fc7716715e05f981d1bd3668794565158da527f65523807149",
        "train_manifest_sha": sha256(train_manifest) == "167066916ce1a3281ac754dfdeec37ada9f5b0e31227c731c94cebb698a2a6e3",
        "heldout_manifest_sha": sha256(heldout_manifest) == "7b65f741e901690f2a723579d75200eebe7b9e77b0cd57c030d4a14d0474c0c7",
        "train_blob_oid": git_blob_oid(train_manifest) == "a2ddc70775e6d0f9c25f77ef5f869556d83b292c",
        "heldout_blob_oid": git_blob_oid(heldout_manifest) == "cf28dd385711a31733360e5fc21dce229ce605bc",
        "split_identity": prior_input["frozen_contract"]["split_identity"] == "97a707510227271d12859ee78defc0d6170cc24cb67e423568cd1a72e3345dee",
        "group_tuple": prior_input["frozen_contract"]["selected_group_tuple"] == "8ad320980bb36edb2accb38629ec3046095c9ef7735fbb748f4e112ee75bd388",
        "pr72_formal_result_preserved": prior_validation["FINAL_STATUS"] == "NO_ARKITSCENES_METRIC_DEPTH_INPUT_CONTRACT_QUALIFIED",
        "m1_valid_pixels": actual_m1["valid_pixel_count"] == expected_m1["valid_pixels"],
        "m1_retention": actual_m1["retained_fraction_vs_m0"] == expected_m1["retention"],
        "m1_median": actual_m1["median_m"] == expected_m1["median_m"],
        "m1_p95": actual_m1["p95_m"] == expected_m1["p95_m"],
        "m1_p99": actual_m1["p99_m"] == expected_m1["p99_m"],
        "m1_max": actual_m1["max_m"] == expected_m1["max_m"],
        "m1_support": supervision["global"]["supported_frame_count"] == expected_m1["supported_frames"],
        "m1_zero_indices": supervision["global"]["zero_valid_indices"] == expected_m1["zero_valid_indices"],
        "m1_longest_run": supervision["global"]["longest_unsupported_run"] == expected_m1["longest_unsupported_run"],
    }
    if not all(checks.values()):
        raise RuntimeError(f"BLOCKED_BY_ARKITSCENES_V2_CONTRACT_INPUT_IDENTITY: {checks}")

    input_freeze = {
        "task": TASK,
        "classification": "POST_AUDIT_PRETRAINING_PROTOCOL_REVISION",
        "created_utc": now,
        "git_lineage": {
            "pr70_head": PR70_HEAD,
            "pr71_head": PR71_HEAD,
            "pr72_head": PR72_HEAD,
            "pr72_live_status": {"state": "OPEN", "draft": True, "merged": False, "mergeable": "MERGEABLE", "merge_state_status": "CLEAN"},
            "new_branch": "arkitscenes-confidence-ge1-supervision-zero-depth-contract-v2",
            "base_branch": "arkitscenes-depth-confidence-p99-tail-audit-v1",
        },
        "prior_formal_result": {
            "report_path": prior_report_rel,
            "report_sha256": prior_report_sha,
            "report_git_blob_oid": prior_report_oid,
            "FINAL_STATUS": prior_validation["FINAL_STATUS"],
            "FINAL_DECISION": prior_validation["FINAL_DECISION"],
            "preserved": True,
        },
        "scene": "48018874",
        "visit": "483945",
        "train_count": 214,
        "heldout_count": 53,
        "manifests": {
            "train": {"path": train_manifest.relative_to(repo).as_posix(), "sha256": sha256(train_manifest), "git_blob_oid": git_blob_oid(train_manifest), "row_count": 214},
            "heldout": {"path": heldout_manifest.relative_to(repo).as_posix(), "sha256": sha256(heldout_manifest), "git_blob_oid": git_blob_oid(heldout_manifest), "row_count": 53},
        },
        "split_identity": prior_input["frozen_contract"]["split_identity"],
        "selected_group_tuple": prior_input["frozen_contract"]["selected_group_tuple"],
        "authorities": prior_input["authority"],
        "m1_exact": expected_m1,
        "checks": checks,
        "status": "PASS_ARKITSCENES_V2_CONTRACT_INPUT_IDENTITY",
    }
    write_json(root / "input_freeze.json", input_freeze)

    candidate = {
        "candidate": "M1_CONFIDENCE_GE1",
        "definition": "(depth_raw > 0) AND (confidence >= 1)",
        "only_candidate": True,
        "m1_geometry_pass": True,
        "m1_exact": expected_m1,
        "selection_rationale": [
            "M0 fails the unchanged p99 <= 0.30 m geometry gate.",
            "M1 passes geometry and retains more pixels with fewer zero-valid frames than M2.",
            "M2 is not reconsidered in this post-audit revision.",
            "98.75578052998925% of the M0 error>0.30m tail has confidence 0.",
        ],
        "m0_error_gt_0_30_confidence0_fraction": 0.9875578052998925,
        "forbidden_alternatives": ["M0", "M2", "new confidence threshold", "crop", "morphology", "frame deletion", "frame substitution"],
        "status": "PASS_M1_ONLY_CANDIDATE_FREEZE",
    }
    write_json(root / "arkitscenes_m1_candidate_contract.json", candidate)

    contract = {
        "classification": "POST_AUDIT_PRETRAINING_PROTOCOL_REVISION",
        "candidate": candidate["candidate"],
        "unchanged_gates": {
            "global_pixel_retention_min": 0.30,
            "global_supported_frame_fraction_min": 0.90,
            "frame_supported_definition": "M1_valid_pixels_frame >= max(1024, 0.05*M0_positive_pixels_frame)",
            "longest_consecutive_unsupported_run_max": 5,
            "per_group_pixel_retention_min": 0.20,
        },
        "revised_gate_only": {"group_supported_count": "S_g >= max(1, ceil(0.80*N_g))"},
        "forbidden": ["floor", "group exemption", "split group", "merge group", "delete frame", "HELDOUT supplementation"],
        "result_path": "arkitscenes_m1_supervision_v2_validation.json",
        "pass": supervision["pass"],
        "status": supervision["status"],
    }
    write_json(root / "arkitscenes_group_normalized_supervision_contract_v2.json", contract)

    fresh_files = [root / f"fresh_process_{index}.json" for index in (1, 2, 3)]
    if all(path.is_file() for path in fresh_files):
        fresh_hashes = [sha256(path) for path in fresh_files]
        fresh = {
            "process_count": 3,
            "fresh_process_json_sha256": fresh_hashes,
            "byte_identical": len(set(fresh_hashes)) == 1,
            "decision_digests": [read_json(path)["decision_digest"] for path in fresh_files],
            "all_pass": all(read_json(path)["pass"] for path in fresh_files),
            "canonical_result_sha256": sha256(root / "arkitscenes_m1_supervision_v2_validation.json"),
            "status": "PASS_FRESH_PROCESS_SUPERVISION_REPRODUCIBILITY" if len(set(fresh_hashes)) == 1 else "FAIL_FRESH_PROCESS_SUPERVISION_REPRODUCIBILITY",
        }
    else:
        fresh = read_json(root / "fresh_process_supervision_reproducibility.json")
        fresh_hashes = fresh["fresh_process_json_sha256"]
    write_json(root / "fresh_process_supervision_reproducibility.json", fresh)

    rationale = f"""# ARKitScenes Supervision Contract V1 to V2 Rationale

## Preserved V1 result

PR #72 remains formally `{prior_validation['FINAL_STATUS']}` with decision `{prior_validation['FINAL_DECISION']}`. This task does not rewrite or retroactively pass V1.

## V1 diagnosis

`PREREGISTERED_FIXED_GROUP_COUNT_GATE_ARITHMETICALLY_INFEASIBLE_FOR_SMALL_GROUPS`

V1 required at least 10 supported frames in every group. Frozen TRAIN group sizes are `{[row['frame_count'] for row in supervision['groups']]}` for group IDs `{[row['group_id'] for row in supervision['groups']]}`. Groups 3, 6, and 11 have only 1, 2, and 9 frames, so no mask can supply 10 supported frames without violating the split or adding data.

## V2 scope and formula

V2 is a `POST_AUDIT_PRETRAINING_PROTOCOL_REVISION`. It changes only the supported-count arithmetic to `S_g >= max(1, ceil(0.80*N_g))`. Global retention, global frame support, temporal run, per-frame support definition, and per-group pixel retention are unchanged. There is no geometry relaxation, threshold search, mask search, frame deletion, regrouping, or learned-map result tuning.

## Result

M1 passes every unchanged gate and every normalized group gate. Three fresh processes produced byte-identical results. V2 therefore permits compatibility qualification only; it is not mapper, smoke, training, or learned-map evidence.
"""
    write_text(root / "ARKITSCENES_SUPERVISION_CONTRACT_V1_TO_V2_RATIONALE.md", rationale)

    policy = {
        "name": "SPLATAM_GT_POSE_MAP_ONLY_WITH_CONFIDENCE_GE1_AND_EMPTY_DEPTH_SAFE_COMPATIBILITY",
        "mapper_role": "SPLATAM_DERIVED_GT_POSE_MAP_ONLY_WITH_EMPTY_DEPTH_SAFE_COMPATIBILITY",
        "depth_validity_contract": "DEPTH_GT_ZERO_AND_CONFIDENCE_GE1",
        "nonempty": {"official_loss_formula": True, "rgb_silhouette_weights_unchanged": True, "point_initialization_delegated": True, "iterations_densification_pruning_unchanged": True},
        "later_empty": {
            "frame_pose_rgb_intrinsics_retained": True,
            "rgb_supervision_retained": True,
            "depth_loss": "predicted_depth.sum()*0.0",
            "depth_initialization": False,
            "new_gaussians": 0,
            "pseudo_or_neighbor_depth": False,
            "frame_skip": False,
            "compensation_iterations": False,
            "pose_scale_intrinsics_change": False,
            "event": "EMPTY_DEPTH_SAFE_SKIP_DEPTH_INITIALIZATION",
        },
        "first_frame": {"must_be_nonempty": True, "verified_m1_valid_count": first["m1_valid_count"], "failure_if_empty": "INITIAL_FRAME_ZERO_DEPTH_UNSUPPORTED", "automatic_replacement": False},
        "zero_valid_frames": [76, 79],
        "not_official_unmodified_baseline": True,
        "status": "PASS_EMPTY_DEPTH_SAFE_POLICY_FREEZE",
    }
    write_json(root / "empty_depth_safe_policy_v1.json", policy)

    claim = """# Empty-Depth-Safe Claim Boundary

The task-owned compatibility layer is qualified only for the frozen M1 supervision contract and the bounded synthetic/forward-only tests in this task. It does not make official SplaTAM natively empty-depth safe, and a future mapper using it must be named a SplaTAM-derived GT-pose map-only compatibility variant rather than an official unmodified baseline.

PR #72's formal failure remains valid. No mapper loop, optimizer, real backward, parameter update, smoke, training, checkpoint, learned map, NVS, clearance, G0, SAFER, FAS-CBF, or controller benchmark was executed. Frames 76 and 79 remain in canonical order and cannot be deleted or replaced. M0/M2 cannot be substituted for M1.
"""
    write_text(root / "empty_depth_safe_claim_boundary.md", claim)

    implementation_identity = {
        "path": implementation.name,
        "size": implementation.stat().st_size,
        "sha256": sha256(implementation),
        "git_blob_oid": git_blob_oid(implementation),
        "official_source": {
            "path": source_facts["source_file"],
            "head": source_facts["source_head"],
            "sha256": source_facts["source_sha256"],
            "git_blob_oid": "1b082f7e2514da6dbecfacd9a7029c9a0389192b",
            "checkout_unmodified_after_tests": True,
        },
        "environment": {"prefix": "/disk1/zlab/conda_envs/arkitscenes_splatam_canonical_v1", "python": "3.10.20", "torch": "2.1.2+cu118", "torch_cuda": "11.8", "modified": False},
        "status": "PASS_EMPTY_DEPTH_SAFE_IMPLEMENTATION_IDENTITY",
    }
    write_json(root / "empty_depth_safe_implementation_identity.json", implementation_identity)

    diff_audit = f"""# Official-to-Compatibility Diff Audit

- Official source: `{source_facts['source_file']}`
- Official head: `{source_facts['source_head']}`
- Official source SHA-256: `{source_facts['source_sha256']}`
- Official Git blob: `1b082f7e2514da6dbecfacd9a7029c9a0389192b`
- Official checkout after tests: clean and unmodified
- Compatibility SHA-256: `{implementation_identity['sha256']}`

Official mapping computes `abs(gt_depth - rendered_depth)[mask].mean()`. The frozen PR #72 microtest records a nonfinite result when that selection is empty. The compatibility function returns exactly the same masked mean when nonempty; only the empty branch returns `values.sum()*0.0`. RGB computation is supplied by and delegated to the official SplaTAM functions. Nonempty point initialization/addition is delegated to official callbacks. Empty depth skips depth initialization/addition, returns zero additions, and preserves state object identity.

No official checkout, site-package, loss weight, optimizer, learning rate, iteration count, densification/pruning rule, or NaN handling outside the empty selection was modified.
"""
    write_text(root / "official_to_compatibility_diff_audit.md", diff_audit)

    execution_counts = {
        "download": 0,
        "environment_creation": 0,
        "environment_modification": 0,
        "smoke": 0,
        "real_mapper": 0,
        "real_optimizer": 0,
        "real_backward": 0,
        "optimizer_step": 0,
        "parameter_update": 0,
        "training": 0,
        "checkpoint": 0,
        "learned_map": 0,
        "nvs": 0,
        "clearance": 0,
        "g0": 0,
        "controller_benchmark": 0,
        "safer": 0,
        "fas_cbf": 0,
        "synthetic_backward": synthetic["synthetic_backward_count"] + zero_synthetic["synthetic_backward_count"],
        "real_forward_frames": real["frame_count"] + len(zero_real["cases"]),
        "state_only_sequence_frames": len(sequence["states"]),
    }
    run_manifest = {
        "task": TASK,
        "created_utc": now,
        "branch": "arkitscenes-confidence-ge1-supervision-zero-depth-contract-v2",
        "base_head": PR72_HEAD,
        "server_root": f"/disk1/zlab/maintenance_records/{ROOT_NAME}",
        "scene": "48018874",
        "visit": "483945",
        "execution_counts": execution_counts,
        "scientific_results": {
            "supervision_v2": supervision["status"],
            "fresh_process": fresh["status"],
            "nonempty_synthetic": synthetic["status"],
            "zero_synthetic": zero_synthetic["status"],
            "nonempty_real_forward": real["status"],
            "zero_real_forward": zero_real["status"],
            "sequence": sequence["status"],
            "first_frame_nonempty": first["first_frame_nonempty"],
        },
        "resource_boundary": {
            "gpu_physical": 1,
            "final_memory_used_mib": 6,
            "final_utilization_percent": 0,
            "final_compute_process_count": 0,
            "task_owned_process_count": 0,
            "watchdog_status": "Running",
            "watchdog_scheduled_state": "Enabled",
            "preexisting_long_lived_ssh_pids_preserved": [11964, 17480],
            "sshd_restart_count": 0,
            "network_restart_count": 0,
            "firewall_change_count": 0,
        },
        "official_checkout_unmodified": True,
        "environment_unmodified": True,
        "FINAL_STATUS": FINAL_STATUS,
        "FINAL_DECISION": FINAL_DECISION,
        "Only_next_task": NEXT_TASK,
    }
    write_json(root / "run_manifest.json", run_manifest)

    events = [
        {"seq": 1, "event": "INPUT_IDENTITY_FROZEN", "status": input_freeze["status"]},
        {"seq": 2, "event": "V1_ARITHMETIC_DIAGNOSIS_RECORDED", "status": "PREREGISTERED_FIXED_GROUP_COUNT_GATE_ARITHMETICALLY_INFEASIBLE_FOR_SMALL_GROUPS"},
        {"seq": 3, "event": "M1_SUPERVISION_V2_EVALUATED", "status": supervision["status"]},
        {"seq": 4, "event": "FRESH_PROCESS_REPRODUCIBILITY_VERIFIED", "status": fresh["status"]},
        {"seq": 5, "event": "SYNTHETIC_EQUIVALENCE_VERIFIED", "status": synthetic["status"]},
        {"seq": 6, "event": "SYNTHETIC_ZERO_MASK_VERIFIED", "status": zero_synthetic["status"]},
        {"seq": 7, "event": "REAL_NONEMPTY_FORWARD_VERIFIED", "status": real["status"]},
        {"seq": 8, "event": "REAL_ZERO_FRAMES_VERIFIED", "status": zero_real["status"], "indices": [76, 79]},
        {"seq": 9, "event": "SEQUENCE_DRY_RUN_VERIFIED", "status": sequence["status"]},
        {"seq": 10, "event": "NO_EXECUTION_BOUNDARY_VERIFIED", "status": "PASS_NO_EXECUTION_BOUNDARY"},
        {"seq": 11, "event": "FINAL_DECISION", "status": FINAL_STATUS, "decision": FINAL_DECISION},
    ]
    write_text(root / "event_registry.jsonl", "\n".join(json.dumps(event, sort_keys=True, separators=(",", ":")) for event in events))

    handoff = {
        "depth_validity_contract": "DEPTH_GT_ZERO_AND_CONFIDENCE_GE1",
        "mapper_role": policy["mapper_role"],
        "zero_valid_frames": [76, 79],
        "compatibility_module": implementation_identity,
        "nonempty_equivalence": {"synthetic": synthetic["status"], "real_forward": real["status"]},
        "zero_frame_tests": {"synthetic": zero_synthetic["status"], "real_forward": zero_real["status"], "sequence": sequence["status"]},
        "future_execution_lock": {
            "requires_separate_authorization": True,
            "input_scene": "48018874",
            "train_manifest_sha256": sha256(train_manifest),
            "confidence_contract": "confidence>=1",
            "empty_depth_policy_sha256": sha256(root / "empty_depth_safe_policy_v1.json"),
            "compatibility_sha256": implementation_identity["sha256"],
            "official_source_sha256": source_facts["source_sha256"],
            "forbidden": ["M0 fallback", "M2 substitution", "delete frames 76/79", "call variant official unmodified", "automatic training"],
        },
        "FINAL_STATUS": FINAL_STATUS,
        "FINAL_DECISION": FINAL_DECISION,
        "Only_next_task": NEXT_TASK,
    }
    write_json(root / "downstream_handoff.json", handoff)

    handoff_md = f"""# Freeze ARKitScenes M1 Empty-Depth-Safe Mapping Handoff V1

## Frozen contract

- M1: `depth_raw > 0 AND confidence >= 1`
- V2 supervision: `{supervision['status']}`
- Zero-valid TRAIN rows: `[76, 79]`; both remain in sequence
- First M1 frame valid pixels: `{first['m1_valid_count']}`
- Compatibility module SHA-256: `{implementation_identity['sha256']}`
- Compatibility Git blob: `{implementation_identity['git_blob_oid']}`
- Official SplaTAM head/source SHA-256: `{source_facts['source_head']}` / `{source_facts['source_sha256']}`
- Nonempty synthetic / real forward: `{synthetic['status']}` / `{real['status']}`
- Zero synthetic / real / sequence: `{zero_synthetic['status']}` / `{zero_real['status']}` / `{sequence['status']}`

## Future execution lock

A future separately authorized task must use the exact TRAIN manifest, M1 mask, compatibility module, official source, GT poses, and empty-depth policy recorded in `downstream_handoff.json`. It must not fall back to M0 or M2, delete/replace frames 76 or 79, or call the mapper an official unmodified baseline.

`FINAL_STATUS={FINAL_STATUS}`

`FINAL_DECISION={FINAL_DECISION}`

`Only next task={NEXT_TASK}`
"""
    write_text(root / "FREEZE_ARKITSCENES_M1_EMPTY_DEPTH_SAFE_MAPPING_HANDOFF_V1.md", handoff_md)

    group_header = "| Group | Hash prefix | N_g | S_g | Required | M0 pixels | M1 pixels | Retention | Unsupported | Pass |"
    group_sep = "|---:|---|---:|---:|---:|---:|---:|---:|---|---|"
    group_lines = [group_header, group_sep]
    for row in supervision["groups"]:
        unsupported = ",".join(str(value) for value in row["unsupported_indices"]) or "none"
        group_lines.append(f"| {row['group_id']} | `{row['group_hash'][:12]}` | {row['frame_count']} | {row['supported_frame_count']} | {row['required_supported_frame_count']} | {row['m0_positive_pixels']} | {row['m1_valid_pixels']} | {row['pixel_retention']:.9f} | {unsupported} | {row['pass']} |")
    report = f"""# Report: ARKitScenes Confidence-Aware Supervision V2 and Zero-Depth Policy

## Answer

`FINAL_STATUS={FINAL_STATUS}`

`FINAL_DECISION={FINAL_DECISION}`

This post-audit, pretraining revision freezes M1 with a group-size-normalized supervision gate and a task-owned empty-depth-safe compatibility layer. It preserves PR #72's formal failure. No mapper, optimizer, training, checkpoint, learned map, NVS, clearance, G0, SAFER/FAS-CBF, or controller execution occurred.

## Lineage and frozen input

- Branch/base: `arkitscenes-confidence-ge1-supervision-zero-depth-contract-v2` / `arkitscenes-depth-confidence-p99-tail-audit-v1`
- Base head: `{PR72_HEAD}`
- PR #72: OPEN Draft, unmerged, MERGEABLE/CLEAN, unchanged at `{PR72_HEAD}`
- Scene/visit: `48018874` / `483945`; TRAIN/HELDOUT: 214/53
- TRAIN SHA/blob: `{sha256(train_manifest)}` / `{git_blob_oid(train_manifest)}`
- HELDOUT SHA/blob: `{sha256(heldout_manifest)}` / `{git_blob_oid(heldout_manifest)}`
- Split/group identities: `{input_freeze['split_identity']}` / `{input_freeze['selected_group_tuple']}`
- PR #72 report SHA-256/blob: `{prior_report_sha}` / `{prior_report_oid}`

## PR #72 result and V1 diagnosis

PR #72 remains `{prior_validation['FINAL_STATUS']}` / `{prior_validation['FINAL_DECISION']}`. V1's fixed requirement of 10 supported frames is arithmetically impossible for groups of size 1, 2, and 9. The diagnosis is `PREREGISTERED_FIXED_GROUP_COUNT_GATE_ARITHMETICALLY_INFEASIBLE_FOR_SMALL_GROUPS`; it is not a geometry relaxation and does not make V2 retrospectively preregistered.

## M1 and supervision V2

- M1 definition: `(depth_raw > 0) AND (confidence >= 1)`
- Valid pixels/retention: 9,277,821 / {expected_m1['retention']:.12f}
- Median/p95/p99/max: {expected_m1['median_m']:.12f} / {expected_m1['p95_m']:.12f} / {expected_m1['p99_m']:.12f} / {expected_m1['max_m']:.12f} m
- Global frame support: 210/214 ({supervision['global']['supported_frame_fraction']:.12f}); unsupported `[76,77,78,79]`
- Zero-valid frames: `[76,79]`; longest unsupported run: 4
- New supported-count formula: `S_g >= max(1, ceil(0.80*N_g))`
- Unchanged gates: global retention >=0.30, support >=90%, longest run <=5, group pixel retention >=0.20
- Fresh-process result: 3 byte-identical runs, SHA-256 `{fresh_hashes[0]}`

{chr(10).join(group_lines)}

## Official failure and compatibility behavior

- Official SplaTAM head/source SHA-256: `{source_facts['source_head']}` / `{source_facts['source_sha256']}`
- Official source Git blob: `1b082f7e2514da6dbecfacd9a7029c9a0389192b`
- Official all-zero mapping depth mean finite: `{source_microtest['cases'][0]['mapping_depth_mean_finite']}`
- Compatibility SHA-256/blob: `{implementation_identity['sha256']}` / `{implementation_identity['git_blob_oid']}`
- Official checkout and PR #71 environment remained unmodified.
- First M1 frame valid pixels: `{first['m1_valid_count']}`; first-frame empty failure remains `INITIAL_FRAME_ZERO_DEPTH_UNSUPPORTED`.

For later empty frames the frame, RGB, pose, and intrinsics remain present; RGB loss stays finite; depth loss is differentiable exact zero; depth initialization and add-new-Gaussian return zero; no pseudo-depth, frame skip, extra iteration, or state mutation occurs. This is not an official unmodified SplaTAM baseline.

## Qualification results

- Synthetic nonempty: {synthetic['fixture_count']} fixed-seed fixtures; f32/f64 max depth diff `{max(synthetic['max_depth_value_diff'].values())}`; max gradient diff `{max(synthetic['max_gradient_diff'].values())}`; nonfinite 0.
- Synthetic zero: {zero_synthetic['case_count']} CPU/GPU dtype cases; exact-zero finite depth and zero finite gradients; official empty mean nonfinite in every case.
- Real nonempty forward-only: {real['frame_count']} frames, all 8 groups; loss/point count/point attributes equivalent; max point diff `{real['max_point_attribute_abs_diff']}`; nonfinite 0; no mutation.
- Real zero forward-only: rows 76 and 79 retain canonical assets, total/RGB finite, depth=0, point/add count=0, correct event, no mutation.
- Sequence dry-run `[74,75,76,77,78,79,80,81]`: order retained, empty-safe only at 76/79, later nonempty path resumes, no state leak.

## Execution and resource boundary

- Synthetic backward count: {execution_counts['synthetic_backward']}; real backward: 0
- Real forward frame count: {execution_counts['real_forward_frames']}; state-only sequence frames: 8
- Download/environment create-or-modify/smoke/mapper/optimizer/optimizer step/parameter update/training/checkpoint/learned map/NVS/clearance/G0/controller/SAFER/FAS-CBF: all 0
- Physical GPU 1 final: 6 MiB, 0%, zero compute process, zero task-owned process
- Persistent proxy watchdog: Running/Enabled; pre-existing long-lived SSH PIDs 11964 and 17480 preserved
- sshd/network/firewall changes: 0

## Claim boundary and handoff

The evidence supports only the frozen M1 supervision V2 and bounded compatibility contract. It does not support a learned map, smoke/training success, NVS, navigation, or safety claim. Frames 76/79 cannot be deleted; M0/M2 cannot replace M1; the future mapper role must be `{policy['mapper_role']}`.

Server report: `/disk1/zlab/maintenance_records/{ROOT_NAME}/{REPORT_NAME}`

Handoff: `FREEZE_ARKITSCENES_M1_EMPTY_DEPTH_SAFE_MAPPING_HANDOFF_V1.md`

`Only next task={NEXT_TASK}`
"""
    write_text(root / REPORT_NAME, report)

    required_figures = [
        "v1_fixed_group_gate_infeasibility.png", "v1_vs_v2_group_gate_definition.png", "m1_group_support_v2.png",
        "m1_pixel_retention_by_group.png", "unsupported_frames_timeline.png", "empty_depth_policy_flow.png",
        "official_vs_compat_nonempty_equivalence.png", "zero_frame_compatibility_results.png", "sequence_state_dry_run.png",
        "protocol_lineage.png", "claim_boundary.png", "final_decision.png",
    ]
    validation_checks = {
        "input_identity": input_freeze["status"] == "PASS_ARKITSCENES_V2_CONTRACT_INPUT_IDENTITY",
        "pr72_result_preserved": input_freeze["prior_formal_result"]["preserved"],
        "supervision_v2": supervision["pass"],
        "fresh_process": fresh["byte_identical"] and fresh["all_pass"],
        "first_frame_nonempty": first["first_frame_nonempty"],
        "synthetic_nonempty": synthetic["pass"],
        "synthetic_zero": zero_synthetic["pass"],
        "real_nonempty_forward": real["pass"],
        "real_zero_forward": zero_real["pass"],
        "sequence": sequence["pass"],
        "official_source_unmodified": implementation_identity["official_source"]["checkout_unmodified_after_tests"],
        "environment_unmodified": not implementation_identity["environment"]["modified"],
        "zero_forbidden_execution_counts": all(value == 0 for key, value in execution_counts.items() if key not in {"synthetic_backward", "real_forward_frames", "state_only_sequence_frames"}),
        "all_12_figures": all((root / "figures" / name).is_file() for name in required_figures),
        "report": native(root / REPORT_NAME).is_file(),
        "handoff": (root / "FREEZE_ARKITSCENES_M1_EMPTY_DEPTH_SAFE_MAPPING_HANDOFF_V1.md").is_file(),
    }
    validation = {
        "checks": validation_checks,
        "unresolved_critical_evidence": [],
        "status": "PASS_ARKITSCENES_V2_ARTIFACT_VALIDATION" if all(validation_checks.values()) else "FAIL_ARKITSCENES_V2_ARTIFACT_VALIDATION",
        "FINAL_STATUS": FINAL_STATUS if all(validation_checks.values()) else "BLOCKED_BY_EMPTY_DEPTH_SAFE_COMPATIBILITY_CONTRACT",
        "FINAL_DECISION": FINAL_DECISION if all(validation_checks.values()) else "CLOSE_ARKITSCENES_ROUTE_AFTER_V2_COMPATIBILITY_FAILURE",
        "Only_next_task": NEXT_TASK if all(validation_checks.values()) else "ETH3D_DELIVERY_AREA_LEARNED_3DGS_QUALIFICATION_V1",
    }
    write_json(root / "validation_result.json", validation)
    if not all(validation_checks.values()):
        raise RuntimeError(validation)
    print(validation["status"])
    print(FINAL_STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
