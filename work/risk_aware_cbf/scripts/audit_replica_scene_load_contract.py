#!/usr/bin/env python3
"""Audit an official Replica scene and optionally run one headless smoke frame."""
import argparse
import csv
import json
import math
from pathlib import Path


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else ["check", "passed", "detail"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def finite_point(point):
    return all(math.isfinite(float(value)) for value in point)


def run_smoke(mesh, navmesh, gpu_device):
    import habitat_sim

    sim_cfg = habitat_sim.SimulatorConfiguration()
    sim_cfg.scene_id = str(mesh)
    sim_cfg.enable_physics = False
    sim_cfg.gpu_device_id = gpu_device

    agent_cfg = habitat_sim.agent.AgentConfiguration()
    specs = []
    for uuid, sensor_type in (
        ("rgba", habitat_sim.SensorType.COLOR),
        ("depth", habitat_sim.SensorType.DEPTH),
    ):
        spec = habitat_sim.CameraSensorSpec()
        spec.uuid = uuid
        spec.sensor_type = sensor_type
        spec.sensor_subtype = habitat_sim.SensorSubType.PINHOLE
        spec.resolution = [480, 640]
        spec.position = [0.0, 1.5, 0.0]
        specs.append(spec)
    agent_cfg.sensor_specifications = specs

    simulator = habitat_sim.Simulator(habitat_sim.Configuration(sim_cfg, [agent_cfg]))
    try:
        navmesh_loaded = bool(simulator.pathfinder.load_nav_mesh(str(navmesh)))
        point = simulator.pathfinder.get_random_navigable_point() if navmesh_loaded else []
        point_is_finite = bool(point) and finite_point(point)
        if point_is_finite:
            agent = simulator.initialize_agent(0)
            state = agent.get_state()
            state.position = point
            agent.set_state(state)
        observations = simulator.get_sensor_observations()
        rgba = observations.get("rgba")
        depth = observations.get("depth")
        rgba_ok = rgba is not None and tuple(rgba.shape) == (480, 640, 4)
        depth_ok = depth is not None and tuple(depth.shape) == (480, 640)
        depth_finite = bool(depth_ok and bool((~__import__("numpy").isfinite(depth)).sum() == 0))
        return {
            "habitat_import": True,
            "simulator_created": True,
            "navmesh_loaded": navmesh_loaded,
            "navigable_point_finite": point_is_finite,
            "rgba_shape": list(rgba.shape) if rgba is not None else None,
            "depth_shape": list(depth.shape) if depth is not None else None,
            "rgba_ok": rgba_ok,
            "depth_ok": depth_ok,
            "depth_finite": depth_finite,
        }
    finally:
        simulator.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--scene-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--gpu-device", type=int, default=1)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    scene = args.scene_dir.resolve()
    mesh = scene / "mesh.ply"
    textures = scene / "textures"
    navmesh = scene / "habitat" / "mesh_semantic.navmesh"
    configs = sorted(scene.rglob("*.stage_config.json")) + sorted(scene.rglob("*.scene_dataset_config.json"))
    texture_count = len(list(textures.glob("*"))) if textures.is_dir() else 0
    contract = {
        "scene_name": scene.name,
        "selection_rule": "complete eligible scene names; alphabetical ascending; first scene",
        "primary_mesh": str(mesh),
        "official_scene_config": ";".join(map(str, configs)),
        "scene_source_priority": "priority_3_official_textured_mesh",
        "texture_path": str(textures),
        "texture_file_count": texture_count,
        "navmesh": str(navmesh),
        "mesh_exists": mesh.is_file(),
        "textures_exist": textures.is_dir() and texture_count > 0,
        "navmesh_exists": navmesh.is_file(),
        "manual_config_generated": False,
        "scene_units_modified": False,
    }
    contract["contract_ready_for_smoke"] = all(
        contract[key] for key in ("mesh_exists", "textures_exist", "navmesh_exists")
    )
    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "scene_load_contract.csv", [contract])

    smoke = {"smoke_requested": args.smoke, "smoke_passed": False, "reason": "not_requested"}
    if args.smoke:
        if not contract["contract_ready_for_smoke"]:
            smoke["reason"] = "scene_contract_incomplete"
        else:
            try:
                smoke.update(run_smoke(mesh, navmesh, args.gpu_device))
                smoke["smoke_passed"] = all(
                    smoke.get(key, False)
                    for key in ("habitat_import", "simulator_created", "navmesh_loaded", "navigable_point_finite", "rgba_ok", "depth_ok", "depth_finite")
                )
                smoke["reason"] = "passed" if smoke["smoke_passed"] else "renderer_contract_failed"
            except Exception as exc:  # Record the exact stage without guessing a fallback.
                smoke["reason"] = "exception"
                smoke["exception_type"] = type(exc).__name__
                smoke["exception_message"] = str(exc)
    write_csv(args.out / "renderer_smoke.csv", [smoke])
    write_csv(args.out / "navmesh_contract.csv", [{
        "navmesh": str(navmesh),
        "navmesh_exists": navmesh.is_file(),
        "navmesh_loaded": smoke.get("navmesh_loaded"),
        "navigable_point_finite": smoke.get("navigable_point_finite"),
    }])
    (args.out / "scene_audit.json").write_text(json.dumps({"contract": contract, "smoke": smoke}, indent=2) + "\n", encoding="utf-8")
    print("scene_contract_ready=" + str(contract["contract_ready_for_smoke"]).lower())
    print("renderer_smoke_passed=" + str(smoke["smoke_passed"]).lower())


if __name__ == "__main__":
    main()
