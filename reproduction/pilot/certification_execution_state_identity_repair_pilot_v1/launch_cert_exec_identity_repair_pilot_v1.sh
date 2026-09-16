#!/usr/bin/env bash
set -euo pipefail

CHECKOUT=/disk1/zlab/v3_repair_worktrees/safer-splat-cert-exec-identity-repair-pilot-protocol-v1
RESULT_ROOT=/disk1/zlab/v3_repair_records/cert_exec_identity_repair_pilot_v1_20260916
TASK="$CHECKOUT/reproduction/pilot/certification_execution_state_identity_repair_pilot_v1"
PYTHON=/disk1/zlab/conda_envs/safer_splat_official/bin/python
RUNNER="$TASK/run_cert_exec_identity_repair_pilot_v1.py"
VALIDATOR="$TASK/validate_cert_exec_identity_repair_pilot_v1.py"
SESSION=cert-exec-identity-repair-pilot-v1

guard() {
  [[ "$(git -C "$CHECKOUT" branch --show-current)" == freeze-cert-exec-identity-repair-pilot-protocol-v1 ]] || { echo BRANCH_MISMATCH >&2; exit 2; }
  git -C "$CHECKOUT" merge-base --is-ancestor 601204bfc14e3ad2c8e3c714b8f5045829491635 HEAD || { echo UPSTREAM_DRIFT >&2; exit 2; }
  [[ -z "$(git -C "$CHECKOUT" status --porcelain --untracked-files=all)" ]] || { echo WORKTREE_NOT_CLEAN >&2; exit 2; }
  [[ ! -e "$RESULT_ROOT" ]] || { echo PILOT_RESULT_ROOT_MUST_BE_ABSENT >&2; exit 2; }
  if tmux has-session -t "$SESSION" 2>/dev/null; then echo PILOT_TMUX_ALREADY_EXISTS >&2; exit 2; fi
}

guard
export CUDA_VISIBLE_DEVICES=1 PYTHONHASHSEED=0 PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
"$PYTHON" "$RUNNER" --cpu-static-preflight --checkout "$CHECKOUT" --output-dir "$RESULT_ROOT"
"$PYTHON" "$VALIDATOR" --repo-root "$CHECKOUT" --prelaunch-check-only
if [[ "${1:-}" == --prelaunch-check-only ]]; then
  echo PRELAUNCH_CHECK_ONLY_PASS
  exit 0
fi
[[ $# -eq 0 ]] || { echo UNKNOWN_LAUNCHER_ARGUMENT >&2; exit 2; }

# This branch is intentionally unreachable during the protocol-freeze task.
mkdir -p "$RESULT_ROOT"
COMMAND="cd '$CHECKOUT' && '$PYTHON' '$RUNNER' --gpu-preflight --checkout '$CHECKOUT' --output-dir '$RESULT_ROOT' && '$PYTHON' '$RUNNER' --batch --checkout '$CHECKOUT' --output-dir '$RESULT_ROOT'; rc=\$?; echo PILOT_COMPLETE_OR_STOPPED_NO_SCIENTIFIC_ANALYSIS; exit \$rc"
tmux new-session -d -s "$SESSION" "exec >'$RESULT_ROOT/launcher.log' 2>&1; $COMMAND"
echo "STARTED_TMUX_SESSION=$SESSION"
