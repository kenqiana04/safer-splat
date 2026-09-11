#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <repo_checkout> <control_dir> <result_dir> [session_name]" >&2
  exit 2
fi

REPO="$(readlink -f "$1")"
CONTROL="$(readlink -f "$2")"
RESULT="$(mkdir -p "$3" && readlink -f "$3")"
SESSION="${4:-safer_formal_v2}"
PY="/disk1/zlab/conda_envs/safer_splat_official/bin/python"
RUNNER="$CONTROL/run_formal_paired_experiment_v2.py"

export CUDA_VISIBLE_DEVICES=1
export PYTHONHASHSEED=0
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export CUBLAS_WORKSPACE_CONFIG=:4096:8

"$PY" "$RUNNER" --checkout "$REPO" --control-dir "$CONTROL" --result-dir "$RESULT" --preflight
"$PY" "$RUNNER" --checkout "$REPO" --control-dir "$CONTROL" --result-dir "$RESULT" --build-difficulty

if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "tmux session already exists: $SESSION" >&2
  exit 2
fi

CMD="cd '$CONTROL' && '$PY' '$RUNNER' --checkout '$REPO' --control-dir '$CONTROL' --result-dir '$RESULT' --run 2>&1 | tee -a '$RESULT/formal_collection.log'"
tmux new-session -d -s "$SESSION" "$CMD"

echo "Started: $SESSION"
echo "Attach: tmux attach -t $SESSION"
echo "Status: $PY $RUNNER --checkout $REPO --control-dir $CONTROL --result-dir $RESULT --status"
