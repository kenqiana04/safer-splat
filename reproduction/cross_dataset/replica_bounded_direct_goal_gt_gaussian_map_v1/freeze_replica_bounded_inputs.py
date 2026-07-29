#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED = {
    "complete_tree_sha256": "24e21d3bccceb0516ed8b9b49b426964f3954ccd0cd804eedd5846baabd66dcb",
    "content_tree_sha256": "60a9e0b517ba8e305c4b7ff010bb330c1e38c422c66899398129cce741a06bd0",
    "contract_sha256": "ddd147f908537165c40a34b412cd21c3cbfb5a0615871375d02adecbbfaec6f7",
    "selected_registry_sha256": "84edb118f01fe1460ff64be4b6ef838f23ed4520740af9f457041b438a7b9f5a",
    "manifest_csv_sha256": "6db89bc0dafaa5993b452216be1205ec9db0a1d9da23b9bc2b9029fabc2113d6",
    "transforms_sha256": "ec50b63a1263d9f6e355a6d5010ab79738d92d59f8bec481150d86f3145d888f",
    "pose_array_sha256": "0bc952fec3236d117b33d0d62085a60412b96e2174ab0a31c7c5fec204789622",
    "mesh_sha256": "274677d9b7caa413230363b68f4aa472e5cc1afe87e422a489fa1b7d844c6182",
    "navmesh_sha256": "32296d6457d3855ffe172cf1970364559def5dd15892e149b44d0bc7c6b7e938",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--v3", type=Path, required=True)
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--navmesh", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    publication = json.loads((args.v3 / "publication_identity.json").read_text(encoding="utf-8"))
    split = json.loads((args.v3 / "replica_v3_location_split.json").read_text(encoding="utf-8"))
    selected = json.loads((args.v3 / "selected_v3_location_registry.json").read_text(encoding="utf-8"))
    observed = {
        "complete_tree_sha256": json.loads(Path("/disk1/zlab/maintenance_records/replica_splatam_protocol_conformance_pilot_v1/input_identity_summary.json").read_text())["complete_tree_sha256"],
        "content_tree_sha256": publication["published_content_tree_sha256"],
        "contract_sha256": sha256(args.v3 / "REPLICA_RENDER_PROTOCOL_V3_CONTRACT.json"),
        "selected_registry_sha256": sha256(args.v3 / "selected_v3_location_registry.json"),
        "manifest_csv_sha256": sha256(args.v3 / "formal_camera_manifest_v3.csv"),
        "transforms_sha256": sha256(args.v3 / "transforms_v3.json"),
        "pose_array_sha256": publication["pose_array_sha256"],
        "mesh_sha256": sha256(args.mesh),
        "navmesh_sha256": sha256(args.navmesh),
    }
    if observed != EXPECTED:
        raise SystemExit("BLOCKED_BY_REPLICA_BOUNDED_BENCHMARK_INPUT_IDENTITY")
    locations = []
    for item in selected["selected_locations"]:
        base = item["source_navmesh_position"]
        locations.append({"id": item["location_hash"], "camera_center_m": [base[0], base[1] + 1.5, base[2]]})
    if len(locations) != 100 or len({x["id"] for x in locations}) != 100:
        raise SystemExit("BLOCKED_BY_REPLICA_BOUNDED_BENCHMARK_INPUT_IDENTITY")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    identity = {
        "status": "PASS", "scene": "apartment_0", "v3_root": str(args.v3), "official_mesh": str(args.mesh),
        "official_navmesh": str(args.navmesh), "identities": observed, "camera_center_count": 100,
        "coordinate_system": "Habitat metric Y-up; V3 camera centers are source navmesh positions plus frozen 1.5 m camera height",
        "camera_transform": "nerfstudio_opengl_c2w", "normalization_used": False, "automatic_scale_used": False,
        "navmesh_controller_path_count": 0, "camera_centers": locations,
    }
    contract = {
        "authority_type": "EXPLICIT_USER_AUTHORIZED_BENCHMARK_DESIGN", "design_choice": "NEW_VERSIONED_REPLICA_BENCHMARK_DESIGN_CHOICE",
        "not_recovered_official_safer_contract": True, "not_physical_robot_platform": True,
        "state": ["px", "py", "pz", "vx", "vy", "vz"], "control": ["ax", "ay", "az"], "environment": "metric_free_3D",
        "robot": {"shape": "sphere_benchmark_primitive", "r_robot_m": 0.10, "epsilon_base_m": 0.01},
        "dt_s": 0.05, "integration": "forward_euler", "position_update": "p_next=p+dt*v", "velocity_update": "v_next=v+dt*u",
        "vmax_component_m_per_s": 0.10, "umax_component_m_per_s2": 0.10, "initial_velocity_m_per_s": [0,0,0], "goal_velocity_m_per_s": [0,0,0],
        "nominal_controller": "vel_des=clip_componentwise(5*(p_goal-p),-vmax,+vmax); u_des=clip_componentwise(vel_des-v,-umax,+umax)",
        "max_steps": 500, "max_simulation_time_s": 25.0, "success_position_tolerance_m": 0.03, "success_velocity_tolerance_m_per_s": 0.03,
    }
    (args.output_dir / "replica_bounded_input_identity.json").write_text(json.dumps(identity, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (args.output_dir / "replica_bounded_robot_contract.json").write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("INPUT_AND_CONTRACT_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
