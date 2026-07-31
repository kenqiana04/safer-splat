#!/usr/bin/env python3
"""Build the compact manifest, validator, handoff, and final audit report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_common import NO_EXECUTION, sha256_file, stable_digest, write_json


REPORT_NAME = "REPORT_AUDIT_ARKITSCENES_DEPTH_CONFIDENCE_ALIGNMENT_AND_P99_TAIL_V1.md"
FIGURES = [
    "m0_m1_m2_global_quantiles.png",
    "mask_retention_vs_geometry.png",
    "per_frame_median_p99.png",
    "tail_frame_concentration.png",
    "tail_confidence_distribution.png",
    "tail_depth_range_distribution.png",
    "tail_image_border_distribution.png",
    "mesh_ray_coverage_tail.png",
    "temporal_consistency_tail.png",
    "group_supervision_coverage.png",
    "zero_valid_frame_timeline.png",
    "top_anomaly_evidence_montage.png",
    "root_cause_summary.png",
    "decision_tree_result.png",
    "claim_boundary.png",
]
SCRIPTS = [
    "freeze_depth_confidence_audit_inputs.py",
    "audit_confidence_assets.py",
    "audit_confidence_alignment.py",
    "audit_full_train_depth_geometry.py",
    "validate_point_to_mesh_engine.py",
    "render_arkit_mesh_depth.py",
    "build_p99_tail_registry.py",
    "audit_tail_concentration.py",
    "audit_tail_spatial_temporal_causes.py",
    "audit_mask_supervision_structure.py",
    "audit_splatam_zero_mask_semantics.py",
    "run_zero_mask_microtests.py",
    "select_depth_validity_candidate.py",
    "validate_no_execution_boundary.py",
]


def read(root: Path, name: str) -> dict:
    return json.loads((root / name).read_text(encoding="utf-8"))


def pct(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    identity = read(root, "input_freeze/input_identity.json")
    confidence = read(root, "confidence_structural_validation.json")
    values = read(root, "confidence_value_distribution.json")
    alignment = read(root, "confidence_alignment_decision.json")
    geometry = read(root, "full_train_mask_metrics.json")
    engine = read(root, "distance_engine_validation.json")
    supervision = read(root, "mask_supervision_structure.json")
    concentration = read(root, "p99_tail_concentration.json")
    ray = read(root, "mesh_ray_coverage_metrics.json")
    spatial = read(root, "tail_spatial_factorization.json")
    depth = read(root, "tail_depth_range_factorization.json")
    temporal = read(root, "tail_temporal_consistency.json")
    index78 = read(root, "index_78_evidence.json")
    zero = read(root, "splatam_mask_compatibility_decision.json")
    microtest = read(root, "splatam_zero_mask_microtest.json")
    causes = read(root, "tail_cause_summary.json")
    decision = read(root, "decision/decision.json")
    resource = read(root, "resource_boundary_validation.json")

    alignment_second = root / "alignment" / "fresh_process_2" / "confidence_alignment_decision.json"
    alignment_repro = {
        "status": "PASS_ALIGNMENT_FRESH_PROCESS_REPRODUCIBILITY" if alignment_second.is_file() and sha256_file(root / "confidence_alignment_decision.json") == sha256_file(alignment_second) else "FAIL_ALIGNMENT_FRESH_PROCESS_REPRODUCIBILITY",
        "run_1_sha256": sha256_file(root / "confidence_alignment_decision.json"),
        "run_2_sha256": sha256_file(alignment_second) if alignment_second.is_file() else None,
        "deterministic_sha256": alignment["deterministic_sha256"],
    }
    write_json(root / "alignment" / "alignment_fresh_process_reproducibility.json", alignment_repro)

    m0 = geometry["global"]["M0_RAW_POSITIVE"]
    m1 = geometry["global"]["M1_CONFIDENCE_GE1"]
    m2 = geometry["global"]["M2_CONFIDENCE_EQ2"]
    s1 = supervision["masks"]["M1_CONFIDENCE_GE1"]
    s2 = supervision["masks"]["M2_CONFIDENCE_EQ2"]
    tail1 = concentration["TAIL_010_PERCENT"]
    gt030 = concentration["TAIL_GT_030"]
    m0ray = ray["M0_RAW_POSITIVE"]["classes"]
    border = spatial["image_border_bands"]
    depth_bins = depth["depth_bins"]
    report = f"""# ARKitScenes depth-confidence alignment and p99-tail audit V1

## Answer first

`FINAL_STATUS={decision['FINAL_STATUS']}`
`FINAL_DECISION={decision['FINAL_DECISION']}`
`Only next task={decision['Only_next_task']}`

No M0/M1/M2 metric-depth input contract qualifies under the frozen combined geometry and supervision gates. M0 retains adequate supervision but fails p99 (`{m0['p99_m']:.6f} m > 0.30 m`). M1 and M2 pass the unchanged geometry gates, but both fail the preregistered group-support contract because frozen TRAIN groups 3, 6, and 11 contain only 1, 2, and 9 frames respectively, making the required minimum of 10 supported frames arithmetically impossible. M1/M2 also contain 2/4 zero-valid frames, and official SplaTAM's non-tracking depth loss uses an empty masked `mean()`, which the bounded synthetic test confirms is nonfinite.

## PR #71 handoff and why its stop was correct

- Base PR/head: `#71` / `1c55f67e7b93b098c672eb09ff483fd8d037fde9`.
- PR #71 stopped before smoke/training because its 64-frame M0 sample failed p99 while median and p95 passed.
- This audit confirms the same pattern on all 214 TRAIN frames. Stopping before mapper execution was correct: the heavy tail is real under M0 and a replacement validity contract cannot be adopted without violating the frozen supervision gates.

## Frozen input identity

- Scene/visit: `48018874` / `483945`; TRAIN/HELDOUT: 214/53.
- TRAIN raw Git-blob SHA-256: `{identity['manifest_records']['train']['git_blob_sha256']}`; OID: `{identity['manifest_records']['train']['git_blob_oid']}`.
- HELDOUT raw Git-blob SHA-256: `{identity['manifest_records']['heldout']['git_blob_sha256']}`; OID: `{identity['manifest_records']['heldout']['git_blob_oid']}`.
- Git blobs equal the server working copies; ARKitScenes/SplaTAM/rasterizer authorities all match the frozen identities.
- Split identity: `97a707510227271d12859ee78defc0d6170cc24cb67e423568cd1a72e3345dee`; group tuple: `8ad320980bb36edb2accb38629ec3046095c9ef7735fbb748f4e112ee75bd388`.

## Confidence assets, values, and alignment

- All 214 TRAIN and 53 HELDOUT confidence files exist, match manifest timestamps and 192x256 RGB/depth orientation, load deterministically as `uint8`, and contain only values 0/1/2.
- TRAIN value counts: 0=`{values['train']['global_value_counts']['0']}`, 1=`{values['train']['global_value_counts']['1']}`, 2=`{values['train']['global_value_counts']['2']}`.
- TRAIN frames 76 and 79 are genuine checksum-recorded all-zero raw confidence assets. They are not unreadable-file fallbacks; the adapter contains no zero-array fallback.
- The adapter joins confidence from the same manifest row and uses nearest-neighbor resizing.
- The fixed 32-frame identity/dihedral/offset comparison found no nonidentity candidate satisfying the 24/32, +10 percentage-point, official-evidence, and retention requirements. Identity reproduced byte-for-byte in a fresh process (`{alignment['deterministic_sha256']}`).

## Full-TRAIN geometry

Evaluation mode: all positive-depth pixels, no sampling. One shared M0 registry of `{m0['valid_pixel_count']}` pixels was used for all masks.

| Mask | Valid pixels | Retention | Median m | p95 m | p99 m | Max m | Geometry |
|---|---:|---:|---:|---:|---:|---:|---|
| M0 | {m0['valid_pixel_count']} | {m0['retained_fraction_vs_m0']:.6f} | {m0['median_m']:.6f} | {m0['p95_m']:.6f} | {m0['p99_m']:.6f} | {m0['max_m']:.6f} | {'PASS' if m0['geometry_pass'] else 'FAIL'} |
| M1 | {m1['valid_pixel_count']} | {m1['retained_fraction_vs_m0']:.6f} | {m1['median_m']:.6f} | {m1['p95_m']:.6f} | {m1['p99_m']:.6f} | {m1['max_m']:.6f} | {'PASS' if m1['geometry_pass'] else 'FAIL'} |
| M2 | {m2['valid_pixel_count']} | {m2['retained_fraction_vs_m0']:.6f} | {m2['median_m']:.6f} | {m2['p95_m']:.6f} | {m2['p99_m']:.6f} | {m2['max_m']:.6f} | {'PASS' if m2['geometry_pass'] else 'FAIL'} |

The point-to-mesh engine is point-to-triangle surface distance, not nearest vertex. Open3D and independent trimesh R-tree results agree within `{engine['open3d_vs_trimesh_max_abs_difference_m']:.9g} m` over 512 points (required <=1e-6 m); all results are finite.

## Supervision structure

| Mask | Retention | Supported frames | Zero-valid frames | Longest unsupported run | Group gate | Structure result |
|---|---:|---:|---:|---:|---|---|
| M1 | {s1['retained_fraction']:.6f} | {s1['supported_frame_count']}/214 ({pct(s1['supported_frame_fraction'])}) | {s1['zero_valid_frame_count']} | {s1['longest_unsupported_run']} | FAIL | FAIL |
| M2 | {s2['retained_fraction']:.6f} | {s2['supported_frame_count']}/214 ({pct(s2['supported_frame_fraction'])}) | {s2['zero_valid_frame_count']} | {s2['longest_unsupported_run']} | FAIL | FAIL |

The global, frame-fraction, retention, and temporal-run gates pass. The all-eight-group gate fails because groups with fewer than 10 total TRAIN frames cannot supply 10 supported frames. These are preregistered audit design thresholds, not Apple or SplaTAM official thresholds; they were not changed after observing results.

## Tail concentration and attribution

- M0 top 1% registry: `{tail1['pixel_count']}` pixels. The smallest frame sets contributing 50/80/90% are `{tail1['frames_for_50_percent']}` / `{tail1['frames_for_80_percent']}` / `{tail1['frames_for_90_percent']}`.
- M0 error >0.30 m: `{gt030['pixel_count']}` pixels. Confidence-0 accounts for `{pct(gt030['confidence']['0']['fraction'])}`; confidence-1 for `{pct(gt030['confidence']['1']['fraction'])}`; confidence-2 for `{pct(gt030['confidence']['2']['fraction'])}`.
- M0 >0.30 m ray classes: no mesh hit `{pct(m0ray['NO_MESH_RAY_HIT']['fraction'])}`, sensor behind mesh `{pct(m0ray['SENSOR_BEHIND_MESH']['fraction'])}`, sensor in front of mesh `{pct(m0ray['SENSOR_IN_FRONT_OF_MESH']['fraction'])}`.
- No-hit does not dominate M0, so the reference-mesh limitation decision (>50% no-hit and not reduced by confidence filtering) is not met.
- Border bands for M0 >0.30 m: 0-2% `{pct(border['0-2%']['fraction'])}`, 2-5% `{pct(border['2-5%']['fraction'])}`, 5-10% `{pct(border['5-10%']['fraction'])}`, >10% `{pct(border['>10%']['fraction'])}`.
- Depth bins: 0-1 m `{pct(depth_bins['0-1m']['fraction'])}`, 1-2 m `{pct(depth_bins['1-2m']['fraction'])}`, 2-3 m `{pct(depth_bins['2-3m']['fraction'])}`, 3-4 m `{pct(depth_bins['3-4m']['fraction'])}`, >4 m `{pct(depth_bins['>4m']['fraction'])}`.
- Top-20 temporal categories: `{temporal['summary']['category_counts']}`. Official poses only were used; HELDOUT and pose optimization were not used.

## Index 78 evidence

Frame 78 / timestamp `{index78['timestamp']}` has `{index78['positive_depth_pixels']}` positive-depth pixels and confidence counts `{index78['confidence_counts']}`. Its median/p95/p99/max point-to-mesh errors are `{index78['distance_median_m']:.6f}` / `{index78['distance_p95_m']:.6f}` / `{index78['distance_p99_m']:.6f}` / `{index78['distance_max_m']:.6f}` m. `{pct(index78['tail_gt_030_fraction'])}` of pixels exceed 0.30 m; within that tail, `{pct(index78['tail_sensor_in_front_fraction'])}` are sensor-in-front-of-mesh and `{pct(index78['tail_no_mesh_hit_fraction'])}` have no mesh hit. The frame was preserved and not excluded.

## Official SplaTAM zero-mask semantics

- Source audit decision: `{zero['status']}`.
- Synthetic microtest: `{microtest['status']}`.
- Tracking's empty masked sum is finite zero, but mapping's empty masked mean is nonfinite. Initial-frame empty depth also lacks an official skip before empty point-cloud initialization and zero scene-radius calculation.
- Exactly three synthetic forward reductions were used; no real scene, mapper, optimizer, backward, update, or checkpoint was used.

## Cause labels and claim boundary

The top-frame registry uses evidence-bounded multi-label causes: `{causes['label_frame_counts']}`. `DYNAMIC_OR_TRANSIENT_SUSPECT` is used only when both temporal inconsistency and RGB temporal difference evidence are present; it is not a confirmed dynamic-object label.

Allowed claims are limited to data geometry, confidence-tail association, reference-mesh coverage attribution, and pre-training data-contract qualification. This audit does not show that a learned map exists, that confidence masking improves a trained map, that any frame should be deleted, or that SAFER/FAS-CBF/controller execution occurred.

## Execution counts and integrity

`{json.dumps(NO_EXECUTION, sort_keys=True)}`

- GPU execution used by task: 0; the audit ran on CPU.
- Raw assets, canonical manifests, official mesh, PR #71 adapter, SplaTAM authority, environment, masks, poses, intrinsics, and thresholds were not modified.
- No frame was deleted or rerun as a scientific rollout.
- Existing SSH sessions and the persistent reverse-proxy watchdog were not stopped, modified, or rebuilt.

## Final decision

`FINAL_STATUS={decision['FINAL_STATUS']}`
`FINAL_DECISION={decision['FINAL_DECISION']}`
`Only next task={decision['Only_next_task']}`

Recommendation: no mask. {decision['recommendation_reason']}
"""
    report = "\n".join(line.rstrip() for line in report.splitlines()) + "\n"
    (root / REPORT_NAME).write_text(report, encoding="utf-8")
    (root / "report").mkdir(parents=True, exist_ok=True)
    (root / "report" / REPORT_NAME).write_text(report, encoding="utf-8")

    compact_paths = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or "tmp" in path.relative_to(root).parts or path.name == "p99_tail_pixel_registry.csv.zst" or path.suffix == ".log":
            continue
        compact_paths.append(
            {
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    manifest = {
        "task": "AUDIT_ARKITSCENES_DEPTH_CONFIDENCE_ALIGNMENT_AND_P99_TAIL_V1",
        "status": "TERMINAL_AUDIT_COMPLETE",
        "branch": "arkitscenes-depth-confidence-p99-tail-audit-v1",
        "base_pr": 71,
        "base_head": "1c55f67e7b93b098c672eb09ff483fd8d037fde9",
        "scene": "48018874",
        "visit": "483945",
        "train": 214,
        "heldout_structure_only": 53,
        "evaluation_mode": "FULL_ALL_POSITIVE_DEPTH_PIXELS",
        "execution_counts": NO_EXECUTION,
        "implementation_repairs": [
            "distinguished genuine raw all-zero confidence files from silent reader fallback",
            "performed reprojection sanity in original float64 geometry rather than float32 distance-engine coordinates",
        ],
        "scientific_inputs_changed": False,
        "frames_deleted": 0,
        "mask_contract_changed": False,
        "thresholds_relaxed": False,
        "FINAL_STATUS": decision["FINAL_STATUS"],
        "FINAL_DECISION": decision["FINAL_DECISION"],
        "Only_next_task": decision["Only_next_task"],
        "compact_artifacts": compact_paths,
        "server_only_large_artifact": {
            "path": "p99_tail_pixel_registry.csv.zst",
            "size": (root / "p99_tail_pixel_registry.csv.zst").stat().st_size,
            "sha256": sha256_file(root / "p99_tail_pixel_registry.csv.zst"),
        },
    }
    manifest["deterministic_sha256"] = stable_digest({k: v for k, v in manifest.items() if k not in {"compact_artifacts", "deterministic_sha256"}})
    write_json(root / "run_manifest.json", manifest)

    checks = {
        "input_identity": identity["status"] == "PASS_DEPTH_CONFIDENCE_AUDIT_INPUT_IDENTITY",
        "confidence_assets": confidence["status"] == "PASS_CONFIDENCE_ASSET_AND_READER_STRUCTURE",
        "alignment": alignment["status"] == "PASS_CONFIDENCE_IDENTITY_ALIGNMENT_RETAINED",
        "alignment_fresh_process": alignment_repro["status"].startswith("PASS"),
        "distance_engine": engine["status"] == "PASS_EXACT_POINT_TO_TRIANGLE_SURFACE_DISTANCE",
        "full_geometry": geometry["status"] == "PASS_FULL_TRAIN_M0_M1_M2_GEOMETRY_AUDIT",
        "all_15_figures": all((root / "figures" / name).is_file() and (root / "figures" / name).stat().st_size > 0 for name in FIGURES),
        "all_required_scripts": all((root / name).is_file() for name in SCRIPTS),
        "report": (root / REPORT_NAME).is_file(),
        "no_execution_counts": all(value == 0 for value in NO_EXECUTION.values()),
        "resource_boundary": resource["status"] == "PASS_NO_EXECUTION_AND_RESOURCE_BOUNDARY",
        "no_mask_or_frame_change": not decision["mask_contract_modified"] and not decision["frame_deleted"] and not decision["geometry_threshold_relaxed"],
        "decision_consistent": decision["FINAL_STATUS"] == "NO_ARKITSCENES_METRIC_DEPTH_INPUT_CONTRACT_QUALIFIED",
    }
    validation = {
        "status": "PASS_AUDIT_ARTIFACT_AND_DECISION_VALIDATION" if all(checks.values()) else "FAIL_AUDIT_ARTIFACT_AND_DECISION_VALIDATION",
        "checks": checks,
        "unresolved_critical_evidence": [],
        "FINAL_STATUS": decision["FINAL_STATUS"],
        "FINAL_DECISION": decision["FINAL_DECISION"],
        "Only_next_task": decision["Only_next_task"],
    }
    write_json(root / "validation_result.json", validation)
    handoff = {
        "status": "HANDOFF_ARKITSCENES_MAPPING_ROUTE_CLOSED_WITHOUT_TRAINING",
        "recommended_mask": None,
        "reason": decision["recommendation_reason"],
        "immutable_results": {
            "M0": {"geometry_pass": m0["geometry_pass"], "p99_m": m0["p99_m"]},
            "M1": {"geometry_pass": m1["geometry_pass"], "structure_pass": False, "p99_m": m1["p99_m"]},
            "M2": {"geometry_pass": m2["geometry_pass"], "structure_pass": False, "p99_m": m2["p99_m"]},
        },
        "Only_next_task": decision["Only_next_task"],
        "do_not_train_arkitscenes_from_this_handoff": True,
    }
    write_json(root / "downstream_handoff.json", handoff)
    print(validation["status"])
    print(decision["FINAL_STATUS"])
    return 0 if validation["status"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
