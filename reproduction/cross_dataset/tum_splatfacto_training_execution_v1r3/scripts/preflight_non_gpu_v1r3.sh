#!/usr/bin/env bash
set -euo pipefail

WT=/disk1/zlab/formal_execution_worktrees/tum_splatfacto_training_execution_v1r3
ROOT=/disk1/zlab/formal_execution_records/tum_fr1_room_splatfacto_v1r3_seed20260716
PROTO=6843fa477adc7f07acdfdb270ad7e4e3349da904
PDIR=reproduction/cross_dataset/tum_splatfacto_training_protocol_v1
EDIR=reproduction/cross_dataset/tum_splatfacto_training_execution_v1r3
DATA=/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room
OUT=/disk1/zlab/formal_splatfacto_runs/tum_fr1_room_splatfacto_v1/splatfacto/20260716_000000
LOG=$ROOT/non_gpu_preflight.log

exec > >(tee "$LOG") 2>&1
echo "preflight_started_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
test "$(hostname)" = zlab-Super-Server
test "$(git -C "$WT" rev-parse HEAD)" = 44d3c821e4036970c976d880703f50cf03a364f6
test -z "$(git -C "$WT" status --porcelain)"
test -d "$ROOT" && test -w "$ROOT" && test -x "$ROOT"

echo "command_blob=$(git -C "$WT" rev-parse "$PROTO:$PDIR/exact_training_command.sh")"
echo "config_blob=$(git -C "$WT" rev-parse "$PROTO:$PDIR/frozen_training_config.json")"
git -C "$WT" cat-file blob "$PROTO:$PDIR/exact_training_command.sh" | sha256sum
git -C "$WT" cat-file blob "$PROTO:$PDIR/frozen_training_config.json" | sha256sum
sha256sum "$WT/$PDIR/exact_training_command.sh" "$WT/$PDIR/frozen_training_config.json"
test "$(git -C "$WT" rev-parse "$PROTO:$PDIR/exact_training_command.sh")" = 1650b873e734d8fcdf56b8bc26fff48fdb2730ac
test "$(git -C "$WT" rev-parse "$PROTO:$PDIR/frozen_training_config.json")" = d3e0c104b37304278dd4074787d8781d2281a375
test "$(git -C "$WT" cat-file blob "$PROTO:$PDIR/exact_training_command.sh" | sha256sum | cut -d' ' -f1)" = 22d00fadea7eb1fb43556d4690c78113d317c6d144e96b6ad0d294d27a9369a4
test "$(git -C "$WT" cat-file blob "$PROTO:$PDIR/frozen_training_config.json" | sha256sum | cut -d' ' -f1)" = 0d15d8d6fa84049c6b4c34d6fdcaf77114f569c8d22ea9d010ae8144e6c924ea
test "$(sha256sum "$WT/$PDIR/exact_training_command.sh" | cut -d' ' -f1)" = 22d00fadea7eb1fb43556d4690c78113d317c6d144e96b6ad0d294d27a9369a4
test "$(sha256sum "$WT/$PDIR/frozen_training_config.json" | cut -d' ' -f1)" = 0d15d8d6fa84049c6b4c34d6fdcaf77114f569c8d22ea9d010ae8144e6c924ea
source ~/anaconda3/etc/profile.d/conda.sh
conda activate safer_splat_official
export CUDA_VISIBLE_DEVICES=1
export PYTHONDONTWRITEBYTECODE=1
python - "$WT/$PDIR/exact_training_command.sh" "$WT/$PDIR/frozen_training_config.json" <<'PY'
from pathlib import Path
import sys
for path in map(Path, sys.argv[1:]):
    data = path.read_bytes()
    assert b"\r\n" not in data
    assert data.endswith(b"\n")
    print(f"{path.name}_crlf_count=0")
    print(f"{path.name}_final_newline=true")
PY
git -C "$WT" check-attr eol -- "$PDIR/exact_training_command.sh" "$PDIR/frozen_training_config.json"
python - "$DATA" "$WT/$PDIR/frozen_training_config.json" <<'PY'
import importlib.metadata as metadata
import json
from pathlib import Path
import torch
from nerfstudio.data.dataparsers.nerfstudio_dataparser import NerfstudioDataParserConfig

data = Path(__import__('sys').argv[1])
frozen = json.loads(Path(__import__('sys').argv[2]).read_text())
assert torch.__version__ == '2.1.2+cu118'
assert torch.version.cuda == '11.8'
assert metadata.version('nerfstudio') == '1.1.5'
assert metadata.version('gsplat') == '1.4.0'
assert torch.cuda.is_available()
assert frozen['method'] == 'splatfacto'
assert frozen['seed'] == 20260716
assert frozen['max_num_iterations'] == 30000
assert frozen['mixed_precision'] is False and frozen['use_grad_scaler'] is False
assert frozen['steps_per_save'] == 2000
assert frozen['steps_per_eval_image'] == 100 and frozen['steps_per_eval_batch'] == 0 and frozen['steps_per_eval_all_images'] == 1000
d = frozen['dataset']
assert (d['source_frame_count'], d['train_frame_count'], d['eval_frame_count'], d['frame_drop_count']) == (300, 240, 60, 0)
assert d['orientation_method'] == 'none' and d['center_method'] == 'none'
assert d['auto_scale_poses'] is False and d['dataparser_scale'] == 1.0
assert d['depth_unit_scale_factor_meters'] == 0.0002 and d['freiburg1_correction_preapplied'] is True
cfg = NerfstudioDataParserConfig(data=data, orientation_method='none', center_method='none', auto_scale_poses=False, downscale_factor=1, eval_mode='fraction', train_split_fraction=0.8, depth_unit_scale_factor=0.0002)
parser = cfg.setup()
train = parser.get_dataparser_outputs(split='train')
val = parser.get_dataparser_outputs(split='val')
identity = torch.eye(4, dtype=train.dataparser_transform.dtype)[:3]
assert len(train.image_filenames) == 240 and len(val.image_filenames) == 60
assert tuple(train.dataparser_transform.shape) == (3, 4)
assert torch.allclose(train.dataparser_transform, identity)
print('python=3.10.20')
print('torch=' + torch.__version__)
print('cuda=' + str(torch.version.cuda))
print('nerfstudio=' + metadata.version('nerfstudio'))
print('gsplat=' + metadata.version('gsplat'))
print('visible_gpu=' + torch.cuda.get_device_name(0))
print('dataparser_train=240')
print('dataparser_val=60')
print('dataparser_transform_shape=[3,4]')
print('dataparser_transform_identity=true')
print('model_trainer_optimizer_created=false')
PY
test "$(nvidia-smi -i 1 --query-gpu=uuid --format=csv,noheader)" = GPU-78ef17e4-66cc-4a58-fe43-67d31be8981d
echo "visible_uuid=$(nvidia-smi -i 1 --query-gpu=uuid --format=csv,noheader)"
test "$(sha256sum "$DATA/transforms.json" | cut -d' ' -f1)" = b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a
echo "transforms_sha256=$(sha256sum "$DATA/transforms.json" | cut -d' ' -f1)"
test ! -e "$OUT"
echo "output_absent=true"
python - <<'PY'
import shutil
free = shutil.disk_usage('/disk1').free
assert free >= 20 * 1024**3
print('disk_free_gib=' + str(free // 1024**3))
PY
bash -n "$WT/$PDIR/exact_training_command.sh"
bash -n "$WT/$EDIR/exact_execution_invocation.sh"
bash -n "$WT/$EDIR/exact_post_training_commands.sh"
ns-train --help >/dev/null
ns-train splatfacto --help >/dev/null
ns-eval --help >/dev/null
timeout 30s ns-render dataset --help >/dev/null
! tmux has-session -t tum_fr1_room_splatfacto_v1r3_seed20260716 2>/dev/null
echo "preflight_non_gpu_status=PASS"
echo "preflight_finished_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
