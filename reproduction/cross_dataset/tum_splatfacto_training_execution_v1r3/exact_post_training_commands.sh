#!/usr/bin/env bash
set -euo pipefail

source ~/anaconda3/etc/profile.d/conda.sh
conda activate safer_splat_official
export CUDA_VISIBLE_DEVICES=1
export PYTHONDONTWRITEBYTECODE=1

RUN=/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1/splatfacto/20260716_000000
CONFIG="$RUN/config.yml"
REPORTS="$RUN/reports"
RENDERS="$RUN/renders"
test -f "$CONFIG"
mkdir -p "$REPORTS" "$RENDERS"
ns-eval --load-config "$CONFIG" --output-path "$REPORTS/eval_metrics.json"
ns-render dataset --load-config "$CONFIG" --output-path "$RENDERS" --image-format png --rendered-output-names rgb --split val
