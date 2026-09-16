#!/usr/bin/env bash
set -euo pipefail

SESSION="cert-exec-identity-repair-smoke-v1"
CHECKOUT="/disk1/zlab/v3_repair_worktrees/safer-splat-cert-exec-identity-smoke-delegate-protocol-projection-r5"
ACTIVE_BRANCH="repair-cert-exec-identity-smoke-delegate-protocol-projection-r5"
RESULT_ROOT="/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry4_20260916"
OLD_FAILED_ROOT="/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_20260916"
OLD_LAUNCHER_LOG_SHA256="e6b627d62ce3a96cb5d975d5e0151fd0c54a93ee547ab34d90668771800f269f"
ATTEMPT1_FAILED_ROOT="/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry1_20260916"
ATTEMPT1_LAUNCHER_LOG_SHA256="a1a647cd52426ebce38459c3e87522864266374842b824fb2d7075d10804910f"
ATTEMPT2_FAILED_ROOT="/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry2_20260916"
ATTEMPT2_LAUNCHER_LOG_SHA256="b82fc2409280b8c545914dc8664ddf8ea9291f213831f277ac7ffa1385439762"
ATTEMPT2_FAILURE_JSON_SHA256="16f2ebd7d40aa93d118b03311903749889509c27516825fa2dda267706e1aa79"
ATTEMPT3_FAILED_ROOT="/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry3_20260916"
ATTEMPT3_LAUNCHER_LOG_SHA256="b8bfd94a3be10812bb9528baa55eb398456a22ec1a239f44c2f10d587760d0dd"
ATTEMPT3_PREFLIGHT_SHA256="bb9473c716fab705766e2358d070f559ec23efa96c800e5469f5c2a5bebf747a"
ATTEMPT3_TRIAL15_SUMMARY_SHA256="6ac573fc4c80debffe52c99186b89501b6479d4ea1abfc2d17f1c10cb350a806"
PYTHON="/disk1/zlab/conda_envs/safer_splat_official/bin/python"
TASK="$CHECKOUT/reproduction/validation/certification_execution_state_identity_repair_smoke_v1"
RUNNER="$TASK/run_cert_exec_identity_repair_smoke_v1.py"
VALIDATOR="$TASK/validate_cert_exec_identity_repair_smoke_v1.py"

guard_static_environment() {
  [[ "$(git -C "$CHECKOUT" branch --show-current)" == "$ACTIVE_BRANCH" ]] || { echo BRANCH_MISMATCH >&2; exit 2; }
  git -C "$CHECKOUT" merge-base --is-ancestor 546598a70e12fa99f9153f1927d0542ca27862b4 HEAD || { echo IMPLEMENTATION_HEAD_NOT_ANCESTOR >&2; exit 2; }
  [[ -z "$(git -C "$CHECKOUT" status --porcelain --untracked-files=all)" ]] || { echo WORKTREE_NOT_CLEAN >&2; exit 2; }
  [[ -d "$OLD_FAILED_ROOT" ]] || { echo OLD_FAILED_ROOT_MISSING >&2; exit 2; }
  [[ -f "$OLD_FAILED_ROOT/launcher.log" ]] || { echo OLD_FAILED_ROOT_LAUNCHER_LOG_MISSING >&2; exit 2; }
  [[ "$(sha256sum "$OLD_FAILED_ROOT/launcher.log" | awk '{print $1}')" == "$OLD_LAUNCHER_LOG_SHA256" ]] || { echo OLD_FAILED_ROOT_IDENTITY_MISMATCH >&2; exit 2; }
  [[ -d "$ATTEMPT1_FAILED_ROOT" ]] || { echo ATTEMPT1_FAILED_ROOT_MISSING >&2; exit 2; }
  [[ -f "$ATTEMPT1_FAILED_ROOT/launcher.log" ]] || { echo ATTEMPT1_LAUNCHER_LOG_MISSING >&2; exit 2; }
  [[ "$(sha256sum "$ATTEMPT1_FAILED_ROOT/launcher.log" | awk '{print $1}')" == "$ATTEMPT1_LAUNCHER_LOG_SHA256" ]] || { echo ATTEMPT1_ROOT_IDENTITY_MISMATCH >&2; exit 2; }
  [[ -d "$ATTEMPT2_FAILED_ROOT" ]] || { echo ATTEMPT2_FAILED_ROOT_MISSING >&2; exit 2; }
  [[ -f "$ATTEMPT2_FAILED_ROOT/launcher.log" && -f "$ATTEMPT2_FAILED_ROOT/gpu_preflight_failure.json" ]] || { echo ATTEMPT2_EVIDENCE_FILE_MISSING >&2; exit 2; }
  [[ "$(sha256sum "$ATTEMPT2_FAILED_ROOT/launcher.log" | awk '{print $1}')" == "$ATTEMPT2_LAUNCHER_LOG_SHA256" ]] || { echo ATTEMPT2_ROOT_IDENTITY_MISMATCH >&2; exit 2; }
  [[ "$(sha256sum "$ATTEMPT2_FAILED_ROOT/gpu_preflight_failure.json" | awk '{print $1}')" == "$ATTEMPT2_FAILURE_JSON_SHA256" ]] || { echo ATTEMPT2_ROOT_IDENTITY_MISMATCH >&2; exit 2; }
  [[ -d "$ATTEMPT3_FAILED_ROOT" ]] || { echo ATTEMPT3_FAILED_ROOT_MISSING >&2; exit 2; }
  [[ -f "$ATTEMPT3_FAILED_ROOT/launcher.log" && -f "$ATTEMPT3_FAILED_ROOT/raw/gpu_preflight.json" && -f "$ATTEMPT3_FAILED_ROOT/raw/trial_15/trial_summary.json" ]] || { echo ATTEMPT3_EVIDENCE_FILE_MISSING >&2; exit 2; }
  [[ "$(sha256sum "$ATTEMPT3_FAILED_ROOT/launcher.log" | awk '{print $1}')" == "$ATTEMPT3_LAUNCHER_LOG_SHA256" ]] || { echo ATTEMPT3_ROOT_IDENTITY_MISMATCH >&2; exit 2; }
  [[ "$(sha256sum "$ATTEMPT3_FAILED_ROOT/raw/gpu_preflight.json" | awk '{print $1}')" == "$ATTEMPT3_PREFLIGHT_SHA256" ]] || { echo ATTEMPT3_ROOT_IDENTITY_MISMATCH >&2; exit 2; }
  [[ "$(sha256sum "$ATTEMPT3_FAILED_ROOT/raw/trial_15/trial_summary.json" | awk '{print $1}')" == "$ATTEMPT3_TRIAL15_SUMMARY_SHA256" ]] || { echo ATTEMPT3_ROOT_IDENTITY_MISMATCH >&2; exit 2; }
  [[ ! -e "$RESULT_ROOT" ]] || { echo RESULT_ROOT_ABSENT_CHECK_FAILED >&2; exit 2; }
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo TMUX_SESSION_ALREADY_EXISTS >&2
    exit 2
  fi
}

if [[ "${1:-}" == "--prelaunch-check-only" ]]; then
  guard_static_environment
  export CUDA_VISIBLE_DEVICES=1 PYTHONHASHSEED=0 PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
  "$PYTHON" "$RUNNER" --cpu-static-preflight --checkout "$CHECKOUT" --output-dir "$RESULT_ROOT"
  "$PYTHON" "$VALIDATOR" --repo-root "$CHECKOUT" --prelaunch-check-only
  echo PRELAUNCH_CHECK_ONLY_PASS
  exit 0
fi

guard_static_environment
export CUDA_VISIBLE_DEVICES=1 PYTHONHASHSEED=0 PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 CUBLAS_WORKSPACE_CONFIG=:4096:8
"$PYTHON" "$RUNNER" --cpu-static-preflight --checkout "$CHECKOUT" --output-dir "$RESULT_ROOT"
"$PYTHON" "$VALIDATOR" --repo-root "$CHECKOUT"
mkdir -p "$RESULT_ROOT"
LOG="$RESULT_ROOT/launcher.log"
COMMAND="cd '$CHECKOUT' && '$PYTHON' '$RUNNER' --gpu-preflight --checkout '$CHECKOUT' --output-dir '$RESULT_ROOT' && '$PYTHON' '$RUNNER' --batch --checkout '$CHECKOUT' --output-dir '$RESULT_ROOT'; rc=\$?; echo COLLECTION_COMPLETE_OR_STOPPED_REVIEW_BEFORE_ANY_SCIENTIFIC_ANALYSIS; exit \$rc"
tmux new-session -d -s "$SESSION" "exec >'$LOG' 2>&1; $COMMAND"
echo "STARTED_TMUX_SESSION=$SESSION"
