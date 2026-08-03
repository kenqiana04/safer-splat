#!/usr/bin/env python3
"""Fail-closed evidence freeze for the frozen ARKitScenes M1 qualification."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


ROOT = Path("/disk1/zlab/maintenance_records/arkitscenes_splatam_m1_learned_map_qualification_v1")
FORMAL_OUTPUT = ROOT / "outputs/ARKITSCENES_SPLATAM_M1_EMPTY_DEPTH_SAFE_GT_POSE_MAP_ONLY_V1"
PUBLISH_ROOT = Path("/disk1/zlab/cross_dataset_assets/qualified_arkitscenes_splatam_m1_learned_map_v1/48018874")
COMPACT = ROOT / "compact_tracking_artifacts"

FINAL_STATUS = "NO_ARKITSCENES_M1_LEARNED_GAUSSIAN_MAP_QUALIFIED_UNDER_FROZEN_CONTRACT"
FINAL_DECISION = "CLOSE_ARKITSCENES_MAPPING_ROUTE_AFTER_FINAL_M1_ATTEMPT"
ONLY_NEXT_TASK = "ETH3D_DELIVERY_AREA_LEARNED_3DGS_QUALIFICATION_V1"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy(relative_source: str, relative_destination: str | None = None) -> None:
    source = ROOT / relative_source
    if not source.is_file():
        raise FileNotFoundError(source)
    destination = COMPACT / (relative_destination or relative_source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def main() -> None:
    identity = read_json(ROOT / "input_identity_freeze.json")
    runtime = read_json(ROOT / "runtime_integration/runtime_identity.json")
    config = read_json(ROOT / "config/resolved_config_diff.json")
    registry = read_json(ROOT / "evaluation_freeze/registry_freeze.json")
    smoke_a = read_json(ROOT / "smoke/smoke_a_validation.json")
    smoke_b = read_json(ROOT / "smoke/smoke_b_validation.json")
    lock = read_json(ROOT / "execution_lock.json")
    formal = read_json(ROOT / "formal/formal_validation.json")
    export = read_json(ROOT / "evaluation/export_determinism.json")
    heldout = read_json(ROOT / "evaluation/heldout_evaluation.json")

    assert identity["status"] == "PASS_ARKITSCENES_M1_MAPPING_INPUT_IDENTITY"
    assert runtime["status"] == "PASS_TASK_OWNED_RUNTIME_INTEGRATION"
    assert config["status"] == "PASS_AUTHORIZED_SPLATAM_M1_CONFIG_DIFF_ONLY"
    assert registry["status"] == "PASS_PREMAPPING_EVALUATION_REGISTRY_FREEZE"
    assert smoke_a["pass"] and smoke_b["pass"]
    assert lock["status"] == "PASS_ARKITSCENES_M1_FORMAL_EXECUTION_LOCK"
    assert formal["pass"] and formal["zero_indices"] == [76, 79]
    assert export["status"] == "PASS_TWO_FRESH_CANONICAL_EXPORTS_IDENTICAL"
    assert heldout["status"] == FINAL_STATUS and not heldout["pass"]
    assert heldout["gates"]["primary_coverage"] is False
    assert all(value for key, value in heldout["gates"].items() if key != "primary_coverage")
    assert heldout["heldout_mapper_access_count"] == 0
    assert not PUBLISH_ROOT.exists(), "failed map must not be published"
    assert not (ROOT / "clearance").exists(), "clearance must not run after depth gate failure"
    assert not (ROOT / "g0").exists(), "G0 must not run after depth gate failure"

    attempt_path = ROOT / "formal_attempt_record.json"
    attempt = read_json(attempt_path)
    launched = datetime.fromisoformat(attempt["launched_utc"])
    params_path = FORMAL_OUTPUT / "params.npz"
    completed = datetime.fromtimestamp(params_path.stat().st_mtime, tz=timezone.utc)
    attempt.update(
        {
            "completed": True,
            "completed_utc": completed.isoformat(),
            "runtime_to_final_params_seconds": round((completed - launched).total_seconds(), 3),
            "formal_validation_status": formal["status"],
            "final_params_sha256": formal["params_sha256"],
            "final_params_size": formal["params_size"],
            "gaussian_count": formal["gaussian_count"],
            "process_attempts": 1,
            "completed_outputs": 1,
            "retry_count": 0,
        }
    )
    write_json(attempt_path, attempt)

    gpu_processes = subprocess.run(
        [
            "nvidia-smi",
            "-i",
            "1",
            "--query-compute-apps=pid,process_name,used_gpu_memory",
            "--format=csv,noheader",
        ],
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if gpu_processes:
        raise RuntimeError(f"GPU 1 not clean at finalization: {gpu_processes}")

    counters = {
        "download": 0,
        "environment_create": 0,
        "environment_modify": 0,
        "runtime_patch": 1,
        "smoke_process_attempts": 2,
        "smoke_completed": 2,
        "formal_process_attempts": 1,
        "formal_completed": 1,
        "formal_retry": 0,
        "final_params": 1,
        "fresh_canonical_exports": 2,
        "heldout_nvs_evaluations_completed": 1,
        "heldout_depth_evaluations_completed": 1,
        "clearance": 0,
        "g0_fresh_processes": 0,
        "controller": 0,
        "m2_or_variant": 0,
        "hyperparameter_sweep": 0,
        "frame_deletion": 0,
        "icp_sim3_scale_repair": 0,
        "optimizer_steps": 21000,
        "checkpoint": 0,
    }

    validation = {
        "final_status": FINAL_STATUS,
        "final_decision": FINAL_DECISION,
        "only_next_task": ONLY_NEXT_TASK,
        "pass": False,
        "failed_gate": "primary_confidence_ge1_depth_coverage",
        "threshold": 0.95,
        "observed": heldout["primary_confidence_ge1"]["coverage"],
        "other_primary_depth_gates_pass": True,
        "clearance_skipped_by_protocol": True,
        "g0_skipped_by_protocol": True,
        "map_published": False,
        "selected_map": None,
        "gpu_1_final_clean": True,
    }
    selection = {
        "status": "NO_MAP_SELECTED",
        "scene": "48018874",
        "selected_map": None,
        "publish_root_created": False,
        "reason": "Frozen primary HELDOUT depth coverage was below 0.95.",
        "forbidden_post_hoc_actions_performed": False,
    }
    handoff = {
        "status": FINAL_STATUS,
        "decision": FINAL_DECISION,
        "only_next_task": ONLY_NEXT_TASK,
        "arkitscenes_mapping_route_closed": True,
        "m2_or_additional_arkitscenes_mapping_authorized": False,
        "map_identity": None,
    }
    manifest = {
        "task": "RESUME_ARKITSCENES_SPLATAM_M1_SMOKE_AND_LEARNED_MAP_QUALIFICATION_V1",
        "scene": "48018874",
        "branch": "arkitscenes-splatam-m1-learned-map-qualification-v1",
        "base_branch": "arkitscenes-confidence-ge1-supervision-zero-depth-contract-v2",
        "base_head": "3fe598dc497cc36b6848d2b9bf19c13955874199",
        "formal_task": lock["task"],
        "seed": 20260730,
        "physical_gpu": 1,
        "input_status": identity["status"],
        "runtime_status": runtime["status"],
        "registry_status": registry["status"],
        "smoke_a_status": smoke_a["status"],
        "smoke_b_status": smoke_b["status"],
        "execution_lock_sha256": sha256(ROOT / "execution_lock.json"),
        "formal_status": formal["status"],
        "canonical_export_status": export["status"],
        "heldout_status": heldout["status"],
        "clearance_status": "NOT_RUN_PREREQUISITE_FAILED",
        "g0_status": "NOT_RUN_PREREQUISITE_FAILED",
        "final_status": FINAL_STATUS,
        "final_decision": FINAL_DECISION,
        "counters": counters,
        "gpu_1_final_clean": True,
        "official_source_modified": False,
        "environment_modified": False,
        "watchdog_or_managed_ssh_modified": False,
    }

    write_json(ROOT / "validation_result.json", validation)
    write_json(ROOT / "selection.json", selection)
    write_json(ROOT / "downstream_handoff.json", handoff)
    write_json(ROOT / "run_manifest.json", manifest)

    report = f"""# REPORT: ARKitScenes SplaTAM M1 learned-map qualification V1

## Result

- `FINAL_STATUS={FINAL_STATUS}`
- `FINAL_DECISION={FINAL_DECISION}`
- `Only next task={ONLY_NEXT_TASK}`
- No ARKitScenes map was selected or published. The route was closed after the one frozen M1 formal attempt.

## Git and scope

- Branch: `arkitscenes-splatam-m1-learned-map-qualification-v1`
- Base branch/head: `arkitscenes-confidence-ge1-supervision-zero-depth-contract-v2` / `3fe598dc497cc36b6848d2b9bf19c13955874199`
- Scene: `48018874`; TRAIN/HELDOUT: `214/53`; seed: `20260730`; physical GPU: `1`
- Mapper role: `{lock['mapper_role']}`
- HELDOUT mapper access count: `0`

## Frozen identities

- ARKitScenes authority: `7283761bf26c27570ec59a5dc0f8686fbff07726`
- SplaTAM authority: `{runtime['official_head']}`
- Diff Gaussian rasterizer authority: `cb65e4b86bc3bd8ed42174b72a62e8d3a3a71110`
- TRAIN SHA-256: `{identity['train_sha256']}`
- HELDOUT SHA-256: `{identity['heldout_sha256']}`
- TRAIN/HELDOUT Git blob OID: `a2ddc70775e6d0f9c25f77ef5f869556d83b292c` / `cf28dd385711a31733360e5fc21dce229ce605bc`
- Split/group tuple SHA-256: `{identity['split_identity_sha256']}` / `{identity['group_tuple_sha256']}`
- M1 compatibility SHA-256 / Git blob OID: `{identity['compat_sha256']}` / `b134d45f68f8de060f94f8867dfb173c98be8f0b`
- M1 valid pixels: `{identity['m1_valid_pixels']}`; zero-valid TRAIN indices: `{identity['zero_valid_train_indices']}`
- Runtime patch SHA-256: `{runtime['patch_sha256']}`; formal config SHA-256: `{config['variants']['formal']['sha256']}`
- Environment: `/disk1/zlab/conda_envs/arkitscenes_splatam_canonical_v1`; Python `3.10.20`; PyTorch `2.1.2+cu118`; CUDA runtime `11.8`; NumPy `1.26.4`; NVIDIA driver `525.147.05`.
- Runtime overlay: `/disk1/zlab/maintenance_records/arkitscenes_splatam_canonical_learned_map_qualification_v1/environment/runtime_overlay_setuptools_81_0_0`.
- Evaluator registry SHA-256: `{lock['artifact_sha256']['evaluation_registry']}`
- Clearance/G0 registry SHA-256: `{registry['clearance_registry_sha256']}` / `{registry['g0_registry_sha256']}`
- Execution-lock SHA-256: `{sha256(ROOT / 'execution_lock.json')}`

## Qualification stages

- Input, task-owned runtime, frozen config and evaluator registries: PASS.
- PR #73 compatibility revalidation: synthetic nonempty equivalence PASS, synthetic zero-mask PASS, real nonempty forward equivalence PASS, real zero-frame PASS, sequence-state dry run PASS, first-frame M1 nonempty PASS.
- Smoke A rows 0-11: `{smoke_a['status']}`, {smoke_a['gaussian_count']:,} Gaussians, 7,000 finite optimizer steps.
- Smoke B rows 70-82: `{smoke_b['status']}`, {smoke_b['gaussian_count']:,} Gaussians, 7,000 finite optimizer steps.
- Smoke B rows 76/79: exact empty-safe events, exact zero depth loss and zero Gaussian additions; rows 80-82 returned to the nonempty path.
- Formal attempt: one process, one completed output, no retry, 214/214 frame events, 7,000 finite optimizer steps, rows 76/79 exact empty-safe, no checkpoint.
- Formal runtime to final params: `{attempt['runtime_to_final_params_seconds']:.3f}` seconds; monitored process RAM peak sample: `8.3%` of 67,294,916,608 bytes (about 5.20 GiB); monitored GPU-memory peak sample: about `5.4 GiB`.
- Formal map: `{formal['gaussian_count']:,}` Gaussians; params SHA-256 `{formal['params_sha256']}`; size `{formal['params_size']}` bytes.
- Two fresh canonical exports: `{export['status']}`; tree SHA-256 `{export['tree_sha256']}`; no filtering, recentering, scale repair, ICP or Sim3.

## Frozen HELDOUT result

- All 53 frames rendered at 256x192; all NVS metrics finite; map parameter identity unchanged.
- NVS mean: PSNR `{heldout['nvs_all_53']['psnr']:.6f}`, SSIM `{heldout['nvs_all_53']['ssim']:.6f}`, LPIPS `{heldout['nvs_all_53']['lpips']:.6f}`.
- Primary confidence>=1: coverage `{heldout['primary_confidence_ge1']['coverage']:.9f}` (gate `>=0.95`, FAIL), AbsRel `{heldout['primary_confidence_ge1']['absrel']:.9f}` (PASS), delta1 `{heldout['primary_confidence_ge1']['delta1']:.9f}` (PASS), median ratio `{heldout['primary_confidence_ge1']['median_pred_gt_ratio']:.9f}` (PASS), nonfinite `{heldout['primary_confidence_ge1']['nonfinite_count']}` (PASS).
- Secondary confidence==2, report-only: coverage `{heldout['secondary_confidence_eq2_report_only']['coverage']:.9f}`, AbsRel `{heldout['secondary_confidence_eq2_report_only']['absrel']:.9f}`, delta1 `{heldout['secondary_confidence_eq2_report_only']['delta1']:.9f}`, median ratio `{heldout['secondary_confidence_eq2_report_only']['median_pred_gt_ratio']:.9f}`, nonfinite `{heldout['secondary_confidence_eq2_report_only']['nonfinite_count']}`.
- Failure attribution: coverage limitation, not a 10x/100x/1000x coordinate-scale failure. The frozen map is geometrically accurate where supported but does not cover enough of the M1 HELDOUT target pixels.
- Clearance, `epsilon_map_empirical`, and SAFER static G0: not run because Primary depth geometry is a prerequisite. No value is claimed.

## Counts and boundaries

```json
{json.dumps(counters, indent=2, sort_keys=True)}
```

- GPU 1 was clean at finalization.
- The official SplaTAM checkout and original Conda environment were not modified.
- The persistent reverse-proxy watchdog and managed SSH tunnel were not modified or stopped.
- No result was rerun or selected post hoc; no M2, variant, sweep, deletion, ICP/Sim3/scale repair, opacity filter, controller benchmark, or checkpoint was created.
- The first HELDOUT launcher invocation stopped before reading HELDOUT because it referenced the wrong frozen manifest filename; its task-owned export directories were safely rebuilt and the same evaluator then completed. This was a non-semantic path wrapper repair, not a scientific retry.

## Artifacts

- Server task root: `{ROOT}`
- Formal params remain only on authoritative storage: `{params_path}`
- Map identity: none (failed maps are not published).
- Downstream handoff: `downstream_handoff.json`; selection: `selection.json`; manifest: `run_manifest.json`; validator: `validation_result.json`.
"""
    report_path = ROOT / "REPORT_RESUME_ARKITSCENES_SPLATAM_M1_SMOKE_AND_LEARNED_MAP_QUALIFICATION_V1.md"
    report_path.write_text(report, encoding="utf-8", newline="\n")

    if COMPACT.exists():
        shutil.rmtree(COMPACT)
    COMPACT.mkdir(parents=True)
    for source, destination in [
        ("input_identity_freeze.json", None),
        ("runtime_integration/runtime_identity.json", None),
        ("runtime_integration/applied.patch", None),
        ("config/arkitscenes_m1_dataset.json", None),
        ("config/resolved_config_diff.json", None),
        ("config/smoke_a.py", None),
        ("config/smoke_b.py", None),
        ("config/formal.py", None),
        ("evaluation_freeze/registry_freeze.json", None),
        ("pr73_revalidation/synthetic/nonempty_synthetic_equivalence.json", None),
        ("pr73_revalidation/synthetic/zero_mask_synthetic_validation.json", None),
        ("pr73_revalidation/real/nonempty_real_frame_equivalence.json", None),
        ("pr73_revalidation/real/zero_frame_real_validation.json", None),
        ("pr73_revalidation/real/sequence_state_dry_run.json", None),
        ("pr73_revalidation/real/first_frame_m1_validation.json", None),
        ("smoke/smoke_a_validation.json", None),
        ("smoke/smoke_b_validation.json", None),
        ("execution_lock.json", None),
        ("execution_lock.sha256", None),
        ("formal_attempt_record.json", None),
        ("formal/formal_validation.json", None),
        ("canonical_export_a/canonical_export_metadata.json", "canonical_export/canonical_export_metadata.json"),
        ("evaluation/export_determinism.json", None),
        ("evaluation/heldout_evaluation.json", None),
        ("selection.json", None),
        ("run_manifest.json", None),
        ("validation_result.json", None),
        ("downstream_handoff.json", None),
        (report_path.name, report_path.name),
    ]:
        copy(source, destination)

    index = {
        "status": FINAL_STATUS,
        "files": {
            path.relative_to(COMPACT).as_posix(): {"sha256": sha256(path), "size": path.stat().st_size}
            for path in sorted(COMPACT.rglob("*"))
            if path.is_file()
        },
    }
    write_json(COMPACT / "server_evidence_index.json", index)
    print(FINAL_STATUS)
    print(f"REPORT={report_path}")
    print(f"COMPACT={COMPACT}")


if __name__ == "__main__":
    main()
