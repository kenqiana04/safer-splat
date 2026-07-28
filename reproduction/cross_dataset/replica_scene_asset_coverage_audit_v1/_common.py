"""Shared helpers and fixed identities for Replica Scene Asset Coverage Audit V1."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

SCENE_ROOT = Path("/disk1/zlab/cross_dataset_assets/raw/replica/replica_v1/apartment_0")
MANIFEST = Path("/disk1/zlab/cross_dataset_assets/manifests/replica_protocol_v1/formal_camera_manifest.csv")
V1_ROOT = Path("/disk1/zlab/cross_dataset_assets/processed/replica/apartment_0.rendering")
V2_ROOT = Path("/disk1/zlab/maintenance_records/replica_rgbd_integrity_root_cause_repair_v2")
ROOT = Path("/disk1/zlab/maintenance_records/replica_scene_asset_coverage_audit_v1")
PYTHON = Path("/disk1/zlab/conda_envs/replica_habitat_renderer_py39/bin/python")
FROZEN = {
    "mesh_sha256": "274677d9b7caa413230363b68f4aa472e5cc1afe87e422a489fa1b7d844c6182",
    "navmesh_sha256": "32296d6457d3855ffe172cf1970364559def5dd15892e149b44d0bc7c6b7e938",
    "manifest_sha256": "1056121e4470124e180a3367172440f540f0acdc5adab665c3187ac8ab87be25",
    "v1_staging_tree_sha256": "39367c04f6e6ea510590f77ee1275e78333123608e6eb2223c1d419260288c51",
    "probe_registry_sha256": "d7079c5c8ea7a7d775d3015f6e6046df593af9dee8001c88932361f9a64a639b",
    "paired20_manifest_sha256": "380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def atomic_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def diagnostic_marker() -> str:
    return "DIAGNOSTIC_ONLY_NOT_A_FORMAL_REPLICA_ASSET"
