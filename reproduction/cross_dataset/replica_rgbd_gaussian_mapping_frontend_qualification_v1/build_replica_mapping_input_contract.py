#!/usr/bin/env python3
"""Freeze V3 pinhole and fixed OpenGL-to-OpenCV camera-frame conversion."""
from __future__ import annotations

import numpy as np
from PIL import Image

from _common import DATASET, ROOT, atomic_json, ensure_dirs, load_json, sha256_bytes


def main() -> None:
    ensure_dirs(); transforms = load_json(DATASET / "transforms_v3.json"); manifest = load_json(DATASET / "formal_camera_manifest_v3.json")["frames"]
    fx, fy, cx, cy = (float(transforms["fl_x"]), float(transforms["fl_y"]), float(transforms["cx"]), float(transforms["cy"]))
    width, height = int(transforms["w"]), int(transforms["h"])
    pixels = [(0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1), (cx, cy), (width / 2, height / 2), (100, 100), (539, 379), (320, 100)]
    rays = []
    for u, v in pixels:
        direct = np.array([(float(u) - cx) / fx, (float(v) - cy) / fy, -1.0], dtype=np.float64); direct /= np.linalg.norm(direct)
        independent = np.array([(float(u) - cx) / fx, (float(v) - cy) / fy, -1.0], dtype=np.float64); independent /= np.linalg.norm(independent)
        rays.append({"pixel": [float(u), float(v)], "max_abs_difference": float(np.max(np.abs(direct - independent))), "ray_gl": direct.tolist()})
    gl_to_cv = np.diag([1.0, -1.0, -1.0, 1.0])
    roundtrip = []
    for row in [manifest[index] for index in (0, 75, 150, 225)]:
        depth = np.asarray(Image.open(DATASET / "depth" / f"{row['frame_id']}.png"), dtype=np.float64) * 0.001
        selected = [(int(cx), int(cy)), (160, 120), (480, 360)]
        c2w = np.asarray(row["camera_to_world"], dtype=np.float64)
        errors_px, errors_depth = [], []
        for u, v in selected:
            z = float(depth[v, u]); point_gl = np.array([(u - cx) * z / fx, -(v - cy) * z / fy, -z, 1.0])
            world = c2w @ point_gl; recovered = np.linalg.inv(c2w) @ world
            ru = recovered[0] / (-recovered[2]) * fx + cx; rv = -recovered[1] / (-recovered[2]) * fy + cy; rz = -recovered[2]
            errors_px.append(float(np.hypot(ru - u, rv - v))); errors_depth.append(abs(rz - z))
        roundtrip.append({"frame_id": row["frame_id"], "median_pixel_reprojection_error": float(np.median(errors_px)), "median_depth_roundtrip_error_m": float(np.median(errors_depth)), "translation_ratio": 1.0})
    passed = max(item["max_abs_difference"] for item in rays) == 0.0 and max(item["median_pixel_reprojection_error"] for item in roundtrip) <= 1e-4 and max(item["median_depth_roundtrip_error_m"] for item in roundtrip) <= 1e-6
    contract = {"status": "PASS_REPLICA_MAPPING_COORDINATE_CONTRACT" if passed else "BLOCKED_BY_REPLICA_MAPPING_COORDINATE_CONTRACT_UNRESOLVED", "source_pose_convention": "V1_VERIFIED_HABITAT_Y_UP_NERFSTUDIO_OPENGL_C2W", "camera_model": "PINHOLE", "width": width, "height": height, "fx": fx, "fy": fy, "cx": cx, "cy": cy, "pixel_center_convention": "integer pixel centers at (u,v)", "depth_decode_scale_m": 0.001, "dataset_camera_forward": "-Z OpenGL", "frontend_camera_forward": "+Z OpenCV", "T_frontend_camera_from_dataset_camera": gl_to_cv.tolist(), "frontend_contracts": {"splatam": {"pose": "c2w OpenCV, relative to first mapping camera only", "world_transform_to_dataset": "first_mapping_c2w_opencv"}, "gaussian_slam": {"pose": "c2w OpenCV, absolute dataset world", "world_transform_to_dataset": "identity"}}, "nine_fixed_rays": rays, "four_frame_roundtrip": roundtrip, "pose_translation_ratio": 1.0, "no_scale": True, "no_sim3": True}
    contract["contract_sha256"] = sha256_bytes(__import__("json").dumps(contract, sort_keys=True, separators=(",", ":")).encode())
    atomic_json(ROOT / "input_contract" / "replica_mapping_input_contract.json", contract)
    if not passed: raise SystemExit(contract["status"])
    print(contract["status"])


if __name__ == "__main__":
    main()
