#!/usr/bin/env bash
set -u
REPO=/disk1/zlab/projects/safer-splat
WT=/disk1/zlab/formal_execution_worktrees/tum_splatfacto_training_execution_v1r2
BRANCH=tum-splatfacto-training-execution-v1r2
AUTH=e44fbdbcda393cd9ab2f63f55d57a0aa922d8e7e
PROTO=6843fa477adc7f07acdfdb270ad7e4e3349da904
PDIR=reproduction/cross_dataset/tum_splatfacto_training_protocol_v1
CMD=$PDIR/exact_training_command.sh
CFG=$PDIR/frozen_training_config.json
DATA=/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room
OUT=/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1/splatfacto/20260716_000000

echo '===== WORKTREE ====='
hostname
if [ -e "$WT" ]; then
  echo 'worktree_absent_at_recovered_preflight=false'
  echo "worktree_reused_after_transport_truncation=$(test "$(git -C "$WT" rev-parse HEAD)" = "$AUTH" && echo true || echo false)"
else
  echo 'worktree_absent_at_recovered_preflight=true'
  git -C "$REPO" fetch origin "$BRANCH"
  git -C "$REPO" worktree add --detach "$WT" "origin/$BRANCH"
fi
echo "worktree_head=$(git -C "$WT" rev-parse HEAD)"
echo "worktree_clean=$(test -z "$(git -C "$WT" status --porcelain)" && echo true || echo false)"
echo "auth_head_match=$(test "$(git -C "$WT" rev-parse HEAD)" = "$AUTH" && echo true || echo false)"
echo "protocol_commit_present=$(git -C "$WT" cat-file -e "$PROTO^{commit}" 2>/dev/null && echo true || echo false)"

echo '===== CANONICAL IDENTITY ====='
echo "command_blob=$(git -C "$WT" rev-parse "$PROTO:$CMD")"
echo "config_blob=$(git -C "$WT" rev-parse "$PROTO:$CFG")"
echo "command_blob_sha256=$(git -C "$WT" cat-file blob "$PROTO:$CMD" | sha256sum | awk '{print $1}')"
echo "config_blob_sha256=$(git -C "$WT" cat-file blob "$PROTO:$CFG" | sha256sum | awk '{print $1}')"
echo "command_checkout_sha256=$(sha256sum "$WT/$CMD" | awk '{print $1}')"
echo "config_checkout_sha256=$(sha256sum "$WT/$CFG" | awk '{print $1}')"
echo "command_crlf_count=$(grep -a -o $'\r' "$WT/$CMD" | wc -l)"
echo "config_crlf_count=$(grep -a -o $'\r' "$WT/$CFG" | wc -l)"
echo "command_final_newline=$(tail -c 1 "$WT/$CMD" | od -An -t x1 | tr -d ' ' | grep -qx 0a && echo true || echo false)"
echo "config_final_newline=$(tail -c 1 "$WT/$CFG" | od -An -t x1 | tr -d ' ' | grep -qx 0a && echo true || echo false)"
git -C "$WT" check-attr eol -- "$CMD" "$CFG"
echo "transforms_sha256=$(sha256sum "$DATA/transforms.json" | awk '{print $1}')"

echo '===== ENVIRONMENT ====='
source ~/anaconda3/etc/profile.d/conda.sh
conda activate safer_splat_official
echo "conda_env=$CONDA_DEFAULT_ENV"
python --version
python - <<'PY'
import torch, nerfstudio, gsplat
print("torch="+torch.__version__)
print("cuda="+str(torch.version.cuda))
print("nerfstudio="+nerfstudio.__version__)
print("gsplat="+gsplat.__version__)
print("cuda_available="+str(torch.cuda.is_available()).lower())
print("visible_device="+torch.cuda.get_device_name(0))
print("visible_uuid="+torch.cuda.get_device_properties(0).uuid)
PY

echo '===== DATAPARSER ONLY ====='
python - "$WT/$CFG" <<'PY'
import json, sys
c=json.load(open(sys.argv[1]))
d=c["dataset"]
checks={
 "method":c["method"]=="splatfacto","seed":c["seed"]==20260716,
 "iterations":c["max_num_iterations"]==30000,"frames":d["source_frame_count"]==300,
 "train":d["train_frame_count"]==240,"val":d["eval_frame_count"]==60,
 "drop":d["frame_drop_count"]==0,"orient":d["orientation_method"]=="none",
 "center":d["center_method"]=="none","auto_scale":d["auto_scale_poses"] is False,
 "parser_scale":d["dataparser_scale"]==1.0,"depth":d["depth_unit_scale_factor_meters"]==0.0002,
 "freiburg_correction":d["freiburg1_correction_preapplied"] is True,
 "resume":c["resume_allowed"] is False,"mixed_precision":c["mixed_precision"] is False,
 "grad_scaler":c["use_grad_scaler"] is False,"eval_image":c["steps_per_eval_image"]==100,
 "eval_all":c["steps_per_eval_all_images"]==1000,"eval_batch":c["steps_per_eval_batch"]==0,
 "save":c["steps_per_save"]==2000,"vis":c["vis"]=="tensorboard"
}
print("dataparser_checks="+json.dumps(checks,sort_keys=True))
print("dataparser_pass="+str(all(checks.values())).lower())
PY

echo '===== OUTPUT AND DISK ====='
echo "output_absent=$(test ! -e "$OUT" && echo true || echo false)"
df -BG "$OUT" 2>/dev/null || df -BG /disk1

echo '===== CLI ====='
bash -n "$WT/$CMD"; echo "bash_protocol=true"
bash -n "$WT/reproduction/cross_dataset/tum_splatfacto_training_execution_v1r2/exact_execution_invocation.sh"; echo "bash_invocation=true"
bash -n "$WT/reproduction/cross_dataset/tum_splatfacto_training_execution_v1r2/exact_post_training_commands.sh"; echo "bash_post=true"
ns-train --help >/dev/null && echo "ns_train_help=true" || echo "ns_train_help=false"
ns-train splatfacto --help >/dev/null && echo "ns_train_splatfacto_help=true" || echo "ns_train_splatfacto_help=false"
ns-eval --help >/dev/null && echo "ns_eval_help=true" || echo "ns_eval_help=false"
ns-render dataset --help >/dev/null && echo "ns_render_dataset_help=true" || echo "ns_render_dataset_help=false"

sample() {
  tag=$1
  now=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  raw=$(nvidia-smi -i 1 --query-compute-apps=pid,process_name,used_gpu_memory --format=csv,noheader,nounits 2>&1 || true)
  lines=$(printf '%s\n' "$raw" | grep -E '^[0-9]+,' || true)
  count=$(printf '%s\n' "$lines" | sed '/^$/d' | wc -l)
  util=$(nvidia-smi -i 1 --query-gpu=utilization.gpu,memory.used --format=csv,noheader,nounits)
  printf 'gpu_sample_%s_utc=%s\n' "$tag" "$now"
  printf 'gpu_sample_%s_compute_count=%s\n' "$tag" "$count"
  printf 'gpu_sample_%s_compute=%s\n' "$tag" "$(printf '%s' "$lines" | tr '\n' ';')"
  printf 'gpu_sample_%s_util_memory=%s\n' "$tag" "$util"
  nvidia-smi pmon -i 1 -c 1 || true
}
echo '===== GPU SAMPLE T60 ====='
sample T60
sleep 30
echo '===== GPU SAMPLE T30 ====='
sample T30
sleep 30
echo '===== GPU SAMPLE T0 ====='
sample T0
echo '===== PREFLIGHT END ====='
