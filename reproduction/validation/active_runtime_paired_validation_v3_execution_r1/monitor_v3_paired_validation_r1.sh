#!/usr/bin/env bash
set -euo pipefail

CHECKOUT="/disk1/zlab/v3_execution_worktrees/safer-splat-v3-paired-validation-r1"
RESULT_ROOT="/disk1/zlab/v3_execution_records/active_runtime_paired_validation_v3_r1_retry1_20260915"
SUMMARY="$RESULT_ROOT/ACTIVE_V3_R1_COLLECTION_INTEGRITY_SUMMARY.json"
GPU="${CUDA_VISIBLE_DEVICES:-1}"

while true; do
  status="STOPPED"
  if tmux has-session -t active-runtime-v3-paired-validation-r1 2>/dev/null; then status="RUNNING"; fi
  complete="0"; last="none"; dirs="0"; hard="none"
  if [[ -f "$SUMMARY" ]]; then
    readarray -t vals < <(/disk1/zlab/conda_envs/safer_splat_official/bin/python - "$SUMMARY" <<'PY'
import json,sys
p=json.load(open(sys.argv[1])); print(p.get('completed_trials',0)); ids=p.get('completed_trial_ids_in_frozen_order',[]); print(ids[-1] if ids else 'none'); print(len(ids)); print(p.get('latest_hard_stop','none'))
PY
)
    complete="${vals[0]}"; last="${vals[1]}"; hard="${vals[3]}"
  fi
  if [[ -d "$RESULT_ROOT/raw" ]]; then dirs=$(find "$RESULT_ROOT/raw" -mindepth 1 -maxdepth 1 -type d -name 'trial_*' | wc -l); fi
  gpu_line=$(nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null | awk -v id="$GPU" '$1==id {print; found=1} END{if(!found)print "unavailable"}')
  printf 'STATUS=%s COMPLETE=%s/85 LAST_COMPLETE_TRIAL=%s PRESENT_TRIAL_DIRS=%s LATEST_HARD_STOP=%s GPU=%s\n' "$status" "$complete" "$last" "$dirs" "$hard" "$gpu_line"
  [[ "$status" == "STOPPED" ]] && break
  sleep 10
done
