#!/usr/bin/env python3
"""Build, summarize, and Reference-B check V3 direct-mesh float64 coverage."""
from __future__ import annotations

import argparse
import csv
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import numpy as np

from _v3_common import ROOT, atomic_json, ensure_server_root, load_json, sha256_path

WIDTH, HEIGHT, FX, FY, CX, CY = 640, 480, 320.0, 320.0, 319.5, 239.5


def truth(value: str) -> bool:
    return value.lower() in {"1", "true"}


def grid_pixels() -> List[Tuple[int, int, str]]:
    xs = [int(round(value)) for value in np.linspace(0, WIDTH - 1, 41)]
    ys = [int(round(value)) for value in np.linspace(0, HEIGHT - 1, 31)]
    quarter_targets = [(WIDTH * .25, HEIGHT * .25), (WIDTH * .75, HEIGHT * .25), (WIDTH * .25, HEIGHT * .75), (WIDTH * .75, HEIGHT * .75)]
    quarter_pixels = {(min(xs, key=lambda x: abs(x - tx)), min(ys, key=lambda y: abs(y - ty))) for tx, ty in quarter_targets}
    values = []
    for y in ys:
        for x in xs:
            tag = "grid"
            if (x, y) == (min(xs, key=lambda q: abs(q - CX)), min(ys, key=lambda q: abs(q - CY))):
                tag = "grid_center"
            elif (x, y) in quarter_pixels:
                tag = "grid_quarter"
            values.append((x, y, tag))
    if len(values) != 1271:
        raise RuntimeError("frozen_grid_ray_count_failure")
    return values


def frame_id(pose: Dict[str, Any]) -> str:
    return f"{pose['candidate_id']}_yaw_{pose['yaw_slot']}"


def build_rays() -> None:
    ensure_server_root()
    poses = load_json(ROOT / "candidate_poses" / "candidate_pose_inventory.json")["poses"]
    output = ROOT / "independent_coverage" / "all_candidate_rays.csv"
    index = []
    pixels = grid_pixels()
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["frame_id", "pixel_x", "pixel_y", "tags", "role", "joint_bad", "rgb_only", "origin_x", "origin_y", "origin_z", "dir_x", "dir_y", "dir_z", "reference_b_key"])
        for pose in poses:
            matrix = np.asarray(pose["c2w"], dtype=np.float64)
            origin = matrix[:3, 3]
            rotation = matrix[:3, :3]
            identifier = frame_id(pose)
            index.append({"frame_id": identifier, **pose})
            for x, y, tag in pixels:
                local = np.asarray(((x - CX) / FX, -(y - CY) / FY, -1.0), dtype=np.float64)
                direction = rotation @ local
                direction /= np.linalg.norm(direction)
                writer.writerow([identifier, x, y, tag, "v3_candidate", "false", "false", *[f"{value:.17g}" for value in origin], *[f"{value:.17g}" for value in direction], "false"])
    atomic_json(ROOT / "independent_coverage" / "ray_input_index.json", {"view_count": len(index), "rays_per_view": 1271, "ray_count": len(index) * 1271, "views": index, "ray_csv_sha256": sha256_path(output)})


def summarize() -> None:
    ensure_server_root()
    row_path = ROOT / "independent_coverage" / "ray_rows.csv"
    input_index = {item["frame_id"]: item for item in load_json(ROOT / "independent_coverage" / "ray_input_index.json")["views"]}
    groups: Dict[str, List[Dict[str, str]]] = defaultdict(list)
    with row_path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            groups[row["frame_id"]].append(row)
    views = []
    locations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for identifier in sorted(groups):
        rows = groups[identifier]
        if len(rows) != 1271:
            raise RuntimeError("raycast_view_row_count_failure:" + identifier)
        hits = [row for row in rows if truth(row["hit"])]
        front = [row for row in rows if truth(row["any_front_hit"])]
        distances = [float(row["hit_distance"]) for row in hits]
        valid = [distance for distance in distances if math.isfinite(distance) and 0.05 <= distance <= 20.0]
        passed = len(valid) / 1271 >= 0.10 and len(front) > 0 and len(valid) == len(distances)
        pose = input_index[identifier]
        summary = {
            "frame_id": identifier, "candidate_id": pose["candidate_id"], "location_hash": pose["location_hash"], "yaw_slot": pose["yaw_slot"], "yaw_offset_deg": pose["yaw_offset_deg"], "final_yaw_deg": pose["final_yaw_deg"], "source_navmesh_position": pose["source_navmesh_position"], "camera_world_position": pose["camera_world_position"], "ray_count": 1271, "any_hit_fraction": len(hits) / 1271, "valid_near_far_hit_fraction": len(valid) / 1271, "front_facing_hit_fraction": len(front) / 1271, "back_facing_only_fraction": sum(truth(row["back_facing_only"]) for row in rows) / 1271, "center_ray_hit": next((truth(row["hit"]) for row in rows if row["tags"] == "grid_center"), None), "quarter_ray_hit_count": sum(truth(row["hit"]) for row in rows if row["tags"] == "grid_quarter"), "median_hit_distance_m": float(statistics.median(valid)) if valid else None, "hit_component_count": len({row["component_id"] for row in hits if row["component_id"]}), "status": "INDEPENDENT_VIEW_COVERAGE_PASS" if passed else "INDEPENDENT_VIEW_COVERAGE_FAIL",
        }
        views.append(summary)
        locations[pose["candidate_id"]].append(summary)
    location_summaries = []
    for candidate_id, group in sorted(locations.items()):
        group.sort(key=lambda item: item["yaw_slot"])
        if len(group) != 3:
            raise RuntimeError("independent_location_three_yaw_contract_failure")
        passed = all(item["status"] == "INDEPENDENT_VIEW_COVERAGE_PASS" for item in group)
        location_summaries.append({"candidate_id": candidate_id, "location_hash": group[0]["location_hash"], "source_navmesh_position": group[0]["source_navmesh_position"], "view_statuses": [item["status"] for item in group], "status": "INDEPENDENT_LOCATION_TRIPLET_PASS" if passed else "INDEPENDENT_LOCATION_TRIPLET_FAIL"})
    payload = {
        "status": "PASS_REPLICA_V3_INDEPENDENT_DIRECT_MESH_COVERAGE", "reference_a": "task_owned_cpu_bvh_float64_moller_trumbore", "reference_b": "task_owned_cpu_bruteforce_float64_moller_trumbore_on_key_rays", "mesh": "/disk1/zlab/cross_dataset_assets/raw/replica/replica_v1/apartment_0/mesh.ply", "ray_grid": [41, 31], "ray_count_per_view": 1271, "candidate_view_count": len(views), "independent_ray_count": len(views) * 1271, "independent_view_pass_count": sum(item["status"] == "INDEPENDENT_VIEW_COVERAGE_PASS" for item in views), "independent_triplet_pass_location_count": sum(item["status"] == "INDEPENDENT_LOCATION_TRIPLET_PASS" for item in location_summaries), "views": views, "locations": location_summaries, "ray_rows_server_only": str(row_path), "ray_rows_sha256": sha256_path(row_path), "bvh_log_server_only": str(ROOT / "logs" / "independent_bvh.log"),
    }
    atomic_json(ROOT / "independent_coverage" / "independent_candidate_coverage_summary.json", payload)


def build_key_rays() -> None:
    summary = load_json(ROOT / "independent_coverage" / "independent_candidate_coverage_summary.json")
    passed = [item for item in summary["locations"] if item["status"] == "INDEPENDENT_LOCATION_TRIPLET_PASS"]
    failed = [item for item in summary["locations"] if item["status"] == "INDEPENDENT_LOCATION_TRIPLET_FAIL"]
    if len(passed) < 4 or len(failed) < 4:
        raise RuntimeError("reference_b_requires_four_pass_and_four_fail_locations")
    selected = sorted(passed, key=lambda item: item["location_hash"])[:4] + sorted(failed, key=lambda item: item["location_hash"])[:4]
    all_rows = ROOT / "independent_coverage" / "all_candidate_rays.csv"
    chosen = {f"{item['candidate_id']}_yaw_0" for item in selected}
    output = ROOT / "independent_coverage" / "reference_b_key_rays.csv"
    captured = []
    with all_rows.open(encoding="utf-8", newline="") as source, output.open("w", encoding="utf-8", newline="") as target:
        reader = csv.DictReader(source)
        writer = csv.DictWriter(target, fieldnames=reader.fieldnames)
        writer.writeheader()
        for row in reader:
            if row["frame_id"] in chosen and row["tags"] == "grid_center":
                row["reference_b_key"] = "true"
                writer.writerow(row)
                captured.append({"frame_id": row["frame_id"], "candidate_id": row["frame_id"].rsplit("_yaw_", 1)[0], "pixel_x": int(row["pixel_x"]), "pixel_y": int(row["pixel_y"])})
    if len(captured) != 8:
        raise RuntimeError("reference_b_key_ray_count_failure")
    atomic_json(ROOT / "independent_coverage" / "reference_b_key_selection.json", {"key_ray_count": len(captured), "locations": [{"candidate_id": item["candidate_id"], "location_hash": item["location_hash"], "independent_status": item["status"]} for item in selected], "rays": captured, "key_ray_csv_sha256": sha256_path(output)})


def finalize_reference_b() -> None:
    summary_path = ROOT / "independent_coverage" / "independent_candidate_coverage_summary.json"
    summary = load_json(summary_path)
    with (ROOT / "independent_coverage" / "reference_b_key_rows.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    checked = sum(truth(row["reference_b_checked"]) for row in rows)
    agreement = sum(truth(row["reference_b_agree"]) for row in rows)
    summary["reference_b_checked_key_ray_count"] = checked
    summary["reference_b_agree_key_ray_count"] = agreement
    summary["reference_a_b_agreement"] = checked >= 8 and checked == agreement
    if not summary["reference_a_b_agreement"]:
        raise SystemExit("reference_a_b_disagreement")
    atomic_json(summary_path, summary)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-rays", action="store_true")
    parser.add_argument("--summarize", action="store_true")
    parser.add_argument("--build-key-rays", action="store_true")
    parser.add_argument("--finalize-reference-b", action="store_true")
    args = parser.parse_args()
    actions = [args.build_rays, args.summarize, args.build_key_rays, args.finalize_reference_b]
    if sum(actions) != 1:
        raise SystemExit("choose_exactly_one_action")
    if args.build_rays:
        build_rays()
    elif args.summarize:
        summarize()
    elif args.build_key_rays:
        build_key_rays()
    else:
        finalize_reference_b()
