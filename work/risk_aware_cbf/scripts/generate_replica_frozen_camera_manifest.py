#!/usr/bin/env python3
"""Generate exactly one immutable 300-row Replica camera manifest."""
import argparse
import csv
import hashlib
import json
import math
import random
import subprocess
from pathlib import Path

import numpy as np


SEED = 20260715
UP = np.array([0.0, 1.0, 0.0])


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_csv(path, rows, fields=None):
    path = Path(path)
    fields = fields or list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def normalize(vector):
    vector = np.asarray(vector, dtype=float)
    length = float(np.linalg.norm(vector))
    if not math.isfinite(length) or length < 1e-6:
        raise ValueError("degenerate vector")
    return vector / length


def resample_polyline(points, count):
    values = [np.asarray(point, dtype=float) for point in points]
    lengths = np.array([np.linalg.norm(values[i + 1] - values[i]) for i in range(len(values) - 1)], dtype=float)
    cumulative = np.concatenate(([0.0], np.cumsum(lengths)))
    if not math.isfinite(float(cumulative[-1])) or cumulative[-1] < 0.10 * (count - 1):
        raise ValueError("polyline_too_short_for_preregistered_spacing")
    targets = np.linspace(0.0, cumulative[-1], count)
    samples = []
    segment = 0
    for target in targets:
        while segment < len(lengths) - 1 and cumulative[segment + 1] < target:
            segment += 1
        ratio = 0.0 if lengths[segment] == 0 else (target - cumulative[segment]) / lengths[segment]
        samples.append(values[segment] + ratio * (values[segment + 1] - values[segment]))
    return samples, cumulative


def tangent_at(samples, index):
    candidates = []
    for distance in range(1, len(samples)):
        if index + distance < len(samples):
            candidates.append(samples[index + distance] - samples[index])
        if index - distance >= 0:
            candidates.append(samples[index] - samples[index - distance])
        for candidate in candidates[-2:]:
            if np.linalg.norm(candidate) >= 1e-6:
                return normalize(candidate)
    raise ValueError("no_non_degenerate_path_tangent")


def yaw_forward(forward, degrees):
    angle = math.radians(degrees)
    # Rodrigues rotation around the audited +Y world-up axis.
    return normalize(forward * math.cos(angle) + np.cross(UP, forward) * math.sin(angle) + UP * np.dot(UP, forward) * (1 - math.cos(angle)))


def c2w_from_forward(position, forward):
    right = normalize(np.cross(forward, UP))
    camera_up = normalize(np.cross(right, forward))
    rotation = np.column_stack((right, camera_up, -forward))
    if abs(np.linalg.det(rotation) - 1.0) > 1e-6:
        raise ValueError("invalid_camera_rotation")
    matrix = np.eye(4, dtype=float)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = position
    return matrix


def quaternion_xyzw(rotation):
    matrix = np.asarray(rotation, dtype=float)
    trace = float(np.trace(matrix))
    if trace > 0:
        scale = math.sqrt(trace + 1.0) * 2.0
        w, x, y, z = 0.25 * scale, (matrix[2, 1] - matrix[1, 2]) / scale, (matrix[0, 2] - matrix[2, 0]) / scale, (matrix[1, 0] - matrix[0, 1]) / scale
    else:
        index = int(np.argmax(np.diag(matrix)))
        if index == 0:
            scale = math.sqrt(1.0 + matrix[0, 0] - matrix[1, 1] - matrix[2, 2]) * 2.0
            w, x, y, z = (matrix[2, 1] - matrix[1, 2]) / scale, 0.25 * scale, (matrix[0, 1] + matrix[1, 0]) / scale, (matrix[0, 2] + matrix[2, 0]) / scale
        elif index == 1:
            scale = math.sqrt(1.0 + matrix[1, 1] - matrix[0, 0] - matrix[2, 2]) * 2.0
            w, x, y, z = (matrix[0, 2] - matrix[2, 0]) / scale, (matrix[0, 1] + matrix[1, 0]) / scale, 0.25 * scale, (matrix[1, 2] + matrix[2, 1]) / scale
        else:
            scale = math.sqrt(1.0 + matrix[2, 2] - matrix[0, 0] - matrix[1, 1]) * 2.0
            w, x, y, z = (matrix[1, 0] - matrix[0, 1]) / scale, (matrix[0, 2] + matrix[2, 0]) / scale, (matrix[1, 2] + matrix[2, 1]) / scale, 0.25 * scale
    return [float(x), float(y), float(z), float(w)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--pose-conversion", type=Path, required=True)
    parser.add_argument("--renderer-manifest", type=Path, required=True)
    parser.add_argument("--protocol-git-blob", required=True)
    parser.add_argument("--gpu-device", type=int, default=0)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--spatial-locations", type=int, default=100)
    parser.add_argument("--max-anchor-attempts", type=int, default=500)
    args = parser.parse_args()
    if (args.seed, args.spatial_locations, args.max_anchor_attempts) != (SEED, 100, 500):
        raise SystemExit("frozen protocol arguments changed")
    args.out.mkdir(parents=True, exist_ok=True)
    for name in ("camera_locations.csv", "formal_camera_manifest.csv", "path_anchor_manifest.csv", "path_polyline.csv", "manifest_metadata.json", "formal_render_lock.json"):
        if (args.out / name).exists():
            raise SystemExit("refuse to overwrite frozen artifact: " + name)

    import habitat_sim

    random.seed(args.seed)
    np.random.seed(args.seed)
    sim_cfg = habitat_sim.SimulatorConfiguration()
    sim_cfg.scene_id = str(args.scene_root / "mesh.ply")
    sim_cfg.enable_physics = False
    sim_cfg.gpu_device_id = args.gpu_device
    sim = habitat_sim.Simulator(habitat_sim.Configuration(sim_cfg, [habitat_sim.agent.AgentConfiguration()]))
    try:
        pathfinder = sim.pathfinder
        pathfinder.seed(args.seed)
        navmesh = args.scene_root / "habitat" / "mesh_semantic.navmesh"
        if not pathfinder.load_nav_mesh(str(navmesh)):
            raise RuntimeError("official_navmesh_load_failed")
        anchors = [np.asarray(pathfinder.get_random_navigable_point(), dtype=float)]
        polylines = []
        for attempt in range(1, args.max_anchor_attempts + 1):
            candidate = np.asarray(pathfinder.get_random_navigable_point(), dtype=float)
            if not np.isfinite(candidate).all() or np.linalg.norm(candidate - anchors[-1]) < 1.0:
                continue
            shortest = habitat_sim.ShortestPath()
            shortest.requested_start = anchors[-1]
            shortest.requested_end = candidate
            if not pathfinder.find_path(shortest) or not math.isfinite(float(shortest.geodesic_distance)):
                continue
            points = [np.asarray(point, dtype=float) for point in shortest.points]
            if len(points) < 2:
                continue
            anchors.append(candidate)
            polylines.extend(points if not polylines else points[1:])
            if len(anchors) == args.spatial_locations:
                break
        if len(anchors) != args.spatial_locations:
            raise RuntimeError("blocked_by_insufficient_preregistered_navmesh_coverage")
        samples, cumulative = resample_polyline(polylines, args.spatial_locations)
        if any(not pathfinder.is_navigable(point) for point in samples):
            raise RuntimeError("resampled_point_not_navigable")
        rows, locations = [], []
        yaw_offsets = [0, -60, 60]
        matrix_fields = [f"c2w_{row}{col}" for row in range(4) for col in range(4)]
        for index, source in enumerate(samples):
            tangent = tangent_at(samples, index)
            camera_position = source + np.array([0.0, 1.5, 0.0])
            locations.append({"position_index": index, "source_navmesh_point_x": source[0], "source_navmesh_point_y": source[1], "source_navmesh_point_z": source[2], "camera_position_x": camera_position[0], "camera_position_y": camera_position[1], "camera_position_z": camera_position[2], "local_tangent_x": tangent[0], "local_tangent_y": tangent[1], "local_tangent_z": tangent[2]})
            for slot, yaw in enumerate(yaw_offsets):
                matrix = c2w_from_forward(camera_position, yaw_forward(tangent, yaw))
                quat = quaternion_xyzw(matrix[:3, :3])
                row = {"frame_id": f"frame_{index * 3 + slot:04d}", "position_index": index, "yaw_slot": slot, "yaw_offset_deg": yaw, "split": "eval" if (index * 3 + slot) % 10 == 0 else "train", "position_x": camera_position[0], "position_y": camera_position[1], "position_z": camera_position[2], "quat_x": quat[0], "quat_y": quat[1], "quat_z": quat[2], "quat_w": quat[3], "source_navmesh_point_x": source[0], "source_navmesh_point_y": source[1], "source_navmesh_point_z": source[2], "local_tangent_x": tangent[0], "local_tangent_y": tangent[1], "local_tangent_z": tangent[2], "scene": "apartment_0", "seed": args.seed, "protocol_version": "G0.5E-v1"}
                row.update({field: matrix.flat[i] for i, field in enumerate(matrix_fields)})
                rows.append(row)
        write_csv(args.out / "camera_locations.csv", locations)
        write_csv(args.out / "formal_camera_manifest.csv", rows)
        write_csv(args.out / "path_anchor_manifest.csv", [{"accepted_anchor_index": i, "x": point[0], "y": point[1], "z": point[2]} for i, point in enumerate(anchors)])
        write_csv(args.out / "path_polyline.csv", [{"polyline_index": i, "x": point[0], "y": point[1], "z": point[2]} for i, point in enumerate(polylines)])
        metadata = {"protocol_version": "G0.5E-v1", "scene": "apartment_0", "seed": args.seed, "spatial_locations": 100, "yaw_offsets_deg": yaw_offsets, "formal_frames": len(rows), "camera_height": 1.5, "path_length": float(cumulative[-1]), "pathfinder_seed_api": "pathfinder.seed", "camera_manifest_sha256": digest(args.out / "formal_camera_manifest.csv"), "camera_locations_sha256": digest(args.out / "camera_locations.csv"), "protocol_sha256": digest(args.protocol), "pose_conversion_sha256": digest(args.pose_conversion)}
        (args.out / "manifest_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        lock = {"protocol_git_blob": args.protocol_git_blob, "paths": {"protocol": str(args.protocol), "pose_conversion": str(args.pose_conversion), "camera_manifest": str(args.out / "formal_camera_manifest.csv"), "mesh": str(args.scene_root / "mesh.ply"), "navmesh": str(navmesh), "renderer_explicit_manifest": str(args.renderer_manifest)}, "sha256": {"protocol": digest(args.protocol), "pose_conversion": digest(args.pose_conversion), "camera_manifest": metadata["camera_manifest_sha256"], "mesh": digest(args.scene_root / "mesh.ply"), "navmesh": digest(navmesh), "renderer_explicit_manifest": digest(args.renderer_manifest)}}
        (args.out / "formal_render_lock.json").write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
        print("camera_manifest_rows=" + str(len(rows)))
    finally:
        sim.close()


if __name__ == "__main__":
    main()
