#!/usr/bin/env bash
set -euo pipefail

WT=/disk1/zlab/formal_execution_worktrees/tum_splatfacto_training_execution_v1r2
PDIR=reproduction/cross_dataset/tum_splatfacto_training_protocol_v1
OUT=/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1/splatfacto/20260716_000000
REC=/disk1/zlab/formal_execution_records/tum_fr1_room_splatfacto_v1r2_seed20260716
SESSION=tum_fr1_room_splatfacto_v1r2_seed20260716
LOG=/tmp/tum_splatfacto_training_execution_v1r2_gpu_gate.log

exec > >(tee -a "$LOG") 2>&1
echo "gate_started_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
test "$(git -C "$WT" rev-parse HEAD)" = e44fbdbcda393cd9ab2f63f55d57a0aa922d8e7e
test -z "$(git -C "$WT" status --porcelain)"
test ! -e "$OUT"
test ! -e "$REC"
! tmux has-session -t "$SESSION" 2>/dev/null

sample() {
  tag=$1
  now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  raw=$(nvidia-smi -i 1 --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader,nounits 2>&1 || true)
  lines=$(printf '%s\n' "$raw" | grep -E '^[0-9]+,' || true)
  count=$(printf '%s\n' "$lines" | sed '/^$/d' | wc -l)
  util=$(nvidia-smi -i 1 --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits)
  printf 'gpu_gate_%s_utc=%s\n' "$tag" "$now"
  printf 'gpu_gate_%s_compute_count=%s\n' "$tag" "$count"
  printf 'gpu_gate_%s_compute=%s\n' "$tag" "$(printf '%s' "$lines" | tr '\n' ';')"
  printf 'gpu_gate_%s_util_memory=%s\n' "$tag" "$util"
  nvidia-smi pmon -i 1 -c 1 || true
  test "$count" -eq 0
}

sample T60
sleep 30
sample T30
sleep 30
sample T0

mkdir "$REC"
printf '{"status":"PASS_READY_TO_LAUNCH_FORMAL_ATTEMPT","attempt_count":0,"third_idle_sample_utc":"%s"}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$REC/prelaunch_status.json"
{
  echo '#!/usr/bin/env bash'
  echo 'set -uo pipefail'
  printf 'cd %q\n' "$WT"
  printf 'export PROTOCOL_DIR=%q\n' "$WT/$PDIR"
  printf 'exec bash %q\n' "$WT/reproduction/cross_dataset/tum_splatfacto_training_execution_v1r2/exact_execution_invocation.sh"
} > "$REC/launch_once.sh"
chmod 700 "$REC/launch_once.sh"
tmux new-session -d -s "$SESSION" "bash '$REC/launch_once.sh' >> '$REC/training_stdout_stderr.log' 2>&1; rc=\$?; printf '{\\\"exit_code\\\":%s,\\\"ended_utc\\\":\\\"%s\\\"}\\n' \"\$rc\" \"\$(date -u +%Y-%m-%dT%H:%M:%SZ)\" > '$REC/training_exit_status.json'"
printf '{"status":"TMUX_STARTED_AWAITING_NS_TRAIN_OBSERVATION","attempt_count":0,"tmux_session":"%s","started_utc":"%s"}\n' \
  "$SESSION" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$REC/run_status.json"
for i in 1 2 3 4 5 6; do
  PID=$(pgrep -n -f 'ns-train splatfacto' || true)
  if [ -n "$PID" ]; then
    printf '{"status":"FORMAL_ATTEMPT_STARTED","attempt_count":1,"ns_train_pid":%s,"observed_utc":"%s"}\n' \
      "$PID" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$REC/training_process_record.json"
    printf '{"status":"FORMAL_ATTEMPT_STARTED","attempt_count":1,"tmux_session":"%s","ns_train_pid":%s,"started_utc":"%s"}\n' \
      "$SESSION" "$PID" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$REC/run_status.json"
    echo "launch_result=FORMAL_ATTEMPT_STARTED pid=$PID"
    exit 0
  fi
  sleep 2
done
printf '{"status":"TMUX_STARTED_NS_TRAIN_NOT_OBSERVED","attempt_count":0,"tmux_session":"%s"}\n' "$SESSION" > "$REC/run_status.json"
echo 'launch_result=TMUX_STARTED_NS_TRAIN_NOT_OBSERVED'
exit 0
