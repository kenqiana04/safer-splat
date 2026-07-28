"""Shared static-only G0 helpers. No controller, CBF-QP, or navigation is imported."""
from __future__ import annotations

import importlib.util
import subprocess
import sys

import numpy as np
import torch

from _common import DATASET, ROOT, SAFER_REPO, load_json, sha256_bytes


EXPECTED_HEAD="f63b4c496861c4f8881348d74244c1ff9a528d51"
EXPECTED_BLOBS={"distances":"d7f17b67df40e36e458c7a5ed77c4a04659c6f35","gsplat_utils":"782c38eca50e78c605085b481155ed61e4607336","cbf":"7c6e1300b125cc0a2a950ac2835a1fbe3d0de113"}


def safer_classes():
    sys.path.insert(0,str(SAFER_REPO))
    from splat.gsplat_utils import DummyGSplatLoader, GSplatLoader
    return DummyGSplatLoader, GSplatLoader


def query_set(means):
    adapters=load_json(ROOT/"pilot_adapter"/"splatfacto_metric_dataset_adapter_identity.json")["adapters"]["qualification_pilot"]
    rows={x["frame_id"]:x for x in load_json(DATASET/"formal_camera_manifest_v3.json")["frames"]}
    ids=adapters["mapping_frame_ids"]+adapters["holdout_frame_ids"]
    centers=np.asarray([np.asarray(rows[x]["camera_to_world"],dtype=np.float32)[:3,3] for x in ids],dtype=np.float32)
    rec=[x.copy() for x in centers]
    for index,point in enumerate(centers):
        shifted=point.copy(); shifted[index%3]+=.05 if (index//3)%2==0 else -.05; rec.append(shifted)
    lo,hi=means.min(axis=0),means.max(axis=0); axes=[np.linspace(lo[i],hi[i],n,dtype=np.float32) for i,n in enumerate((6,4,3))]
    grid=np.stack(np.meshgrid(*axes,indexing="ij"),axis=-1).reshape(-1,3); extent=hi-lo
    outside=np.asarray([np.where(np.asarray(sign)<0,lo-.1*extent,hi+.1*extent) for sign in ((-1,-1,-1),(-1,1,1),(1,-1,1),(1,1,-1))],dtype=np.float32)
    result=np.concatenate((np.asarray(rec,dtype=np.float32),grid,outside),axis=0); assert result.shape==(256,3),result.shape
    return result,sha256_bytes(result.tobytes())


def identity():
    def git(path): return subprocess.check_output(["git","-C",str(SAFER_REPO),"rev-parse",path],text=True).strip()
    actual={"head":git("HEAD"),"distances":git("HEAD:splat/distances.py"),"gsplat_utils":git("HEAD:splat/gsplat_utils.py"),"cbf":git("HEAD:cbf/cbf_utils.py")}
    expected={"head":EXPECTED_HEAD,**EXPECTED_BLOBS}; return actual,actual==expected


def three_passes(loader, queries):
    def once():
        hs=[]; gs=[]; hess=[]; inds=[]
        for point in queries:
            h,g,H,_=loader.query_distance(torch.from_numpy(point).cuda(),distance_type="ball-to-ellipsoid",radius=.015); i=int(torch.argmin(h)); hs.append(float(h[i])); gs.append(g[i].detach().cpu().numpy()); hess.append(H[i].detach().cpu().numpy()); inds.append(i)
        return np.asarray(hs),np.asarray(gs),np.asarray(hess),np.asarray(inds,dtype=np.int64)
    a=once(); b=once(); c=once(); torch.cuda.synchronize()
    H=a[2]; symmetry=np.linalg.norm(H-H.swapaxes(1,2),axis=(1,2))/(1.+np.linalg.norm(H,axis=(1,2)))
    passed=bool(np.isfinite(a[0]).all() and np.isfinite(a[1]).all() and np.isfinite(a[2]).all() and np.array_equal(a[0],b[0]) and np.array_equal(a[0],c[0]) and np.array_equal(a[1],b[1]) and np.array_equal(a[1],c[1]) and np.array_equal(a[2],b[2]) and np.array_equal(a[2],c[2]) and np.array_equal(a[3],b[3]) and np.array_equal(a[3],c[3]) and float(symmetry.max())<=1e-5)
    return a,passed,float(symmetry.max())
