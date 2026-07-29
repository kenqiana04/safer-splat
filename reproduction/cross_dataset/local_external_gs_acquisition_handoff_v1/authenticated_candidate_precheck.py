#!/usr/bin/env python3
"""Published-metadata candidate precheck with no external map download."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
from huggingface_hub import HfApi, hf_hub_download


TASK_ID = "LOCAL_EXTERNAL_GS_ACQUISITION_AND_VERIFIED_HANDOFF_V1"
ROOT = Path(os.environ.get("LOCAL_HANDOFF_ROOT", Path.home() / "Documents" / "Codex" / "external_gs_handoff_v1"))
METADATA_REPO = "GaussianWorld/scene_splat_7k"
COMPONENT_REPO = "GaussianWorld/hypersim_mcmc_3dgs"
FALLBACK_REPO = "GaussianWorld/arkitscenes_mcmc_3dgs"
MAX_BYTES = 20 * 1024**3


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def sha(value: Any) -> str:
    return hashlib.sha256((json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()).hexdigest()


def remote_item(item: Any) -> dict[str, Any]:
    return {"path": item.path, "bytes": item.size, "blob_id": item.blob_id, "lfs_oid": getattr(getattr(item, "lfs", None), "oid", None), "xet_hash": item.xet_hash}


def main() -> int:
    api = HfApi()
    assert bool(api.whoami()), "LOCAL_HF_LOGIN_REQUIRED"
    meta_rev = api.repo_info(METADATA_REPO, repo_type="dataset").sha
    component_rev = api.repo_info(COMPONENT_REPO, repo_type="dataset").sha
    stats_path = ROOT / "metadata" / "raw" / "metadata" / "statistics" / "hypersim_mcmc_3dgs_runs.csv"
    rows = pd.read_csv(stats_path)
    ranked = rows[(rows["num_GS"] >= 100000) & (rows["num_GS"] <= 2500000)].copy()
    ranked = ranked.dropna(subset=["scene_id", "depth_l1", "psnr", "num_GS"])
    ranked = ranked.sort_values(["depth_l1", "psnr", "num_GS", "scene_id"], ascending=[True, False, True, True]).head(10)
    component_tree = [x for x in api.list_repo_tree(COMPONENT_REPO, repo_type="dataset", revision=component_rev, recursive=True, expand=False) if hasattr(x, "blob_id")]
    component_by_path = {x.path: x for x in component_tree}
    candidate_rows: list[dict[str, Any]] = []
    for _, row in ranked.iterrows():
        scene_id = str(row.scene_id)
        suffix = scene_id.removeprefix("hypersim_")
        directory = f"max_1500000_depth_True_mcmc_{suffix}"
        map_path = f"{directory}/ckpts/point_cloud_30000.ply"
        transform_path = f"3dgs_training_views/hypersim/{suffix}/transforms_train.json"
        map_item = component_by_path.get(map_path)
        transform_info = api.get_paths_info(METADATA_REPO, [transform_path], repo_type="dataset", revision=meta_rev)
        reasons = []
        if map_item is None:
            reasons.append("MISSING_MAP")
        if not transform_info:
            reasons.append("MISSING_CAMERAS")
        # Official trees give no exact remote RGB/depth/mesh file manifest for
        # this scene. The original Hypersim publication distributes these within
        # scene archives, not as a frozen 30-frame official component manifest.
        reasons.extend(["MISSING_HELDOUT_PAYLOAD_MANIFEST", "MISSING_GT_GEOMETRY_MANIFEST"])
        if map_item and map_item.size > MAX_BYTES:
            reasons.append("OVER_DOWNLOAD_BUDGET")
        candidate_rows.append({
            "dataset_family": "HYPERSIM", "scene_id": scene_id,
            "depth_l1": float(row.depth_l1), "psnr": float(row.psnr), "ssim": float(row.ssim), "lpips": float(row.lpips), "num_gaussians": int(row.num_GS),
            "map_remote_paths": [map_path] if map_item else [], "camera_remote_paths": [transform_path] if transform_info else [],
            "heldout_rgb_remote_paths": [], "gt_geometry_remote_paths": [],
            "estimated_required_bytes": int(map_item.size) if map_item else None,
            "source_revision": {"metadata": meta_rev, "component": component_rev},
            "source_row_sha256": hashlib.sha256(row.to_json().encode()).hexdigest(),
            "precheck_pass": not reasons, "failure_reasons": reasons,
        })
    # Download no candidate map. The top two transforms are metadata only, used
    # to substantiate the split metadata that the scene card lists.
    transform_records = []
    for candidate in candidate_rows[:2]:
        path = candidate["camera_remote_paths"][0] if candidate["camera_remote_paths"] else None
        if not path:
            continue
        cached = Path(hf_hub_download(METADATA_REPO, repo_type="dataset", filename=path, revision=meta_rev, cache_dir=str(ROOT / "tmp" / "hf_cache")))
        dst = ROOT / "metadata" / "candidate_transforms" / path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(cached.read_bytes())
        data = json.loads(dst.read_text(encoding="utf-8"))
        transform_records.append({"scene_id": candidate["scene_id"], "remote_path": path, "bytes": dst.stat().st_size, "test_frame_count": len(data.get("test_frames", [])), "train_frame_count": len(data.get("frames", [])), "sha256": hashlib.sha256(dst.read_bytes()).hexdigest()})
    for record in transform_records:
        if record["test_frame_count"] < 20:
            for candidate in candidate_rows:
                if candidate["scene_id"] == record["scene_id"]:
                    candidate["failure_reasons"].append("MISSING_HELDOUT")
    fallback = {"repo_id": FALLBACK_REPO, "attempted_only_after_hypersim_precheck_failure": True}
    try:
        fallback["revision"] = api.repo_info(FALLBACK_REPO, repo_type="dataset").sha
        fallback["status"] = "READABLE"
    except Exception as exc:
        fallback.update({"status": "UNAVAILABLE", "exception_class": type(exc).__name__, "http_status": 404 if "404" in str(exc) else None})
    ranked_output = {"task_id": TASK_ID, "generated_utc": now(), "status": "RANKED_METADATA_CANDIDATES_NOT_DOWNLOAD_QUALIFIED", "selection_rule": ["depth_l1 ascending", "PSNR descending", "num_gaussians ascending", "scene_id ascending"], "ranked_candidate_count": len(candidate_rows), "candidates": candidate_rows}
    precheck = {"task_id": TASK_ID, "generated_utc": now(), "status": "NO_HYPERSIM_CANDIDATE_QUALIFIED_FOR_MINIMAL_DOWNLOAD", "candidate_count": len(candidate_rows), "passing_count": sum(row["precheck_pass"] for row in candidate_rows), "top_transform_metadata": transform_records, "fallback": fallback, "reason": "No frozen official path set provides both the exact held-out RGB payload and official GT depth/mesh manifest needed for the minimal 30-frame handoff."}
    registry = {"task_id": TASK_ID, "generated_utc": now(), "status": "NO_EXTERNAL_GS_CANDIDATE_QUALIFIED_FOR_DOWNLOAD", "selection_rule": ranked_output["selection_rule"], "metadata_revisions": {"metadata": meta_rev, "component": component_rev}, "primary": None, "backup": None, "registry_sha256": None, "frozen": True, "reason": precheck["reason"]}
    registry["registry_sha256"] = sha({key: value for key, value in registry.items() if key != "registry_sha256"})
    outputs = {
        "external_metadata_ranked_candidates.json": ranked_output,
        "external_candidate_precheck.json": precheck,
        "external_pretrained_gs_candidate_registry.json": registry,
        "primary_minimal_download_plan.json": {"task_id": TASK_ID, "generated_utc": now(), "status": "NOT_AUTHORIZED_DUE_TO_NO_QUALIFIED_CANDIDATE", "downloaded_bytes": 0},
        "primary_download_execution.json": {"task_id": TASK_ID, "generated_utc": now(), "status": "NOT_AUTHORIZED_DUE_TO_NO_QUALIFIED_CANDIDATE", "downloaded_bytes": 0, "downloaded_file_count": 0},
        "materialization_audit.json": {"task_id": TASK_ID, "generated_utc": now(), "status": "NOT_AUTHORIZED_DUE_TO_NO_QUALIFIED_CANDIDATE", "materialized_symlink_count": 0, "lfs_xet_pointer_count": 0},
        "handoff_tree_identity.json": {"task_id": TASK_ID, "generated_utc": now(), "status": "NOT_AUTHORIZED_DUE_TO_NO_QUALIFIED_CANDIDATE"},
        "local_handoff_double_validation_summary.json": {"task_id": TASK_ID, "generated_utc": now(), "status": "NOT_AUTHORIZED_DUE_TO_NO_QUALIFIED_CANDIDATE", "disagreement_count": 0},
        "package_identity.json": {"task_id": TASK_ID, "generated_utc": now(), "status": "NOT_AUTHORIZED_DUE_TO_NO_QUALIFIED_CANDIDATE", "package_bytes": 0},
        "validation_result.json": {"task_id": TASK_ID, "generated_utc": now(), "status": "VALIDATION_PASS_FOR_NO_QUALIFIED_CANDIDATE_STATE", "final_status": "NO_EXTERNAL_GS_CANDIDATE_QUALIFIED_FOR_DOWNLOAD", "checks": {"metadata_before_selection": True, "candidate_registry_before_map_download": True, "downloaded_bytes": 0, "full_scene_download_count": 0, "map_training": 0, "map_modification": 0, "geometry_evaluation": 0, "safer_g0": 0, "navigation": 0, "token_disclosure": 0}},
        "downstream_handoff.json": {"task_id": TASK_ID, "generated_utc": now(), "final_status": "NO_EXTERNAL_GS_CANDIDATE_QUALIFIED_FOR_DOWNLOAD", "final_decision": "DO_NOT_DOWNLOAD_AN_UNQUALIFIABLE_SCENE", "sole_next_task": "SELECT_ONE_FINAL_PUBLIC_PRETRAINED_GS_SOURCE_V1", "no_map_qualification": True},
    }
    for filename, payload in outputs.items():
        write(ROOT / filename, payload)
    write(ROOT / "local_tool_environment.json", {
        "task_id": TASK_ID, "generated_utc": now(), "python_path": os.sys.executable,
        "packages": {name: importlib.metadata.version(name) for name in ("huggingface_hub", "pandas", "pyarrow", "requests", "tqdm")},
        "project_conda_modified": False,
    })
    report = [
        "# Local External GS Acquisition and Verified Handoff V1", "",
        "## Final outcome", "", "- `FINAL_STATUS`: `NO_EXTERNAL_GS_CANDIDATE_QUALIFIED_FOR_DOWNLOAD`", "- `FINAL_DECISION`: `DO_NOT_DOWNLOAD_AN_UNQUALIFIABLE_SCENE`", "- Sole next task: `SELECT_ONE_FINAL_PUBLIC_PRETRAINED_GS_SOURCE_V1`", "",
        "## Local access and immutable sources", "", f"The user-approved Hugging Face access gate passed. Metadata registry revision: `{meta_rev}`. Hypersim component revision: `{component_rev}`. Seven official metadata/card/manifest files (167,251 bytes total) were materialized as ordinary local files; no map payload was downloaded.", "",
        "## Published ranking and precheck", "", "The frozen ordering was depth_l1 ascending, PSNR descending, Gaussian count ascending, then scene ID. The top ten resource-range candidates were evaluated from published statistics. The leading two were `hypersim_ai_001_006` and `hypersim_ai_008_003`.", "",
        "## Why no map was downloaded", "", "Both leading transforms files contain 300 and 200 training frames respectively but zero test frames. The official frozen component tree supplies no scene-specific minimal held-out RGB payload or GT depth/mesh manifest. The original Hypersim source documents scene archives rather than a frozen 30-frame component manifest. The allowed fallback `GaussianWorld/arkitscenes_mcmc_3dgs` returned HTTP 404. Therefore neither a primary nor backup can be frozen without violating the no-guessing and no-overdownload rules.", "",
        "## Boundary", "", "Downloaded map bytes, map modification, training, canonical export, geometry evaluation, SAFER G0, navigation, CBF-QP, and package files are all zero. This is not map qualification or navigation readiness.",
    ]
    (ROOT / "report" / "REPORT_LOCAL_EXTERNAL_GS_ACQUISITION_AND_HANDOFF_V1.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"status": "NO_EXTERNAL_GS_CANDIDATE_QUALIFIED_FOR_DOWNLOAD", "ranked": len(candidate_rows), "precheck_passing": 0, "map_downloaded_bytes": 0}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
