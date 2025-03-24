# Interactive Open3D visualization of a list of voxel grids loaded
# from a folder of .ply files. The voxel grids are visualized one at
# a time, and the user can cycle through them using the left and right
# arrow keys. 

import open3d as o3d
from pathlib import Path

ply_folder = Path('voxels')
vox_files = list(ply_folder.glob('*.ply'))
vox_files.sort()

voxel_grids = [o3d.io.read_voxel_grid(str(f)) for f in vox_files]
n_grids = len(voxel_grids)
print(f'Loaded {n_grids} voxel grids.')

def key_callback(vis):
    global idx
    global voxel_grids
    global n_grids
    global vox_files

    if vis.get_key() == 262: # Right arrow key
        idx = (idx + 1) % n_grids
        print(f'Loading voxel grid {idx + 1}/{n_grids} from {vox_files[idx]}')
        vis.clear_geometries()
        vis.add_geometry(voxel_grids[idx])

    elif vis.get_key() == 263: # Left arrow key
        idx = (idx - 1) % n_grids
        print(f'Loading voxel grid {idx + 1}/{n_grids} from {vox_files[idx]}')
        vis.clear_geometries()
        vis.add_geometry(voxel_grids[idx])

    return False

idx = 0
vis = o3d.visualization.Visualizer()
vis.create_window()
vis.register_key_callback(262, key_callback)
vis.register_key_callback(263, key_callback)
vis.add_geometry(voxel_grids[idx])
vis.run()
vis.destroy_window()
