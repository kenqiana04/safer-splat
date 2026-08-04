#!/usr/bin/env python3
"""Minimal deterministic COLMAP text-model reader/writer for the frozen audit."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np


def data_lines(path: Path):
    return [line.rstrip("\n") for line in path.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")]


def read_cameras(path: Path) -> dict:
    cameras = {}
    for line in data_lines(path):
        tok = line.split()
        cameras[int(tok[0])] = {
            "id": int(tok[0]), "model": tok[1], "width": int(tok[2]),
            "height": int(tok[3]), "params": [float(x) for x in tok[4:]],
            "raw": line,
        }
    return cameras


def read_images(path: Path) -> dict:
    lines = data_lines(path)
    if len(lines) % 2:
        raise RuntimeError(f"ODD_COLMAP_IMAGE_DATA_LINES {path} {len(lines)}")
    images = {}
    for index in range(0, len(lines), 2):
        header, points = lines[index], lines[index + 1]
        tok = header.split()
        if len(tok) < 10:
            raise RuntimeError(f"INVALID_COLMAP_IMAGE_HEADER {header}")
        point_tok = points.split()
        if len(point_tok) % 3:
            raise RuntimeError(f"INVALID_POINTS2D_LINE image={tok[0]}")
        image_id = int(tok[0])
        images[image_id] = {
            "id": image_id,
            "qvec": np.asarray([float(x) for x in tok[1:5]], dtype=np.float64),
            "tvec": np.asarray([float(x) for x in tok[5:8]], dtype=np.float64),
            "camera_id": int(tok[8]),
            "name": " ".join(tok[9:]),
            "header_raw": header,
            "points_tokens": point_tok,
        }
    return images


def read_points3d(path: Path) -> dict:
    points = {}
    for line in data_lines(path):
        tok = line.split()
        if len(tok) < 8 or (len(tok) - 8) % 2:
            raise RuntimeError(f"INVALID_POINT3D_LINE {tok[:9]}")
        point_id = int(tok[0])
        points[point_id] = {
            "id": point_id,
            "xyz": np.asarray([float(x) for x in tok[1:4]], dtype=np.float64),
            "rgb": tuple(int(x) for x in tok[4:7]),
            "error": float(tok[7]),
            "track": [(int(tok[i]), int(tok[i + 1])) for i in range(8, len(tok), 2)],
        }
    return points


def qvec_to_rotmat(qvec: np.ndarray) -> np.ndarray:
    q = qvec / np.linalg.norm(qvec)
    w, x, y, z = q
    return np.asarray([
        [1 - 2 * y * y - 2 * z * z, 2 * x * y - 2 * w * z, 2 * x * z + 2 * w * y],
        [2 * x * y + 2 * w * z, 1 - 2 * x * x - 2 * z * z, 2 * y * z - 2 * w * x],
        [2 * x * z - 2 * w * y, 2 * y * z + 2 * w * x, 1 - 2 * x * x - 2 * y * y],
    ], dtype=np.float64)


def camera_to_world(image: dict) -> np.ndarray:
    rotation = qvec_to_rotmat(image["qvec"])
    transform = np.eye(4, dtype=np.float64)
    transform[:3, :3] = rotation.T
    transform[:3, 3] = -rotation.T @ image["tvec"]
    return transform


def camera_center(image: dict) -> np.ndarray:
    return camera_to_world(image)[:3, 3]


def rotation_angle_deg(rotation: np.ndarray) -> float:
    value = max(-1.0, min(1.0, (float(np.trace(rotation)) - 1.0) / 2.0))
    return math.degrees(math.acos(value))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_cameras(path: Path, cameras: dict) -> None:
    rows = ["# Camera list with one line of data per camera:",
            "#   CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]",
            f"# Number of cameras: {len(cameras)}"]
    rows.extend(cameras[key]["raw"] for key in sorted(cameras))
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def write_images(path: Path, images: dict, kept_point_ids: set) -> None:
    rows = ["# Image list with two lines of data per image:",
            "#   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME",
            "#   POINTS2D[] as (X, Y, POINT3D_ID)",
            f"# Number of images: {len(images)}"]
    for image_id in sorted(images):
        image = images[image_id]
        rows.append(image["header_raw"])
        tok = image["points_tokens"][:]
        for index in range(2, len(tok), 3):
            point_id = int(tok[index])
            if point_id >= 0 and point_id not in kept_point_ids:
                tok[index] = "-1"
        rows.append(" ".join(tok))
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def write_points3d(path: Path, points: dict) -> None:
    rows = ["# 3D point list with one line of data per point:",
            "#   POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[] as (IMAGE_ID, POINT2D_IDX)",
            f"# Number of points: {len(points)}"]
    for point_id in sorted(points):
        point = points[point_id]
        xyz = " ".join(format(float(v), ".17g") for v in point["xyz"])
        rgb = " ".join(str(v) for v in point["rgb"])
        track = " ".join(f"{image_id} {point2d_idx}" for image_id, point2d_idx in point["track"])
        rows.append(f"{point_id} {xyz} {rgb} {format(float(point['error']), '.17g')} {track}".rstrip())
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
