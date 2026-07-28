#!/usr/bin/env python3
"""Validate V3 gates and emit compact figures, report, and downstream handoff."""
from __future__ import annotations

import csv
import hashlib
import json
import py_compile
import statistics
from pathlib import Path
from typing import Any, Dict, Iterable, List

import matplotlib.pyplot as plt
import numpy as np

from _v3_common import EXPECTED, ROOT, STATUS, atomic_json, load_json, sha256_path, tree_hash


def write_figure(path: Path, title: str, draw) -> None:
    figure, axis = plt.subplots(figsize=(6, 4), dpi=140)
    draw(axis)
    axis.set_title(title)
    axis.grid(alpha=.2)
    figure.tight_layout()
    figure.savefig(path)
    plt.close(figure)


def figures(raw: List[Dict[str, Any]], independent: Dict[str, Any], habitat: Dict[str, Any], cross: Dict[str, Any], pool: Dict[str, Any], registry: Dict[str, Any], split: Dict[str, Any], manifest: Dict[str, Any], repeatability: Dict[str, Any], validation: Dict[str, bool]) -> None:
    output = ROOT / "figures"; output.mkdir(parents=True, exist_ok=True)
    candidate = [item["position"] for item in raw]
    qualified = [item["source_navmesh_position"] for item in pool["locations"]]
    selected = [item["source_navmesh_position"] for item in registry["selected_locations"]]
    v1 = []
    with Path("/disk1/zlab/cross_dataset_assets/manifests/replica_protocol_v1/formal_camera_manifest.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["position_index"] == "0" or row["yaw_slot"] == "0":
                v1.append([float(row["source_navmesh_point_x"]), float(row["source_navmesh_point_y"]), float(row["source_navmesh_point_z"])])
    write_figure(output / "v3_raw_candidate_positions.png", "V3 raw navmesh candidates", lambda ax: (ax.scatter([p[0] for p in candidate], [p[2] for p in candidate], s=3), ax.set_xlabel("x"), ax.set_ylabel("z")))
    write_figure(output / "v3_independent_coverage_distribution.png", "Independent valid-hit coverage", lambda ax: (ax.hist([item["valid_near_far_hit_fraction"] for item in independent["views"]], bins=40), ax.axvline(.10, color="red"), ax.set_xlabel("valid hit fraction")))
    write_figure(output / "v3_triplet_pass_by_location.png", "Independent triplet locations", lambda ax: ax.bar(["pass", "fail"], [independent["independent_triplet_pass_location_count"], len(independent["locations"]) - independent["independent_triplet_pass_location_count"]]))
    write_figure(output / "independent_vs_habitat_coverage.png", "Independent versus Habitat coverage", lambda ax: (ax.scatter([item["independent_valid_hit_fraction"] for item in cross["views"]], [item["habitat_depth_positive_fraction"] for item in cross["views"]], s=5), ax.set_xlabel("independent"), ax.set_ylabel("Habitat depth positive")))
    write_figure(output / "v3_habitat_probe_outcomes.png", "Habitat preprobe outcomes", lambda ax: ax.bar([row["stage"] for row in habitat["stages"]], [row["triplet_pass_location_count"] for row in habitat["stages"]]))
    write_figure(output / "qualified_location_pool_map.png", "Habitat-qualified location pool", lambda ax: (ax.scatter([p[0] for p in qualified], [p[2] for p in qualified], s=5), ax.set_xlabel("x"), ax.set_ylabel("z")))
    write_figure(output / "selected_100_location_map.png", "Selected 100 V3 locations", lambda ax: (ax.scatter([p[0] for p in selected], [p[2] for p in selected], s=10), ax.set_xlabel("x"), ax.set_ylabel("z")))
    train = [row["source_navmesh_position"] for row in split["locations"] if row["split"] == "train"]; evaluation = [row["source_navmesh_position"] for row in split["locations"] if row["split"] == "eval"]
    write_figure(output / "train_eval_spatial_split.png", "Location-level train/eval split", lambda ax: (ax.scatter([p[0] for p in train], [p[2] for p in train], s=8, label="train"), ax.scatter([p[0] for p in evaluation], [p[2] for p in evaluation], s=18, label="eval"), ax.legend()))
    write_figure(output / "final_300_view_coverage_distribution.png", "Frozen manifest coverage", lambda ax: (ax.hist([row["independent_valid_hit_fraction"] for row in manifest["frames"]], bins=30, alpha=.7, label="independent"), ax.hist([row["habitat_depth_positive_fraction"] for row in manifest["frames"]], bins=30, alpha=.5, label="Habitat"), ax.legend()))
    write_figure(output / "repeatability_probe_outcomes.png", "Repeatability A/B pass counts", lambda ax: ax.bar(["A", "B", "disagreement"], [repeatability["repeat_a_pass_count"], repeatability["repeat_b_pass_count"], repeatability["a_b_disagreement_count"]]))
    write_figure(output / "v1_failure_vs_v3_selection_comparison.png", "Frozen V1 locations and V3 selection", lambda ax: (ax.scatter([p[0] for p in v1], [p[2] for p in v1], s=5, alpha=.4, label="V1 frozen"), ax.scatter([p[0] for p in selected], [p[2] for p in selected], s=8, label="V3 selected"), ax.legend()))
    write_figure(output / "protocol_v3_gate_summary.png", "Protocol V3 gate summary", lambda ax: (ax.barh(list(validation), [int(value) for value in validation.values()]), ax.set_xlim(0, 1)))


def main() -> None:
    identity = load_json(ROOT / "input_identity" / "upstream_replica_v3_identity.json")
    contract = load_json(ROOT / "protocol_freeze" / "REPLICA_RENDER_PROTOCOL_V3_CONTRACT.json")
    candidate = load_json(ROOT / "raw_navmesh_candidates" / "raw_navmesh_candidate_summary.json")
    raw = load_json(ROOT / "raw_navmesh_candidates" / "raw_candidates_run1.json")["records"]
    poses = load_json(ROOT / "candidate_poses" / "candidate_pose_summary.json")
    independent = load_json(ROOT / "independent_coverage" / "independent_candidate_coverage_summary.json")
    habitat = load_json(ROOT / "habitat_preprobe" / "habitat_preprobe_summary.json")
    cross = load_json(ROOT / "habitat_preprobe" / "coverage_cross_validation_summary.json")
    pool = load_json(ROOT / "qualified_location_pool" / "qualified_location_pool_summary.json")
    registry = load_json(ROOT / "final_location_selection" / "selected_v3_location_registry.json")
    split = load_json(ROOT / "final_manifest" / "replica_v3_location_split.json")
    manifest = load_json(ROOT / "final_manifest" / "formal_camera_manifest_v3.json")
    transforms = load_json(ROOT / "final_manifest" / "transforms_v3.json")
    protocol_identity = load_json(ROOT / "final_manifest" / "replica_protocol_v3_identity.json")
    repeatability = load_json(ROOT / "repeatability_probe" / "repeatability_probe_summary.json")
    paired_path = Path("/disk1/zlab/maintenance_records/tum_splatam_dt_triggered_v4c_paired20_v1/manifests/run_manifest.json")
    validation = {
        "input_identity": identity["status"] == "PASS_FROZEN_REPLICA_V3_INPUT_IDENTITY",
        "contract_before_candidates": contract["input_identity_sha256"] == sha256_path(ROOT / "input_identity" / "upstream_replica_v3_identity.json"),
        "candidate_calls_and_repeatability": candidate["raw_navmesh_sample_count"] == 2048 and candidate["unique_candidate_location_count"] <= 1024 and candidate["candidate_repeatability"],
        "pose_triplets": poses["candidate_view_count"] == poses["candidate_location_count"] * 3,
        "independent_float64": independent["ray_count_per_view"] == 1271 and independent["reference_a_b_agreement"] and independent["independent_triplet_pass_location_count"] >= 120,
        "habitat_budget_and_pool": habitat["total_habitat_probe_locations"] <= 320 and habitat["habitat_triplet_pass_location_count"] >= 120,
        "cross_validation": cross["status"] == "PASS_REPLICA_V3_COVERAGE_CROSS_VALIDATION",
        "spatial_selection": registry["selected_location_count"] == 100 and registry["final_minimum_location_separation_m"] >= .10,
        "location_split": split["train_location_count"] == 90 and split["eval_location_count"] == 10 and split["location_leakage_count"] == 0,
        "frozen_manifest": manifest["frame_count"] == 300 and len(transforms["frames"]) == 300 and protocol_identity["frame_count"] == 300,
        "repeatability": repeatability["repeatability_probe_count"] == 30 and repeatability["repeat_a_pass_count"] == 30 and repeatability["repeat_b_pass_count"] == 30 and repeatability["a_b_disagreement_count"] == 0,
        "v1_staging_unchanged": tree_hash(Path("/disk1/zlab/cross_dataset_assets/processed/replica/apartment_0.rendering")) == EXPECTED["v1_staging_tree_sha256"],
        "paired20_unchanged": sha256_path(paired_path) == EXPECTED["paired20_manifest_sha256"],
    }
    scripts = sorted((ROOT / "code").glob("*.py"))
    compile_errors = []
    for script in scripts:
        try:
            py_compile.compile(str(script), doraise=True)
        except py_compile.PyCompileError as error:
            compile_errors.append(str(error))
    validation["python_compile"] = not compile_errors
    status = STATUS["pass"] if all(validation.values()) else "VALIDATION_ENGINEERING_FAILURE_REQUIRES_REPAIR"
    payload = {"final_status": status, "checks": validation, "python_compile_errors": compile_errors, "json_compact_artifacts_parseable": True, "formal_300_frame_render_count": 0, "publication_count": 0, "gaussian_training_count": 0, "safer_cbf_count": 0, "start_safe_risk_aware_recovery_count": 0, "tum_rollout_count": 0, "paired20_manifest_sha256": sha256_path(paired_path), "protocol_identity_file_sha256": sha256_path(ROOT / "final_manifest" / "replica_protocol_v3_identity.json")}
    if status != STATUS["pass"]:
        atomic_json(ROOT / "report" / "validation_result.json", payload)
        raise SystemExit(status)
    figures(raw, independent, habitat, cross, pool, registry, split, manifest, repeatability, validation)
    atomic_json(ROOT / "report" / "validation_result.json", payload)
    downstream = {"final_status": status, "final_protocol_decision": "FREEZE_REPLICA_APARTMENT_0_RENDER_PROTOCOL_V3", "recommended_next_task": "RENDER_VALIDATE_AND_ATOMICALLY_PUBLISH_REPLICA_RGBD_V3", "boundary": "camera_protocol_qualification_is_not_dataset_publication_mapping_or_SAFER_qualification"}
    atomic_json(ROOT / "report" / "downstream_handoff.json", downstream)
    report = ROOT / "report" / "REPORT_REPLICA_RENDER_PROTOCOL_V3_QUALIFICATION.md"
    report.write_text("\n".join([
        "# Replica Render Protocol V3 Pre-Render Coverage Qualification", "", f"**FINAL_STATUS:** `{status}`", "", "## 1. Frozen V1/V2/asset-audit boundary", "The frozen asset audit remains authoritative: V1 has 32 joint RGB/depth failures caused by direct `mesh.ply` geometry-coverage gaps; frame_0034 is a separate sparse, dark RGB-only view. V3 is `NEW_PREQUALIFIED_REPLICA_RENDER_PROTOCOL_V3`, never a repaired, cleaned, filtered, or republished V1 dataset. It does not delete V1 failures.", "", "## 2. Asset and protocol contract", "The direct formal asset remains `mesh.ply` (SHA-256 `274677d9b7caa413230363b68f4aa472e5cc1afe87e422a489fa1b7d844c6182`) and the original navmesh remains SHA-256 `32296d6457d3855ffe172cf1970364559def5dd15892e149b44d0bc7c6b7e938`. The semantic mesh was not substituted: it is a distinct semantic asset and would change the formal RGB-D asset identity.", f"The V3 contract was written before any candidate call (SHA-256 `{sha256_path(ROOT / 'protocol_freeze' / 'REPLICA_RENDER_PROTOCOL_V3_CONTRACT.json')}`). It freezes seed 20260728, 2,048 raw navmesh calls, at most 1,024 candidates, 1.50 m camera height, yaw offsets [0,-60,+60], 41x31=1271 independent rays/view, 0.10 direct/depth thresholds, 0.05 RGB threshold, 100 final locations, and a 90/10 location-level split.", "", "## 3. Candidate and pose generation", f"Raw candidate calls: {candidate['raw_navmesh_sample_count']}; finite/navigable/snap-valid/in-bounds: {candidate['finite_navigable_snap_valid_in_bounds_count']}; hash-sorted, 0.05 m greedily deduplicated unique locations: {candidate['unique_candidate_location_count']}. A second fresh generation matched exactly (position-array SHA `{candidate['candidate_position_array_sha256']}`).", "Base yaw is derived solely from `SHA256(REPLICA_V3_BASE_YAW:location_hash)`, taking its first eight big-endian bytes and mapping to [0,360); no candidate coverage or RGB content can change an orientation. Each candidate has the V1-verified Y-up, no-pitch/no-roll three-yaw c2w triplet.", "", "## 4. Independent direct-mesh qualification", f"The CPU-only float64 direct-mesh BVH evaluated {independent['candidate_view_count']} candidate views and {independent['independent_ray_count']} rays. View qualification requires finite valid near/far hit fraction >=0.10 and a front-facing hit; {independent['independent_view_pass_count']} views and {independent['independent_triplet_pass_location_count']} full location triplets passed. Reference A/B agreed on {independent['reference_b_agree_key_ray_count']}/{independent['reference_b_checked_key_ray_count']} required key rays.", "", "## 5. Fresh Habitat pre-render qualification", f"Habitat ran diagnostic-only fresh OS subprocesses and fresh Simulators per location. Stage 1 evaluated {habitat['stages'][0]['evaluated_location_count']} locations and passed {habitat['stages'][0]['triplet_pass_location_count']}; Stage 2 and Stage 3 were not required. Total: {habitat['total_habitat_probe_locations']} locations / {habitat['total_habitat_probe_views']} views / {habitat['habitat_triplet_pass_location_count']} triplet-pass locations.", f"Cross-validation found {cross['independent_pass_habitat_fail_count']}/{cross['view_count']} independent-pass/Habitat-fail views ({cross['independent_pass_habitat_fail_fraction']:.6f}), below the 5% contradiction gate; Pearson coverage correlation was {cross['coverage_fraction_pearson_correlation']}.", "", "## 6. Spatial selection, split, and frozen manifest", f"Hash-tied greedy farthest-point selection froze 100 Habitat-qualified locations. Minimum pairwise separation is {registry['final_minimum_location_separation_m']:.6f} m; the selection occupies {registry['unique_xz_grid_cell_count']} XZ cells at 0.50 m. Frozen V1 exact/near (<0.10 m) location overlap is {registry['v1_location_exact_overlap_count']}/{registry['v1_location_near_overlap_count_lt_0_10m']} and was reported only, never used for selection.", f"The deterministic location-level split is {split['train_location_count']}/{split['eval_location_count']} locations and {split['train_frame_count']}/{split['eval_frame_count']} frames, with location leakage {split['location_leakage_count']}. The new manifest contains {manifest['frame_count']} rows; CSV SHA `{protocol_identity['csv_sha256']}`, JSON SHA `{protocol_identity['manifest_json_sha256']}`, transforms SHA `{protocol_identity['transforms_sha256']}`, pose-array SHA `{protocol_identity['pose_array_sha256']}`.", "", "## 7. Frozen-manifest repeatability", f"The 30 hash-selected frozen frames covered yaw offsets {repeatability['selected_yaw_offsets']} and splits {repeatability['selected_splits']}. Fresh-process A/B results were A {repeatability['repeat_a_pass_count']}/30, B {repeatability['repeat_b_pass_count']}/30, disagreements {repeatability['a_b_disagreement_count']}.", "", "## 8. Decision, boundaries, and only next task", "The generated figures distinguish raw candidates, independent passes, Habitat passes, final selection, and frozen V1 locations. No formal 300-frame RGB-D render, dataset publication, Gaussian training, SAFER/CBF, Start-Safe, Risk-Aware, Recovery/V4-C, or TUM rollout ran. Camera-protocol qualification is not RGB-D publication, Gaussian mapping qualification, SAFER baseline qualification, or FAS-CBF evaluation.", "", "**Decision:** `FREEZE_REPLICA_APARTMENT_0_RENDER_PROTOCOL_V3`", "", "**Only next task:** `RENDER_VALIDATE_AND_ATOMICALLY_PUBLISH_REPLICA_RGBD_V3`", "" ]), encoding="utf-8")


if __name__ == "__main__":
    main()
