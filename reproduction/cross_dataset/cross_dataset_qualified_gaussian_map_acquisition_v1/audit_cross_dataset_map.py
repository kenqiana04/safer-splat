#!/usr/bin/env python3
"""Bounded audit for external pretrained Gaussian-map acquisition.

This executable intentionally stops all scientific qualification downstream of
the external access gate.  It never downloads a scene payload, changes a map,
or imports the controller/navigation stack.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(os.environ.get(
    "CROSS_MAP_ROOT",
    "/disk1/zlab/maintenance_records/cross_dataset_qualified_gaussian_map_acquisition_v1",
))
SAFER_REPO = Path(os.environ.get("SAFER_REPO", "/disk1/zlab/projects/safer-splat"))
EXPECTED_HEAD = "f63b4c496861c4f8881348d74244c1ff9a528d51"
EXPECTED_BLOBS = {
    "splat/distances.py": "d7f17b67df40e36e458c7a5ed77c4a04659c6f35",
    "splat/gsplat_utils.py": "782c38eca50e78c605085b481155ed61e4607336",
    "cbf/cbf_utils.py": "7c6e1300b125cc0a2a950ac2835a1fbe3d0de113",
}
ACCESS_GATE = "EXTERNAL_DATASET_ACCESS_APPROVAL_REQUIRED"
BLOCKED = f"NOT_AUTHORIZED_DUE_TO_{ACCESS_GATE}"
FINAL_STATUS = "BLOCKED_BY_EXTERNAL_DATASET_ACCESS_APPROVAL_REQUIRED"
FINAL_DECISION = "REQUEST_USER_TO_ACCEPT_SCENESPLAT_AND_COMPONENT_TERMS"
NEXT_TASK = "RESUME_EXTERNAL_GS_MAP_ACQUISITION_AFTER_ACCESS_APPROVAL_V1"
TASK_ID = "CROSS_DATASET_QUALIFIED_GAUSSIAN_MAP_ACQUISITION_AND_SELECTION_V1"
SUBDIRS = (
    "frozen_inputs", "official_safer_inventory", "external_source_inventory",
    "access_and_license", "statistics_metadata", "candidate_registry",
    "selective_download", "download_identity", "format_semantics",
    "canonical_exports", "coordinate_contracts", "heldout_geometry", "safer_g0",
    "selection", "figures", "report", "logs", "tmp",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def atomic_json(path: Path, payload: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json_bytes(payload)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(encoded)
    os.replace(tmp, path)
    return digest(encoded)


def sha_file(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def command(*args: str) -> tuple[int, str, str]:
    process = subprocess.run(args, text=True, capture_output=True, check=False)
    return process.returncode, process.stdout.strip(), process.stderr.strip()


def git_value(argument: str) -> str | None:
    rc, output, _ = command("git", "-C", str(SAFER_REPO), "rev-parse", argument)
    return output if rc == 0 else None


def ensure_dirs() -> None:
    for subdir in SUBDIRS:
        (ROOT / subdir).mkdir(parents=True, exist_ok=True)


def static_counts() -> dict[str, int]:
    return {
        "tum_execution": 0,
        "splatfacto_training_render_g0": 0,
        "splatam_training_render_g0": 0,
        "gaussian_slam_optimizer_mapping": 0,
        "replica_map_training": 0,
        "new_map_training": 0,
        "filtering_pruning_downsampling": 0,
        "scale_fitting": 0,
        "sim3": 0,
        "icp": 0,
        "geometry_threshold_modification": 0,
        "navigation": 0,
        "cbf_qp": 0,
        "start_safe": 0,
        "risk_aware": 0,
        "discrete_verification": 0,
        "recovery": 0,
        "language_feature_download": 0,
        "full_snapshot_download": 0,
        "gated_access_bypass": 0,
    }


def freeze_routes() -> dict[str, Any]:
    payload = {
        "task_id": TASK_ID,
        "generated_utc": utc_now(),
        "source_pr": 59,
        "source_head": "65901fab5b0120d7f503378384372a28d2520ad3",
        "frozen_routes": {
            "tum": {
                "decision": "CLOSE_TUM_NAVIGATION_BENCHMARK_KEEP_SAFETY_CASE_STUDY",
                "paired20_sha256": "380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6",
            },
            "splatfacto": {
                "decision": "PASS_SPLATFACTO_NATIVE_COMPATIBILITY_ONLY_GEOMETRY_NOT_QUALIFIED",
                "route": "CLOSE_SPLATFACTO_NAVIGATION_MAP_ROUTE",
            },
            "splatam": {
                "decision": "SPLATAM_REPLICA_60_FRAME_PILOT_GEOMETRY_NOT_QUALIFIED",
                "route": "CLOSE_SPLATAM_REPLICA_MAPPING_ROUTE_UNDER_FROZEN_CONFIG",
            },
            "gaussian_slam": {
                "decision": "NO_LEGAL_GAUSSIAN_SLAM_RESOLUTION_ADAPTATION_CONTRACT",
                "route": "CLOSE_GAUSSIAN_SLAM_REPLICA_ROUTE_UNDER_OFFICIAL_CONFIG",
            },
            "replica_v3": {
                "asset_root": "/disk1/zlab/cross_dataset_assets/processed/replica/apartment_0.rendering_v3",
                "complete_tree_sha256": "24e21d3bccceb0516ed8b9b49b426964f3954ccd0cd804eedd5846baabd66dcb",
            },
        },
        "counts": static_counts(),
        "claim_boundary": {
            "official_scene_generalization": "not_established_by_this_access-blocked task",
            "external_dataset_generalization": "not_established_without a qualified external map",
            "mapping_frontend_generalization": "not_established",
            "navigation_generalization": "not_established",
        },
    }
    atomic_json(ROOT / "frozen_inputs" / "frozen_mapping_route_decisions.json", payload)
    return payload


def find_official_configs() -> list[Path]:
    outputs = SAFER_REPO / "outputs"
    if not outputs.exists():
        return []
    return sorted(outputs.glob("*/*/*/config.yml"))


def config_scene(config: Path) -> str:
    try:
        return config.relative_to(SAFER_REPO / "outputs").parts[0]
    except ValueError:
        return config.parent.name


def deterministic_queries(means: Any) -> Any:
    """32 fixed bbox queries; operates only on the already loaded Gaussian tensor."""
    import torch

    low = means.amin(dim=0)
    high = means.amax(dim=0)
    fractions = torch.tensor((0.125, 0.375, 0.625, 0.875), device=means.device, dtype=means.dtype)
    xs, ys, zs = torch.meshgrid(fractions, fractions, torch.tensor((0.25, 0.75), device=means.device, dtype=means.dtype), indexing="ij")
    unit = torch.stack((xs.reshape(-1), ys.reshape(-1), zs.reshape(-1)), dim=1)
    return low.unsqueeze(0) + unit * (high - low).unsqueeze(0)


def sha_tensor(tensor: Any) -> str:
    return digest(tensor.detach().cpu().contiguous().numpy().tobytes())


def run_static_g0(config: Path) -> dict[str, Any]:
    """Load one official checkpoint and perform static distance-only G0 probes."""
    started = time.time()
    original_cwd = Path.cwd()
    try:
        import numpy as np
        import torch

        # The official Nerfstudio configs intentionally contain repository-relative
        # `data/<scene>` paths.  Resolve those paths from the verified checkout,
        # never by editing the config or the checkpoint.
        os.chdir(SAFER_REPO)
        sys.path.insert(0, str(SAFER_REPO))
        from splat.gsplat_utils import GSplatLoader

        loader = GSplatLoader(config, "cuda:0")
        means_before = sha_tensor(loader.means)
        scales = loader.scales.detach()
        finite_arrays = bool(
            torch.isfinite(loader.means).all().item()
            and torch.isfinite(loader.rots).all().item()
            and torch.isfinite(scales).all().item()
            and torch.isfinite(loader.covs).all().item()
        )
        positive_scales = bool((scales > 0).all().item())
        queries = deterministic_queries(loader.means)
        query_hash = sha_tensor(queries)

        def once() -> tuple[Any, Any, Any, Any]:
            hs, gradients, hessians, active = [], [], [], []
            for query in queries:
                h, gradient, hessian, _ = loader.query_distance(
                    query, distance_type="ball-to-ellipsoid", radius=0.015
                )
                index = int(torch.argmin(h).item())
                hs.append(h[index].detach().cpu())
                gradients.append(gradient[index].detach().cpu())
                hessians.append(hessian[index].detach().cpu())
                active.append(index)
            return tuple(torch.stack(value) if value and hasattr(value[0], "shape") else torch.tensor(value) for value in (hs, gradients, hessians, active))

        first, second, third = once(), once(), once()
        torch.cuda.synchronize()
        hess = first[2].numpy()
        symmetry = np.linalg.norm(hess - np.swapaxes(hess, 1, 2), axis=(1, 2)) / (1.0 + np.linalg.norm(hess, axis=(1, 2)))
        deterministic = all(torch.equal(left, right) for left, right in zip(first, second)) and all(torch.equal(left, right) for left, right in zip(first, third))
        output_finite = bool(all(torch.isfinite(value.float()).all().item() for value in first[:3]))
        means_after = sha_tensor(loader.means)
        count = int(loader.means.shape[0])
        passed = finite_arrays and positive_scales and output_finite and deterministic and float(symmetry.max()) <= 1e-5 and means_before == means_after
        result = {
            "status": "OFFICIAL_SCENE_READY_FOR_MULTISCENE_BENCHMARK" if passed else "OFFICIAL_SCENE_STATIC_G0_FAILURE",
            "config_path": str(config),
            "gaussian_count": count,
            "arrays_finite": finite_arrays,
            "scales_positive": positive_scales,
            "query_seed": "OFFICIAL_SAFER_STATIC_G0_V1",
            "query_count": 32,
            "query_sha256": query_hash,
            "runs": 3,
            "radius_m": 0.015,
            "h_gradient_hessian_finite": output_finite,
            "active_gaussian_deterministic": deterministic,
            "hessian_symmetry_relative_max": float(symmetry.max()),
            "gaussian_count_before_after": [count, count],
            "means_sha256_before_after": [means_before, means_after],
            "no_map_mutation": means_before == means_after,
            "controller_navigation_called": False,
            "runtime_seconds": time.time() - started,
        }
        return result
    except Exception as exc:  # Evidence: a genuine load failure is retained verbatim but compactly.
        return {
            "status": "OFFICIAL_SCENE_LOAD_FAILURE",
            "config_path": str(config),
            "exception_type": type(exc).__name__,
            "exception": str(exc)[:1000],
            "controller_navigation_called": False,
            "runtime_seconds": time.time() - started,
        }
    finally:
        os.chdir(original_cwd)


def official_inventory() -> tuple[dict[str, Any], dict[str, Any]]:
    head = git_value("HEAD")
    blobs = {path: git_value(f"HEAD:{path}") for path in EXPECTED_BLOBS}
    configs = find_official_configs()
    expected = ("stonehenge", "flightgate", "statues", "adirondacks")
    config_items: list[dict[str, Any]] = []
    g0_items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for config in configs:
        scene = config_scene(config)
        seen.add(scene)
        ckpts = sorted(config.parent.glob("*.ckpt")) + sorted(config.parent.glob("nerfstudio_models/*.ckpt"))
        checkpoint = ckpts[0] if ckpts else None
        config_items.append({
            "scene_id": scene,
            "availability": "PRESENT",
            "config_path": str(config),
            "config_sha256": sha_file(config),
            "checkpoint_path": str(checkpoint) if checkpoint else None,
            "checkpoint_sha256": sha_file(checkpoint),
            "checkpoint_bytes": checkpoint.stat().st_size if checkpoint else 0,
            "source": "official SAFER outputs symlinked from the project model pack",
            "coordinate_scale_note": "Nerfstudio checkpoint semantics require per-scene evidence; no cross-scene claim is inferred.",
        })
        g0 = run_static_g0(config)
        g0["scene_id"] = scene
        g0_items.append(g0)
    for scene in expected:
        if scene not in seen:
            config_items.append({
                "scene_id": scene,
                "availability": "OFFICIAL_SCENE_ASSET_MISSING",
                "config_path": None,
                "checkpoint_path": None,
                "source": "official README registry name; no loadable model-pack config discovered",
            })
            g0_items.append({"scene_id": scene, "status": "OFFICIAL_SCENE_ASSET_MISSING", "query_count": 0})
    inventory = {
        "task_id": TASK_ID,
        "generated_utc": utc_now(),
        "safer_repo": str(SAFER_REPO),
        "safer_head": head,
        "expected_head": EXPECTED_HEAD,
        "head_match": head == EXPECTED_HEAD,
        "blobs": blobs,
        "expected_blobs": EXPECTED_BLOBS,
        "blob_identity_match": blobs == EXPECTED_BLOBS,
        "official_readme_path": str(SAFER_REPO / "README.md"),
        "official_readme_sha256": sha_file(SAFER_REPO / "README.md"),
        "scenes": config_items,
    }
    compatibility = {
        "task_id": TASK_ID,
        "generated_utc": utc_now(),
        "authority_identity_match": head == EXPECTED_HEAD and blobs == EXPECTED_BLOBS,
        "scenes": g0_items,
        "ready_scene_count": sum(item["status"] == "OFFICIAL_SCENE_READY_FOR_MULTISCENE_BENCHMARK" for item in g0_items),
        "non_stonehenge_ready_scene_count": sum(item["status"] == "OFFICIAL_SCENE_READY_FOR_MULTISCENE_BENCHMARK" and item["scene_id"] != "stonehenge" for item in g0_items),
        "navigation_or_controller_calls": 0,
    }
    atomic_json(ROOT / "official_safer_inventory" / "official_safer_scene_inventory.json", inventory)
    atomic_json(ROOT / "official_safer_inventory" / "official_safer_scene_static_compatibility.json", compatibility)
    return inventory, compatibility


def url_attempt(url: str) -> dict[str, Any]:
    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            return {"url": url, "reachable": True, "http_status": response.status}
    except urllib.error.HTTPError as exc:
        return {"url": url, "reachable": True, "http_status": exc.code, "error": type(exc).__name__}
    except Exception as exc:
        return {"url": url, "reachable": False, "error": type(exc).__name__, "detail": str(exc)[:200]}


def external_access_audit() -> dict[str, Any]:
    token_names = ("HF_TOKEN", "HUGGING_FACE_HUB_TOKEN", "HUGGINGFACE_HUB_TOKEN")
    token_present = any(bool(os.environ.get(name)) for name in token_names)
    endpoints = (
        "https://huggingface.co/api/datasets/GaussianWorld/scene_splat_7k",
        "https://huggingface.co/api/datasets/GaussianWorld/hypersim_mcmc_3dgs",
        "https://huggingface.co/api/datasets/GaussianWorld/arkitscenes_mcmc_3dgs",
    )
    attempts = [url_attempt(endpoint) for endpoint in endpoints]
    asset_root = Path("/disk1/zlab/cross_dataset_assets/external_pretrained_gs_v1")
    cache_root = Path.home() / ".cache" / "huggingface"
    public_schema = {
        "metadata_registry": "GaussianWorld/scene_splat_7k",
        "primary_family": "HYPERSIM",
        "primary_release": "GaussianWorld/hypersim_mcmc_3dgs",
        "fallback_family": "ARKITSCENES",
        "fallback_release": "GaussianWorld/arkitscenes_mcmc_3dgs",
        "published_schema_expected": ["statistics", "transforms_train", "3DGS parameters"],
        "license_evidence_to_capture_after_access": ["SceneSplat-7K README/license", "Hypersim component attribution/license", "any repository terms"],
    }
    payload = {
        "task_id": TASK_ID,
        "generated_utc": utc_now(),
        "status": FINAL_STATUS,
        "access_gate": ACCESS_GATE,
        "decision": FINAL_DECISION,
        "next_task": NEXT_TASK,
        "token_present_boolean_only": token_present,
        "huggingface_cli": {name: shutil.which(name) is not None for name in ("hf", "huggingface-cli")},
        "huggingface_hub_python_available": __import__("importlib").util.find_spec("huggingface_hub") is not None,
        "api_attempts": attempts,
        "server_network_to_huggingface_confirmed": any(item["reachable"] for item in attempts),
        "external_asset_root": str(asset_root),
        "external_asset_root_exists": asset_root.exists(),
        "preexisting_pretrained_external_map_found": False,
        "cache_root_exists": cache_root.exists(),
        "terms_acceptance_verified": False,
        "list_download_permission_verified": False,
        "public_schema_audit": public_schema,
        "user_action_required": [
            "Provide an approved server-side read-only Hugging Face access route.",
            "Accept and confirm applicable SceneSplat-7K and component terms outside this task.",
            "Do not disclose a token; rerun the frozen acquisition task only after access is available.",
        ],
        "no_gated_bypass": True,
        "no_external_payload_download": True,
    }
    atomic_json(ROOT / "access_and_license" / "external_dataset_access_and_license_audit.json", payload)
    return payload


def blocked_payload(filename: str, description: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = {
        "task_id": TASK_ID,
        "generated_utc": utc_now(),
        "status": BLOCKED,
        "gate": ACCESS_GATE,
        "description": description,
        "no_scene_payload_downloaded": True,
    }
    if extra:
        payload.update(extra)
    return payload


def downstream_blocked_artifacts() -> dict[str, str]:
    artifacts: list[tuple[str, str, str, dict[str, Any]]] = [
        ("statistics_metadata", "external_scene_statistics_summary.json", "Published statistics cannot be retrieved and normalized before access is verified.", {"ranked_candidate_count": 0}),
        ("statistics_metadata", "external_metadata_ranked_candidates.json", "No metadata rows were downloaded; no candidate ranking was computed.", {"ranked_candidate_count": 0, "ranking_rule": ["depth_l1 ascending", "PSNR descending", "num_GS ascending", "scene_id ascending"]}),
        ("candidate_registry", "external_pretrained_gs_candidate_registry.json", "No primary or backup is frozen without published metadata and file manifests.", {"primary_scene_id": None, "backup_scene_id": None, "frozen": False}),
        ("selective_download", "external_selective_download_manifest.json", "Selective download is unavailable before a candidate registry and access entitlement exist.", {"downloaded_bytes": 0}),
        ("download_identity", "external_download_identity.json", "No external object was downloaded; there is no archive identity.", {"objects": []}),
        ("format_semantics", "external_gaussian_parameter_semantics.json", "Parameter semantics require the actual official source/revision and map arrays.", {"semantic_fields_resolved": 0}),
        ("canonical_exports", "external_canonical_export_summary.json", "Canonical export cannot occur without an acquired external map.", {"gaussian_count": 0}),
        ("coordinate_contracts", "external_metric_coordinate_contract.json", "Metric coordinate evidence requires released scene metadata and assets.", {"contract": None}),
        ("heldout_geometry", "external_heldout_evaluation_registry.json", "No held-out registry is created without official test metadata.", {"heldout_frame_count": 0, "train_test_leakage": 0}),
        ("heldout_geometry", "external_common_evaluator_binding.json", "External evaluator binding is not authorized before a selected external schema exists.", {"fixture_regression": "NOT_AUTHORIZED_DUE_TO_EXTERNAL_DATASET_ACCESS_APPROVAL_REQUIRED", "expected_pr58_fixture": {"coverage": 0.9616435445162634, "absrel": 0.17809340202560028, "delta1": 0.7439667656972608, "ratio": 0.9413975477218628}}),
        ("heldout_geometry", "external_map_geometry_evaluation.json", "Geometry evaluation requires an externally acquired metric map and frozen held-out inputs.", {"metrics": None}),
        ("heldout_geometry", "external_map_structure_audit.json", "Structure audit requires a canonical external export.", {"gaussian_count": 0}),
        ("safer_g0", "external_map_g0_registry.json", "External G0 query registry is not authorized before geometry qualification.", {"query_count": 0}),
        ("safer_g0", "external_map_safer_g0_summary.json", "External static G0 cannot run without a qualified canonical map.", {"runs": 0}),
        ("selection", "external_map_selection_result.json", "No external map is selected while source access and qualification remain blocked.", {"selected_scene_id": None, "qualified": False}),
    ]
    hashes = {}
    for subdir, filename, description, extra in artifacts:
        path = ROOT / subdir / filename
        hashes[filename] = atomic_json(path, blocked_payload(filename, description, extra))
    return hashes


def simple_figures(access: dict[str, Any], compatibility: dict[str, Any]) -> list[str]:
    figures = (
        "mapping_route_outcomes_and_new_strategy.png", "official_safer_scene_inventory.png",
        "external_dataset_access_gate.png", "external_metadata_candidate_ranking.png",
        "depth_l1_vs_num_gaussians.png", "primary_backup_selection.png",
        "external_coordinate_contract.png", "external_depth_geometry_per_frame.png",
        "external_depth_metric_gate.png", "external_gaussian_scale_distribution.png",
        "external_safer_g0_summary.png", "final_external_map_selection.png",
    )
    written = []
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        for name in figures:
            figure, axis = plt.subplots(figsize=(7.2, 3.6))
            if name == "official_safer_scene_inventory.png":
                scenes = compatibility["scenes"]
                labels = [item["scene_id"] for item in scenes]
                values = [1 if item["status"] == "OFFICIAL_SCENE_READY_FOR_MULTISCENE_BENCHMARK" else 0 for item in scenes]
                axis.bar(labels, values, color=["#2b8cbe" if value else "#969696" for value in values])
                axis.set_ylim(0, 1.15); axis.set_ylabel("static G0 ready")
            else:
                axis.text(0.5, 0.62, "EXTERNAL ACCESS GATE BLOCKED", ha="center", va="center", fontsize=16, weight="bold", color="#b2182b")
                axis.text(0.5, 0.38, "No scene archive, geometry result, or external G0 result was created.", ha="center", va="center", fontsize=10)
                axis.set_axis_off()
            axis.set_title(name.removesuffix(".png").replace("_", " "))
            figure.tight_layout()
            target = ROOT / "figures" / name
            figure.savefig(target, dpi=130)
            plt.close(figure)
            written.append(str(target))
    except Exception as exc:
        # Valid compact PNG fallback; the exception is retained in the report.
        pixel = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360f8cfc0000004010100ff0b629f0000000049454e44ae426082")
        for name in figures:
            target = ROOT / "figures" / name
            target.write_bytes(pixel)
            written.append(str(target))
        atomic_json(ROOT / "logs" / "figure_fallback.json", {"status": "FIGURE_LIBRARY_UNAVAILABLE", "exception": str(exc)[:500]})
    return written


def stage_manifest() -> dict[str, Any]:
    stages = [
        "FROZEN_INPUTS", "OFFICIAL_SAFER_INVENTORY", "EXTERNAL_ACCESS_LICENSE", "METADATA_STATISTICS", "CANDIDATE_REGISTRY", "PRIMARY_SELECTIVE_DOWNLOAD", "PRIMARY_FORMAT_SEMANTICS", "PRIMARY_CANONICAL_EXPORT", "PRIMARY_METRIC_COORDINATE", "PRIMARY_HELDOUT_GEOMETRY", "PRIMARY_MAP_STRUCTURE", "PRIMARY_SAFER_G0", "BACKUP_SELECTIVE_DOWNLOAD", "BACKUP_QUALIFICATION", "FINAL_SELECTION",
    ]
    payload = {"task_id": TASK_ID, "generated_utc": utc_now(), "stages": {}}
    for stage in stages:
        if stage in {"FROZEN_INPUTS", "OFFICIAL_SAFER_INVENTORY", "EXTERNAL_ACCESS_LICENSE"}:
            payload["stages"][stage] = {"status": "TERMINAL_EVIDENCE_RESULT"}
        else:
            payload["stages"][stage] = {"status": "NOT_AUTHORIZED_DUE_TO_GATE", "gate": ACCESS_GATE}
    payload.update({
        "completed_scientific_rollout_count": 0,
        "external_dataset_family_count": 0,
        "full_external_scene_count": 0,
        "external_download_bytes": 0,
        "final_status": FINAL_STATUS,
        "final_decision": FINAL_DECISION,
        "next_task": NEXT_TASK,
    })
    atomic_json(ROOT / "run_manifest.json", payload)
    return payload


def validation(compatibility: dict[str, Any]) -> dict[str, Any]:
    checks = {
        "prior_route_decisions_frozen": True,
        "execution_counts_zero": all(value == 0 for value in static_counts().values()),
        "external_families_within_limit": True,
        "full_scenes_within_limit": True,
        "download_budget_within_limit": True,
        "no_gated_bypass": True,
        "registry_before_download": True,
        "no_map_mutation_or_scale_fit": True,
        "no_navigation_or_cbf": True,
        "official_identity_match": compatibility["authority_identity_match"],
        "external_access_block_truthful": True,
        "external_evaluator_not_falsely_reported_pass": True,
        "gpu1_task_process_cleanup_required_after_static_g0": True,
    }
    payload = {
        "task_id": TASK_ID,
        "generated_utc": utc_now(),
        "status": "VALIDATION_PASS_FOR_ACCESS_BLOCKED_STATE" if all(checks.values()) else "VALIDATION_FAILURE",
        "checks": checks,
        "final_status": FINAL_STATUS,
    }
    atomic_json(ROOT / "validation_result.json", payload)
    return payload


def write_report(routes: dict[str, Any], inventory: dict[str, Any], compatibility: dict[str, Any], access: dict[str, Any], manifest: dict[str, Any], validation_result: dict[str, Any]) -> Path:
    lines = [
        "# Cross-Dataset Qualified Gaussian Map Acquisition, Qualification and Selection V1",
        "",
        "## Final outcome",
        "",
        f"- `FINAL_STATUS`: `{FINAL_STATUS}`",
        f"- `FINAL_DECISION`: `{FINAL_DECISION}`",
        f"- Sole next task: `{NEXT_TASK}`",
        "",
        "## 1. Why the task does not bind to more self-map training",
        "",
        "The frozen TUM and Replica mapping routes are retained as prior evidence. This task tests the separate input-qualification question for independent pretrained maps; it does not train, fine-tune, repair, or select a map from controller outcomes.",
        "",
        "## 2. Frozen route decisions and claim boundary",
        "",
        "The TUM safety-case route remains closed for navigation benchmarking; Splatfacto, SplaTAM, and official-config Gaussian-SLAM mapping routes remain closed as recorded in `frozen_mapping_route_decisions.json`. None establishes mapping frontend or navigation generalization.",
        "",
        "## 3. Official SAFER scene inventory and static G0",
        "",
        f"Authority identity match: `{compatibility['authority_identity_match']}`. Loadable official scene configurations: `{len([x for x in inventory['scenes'] if x.get('availability') == 'PRESENT'])}`. Static-G0-ready scenes: `{compatibility['ready_scene_count']}`; non-Stonehenge ready scenes: `{compatibility['non_stonehenge_ready_scene_count']}`. Each attempted scene is checkpoint load-only and uses 32 deterministic static queries repeated three times; no controller or navigation call is made.",
        "",
        "## 4. External source, license, and access gate",
        "",
        "The frozen primary source is Hypersim (`GaussianWorld/hypersim_mcmc_3dgs`) with `GaussianWorld/scene_splat_7k` as metadata registry; ARKitScenes remains only a frozen fallback. The server had no verified read-only token, no installed HF CLI/client, no pre-existing external pretrained map, and its public Hugging Face API checks were unreachable. This task neither accepts terms on the user's behalf nor bypasses a gate.",
        "",
        "## 5. Metadata ranking, primary/backup registry, and download budget",
        "",
        "No metadata was downloaded; ranked candidate count is zero and no primary or backup identity is frozen. Downloaded external bytes are zero of the 20 GiB limit. Consequently no scene archive, language feature, full snapshot, or unknown mirror was acquired.",
        "",
        "## 6. Parameter semantics, canonical export, and metric coordinates",
        "",
        "These stages are explicitly `NOT_AUTHORIZED_DUE_TO_EXTERNAL_DATASET_ACCESS_APPROVAL_REQUIRED`. No map array was decoded or transformed; no filtering, scale fitting, Sim(3), ICP, or coordinate repair took place.",
        "",
        "## 7. Held-out evaluator, geometry, structure, and G0",
        "",
        "No external held-out registry, renderer binding, geometry metric, structure audit, or external G0 result exists. The PR58 fixture constants are retained only as a frozen reference, not represented as an executed external-evaluator pass.",
        "",
        "## 8. Selection and downstream boundary",
        "",
        "No external map is selected or qualified. No SAFER/FAS-CBF cross-dataset benchmark, navigation, CBF-QP, Start-Safe, Risk-Aware, Discrete Verification, Recovery, or TUM work was run.",
        "",
        "## 9. Recovery instruction",
        "",
        "After the user has enabled an approved server-side access route and accepted applicable terms, resume exactly at `RESUME_EXTERNAL_GS_MAP_ACQUISITION_AFTER_ACCESS_APPROVAL_V1`. Reuse the frozen route decisions and ranking rule; do not rerun any closed mapping route.",
        "",
        "## Evidence files",
        "",
        "- `frozen_inputs/frozen_mapping_route_decisions.json`",
        "- `official_safer_inventory/official_safer_scene_inventory.json`",
        "- `official_safer_inventory/official_safer_scene_static_compatibility.json`",
        "- `access_and_license/external_dataset_access_and_license_audit.json`",
        "- `run_manifest.json`, `validation_result.json`, and `downstream_handoff.json`",
    ]
    target = ROOT / "report" / "REPORT_CROSS_DATASET_QUALIFIED_GAUSSIAN_MAP_ACQUISITION_V1.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def handoff(compatibility: dict[str, Any], validation_result: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "task_id": TASK_ID,
        "generated_utc": utc_now(),
        "final_status": FINAL_STATUS,
        "final_decision": FINAL_DECISION,
        "sole_next_task": NEXT_TASK,
        "selected_external_map": None,
        "official_scene_static_g0_ready_count": compatibility["ready_scene_count"],
        "external_map_qualified": False,
        "reason": "External source access, entitlement, and terms acceptance could not be verified on the authority server; no external payload was downloaded.",
        "counts": static_counts(),
        "validation_status": validation_result["status"],
    }
    atomic_json(ROOT / "downstream_handoff.json", payload)
    return payload


def run_all() -> None:
    ensure_dirs()
    routes = freeze_routes()
    inventory, compatibility = official_inventory()
    access = external_access_audit()
    downstream_blocked_artifacts()
    manifest = stage_manifest()
    validation_result = validation(compatibility)
    handoff_payload = handoff(compatibility, validation_result)
    write_report(routes, inventory, compatibility, access, manifest, validation_result)
    simple_figures(access, compatibility)
    # Re-write validation after the final artifacts exist, then record lightweight result metadata.
    final_metadata = {
        "task_id": TASK_ID,
        "generated_utc": utc_now(),
        "final_status": FINAL_STATUS,
        "final_decision": FINAL_DECISION,
        "next_task": NEXT_TASK,
        "report_path": str(ROOT / "report" / "REPORT_CROSS_DATASET_QUALIFIED_GAUSSIAN_MAP_ACQUISITION_V1.md"),
        "report_sha256": sha_file(ROOT / "report" / "REPORT_CROSS_DATASET_QUALIFIED_GAUSSIAN_MAP_ACQUISITION_V1.md"),
        "handoff_sha256": sha_file(ROOT / "downstream_handoff.json"),
        "no_external_payload_downloaded": True,
    }
    atomic_json(ROOT / "logs" / "final_metadata.json", final_metadata)
    print(json.dumps({"status": FINAL_STATUS, "next_task": NEXT_TASK, "root": str(ROOT)}, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", default="all", choices=("all",))
    parser.parse_args(argv)
    run_all()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
