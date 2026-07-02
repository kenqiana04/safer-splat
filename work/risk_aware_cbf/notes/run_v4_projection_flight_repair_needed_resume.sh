#!/usr/bin/env bash
set -euo pipefail
cd /disk1/zlab/projects/safer-splat
source ~/anaconda3/etc/profile.d/conda.sh
conda activate safer_splat_official
export CUDA_VISIBLE_DEVICES=1
export PYTHONDONTWRITEBYTECODE=1
python work/risk_aware_cbf/scripts/run_v4_projection_repair_needed.py \
  --scene flight \
  --initial-safety-csv work/risk_aware_cbf/results/startguard_flight100_v1_bestD/initial_safety_trials.csv \
  --safety-margin 0.0005 \
  --near-unsafe-margin 0.0010 \
  --output-dir work/risk_aware_cbf/results/v4_projection_flight_repair_needed \
  --resume \
  --skip-existing \
  2>&1 | tee -a work/risk_aware_cbf/notes/run_v4_projection_flight_repair_needed.log
