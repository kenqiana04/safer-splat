"""Launch exactly one fresh, nonformal E3 coordinate-search candidate."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from nerfstudio.engine.trainer import Trainer


def load_source_launcher(source_root: Path):
    sys.path.insert(0, str(source_root))
    spec = importlib.util.spec_from_file_location("frozen_e3_launcher", source_root / "launch_nonformal_repair_candidate.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"SOURCE_LAUNCHER_UNAVAILABLE:{source_root}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare_config(source_root: Path, candidate_id: str, output_root: Path, steps: int, late_lambda: float, lock_step: int, beta_m: float):
    if steps not in {100, 6000, 10000}:
        raise ValueError(f"UNAUTHORIZED_STEP_COUNT:{steps}")
    if late_lambda not in {0.20, 0.30, 0.40, 0.50}:
        raise ValueError(f"UNAUTHORIZED_LATE_LAMBDA:{late_lambda}")
    if lock_step not in {2000, 3000, 4000}:
        raise ValueError(f"UNAUTHORIZED_LOCK_STEP:{lock_step}")
    if beta_m not in {0.05, 0.10, 0.20}:
        raise ValueError(f"UNAUTHORIZED_DEPTH_BETA:{beta_m}")
    module = load_source_launcher(source_root)
    config = module.configure("C3_METRIC_SEED_PLUS_DEPTH", output_root, steps)
    model = config.pipeline.model
    model.late_depth_hold_start = 3000
    model.late_depth_hold_lambda = late_lambda
    model.refinement_lock_step = lock_step
    model.depth_loss_beta_m = beta_m
    config.experiment_name = f"NONFORMAL_SWEEP_{candidate_id}"
    config.timestamp = f"seed20260716_{steps:05d}"
    config.load_dir = None
    config.load_checkpoint = None
    config.load_step = None
    return config


def contract(config) -> dict[str, object]:
    model = config.pipeline.model
    return {
        "seed": int(config.machine.seed), "steps": int(config.max_num_iterations), "model_class": f"{type(model).__module__}.{type(model).__name__}",
        "late_depth_hold_start": int(model.late_depth_hold_start), "late_depth_hold_lambda": float(model.late_depth_hold_lambda),
        "refinement_lock_step": int(model.refinement_lock_step), "depth_loss_beta_m": float(model.depth_loss_beta_m),
        "depth_loss_lambda": float(model.depth_loss_lambda), "depth_unit_scale_factor": float(model.depth_unit_scale_factor),
        "depth_accumulation_threshold": float(model.depth_accumulation_threshold), "load_dir": config.load_dir, "load_checkpoint": config.load_checkpoint,
        "output_depth_during_training": bool(model.output_depth_during_training), "formal_training": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--steps", type=int, required=True)
    parser.add_argument("--late-lambda", type=float, required=True)
    parser.add_argument("--lock-step", type=int, required=True)
    parser.add_argument("--beta-m", type=float, required=True)
    parser.add_argument("--contract-out", type=Path, required=True)
    args = parser.parse_args()
    if args.output_root.exists():
        raise SystemExit(f"FRESH_OUTPUT_REQUIRED:{args.output_root}")
    config = prepare_config(args.source_root, args.candidate_id, args.output_root, args.steps, args.late_lambda, args.lock_step, args.beta_m)
    info = contract(config) | {"candidate_id": args.candidate_id, "output_root": str(args.output_root), "source_root": str(args.source_root)}
    args.contract_out.parent.mkdir(parents=True, exist_ok=True)
    args.contract_out.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    trainer = Trainer(config, local_rank=0, world_size=1)
    trainer.setup(test_mode="val")
    trainer.train()
    print(json.dumps(info, sort_keys=True))


if __name__ == "__main__":
    main()
