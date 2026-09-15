#!/usr/bin/env bash
set -euo pipefail

SESSION="active-runtime-v3-paired-validation-r1"
CHECKOUT="/disk1/zlab/v3_execution_worktrees/safer-splat-v3-paired-validation-r1"
RESULT_ROOT="/disk1/zlab/v3_execution_records/active_runtime_paired_validation_v3_r1_retry1_20260915"
MAP_ROOT="/disk1/zlab/projects/safer-splat/outputs/stonehenge/splatfacto/2024-09-11_100724"
PYTHON="/disk1/zlab/conda_envs/safer_splat_official/bin/python"
RUNNER="$CHECKOUT/reproduction/validation/active_runtime_paired_validation_v3_execution_r1/run_active_runtime_v3_paired_validation_r1.py"
VALIDATOR="$CHECKOUT/reproduction/validation/active_runtime_paired_validation_v3_execution_r1/validate_v3_paired_execution_harness_r1.py"

[[ "$(git -C "$CHECKOUT" branch --show-current)" == "refreeze-active-runtime-v3-paired-execution-harness-after-trace-repair-v1" ]] || { echo "EXECUTION_BRANCH_MISMATCH" >&2; exit 2; }
[[ "$(git -C "$CHECKOUT" rev-parse --is-inside-work-tree)" == true ]] || exit 2
[[ -z "$(git -C "$CHECKOUT" status --porcelain --untracked-files=all)" ]] || { echo "WORKTREE_NOT_CLEAN" >&2; exit 2; }
tmux has-session -t "$SESSION" 2>/dev/null && { echo "TMUX_SESSION_ALREADY_EXISTS" >&2; exit 2; }
[[ ! -e "$RESULT_ROOT" ]] || { echo "FIRST_LAUNCH_RESULT_ROOT_ALREADY_EXISTS" >&2; exit 2; }

export CUDA_VISIBLE_DEVICES=1 PYTHONHASHSEED=0 PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
"$PYTHON" "$RUNNER" --static-preflight --checkout "$CHECKOUT" --output-dir "$RESULT_ROOT" --map-source-root "$MAP_ROOT"
"$PYTHON" "$VALIDATOR" --repo-root "$CHECKOUT"

mkdir -p "$RESULT_ROOT"
LOG="$RESULT_ROOT/launcher.log"
COMMAND="cd '$CHECKOUT' && '$PYTHON' '$RUNNER' --gpu-preflight --resume --checkout '$CHECKOUT' --output-dir '$RESULT_ROOT' --map-source-root '$MAP_ROOT' && '$PYTHON' '$RUNNER' --batch --resume --checkout '$CHECKOUT' --output-dir '$RESULT_ROOT' --map-source-root '$MAP_ROOT'; rc=\$?; echo COLLECTION_COMPLETE_OR_STOPPED_REVIEW_BEFORE_ANALYSIS; exit \$rc"
tmux new-session -d -s "$SESSION" "exec >'$LOG' 2>&1; $COMMAND"
echo "STARTED_TMUX_SESSION=$SESSION"
