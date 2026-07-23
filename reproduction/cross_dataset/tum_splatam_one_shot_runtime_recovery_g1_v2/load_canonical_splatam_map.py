#!/usr/bin/env python3
import gc, json, os, time
from pathlib import Path
import numpy as np
import torch
from ellipsoids.covariance_utils import compute_cov

ROOT=Path('/disk1/zlab/maintenance_records/tum_splatam_one_shot_runtime_recovery_g1_v2/resumed_map')
BASE=Path('/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/splatam/canonical_export/export_a')
N=5464102
def one(label):
 t=time.perf_counter(); arrays={k:np.load(BASE/f'{k}.npy',mmap_mode='r') for k in ('means_world_m','scales_linear_m','quaternions_wxyz','opacities_activated','source_index','source_submap_index')}; read=time.perf_counter()-t
 assert arrays['means_world_m'].shape==(N,3) and arrays['scales_linear_m'].shape==(N,3) and arrays['quaternions_wxyz'].shape==(N,4)
 assert np.isfinite(arrays['means_world_m']).all() and np.isfinite(arrays['scales_linear_m']).all() and (arrays['scales_linear_m']>0).all() and np.isfinite(arrays['quaternions_wxyz']).all()
 torch.cuda.reset_peak_memory_stats(); t=time.perf_counter()
 means=torch.from_numpy(arrays['means_world_m']).to('cuda:0'); scales=torch.from_numpy(arrays['scales_linear_m']).to('cuda:0'); rots=torch.from_numpy(arrays['quaternions_wxyz']).to('cuda:0')
 covs=compute_cov(rots,scales); covs_inv=compute_cov(rots,1/scales)
 init=time.perf_counter()-t; out={'label':label,'count':int(means.shape[0]),'bbox_min':means.amin(0).tolist(),'bbox_max':means.amax(0).tolist(),'cov_finite':bool(torch.isfinite(covs).all() and torch.isfinite(covs_inv).all()),'cpu_read_s':read,'gpu_init_s':init,'peak_allocated':torch.cuda.max_memory_allocated(),'peak_reserved':torch.cuda.max_memory_reserved()}
 del means,scales,rots,covs,covs_inv,arrays; t=time.perf_counter(); gc.collect(); torch.cuda.empty_cache(); out['unload_s']=time.perf_counter()-t; return out
ROOT.mkdir(parents=True,exist_ok=True); a=one('LOAD_A'); b=one('LOAD_B'); result={'status':'PASS' if a['count']==b['count'] and a['bbox_min']==b['bbox_min'] and a['bbox_max']==b['bbox_max'] and a['cov_finite'] and b['cov_finite'] else 'FAIL','load_a':a,'load_b':b}; (ROOT/'map_load_summary.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result))
