#!/usr/bin/env bash
set -euo pipefail

SESSION="cert-exec-identity-repair-smoke-v1"
CHECKOUT="/disk1/zlab/v3_repair_worktrees/safer-splat-cert-exec-identity-repair-smoke-protocol-v1"
RESULT_ROOT="/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry1_20260916"
PYTHON="/disk1/zlab/conda_envs/safer_splat_official/bin/python"
TASK="$CHECKOUT/reproduction/validation/certification_execution_state_identity_repair_smoke_v1"
RUNNER="$TASK/run_cert_exec_identity_repair_smoke_v1.py"
VALIDATOR="$TASK/validate_cert_exec_identity_repair_smoke_v1.py"

[[ "$(git -C "$CHECKOUT" branch --show-current)" == "freeze-cert-exec-identity-repair-smoke-protocol-v1" ]] || { echo BRANCH_MISMATCH >&2; exit 2; }
git -C "$CHECKOUT" merge-base --is-ancestor 546598a70e12fa99f9153f1927d0542ca27862b4 HEAD || { echo IMPLEMENTATION_HEAD_NOT_ANCESTOR >&2; exit 2; }
[[ -z "$(git -C "$CHECKOUT" status --porcelain --untracked-files=all)" ]] || { echo WORKTREE_NOT_CLEAN >&2; exit 2; }
tmux has-session -t "$SESSION" 2>/dev/null && { echo TMUX_SESSION_ALREADY_EXISTS >&2; exit 2; }
[[ ! -e "/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_20260916" ]] || { echo OLD_FAILED_ROOT_MUST_REMAIN_READ_ONLY >&2; exit 2; }
[[ ! -e "$RESULT_ROOT" ]] || { echo RESULT_ROOT_ABSENT_CHECK_FAILED >&2; exit 2; }
echo RESULT_ROOT_ABSENT

export CUDA_VISIBLE_DEVICES=1 PYTHONHASHSEED=0 PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
"$PYTHON" "$RUNNER" --cpu-static-preflight --checkout "$CHECKOUT" --output-dir "$RESULT_ROOT"
"$PYTHON" "$VALIDATOR" --repo-root "$CHECKOUT"
mkdir -p "$RESULT_ROOT"
LOG="$RESULT_ROOT/launcher.log"
COMMAND="cd '$CHECKOUT' && '$PYTHON' '$RUNNER' --gpu-preflight --checkout '$CHECKOUT' --output-dir '$RESULT_ROOT' && '$PYTHON' '$RUNNER' --batch --checkout '$CHECKOUT' --output-dir '$RESULT_ROOT'; rc=\$?; echo COLLECTION_COMPLETE_OR_STOPPED_REVIEW_BEFORE_ANY_SCIENTIFIC_ANALYSIS; exit \$rc"
tmux new-session -d -s "$SESSION" "exec >'$LOG' 2>&1; $COMMAND"
echo "STARTED_TMUX_SESSION=$SESSION"
