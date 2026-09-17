#!/usr/bin/env bash
set -euo pipefail
TASK_DIR=/disk1/zlab/v3_repair_worktrees/safer-splat-post-repair-v3-paired-validation-protocol-v1/reproduction/formal/post_repair_v3_paired_validation_v1
CHECKOUT=/disk1/zlab/v3_repair_worktrees/safer-splat-post-repair-v3-paired-validation-protocol-v1
ROOT=/disk1/zlab/v3_repair_records/post_repair_v3_paired_validation_v1_20260917
PY=/disk1/zlab/conda_envs/safer_splat_official/bin/python
SESSION=post_repair_v3_paired_validation_v1
export PYTHONHASHSEED=0 PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1
if [[ "${1:-}" == --prelaunch-check-only && $# == 1 ]]; then
  "$PY" "$TASK_DIR/validate_post_repair_v3_paired_validation_v1.py"
  "$PY" "$TASK_DIR/run_post_repair_v3_paired_validation_v1.py" --cpu-static-preflight
  if [[ -e "$ROOT" ]]; then echo FUTURE_RESULT_ROOT_NOT_ABSENT >&2; exit 2; fi
  if tmux has-session -t "$SESSION" 2>/dev/null; then echo TMUX_SESSION_ALREADY_EXISTS >&2; exit 2; fi
  echo PRELAUNCH_CHECK_ONLY_PASS
  exit 0
fi
if [[ $# != 0 ]]; then echo 'Only --prelaunch-check-only or explicit future launch with no args is supported' >&2; exit 2; fi
"$PY" "$TASK_DIR/validate_post_repair_v3_paired_validation_v1.py"
if [[ -e "$ROOT" ]]; then echo EXISTING_RESULT_ROOT_NO_AUTO_RERUN >&2; exit 2; fi
if tmux has-session -t "$SESSION" 2>/dev/null; then echo TMUX_SESSION_ALREADY_EXISTS >&2; exit 2; fi
if [[ "$(git -C "$CHECKOUT" branch --show-current)" != freeze-post-repair-v3-paired-scientific-validation-protocol-v1 ]]; then exit 2; fi
if [[ -n "$(git -C "$CHECKOUT" status --porcelain --untracked-files=all)" ]]; then echo DIRTY_WORKTREE >&2; exit 2; fi
export CUDA_VISIBLE_DEVICES=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
mkdir -m 700 "$ROOT"
"$PY" "$TASK_DIR/run_post_repair_v3_paired_validation_v1.py" --gpu-preflight
tmux new-session -d -s "$SESSION" "cd '$CHECKOUT' && '$PY' '$TASK_DIR/run_post_repair_v3_paired_validation_v1.py' --batch > '$ROOT/batch.log' 2>&1"
echo FORMAL_COLLECTION_LAUNCHED_NO_SCIENTIFIC_ANALYSIS
