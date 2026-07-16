#!/usr/bin/env bash
set -euo pipefail

SERVER_WORKTREE=/disk1/zlab/formal_execution_worktrees/tum_splatfacto_training_execution_v1
PROTOCOL_DIR="$SERVER_WORKTREE/reproduction/cross_dataset/tum_splatfacto_training_protocol_v1"
EXECUTION_RECORD_ROOT=/disk1/zlab/formal_execution_records/tum_fr1_room_splatfacto_v1_seed20260716
LOG="$EXECUTION_RECORD_ROOT/training_stdout_stderr.log"
EXIT_FILE="$EXECUTION_RECORD_ROOT/training_exit_code.txt"
START_FILE="$EXECUTION_RECORD_ROOT/training_started_utc.txt"
END_FILE="$EXECUTION_RECORD_ROOT/training_ended_utc.txt"

mkdir -p "$EXECUTION_RECORD_ROOT"
date -u +%FT%TZ > "$START_FILE"
cd "$SERVER_WORKTREE"
set +e
bash "$PROTOCOL_DIR/exact_training_command.sh" > "$LOG" 2>&1
rc=$?
set -e
printf '%s\n' "$rc" > "$EXIT_FILE"
date -u +%FT%TZ > "$END_FILE"
exit "$rc"
