#!/usr/bin/env bash
set -euo pipefail

cd /disk1/zlab/projects/safer-splat
source ~/anaconda3/etc/profile.d/conda.sh
conda activate safer_splat_official
export CUDA_VISIBLE_DEVICES=1
export PYTHONDONTWRITEBYTECODE=1

run_case() {
  local name="$1"
  shift
  echo "===== START ${name} $(date --iso-8601=seconds) ====="
  "$@"
  echo "===== DONE ${name} $(date --iso-8601=seconds) ====="
}

run_case baseline_reference \
  python work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py \
    --scene flight \
    --methods safer_splat_filter \
    --trial-start 57 \
    --trial-end 57 \
    --max-steps 800 \
    --candidate-budget 2000 \
    --near-distance-threshold 0.05 \
    --heading-distance-threshold 0.25 \
    --heading-cos-threshold 0.5 \
    --risk-score risk_v2_hybrid \
    --output-dir work/risk_aware_cbf/results/flight_trial57_baseline_reference \
    --resume \
    --skip-existing \
  2>&1 | tee work/risk_aware_cbf/notes/run_flight_trial57_baseline_reference.log

run_case v1_bestD_repro \
  python work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py \
    --scene flight \
    --methods risk_aware_v1_pre_cbf \
    --trial-start 57 \
    --trial-end 57 \
    --max-steps 800 \
    --candidate-budget 2000 \
    --near-distance-threshold 0.05 \
    --heading-distance-threshold 0.25 \
    --heading-cos-threshold 0.5 \
    --risk-score risk_v2_hybrid \
    --output-dir work/risk_aware_cbf/results/flight_trial57_v1_bestD_repro \
    --resume \
    --skip-existing \
  2>&1 | tee work/risk_aware_cbf/notes/run_flight_trial57_v1_bestD_repro.log

run_case v1_near008 \
  python work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py \
    --scene flight \
    --methods risk_aware_v1_pre_cbf \
    --trial-start 57 \
    --trial-end 57 \
    --max-steps 800 \
    --candidate-budget 2000 \
    --near-distance-threshold 0.08 \
    --heading-distance-threshold 0.25 \
    --heading-cos-threshold 0.5 \
    --risk-score risk_v2_hybrid \
    --output-dir work/risk_aware_cbf/results/flight_trial57_v1_near008 \
    --resume \
    --skip-existing \
  2>&1 | tee work/risk_aware_cbf/notes/run_flight_trial57_v1_near008.log

run_case v1_near008_heading035 \
  python work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py \
    --scene flight \
    --methods risk_aware_v1_pre_cbf \
    --trial-start 57 \
    --trial-end 57 \
    --max-steps 800 \
    --candidate-budget 2000 \
    --near-distance-threshold 0.08 \
    --heading-distance-threshold 0.35 \
    --heading-cos-threshold 0.5 \
    --risk-score risk_v2_hybrid \
    --output-dir work/risk_aware_cbf/results/flight_trial57_v1_near008_heading035 \
    --resume \
    --skip-existing \
  2>&1 | tee work/risk_aware_cbf/notes/run_flight_trial57_v1_near008_heading035.log

run_case v1_budget5000_near008_heading035 \
  python work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py \
    --scene flight \
    --methods risk_aware_v1_pre_cbf \
    --trial-start 57 \
    --trial-end 57 \
    --max-steps 800 \
    --candidate-budget 5000 \
    --near-distance-threshold 0.08 \
    --heading-distance-threshold 0.35 \
    --heading-cos-threshold 0.5 \
    --risk-score risk_v2_hybrid \
    --output-dir work/risk_aware_cbf/results/flight_trial57_v1_budget5000_near008_heading035 \
    --resume \
    --skip-existing \
  2>&1 | tee work/risk_aware_cbf/notes/run_flight_trial57_v1_budget5000_near008_heading035.log

run_case v1_full_fallback_diag \
  python work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py \
    --scene flight \
    --methods risk_aware_v1_pre_cbf \
    --trial-start 57 \
    --trial-end 57 \
    --max-steps 800 \
    --candidate-budget 999999 \
    --near-distance-threshold 999 \
    --heading-distance-threshold 999 \
    --heading-cos-threshold -1 \
    --risk-score risk_v2_hybrid \
    --output-dir work/risk_aware_cbf/results/flight_trial57_v1_full_fallback_diag \
    --resume \
    --skip-existing \
  2>&1 | tee work/risk_aware_cbf/notes/run_flight_trial57_v1_full_fallback_diag.log
