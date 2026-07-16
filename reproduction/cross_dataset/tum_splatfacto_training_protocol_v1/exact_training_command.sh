#!/usr/bin/env bash
# NOT EXECUTED: formal V1 command.
set -euo pipefail
source ~/anaconda3/etc/profile.d/conda.sh
conda activate safer_splat_official
export CUDA_VISIBLE_DEVICES=1
export PYTHONDONTWRITEBYTECODE=1
ns-train splatfacto --output-dir /disk1/zlab/formal_splatfacto_runs --experiment-name tum_fr1_room_splatfacto_v1 --timestamp 20260716_000000 --vis tensorboard --machine.seed 20260716 --machine.num-devices 1 --max-num-iterations 30000 --mixed-precision False --use-grad-scaler False --steps-per-save 2000 --steps-per-eval-image 100 --steps-per-eval-batch 0 --steps-per-eval-all-images 1000 --pipeline.model.camera-optimizer.mode off --pipeline.model.warmup-length 500 --pipeline.model.refine-every 100 --pipeline.model.resolution-schedule 3000 --pipeline.model.num-downscales 2 --pipeline.model.cull-alpha-thresh 0.1 --pipeline.model.cull-scale-thresh 0.5 --pipeline.model.densify-grad-thresh 0.0008 --pipeline.model.densify-size-thresh 0.01 --pipeline.model.sh-degree 3 --pipeline.model.sh-degree-interval 1000 --pipeline.model.reset-alpha-every 30 --pipeline.model.stop-split-at 15000 nerfstudio-data --data /disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room --orientation-method none --center-method none --auto-scale-poses False --downscale-factor 1 --eval-mode fraction --train-split-fraction 0.8 --depth-unit-scale-factor 0.0002
