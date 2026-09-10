#!/usr/bin/env bash
set -euo pipefail

ROOT=/disk1/zlab/maintenance_records/active_runtime_pilot_v2
EXEC="$ROOT/server_execution"
SRC=/disk1/zlab/maintenance_records/active_runtime_smoke_v2/source_checkout
PY=/disk1/zlab/conda_envs/safer_splat_official/bin/python
RUNNER="$ROOT/harness/run_active_runtime_pilot_v2.py"

export CUDA_VISIBLE_DEVICES=1
export PYTHONHASHSEED=0
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8

mkdir -p "$ROOT/autofix_attempts/oracle_summary_v1"
cd "$EXEC"
find raw -name summary.json -exec cp --parents '{}' "$ROOT/autofix_attempts/oracle_summary_v1/" ';'

for trial in 5 15 25 35 45 55 65 75 85 95; do
  for arm in REFERENCE_CBF_QP ACTIVE_RUNTIME_V2; do
    "$PY" "$RUNNER" --oracle-only-trial "$trial" --arm "$arm" --checkout "$SRC" --output-dir "$EXEC"
  done
done

"$PY" "$RUNNER" --aggregate-only --checkout "$SRC" --output-dir "$EXEC"
echo 0 > "$EXEC/oracle_recompute_exit_code.txt"
