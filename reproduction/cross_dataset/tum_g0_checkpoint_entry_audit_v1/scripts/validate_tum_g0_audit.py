#!/usr/bin/env python3
"""Validate the complete TUM G0 correction evidence bundle without training."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[2]
BASE = "0fb8698e8590aead60032487fc3321c07f2fd99c"
CORRECTION_PREREG = "1f15ad20999ebc4b21cb628fc2866b1fc7742bb8"


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def is_cache(path: str) -> bool:
    return path.endswith(".pyc") or "/__pycache__/" in path


def main() -> None:
    contract = load("official_tum_depth_contract.json")
    closure = load("depth_scale_closure.json")
    parser = load("dataparser_correction_result.json")
    preflight = load("remote_server_preflight.json")
    source = load("remote_outputs/source_asset_hash_manifest.json")
    transforms = load("transforms_contract_audit.json")
    decision = load("checkpoint_entry_decision.json")
    entry = load("splatfacto_entry_command.json")
    bundle = load("audit_bundle_sha256.json")
    remote = load("remote_output_manifest.json")
    inventory = load("preexisting_tracked_cache_inventory.json")
    summary = closure["identity_summary"]
    stage_names = [item["stage"] for item in parser["stages"]]
    expected_stages = ["import_environment", "create_config", "instantiate_dataparser", "generate_train_outputs", "generate_eval_outputs", "inspect_transform_shape", "compare_dataparser_transform", "map_parsed_files_to_source", "compare_source_and_parsed_poses", "compute_translation_scale_ratio", "write_results"]
    base_caches = sorted(path for path in command("git", "ls-tree", "-r", "--name-only", BASE).stdout.splitlines() if is_cache(path))
    current_caches = sorted(path for path in command("git", "ls-files").stdout.splitlines() if is_cache(path))
    cache_diff = [line for line in command("git", "diff", "--name-status", BASE, "--").stdout.splitlines() if is_cache(line.split("\t")[-1])]
    audit_rel = "reproduction/cross_dataset/tum_g0_checkpoint_entry_audit_v1"
    audit_tracked = [path for path in command("git", "ls-files", "--", audit_rel).stdout.splitlines() if is_cache(path)]
    audit_untracked = [path for path in command("git", "ls-files", "--others", "--exclude-standard", "--", audit_rel).stdout.splitlines() if is_cache(path)]
    checks: list[tuple[str, bool]] = [
        ("correction_preregistration_is_ancestor", command("git", "merge-base", "--is-ancestor", CORRECTION_PREREG, "HEAD").returncode == 0),
        ("authoritative_host", preflight.get("authoritative_execution_host") == "zlab-Super-Server"),
        ("authoritative_conda", preflight.get("authoritative_conda_env") == "/disk1/zlab/conda_envs/safer_splat_official"),
        ("official_tum_url", contract.get("source_url", "").startswith("https://cvg.cit.tum.de/")),
        ("official_source_hash", len(contract.get("source_page_sha256", "")) == 64),
        ("depth_units", contract.get("depth_units_per_meter") == 5000),
        ("depth_scale", abs(contract.get("depth_unit_scale_factor_meters", 0.0) - 0.0002) <= 1e-12),
        ("zero_no_data", contract.get("zero_semantics") == "missing_value_or_no_data"),
        ("freiburg1_pre_scaled", contract.get("correction_already_applied") is True),
        ("depth_mapping_300", summary.get("mapped_count") == 300 and summary.get("unresolved_mapping_count") == 0),
        ("depth_byte_identity", summary.get("byte_identical_count") == 300 and summary.get("mismatch_count") == 0),
        ("no_double_scaling", closure.get("double_scaling_risk") is False and closure.get("final_depth_contract_status") == "pass"),
        ("future_scale_override", entry.get("required_depth_unit_scale_factor") == 0.0002 and entry.get("explicit_override_required") is True and "depth-unit-scale-factor 0.0002" in entry.get("exact_cli_option_if_available", "")),
        ("dataparser_completed", parser.get("status") == "PASS_DATAPARSER_ONLY" and stage_names == expected_stages and all(item.get("status") == "passed" for item in parser["stages"])),
        ("native_transform_shape", parser.get("dataparser_transform_shape") in ([3, 4], [4, 4]) and parser.get("expected_identity_shape") == parser.get("dataparser_transform_shape")),
        ("native_identity", parser.get("dataparser_transform_identity") is True and parser.get("dataparser_transform_max_abs_error") == 0.0),
        ("dataparser_frame_counts", parser.get("parsed_total_count") == 300 and parser.get("frame_drop_count") == 0 and parser.get("duplicate_parsed_path_count") == 0),
        ("pose_mapping_complete", parser.get("matched_pose_count") == 300 and parser.get("unmatched_pose_count") == 0 and parser.get("unmatched_source_count") == 0 and parser.get("unmatched_parsed_count") == 0),
        ("actual_pose_ratio", parser.get("ratio_median") is not None and abs(parser["ratio_median"] - 1.0) <= 1e-9),
        ("metric_parser_config", parser.get("dataparser_scale_is_one") is True and parser.get("orientation_method") == "none" and parser.get("center_method") == "none" and parser.get("auto_scale_poses") is False),
        ("no_training", parser.get("model_created") is False and parser.get("optimizer_created") is False and parser.get("trainer_created") is False and parser.get("viewer_created") is False and parser.get("training_iterations_executed") == 0 and parser.get("checkpoint_created") is False),
        ("source_assets_unchanged", source.get("unchanged") is True and source.get("transforms_sha256") == transforms.get("sha256")),
        ("correction_decision", decision.get("decision") == "PASS_DEPTH_AND_DATAPARSER_CORRECTION" and decision.get("checkpoint_entry_decision") == "READY_FOR_FORMAL_SPLATFACTO_TRAINING_PREREGISTRATION" and decision.get("global_G0_status") == "partial_ready" and decision.get("G1_allowed") is False),
        ("freeze_zero_diff", command("git", "diff", "--exit-code", BASE, "--", "reproduction/experiment_protocol_freeze_v1").returncode == 0),
        ("core_zero_diff", command("git", "diff", "--exit-code", BASE, "--", "cbf", "splat", "ellipsoids", "dynamics", "run.py").returncode == 0),
        ("preexisting_tracked_cache_set_unchanged", base_caches == current_caches and inventory.get("base_tracked_cache_count") == len(base_caches) and inventory.get("current_tracked_cache_count") == len(current_caches) and inventory.get("set_difference_count") == 0),
        ("preexisting_tracked_cache_content_unchanged", not cache_diff and inventory.get("diff_count") == 0),
        ("audit_directory_untracked_cache_absent", not audit_untracked and inventory.get("audit_directory_untracked_cache_count") == 0),
        ("audit_directory_tracked_cache_absent", not audit_tracked and inventory.get("audit_directory_tracked_cache_count") == 0),
        ("core_cache_cleanup_not_attempted", not command("git", "diff", "--name-status", BASE, "--", "cbf", "dynamics", "ellipsoids", "ns_utils", "splat").stdout.strip()),
        ("remote_manifest_hashes", all(sha(ROOT / "remote_outputs" / key) == value for key, value in remote["files"].items())),
        ("bundle_hashes", all((ROOT / key).is_file() and sha(ROOT / key) == value for key, value in bundle["files"].items())),
    ]
    status = "PASS_READY_FOR_TRAINING_PREREGISTRATION" if all(ok for _, ok in checks) else "FAIL"
    result = {"status": status, "checks": [{"check": name, "passed": ok} for name, ok in checks], "cache_policy": {"policy": "no_task_introduced_or_modified_cache", "preexisting_tracked_cache_allowed": True, "base_tracked_cache_count": len(base_caches), "current_tracked_cache_count": len(current_caches), "tracked_cache_set_difference_count": len(set(base_caches).symmetric_difference(current_caches)), "tracked_cache_diff_count": len(cache_diff), "audit_directory_tracked_cache_count": len(audit_tracked), "audit_directory_untracked_cache_count": len(audit_untracked), "core_cache_cleanup_attempted": False}, "authoritative_data_host": "zlab-Super-Server", "authoritative_runtime_host": "zlab-Super-Server", "authoritative_conda_env": preflight.get("authoritative_conda_env"), "authoritative_python": preflight.get("authoritative_python"), "authoritative_gpu": preflight.get("visible_device_0"), "remote_execution_complete": True, "training_iterations_executed": 0, "checkpoint_created": False, "windows_probe_role": "superseded_non_authoritative_local_probe"}
    (ROOT / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(status)
    if status == "FAIL":
        failed = [name for name, ok in checks if not ok]
        raise SystemExit("failed checks: " + ", ".join(failed))


if __name__ == "__main__":
    main()
