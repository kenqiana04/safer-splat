#!/usr/bin/env bash
set -u
source ~/anaconda3/etc/profile.d/conda.sh
conda activate safer_splat_official

echo '===== ENVIRONMENT COMPLETION ====='
python - <<'PY'
import importlib.metadata as metadata
import torch
print("nerfstudio=" + metadata.version("nerfstudio"))
print("gsplat=" + metadata.version("gsplat"))
print("torch=" + torch.__version__)
print("cuda=" + str(torch.version.cuda))
print("cuda_available=" + str(torch.cuda.is_available()).lower())
print("visible_device=" + torch.cuda.get_device_name(0))
PY

echo '===== CLI COMPLETION ====='
timeout 30s ns-render dataset --help >/dev/null
echo "ns_render_dataset_help_exit=$?"

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
echo '===== REMAINING PREFLIGHT END ====='
