#!/usr/bin/env bash
set -euo pipefail

SESSION="active-runtime-v3-paired-validation"
CHECKOUT="/disk1/zlab/v3_execution_worktrees/safer-splat-v3-paired-validation"
RESULT_ROOT="/disk1/zlab/v3_execution_records/active_runtime_paired_validation_v3_20260914"
MAP_ROOT="/disk1/zlab/projects/safer-splat/outputs/stonehenge/splatfacto/2024-09-11_100724"
PYTHON="/disk1/zlab/conda_envs/safer_splat_official/bin/python"
RUNNER="$CHECKOUT/reproduction/validation/active_runtime_paired_validation_v3_execution/run_active_runtime_v3_paired_validation.py"

test "$(git -C "$CHECKOUT" branch --show-current)" = "execute-active-runtime-v3-paired-validation-v1"
git -C "$CHECKOUT" status --porcelain | grep -q . && { echo "WORKTREE_NOT_CLEAN" >&2; exit 2; } || true
tmux has-session -t "$SESSION" 2>/dev/null && { echo "TMUX_SESSION_ALREADY_EXISTS" >&2; exit 2; }
mkdir -p "$RESULT_ROOT"

export CUDA_VISIBLE_DEVICES=1 PYTHONHASHSEED=0 PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
COMMAND="cd '$CHECKOUT' && '$PYTHON' '$RUNNER' --gpu-preflight --checkout '$CHECKOUT' --output-dir '$RESULT_ROOT' --map-source-root '$MAP_ROOT' && '$PYTHON' '$RUNNER' --batch --checkout '$CHECKOUT' --output-dir '$RESULT_ROOT' --map-source-root '$MAP_ROOT'; rc=\$?; echo COLLECTION_COMPLETE_OR_STOPPED_REVIEW_BEFORE_ANALYSIS; exit \$rc"
tmux new-session -d -s "$SESSION" "$COMMAND"
echo "STARTED_TMUX_SESSION=$SESSION"
