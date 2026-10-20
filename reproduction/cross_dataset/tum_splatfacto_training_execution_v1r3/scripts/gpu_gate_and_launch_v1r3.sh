#!/usr/bin/env bash
set -euo pipefail

WT=/disk1/zlab/formal_execution_worktrees/tum_splatfacto_training_execution_v1r3
ROOT=/disk1/zlab/formal_execution_records/tum_fr1_room_splatfacto_v1r3_seed20260716
PDIR=reproduction/cross_dataset/tum_splatfacto_training_protocol_v1
OUT=/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1/splatfacto/20260716_000000
SESSION=tum_fr1_room_splatfacto_v1r3_seed20260716
GPU_LOG=$ROOT/gpu_prelaunch_samples.txt
LAUNCH=$ROOT/launch_once.sh
LOG=$ROOT/training_stdout_stderr.log
EXIT_FILE=$ROOT/training_exit_code.txt
START_FILE=$ROOT/training_started_utc.txt
END_FILE=$ROOT/training_ended_utc.txt
INVOCATION_FILE=$ROOT/exact_invocation.txt

test -d "$ROOT" && test -w "$ROOT" && test -x "$ROOT"
grep -qx 'preflight_non_gpu_status=PASS' "$ROOT/non_gpu_preflight.log"
test ! -e "$OUT"
! tmux has-session -t "$SESSION" 2>/dev/null
test ! -e "$LAUNCH"
{
  echo '#!/usr/bin/env bash'
  echo 'set -o pipefail'
  printf 'date -u +%%FT%%TZ > %q\n' "$START_FILE"
  printf 'cd %q\n' "$WT"
  printf 'printf "%%s\\n" %q > %q\n' "bash $WT/$PDIR/exact_training_command.sh" "$INVOCATION_FILE"
  printf 'bash %q > %q 2>&1\n' "$WT/$PDIR/exact_training_command.sh" "$LOG"
} > "$LAUNCH"
chmod 700 "$LAUNCH"
printf 'preflight_status=PASS_READY_TO_LAUNCH_FORMAL_ATTEMPT\nattempt_count=0\n' > "$ROOT/preflight_launch_gate.txt"

sample() {
  tag=$1
  now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  raw=$(nvidia-smi -i 1 --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader,nounits 2>&1 || true)
  lines=$(printf '%s\n' "$raw" | grep -E '^[0-9]+,' || true)
  count=$(printf '%s\n' "$lines" | sed '/^$/d' | wc -l)
  gpu=$(nvidia-smi -i 1 --query-gpu=index,name,uuid,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu --format=csv,noheader)
  {
    printf 'sample=%s utc=%s compute_count=%s\n' "$tag" "$now" "$count"
    printf 'compute=%s\n' "$(printf '%s' "$lines" | tr '\n' ';')"
    printf 'gpu=%s\n' "$gpu"
  } | tee -a "$GPU_LOG"
  test "$count" -eq 0
}

sample T60
sleep 30
sample T30
sleep 30
sample T0

if ! tmux new-session -d -s "$SESSION" "bash '$LAUNCH'; rc=\$?; printf '%s\\n' \"\$rc\" > '$EXIT_FILE'; date -u +%FT%TZ > '$END_FILE'; exit \"\$rc\""; then
  printf 'status=BLOCKED_BY_LAUNCH_WRAPPER\nattempt_count=0\n' > "$ROOT/run_status.txt"
  exit 0
fi
for _ in $(seq 1 15); do
  PID=$(pgrep -n -f 'ns-train.*splatfacto' || true)
  if [ -n "$PID" ]; then
    printf 'status=FORMAL_ATTEMPT_STARTED\nattempt_count=1\ntmux_session=%s\nns_train_pid=%s\nstarted_utc=%s\n' \
      "$SESSION" "$PID" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$ROOT/run_status.txt"
    printf '%s\n' "$PID" > "$ROOT/ns_train_pid.txt"
    exit 0
  fi
  sleep 2
done
printf 'status=TMUX_STARTED_NS_TRAIN_NOT_OBSERVED\nattempt_count=0\ntmux_session=%s\n' "$SESSION" > "$ROOT/run_status.txt"
