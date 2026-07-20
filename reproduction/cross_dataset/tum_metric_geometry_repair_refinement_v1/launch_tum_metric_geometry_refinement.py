"""Launch one preregistered task-owned nonformal refinement candidate."""
from __future__ import annotations

import argparse
import copy
from pathlib import Path

import yaml
from nerfstudio.engine.trainer import Trainer

from tum_metric_seed_dataparser import TumMetricSeedDataParserConfig
from tum_metric_geometry_refinement_model import TumMetricGeometryRefinementConfig

V1_CONFIG = Path("/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1r6/splatfacto/20260717_070309/config.yml")
SEED_NPZ = Path("/disk1/zlab/maintenance_records/tum_map_geometry_root_cause_repair_v1/metric_seed_points/tum_fr1_room_metric_seed_points.npz")
MATRIX = {
    "R0_C3_BASELINE": ("CONSTANT_010", "STOCK_REFINEMENT"),
    "R1_LATE_DEPTH_HOLD": ("LATE_HOLD_030", "STOCK_REFINEMENT"),
    "R2_REFINEMENT_LOCK_3000": ("CONSTANT_010", "LOCK_AFTER_3000"),
    "R3_LATE_DEPTH_HOLD_AND_LOCK": ("LATE_HOLD_030", "LOCK_AFTER_3000"),
}


def configure(candidate: str, output_root: Path, steps: int):
    schedule, refinement = MATRIX[candidate]
    config = yaml.load(V1_CONFIG.read_text(encoding="utf-8"), Loader=yaml.UnsafeLoader)
    config.machine.seed = 20260716; config.max_num_iterations = steps
    config.steps_per_save = 1000; config.save_only_latest_checkpoint = False
    config.steps_per_eval_all_images = steps; config.steps_per_eval_image = steps
    config.output_dir = output_root; config.experiment_name = f"NONFORMAL_{candidate}"; config.timestamp = f"seed20260716_{steps:05d}"
    config.load_dir = None; config.load_checkpoint = None; config.load_step = None
    base_parser = copy.deepcopy(config.pipeline.datamanager.dataparser)
    config.pipeline.datamanager.dataparser = TumMetricSeedDataParserConfig(base_dataparser=base_parser, seed_points_npz=SEED_NPZ)
    model = TumMetricGeometryRefinementConfig()
    for key, value in vars(config.pipeline.model).items():
        if key != "_target" and hasattr(model, key): setattr(model, key, value)
    model.depth_loss_lambda = 0.10; model.depth_loss_beta_m = 0.10; model.depth_unit_scale_factor = 0.0002
    model.output_depth_during_training = True; model.depth_schedule = schedule; model.refinement_mode = refinement
    model.instrumentation_path = str(output_root / "training_events.jsonl")
    config.pipeline.model = model
    return config


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--candidate", choices=MATRIX, required=True); parser.add_argument("--steps", choices=(100, 6000, 10000), type=int, required=True); parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(); config = configure(args.candidate, args.output_root, args.steps)
    trainer = Trainer(config, local_rank=0, world_size=1); trainer.setup(test_mode="val"); trainer.train()


if __name__ == "__main__": main()
