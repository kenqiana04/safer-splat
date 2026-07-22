"""One-point read-only capacity probe for the unchanged SAFER h implementation."""
import json
import time
from pathlib import Path
import numpy as np
import torch
from splat.gsplat_utils import DummyGSplatLoader

root = Path('/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/splatam/canonical_export/export_a')
loader = DummyGSplatLoader('cuda:0')
loader.initialize_attributes(torch.from_numpy(np.load(root / 'means_world_m.npy')), torch.from_numpy(np.load(root / 'quaternions_wxyz.npy')), torch.from_numpy(np.load(root / 'scales_linear_m.npy')))
point = torch.zeros(3, device='cuda:0')
start = time.perf_counter()
h, _, _, _ = loader.query_distance(point, distance_type='ball-to-ellipsoid', radius=0.0)
torch.cuda.synchronize()
print(json.dumps({'gaussian_count': int(h.numel()), 'seconds': time.perf_counter()-start, 'min_h': float(h.min()), 'peak_memory_bytes': int(torch.cuda.max_memory_allocated())}, sort_keys=True))
