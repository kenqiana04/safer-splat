#!/usr/bin/env python3
"""Read-only G0 inventory for locally available cross-dataset GSplat assets."""

from __future__ import annotations

import argparse
import csv
import hashlib
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


RESULT_DIR = Path("work/risk_aware_cbf/results/safer_baseline_cross_dataset_g0_g1")
SKIP_DIRS = {".git", "conda", "site-packages", "node_modules", "__pycache__", "traces", "trace", "raw_traces"}
CHECKPOINT_SUFFIXES = {".ply", ".splat", ".ckpt", ".pt", ".pth"}
GEOMETRY_SUFFIXES = {".obj", ".glb", ".gltf", ".npz"}
METADATA_NAMES = {"cameras.json", "transforms.json", "cfg_args", "input.ply"}

INVENTORY_FIELDS = [
    "candidate_id", "dataset_family", "scene_name", "source_type", "source_location",
    "source_reference", "source_verified", "license_status", "raw_images_available",
    "camera_metadata_available", "gsplat_checkpoint_available", "mesh_or_geometry_available",
    "metric_scale_available", "reconstruction_pipeline_known", "cross_scene",
    "true_cross_dataset", "cross_reconstruction", "eligible_for_compatibility_audit",
    "exclusion_reason", "notes",
]
SCORE_FIELDS = [
    "candidate_id", "dataset_family", "scene_name", "source_provenance_confirmed",
    "license_source_metadata_available", "gsplat_checkpoint_locally_available",
    "checkpoint_format_directly_parseable", "camera_coordinate_metadata_available",
    "metric_scale_available", "navigable_free_space_volume_exists", "static_scene",
    "independent_geometry_available", "different_dataset_family", "different_reconstruction_pipeline",
    "bounded_storage_compute_cost", "selection_score", "selection_rank", "notes",
]
PREREG_FIELDS = [
    "candidate_id", "tier", "dataset_family", "scene_name", "checkpoint_path", "geometry_path",
    "scale_source", "coordinate_source", "reconstruction_pipeline", "selection_score",
    "selection_rank", "selected_for_g1", "selection_reason", "notes",
]


def write_csv(path: Path, fields: list[str], rows: Iterable[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def candidate_id(source_root: Path, scene_root: Path) -> str:
    digest = hashlib.sha256(str(scene_root).encode("utf-8")).hexdigest()[:12]
    return f"local-{source_root.name.lower()}-{scene_root.name.lower()}-{digest}"


def read_ply_vertex_count(path: Path) -> int | None:
    try:
        with path.open("rb") as handle:
            for _ in range(80):
                line = handle.readline().decode("ascii", errors="ignore").strip()
                if line.startswith("element vertex "):
                    return int(line.rsplit(" ", 1)[1])
                if line == "end_header":
                    return None
    except (OSError, ValueError):
        return None
    return None


def artifact_kind(path: Path) -> str | None:
    name = path.name.lower()
    if name in METADATA_NAMES:
        return "metadata"
    if path.suffix.lower() in CHECKPOINT_SUFFIXES:
        return "checkpoint"
    if path.suffix.lower() in GEOMETRY_SUFFIXES or name.startswith("mesh."):
        return "geometry"
    return None


def scan_root(root: Path) -> tuple[dict[Path, list[Path]], dict[str, int]]:
    grouped: dict[Path, list[Path]] = defaultdict(list)
    counters = {"visited_directories": 0, "excluded_directories": 0, "artifact_files": 0, "errors": 0}
    if not root.exists():
        return grouped, counters
    for current, dirnames, filenames in os.walk(root, topdown=True, onerror=lambda _: None):
        counters["visited_directories"] += 1
        kept = []
        for dirname in dirnames:
            if dirname.lower() in SKIP_DIRS:
                counters["excluded_directories"] += 1
            else:
                kept.append(dirname)
        dirnames[:] = kept
        current_path = Path(current)
        for filename in filenames:
            path = current_path / filename
            if artifact_kind(path) is not None:
                grouped[current_path].append(path)
                counters["artifact_files"] += 1
    return grouped, counters


def build_inventory(search_roots: list[Path]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    inventory: list[dict[str, object]] = []
    search_rows: list[dict[str, object]] = []
    asset_rows: list[dict[str, object]] = []
    for root in search_roots:
        grouped, counters = scan_root(root)
        search_rows.append({"search_root": str(root), "exists": bool_text(root.exists()), **counters, "candidate_directories": len(grouped)})
        for scene_root, files in sorted(grouped.items(), key=lambda item: str(item[0]).lower()):
            checkpoints = [item for item in files if artifact_kind(item) == "checkpoint"]
            metadata = [item for item in files if artifact_kind(item) == "metadata"]
            geometry = [item for item in files if artifact_kind(item) == "geometry"]
            images_dir = scene_root / "images"
            checkpoint = next((item for item in checkpoints if item.name.lower() == "point_cloud.ply"), checkpoints[0] if checkpoints else None)
            gaussian_count = read_ply_vertex_count(checkpoint) if checkpoint and checkpoint.suffix.lower() == ".ply" else None
            size_bytes = sum(item.stat().st_size for item in files if item.exists())
            row = {
                "candidate_id": candidate_id(root, scene_root),
                "dataset_family": "unknown",
                "scene_name": scene_root.name,
                "source_type": "unknown",
                "source_location": str(scene_root),
                "source_reference": "",
                "source_verified": "false",
                "license_status": "unknown",
                "raw_images_available": bool_text(images_dir.is_dir()),
                "camera_metadata_available": bool_text(bool(metadata)),
                "gsplat_checkpoint_available": bool_text(checkpoint is not None),
                "mesh_or_geometry_available": bool_text(bool(geometry)),
                "metric_scale_available": "false",
                "reconstruction_pipeline_known": "false",
                "cross_scene": "false",
                "true_cross_dataset": "false",
                "cross_reconstruction": "false",
                "eligible_for_compatibility_audit": "false",
                "exclusion_reason": "source_or_checkpoint_provenance_unverified",
                "notes": "Discovered by local filename inventory only; directory naming is not provenance evidence.",
            }
            inventory.append(row)
            asset_rows.append({
                "candidate_id": row["candidate_id"], "source_root": str(root), "scene_root": str(scene_root),
                "checkpoint_path": str(checkpoint) if checkpoint else "", "checkpoint_format": checkpoint.suffix.lower().lstrip(".") if checkpoint else "",
                "camera_metadata_path": ";".join(str(item) for item in metadata), "image_source_path": str(images_dir) if images_dir.is_dir() else "",
                "mesh_or_geometry_path": ";".join(str(item) for item in geometry), "number_of_gaussians": gaussian_count if gaussian_count is not None else "",
                "file_size_bytes": size_bytes, "coordinate_metadata": bool_text(bool(metadata)), "scale_metadata": "false",
                "license_or_source_metadata": "false", "reconstruction_pipeline": "unknown", "local_available": "true", "source_verified": "false",
            })
    return inventory, search_rows, asset_rows


def reference_row(repo_root: Path) -> dict[str, object]:
    checkpoint = repo_root / "outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml"
    return {
        "candidate_id": "reference-stonehenge", "dataset_family": "SAFER_reference", "scene_name": "stonehenge",
        "source_type": "original_safer_reference", "source_location": str(checkpoint),
        "source_reference": "reproduction/scripts/run_official_runpy_smoke.py::SCENES['stonehenge']",
        "source_verified": "true", "license_status": "repository_reference", "raw_images_available": "false",
        "camera_metadata_available": "false", "gsplat_checkpoint_available": bool_text(checkpoint.exists()),
        "mesh_or_geometry_available": "false", "metric_scale_available": "false", "reconstruction_pipeline_known": "true",
        "cross_scene": "false", "true_cross_dataset": "false", "cross_reconstruction": "false",
        "eligible_for_compatibility_audit": bool_text(checkpoint.exists()),
        "exclusion_reason": "" if checkpoint.exists() else "reference_checkpoint_not_locally_available",
        "notes": "Tier-R parity reference only; it is excluded from cross-dataset counting.",
    }


def score_row(row: dict[str, object]) -> dict[str, object]:
    truth = lambda name: str(row[name]).lower() == "true"
    checkpoint_path = str(row["source_location"])
    parseable = checkpoint_path.lower().endswith((".yml", ".yaml", ".json", ".ply", ".splat", ".ckpt", ".pt", ".pth"))
    values = {
        "source_provenance_confirmed": 2 if truth("source_verified") else 0,
        "license_source_metadata_available": 1 if str(row["license_status"]) not in {"", "unknown"} else 0,
        "gsplat_checkpoint_locally_available": 2 if truth("gsplat_checkpoint_available") else 0,
        "checkpoint_format_directly_parseable": 2 if parseable else 0,
        "camera_coordinate_metadata_available": 1 if truth("camera_metadata_available") else 0,
        "metric_scale_available": 2 if truth("metric_scale_available") else 0,
        "navigable_free_space_volume_exists": 0,
        "static_scene": 0,
        "independent_geometry_available": 2 if truth("mesh_or_geometry_available") else 0,
        "different_dataset_family": 2 if truth("true_cross_dataset") else 0,
        "different_reconstruction_pipeline": 1 if truth("cross_reconstruction") else 0,
        "bounded_storage_compute_cost": 1,
    }
    return {"candidate_id": row["candidate_id"], "dataset_family": row["dataset_family"], "scene_name": row["scene_name"], **values, "selection_score": sum(values.values()), "selection_rank": "", "notes": "Score uses pre-execution metadata only."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=RESULT_DIR)
    parser.add_argument("--search-root", action="append", dest="search_roots")
    args = parser.parse_args()
    default_roots = [
        Path("/disk1/zlab/projects"), Path("/disk1/zlab/data"), Path("/disk1/zlab/datasets"), Path("/disk1/zlab/checkpoints"),
        Path(r"C:\Users\zlab\Documents"), Path(r"C:\Users\zlab\Desktop"),
    ]
    roots = [Path(item) for item in args.search_roots] if args.search_roots else default_roots
    inventory, search_rows, asset_rows = build_inventory(roots)
    inventory.append(reference_row(args.repo_root.resolve()))
    scores = [score_row(row) for row in inventory]
    scores.sort(key=lambda row: (-int(row["selection_score"]), str(row["dataset_family"]).lower(), str(row["scene_name"]).lower(), str(row["candidate_id"])))
    for rank, row in enumerate(scores, start=1):
        row["selection_rank"] = rank
    score_by_id = {str(row["candidate_id"]): row for row in scores}
    asset_by_id = {str(row["candidate_id"]): str(row["checkpoint_path"]) for row in asset_rows}
    eligible = [row for row in inventory if row["true_cross_dataset"] == "true" and row["eligible_for_compatibility_audit"] == "true"]
    eligible.sort(key=lambda row: int(score_by_id[str(row["candidate_id"])]["selection_rank"]))
    selected_ids = {str(row["candidate_id"]) for row in eligible[:3]}
    prereg = []
    for row in inventory:
        score = score_by_id[str(row["candidate_id"])]
        is_reference = row["candidate_id"] == "reference-stonehenge"
        selected = str(row["candidate_id"]) in selected_ids or (is_reference and row["gsplat_checkpoint_available"] == "true")
        prereg.append({
            "candidate_id": row["candidate_id"], "tier": "Tier-R" if is_reference else ("Tier-2" if row["true_cross_dataset"] == "true" else "Unclassified"),
            "dataset_family": row["dataset_family"], "scene_name": row["scene_name"], "checkpoint_path": asset_by_id.get(str(row["candidate_id"]), str(row["source_location"])) if row["gsplat_checkpoint_available"] == "true" else "",
            "geometry_path": "", "scale_source": "" if row["metric_scale_available"] == "false" else "verified metadata",
            "coordinate_source": "" if row["camera_metadata_available"] == "false" else "local metadata", "reconstruction_pipeline": "known" if row["reconstruction_pipeline_known"] == "true" else "unknown",
            "selection_score": score["selection_score"], "selection_rank": score["selection_rank"], "selected_for_g1": bool_text(selected),
            "selection_reason": "Tier-R reference parity" if is_reference else ("Eligible independent asset" if selected else row["exclusion_reason"]), "notes": row["notes"],
        })
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "dataset_source_inventory.csv", INVENTORY_FIELDS, inventory)
    write_csv(args.output_dir / "dataset_selection_score.csv", SCORE_FIELDS, scores)
    write_csv(args.output_dir / "selected_scene_preregistration.csv", PREREG_FIELDS, prereg)
    write_csv(args.output_dir / "asset_search_summary.csv", ["search_root", "exists", "visited_directories", "excluded_directories", "artifact_files", "errors", "candidate_directories"], search_rows)
    write_csv(args.output_dir / "asset_inventory_details.csv", list(asset_rows[0].keys()) if asset_rows else ["candidate_id", "source_root", "scene_root", "checkpoint_path", "checkpoint_format", "camera_metadata_path", "image_source_path", "mesh_or_geometry_path", "number_of_gaussians", "file_size_bytes", "coordinate_metadata", "scale_metadata", "license_or_source_metadata", "reconstruction_pipeline", "local_available", "source_verified"], asset_rows)
    timestamp = datetime.now(timezone.utc).isoformat()
    (args.output_dir / "README.md").write_text(
        "# SAFER Baseline Cross-Dataset G0-G1 Results\n\n"
        f"Generated by a read-only asset inventory at {timestamp}. G0 does not run navigation and does not establish generalization.\n",
        encoding="utf-8",
    )
    (args.output_dir / "source_provenance_notes.md").write_text(
        "# Source Provenance Notes\n\nLocal filenames and directories are discovery signals only. A candidate remains unverified until dataset source, checkpoint origin, and license conditions are documented.\n",
        encoding="utf-8",
    )
    (args.output_dir / "dataset_acquisition_plan.md").write_text(
        "# Acquisition Plan\n\nNo unknown or large asset is downloaded by this audit. For each future candidate, record the public or lab source, license, checkpoint provenance, coordinate/scale source, and geometry availability before rerunning G0.\n",
        encoding="utf-8",
    )
    print(f"wrote={args.output_dir}")
    print(f"local_candidate_count={len(inventory) - 1}")
    print(f"eligible_cross_dataset_count={len(eligible)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
