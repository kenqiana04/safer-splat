"""Lossless, no-filter canonical Gaussian exports from task-owned pilot checkpoints."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from _common import FRONTENDS, ROOT, atomic_json, ensure_dirs, load_json, sha256_path, update_stage
from _frontend_runner import P, c2w_cv, frame_rows


def sigmoid(value: np.ndarray) -> np.ndarray: return 1.0 / (1.0 + np.exp(-value))


def matrix_quaternion(matrix: np.ndarray) -> np.ndarray:
    trace = float(np.trace(matrix));
    if trace > 0:
        s = (trace + 1.0) ** 0.5 * 2.0; return np.array([0.25 * s, (matrix[2,1]-matrix[1,2])/s, (matrix[0,2]-matrix[2,0])/s, (matrix[1,0]-matrix[0,1])/s])
    index = int(np.argmax(np.diag(matrix))); values = np.zeros(4)
    if index == 0:
        s=(1+matrix[0,0]-matrix[1,1]-matrix[2,2])**.5*2; values[:]=[(matrix[2,1]-matrix[1,2])/s,.25*s,(matrix[0,1]+matrix[1,0])/s,(matrix[0,2]+matrix[2,0])/s]
    elif index == 1:
        s=(1+matrix[1,1]-matrix[0,0]-matrix[2,2])**.5*2; values[:]=[(matrix[0,2]-matrix[2,0])/s,(matrix[0,1]+matrix[1,0])/s,.25*s,(matrix[1,2]+matrix[2,1])/s]
    else:
        s=(1+matrix[2,2]-matrix[0,0]-matrix[1,1])**.5*2; values[:]=[(matrix[1,0]-matrix[0,1])/s,(matrix[0,2]+matrix[2,0])/s,(matrix[1,2]+matrix[2,1])/s,.25*s]
    return values


def hamilton(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    w,x,y,z=np.moveaxis(left,-1,0); a,b,c,d=np.moveaxis(right,-1,0)
    return np.stack((w*a-x*b-y*c-z*d,w*b+x*a+y*d-z*c,w*c-x*d+y*a+z*b,w*d+x*c-y*b+z*a),axis=-1)


def save_arrays(path: Path, values: dict[str, np.ndarray]) -> dict:
    path.mkdir(parents=True, exist_ok=False); arrays = {}
    for name, value in values.items():
        value = np.ascontiguousarray(value.astype(np.float32, copy=False)); np.save(path / f"{name}.npy", value, allow_pickle=False); arrays[name] = {"shape": list(value.shape), "dtype": str(value.dtype), "sha256": sha256_path(path / f"{name}.npy")}
    return arrays


def export_splatam(stage: str) -> tuple[dict[str,np.ndarray],dict]:
    summary=load_json(ROOT/"splatam"/f"{stage}_summary.json"); checkpoint=Path(summary["checkpoint"]); z=np.load(checkpoint,allow_pickle=False); means=np.asarray(z["means3D"],dtype=np.float32); scales=np.exp(np.asarray(z["log_scales"],dtype=np.float32)); scales=np.repeat(scales,3,axis=1) if scales.shape[1]==1 else scales; quats=np.asarray(z["unnorm_rotations"],dtype=np.float32); quats/=np.linalg.norm(quats,axis=1,keepdims=True); op=sigmoid(np.asarray(z["logit_opacities"],dtype=np.float32).reshape(-1)); rgb=np.asarray(z["rgb_colors"],dtype=np.float32)
    order=load_json(ROOT/"pilot_registry"/"replica_frontend_map_only_order.json"); ids=order["smoke_mapping_frame_ids"] if stage=="smoke" else order["mapping_frame_order"]; first=c2w_cv(frame_rows(ids)[0]); means=(means@first[:3,:3].T+first[:3,3]); q0=matrix_quaternion(first[:3,:3]); quats=hamilton(np.broadcast_to(q0,quats.shape),quats); quats/=np.linalg.norm(quats,axis=1,keepdims=True)
    return {"means_world_m":means,"scales_linear_m":scales,"quaternions_wxyz":quats,"opacities":op,"appearance":rgb},{"source_checkpoint":str(checkpoint),"source_checkpoint_sha256":sha256_path(checkpoint),"source_representation":"SplaTAM params.npz means3D/log_scales/unnorm_rotations/logit_opacities/rgb_colors","coordinate_transform":"dataset_world_from_relative_frontend_world=first_mapping_c2w_opencv","scale_conversion":"exp(log_scales), broadcast isotropic scale to 3 axes","quaternion_conversion":"normalized WXYZ then left-multiplied by first camera world rotation","gaussian_index_order":"source params.npz order; no filtering"}


def export_gaussian_slam(stage: str) -> tuple[dict[str,np.ndarray],dict]:
    import torch
    summary=load_json(ROOT/"gaussian_slam"/f"{stage}_summary.json"); checkpoint=Path(summary["checkpoint"]); checkpoints=sorted(checkpoint.parent.glob("*.ckpt")); parts=[]
    for item in checkpoints:
        payload=torch.load(item,map_location="cpu"); values=payload.get("gaussian_params")
        if values is not None: parts.append((item,values))
    if not parts: raise RuntimeError("NO_GAUSSIAN_SLAM_SUBMAP_CHECKPOINTS")
    def gather(key): return np.concatenate([values[key].detach().cpu().numpy() for _,values in parts],axis=0)
    means=gather("xyz"); scales=np.exp(gather("scaling")); quats=gather("rotation"); quats/=np.linalg.norm(quats,axis=1,keepdims=True); op=sigmoid(gather("opacity").reshape(-1)); dc=gather("features_dc"); rest=gather("features_rest"); sh=np.concatenate((dc,rest),axis=1)
    return {"means_world_m":means,"scales_linear_m":scales,"quaternions_wxyz":quats,"opacities":op,"sh_coefficients":sh},{"source_checkpoint":str(checkpoint),"source_checkpoint_sha256":sha256_path(checkpoint),"source_checkpoints":[str(item) for item,_ in parts],"source_representation":"Gaussian-SLAM submap gaussian_params xyz/scaling/rotation/opacity/features","coordinate_transform":"identity: Gaussian-SLAM adapter receives absolute OpenCV c2w in dataset metric world","scale_conversion":"exp(log scaling)","quaternion_conversion":"source WXYZ normalized","gaussian_index_order":"submap filename lexical order then source index; no filtering"}


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("frontend",choices=("splatam","gaussian_slam"));parser.add_argument("--stage",choices=("smoke","pilot"),default="pilot");args=parser.parse_args();ensure_dirs(); summary_path=ROOT/args.frontend/f"{args.stage}_summary.json"; expected="SMOKE_MAP_COMPLETE_PENDING_SHARED_EVALUATION" if args.stage=="smoke" else "QUALIFICATION_PILOT_MAP_COMPLETE_PENDING_SHARED_EVALUATION"
    if not summary_path.exists() or load_json(summary_path)["status"] != expected:
        output={"status":f"NOT_AUTHORIZED_DUE_TO_{args.stage.upper()}","frontend":args.frontend,"stage":args.stage};atomic_json(ROOT/"canonical_exports"/f"{args.frontend}_{args.stage}_canonical_export_summary.json",output);print(output["status"]);return
    arrays,identity=export_splatam(args.stage) if args.frontend=="splatam" else export_gaussian_slam(args.stage); n=len(arrays["means_world_m"]); valid=n>0 and all(np.isfinite(value).all() for value in arrays.values()) and (arrays["scales_linear_m"]>0).all() and len(arrays["scales_linear_m"])==len(arrays["quaternions_wxyz"])==len(arrays["opacities"])
    destination=ROOT/"canonical_exports"/args.frontend/args.stage; metadata=save_arrays(destination,arrays); identity.update({"frontend":FRONTENDS[args.frontend]["display"],"source_commit":FRONTENDS[args.frontend]["commit"],"stage":args.stage,"gaussian_count":n,"arrays":metadata,"valid":bool(valid),"no_filtering":True,"no_pruning":True,"no_downsampling":True,"no_scale_fitting":True,"no_sim3":True});atomic_json(destination/"canonical_map_identity.json",identity)
    output={"status":"CANONICAL_EXPORT_PASS" if valid else f"{args.stage.upper()}_EXPORT_FAILURE","frontend":FRONTENDS[args.frontend]["display"],"stage":args.stage,"canonical_root":str(destination),"identity_path":str(destination/"canonical_map_identity.json"),"gaussian_count":n,"arrays":metadata,"no_filtering":True};atomic_json(ROOT/"canonical_exports"/f"{args.frontend}_{args.stage}_canonical_export_summary.json",output)
    if args.stage=="pilot": update_stage(args.frontend,"CANONICAL_EXPORT","TERMINAL_SCIENTIFIC_RESULT" if valid else "FAILED_INFRASTRUCTURE",result_status=output["status"])
    print(json.dumps(output,sort_keys=True))


if __name__ == "__main__": main()
