"""Read a 100-step smoke checkpoint and verify one real metric-depth loss is finite."""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import torch


def load_launcher(path: Path):
    spec = importlib.util.spec_from_file_location("sweep_launch", path)
    if spec is None or spec.loader is None: raise RuntimeError(f"LAUNCHER_LOAD_FAILED:{path}")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--launcher", type=Path, required=True)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--late-lambda", type=float, required=True)
    parser.add_argument("--lock-step", type=int, required=True)
    parser.add_argument("--beta-m", type=float, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.source_root))
    launcher = load_launcher(args.launcher)
    cfg = launcher.prepare_config(args.source_root, args.candidate_id, args.out.parent / "ephemeral_validation_config", 100, args.late_lambda, args.lock_step, args.beta_m)
    cfg.load_dir = None; cfg.load_checkpoint = None; cfg.load_step = None
    pipeline = cfg.pipeline.setup(device="cuda:0", test_mode="test", world_size=1, local_rank=0)
    payload = torch.load(args.checkpoint, map_location="cpu")
    pipeline.load_state_dict(payload["pipeline"], strict=True); pipeline.eval()
    camera, batch = pipeline.datamanager.fixed_indices_eval_dataloader[0]
    camera = camera.to(pipeline.device)
    with torch.no_grad():
        outputs = pipeline.model.get_outputs_for_camera(camera)
        losses = pipeline.model.get_loss_dict(outputs, batch)
    depth_loss = float(losses["loss_depth_metric"].detach().cpu().item())
    result = {"candidate_id": args.candidate_id, "checkpoint": str(args.checkpoint), "checkpoint_step": int(payload.get("step", -1)), "loss_depth_metric": depth_loss, "loss_depth_metric_finite": math.isfinite(depth_loss), "parameters": launcher.contract(cfg), "resume_or_load": False, "formal_training": False, "status": "PASS" if int(payload.get("step", -1)) == 99 and math.isfinite(depth_loss) else "SMOKE_VALIDATION_FAILED"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS": raise SystemExit(2)


if __name__ == "__main__":
    main()
