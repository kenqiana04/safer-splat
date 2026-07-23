#!/usr/bin/env bash
set -euo pipefail
cd /disk1/zlab/projects/safer-splat
export CUDA_VISIBLE_DEVICES=1
export PYTHONNOUSERSITE=1
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=/disk1/zlab/runtime_overlays/tum_splatfacto_gsplat_prebuilt_v1/gsplat_1_4_0_pt21cu118:/disk1/zlab/runtime_overlays/tum_splatfacto_pkgresources_v1/setuptools_81_0_0
export LD_LIBRARY_PATH=/disk1/zlab/conda_envs/safer_splat_official/lib/python3.10/site-packages/torch/lib:/disk1/zlab/conda_envs/safer_splat_official/lib:${LD_LIBRARY_PATH-}
/disk1/zlab/conda_envs/safer_splat_official/bin/python - <<'PY'
import json, sys, torch
import splat.distances as distances
import splat.gsplat_utils as gsplat_utils
import cbf.cbf_utils as cbf_utils
print('python', sys.executable)
print('torch', torch.__version__, torch.version.cuda, torch.cuda.is_available(), torch.cuda.get_device_name(0))
print('distances', distances.__file__)
print('gsplat_utils', gsplat_utils.__file__)
print('cbf_utils', cbf_utils.__file__)
with open('reproduction/cross_dataset/safer_world_frame_stable_ellipsoid_hessian_runtime_correction_v1/SAFER_ELLIPSOID_QUERY_NUMERICAL_CONTRACT_V2.json', encoding='utf-8') as handle:
    contract = json.load(handle)
for key in ('version', 'gradient', 'hessian_frame', 'sign_reflection', 'stable_diagonal', 'static_audit_authorized'):
    print(key, contract.get(key))
PY
