from typing import List, Tuple
from pathlib import Path
import open3d as o3d
import torch
from torch import Tensor
import shutil
import time

from rich.console import Console

CONSOLE = Console(width=90)


class VisibilityGrid:
    def __init__(
        self,
        voxel_size: float,
        bounds: List[List[float]],
    ):
        self.voxel_size = voxel_size
        self.bounds = torch.tensor(bounds)

        resolutions = [int((bound[1] - bound[0]) / voxel_size) for bound in bounds]
        self.occ_counts = torch.zeros(resolutions, dtype=torch.int16)
        self.colors = torch.zeros(resolutions + [3], dtype=torch.float32)
        self.emp_counts = torch.zeros(resolutions, dtype=torch.int16)
        self.dir_means = torch.zeros(resolutions + [3], dtype=torch.float16)
        self.dir_vars = torch.zeros(resolutions + [3], dtype=torch.float16)
        self.shape = self.occ_counts.shape

    def get_voxels(self, points: Tensor) -> Tensor:
        voxel_indices = ((points - self.bounds[:, 0]) / self.voxel_size).long()
        return voxel_indices

    def update(self, points: Tensor, colors: Tensor, directions: Tensor):
        occ_inds = self.get_voxels(points)
        # Insane tech to add with repeated indices
        # values = torch.ones(1, dtype=torch.int16).expand(occ_inds.shape[0])
        # occ_inds = (occ_inds[:, 0], occ_inds[:, 1], occ_inds[:, 2])
        # self.occ_counts.index_put_(occ_inds, values, accumulate=True)
        for i, occ_ind in enumerate(occ_inds):
            self.occ_counts[occ_ind[0], occ_ind[1], occ_ind[2]] += 1
            self.colors[occ_ind[0], occ_ind[1], occ_ind[2], ...] = colors[i]
            self.dir_means[occ_ind[0], occ_ind[1], occ_ind[2], ...] += directions[i]

        mask = self.occ_counts > 0
        self.dir_means[mask] /= self.occ_counts[mask].unsqueeze(-1)
        for i, occ_ind in enumerate(occ_inds):
            self.dir_vars[occ_ind[0], occ_ind[1], occ_ind[2], ...] += (
                directions[i] - self.dir_means[occ_ind[0], occ_ind[1], occ_ind[2]]
            ) ** 2
        self.dir_vars[mask] /= self.occ_counts[mask].unsqueeze(-1)
        self.dir_vars[mask] = torch.sqrt(self.dir_vars[mask])

    def convert_to_o3d(self, occ_thresh: int = 1, occ_var_thresh: float = 0.1):
        CONSOLE.print("Converting to Open3D VoxelGrid.")
        mask_occ = self.occ_counts > occ_thresh
        n_occ = mask_occ.sum()
        CONSOLE.print(f"Occupied voxels: {n_occ}.")
        mask_l1 = torch.norm(self.dir_vars, p=1, dim=-1) > occ_var_thresh
        mask = mask_occ & mask_l1
        n_occ_l1 = mask.sum()
        CONSOLE.print(
            f"Occupied voxels with L1 dir variance > {occ_var_thresh}: {n_occ_l1}."
        )
        occ_voxels = mask.nonzero(as_tuple=False)
        occ_points = (occ_voxels.float() + 0.5) * self.voxel_size + self.bounds[:, 0]
        occ_colors = self.colors[occ_voxels[:, 0], occ_voxels[:, 1], occ_voxels[:, 2]]
        occ_pcd = o3d.geometry.PointCloud()
        occ_pcd.points = o3d.utility.Vector3dVector(occ_points)
        occ_pcd.colors = o3d.utility.Vector3dVector(occ_colors)
        voxel_grid = o3d.geometry.VoxelGrid.create_from_point_cloud(
            occ_pcd, self.voxel_size
        )
        return voxel_grid


if __name__ == "__main__":
    pcd_path = Path(
        "../outputs/configs/ros-dff-nerfacto/2024-09-03_093015/pointclouds/pcd_4050.pt"
    )
    bounds = [[-4, 4], [-4, 4], [-1.0, 2.0]]
    pcd = torch.load(pcd_path)
    occ_threshes = [1, 2, 5]
    occ_var_threshes = [0.1, 0.2, 0.5]

    vg = VisibilityGrid(0.1, bounds)

    # Filter Point Cloud
    n_raw = pcd.shape[0]
    maskx = (pcd[:, 0] > bounds[0][0]) & (pcd[:, 0] < bounds[0][1])
    masky = (pcd[:, 1] > bounds[1][0]) & (pcd[:, 1] < bounds[1][1])
    maskz = (pcd[:, 2] > bounds[2][0]) & (pcd[:, 2] < bounds[2][1])
    mask = maskx & masky & maskz
    pcd = pcd[mask]
    n_filtered = pcd.shape[0]
    CONSOLE.print(f"Filtered {n_raw - n_filtered} points. Remaining: {n_filtered}.")

    xyzs = pcd[:, :3]
    rgbs = pcd[:, 3:6]
    origins = pcd[:, 7:10]
    directions = torch.nn.functional.normalize(xyzs - origins, p=2, dim=-1)

    start = time.time()
    vg.update(xyzs, rgbs, directions)
    end = time.time()
    CONSOLE.print(f"Voxelization took {end - start} seconds.")

    out_path = Path("../outputs/latest/")
    out_path.mkdir(parents=True, exist_ok=True)

    for occ_thresh in occ_threshes:
        for occ_var_thresh in occ_var_threshes:
            CONSOLE.print(
                f"Converting to Open3D VoxelGrid with thresholds {occ_thresh} and {occ_var_thresh}."
            )
            o3d_vox = vg.convert_to_o3d(occ_thresh, occ_var_thresh)
            out_fname = out_path / f"voxel_grid_{occ_thresh}_{occ_var_thresh}.ply"
            o3d.io.write_voxel_grid(out_fname.as_posix(), o3d_vox)
