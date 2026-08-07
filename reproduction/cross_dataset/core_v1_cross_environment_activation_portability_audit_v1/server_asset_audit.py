"""Read-only inventory and bounds audit for the seven frozen environments."""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path


ROOT = Path("/disk1/zlab/maintenance_records/core_v1_cross_environment_activation_portability_audit_v1")
TUM_GT = Path("/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/build/dataset_adapters_v2/train_240/rgbd_dataset_freiburg1_room/groundtruth.txt")
ASSETS = {
    "E1_REPLICA_GT_FINE_map": Path("/disk1/zlab/cross_dataset_assets/qualified_replica_gaussian_safety_maps_v1/bounded_direct_goal_v1/means_world_m.npy"),
    "E1_REPLICA_GT_FINE_registry": Path("/disk1/zlab/maintenance_records/resume_replica_gt_executable_safety_activated_benchmark_v1/registry/representative_holdout_registry_v1.json"),
    "E2_ETH3D_LEARNED_GAUSSIAN_map": Path("/disk1/zlab/cross_dataset_maps/eth3d_delivery_area_official_3dgs_v1/point_cloud/iteration_30000/point_cloud.ply"),
    "E2_ETH3D_route_failure": Path("/disk1/zlab/maintenance_records/eth3d_delivery_area_provision_7zz_resume_assets_v1/routes/reference_route_contract_failure.json"),
    "E3_TUM_SPLATAM_map": Path("/disk1/zlab/external_baselines/tum_rgbd_gaussian_v1/build/runs/splatam_full240/params.npz"),
    "E4_TUM_GAUSSIAN_SLAM_map": Path("/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/gaussian_slam/canonical_export/geometry_concat/means_world_m.npy"),
    "E5_STONEHENGE_SAFER_config": Path("/disk1/zlab/projects/safer-splat/outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml"),
    "E5_STONEHENGE_SAFER_checkpoint": Path("/disk1/zlab/projects/safer-splat/outputs/stonehenge/splatfacto/2024-09-11_100724/nerfstudio_models/step-000029999.ckpt"),
    "E5_STONEHENGE_SAFER_trials": Path("/disk1/zlab/projects/safer-splat/reproduction/results/official_checkpoint_filter_comparison_stonehenge_100/trials.csv"),
    "E6_FLIGHT_SAFER_config": Path("/disk1/zlab/projects/safer-splat/outputs/flight/splatfacto/2024-09-12_172434/config.yml"),
    "E6_FLIGHT_SAFER_checkpoint": Path("/disk1/zlab/projects/safer-splat/outputs/flight/splatfacto/2024-09-12_172434/nerfstudio_models/step-000029999.ckpt"),
    "E6_FLIGHT_SAFER_trials": Path("/disk1/zlab/projects/safer-splat/work/risk_aware_cbf/results/risk_aware_v1_pre_cbf_flight_100_bestD/per_step_trajectory.csv"),
    "E7_TUM_SPLATFACTO_negative_evidence": Path("/disk1/zlab/maintenance_records/retrospective_requalify_existing_gaussian_maps_protocol_v2/classification/per_map_evidence_cards/TUM_SPLATFACTO_NEGATIVE.json"),
    "official_trial_generator": Path("/disk1/zlab/projects/safer-splat/reproduction/scripts/run_official_checkpoint_filter_comparison.py"),
    "official_query_source": Path("/disk1/zlab/projects/safer-splat/splat/gsplat_utils.py"),
    "official_cbf_source": Path("/disk1/zlab/projects/safer-splat/cbf/cbf_utils.py"),
}


def sha256(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def tum_velocity_audit() -> dict:
    if not TUM_GT.is_file():
        return {"status": "NOT_EVALUABLE", "reason": "groundtruth missing", "candidate_count": 0}
    poses = []
    for line in TUM_GT.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        values = [float(value) for value in line.split()]
        poses.append((values[0], values[1:4]))
    candidates = []
    maxima = []
    for index, (timestamp, position) in enumerate(poses):
        if index == 0 or index + 1 == len(poses):
            continue
        previous_t, previous_p = poses[index - 1]
        next_t, next_p = poses[index + 1]
        dt = next_t - previous_t
        velocity = [(next_p[axis] - previous_p[axis]) / dt for axis in range(3)]
        component_max = max(abs(value) for value in velocity)
        maxima.append(component_max)
        if all(math.isfinite(value) and abs(value) <= 0.1 for value in velocity):
            candidates.append({"pose_index": index, "timestamp": timestamp, "position_m": position, "velocity_m_per_s": velocity})
    maxima.sort()
    def quantile(fraction: float) -> float | None:
        if not maxima:
            return None
        return maxima[round(fraction * (len(maxima) - 1))]
    return {
        "status": "ENVIRONMENT_STRUCTURAL_SHORTFALL", "source_path": str(TUM_GT),
        "source_sha256": sha256(TUM_GT), "pose_count": len(poses),
        "central_difference_candidate_count": len(maxima), "bounds_valid_candidate_count": len(candidates),
        "velocity_component_max_quantiles": {"min": quantile(0), "q25": quantile(.25), "median": quantile(.5), "q75": quantile(.75), "max": quantile(1)},
        "bounds_valid_candidates": candidates,
        "clipping_applied": False, "velocity_bound_inf_m_per_s": 0.1,
    }


def command_text(command: list[str]) -> str:
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    return result.stdout.strip()


def main() -> None:
    ROOT.joinpath("audits").mkdir(parents=True, exist_ok=True)
    inventory = {}
    for label, path in ASSETS.items():
        inventory[label] = {"path": str(path), "exists": path.is_file(), "size": path.stat().st_size if path.is_file() else None, "sha256": sha256(path)}
    payload = {
        "host": command_text(["hostname"]), "user": command_text(["whoami"]),
        "assets": inventory, "tum_velocity_audit": tum_velocity_audit(),
        "gpu_1": command_text(["nvidia-smi", "-i", "1", "--query-gpu=index,name,memory.used,utilization.gpu", "--format=csv,noheader"]),
        "gpu_1_compute_processes": command_text(["nvidia-smi", "-i", "1", "--query-compute-apps=pid,process_name,used_gpu_memory", "--format=csv,noheader"]),
        "project_head": command_text(["git", "-C", "/disk1/zlab/projects/safer-splat", "rev-parse", "HEAD"]),
        "project_status": command_text(["git", "-C", "/disk1/zlab/projects/safer-splat", "status", "--short", "--branch"]),
        "map_training_count": 0, "map_mutation_count": 0, "controller_mutation_count": 0,
    }
    data = (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    ROOT.joinpath("audits/environment_asset_inventory.json").write_bytes(data)
    print("PASS_READ_ONLY_ENVIRONMENT_ASSET_INVENTORY", len(inventory))


if __name__ == "__main__":
    main()
