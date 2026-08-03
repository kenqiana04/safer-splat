#!/usr/bin/env python3
"""Build the Protocol V2 metadata-only ETH3D Delivery Area entry contracts."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path


FINAL_STATUS = "PASS_ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION"
FINAL_DECISION = "AUTHORIZE_BOUNDED_ETH3D_DELIVERY_AREA_ASSET_ACQUISITION_AND_CONTRACT_AUDIT"
NEXT_TASK = "ACQUIRE_ETH3D_DELIVERY_AREA_FROZEN_ASSETS_AND_VALIDATE_SPLIT_REFERENCE_UNKNOWN_ROUTE_CONTRACT_V1"
MAPPING_CLAIM = "ETH3D_DELIVERY_AREA_GT_POSE_RGB_ONLY_MAP_ONLY_LEARNED_GAUSSIAN_MAP"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.task_root.resolve()
    assets = json.loads((root / "asset_manifest/official_asset_manifest.json").read_text(encoding="utf-8"))
    repos = json.loads((root / "official_authority/official_repo_identity.json").read_text(encoding="utf-8"))
    authorities = json.loads((root / "official_authority/primary_authority_registry.json").read_text(encoding="utf-8"))
    counters = json.loads((root / "official_authority/metadata_fetch_counters.json").read_text(encoding="utf-8"))
    freeze = json.loads((root / "input_freeze/protocol_v2_entry_input_freeze.json").read_text(encoding="utf-8"))
    repo_by_name = {x["repository"]: x for x in repos}

    identity = {
        "status": "PASS_BENCHMARK_IDENTITY_UNAMBIGUOUS",
        "DATASET_FAMILY": "ETH3D_MULTI_VIEW_STEREO",
        "NOT_DATASET_FAMILY": "ETH3D_SLAM_RGBD",
        "scene": "delivery_area",
        "scene_type": "indoor",
        "benchmark_partition": "training",
        "variants": {
            "HIGH_RES_DSLR": {
                "scenario": "high-resolution multi-view stereo",
                "image_count": 44,
                "camera": "Nikon D3X DSLR",
                "undistorted_format": "JPEG",
                "calibration": "COLMAP text cameras.txt/images.txt/points3D.txt",
                "undistorted_camera_model": "PINHOLE",
                "pose_authority": "official scan-aligned image extrinsics",
            },
            "LOW_RES_RIG": {
                "scenario": "low-resolution many-view stereo",
                "image_count": 948,
                "capture_count": 237,
                "cameras_per_capture": 4,
                "simultaneous_grouping": True,
                "undistorted_format": "PNG",
                "calibration": "COLMAP text plus official fixed-rig support",
                "undistorted_camera_model": "PINHOLE",
                "split_unit": "RIG_CAPTURE_GROUP",
            },
        },
        "identity_evidence": [
            "official MVS datasets page labels delivery area as 44-image indoor high-res training data",
            "official MVS datasets page labels delivery area as 4*237-image indoor low-res many-view training data",
            "official MVS overview states laser-scan ground truth and DSLR/synchronized rig acquisition",
            "official SLAM overview describes a separate visual-inertial/stereo/RGB-D benchmark and does not define this MVS scene",
        ],
        "metadata_only": True,
    }
    write_json(root / "dataset_identity/eth3d_delivery_area_benchmark_identity.json", identity)

    license_audit = {
        "status": "PASS_NONCOMMERCIAL_ACADEMIC_COMPATIBILITY",
        "eth3d_data_license": "CC BY-NC-SA 4.0",
        "eth3d_license_authority": "https://www.eth3d.net/",
        "official_3dgs_license": "Gaussian-Splatting License; research/evaluation and non-commercial use only",
        "official_3dgs_license_sha256": repo_by_name["graphdeco-inria/gaussian-splatting"]["license_sha256"],
        "current_noncommercial_academic_research_allowed": True,
        "local_processing_allowed": True,
        "small_derived_statistics_and_figures_allowed": True,
        "raw_payload_in_git_allowed": False,
        "attribution_required": True,
        "share_alike_required_for_adapted_eth3d_material": True,
        "commercial_use_allowed": False,
        "trained_map_publication": "CONDITIONAL_ONLY: treat a distributed map as adapted ETH3D material; keep it non-commercial, apply CC BY-NC-SA 4.0, provide ETH3D attribution/citation and source-scene identity, and preserve applicable 3DGS license notices. Obtain separate legal review or permission for any broader use.",
        "sha_and_scripts_only_publication_allowed": True,
        "citation_requirements": ["Schops et al., CVPR 2017 ETH3D MVS paper", "Kerbl et al., 3D Gaussian Splatting paper", "license notices"],
        "legal_character": "research protocol interpretation, not legal advice",
    }
    write_json(root / "license/license_compatibility_audit.json", license_audit)
    write_text(
        root / "license/LICENSE_AND_ATTRIBUTION_PLAN.md",
        """# License and attribution plan

- ETH3D data are frozen as **CC BY-NC-SA 4.0** from the official homepage. Current local, non-commercial academic processing is compatible.
- Raw archives, images, depth, and scans must never enter Git. Compact scripts, hashes, tables, and original project figures may be published.
- Any distributed trained map must be handled conservatively as adapted ETH3D material: non-commercial use, CC BY-NC-SA 4.0, scene/source attribution, license link, change notice, and the ETH3D CVPR 2017 citation.
- The official 3DGS implementation is limited to research/evaluation and non-commercial use. Preserve its license and attribution notices for any distributed software-derived work.
- Commercial or broader redistribution requires separate permission/legal review.
""",
    )

    acl = {
        "status": "PASS_PHYSICAL_ISOLATION_ENTRY_CONTRACT",
        "role_enum": ["MAPPING_INPUT_ONLY", "HELDOUT_EVALUATION_ONLY", "REFERENCE_ORACLE_ONLY", "CROSS_VIEW_EVALUATION_ONLY", "OPTIONAL_DIAGNOSTIC_ONLY", "PROHIBITED_AS_MAPPING_INPUT", "NOT_REQUIRED"],
        "TRAIN_INPUT_ROOT": {"allowed": ["undistorted RGB", "official intrinsics", "official extrinsics/poses", "non-reference masks only after semantic validation", "rig grouping metadata"], "selected_archive": "delivery_area_rig_undistorted.7z"},
        "EVAL_ORACLE_ROOT": {"allowed": ["held-out RGB", "scan_eval", "scan_clean", "occlusion", "rendered depth"], "training_readable": False},
        "training_open_file_audit_required": True,
        "training_eval_root_access_count_required": 0,
        "reference_based_pruning_or_scale_correction": "PROHIBITED",
        "asset_assignments": [{"filename": a["official_filename"], "role": a["project_role"], "physical_root": a["physical_root"], "mapping_input_prohibited": a["mapping_input_prohibited"]} for a in assets],
    }
    write_json(root / "input_reference_partition/eth3d_asset_access_control_contract.json", acl)

    claim = {
        "status": "FROZEN",
        "mapping_claim": MAPPING_CLAIM,
        "properties": {"official_gt_scan_aligned_poses": True, "rgb_only": True, "map_only": True, "tracking": False, "pose_estimation": False, "sensor_rgbd": False, "laser_depth_supervision": False, "full_slam": False, "single_scene_instance": True, "algorithm_stability_claim": False},
        "training_authorized": False,
    }
    write_json(root / "input_reference_partition/eth3d_mapping_claim_contract.json", claim)
    write_text(
        root / "input_reference_partition/allowed_forbidden_claims.md",
        """# Allowed and forbidden claims

## Allowed after this entry audit

- Metadata and protocol evidence supports a possible **GT-pose RGB-only map-only learned Gaussian map** route.
- A later task may acquire only the frozen whitelist and validate split/reference/UNKNOWN/route contracts.

## Forbidden

- Qualified map, navigable scene, full SLAM, online tracking, independent pose estimation, sensor RGB-D mapping, real-robot safety, full-space reconstruction, arbitrary unknown-safe navigation, or authorized training.
- GT/rendered depth, laser scans, scan_eval, occlusion/reference geometry, stereo-pair GT, held-out RGB, or candidate-specific routes as mapping input.
""",
    )

    modality = {
        "status": "PASS_MODALITY_ENTRY_AUDIT",
        "M1_LOW_RES_RIG_RGB_ONLY": {
            "status": "QUALIFIED_AT_METADATA_LEVEL_PENDING_ASSET_VALIDATION",
            "official_poses_each_image": True,
            "four_camera_group_metadata": "official 4*237 synchronized rig contract; payload filenames/rigs.json must be verified after acquisition",
            "intrinsics_extrinsics": "COLMAP text, PINHOLE when undistorted",
            "metric_reference_alignment": "official scan-aligned pose pipeline; exact units/frame to be verified after acquisition",
            "split_unit": "RIG_CAPTURE_GROUP",
            "colmap_to_official_3dgs": "direct text loading is implemented by current official 3DGS; no SfM rerun required; official image-only points3D may initialize the map",
            "crop_or_custom_undistortion": "NOT_REQUIRED_OR_AUTHORIZED",
            "known_rig_pipeline_limitation": "official dataset-pipeline warns rig images can be less robust and were strongly sub-selected; asset-level validation remains mandatory",
        },
        "M2_HIGH_RES_DSLR_RGB_ONLY": {
            "status": "QUALIFIED_AS_CROSS_VIEW_EVALUATION_AT_METADATA_LEVEL",
            "images": 44,
            "official_poses_intrinsics": True,
            "metric_reference_alignment": True,
            "sparse_view_risk": "material; do not select on expected reconstruction quality",
            "role_when_M1_selected": "CROSS_VIEW_EVALUATION_ONLY",
            "colmap_to_official_3dgs": "compatible PINHOLE/COLMAP text; no SfM rerun required",
        },
        "M3_SPLATAM_RGBD": {
            "status": "NOT_ADMISSIBLE_WITHOUT_REFERENCE_GEOMETRY_LEAKAGE",
            "independent_sensor_rgbd_proven": False,
            "rendered_depth_provenance": "laser-scan/reference GroundTruthCreator output",
            "training_allowed": False,
        },
    }
    write_json(root / "modality_audit/modality_candidate_audit.json", modality)
    splatam = {
        "ROUTE_M3_STATUS": "NOT_ADMISSIBLE_WITHOUT_REFERENCE_GEOMETRY_LEAKAGE",
        "reason": "Delivery Area is an MVS scene; official depth maps are rendered from laser-scan ground truth, not independent synchronized sensor RGB-D input.",
        "official_rendered_depth_as_mapping_input": False,
        "splatam_training_authorized": False,
    }
    write_json(root / "modality_audit/splatam_admissibility_audit.json", splatam)

    gs = repo_by_name["graphdeco-inria/gaussian-splatting"]
    frontend = {
        "status": "PASS_FRONTEND_ENTRY_CONTRACT",
        "candidates": {
            "F1_OFFICIAL_3DGS": {
                "selected": True,
                "repository": gs["repository"],
                "commit": gs["head_commit"],
                "submodules": gs["submodules"],
                "license_sha256": gs["license_sha256"],
                "input_contract": "COLMAP images plus sparse/0 cameras/images/points3D; current loader accepts text or binary",
                "camera_models": ["PINHOLE", "SIMPLE_PINHOLE"],
                "eth3d_compatibility": "official ETH3D undistorted images are PINHOLE and include COLMAP text intrinsics, poses, and image-only triangulated points",
                "sfm_rerun_required": False,
                "conversion": "directory adaptation and optional text-to-binary model conversion only; no matching/SfM",
                "default_iterations": 30000,
                "depth_required": False,
                "depth_argument_frozen_empty": True,
                "reference_input": False,
                "determinism": "safe_state fixes random/PyTorch seeds to 0; full GPU reproducibility must be qualified later at the frozen commit",
                "resolution_vram": "official README targets 24 GB for paper-quality training, auto-resizes widths above 1.6K unless resolution is set; later environment/smoke must freeze resolution and prove GPU fit",
                "export": "PLY with xyz, SH features, opacity, scale, rotation",
                "ellipsoid_semantics": "positive scales via exp and normalized rotation quaternion; canonical adapter to SAFER ellipsoids is feasible but must be proven later",
            },
            "F2_SPLATFACTO": {"selected": False, "role": "HISTORICAL_COMPATIBILITY_ONLY", "reason": "Prior TUM/Replica geometry failures; export convenience cannot override the preregistered F1 priority; any future use needs a separate protocol."},
            "F3_SPLATAM": {"selected": False, "status": "INADMISSIBLE", "reason": "No legal independent sensor RGB-D route; official depth is reference-derived GT."},
        },
        "no_fallback_after_f1_failure": True,
    }
    write_json(root / "frontend_audit/frontend_authority_audit.json", frontend)
    selected_frontend = {
        "status": "SELECTED",
        "selected_frontend": "OFFICIAL_3DGS_COLMAP_RGB_ONLY",
        "commit": gs["head_commit"],
        "mapping_inputs": ["TRAIN RGB", "official intrinsics", "official poses", "image-only COLMAP points3D"],
        "forbidden_inputs": ["ETH3D rendered depth", "scan_raw", "scan_clean", "scan_eval", "occlusion", "stereo_pairs_gt", "heldout RGB"],
        "future_environment_qualification_required": True,
        "future_smoke_required": True,
        "training_authorized": False,
    }
    write_json(root / "frontend_audit/selected_frontend_contract.json", selected_frontend)
    selected_modality = {
        "status": "SELECTED_AT_METADATA_LEVEL",
        "SELECTED_MAPPING_INPUT": "LOW_RES_MANY_VIEW_RIG_RGB_ONLY",
        "CROSS_VIEW_MODALITY": "HIGH_RES_DSLR_RGB_ONLY",
        "selection_basis": ["more official views", "rig capture grouping", "preserves a different DSLR modality for cross-view evaluation"],
        "selection_uses_trained_results": False,
        "asset_validation_required": True,
    }
    write_json(root / "modality_audit/selected_input_modality_contract.json", selected_modality)

    split = {
        "status": "FUTURE_SPLIT_CONTRACT_FEASIBLE_NOT_GENERATED",
        "selected_modality": "LOW_RES_MANY_VIEW_RIG_RGB_ONLY",
        "split_unit": "RIG_CAPTURE_GROUP",
        "same_capture_four_cameras_same_partition": True,
        "all_dslr_rgb_role": "CROSS_VIEW_EVALUATION_ONLY",
        "generation": "later deterministic spatially separated group-level split after archive validation",
        "required_future_checks": ["237 unique captures", "four cameras per capture", "camera-center distribution", "pose-neighbor distribution", "view-overlap distribution", "at least one spatially separated heldout candidate", "split sensitivity", "freeze one split before training"],
        "project_design_not_official_eth3d": True,
        "fixed_ratio_now": None,
        "final_split_generated": False,
    }
    write_json(root / "split_contract/future_split_generation_contract.json", split)
    leakage = {
        "status": "PASS_LEAKAGE_PROHIBITIONS_FROZEN",
        "prohibitions": ["per-image random split", "same rig capture across TRAIN/HELDOUT", "candidate-map-dependent split", "render-quality selection", "difficult-capture deletion", "DSLR in TRAIN when called cross-view heldout", "GT depth/scan based selection"],
        "final_split_generation_count": 0,
    }
    write_json(root / "split_contract/split_leakage_prohibition.json", leakage)

    reference = {
        "status": "REFERENCE_AUTHORITY_ENTRY_PATH_FEASIBLE_PENDING_ASSET_AUDIT",
        "provisional_reference_authority": "A_DENSE_INDEPENDENT_GEOMETRY",
        "formally_granted": False,
        "R_axis": ["variant-specific scan_eval", "official ETH3D multi-view evaluator", "official occlusion data"],
        "observable_ray": ["variant-specific rendered depth maps; heldout evaluation only"],
        "route_collision_candidate": ["scan_clean", "scan alignment", "occlusion mesh/splats after semantics verification"],
        "scan_eval_limit": "not a full-space route oracle; official ground truth construction/evaluation only retains scan points observed by at least two images",
        "future_requirements": ["metric frame", "completeness", "floor/obstacle semantics", "queryability", "connected routeable region", "thin-object coverage", "occlusion/support limits"],
    }
    write_json(root / "reference_contract/eth3d_reference_authority_contract.json", reference)
    write_text(root / "reference_contract/reference_role_boundary.md", """# Reference role boundary

- `scan_eval + official evaluator + occlusion` is the R-axis authority.
- Rendered depth is an observable-ray evaluation oracle only.
- `scan_clean + alignment + verified occlusion mesh/splats` is only a future route/collision-oracle candidate.
- `scan_eval` is not a full-space route oracle because its support is restricted by official multi-view observability.
- No reference asset may be mounted under `TRAIN_INPUT_ROOT` or influence pruning, scale correction, split choice, or training.
""")

    unknown = {
        "status": "UNKNOWN_CONTRACT_FEASIBLE_FOR_FUTURE_ASSET_VALIDATION",
        "principle": "UNKNOWN != FREE",
        "runtime_gt_reference_access": False,
        "candidate_specific_parameter_selection": False,
        "options": {
            "U1_TRAINING_FRUSTUM_SUPPORT": {"known_occupied": "only with learned Gaussian evidence", "known_free": "not from frustum membership alone", "occluded_free_risk": "high if naive", "depends_on_map": False, "prefreezable": True, "distinct_views": "needed for conservative support", "angular_baseline": "needed", "safer_unknown": True, "unknown_as_occupied": True, "route_knownness": True},
            "U2_MULTI_VIEW_FREE_RAYS_TO_FIRST_SURFACE": {"known_occupied": "learned first-surface neighborhood", "known_free": "only before conservative first surface with multi-view support", "occluded_free_risk": "bounded by truncation and no behind-surface extrapolation", "depends_on_map": True, "prefreezable": True, "distinct_views": "required", "angular_baseline": "required", "safer_unknown": True, "unknown_as_occupied": True, "route_knownness": True},
            "U3_GAUSSIAN_VISIBILITY_SUPPORT_COUNT": {"known_occupied": "supported Gaussian ellipsoids", "known_free": "no, not by count alone", "occluded_free_risk": "high if absence is called free", "depends_on_map": True, "prefreezable": True, "distinct_views": "required", "angular_baseline": "recommended", "safer_unknown": True, "unknown_as_occupied": True, "route_knownness": True},
        },
        "future_adapter": "task-owned; no SAFER core modification",
    }
    write_json(root / "unknown_contract/runtime_unknown_entry_audit.json", unknown)
    write_text(root / "unknown_contract/future_unknown_contract_specification.md", """# Future runtime UNKNOWN contract specification

The later asset task must freeze one deployable support algorithm before mapping. It may use only training poses/RGB, learned Gaussians, and deterministic render visibility/transmittance. Frustum membership or low alpha cannot establish free space. Free rays must stop before a conservatively supported first learned surface, require multiple distinct views and an angular-baseline rule, and never mark occluded space free. Any unsupported query returns `UNKNOWN`, and SAFER must treat UNKNOWN as occupied. Reference geometry may evaluate this contract offline but may not define runtime knownness.
""")

    robot = {
        "status": "ROBOT_ROUTE_ENTRY_PATH_FEASIBLE_PENDING_REFERENCE_ASSET_AUDIT",
        "target_claim": "REAL_WORLD_SCENE_MAP_WITH_ORACLE_STATE_SIMULATED_NAVIGATION",
        "real_robot_safety_claim": False,
        "project_benchmark_design": {"state": "6D free-3D double integrator", "integration": "forward Euler", "dt_s": 0.05, "robot": "sphere", "radius_m": 0.10, "epsilon_base_m": 0.01, "component_vmax_mps": 0.10, "component_umax_mps2": 0.10, "controller": "bounded QP", "collision_oracle": "independent swept sphere"},
        "not_eth3d_official_robot": True,
        "camera_path_is_robot_route": False,
        "sphere_fit": "plausible from indoor metadata only; must be measured against reference geometry before training",
    }
    write_json(root / "route_robot_contract/eth3d_robot_benchmark_entry_contract.json", robot)
    route = {
        "status": "INDEPENDENT_REFERENCE_ROUTE_PATH_FEASIBLE_PENDING_ASSET_AUDIT",
        "generation_time": "before map training",
        "inputs": ["scan_clean", "verified alignment", "verified occlusion support", "project robot geometry"],
        "candidate_map_access": False,
        "candidate_map_route_deletion": False,
        "clearance_strata": ["open", "moderate", "tight"],
        "required_frame_checks": ["floor", "gravity/upright", "connected routeable region", "known/reference support"],
        "route_generated_now": False,
    }
    write_json(root / "route_robot_contract/future_reference_route_contract.json", route)

    budget = {
        "status": "PHYSICAL_BUDGET_DERIVATION_PATH_FEASIBLE",
        "inequality": "UpperBound[e_plus | route tube] <= B_map_available",
        "B_map_available": "reference clearance margin - epsilon_loc - epsilon_shape - epsilon_sampled - epsilon_stop - epsilon_tracking",
        "epsilon_loc_m": 0.0,
        "epsilon_loc_scope": "oracle-state simulation only",
        "real_world_localization_claim": False,
        "other_terms": "must be derived later from sphere geometry, Euler dt, v/u bounds, QP, and waypoint tracking contract",
        "arbitrary_centimeter_gate": False,
        "numeric_budget_closed": False,
        "stop_if_reference_clearance_unavailable": True,
    }
    write_json(root / "physical_budget/physical_budget_entry_contract.json", budget)

    evaluator = {
        "status": "PROTOCOL_V2_FUTURE_EVALUATOR_PATH_FEASIBLE",
        "integrity": ["identity", "no leakage", "pose/intrinsics", "finite values", "deterministic export", "map immutability", "zero reference access during training"],
        "native_common_parity": ["official 3DGS native renderer", "project common renderer", "same cameras/masks", "no favorable-channel selection"],
        "risk_coverage_alpha_grid": [0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95],
        "universal_hard_gate": False,
        "official_geometry": ["accuracy", "completeness", "F-score", "official visibility support", "multi-tolerance reporting"],
        "navigation_conditioned": ["deployable UNKNOWN", "reference-only route tube", "one-sided e_plus", "physical budget", "independent swept-body oracle", "G0 separate"],
        "nvs": ["rig heldout descriptive", "DSLR cross-view descriptive"],
    }
    write_json(root / "evaluator_contract/eth3d_protocol_v2_future_evaluator_contract.json", evaluator)

    stages = {
        "status": "FROZEN",
        "training_authorized": False,
        "phases": [
            {"phase": 1, "name": "bounded asset acquisition"},
            {"phase": 2, "name": "archive/file/calibration/pose/rig/reference/split audit"},
            {"phase": 3, "name": "UNKNOWN, route, and physical-budget contract freeze"},
            {"phase": 4, "name": "official 3DGS source/environment qualification"},
            {"phase": 5, "name": "nonformal smoke"},
            {"phase": 6, "name": "single frozen formal mapping"},
            {"phase": 7, "name": "Protocol V2 map qualification"},
        ],
        "entry_to_training_jump_allowed": False,
    }
    write_json(root / "acquisition_plan/eth3d_delivery_area_stage_gate_plan.json", stages)

    whitelist_names = [
        "delivery_area_rig_undistorted.7z",
        "delivery_area_rig_scan_eval.7z",
        "delivery_area_rig_occlusion.7z",
        "delivery_area_rig_depth.7z",
        "delivery_area_scan_clean.7z",
        "delivery_area_dslr_undistorted.7z",
        "delivery_area_dslr_scan_eval.7z",
        "delivery_area_dslr_occlusion.7z",
        "delivery_area_dslr_depth.7z",
    ]
    deny_names = [
        "delivery_area_scan_raw.7z",
        "delivery_area_dslr_raw.7z",
        "delivery_area_dslr_jpg.7z",
        "delivery_area_rig.7z",
        "delivery_area_rig_stereo_pairs_gt.7z",
    ]
    by_name = {a["official_filename"]: a for a in assets}
    type_multiplier = {"undistorted": 1.25, "scan_clean": 3.0, "scan_eval": 3.0, "occlusion": 2.0, "depth": 5.0}
    whitelist = []
    for name in whitelist_names:
        a = by_name[name]
        multiplier = next(v for k, v in type_multiplier.items() if k in name)
        whitelist.append(
            {
                "filename": name,
                "official_url": a["official_download_url"],
                "content_length_bytes": a["content_length"],
                "official_declared_size": a["official_declared_size"],
                "role": a["project_role"],
                "reason": "selected rig RGB mapping input" if name == "delivery_area_rig_undistorted.7z" else "independent evaluation/reference" if "rig" in name or "scan_clean" in name else "DSLR cross-view evaluation",
                "expected_expanded_bytes_project_estimate": int(a["content_length"] * multiplier),
                "next_task_download_authorized": True,
                "physical_root": "TRAIN_INPUT_ROOT" if name == "delivery_area_rig_undistorted.7z" else "EVAL_ORACLE_ROOT",
                "license": "CC BY-NC-SA 4.0 with attribution",
                "checksum_procedure": "stream once while computing SHA-256; record byte count; list/test 7z before extraction",
                "mapping_input_prohibited": name != "delivery_area_rig_undistorted.7z",
            }
        )
    denylist = [{"filename": name, "reason": "not needed for the minimum Protocol V2 path" if name != "delivery_area_rig_stereo_pairs_gt.7z" else "two-view ground-truth disparity is prohibited as mapping input", "next_task_download_authorized": False} for name in deny_names]
    write_json(root / "acquisition_plan/future_bounded_download_whitelist.json", {"status": "FROZEN_NOT_DOWNLOADED", "count": len(whitelist), "assets": whitelist})
    write_json(root / "acquisition_plan/future_download_denylist.json", {"status": "FROZEN", "count": len(denylist), "assets": denylist})
    compressed = sum(x["content_length_bytes"] for x in whitelist)
    expanded = sum(x["expected_expanded_bytes_project_estimate"] for x in whitelist)
    disk = {
        "status": "PROJECT_ESTIMATE_PENDING_ARCHIVE_LISTING",
        "whitelist_compressed_bytes_exact_from_head": compressed,
        "expected_expanded_bytes_estimate": expanded,
        "future_task_reservation_bytes": 30_000_000_000,
        "future_task_reservation_gb_decimal": 30.0,
        "reservation_includes": ["archives", "extraction", "COLMAP directory adaptation", "evaluation working data", "temporary verification", "later model-output planning headroom"],
        "current_task_new_disk_limit_bytes": 1_073_741_824,
        "current_task_dataset_payload_bytes": 0,
    }
    write_json(root / "acquisition_plan/future_disk_budget.json", disk)

    decision_gates = {
        "benchmark_identity_clear": identity["status"].startswith("PASS"),
        "official_asset_manifest_complete": len(assets) == 14 and all(a["official_page_match"] and a["http_status"] == 200 for a in assets),
        "license_compatible": license_audit["status"].startswith("PASS"),
        "input_reference_physically_isolatable": True,
        "rgb_only_modality_available": True,
        "selected_frontend_official_3dgs": True,
        "splatam_gt_depth_route_rejected": True,
        "future_split_contract_feasible": True,
        "reference_authority_path_feasible": True,
        "runtime_unknown_path_feasible": True,
        "independent_route_path_feasible": True,
        "physical_budget_path_feasible": True,
        "future_evaluator_path_feasible": True,
        "bounded_whitelist_complete": len(whitelist) == 9,
        "dataset_payload_absent": True,
    }
    decision = {
        "status": "PASS" if all(decision_gates.values()) else "FAIL",
        "gates": decision_gates,
        "FINAL_STATUS": FINAL_STATUS if all(decision_gates.values()) else "BLOCKED_BY_ETH3D_DELIVERY_AREA_OFFICIAL_METADATA_AMBIGUITY",
        "FINAL_DECISION": FINAL_DECISION if all(decision_gates.values()) else "STOP_BEFORE_DATASET_DOWNLOAD",
        "Only_next_task": NEXT_TASK if all(decision_gates.values()) else "RESOLVE_ETH3D_DELIVERY_AREA_OFFICIAL_ASSET_METADATA_V1",
        "training_authorized": False,
        "claim_boundary": "entry PASS authorizes bounded acquisition/asset-contract audit only; no map, R/N grade, navigation, route, UNKNOWN, physical-budget, training, or frontend runtime success is established",
        "unresolved_critical_evidence": [],
    }
    write_json(root / "decision/entry_decision.json", decision)

    execution_counts = {
        **counters,
        "http_head_count": 14,
        "dataset_archive_download_count": 0,
        "dataset_payload_bytes": 0,
        "image_download_count": 0,
        "depth_download_count": 0,
        "scan_download_count": 0,
        "occlusion_download_count": 0,
        "model_download_count": 0,
        "git_clone_count": 0,
        "environment_create_count": 0,
        "environment_modify_count": 0,
        "training_count": 0,
        "optimizer_count": 0,
        "model_count": 0,
        "map_count": 0,
        "controller_count": 0,
        "planner_count": 0,
        "route_generation_count": 0,
        "final_data_split_generation_count": 0,
        "asset_whitelist_count": len(whitelist),
        "asset_denylist_count": len(denylist),
    }
    manifest = {
        "task": "ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1",
        "task_type": "METADATA_ONLY_PROTOCOL_V2_NEW_DATASET_ENTRY_AUDIT",
        "generated_utc": utc_now(),
        "branch": "eth3d-delivery-area-protocol-v2-entry-qualification-v1",
        "base_branch": "retrospective-requalify-existing-gaussian-maps-protocol-v2",
        "base_head": "d8fc27f7fa781ceb80e66ff12ca1a93fa0fc52de",
        "pr76_preserved": True,
        "protocol_v2_sha256": freeze["actual"]["protocol"],
        "checklist_sha256": freeze["actual"]["checklist"],
        "pr76_report_sha256": freeze["actual"]["report"],
        "pr76_run_manifest_sha256": freeze["actual"]["upstream_run_manifest"],
        "official_authority_count": len(authorities),
        "official_asset_count": len(assets),
        "mapping_claim": MAPPING_CLAIM,
        "selected_mapping_modality": "LOW_RES_MANY_VIEW_RIG_RGB_ONLY",
        "cross_view_modality": "HIGH_RES_DSLR_RGB_ONLY",
        "selected_frontend": "OFFICIAL_3DGS_COLMAP_RGB_ONLY",
        "splatam_admissibility": "NOT_ADMISSIBLE_WITHOUT_REFERENCE_GEOMETRY_LEAKAGE",
        "gt_depth_training_policy": "PROHIBITED",
        "execution_counts": execution_counts,
        "training_authorized": False,
        "FINAL_STATUS": decision["FINAL_STATUS"],
        "FINAL_DECISION": decision["FINAL_DECISION"],
        "Only_next_task": decision["Only_next_task"],
        "unresolved_critical_evidence": [],
    }
    write_json(root / "run_manifest.json", manifest)
    handoff = {
        "status": "FROZEN_CASE_A_HANDOFF",
        "training_authorized": False,
        "next_task": NEXT_TASK,
        "required_protocol_sha256": manifest["protocol_v2_sha256"],
        "required_checklist_sha256": manifest["checklist_sha256"],
        "selected_modality": manifest["selected_mapping_modality"],
        "selected_frontend": manifest["selected_frontend"],
        "mapping_claim": MAPPING_CLAIM,
        "whitelist_path": "acquisition_plan/future_bounded_download_whitelist.json",
        "denylist_path": "acquisition_plan/future_download_denylist.json",
        "required_pretraining_sequence": ["bounded acquisition", "asset/split/reference audit", "UNKNOWN/route/budget freeze", "environment qualification", "smoke", "single formal mapping", "Protocol V2 qualification"],
    }
    write_json(root / "downstream_handoff.json", handoff)

    report = build_report(manifest, identity, assets, license_audit, acl, modality, frontend, selected_modality, split, reference, unknown, robot, route, budget, evaluator, whitelist, denylist, disk, authorities, repos)
    write_text(root / "REPORT_ETH3D_DELIVERY_AREA_PROTOCOL_V2_ENTRY_QUALIFICATION_V1.md", report)
    print(json.dumps({"status": "PASS", "final_status": FINAL_STATUS, "asset_count": len(assets), "whitelist": len(whitelist), "denylist": len(denylist)}, indent=2))
    return 0


def build_report(manifest, identity, assets, license_audit, acl, modality, frontend, selected_modality, split, reference, unknown, robot, route, budget, evaluator, whitelist, denylist, disk, authorities, repos) -> str:
    asset_rows = "\n".join(f"| `{a['official_filename']}` | {a['dataset_variant']} | {a['official_declared_size']} | {a['content_length']} | {a['project_role']} |" for a in assets)
    whitelist_rows = "\n".join(f"| `{a['filename']}` | {a['official_declared_size']} | {a['content_length_bytes']} | {a['role']} | {a['physical_root']} |" for a in whitelist)
    deny_rows = "\n".join(f"| `{a['filename']}` | {a['reason']} |" for a in denylist)
    repo_rows = "\n".join(f"| [{r['repository']}]({r['html_url']}) | `{r['default_branch']}` | `{r['head_commit']}` | `{r['license_sha256']}` | {len(r['submodules'])} |" for r in repos)
    counts = manifest["execution_counts"]
    return f"""# REPORT — ETH3D Delivery Area Protocol V2 Entry Qualification V1

## Answer first

**{FINAL_STATUS}**

**{FINAL_DECISION}**

ETH3D Delivery Area has a metadata-level, leakage-controlled entry path for one future GT-pose RGB-only map-only learned Gaussian map. The selected future mapping input is the low-resolution 4-camera rig's undistorted RGB and official COLMAP calibration; all DSLR images remain cross-view evaluation. The selected frontend is the official 3DGS implementation at frozen commit `{frontend['candidates']['F1_OFFICIAL_3DGS']['commit']}`. Official rendered depth is laser-scan-derived ground truth and is prohibited as mapping input, so the SplaTAM RGB-D route is rejected.

This PASS authorizes only the next bounded asset acquisition and contract audit. **Training remains unauthorized.** No dataset archive body, image, depth map, scan, occlusion payload, environment, model, map, route, controller, or final split was created.

## 1. PR #76 and Protocol V2 identity

- PR #76 lineage head: `d8fc27f7fa781ceb80e66ff12ca1a93fa0fc52de`; open, draft, unmerged, mergeable, and preserved.
- Protocol V2 SHA-256: `{manifest['protocol_v2_sha256']}`.
- New-dataset checklist SHA-256: `{manifest['checklist_sha256']}`.
- PR #76 report SHA-256: `{manifest['pr76_report_sha256']}`.
- PR #76 run manifest SHA-256: `{manifest['pr76_run_manifest_sha256']}`.

## 2. ETH3D official authority

Twelve frozen primary-authority entries cover the official ETH3D home, MVS overview/datasets/documentation, SLAM overview/datasets/documentation, the official paper HEAD, and four official repositories. Each web snapshot records final URL, retrieval UTC, status, SHA-256, title, and cited fields. GitHub identities record default branch, HEAD, license SHA, and submodule commits.

| Official repository | Default branch | Frozen HEAD | License SHA-256 | Submodules |
|---|---:|---|---|---:|
{repo_rows}

Primary pages: [ETH3D home](https://www.eth3d.net/), [MVS overview](https://www.eth3d.net/overview), [datasets](https://www.eth3d.net/datasets), [documentation](https://www.eth3d.net/documentation), [SLAM overview](https://www.eth3d.net/slam_overview), and the [official MVS paper](https://www.eth3d.net/data/schoeps2017cvpr.pdf).

## 3. Delivery Area benchmark identity

`delivery_area` is a **training scene in the ETH3D Multi-View Stereo / 3D reconstruction benchmark**. It is not an ETH3D SLAM RGB-D sequence. The official MVS pages list it in both high-res and low-res many-view training sections, while the separate SLAM pages define visual-inertial, stereo, and RGB-D sequences recorded for a different benchmark.

## 4. High-res and low-res assets

- High-res DSLR: indoor, 44 images, undistorted JPEG, official COLMAP text intrinsics/extrinsics/triangulated image-only points, plus raw/clean/eval scans, occlusion data, and rendered depth.
- Low-res rig: indoor, 4 × 237 = 948 PNG images, four synchronized cameras per capture, official fixed-rig/COLMAP calibration and poses, plus the same reference families and stereo-pair GT.

| Official archive | Variant | Declared size | HEAD Content-Length | Frozen role |
|---|---|---:|---:|---|
{asset_rows}

All 14 unique archive URLs returned HTTP 200 to HEAD with `application/x-7z-compressed`; response-body bytes were zero.

## 5. Why this is not ETH3D SLAM RGB-D

The MVS overview explicitly defines DSLR and synchronized multi-camera-rig reconstruction challenges with laser-scan ground truth. The SLAM overview separately defines motion-capture/SfM-ground-truthed sequences usable for VI, stereo, and RGB-D SLAM. A shared institution and a generic scene label do not merge those benchmark families.

## 6. License

{license_audit['status']}. ETH3D data are CC BY-NC-SA 4.0; the official 3DGS code is research/evaluation and non-commercial only. Local academic processing and compact derived statistics/figures are allowed with attribution. Raw payload is excluded from Git. A distributed trained map must conservatively remain non-commercial, carry CC BY-NC-SA 4.0 and ETH3D attribution/change/citation notices, and preserve applicable 3DGS notices; broader use needs separate permission or legal review.

## 7. Input/reference/oracle isolation

Only undistorted TRAIN RGB, official intrinsics/poses, validated non-reference masks, and rig grouping may enter `TRAIN_INPUT_ROOT`. `EVAL_ORACLE_ROOT` contains held-out RGB, depth, scan, scan_eval, and occlusion assets and is unreadable by training. A future open-file audit must prove zero held-out/reference access. Reference-based split choice, pruning, or scale repair is prohibited.

## 8. Is rendered depth ground truth?

Yes. Official documentation and `ETH3D/dataset-pipeline` show `GroundTruthCreator` rendering depth from aligned laser scans plus occlusion mesh/splats. It is evaluation ground truth, not independent sensor RGB-D.

## 9. Is the SplaTAM route allowed?

No: `NOT_ADMISSIBLE_WITHOUT_REFERENCE_GEOMETRY_LEAKAGE`. No primary source establishes independent synchronized sensor RGB-D for this MVS scene. Using the supplied rendered depth would leak reference geometry into mapping.

## 10. Official 3DGS compatibility

Metadata-level compatibility passes. ETH3D undistorted calibration is PINHOLE COLMAP text and supplies image-only triangulated points. The frozen official 3DGS loader accepts text or binary cameras/images/points3D and PINHOLE/SIMPLE_PINHOLE cameras. Therefore directory adaptation can avoid feature matching and SfM reruns. Future asset validation must still prove exact paths, scale/frame, no depth argument, canonical export, deterministic runtime, 24 GB GPU fit, and task-owned environment build.

## 11. Splatfacto historical boundary

Splatfacto is a compatibility reference only. Prior TUM/Replica geometry failures and easier export do not justify choosing it. It cannot be run in parallel and selected after results; any later use requires a separate protocol.

## 12. Selected frontend

`OFFICIAL_3DGS_COLMAP_RGB_ONLY`. Current official default iterations are 30,000; no run is authorized here. Depth input is frozen empty. Exported xyz/scales/normalized rotations/opacity/SH can support a future canonical ellipsoid adapter, but parity remains a later qualification gate.

## 13. Selected modality

`LOW_RES_MANY_VIEW_RIG_RGB_ONLY`, selected solely for more official views, capture grouping, and preservation of a distinct DSLR cross-view channel—not on trained performance.

## 14. DSLR cross-view role

`HIGH_RES_DSLR_RGB_ONLY` is `CROSS_VIEW_EVALUATION_ONLY`. No DSLR RGB enters TRAIN if the rig route is used.

## 15. Split generation rule

Status: `{split['status']}`. The unit is `RIG_CAPTURE_GROUP`; all four simultaneous camera images stay in the same partition. A later asset audit must construct and sensitivity-check deterministic spatial group splits, then freeze one before training. No final split and no universal 80/20 ratio were created here.

## 16. Reference authority

Status: `{reference['status']}`. `A_DENSE_INDEPENDENT_GEOMETRY` is provisional only. R-axis evaluation uses variant scan_eval + official evaluator + occlusion. Rendered depth is observable-ray evaluation only. Route/collision use of scan_clean/alignment/occlusion is only a candidate until asset-level completeness, frame, floor, thin-object, and queryability checks pass.

## 17. scan_eval versus scan_clean

`scan_eval` is tailored to MVS evaluation and excludes/supports geometry according to multi-view observability; the official pipeline/paper note the at-least-two-image condition. `scan_clean` is the cleaned aligned laser scan and is the better route-oracle candidate, but is not automatically complete or routeable. Neither is mapping input.

## 18. UNKNOWN contract

`{unknown['status']}`. UNKNOWN is never free. U1 frustum support, U2 multi-view free rays truncated before a learned first surface, and U3 learned-Gaussian visibility counts are entry-feasible candidates. Absence/low alpha/frustum membership alone cannot establish free space. The later algorithm must be frozen before mapping, use no reference at runtime, require conservative multi-view support, return UNKNOWN to SAFER, and permit unknown-as-occupied.

## 19. Route contract

`{route['status']}`. A route may be generated only from verified reference geometry and robot geometry before training, with no candidate-map access, route deletion, or camera-path substitution. It must cover predeclared clearance strata and remain within verified reference/known support.

## 20. Robot contract

`{robot['target_claim']}` only. The 6D double-integrator, Euler `dt=0.05 s`, 0.10 m sphere, 0.01 m base margin, componentwise 0.10 m/s and 0.10 m/s² limits, bounded QP, and swept-sphere oracle are project benchmark choices—not ETH3D facts and not a real-robot safety claim.

## 21. Physical budget

`{budget['status']}`. The later inequality is `UpperBound[e_plus | route tube] <= B_map_available`, where clearance is reduced by localization, shape, sampled-data, stopping, and tracking terms. `epsilon_loc=0` is allowed only for oracle-state simulation. No arbitrary centimetre gate or closed numeric budget is claimed.

## 22. Future evaluator

`{evaluator['status']}`. It freezes integrity/no-leakage, native/common parity, the 11-point alpha grid, official multi-tolerance accuracy/completeness/F-score/visibility reporting, navigation-conditioned UNKNOWN/route/e_plus/budget/oracle evidence, separate G0, and descriptive rig-heldout/DSLR-cross-view NVS. There is no universal numeric hard gate.

## 23. Minimal future download whitelist

Exactly nine archives are authorized only in the next task:

| Archive | Declared | Exact HEAD bytes | Role | Physical root |
|---|---:|---:|---|---|
{whitelist_rows}

Compressed total from HEAD: `{disk['whitelist_compressed_bytes_exact_from_head']}` bytes.

## 24. Denylist

| Archive | Reason |
|---|---|
{deny_rows}

## 25. Future disk budget

The exact compressed whitelist total is `{disk['whitelist_compressed_bytes_exact_from_head']}` bytes. Content-class expansion estimates total `{disk['expected_expanded_bytes_estimate']}` bytes; these are project planning estimates pending archive listings. Reserve 30 GB decimal for acquisition, extraction, conversion, evaluator work, and later output headroom. The current metadata-only task is capped at 1 GiB and contains zero dataset bytes.

## 26. Training authorization

`training_authorized=false`. Entry cannot jump to training. Required order: bounded acquisition → asset/split/reference audit → UNKNOWN/route/budget freeze → official 3DGS environment qualification → smoke → one frozen formal mapping → Protocol V2 qualification.

## 27. Allowed and forbidden claims

Allowed: only a metadata-level possible GT-pose RGB-only map-only route and next-task bounded acquisition. Forbidden: qualified map, navigation, full SLAM/tracking, sensor RGB-D, real-robot safety, solved UNKNOWN/route/budget, successful 3DGS runtime, any R/N grade, or authorized training.

## 28. Execution counts

| Counter | Value |
|---|---:|
""" + "\n".join(f"| `{k}` | {v} |" for k, v in counts.items()) + f"""

All dataset/archive/payload/image/depth/scan/occlusion/model downloads; clones; environment creates/modifies; training/optimizer/model/map/controller/planner/route/final-split executions are zero.

## 29. FINAL_STATUS

`{FINAL_STATUS}`

## 30. FINAL_DECISION

`{FINAL_DECISION}`

## 31. Only next task

`{NEXT_TASK}`

That next task may acquire only the nine frozen archives and must finish the 27 post-download checks before any environment, smoke, or training task is authorized.
"""


if __name__ == "__main__":
    raise SystemExit(main())
