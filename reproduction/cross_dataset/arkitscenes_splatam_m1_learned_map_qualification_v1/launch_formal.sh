#!/usr/bin/env bash
set -euo pipefail

ROOT=/disk1/zlab/maintenance_records/arkitscenes_splatam_m1_learned_map_qualification_v1
RUNTIME="$ROOT/runtime_checkout/SplaTAM-m1-empty-depth-safe"
ENV_PREFIX=/disk1/zlab/conda_envs/arkitscenes_splatam_canonical_v1
OVERLAY=/disk1/zlab/maintenance_records/arkitscenes_splatam_canonical_learned_map_qualification_v1/environment/runtime_overlay_setuptools_81_0_0
OUTPUT="$ROOT/outputs/ARKITSCENES_SPLATAM_M1_EMPTY_DEPTH_SAFE_GT_POSE_MAP_ONLY_V1"

test ! -e "$OUTPUT"
test ! -e "$ROOT/formal.pid"
test ! -e "$ROOT/formal_attempt_record.json"
(cd "$ROOT" && sha256sum -c execution_lock.sha256)
if nvidia-smi -i 1 --query-compute-apps=pid --format=csv,noheader,nounits | grep -q '[0-9]'; then
    echo "GPU 1 has a compute process; formal launch refused" >&2
    exit 71
fi

mkdir -p "$ROOT/logs" "$ROOT/events"
cd "$RUNTIME"
nohup env \
    CUDA_VISIBLE_DEVICES=1 \
    PYTHONNOUSERSITE=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="$RUNTIME:$OVERLAY" \
    SPLATAM_M1_EVENT_LOG="$ROOT/events/formal.jsonl" \
    SPLATAM_M1_INDEX_OFFSET=0 \
    "$ENV_PREFIX/bin/python" -u scripts/gaussian_splatting.py "$ROOT/config/formal.py" \
    > "$ROOT/logs/formal.log" 2>&1 < /dev/null &
PID=$!
printf '%s\n' "$PID" > "$ROOT/formal.pid"
"$ENV_PREFIX/bin/python" - "$ROOT" "$PID" <<'PY'
import datetime, hashlib, json, pathlib, sys
root = pathlib.Path(sys.argv[1]); pid = int(sys.argv[2])
lock = root / "execution_lock.json"
record = {
    "task": "ARKITSCENES_SPLATAM_M1_EMPTY_DEPTH_SAFE_GT_POSE_MAP_ONLY_V1",
    "attempt": 1,
    "pid": pid,
    "launched_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "execution_lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
    "physical_gpu": 1,
    "seed": 20260730,
    "train_frames": 214,
    "heldout_mapper_access_count": 0,
    "completed": False,
    "checkpoint": False,
}
(root / "formal_attempt_record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
PY
echo "FORMAL_PID=$PID"

