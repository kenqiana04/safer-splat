"""Task-owned native-render parity for frozen external Gaussian maps."""
from __future__ import annotations
import argparse, json
from pathlib import Path

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True); path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")

def splatam(repo: Path, params_path: Path, adapter: Path, train_adapter: Path, canonical_root: Path, output: Path) -> dict:
    import sys, numpy as np, torch
    sys.path.insert(0, str(repo)); torch._C._jit_set_profiling_executor(False); torch._C._jit_set_profiling_mode(False); torch._C._jit_override_can_fuse_on_gpu(False)
    from datasets.gradslam_datasets import TUMDataset, load_dataset_config
    from diff_gaussian_rasterization import GaussianRasterizer as Renderer
    from utils.gs_helpers import params2rendervar, params2depthplussilhouette
    from utils.recon_helpers import setup_camera
    raw = np.load(params_path); original = {k: torch.tensor(raw[k], dtype=torch.float32, device="cuda:0") for k in raw.files if k not in {"intrinsics", "w2c", "org_width", "org_height", "gt_w2c_all_frames"}}
    canonical = {k: v.clone() for k, v in original.items()}
    means=np.load(canonical_root / "means_world_m.npy"); scales=np.load(canonical_root / "scales_linear_m.npy"); quats=np.load(canonical_root / "quaternions_wxyz.npy"); opacity=np.load(canonical_root / "opacities_activated.npy"); colors=np.load(canonical_root / "colors_or_sh.npy")
    canonical["means3D"]=torch.from_numpy(means).cuda(); canonical["log_scales"]=torch.log(torch.from_numpy(scales[:, :1] if original["log_scales"].shape[1]==1 else scales)).cuda(); canonical["unnorm_rotations"]=torch.from_numpy(quats).cuda(); canonical["logit_opacities"]=torch.logit(torch.from_numpy(opacity).cuda().clamp(1e-7,1-1e-7)); canonical["rgb_colors"]=torch.from_numpy(colors).cuda()
    cfg = load_dataset_config(repo / "configs/data/TUM/freiburg1_room.yaml")
    data = TUMDataset(cfg, str(adapter.parent), adapter.name, start=0, end=-1, stride=1, desired_height=480, desired_width=640, device="cuda:0", relative_pose=True)
    train = TUMDataset(cfg, str(train_adapter.parent), train_adapter.name, start=0, end=-1, stride=1, desired_height=480, desired_width=640, device="cuda:0", relative_pose=True); rows=[]
    with torch.no_grad():
        for split, dataset, indices in (("train",train,(0,79,159,239)),("eval",data,(1,9,17,25,33,41,49,57))):
            for index in indices:
                color, _, intrinsics, pose = dataset[index]; w2c=torch.linalg.inv(pose); camera=setup_camera(color.shape[2], color.shape[1], intrinsics[:3,:3].cpu().numpy(), w2c.cpu().numpy())
                a=Renderer(raster_settings=camera)(**params2rendervar(original))[0]; b=Renderer(raster_settings=camera)(**params2rendervar(canonical))[0]
                da=Renderer(raster_settings=camera)(**params2depthplussilhouette(original,w2c))[0]; db=Renderer(raster_settings=camera)(**params2depthplussilhouette(canonical,w2c))[0]
                rows.append({"split":split,"index":index,"rgb_max_abs":float((a-b).abs().max()),"depth_max_abs":float((da[0]-db[0]).abs().max()),"alpha_max_abs":float((da[1]-db[1]).abs().max()),"depth_valid_mask_exact":bool(torch.equal(da[0]>0,db[0]>0)),"alpha_mask_exact":bool(torch.equal(da[1]>0,db[1]>0))})
    result={"method":"SplaTAM","train_frame_count":4,"eval_frame_count":8,"rows":rows,"status":"PASS" if all(r["rgb_max_abs"]<=1e-5 and r["depth_max_abs"]<=1e-5 and r["alpha_max_abs"]<=1e-5 and r["depth_valid_mask_exact"] and r["alpha_mask_exact"] for r in rows) else "SPLATAM_NATIVE_RENDER_PARITY_FAILED"}; dump(output,result); return result

def main():
    p=argparse.ArgumentParser(); p.add_argument("--method",choices=("splatam",)); p.add_argument("--repo",type=Path,required=True); p.add_argument("--params",type=Path,required=True); p.add_argument("--adapter",type=Path,required=True); p.add_argument("--train-adapter",type=Path,required=True); p.add_argument("--canonical-root",type=Path,required=True); p.add_argument("--output",type=Path,required=True); a=p.parse_args(); print(json.dumps(splatam(a.repo,a.params,a.adapter,a.train_adapter,a.canonical_root,a.output),sort_keys=True))
if __name__=="__main__": main()
