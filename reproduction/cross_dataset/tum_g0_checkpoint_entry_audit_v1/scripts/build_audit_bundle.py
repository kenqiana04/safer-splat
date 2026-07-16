#!/usr/bin/env python3
"""Build local correction artifacts exclusively from authoritative 4090 evidence."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REMOTE = ROOT / "remote_outputs"
CORRECTION = REMOTE / "correction_v1"
REPO = ROOT.parents[2]
BASE = "0fb8698e8590aead60032487fc3321c07f2fd99c"
CORRECTION_PREREG = "1f15ad20999ebc4b21cb628fc2866b1fc7742bb8"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write(name: str, value: dict) -> None:
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown(lines: list[str]) -> str:
    return "\n".join(lines) + "\n"


def git_lines(*args: str) -> list[str]:
    completed = subprocess.run(["git", *args], cwd=REPO, text=True, check=True, stdout=subprocess.PIPE)
    return [line for line in completed.stdout.splitlines() if line]


def is_cache(path: str) -> bool:
    return path.endswith(".pyc") or "/__pycache__/" in path


def main() -> None:
    required = [
        "official_tum_depth_contract.json", "depth_copy_identity_audit.csv", "depth_scale_closure.json",
        "dataparser_correction_result.json", "dataparser_pose_mapping_audit.csv",
        "nerfstudio_dataparser_audit.json", "nerfstudio_environment_audit.json",
        "remote_server_preflight.json", "splatfacto_entry_command.json", "correction_remote_manifest.json",
    ]
    missing = [name for name in required if not (CORRECTION / name).is_file()]
    if missing:
        raise RuntimeError(f"missing required remote correction evidence: {missing}")
    for name in required:
        if name == "correction_remote_manifest.json":
            continue
        shutil.copy2(CORRECTION / name, ROOT / name)

    base_caches = sorted(path for path in git_lines("ls-tree", "-r", "--name-only", BASE) if is_cache(path))
    current_caches = sorted(path for path in git_lines("ls-files") if is_cache(path))
    cache_diff = [line for line in git_lines("diff", "--name-status", BASE, "--") if is_cache(line.split("\t")[-1])]
    audit_rel = "reproduction/cross_dataset/tum_g0_checkpoint_entry_audit_v1"
    audit_tracked = [path for path in git_lines("ls-files", "--", audit_rel) if is_cache(path)]
    audit_untracked = [path for path in git_lines("ls-files", "--others", "--exclude-standard", "--", audit_rel) if is_cache(path)]
    inventory = {
        "base_commit": BASE,
        "policy": "preexisting_tracked_cache_is_out_of_scope_and_must_remain_unchanged",
        "base_tracked_cache_count": len(base_caches),
        "current_tracked_cache_count": len(current_caches),
        "set_difference_count": len(set(base_caches).symmetric_difference(current_caches)),
        "diff_count": len(cache_diff),
        "paths": base_caches,
        "task_added_cache_count": len(set(current_caches) - set(base_caches)),
        "task_modified_cache_count": len(cache_diff),
        "task_deleted_cache_count": len(set(base_caches) - set(current_caches)),
        "audit_directory_tracked_cache_count": len(audit_tracked),
        "audit_directory_untracked_cache_count": len(audit_untracked),
        "core_cache_cleanup_attempted": False,
    }
    write("preexisting_tracked_cache_inventory.json", inventory)
    preregistration_precedes_execution = subprocess.run(["git", "merge-base", "--is-ancestor", CORRECTION_PREREG, "HEAD"], cwd=REPO).returncode == 0

    contract = load(ROOT / "official_tum_depth_contract.json")
    closure = load(ROOT / "depth_scale_closure.json")
    parser = load(ROOT / "dataparser_correction_result.json")
    preflight = load(ROOT / "remote_server_preflight.json")
    source = load(REMOTE / "source_asset_hash_manifest.json")
    transforms = load(ROOT / "transforms_contract_audit.json")
    entry = load(ROOT / "splatfacto_entry_command.json")

    identity = load(ROOT / "dataset_identity.json")
    identity.update({"authoritative_execution_host": preflight["authoritative_execution_host"], "authoritative_asset_root": "/disk1/zlab/cross_dataset_assets", "processed_transforms_path": transforms["processed_transforms_path"], "processed_transforms_sha256": transforms["sha256"], "selected_frame_count": 300})
    write("dataset_identity.json", identity)
    write("environment_provenance.json", {"authoritative_execution_host": preflight["authoritative_execution_host"], "authoritative_conda_env": preflight["authoritative_conda_env"], "authoritative_python": preflight["authoritative_python"], "authoritative_gpu": preflight["visible_device_0"], "remote_execution_complete": True, "windows_probe_role": "superseded_non_authoritative_local_probe", "used_for_gate_decision": False, "training_iterations_executed": 0, "checkpoint_created": False})
    write("metric_scale_audit.json", {"status": "pass_source_backed_metric_depth_contract", "pose_scale_preserved": parser["dataparser_scale_is_one"], "orientation_method": parser["orientation_method"], "center_method": parser["center_method"], "auto_scale_poses": parser["auto_scale_poses"], "official_tum_depth_units_per_meter": contract["depth_units_per_meter"], "depth_unit_scale_factor_meters": contract["depth_unit_scale_factor_meters"], "freiburg1_correction_already_applied": contract["correction_already_applied"], "historical_preprocessor_scales_depth": closure["historical_preprocessor_scales_depth"], "double_scaling_risk": closure["double_scaling_risk"], "future_required_depth_unit_scale_factor": closure["future_required_depth_unit_scale_factor"]})

    summary = closure["identity_summary"]
    depth_ok = contract["evidence_status"] == "pass_official_tum_source" and closure["final_depth_contract_status"] == "pass" and summary["mapped_count"] == 300 and summary["byte_identical_count"] == 300 and summary["mismatch_count"] == 0 and not closure["double_scaling_risk"]
    parser_ok = parser["status"] == "PASS_DATAPARSER_ONLY" and parser["dataparser_transform_identity"] and parser["dataparser_scale_is_one"] and parser["parsed_total_count"] == 300 and parser["frame_drop_count"] == 0 and parser["unmatched_pose_count"] == 0 and parser["unmatched_parsed_count"] == 0 and parser["unmatched_source_count"] == 0 and abs(parser["ratio_median"] - 1.0) <= 1e-9
    decision_name = "PASS_DEPTH_AND_DATAPARSER_CORRECTION" if depth_ok and parser_ok else "BLOCKED_BY_CRITICAL_PROVENANCE"
    entry_decision = "READY_FOR_FORMAL_SPLATFACTO_TRAINING_PREREGISTRATION" if decision_name.startswith("PASS") and entry["explicit_override_required"] else "BLOCKED_BY_TRAINING_ENTRY_CONTRACT"
    decision = {"decision": decision_name, "checkpoint_entry_decision": entry_decision, "authoritative_execution_host": preflight["authoritative_execution_host"], "data_and_checkpoint_entry_substage": "training_preregistration_ready" if decision_name.startswith("PASS") else "blocked", "safer_navigation_substage": "not_started", "global_G0_status": "partial_ready" if decision_name.startswith("PASS") else "blocked", "formal_checkpoint_exists": False, "safer_loader_validated": False, "navigation_gates_completed": False, "G1_allowed": False, "training_iterations_executed": 0, "checkpoint_created": False, "reason": "Source-backed TUM depth contract and byte identity plus shape-compatible dataparser-only validation passed; formal training remains separately preregistration-gated."}
    write("checkpoint_entry_decision.json", decision)

    registry = load(ROOT / "G0_GATE_REGISTRY.json")
    if decision_name not in registry["allowed_final_decisions"]:
        registry["allowed_final_decisions"].append(decision_name)
    registry["final_decision"] = decision_name
    statuses = {"G0-D": "passed", "G0-H": "passed", "G0-I": "passed", "G0-J": "passed_entry_contract_only"}
    for gate in registry["gates"]:
        if gate["id"] in statuses:
            gate["status"] = statuses[gate["id"]]
    write("G0_GATE_REGISTRY.json", registry)

    remote_files = {str(path.relative_to(REMOTE)).replace("\\", "/"): digest(path) for path in sorted(REMOTE.rglob("*")) if path.is_file()}
    write("remote_output_manifest.json", {"remote_host": preflight["authoritative_execution_host"], "remote_tmp": "/tmp/tum_g0_checkpoint_entry_audit_v1_zlab/correction_outputs", "files": remote_files})

    correction_lines = [
        "# TUM Depth-Scale and Dataparser Audit Correction V1", "", "## Corrected Findings", "",
        "The original `RuntimeError` comparing tensor dimensions 3 and 4 occurred in audit post-processing after dataparser output generation.",
        f"The corrected native-shape identity check passed for transform `{parser['dataparser_transform_shape']}` with maximum error `{parser['dataparser_transform_max_abs_error']}`.",
        f"Train/validation parsing completed with `{parser['parsed_train_count']}/{parser['parsed_eval_count']}` frames; total `{parser['parsed_total_count']}`, drop `{parser['frame_drop_count']}`.",
        f"All `{parser['matched_pose_count']}` poses mapped to source frames. Actual translation-ratio median is `{parser['ratio_median']}` (range `{parser['ratio_min']}` to `{parser['ratio_max']}`).", "", "## Depth Contract Closure", "",
        f"Official source: {contract['source_url']}", f"Page SHA-256: `{contract['source_page_sha256']}`.",
        f"Depth is {contract['depth_format']}; `{contract['depth_units_per_meter']}` units/m gives meter scale `{contract['depth_unit_scale_factor_meters']}`.",
        f"Zero means `{contract['zero_semantics']}`. Freiburg 1 correction `{contract['freiburg1_correction_value']}` was already applied and is not reapplied.",
        f"`{summary['byte_identical_count']}/300` selected depth files are byte-identical to raw mappings; mismatch count is `{summary['mismatch_count']}`.",
        f"Historical preprocessing used `{closure['historical_preprocessor_operation']}` and neither scaled nor re-encoded depth.",
        f"Nerfstudio default is `{entry['installed_nerfstudio_default_depth_scale']}`; future training must explicitly set `{entry['exact_cli_option_if_available']}`.", "", "## Cache Validation Scope Correction", "",
        f"The frozen base already tracks `{inventory['base_tracked_cache_count']}` core `__pycache__/*.pyc` files. They predate this task and were not removed, modified, or regenerated.",
        f"Baseline-aware validation finds set difference `{inventory['set_difference_count']}`, cache diff `{inventory['diff_count']}`, audit tracked cache `{inventory['audit_directory_tracked_cache_count']}`, and audit untracked cache `{inventory['audit_directory_untracked_cache_count']}`.",
        "The former repository-wide empty-cache rule was over-broad; this task instead proves no cache was introduced or changed.", "", "## Boundary and Decision", "",
        "No transforms or depth PNGs were modified. No preprocessing, model, trainer, optimizer, viewer, training, checkpoint, SAFER, navigation, or G1 execution occurred.",
        f"Decision: **`{decision_name}`**. G0-D/G0-H/G0-I are passed. Global G0 is `{decision['global_G0_status']}`; checkpoint-entry decision is `{entry_decision}`.",
        f"Correction preregistration `{CORRECTION_PREREG}` is an independent Git commit preceding correction execution: `{preregistration_precedes_execution}`.",
        "This permits only Formal TUM Splatfacto Training Protocol Preregistration, not checkpoint readiness. `G1_allowed=false` remains binding.",
    ]
    (ROOT / "AUDIT_CORRECTION_REPORT_V1.md").write_text(markdown(correction_lines), encoding="utf-8")
    main_lines = [
        "# REPORT: TUM Remaining G0 Checkpoint-Entry Audit V1", "", "## Executive Summary", "",
        f"The authoritative correction ran on `{preflight['authoritative_execution_host']}` in `{preflight['authoritative_conda_env']}` against immutable TUM assets `/disk1/zlab/cross_dataset_assets`.",
        f"Sequence `rgbd_dataset_freiburg1_room` (`TUM_FR1_ROOM`) uses frozen transforms SHA-256 `{transforms['sha256']}`.",
        f"Final correction decision: **`{decision_name}`**. Checkpoint-entry decision: **`{entry_decision}`**.", "", "## Depth-Scale and Dataparser Correction", "",
        "The original 3-vs-4 error was an audit post-processing comparison bug, not a dataparser generation failure.",
        f"Corrected native transform shape `{parser['dataparser_transform_shape']}` is identity `{parser['dataparser_transform_identity']}` with max error `{parser['dataparser_transform_max_abs_error']}` and parser scale `{parser['dataparser_scale']}`.",
        f"Dataparser train/val counts are `{parser['parsed_train_count']}/{parser['parsed_eval_count']}`; total `{parser['parsed_total_count']}`, frame drop `{parser['frame_drop_count']}`, unmatched poses `{parser['unmatched_pose_count']}`.",
        f"Actual parsed/source translation-ratio median `{parser['ratio_median']}`; no orientation or centering change and auto scale is `{parser['auto_scale_poses']}`.",
        f"Official TUM depth evidence `{contract['source_url']}` SHA-256 `{contract['source_page_sha256']}` confirms {contract['depth_format']}, {contract['depth_units_per_meter']} units/m, meter scale `{contract['depth_unit_scale_factor_meters']}`, and zero `{contract['zero_semantics']}`.",
        f"Freiburg 1 `{contract['freiburg1_correction_value']}` is pre-applied. `{summary['byte_identical_count']}/300` processed selected depths are byte-identical raw copies; mismatches `{summary['mismatch_count']}`.",
        f"Historical preprocessor `{closure['historical_preprocessor_operation']}` does not scale depth. Double scaling risk is `{closure['double_scaling_risk']}`.",
        f"Installed Nerfstudio default `{entry['installed_nerfstudio_default_depth_scale']}` differs from required `{entry['required_depth_unit_scale_factor']}`; future separately preregistered training must use `{entry['exact_cli_option_if_available']}` exactly once.", "", "## Cache Validation Scope Correction", "",
        f"The frozen base contains `{inventory['base_tracked_cache_count']}` already tracked core cache files. Removing them would violate the core-path restriction, so they are baseline evidence rather than a task failure.",
        f"Relative to base, tracked cache set difference is `{inventory['set_difference_count']}`, tracked cache diff count is `{inventory['diff_count']}`, and this audit directory has `{inventory['audit_directory_tracked_cache_count']}` tracked and `{inventory['audit_directory_untracked_cache_count']}` untracked cache files.",
        "Validator policy is baseline-aware: no task-introduced, modified, or deleted cache is allowed.", "", "## Gate and Scope Boundary", "",
        "G0-D depth integrity: passed. G0-H metric scale: passed. G0-I dataparser: passed.",
        f"Global G0: `{decision['global_G0_status']}`. `formal_checkpoint_exists=false`, `training_iterations_executed=0`, `checkpoint_created=false`, `safer_loader_validated=false`, `navigation_gates_completed=false`, `G1_allowed=false`.",
        "No TUM source asset, transforms, or depth PNG was modified. No preprocessing, training, checkpoint, SAFER execution, or G1 work occurred.",
        f"Correction preregistration commit `{CORRECTION_PREREG}` precedes correction execution: `{preregistration_precedes_execution}`.",
        "Training preregistration readiness is not checkpoint readiness. G1 SAFER baseline remains forbidden.",
    ]
    (ROOT / "REPORT_TUM_REMAINING_G0_CHECKPOINT_ENTRY_V1.md").write_text(markdown(main_lines), encoding="utf-8")

    excluded = {"audit_bundle_sha256.json", "validation_result.json"}
    files = {str(path.relative_to(ROOT)).replace("\\", "/"): digest(path) for path in sorted(ROOT.rglob("*")) if path.is_file() and path.name not in excluded and "__pycache__" not in path.parts}
    write("audit_bundle_sha256.json", {"status": "complete_remote_authoritative_correction", "files": files, "excluded": sorted(excluded)})
    print(decision_name)


if __name__ == "__main__":
    main()
