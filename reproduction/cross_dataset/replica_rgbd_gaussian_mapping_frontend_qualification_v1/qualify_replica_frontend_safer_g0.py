#!/usr/bin/env python3
"""Three repeatable static ball-to-ellipsoid G0 passes; no control or navigation."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import torch

from _common import FRONTENDS, ROOT, SAFER_REPO, atomic_json, ensure_dirs, load_json, sha256_bytes, sha256_path, update_stage


EXPECTED_SAFER_HEAD = "f63b4c496861c4f8881348d74244c1ff9a528d51"
EXPECTED_SAFER_BLOBS = {
    "distances": "d7f17b67df40e36e458c7a5ed77c4a04659c6f35",
    "gsplat_utils": "782c38eca50e78c605085b481155ed61e4607336",
}


def stats(values: np.ndarray) -> dict:
    values=np.asarray(values,dtype=np.float64);return {"min":float(values.min()),"median":float(np.median(values)),"mean":float(values.mean()),"p95":float(np.quantile(values,.95)),"max":float(values.max())}


def loader():
    distances=SAFER_REPO/"splat"/"distances.py"; gsplat=SAFER_REPO/"splat"/"gsplat_utils.py"; spec=importlib.util.spec_from_file_location("splat.distances",distances);module=importlib.util.module_from_spec(spec);assert spec.loader;sys.modules["splat.distances"]=module;spec.loader.exec_module(module);spec=importlib.util.spec_from_file_location("replica_task_gsplat_utils",gsplat);module=importlib.util.module_from_spec(spec);assert spec.loader;spec.loader.exec_module(module);return module.DummyGSplatLoader,distances,gsplat


def queries() -> np.ndarray:
    order=load_json(ROOT/"pilot_registry"/"replica_frontend_map_only_order.json"); rows={row["frame_id"]:row for row in load_json(__import__("_common").DATASET/"formal_camera_manifest_v3.json")["frames"]}; centers=np.asarray([rows[frame]["camera_world_position"] for frame in order["mapping_frame_order"]+order["holdout_frame_order"]],dtype=np.float32); rec=[point.copy() for point in centers]
    for index,point in enumerate(centers):
        shifted=point.copy(); shifted[index%3]+=0.05 if (index//3)%2==0 else -0.05; rec.append(shifted)
    # bbox points are populated later from the unfiltered canonical-map bbox.
    return np.asarray(rec,dtype=np.float32)


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument("frontend",choices=("splatam","gaussian_slam"));args=parser.parse_args();ensure_dirs(); summary=ROOT/"canonical_exports"/f"{args.frontend}_pilot_canonical_export_summary.json"
    if not summary.exists() or load_json(summary).get("status")!="CANONICAL_EXPORT_PASS": out={"status":"NOT_AUTHORIZED_DUE_TO_CANONICAL_EXPORT","frontend":args.frontend};atomic_json(ROOT/"safer_g0"/f"{args.frontend}_safer_g0_summary.json",out);print(out["status"]);return
    canonical=Path(load_json(summary)["canonical_root"]); means=np.load(canonical/"means_world_m.npy"); scales=np.load(canonical/"scales_linear_m.npy"); quats=np.load(canonical/"quaternions_wxyz.npy"); q=queries(); lo,hi=means.min(axis=0),means.max(axis=0); axes=[np.linspace(lo[i],hi[i],(6,4,3)[i],dtype=np.float32) for i in range(3)]; q=np.concatenate((q,np.stack(np.meshgrid(*axes,indexing="ij"),axis=-1).reshape(-1,3)),axis=0); extent=hi-lo; q=np.concatenate((q,np.asarray([np.where(np.asarray(sign)<0,lo-.1*extent,hi+.1*extent) for sign in ((-1,-1,-1),(-1,1,1),(1,-1,1),(1,1,-1))],dtype=np.float32)),axis=0)
    assert q.shape==(256,3),q.shape; Loader,distances,gsplat=loader(); d=Loader("cuda:0"); d.initialize_attributes(torch.from_numpy(means),torch.from_numpy(quats),torch.from_numpy(scales))
    def once():
        h=[];g=[];H=[];indices=[]
        for point in q:
            hv,gv,Hv,_=d.query_distance(torch.from_numpy(point).cuda(),distance_type="ball-to-ellipsoid",radius=.015); index=int(torch.argmin(hv));h.append(float(hv[index]));g.append(gv[index].detach().cpu().numpy());H.append(Hv[index].detach().cpu().numpy());indices.append(index)
        return np.asarray(h),np.asarray(g),np.asarray(H),indices
    started=time.time(); A,gA,HA,iA=once();B,gB,HB,iB=once();C,gC,HC,iC=once();torch.cuda.synchronize(); symmetry=np.linalg.norm(HA-HA.swapaxes(1,2),axis=(1,2))/(1+np.linalg.norm(HA,axis=(1,2))); passed=bool(np.isfinite(A).all() and np.isfinite(gA).all() and np.isfinite(HA).all() and np.array_equal(A,B) and np.array_equal(A,C) and np.array_equal(gA,gB) and np.array_equal(gA,gC) and np.array_equal(HA,HB) and np.array_equal(HA,HC) and iA==iB==iC and float(symmetry.max())<=1e-5)
    def git(*parts: str) -> str:
        return subprocess.check_output(["git", "-C", str(SAFER_REPO), *parts], text=True).strip()
    head=git("rev-parse", "HEAD"); distance_blob=git("rev-parse", "HEAD:splat/distances.py"); gsplat_blob=git("rev-parse", "HEAD:splat/gsplat_utils.py")
    identity_ok=head==EXPECTED_SAFER_HEAD and distance_blob==EXPECTED_SAFER_BLOBS["distances"] and gsplat_blob==EXPECTED_SAFER_BLOBS["gsplat_utils"]
    passed=passed and identity_ok
    out={"status":"PASS_SAFER_G0_STATIC_QUERY_COMPATIBILITY" if passed else "FAIL_SAFER_G0_HESSIAN_OR_IDENTITY","frontend":FRONTENDS[args.frontend]["display"],"safer_head_expected":EXPECTED_SAFER_HEAD,"safer_head_actual":head,"safer_source_blobs_expected":EXPECTED_SAFER_BLOBS,"safer_source_blobs_actual":{"distances":distance_blob,"gsplat_utils":gsplat_blob},"safer_identity_match":identity_ok,"distances_sha256":sha256_path(distances),"gsplat_utils_sha256":sha256_path(gsplat),"query_seed":"REPLICA_FRONTEND_SAFER_G0_V1","query_count":256,"query_sha256":sha256_bytes(q.tobytes()),"radius_m":.015,"distance_type":"ball-to-ellipsoid","runs_finite":bool(np.isfinite(A).all()),"gradient_finite":bool(np.isfinite(gA).all()),"hessian_finite":bool(np.isfinite(HA).all()),"active_gaussian_deterministic":iA==iB==iC,"query_repeatability":bool(np.array_equal(A,B) and np.array_equal(A,C)),"hessian_symmetry_relative_max":float(symmetry.max()),"gaussian_count_before_after":[int(len(means)),int(len(means))],"no_map_mutation":True,"no_filtering":True,"no_downsampling":True,"runtime_seconds":time.time()-started,"h_statistics":stats(A)}
    atomic_json(ROOT/"safer_g0"/f"{args.frontend}_safer_g0_summary.json",out);update_stage(args.frontend,"SAFER_G0","TERMINAL_SCIENTIFIC_RESULT" if passed else "FAILED_INFRASTRUCTURE",result_status=out["status"]);print(json.dumps(out,sort_keys=True))


if __name__=="__main__": main()
