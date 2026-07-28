#!/usr/bin/env python3
"""Write V3's immutable contract before any candidate-generation call."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone

from _v3_common import ROOT, atomic_json, ensure_server_root, sha256_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-identity", required=True)
    args = parser.parse_args()
    ensure_server_root()
    if not (ROOT / "input_identity" / "upstream_replica_v3_identity.json").exists():
        raise SystemExit("missing_input_identity")
    contract = {
        "protocol": "NEW_PREQUALIFIED_REPLICA_RENDER_PROTOCOL_V3",
        "scene": "apartment_0",
        "formal_render_asset": "mesh.ply",
        "candidate_seed": 20260728,
        "raw_navmesh_sample_count": 2048,
        "maximum_unique_candidate_locations": 1024,
        "camera_height_m": 1.50,
        "yaw_offsets_deg": [0, -60, 60],
        "frame_order_per_location": [0, -60, 60],
        "target_location_count": 100,
        "target_frame_count": 300,
        "train_location_count": 90,
        "eval_location_count": 10,
        "train_frame_count": 270,
        "eval_frame_count": 30,
        "independent_raycast_grid": [41, 31],
        "ray_count_per_view": 1271,
        "independent_valid_hit_fraction_threshold": 0.10,
        "habitat_depth_positive_fraction_threshold": 0.10,
        "habitat_rgb_nonzero_fraction_threshold": 0.05,
        "v1_compatibility_rgb_floor": 0.01,
        "minimum_actual_qualified_location_pool": 120,
        "maximum_habitat_preprobe_locations": 320,
        "repeatability_probe_frame_count": 30,
        "location_deduplication_radius_m": 0.05,
        "final_minimum_location_separation_m": 0.10,
        "spatial_grid_cell_size_m": 0.50,
        "location_hash_round_decimals": 6,
        "base_yaw_digest_prefix_bytes": 8,
        "camera_convention": "V1_verified_habitat_y_up_nerfstudio_opengl_c2w",
        "input_identity_sha256": sha256_path(__import__("pathlib").Path(args.input_identity)),
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "formal_render_count": 0,
        "publication_count": 0,
        "training_count": 0,
        "safer_count": 0,
        "tum_rollout_count": 0,
    }
    path = ROOT / "protocol_freeze" / "REPLICA_RENDER_PROTOCOL_V3_CONTRACT.json"
    if path.exists():
        raise SystemExit("contract_already_exists_refuse_mutation")
    atomic_json(path, contract)
    atomic_json(ROOT / "protocol_freeze" / "contract_identity.json", {"contract_sha256": sha256_path(path), "contract_path": str(path)})


if __name__ == "__main__":
    main()
