"""Create a task-owned SplaTAM GT-pose configuration; do not edit official code."""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--output", type=Path, required=True); p.add_argument("--data-root", type=Path, required=True); p.add_argument("--workdir", type=Path, required=True); p.add_argument("--run-name", required=True); p.add_argument("--frames", type=int, required=True); p.add_argument("--mapping-iters", type=int, required=True); a = p.parse_args()
    if a.frames not in {5, 30, 240}:
        raise RuntimeError("UNREGISTERED_FRAME_COUNT")
    # Values below are copied from the official Replica offline Gaussian mapping
    # configuration.  Only I/O, seed, headless mode, and bounded smoke length vary.
    a.output.write_text(f'''config = dict(
    workdir={str(a.workdir)!r}, run_name={a.run_name!r}, seed=0, primary_device="cuda:0",
    report_global_progress_every=500, eval_every=500, scene_radius_depth_ratio=3,
    mean_sq_dist_method="projective", gaussian_distribution="isotropic", report_iter_progress=False,
    load_checkpoint=False, checkpoint_time_idx=0, save_checkpoints=False, checkpoint_interval=5, use_wandb=False,
    wandb=dict(entity="", project="", group="", name="", save_qual=False, eval_save_qual=False),
    data=dict(basedir={str(a.data_root)!r}, gradslam_data_cfg="configs/data/TUM/freiburg1_room.yaml",
              sequence="rgbd_dataset_freiburg1_room", desired_image_height_init=480, desired_image_width_init=640,
              desired_image_height=480, desired_image_width=640, start=0, end=-1, stride=1,
              num_frames={a.frames}, eval_stride=1, eval_num_frames={a.frames}),
    train=dict(num_iters_mapping={a.mapping_iters}, sil_thres=0.5, use_sil_for_loss=True,
        loss_weights=dict(im=0.5, depth=1.0),
        lrs_mapping=dict(means3D=0.00032, rgb_colors=0.0025, unnorm_rotations=0.001, logit_opacities=0.05, log_scales=0.005, cam_unnorm_rots=0.0, cam_trans=0.0),
        lrs_mapping_means3D_final=0.0000032, lr_delay_mult=0.01, use_gaussian_splatting_densification=True,
        densify_dict=dict(start_after=500, remove_big_after=3000, stop_after=15000, densify_every=100, grad_thresh=0.0002, num_to_split_into=2, removal_opacity_threshold=0.005, final_removal_opacity_threshold=0.005, reset_opacities=True, reset_opacities_every=3000)),
    viz=dict(render_mode="color", offset_first_viz_cam=True, show_sil=False, visualize_cams=False, viz_w=600, viz_h=340, viz_near=0.01, viz_far=100.0, view_scale=2, viz_fps=5, enter_interactive_post_online=False))
''', encoding="utf-8")
    print("PATCH_STATUS=TASK_OWNED_CONFIG_ONLY")


if __name__ == "__main__": main()
