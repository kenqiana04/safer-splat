#!/usr/bin/env bash
set -o pipefail
cd /disk1/zlab/projects/safer-splat || exit 1
source ~/anaconda3/etc/profile.d/conda.sh
conda activate safer_splat_official
export CUDA_VISIBLE_DEVICES=1
export PYTHONDONTWRITEBYTECODE=1
python work/risk_aware_cbf/scripts/run_startguard_flight100.py \
  --scene flight \
  --trial-start 0 \
  --trial-end 99 \
  --safety-margin 0.0005 \
  --near-unsafe-margin 0.0010 \
  --method risk_aware_v1_bestD \
  --max-steps 800 \
  --candidate-budget 2000 \
  --near-distance-threshold 0.05 \
  --heading-distance-threshold 0.25 \
  --heading-cos-threshold 0.5 \
  --risk-score risk_v2_hybrid \
  --repair-step-size 0.005 \
  --repair-max-steps 100 \
  --repair-max-distance 0.20 \
  --num-nearby-gaussians 20 \
  --output-dir work/risk_aware_cbf/results/startguard_flight100_v1_bestD \
  --resume \
  --skip-existing \
  2>&1 | tee work/risk_aware_cbf/notes/run_startguard_flight100_v1_bestD.log
status=${PIPESTATUS[0]}
echo STARTGUARD_V1_EXIT:${status} | tee -a work/risk_aware_cbf/notes/run_startguard_flight100_v1_bestD.log
exit ${status}
