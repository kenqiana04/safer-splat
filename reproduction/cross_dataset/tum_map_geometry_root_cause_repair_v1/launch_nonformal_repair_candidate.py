"""Launch one isolated NONFORMAL TUM repair candidate from the frozen config."""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path

import yaml
from nerfstudio.engine.trainer import Trainer

from tum_metric_depth_splatfacto import TumMetricDepthSplatfactoConfig
from tum_metric_seed_dataparser import TumMetricSeedDataParserConfig


V1_CONFIG = Path("/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1r6/splatfacto/20260717_070309/config.yml")
SEED_NPZ = Path("/disk1/zlab/maintenance_records/tum_map_geometry_root_cause_repair_v1/metric_seed_points/tum_fr1_room_metric_seed_points.npz")


def configure(candidate: str, output_root: Path, steps: int):
    config = yaml.load(V1_CONFIG.read_text(encoding="utf-8"), Loader=yaml.UnsafeLoader)
    config.machine.seed = 20260716
    config.max_num_iterations = steps
    config.steps_per_save = steps
    config.steps_per_eval_all_images = steps
    config.steps_per_eval_image = steps
    config.output_dir = output_root
    config.experiment_name = f"NONFORMAL_{candidate}"
    config.timestamp = f"seed20260716_{steps:05d}"
    config.load_dir = None
    config.load_checkpoint = None
    config.load_step = None
    base_parser = copy.deepcopy(config.pipeline.datamanager.dataparser)
    if candidate in {"C1_METRIC_SEED_ONLY", "C3_METRIC_SEED_PLUS_DEPTH"}:
        config.pipeline.datamanager.dataparser = TumMetricSeedDataParserConfig(base_dataparser=base_parser, seed_points_npz=SEED_NPZ)
    if candidate in {"C2_DEPTH_SUPERVISION_ONLY", "C3_METRIC_SEED_PLUS_DEPTH"}:
        model = TumMetricDepthSplatfactoConfig()
        for key, value in vars(config.pipeline.model).items():
            # Preserve the task-owned model target.  Copying the frozen
            # SplatfactoConfig ``_target`` would silently replace this wrapper
            # with the stock RGB-only model.
            if key != "_target" and hasattr(model, key):
                setattr(model, key, value)
        model.depth_loss_lambda = 0.10
        model.depth_loss_beta_m = 0.10
        model.depth_unit_scale_factor = 0.0002
        model.depth_accumulation_threshold = 1e-4
        model.output_depth_during_training = True
        config.pipeline.model = model
    return config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=["C1_METRIC_SEED_ONLY", "C2_DEPTH_SUPERVISION_ONLY", "C3_METRIC_SEED_PLUS_DEPTH"], required=True)
    parser.add_argument("--steps", type=int, choices=[100, 3000, 10000], required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    config = configure(args.candidate, args.output_root, args.steps)
    trainer = Trainer(config, local_rank=0, world_size=1)
    trainer.setup(test_mode="val")
    trainer.train()
    summary = {
        "candidate": args.candidate,
        "steps": args.steps,
        "seed": 20260716,
        "seed_points": args.candidate in {"C1_METRIC_SEED_ONLY", "C3_METRIC_SEED_PLUS_DEPTH"},
        "depth_supervision": args.candidate in {"C2_DEPTH_SUPERVISION_ONLY", "C3_METRIC_SEED_PLUS_DEPTH"},
        "depth_loss_lambda": 0.10 if "DEPTH" in args.candidate else 0.0,
        "depth_loss_beta_m": 0.10 if "DEPTH" in args.candidate else None,
        "output_root": str(args.output_root),
        "formal_training": False,
    }
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
