"""Build the fixed deterministic RGB-D surface-oriented Gaussian prior."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def array_sha(value: np.ndarray) -> str:
    return sha256_bytes(np.ascontiguousarray(value).tobytes())


def normalize(vector: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(vector, axis=-1, keepdims=True)
    return vector / np.maximum(norm, np.finfo(np.float64).tiny)


def rotmat_to_wxyz(rotation: np.ndarray) -> np.ndarray:
    """Deterministic matrix-to-quaternion conversion for proper rotations."""
    result = np.empty((rotation.shape[0], 4), dtype=np.float64)
    for index, matrix in enumerate(rotation):
        trace = float(np.trace(matrix))
        if trace > 0.0:
            scale = 2.0 * np.sqrt(trace + 1.0)
            result[index] = (0.25 * scale, (matrix[2, 1] - matrix[1, 2]) / scale,
                             (matrix[0, 2] - matrix[2, 0]) / scale, (matrix[1, 0] - matrix[0, 1]) / scale)
        else:
            axis = int(np.argmax(np.diag(matrix)))
            if axis == 0:
                scale = 2.0 * np.sqrt(1.0 + matrix[0, 0] - matrix[1, 1] - matrix[2, 2])
                result[index] = ((matrix[2, 1] - matrix[1, 2]) / scale, 0.25 * scale,
                                 (matrix[0, 1] + matrix[1, 0]) / scale, (matrix[0, 2] + matrix[2, 0]) / scale)
            elif axis == 1:
                scale = 2.0 * np.sqrt(1.0 + matrix[1, 1] - matrix[0, 0] - matrix[2, 2])
                result[index] = ((matrix[0, 2] - matrix[2, 0]) / scale, (matrix[0, 1] + matrix[1, 0]) / scale,
                                 0.25 * scale, (matrix[1, 2] + matrix[2, 1]) / scale)
            else:
                scale = 2.0 * np.sqrt(1.0 + matrix[2, 2] - matrix[0, 0] - matrix[1, 1])
                result[index] = ((matrix[1, 0] - matrix[0, 1]) / scale, (matrix[0, 2] + matrix[2, 0]) / scale,
                                 (matrix[1, 2] + matrix[2, 1]) / scale, 0.25 * scale)
    result = normalize(result)
    result[result[:, 0] < 0.0] *= -1.0
    return result


def construct(seed_path: Path) -> dict[str, np.ndarray]:
    seed = np.load(seed_path, allow_pickle=False)
    xyz = np.asarray(seed["xyz"])
    rgb = np.asarray(seed["rgb"])
    if xyz.shape != (359140, 3) or rgb.shape[0] != xyz.shape[0]:
        raise RuntimeError(f"METRIC_SEED_CONTRACT_MISMATCH:{xyz.shape}:{rgb.shape}")
    points = xyz.astype(np.float64, copy=False)
    tree = cKDTree(points)
    distance, neighbors = tree.query(points, k=17, workers=1, eps=0.0, p=2)
    if not np.all(neighbors[:, 0] == np.arange(len(points))):
        raise RuntimeError("CKDTREE_SELF_NEIGHBOR_CONTRACT_FAILURE")
    neighbor_points = points[neighbors[:, 1:]]
    centered = neighbor_points - neighbor_points.mean(axis=1, keepdims=True)
    covariance = np.einsum("nki,nkj->nij", centered, centered, optimize=True) / 16.0
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    normal = eigenvectors[:, :, 0]
    tangent1 = eigenvectors[:, :, 2]
    normal *= np.where(normal[np.arange(len(normal)), np.abs(normal).argmax(axis=1)] < 0.0, -1.0, 1.0)[:, None]
    tangent1 *= np.where(tangent1[np.arange(len(tangent1)), np.abs(tangent1).argmax(axis=1)] < 0.0, -1.0, 1.0)[:, None]
    tangent2 = normalize(np.cross(normal, tangent1))
    tangent1 = normalize(np.cross(tangent2, normal))
    rotation = np.stack((tangent1, tangent2, normal), axis=2)
    determinant = np.linalg.det(rotation)
    s_t1 = np.clip(np.sqrt(np.maximum(eigenvalues[:, 2], 0.0)), 0.006, 0.050)
    s_t2 = np.clip(np.sqrt(np.maximum(eigenvalues[:, 1], 0.0)), 0.006, 0.050)
    s_n_raw = np.clip(np.sqrt(np.maximum(eigenvalues[:, 0], 0.0)), 0.002, 0.015)
    s_n = np.minimum(s_n_raw, 0.35 * np.minimum(s_t1, s_t2))
    scales = np.stack((s_t1, s_t2, s_n), axis=1)
    quats = rotmat_to_wxyz(rotation)
    valid = (np.isfinite(eigenvalues).all(axis=1) & (eigenvalues >= -1e-10).all(axis=1)
             & np.isfinite(rotation).all(axis=(1, 2)) & (determinant > 0.0)
             & np.isfinite(quats).all(axis=1) & np.isfinite(scales).all(axis=1) & (scales > 0.0).all(axis=1))
    if not valid.all():
        fallback = np.clip(distance[:, 1:4].mean(axis=1), 0.006, 0.050)
        quats[~valid] = np.array([1.0, 0.0, 0.0, 0.0])
        scales[~valid] = fallback[~valid, None]
        normal[~valid] = 0.0
    return {"xyz": xyz, "rgb": rgb, "quats_wxyz": quats.astype(np.float32), "log_scales": np.log(scales).astype(np.float32),
            "normals": normal.astype(np.float32), "eigenvalues": eigenvalues.astype(np.float32), "prior_valid": valid.astype(np.uint8),
            "neighbor_distance_summary": np.asarray([distance[:, 1:].min(), np.median(distance[:, 1:]), distance[:, 1:].mean(), distance[:, 1:].max()], dtype=np.float64)}


def semantic_identity(arrays: dict[str, np.ndarray]) -> dict[str, str]:
    return {key: array_sha(value) for key, value in arrays.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    first, second = construct(args.seed), construct(args.seed)
    first_identity, second_identity = semantic_identity(first), semantic_identity(second)
    if first_identity != second_identity:
        raise RuntimeError("SURFACE_PRIOR_DETERMINISM_FAILURE")
    valid = first["prior_valid"].astype(bool)
    if valid.mean() < 0.995:
        raise RuntimeError(f"BLOCKED_BY_SURFACE_PRIOR_VALID_FRACTION:{valid.mean():.9f}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(args.out, **first)
    scales = np.exp(first["log_scales"])
    summary = {"algorithm": "DETERMINISTIC_TUM_RGBD_SURFACE_ORIENTED_INITIALIZATION", "scipy": {"version": __import__("scipy").__version__, "path": __import__("scipy").__file__, "ckdtree": "scipy.spatial._ckdtree.cKDTree"},
               "seed": {"path": str(args.seed), "count": int(len(first["xyz"])), "xyz_sha256": array_sha(first["xyz"]), "rgb_sha256": array_sha(first["rgb"]), "order_identity": True},
               "asset": {"path": str(args.out), "sha256": hashlib.sha256(args.out.read_bytes()).hexdigest(), "arrays_sha256": first_identity},
               "knn": {"k_query": 17, "nonself_neighbors": 16, "workers": 1, "eps": 0.0, "p": 2},
               "prior_valid_count": int(valid.sum()), "prior_valid_fraction": float(valid.mean()), "fallback_count": int((~valid).sum()),
               "tangent_scale_quantiles": np.quantile(scales[:, :2], [0.0, .05, .5, .95, 1.0]).tolist(), "normal_scale_quantiles": np.quantile(scales[:, 2], [0.0, .05, .5, .95, 1.0]).tolist(),
               "anisotropy_quantiles": np.quantile(scales[:, :2].max(axis=1) / scales[:, 2], [0.0, .05, .5, .95, 1.0]).tolist(), "quaternion_norm_max_abs_error": float(np.max(np.abs(np.linalg.norm(first["quats_wxyz"], axis=1) - 1.0))), "double_build_exact": True}
    args.summary.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
