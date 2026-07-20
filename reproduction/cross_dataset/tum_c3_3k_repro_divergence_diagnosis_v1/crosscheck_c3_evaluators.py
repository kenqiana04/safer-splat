"""Independent fixed-60 raw expected-depth evaluator for immutable checkpoints."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import imageio.v3 as iio
import numpy as np
import torch
import yaml

from tum_metric_depth_splatfacto import TumMetricDepthSplatfactoConfig
from tum_metric_seed_dataparser import TumMetricSeedDataParserConfig

V1_CONFIG = Path("/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1r6/splatfacto/20260717_070309/config.yml")
SEED = Path("/disk1/zlab/maintenance_records/tum_map_geometry_root_cause_repair_v1/metric_seed_points/tum_fr1_room_metric_seed_points.npz")


def config() -> object:
    cfg = yaml.load(V1_CONFIG.read_text(encoding="utf-8"), Loader=yaml.UnsafeLoader)
    cfg.machine.seed = 20260716
    parser = TumMetricSeedDataParserConfig(base_dataparser=cfg.pipeline.datamanager.dataparser, seed_points_npz=SEED)
    cfg.pipeline.datamanager.dataparser = parser
    model = TumMetricDepthSplatfactoConfig()
    for key, value in vars(cfg.pipeline.model).items():
        if key != "_target" and hasattr(model, key):
            setattr(model, key, value)
    model.depth_loss_lambda = 0.10; model.depth_loss_beta_m = 0.10
    model.depth_unit_scale_factor = 0.0002; model.depth_accumulation_threshold = 1e-4
    model.output_depth_during_training = True; cfg.pipeline.model = model
    return cfg


def metric(gt: np.ndarray, pred: np.ndarray) -> tuple[dict[str, float], np.ndarray]:
    mask = (gt > 0) & np.isfinite(gt) & np.isfinite(pred) & (pred > 0)
    g, p = gt[mask], pred[mask]; ratio = (p / g).astype(np.float32); threshold = np.maximum(ratio, 1 / ratio)
    return {"overlap": float(mask.sum()), "valid_gt": float((gt > 0).sum()), "AbsRel": float(np.mean(np.abs(p-g)/g)), "delta_1_25": float(np.mean(threshold < 1.25))}, ratio


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--checkpoint", type=Path, required=True); parser.add_argument("--out", type=Path, required=True); args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True); pipe = config().pipeline.setup(device="cuda:0", test_mode="test", world_size=1, local_rank=0)
    checkpoint = torch.load(args.checkpoint, map_location="cpu"); pipe.load_state_dict(checkpoint["pipeline"], strict=True); pipe.eval()
    files = pipe.datamanager.eval_dataset._dataparser_outputs.metadata["depth_filenames"]; rows=[]; ratios=[]
    with torch.no_grad():
        for index in range(len(pipe.datamanager.fixed_indices_eval_dataloader)):
            camera, batch = pipe.datamanager.fixed_indices_eval_dataloader[index]; output=pipe.model.get_outputs_for_camera(camera.to(pipe.device))
            pred=output["depth"].squeeze(-1).float().cpu().numpy(); depth_path=str(files[int(batch["image_idx"])])
            values, ratio = metric(iio.imread(depth_path).astype(np.float32)*0.0002, pred); rows.append({"eval_index":index,"image_idx":int(batch["image_idx"]),"depth_path":depth_path,**values}); ratios.append(ratio)
    weights=np.asarray([r["overlap"] for r in rows]); result={"evaluator":"EVAL_C_INDEPENDENT_EXPLICIT_CONFIG","checkpoint":str(args.checkpoint),"checkpoint_step":int(checkpoint["step"]),"frame_count":len(rows),"valid_overlap_pixel_count":int(weights.sum()),"valid_overlap_ratio":float(weights.sum()/sum(r["valid_gt"] for r in rows)),"AbsRel":float(np.average([r["AbsRel"] for r in rows],weights=weights)),"delta_1_25":float(np.average([r["delta_1_25"] for r in rows],weights=weights)),"median_predicted_over_gt_depth_ratio":float(np.median(np.concatenate(ratios))),"depth_semantic":"expected_depth_from_splatfacto_RGB+ED; raw metric comparison; no scale alignment"}
    with (args.out/"depth_metrics_per_frame.csv").open("w",newline="") as handle: writer=csv.DictWriter(handle,fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows(rows)
    (args.out/"depth_metrics_raw.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(result,sort_keys=True))


if __name__ == "__main__": main()
