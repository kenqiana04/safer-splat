"""Fixed identities and deterministic helpers for Replica render protocol V3."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

import numpy as np

ROOT = Path("/disk1/zlab/maintenance_records/replica_render_protocol_v3_coverage_qualification_v1")
SCENE_ROOT = Path("/disk1/zlab/cross_dataset_assets/raw/replica/replica_v1/apartment_0")
MESH = SCENE_ROOT / "mesh.ply"
NAVMESH = SCENE_ROOT / "habitat" / "mesh_semantic.navmesh"
V1_MANIFEST = Path("/disk1/zlab/cross_dataset_assets/manifests/replica_protocol_v1/formal_camera_manifest.csv")
V1_STAGING = Path("/disk1/zlab/cross_dataset_assets/processed/replica/apartment_0.rendering")
PYTHON = Path("/disk1/zlab/conda_envs/replica_habitat_renderer_py39/bin/python")
EXPECTED = {
    "mesh_sha256": "274677d9b7caa413230363b68f4aa472e5cc1afe87e422a489fa1b7d844c6182",
    "navmesh_sha256": "32296d6457d3855ffe172cf1970364559def5dd15892e149b44d0bc7c6b7e938",
    "v1_manifest_sha256": "1056121e4470124e180a3367172440f540f0acdc5adab665c3187ac8ab87be25",
    "v1_staging_tree_sha256": "39367c04f6e6ea510590f77ee1275e78333123608e6eb2223c1d419260288c51",
    "paired20_manifest_sha256": "380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6",
}
STATUS = {
    "input": "BLOCKED_BY_REPLICA_V3_INPUT_IDENTITY_MISMATCH",
    "nav": "BLOCKED_BY_REPLICA_V3_INSUFFICIENT_NAVMESH_CANDIDATES",
    "nondeterminism": "BLOCKED_BY_REPLICA_V3_CANDIDATE_GENERATION_NONDETERMINISM",
    "direct": "BLOCKED_BY_REPLICA_V3_INSUFFICIENT_DIRECT_ASSET_COVERAGE_POOL",
    "habitat": "BLOCKED_BY_REPLICA_V3_INSUFFICIENT_HABITAT_QUALIFIED_LOCATION_POOL",
    "contradiction": "BLOCKED_BY_REPLICA_V3_INDEPENDENT_HABITAT_COVERAGE_CONTRADICTION",
    "spatial": "BLOCKED_BY_REPLICA_V3_SPATIAL_DIVERSITY_GATE",
    "repeat": "BLOCKED_BY_REPLICA_V3_FROZEN_MANIFEST_REPEATABILITY_FAILURE",
    "pass": "PASS_REPLICA_RENDER_PROTOCOL_V3_PRE_RENDER_COVERAGE_QUALIFICATION",
}


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def position_text(point: Sequence[float]) -> List[str]:
    return [f"{float(component):.6f}" for component in point]


def location_hash(point: Sequence[float]) -> str:
    return sha256_text("REPLICA_V3_LOCATION:" + "".join(position_text(point)))


def base_yaw(location_digest: str) -> float:
    digest = hashlib.sha256(("REPLICA_V3_BASE_YAW:" + location_digest).encode("utf-8")).digest()
    return 360.0 * int.from_bytes(digest[:8], "big", signed=False) / float(2 ** 64)


def normalize_yaw(value: float) -> float:
    return float(value % 360.0)


def normalize(vector: Sequence[float]) -> np.ndarray:
    result = np.asarray(vector, dtype=np.float64)
    magnitude = float(np.linalg.norm(result))
    if not math.isfinite(magnitude) or magnitude <= 1e-12:
        raise ValueError("nonfinite_or_zero_vector")
    return result / magnitude


def c2w_from_yaw(camera_position: Sequence[float], yaw_degrees: float) -> np.ndarray:
    angle = math.radians(float(yaw_degrees))
    forward = normalize((-math.sin(angle), 0.0, -math.cos(angle)))
    up = np.asarray((0.0, 1.0, 0.0), dtype=np.float64)
    right = normalize(np.cross(forward, up))
    camera_up = normalize(np.cross(right, forward))
    rotation = np.column_stack((right, camera_up, -forward))
    if not np.isfinite(rotation).all() or abs(float(np.linalg.det(rotation)) - 1.0) > 1e-9:
        raise ValueError("invalid_v1_convention_rotation")
    matrix = np.eye(4, dtype=np.float64)
    matrix[:3, :3] = rotation
    matrix[:3, 3] = np.asarray(camera_position, dtype=np.float64)
    return matrix


def quaternion_xyzw(rotation: np.ndarray) -> List[float]:
    m = np.asarray(rotation, dtype=np.float64)
    trace = float(np.trace(m))
    if trace > 0.0:
        scale = math.sqrt(trace + 1.0) * 2.0
        w, x, y, z = 0.25 * scale, (m[2, 1] - m[1, 2]) / scale, (m[0, 2] - m[2, 0]) / scale, (m[1, 0] - m[0, 1]) / scale
    else:
        index = int(np.argmax(np.diag(m)))
        if index == 0:
            scale = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2.0
            w, x, y, z = (m[2, 1] - m[1, 2]) / scale, 0.25 * scale, (m[0, 1] + m[1, 0]) / scale, (m[0, 2] + m[2, 0]) / scale
        elif index == 1:
            scale = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2.0
            w, x, y, z = (m[0, 2] - m[2, 0]) / scale, (m[0, 1] + m[1, 0]) / scale, 0.25 * scale, (m[1, 2] + m[2, 1]) / scale
        else:
            scale = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2.0
            w, x, y, z = (m[1, 0] - m[0, 1]) / scale, (m[0, 2] + m[2, 0]) / scale, (m[1, 2] + m[2, 1]) / scale, 0.25 * scale
    return [float(x), float(y), float(z), float(w)]


def tree_hash(root: Path) -> str:
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rows.append(f"{path.relative_to(root).as_posix()}\0{sha256_path(path)}\0{path.stat().st_size}")
    return sha256_text("\n".join(rows))


def ensure_server_root() -> None:
    for name in ("input_identity", "protocol_freeze", "raw_navmesh_candidates", "candidate_locations", "candidate_poses", "independent_coverage", "habitat_preprobe", "qualified_location_pool", "final_location_selection", "final_manifest", "repeatability_probe", "figures", "report", "logs", "tmp"):
        (ROOT / name).mkdir(parents=True, exist_ok=True)
