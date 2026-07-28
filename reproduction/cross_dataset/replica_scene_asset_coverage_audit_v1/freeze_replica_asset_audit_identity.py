#!/usr/bin/env python3
"""Record and verify upstream V2 identities; never mutates frozen sources."""
from __future__ import annotations
import csv
import hashlib
from pathlib import Path
from _common import FROZEN, MANIFEST, ROOT, SCENE_ROOT, V1_ROOT, V2_ROOT, atomic_json, sha256


def tree_hash(root: Path) -> str:
    records = []
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        records.append((str(p.relative_to(root)).replace("\\", "/"), sha256(p), p.stat().st_size))
    payload = "\n".join(f"{rel}\0{digest}\0{size}" for rel, digest, size in records).encode()
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    registry = V2_ROOT / "anomaly_registry/diagnostic_probe_registry.json"
    found = {"mesh": sha256(SCENE_ROOT / "mesh.ply"), "navmesh": sha256(SCENE_ROOT / "habitat/mesh_semantic.navmesh"), "manifest": sha256(MANIFEST), "v1_staging_tree": tree_hash(V1_ROOT), "probe_registry": sha256(registry)}
    for name, value in found.items():
        if value != FROZEN[name + "_sha256"]:
            raise SystemExit("frozen_identity_mismatch:" + name)
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8")))
    if len(rows) != 300 or [r["frame_id"] for r in rows] != [f"frame_{i:04d}" for i in range(300)]:
        raise SystemExit("frozen_manifest_contract_mismatch")
    textures = sorted((SCENE_ROOT / "textures").iterdir())
    atomic_json(ROOT / "input_identity/upstream_replica_asset_audit_identity.json", {
        "status": "PASS_FROZEN_UPSTREAM_IDENTITY", "upstream_pr": 52,
        "upstream_head": "44bd09e4236104aa97d9f075f120d4a4962dab17", "historical_source_commit": "fe250df543aa158557c176ee4f87dc131bb61e60", "scene": "apartment_0", "checks": found,
        "texture_files": [{"path": str(p), "size": p.stat().st_size, "sha256": sha256(p)} for p in textures],
        "camera_contract": {"rows": 300, "locations": 100, "yaw_order_deg": [0, -60, 60], "resolution": [640, 480], "hfov_deg": 90.0, "near_m": 0.05, "far_m": 20.0, "height_m": 1.5},
        "v1_bad_counts": {"rgb": 33, "depth": 32, "joint": 32, "rgb_only": ["frame_0034"], "depth_only": []},
        "task_boundary": {"formal_rerender_count": 0, "publication_count": 0, "gaussian_training_count": 0, "safer_execution_count": 0, "tum_rollout_count": 0},
    })

if __name__ == "__main__": main()
