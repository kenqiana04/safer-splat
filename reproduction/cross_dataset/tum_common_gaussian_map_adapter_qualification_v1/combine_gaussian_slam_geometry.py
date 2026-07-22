"""Create task-owned geometry-only canonical concat in frozen native submap order."""
import argparse
from pathlib import Path
import numpy as np
p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
for name in ('means_world_m','scales_linear_m','quaternions_wxyz'):
    arrays=[np.load(a.input/f'submap_{i:02d}'/f'{name}.npy') for i in range(25)]
    np.save(a.output/f'{name}.npy',np.concatenate(arrays,axis=0),allow_pickle=False)
print(sum(len(np.load(a.input/f'submap_{i:02d}/means_world_m.npy',mmap_mode='r')) for i in range(25)))
