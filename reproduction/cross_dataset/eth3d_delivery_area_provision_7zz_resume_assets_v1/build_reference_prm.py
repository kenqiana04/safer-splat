#!/usr/bin/env python3
"""Build the frozen reference-only 3D PRM and ideal UNKNOWN support graph."""

from __future__ import annotations

import hashlib
import json
import math
import multiprocessing as mp
from collections import defaultdict
from pathlib import Path

import numpy as np
import open3d as o3d
import trimesh
from scipy.spatial import cKDTree

from colmap_text import camera_center, qvec_to_rotmat, read_cameras, read_images
from reference_route_geometry import certified_segment_mesh_clearance
from task_config import QUARANTINE, TASK_ROOT


SEED = 20260804
NODE_SPACING = 0.05
MAX_EDGE = 0.40
NONMAP_RESERVE = 0.23526279441628825
MARGIN = 0.01
MAX_QUALIFIED_NODES = 512
EDGE_WORKERS = 8
EDGE_CLEARANCE_CERTIFICATION_CAP = NONMAP_RESERVE + MAX_EDGE

_EDGE_MESH = None


def edge_clearance_worker(payload):
    first, second, a, b = payload
    clearance, capped = certified_segment_mesh_clearance(
        _EDGE_MESH, a, b, EDGE_CLEARANCE_CERTIFICATION_CAP)
    return first, second, float(np.linalg.norm(b - a)), clearance, capped


def load_mesh(path: Path):
    mesh = trimesh.load(str(path), process=False, maintain_order=True)
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))
    return mesh


def make_scene(mesh):
    legacy = o3d.geometry.TriangleMesh()
    legacy.vertices = o3d.utility.Vector3dVector(np.asarray(mesh.vertices, dtype=np.float64))
    legacy.triangles = o3d.utility.Vector3iVector(np.asarray(mesh.faces, dtype=np.int32))
    tensor = o3d.t.geometry.TriangleMesh.from_legacy(legacy)
    scene = o3d.t.geometry.RaycastingScene()
    scene.add_triangles(tensor)
    return scene


def group_images(images: dict) -> dict:
    groups = defaultdict(list)
    for image in images.values():
        groups[Path(image["name"]).stem].append(image)
    return dict(groups)


def intrinsics(camera):
    if camera["model"] == "PINHOLE":
        return camera["params"]
    f, cx, cy = camera["params"]
    return [f, f, cx, cy]


def ideal_support(point, groups, group_centers, cameras, scene):
    # The frozen contract requires all TRAIN capture groups.  Do not prune to
    # an arbitrary nearest-group subset: outward-facing rig cameras can make a
    # farther capture the valid observing view even when nearer captures do
    # not project the free-space query.
    ordered_groups = sorted(groups, key=lambda group: (float(np.linalg.norm(group_centers[group] - point)), group))
    candidate = []
    for group in ordered_groups:
        views = []
        for image in groups[group]:
            camera = cameras[image["camera_id"]]
            rotation = qvec_to_rotmat(image["qvec"])
            camera_point = rotation @ point + image["tvec"]
            if camera_point[2] <= 0:
                continue
            fx, fy, cx, cy = intrinsics(camera)
            u = fx * camera_point[0] / camera_point[2] + cx
            v = fy * camera_point[1] / camera_point[2] + cy
            if not (0 <= u < camera["width"] and 0 <= v < camera["height"]):
                continue
            central = ((u - cx) / camera["width"]) ** 2 + ((v - cy) / camera["height"]) ** 2
            views.append((central, image))
        if views:
            image = min(views, key=lambda item: (item[0], item[1]["id"]))[1]
            origin = camera_center(image)
            vector = point - origin
            distance = float(np.linalg.norm(vector))
            if distance > 1e-9:
                candidate.append((group, origin, vector / distance, distance))
    if not candidate:
        return {"support_group_count": 0, "angular_spread_deg": 0.0, "primary": False,
                "projectable_group_count": 0, "finite_first_hit_count": 0,
                "blocked_by_first_surface_count": 0}
    rays = np.asarray([np.r_[origin, direction] for _, origin, direction, _ in candidate], dtype=np.float32)
    hits = scene.cast_rays(o3d.core.Tensor(rays))["t_hit"].numpy().astype(np.float64)
    support = [(candidate[index][0], candidate[index][2]) for index in range(len(candidate))
               if math.isfinite(float(hits[index])) and candidate[index][3] <= float(hits[index]) - MARGIN]
    max_angle = 0.0
    for first in range(len(support)):
        for second in range(first + 1, len(support)):
            cosine = max(-1.0, min(1.0, float(np.dot(support[first][1], support[second][1]))))
            max_angle = max(max_angle, math.degrees(math.acos(cosine)))
    return {"support_group_count": len(support), "angular_spread_deg": max_angle,
            "primary": len(support) >= 3 and max_angle >= 15.0,
            "projectable_group_count": len(candidate),
            "finite_first_hit_count": int(np.isfinite(hits).sum()),
            "blocked_by_first_surface_count": int(sum(
                math.isfinite(float(hits[index])) and candidate[index][3] > float(hits[index]) - MARGIN
                for index in range(len(candidate)))),
            "ray_distance_to_hit_examples_m": [[float(candidate[index][3]), float(hits[index])]
                                                  for index in range(min(5, len(candidate)))],
            "sensitivity": {f"groups_{groups_required}_angle_{angle}": len(support) >= groups_required and max_angle >= angle
                            for groups_required in (2, 3, 4) for angle in (5, 10, 15, 20)}}


def candidate_nodes(group_centers: dict) -> list:
    captures = sorted(group_centers)
    center_rows = [(group_centers[capture], "SAFE_CAMERA_GROUP_CENTER", capture) for capture in captures]
    center_points = np.asarray([row[0] for row in center_rows], dtype=np.float64)
    bounds = np.asarray([center_points.min(axis=0), center_points.max(axis=0)])
    # The frozen robot is free-3D, so verified-domain voxel candidates span all
    # 0.05 m lattice layers inside the observed rig-center bounds.  They remain
    # reference-only candidates and are subsequently gated by exact clearance
    # and ideal GT-supported knownness; the camera trajectory is never used as
    # a route.
    x_indices = range(int(math.floor(bounds[0, 0] / NODE_SPACING)),
                      int(math.ceil(bounds[1, 0] / NODE_SPACING)) + 1)
    y_indices = range(int(math.floor(bounds[0, 1] / NODE_SPACING)),
                      int(math.ceil(bounds[1, 1] / NODE_SPACING)) + 1)
    z_indices = range(int(math.floor(bounds[0, 2] / NODE_SPACING)),
                      int(math.ceil(bounds[1, 2] / NODE_SPACING)) + 1)
    center_tree = cKDTree(center_points)
    voxels = []
    for x_index in x_indices:
        for y_index in y_indices:
            for z_index in z_indices:
                point = np.asarray([x_index * NODE_SPACING, y_index * NODE_SPACING,
                                    z_index * NODE_SPACING], dtype=np.float64)
                if float(center_tree.query(point, k=1)[0]) < NODE_SPACING * 0.45:
                    continue
                label = f"{x_index}:{y_index}:{z_index}"
                order = hashlib.sha256(f"{SEED}:{label}".encode("ascii")).hexdigest()
                voxels.append((order, point, "VERIFIED_DOMAIN_DETERMINISTIC_VOXEL_SAMPLE", label))
    voxel_rows = [(point, source, label) for _, point, source, label in sorted(voxels)]
    return center_rows + voxel_rows


def main() -> None:
    model = QUARANTINE / "delivery_area_rig_undistorted" / "delivery_area" / "rig_calibration_undistorted"
    cameras, images = read_cameras(model / "cameras.txt"), read_images(model / "images.txt")
    groups = group_images(images)
    split = json.loads((TASK_ROOT / "split" / "pose_block_split_v1.json").read_text(encoding="utf-8"))
    train_groups = {group: groups[group] for group in split["TRAIN"]}
    group_centers = {group: np.mean([camera_center(image) for image in value], axis=0) for group, value in groups.items()}
    surface = QUARANTINE / "delivery_area_rig_occlusion" / "delivery_area" / "occlusion" / "surface_mesh.ply"
    mesh = load_mesh(surface)
    scene = make_scene(mesh)
    candidates = candidate_nodes(group_centers)
    nodes = []
    unknown_sensitivity_counts = defaultdict(int)
    clearance_pass_count = 0
    support_group_histogram = defaultdict(int)
    support_angle_values = []
    rejection_examples = []
    evaluated_candidate_count = 0
    for start in range(0, len(candidates), 256):
        batch = candidates[start:start + 256]
        batch_points = np.vstack([item[0] for item in batch])
        _, batch_clearances, _ = trimesh.proximity.closest_point(mesh, batch_points)
        for (point, source, label), clearance in zip(batch, np.asarray(batch_clearances, dtype=np.float64)):
            evaluated_candidate_count += 1
            if float(clearance) <= NONMAP_RESERVE:
                if len(rejection_examples) < 20:
                    rejection_examples.append({"source_label": label, "reason": "clearance",
                                               "reference_clearance_m": float(clearance)})
                continue
            clearance_pass_count += 1
            support = ideal_support(point, train_groups, group_centers, cameras, scene)
            support_group_histogram[support["support_group_count"]] += 1
            support_angle_values.append(float(support["angular_spread_deg"]))
            for key, passed in support.get("sensitivity", {}).items():
                unknown_sensitivity_counts[key] += int(passed)
            if not support["primary"]:
                if len(rejection_examples) < 20:
                    rejection_examples.append({"source_label": label, "reason": "ideal_unknown",
                                               "reference_clearance_m": float(clearance),
                                               "support_group_count": support["support_group_count"],
                                               "angular_spread_deg": support["angular_spread_deg"],
                                               "projectable_group_count": support["projectable_group_count"],
                                               "finite_first_hit_count": support["finite_first_hit_count"],
                                               "blocked_by_first_surface_count": support["blocked_by_first_surface_count"],
                                               "ray_distance_to_hit_examples_m": support.get("ray_distance_to_hit_examples_m", [])})
                continue
            nodes.append({"id": len(nodes), "point_m": [float(value) for value in point], "source": source,
                          "source_label": label, "reference_clearance_m": float(clearance), "ideal_support": support})
            if len(nodes) >= MAX_QUALIFIED_NODES:
                break
        if len(nodes) >= MAX_QUALIFIED_NODES:
            break
    node_gate_diagnostic = {
        "status": "PASS" if len(nodes) >= 30 else "FAIL",
        "candidate_node_count": len(candidates),
        "clearance_pass_count": clearance_pass_count,
        "primary_ideal_unknown_pass_count": len(nodes),
        "evaluated_candidate_count": evaluated_candidate_count,
        "implementation_qualified_node_cap": MAX_QUALIFIED_NODES,
        "candidate_voxel_dimensionality": "THREE_DIMENSIONAL_FREE_3D_ROBOT_CONTRACT",
        "proximity_batch_size": 256,
        "proximity_evaluation": "DETERMINISTIC_ORDER_BATCHED_UNTIL_QUALIFIED_NODE_CAP",
        "nonmap_reserve_m": NONMAP_RESERVE,
        "primary_support_group_count": 3,
        "primary_angular_spread_deg": 15.0,
        "support_group_histogram_after_clearance": dict(sorted(support_group_histogram.items())),
        "support_angle_range_deg": ([float(min(support_angle_values)), float(max(support_angle_values))]
                                    if support_angle_values else None),
        "rejection_examples": rejection_examples,
    }
    (TASK_ROOT / "routes" / "reference_prm_node_gate_diagnostic.json").parent.mkdir(parents=True, exist_ok=True)
    (TASK_ROOT / "routes" / "reference_prm_node_gate_diagnostic.json").write_text(
        json.dumps(node_gate_diagnostic, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if len(nodes) < 30:
        raise RuntimeError(f"INSUFFICIENT_SAFE_KNOWN_PRM_NODES {len(nodes)}")
    (TASK_ROOT / "routes" / "reference_prm_nodes_pre_edges.json").write_text(
        json.dumps({"status": "PASS_NODE_GATE", "nodes": nodes}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    node_points = np.asarray([node["point_m"] for node in nodes])
    tree = cKDTree(node_points)
    edge_pairs = set()
    for index, point in enumerate(node_points):
        distance, neighbors = tree.query(point, k=min(13, len(nodes)), distance_upper_bound=MAX_EDGE)
        for neighbor in np.atleast_1d(neighbors):
            neighbor = int(neighbor)
            if neighbor < len(nodes) and neighbor != index:
                edge_pairs.add(tuple(sorted((index, neighbor))))
    edge_work = []
    for first, second in sorted(edge_pairs):
        a, b = node_points[first], node_points[second]
        length = float(np.linalg.norm(b - a))
        if length > MAX_EDGE + 1e-12:
            continue
        edge_work.append((first, second, a, b))
    global _EDGE_MESH
    _EDGE_MESH = mesh
    # Materialize read-only acceleration data before fork so workers share it.
    _ = mesh.triangles_tree
    _ = mesh.triangles
    context = mp.get_context("fork")
    with context.Pool(processes=EDGE_WORKERS) as pool:
        edge_results = list(pool.imap(edge_clearance_worker, edge_work, chunksize=1))
    edges = []
    for first, second, length, clearance, capped in edge_results:
        if clearance <= NONMAP_RESERVE:
            continue
        residual_budget = clearance - NONMAP_RESERVE
        edges.append({"id": len(edges), "a": first, "b": second, "length_m": length,
                      "certified_reference_clearance_lower_bound_m": clearance,
                      "certified_residual_budget_lower_bound_m": residual_budget,
                      "planning_cost": length + 1.0 / residual_budget,
                      "planning_cost_contract": "edge_length_plus_inverse_reference_residual_budget",
                      "reference_clearance_is_conservative_lower_bound": capped,
                      "clearance_certification_cap_m": EDGE_CLEARANCE_CERTIFICATION_CAP,
                      "exact_within_certification_cap": not capped,
                      "exact_swept_sphere_collision_free_predicate": True})
    graph_payload = {"nodes": nodes, "edges": edges}
    identity = hashlib.sha256(json.dumps(graph_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    record = {
        "status": "PASS_REFERENCE_ONLY_PRM_GRAPH" if len(edges) else "FAIL",
        "classification": "PROJECT_REFERENCE_ROUTE_DESIGN_V1", "seed": SEED,
        "node_spacing_m": NODE_SPACING, "max_edge_m": MAX_EDGE,
        "robot_radius_m": 0.10, "nonmap_reserve_m": NONMAP_RESERVE,
        "candidate_map_access": False, "training_access": False,
        "candidate_node_count": len(candidates), "qualified_node_count": len(nodes),
        "edge_candidate_count": len(edge_work), "edge_worker_count": EDGE_WORKERS,
        "qualified_edge_count": len(edges), "graph_sha256": identity,
        "edge_clearance_certification_cap_m": EDGE_CLEARANCE_CERTIFICATION_CAP,
        "edge_clearance_capped_lower_bound_count": sum(
            edge["reference_clearance_is_conservative_lower_bound"] for edge in edges),
        "unknown_sensitivity_qualified_node_counts": dict(sorted(unknown_sensitivity_counts.items())),
        "exact_swept_segment_collision_predicate": True,
        "edge_cost_contract": "edge_length_plus_inverse_reference_residual_budget",
        "uncapped_clearance_claimed": False,
    }
    if record["status"] != "PASS_REFERENCE_ONLY_PRM_GRAPH":
        raise RuntimeError(f"REFERENCE_PRM_GRAPH_FAILURE {record}")
    (TASK_ROOT / "routes" / "reference_prm_graph_full.json").write_text(json.dumps({**record, **graph_payload}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (TASK_ROOT / "routes" / "reference_prm_contract.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (TASK_ROOT / "unknown" / "unknown_sensitivity_report.json").write_text(json.dumps({
        "status": "REPORT_ONLY_PRIMARY_UNCHANGED", "primary_groups": 3, "primary_angle_deg": 15,
        "qualified_node_counts": dict(sorted(unknown_sensitivity_counts.items())),
        "total_candidate_nodes": len(candidates)}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS_REFERENCE_PRM", len(nodes), len(edges), identity)


if __name__ == "__main__":
    main()
