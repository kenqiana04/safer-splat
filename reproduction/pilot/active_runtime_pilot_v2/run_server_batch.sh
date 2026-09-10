#!/usr/bin/env bash
set -u

ROOT=/disk1/zlab/maintenance_records/active_runtime_pilot_v2
EXEC="$ROOT/server_execution"
SRC=/disk1/zlab/maintenance_records/active_runtime_smoke_v2/source_checkout

echo $$ > "$EXEC/scheduler_pid.txt"
/disk1/zlab/conda_envs/safer_splat_official/bin/python \
  "$ROOT/harness/run_active_runtime_pilot_v2.py" \
  --all \
  --checkout "$SRC" \
  --output-dir "$EXEC" \
  > "$EXEC/full.log" 2>&1
rc=$?
echo "$rc" > "$EXEC/batch_exit_code.txt"
exit "$rc"
