"""Task-owned GT-pose adapters and serial launchers; frontend source trees remain read-only."""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import time
from pathlib import Path

import numpy as np

from _common import DATASET, FRONTENDS, ROOT, atomic_json, ensure_dirs, load_json, task_env, update_stage


P = np.diag([1.0, -1.0, -1.0, 1.0])


def sample_gpu() -> int | None:
    result = subprocess.run(["nvidia-smi", "-i", "1", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=False)
    try: return int(result.stdout.strip().splitlines()[0])
    except (ValueError, IndexError): return None


def run_logged(command: list[str], cwd: Path, log: Path, cap: int) -> dict:
    log.parent.mkdir(parents=True, exist_ok=True); before = sample_gpu(); samples: list[int] = []; started = time.time()
    with log.open("w", encoding="utf-8") as handle:
        process = subprocess.Popen(command, cwd=cwd, env=task_env(), stdout=handle, stderr=subprocess.STDOUT, start_new_session=True)
        timed_out = False
        while process.poll() is None:
            value = sample_gpu()
            if value is not None: samples.append(value)
            if time.time() - started > cap:
                timed_out = True; os.killpg(process.pid, signal.SIGTERM)
                try: process.wait(timeout=30)
                except subprocess.TimeoutExpired: os.killpg(process.pid, signal.SIGKILL); process.wait()
                break
            time.sleep(5)
        code = process.wait() if process.poll() is None else process.returncode
    return {"returncode": code, "timeout": timed_out, "wall_seconds": time.time() - started, "gpu_memory_before_mib": before, "gpu_memory_peak_mib": max(samples) if samples else before, "gpu_memory_mean_mib": float(np.mean(samples)) if samples else before, "command": command, "log": str(log)}


def frame_rows(frame_ids: list[str]) -> list[dict]:
    rows = {row["frame_id"]: row for row in load_json(DATASET / "formal_camera_manifest_v3.json")["frames"]}
    return [rows[frame] for frame in frame_ids]


def c2w_cv(row: dict) -> np.ndarray:
    return np.asarray(row["camera_to_world"], dtype=np.float64) @ P


def link(source: Path, target: Path) -> None:
    if target.exists() or target.is_symlink(): raise RuntimeError(f"ADAPTER_PATH_ALREADY_EXISTS:{target}")
    target.parent.mkdir(parents=True, exist_ok=True); target.symlink_to(source)


def write_splatam_adapter(stage: str, rows: list[dict]) -> tuple[Path, Path]:
    base = ROOT / "splatam" / "dataset_adapters" / stage / "pilot" / "imap" / "00"; rgb = base / "rgb"; depth = base / "depth"; rgb.mkdir(parents=True, exist_ok=False); depth.mkdir(parents=True, exist_ok=False)
    pose_lines = []
    for index, row in enumerate(rows):
        link(DATASET / "images" / f"{row['frame_id']}.png", rgb / f"rgb_{index}.png"); link(DATASET / "depth" / f"{row['frame_id']}.png", depth / f"depth_{index}.png")
        pose_lines.append(" ".join(f"{value:.17g}" for value in c2w_cv(row).reshape(-1)))
    (base / "traj_w_c.txt").write_text("\n".join(pose_lines) + "\n", encoding="utf-8")
    yaml = ROOT / "splatam" / "dataset_adapters" / f"{stage}_adapter.yaml"; yaml.write_text("dataset_name: replicav2\ncamera_params:\n  image_height: 480\n  image_width: 640\n  fx: " + str(load_json(ROOT / "input_contract" / "replica_mapping_input_contract.json")["fx"]) + "\n  fy: " + str(load_json(ROOT / "input_contract" / "replica_mapping_input_contract.json")["fy"]) + "\n  cx: " + str(load_json(ROOT / "input_contract" / "replica_mapping_input_contract.json")["cx"]) + "\n  cy: " + str(load_json(ROOT / "input_contract" / "replica_mapping_input_contract.json")["cy"]) + "\n  png_depth_scale: 1000.0\n", encoding="utf-8")
    return base.parents[2], yaml


def write_splatam_config(stage: str, count: int, basedir: Path, dataset_yaml: Path, output: Path) -> Path:
    config = ROOT / "splatam" / "configs" / f"{stage}.py"; config.parent.mkdir(parents=True, exist_ok=True)
    text = "config = " + repr({"workdir": str(output.parent), "run_name": output.name, "seed": 0, "primary_device": "cuda:0", "report_global_progress_every": 500, "eval_every": 500, "scene_radius_depth_ratio": 3, "mean_sq_dist_method": "projective", "gaussian_distribution": "isotropic", "report_iter_progress": False, "load_checkpoint": False, "checkpoint_time_idx": 0, "save_checkpoints": False, "checkpoint_interval": 5, "use_wandb": False, "wandb": {"entity": "", "project": "", "group": "", "name": "", "save_qual": False, "eval_save_qual": False}, "data": {"basedir": str(basedir), "gradslam_data_cfg": str(dataset_yaml), "sequence": "pilot", "desired_image_height_init": 480, "desired_image_width_init": 640, "desired_image_height": 480, "desired_image_width": 640, "start": 0, "end": -1, "stride": 1, "num_frames": count, "eval_stride": 1, "eval_num_frames": count}, "train": {"num_iters_mapping": 30000, "sil_thres": 0.5, "use_sil_for_loss": True, "loss_weights": {"im": 0.5, "depth": 1.0}, "lrs_mapping": {"means3D": 0.00032, "rgb_colors": 0.0025, "unnorm_rotations": 0.001, "logit_opacities": 0.05, "log_scales": 0.005, "cam_unnorm_rots": 0.0, "cam_trans": 0.0}, "lrs_mapping_means3D_final": 0.0000032, "lr_delay_mult": 0.01, "use_gaussian_splatting_densification": True, "densify_dict": {"start_after": 500, "remove_big_after": 3000, "stop_after": 15000, "densify_every": 100, "grad_thresh": 0.0002, "num_to_split_into": 2, "removal_opacity_threshold": 0.005, "final_removal_opacity_threshold": 0.005, "reset_opacities": True, "reset_opacities_every": 3000}}, "viz": {"render_mode": "color", "offset_first_viz_cam": True, "show_sil": False, "visualize_cams": False, "viz_w": 600, "viz_h": 340, "viz_near": 0.01, "viz_far": 100.0, "view_scale": 2, "viz_fps": 5, "enter_interactive_post_online": False}}) + "\n"; config.write_text(text, encoding="utf-8"); return config


def write_splatam_launcher(stage: str) -> Path:
    launcher = ROOT / "splatam" / "launchers" / f"{stage}.py"; launcher.parent.mkdir(parents=True, exist_ok=True)
    launcher.write_text("import runpy,sys\nfrom pathlib import Path\nrepo=Path(sys.argv[1]); cfg=sys.argv[2]\nsys.path.insert(0,str(repo))\nm=runpy.run_path(str(repo/'scripts'/'gaussian_splatting.py'),run_name='splatam_official')\nf=m['offline_splatting']; f.__globals__['eval']=lambda *args,**kwargs: None\nfrom importlib.machinery import SourceFileLoader\ne=SourceFileLoader('task_config',cfg).load_module()\nm['seed_everything'](seed=e.config['seed'])\nf(e.config)\n", encoding="utf-8")
    return launcher


def write_gaussian_adapter(stage: str, rows: list[dict]) -> Path:
    base = ROOT / "gaussian_slam" / "dataset_adapters" / stage; results = base / "results"; results.mkdir(parents=True, exist_ok=False); poses = []
    for index, row in enumerate(rows):
        link(DATASET / "images" / f"{row['frame_id']}.png", results / f"frame{index:06d}.jpg"); link(DATASET / "depth" / f"{row['frame_id']}.png", results / f"depth{index:06d}.png")
        poses.append(" ".join(f"{value:.17g}" for value in c2w_cv(row).reshape(-1)))
    (base / "traj.txt").write_text("\n".join(poses) + "\n", encoding="utf-8"); return base


def write_gaussian_config(stage: str, count: int, adapter: Path, output: Path) -> Path:
    camera = load_json(ROOT / "input_contract" / "replica_mapping_input_contract.json"); config = ROOT / "gaussian_slam" / "configs" / f"{stage}.yaml"; config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(f'''project_name: Gaussian_SLAM_replica_v3\ndataset_name: replica\ncheckpoint_path: null\nuse_wandb: false\nframe_limit: {count}\nseed: 0\nmapping:\n  new_submap_every: 50\n  map_every: 5\n  iterations: 100\n  new_submap_iterations: 1000\n  new_submap_points_num: 600000\n  new_submap_gradient_points_num: 50000\n  new_frame_sample_size: -1\n  new_points_radius: 0.0000001\n  current_view_opt_iterations: 0.4\n  alpha_thre: 0.6\n  pruning_thre: 0.1\n  submap_using_motion_heuristic: true\ntracking:\n  gt_camera: true\n  w_color_loss: 0.95\n  iterations: 60\n  cam_rot_lr: 0.0002\n  cam_trans_lr: 0.002\n  odometry_type: gt\n  help_camera_initialization: false\n  init_err_ratio: 5\n  odometer_method: point_to_plane\n  filter_alpha: false\n  filter_outlier_depth: true\n  alpha_thre: 0.98\n  soft_alpha: true\n  mask_invalid_depth: false\ncam:\n  H: {camera['height']}\n  W: {camera['width']}\n  fx: {camera['fx']}\n  fy: {camera['fy']}\n  cx: {camera['cx']}\n  cy: {camera['cy']}\n  depth_scale: 1000.0\ndata:\n  scene_name: apartment_0_v3_{stage}\n  input_path: {adapter}\n  output_path: {output}\n  frame_limit: {count}\n''', encoding="utf-8"); return config


def write_gaussian_launcher(stage: str) -> Path:
    launcher = ROOT / "gaussian_slam" / "launchers" / f"{stage}.py"; launcher.parent.mkdir(parents=True, exist_ok=True)
    launcher.write_text("import sys\nfrom pathlib import Path\nrepo=Path(sys.argv[1]);cfg=sys.argv[2]\nsys.path.insert(0,str(repo))\nfrom src.utils.io_utils import load_config,save_dict_to_ckpt\nfrom src.utils.utils import setup_seed\nfrom src.entities.gaussian_slam import GaussianSLAM\nc=load_config(cfg);setup_seed(c['seed']);g=GaussianSLAM(c)\ng.tracker.track=lambda frame_id, gaussian_model, estimated: g.dataset[frame_id][-1]\norig=g.mapper.map\ndef map_capture(frame_id,estimate_c2w,gaussian_model,is_new_submap):\n g._task_last_gaussian_model=gaussian_model\n return orig(frame_id,estimate_c2w,gaussian_model,is_new_submap)\ng.mapper.map=map_capture\ng.run()\nmodel=g._task_last_gaussian_model\nsave_dict_to_ckpt({'gaussian_params':model.capture_dict(),'submap_keyframes':sorted(g.keyframes_info)},'final_submap.ckpt',directory=g.output_path/'submaps')\n", encoding="utf-8")
    return launcher


def execute(frontend: str, stage: str) -> None:
    ensure_dirs(); contract = load_json(ROOT / "pilot_registry" / "frontend_pilot_configuration_contract.json"); order = load_json(ROOT / "pilot_registry" / "replica_frontend_map_only_order.json")
    ids = order["smoke_mapping_frame_ids"] if stage == "smoke" else order["mapping_frame_order"]; cap = contract["frontends"][frontend]["wall_clock_cap_seconds"][stage]; rows = frame_rows(ids); output = ROOT / frontend / stage / "run"
    if output.exists(): raise SystemExit(f"OUTPUT_MUST_BE_NEW:{output}")
    if frontend == "splatam":
        basedir, adapter = write_splatam_adapter(stage, rows); config = write_splatam_config(stage, len(rows), basedir, adapter, output); launcher = write_splatam_launcher(stage)
    else:
        basedir = write_gaussian_adapter(stage, rows); config = write_gaussian_config(stage, len(rows), basedir, output); launcher = write_gaussian_launcher(stage)
    log = ROOT / "logs" / f"{frontend}_{stage}.log"; info = run_logged([str(FRONTENDS[frontend]["python"]), str(launcher), str(FRONTENDS[frontend]["repo"]), str(config)], FRONTENDS[frontend]["repo"], log, cap)
    required = output / "params.npz" if frontend == "splatam" else output / "submaps" / "final_submap.ckpt"
    prefix = "SMOKE" if stage == "smoke" else "QUALIFICATION_PILOT"; status = f"{prefix}_RESOURCE_LIMIT_EXCEEDED" if info["timeout"] else f"{prefix}_CHECKPOINT_FAILURE" if info["returncode"] == 0 and not required.is_file() else f"{prefix}_ALGORITHM_FAILURE" if info["returncode"] else f"{prefix}_MAP_COMPLETE_PENDING_SHARED_EVALUATION"
    summary = {"frontend": FRONTENDS[frontend]["display"], "stage": stage, "status": status, "mapping_frame_count": len(rows), "frame_ids": ids, "gt_pose": True, "tracking_count": 0, "pose_update_count": 0, "scale_fitting": False, "sim3": False, "checkpoint": str(required), "checkpoint_exists": required.is_file(), "runtime": info, "infrastructure_events": []}
    path = ROOT / frontend / f"{stage}_summary.json"; atomic_json(path, summary); update_stage(frontend, "SMOKE" if stage == "smoke" else "QUALIFICATION_PILOT", "TERMINAL_SCIENTIFIC_RESULT" if info["returncode"] == 0 else "FAILED_INFRASTRUCTURE", result_status=status)
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("frontend", choices=tuple(FRONTENDS)); parser.add_argument("stage", choices=("smoke", "pilot")); args = parser.parse_args(); execute(args.frontend, args.stage)
