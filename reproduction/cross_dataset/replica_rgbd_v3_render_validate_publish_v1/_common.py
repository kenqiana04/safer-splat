"""Immutable paths and helpers for formal Replica RGB-D V3 rendering."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

ROOT = Path("/disk1/zlab/maintenance_records/replica_rgbd_v3_render_validate_publish_v1")
SCENE_ROOT = Path("/disk1/zlab/cross_dataset_assets/raw/replica/replica_v1/apartment_0")
MESH = SCENE_ROOT / "mesh.ply"
NAVMESH = SCENE_ROOT / "habitat" / "mesh_semantic.navmesh"
PUBLISHED = Path("/disk1/zlab/cross_dataset_assets/processed/replica/apartment_0.rendering_v3")
PUBLISH_TMP = Path("/disk1/zlab/cross_dataset_assets/processed/replica/.apartment_0.rendering_v3.publish_tmp")
PYTHON = Path("/disk1/zlab/conda_envs/replica_habitat_renderer_py39/bin/python")
EXPECTED = {
    "pr54_head": "1b8fabb504235774885e40e28bd2ea83032a1bb8",
    "contract_sha256": "ddd147f908537165c40a34b412cd21c3cbfb5a0615871375d02adecbbfaec6f7",
    "manifest_csv_sha256": "6db89bc0dafaa5993b452216be1205ec9db0a1d9da23b9bc2b9029fabc2113d6",
    "manifest_json_sha256": "f029de724f33a2788c1f6570b5d730ec06f3223a2d512c38a0427ca9c1d14b2b",
    "transforms_sha256": "ec50b63a1263d9f6e355a6d5010ab79738d92d59f8bec481150d86f3145d888f",
    "pose_array_sha256": "0bc952fec3236d117b33d0d62085a60412b96e2174ab0a31c7c5fec204789622",
    "registry_sha256": "84edb118f01fe1460ff64be4b6ef838f23ed4520740af9f457041b438a7b9f5a",
    "mesh_sha256": "274677d9b7caa413230363b68f4aa472e5cc1afe87e422a489fa1b7d844c6182",
    "navmesh_sha256": "32296d6457d3855ffe172cf1970364559def5dd15892e149b44d0bc7c6b7e938",
    "paired20_sha256": "380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6",
    "historical_commit": "fe250df543aa158557c176ee4f87dc131bb61e60",
    "historical_renderer_blob": "8d59eb5b0d7434be76c8b385c97ee0d7e5dcfaa4",
    "historical_integrity_blob": "cae67b3be07c1b801dc7af51ebc0ffcc6bbe6efb",
}


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with temporary.open("rb") as handle:
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def fsync_directory(path: Path) -> None:
    descriptor = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def tree_rows(root: Path, exclude: Iterable[str] = ()) -> list[str]:
    excluded = set(exclude)
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        rows.append(relative + "\0" + str(path.stat().st_size) + "\0" + sha256_path(path))
    return rows


def tree_sha(root: Path, exclude: Iterable[str] = ()) -> str:
    return hashlib.sha256("\n".join(tree_rows(root, exclude)).encode("utf-8")).hexdigest()


def ensure_root() -> None:
    for name in ("input_identity", "renderer_contract", "formal_staging", "render_manifests", "per_location_status", "per_frame_integrity", "full_integrity", "tree_identity", "publication", "figures", "report", "logs", "tmp", "code"):
        (ROOT / name).mkdir(parents=True, exist_ok=True)
