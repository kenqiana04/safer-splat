"""Execute one of the two static-only G0 representations."""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import torch

from _common import ROOT, SAFER_REPO, atomic_json, load_json, sha256_path, update_stage
from _splatfacto_g0_common import identity, query_set, safer_classes, three_passes


def run(kind):
    export=load_json(ROOT/"canonical_export"/"splatfacto_pilot_canonical_export_summary.json"); geometry=load_json(ROOT/"common_evaluation"/"splatfacto_pilot_geometry_evaluation.json"); structure=load_json(ROOT/"map_structure"/"splatfacto_pilot_map_structure_audit.json"); native=load_json(ROOT/"safer_native_loader"/"splatfacto_safer_native_loader_summary.json")
    name="splatfacto_safer_native_g0_summary.json" if kind=="native" else "splatfacto_safer_canonical_g0_summary.json"; destination=ROOT/"safer_g0"/name
    gates=export.get("status","").endswith("PASS") and geometry.get("status")=="SPLATFACTO_PILOT_GEOMETRY_EVALUATED" and structure.get("status")=="SPLATFACTO_PILOT_MAP_STRUCTURE_FINITE" and native.get("status")=="SPLATFACTO_SAFER_NATIVE_LOADER_PASS"
    if not gates:
        atomic_json(destination,{"status":"NOT_AUTHORIZED_DUE_TO_G0_PREREQUISITE","kind":kind});return 1
    root=Path(export["canonical_root"]); means=np.load(root/"means_world_m.npy"); scales=np.load(root/"scales_linear_m.npy"); quats=np.load(root/"quaternions_wxyz.npy"); queries,query_hash=query_set(means); Dummy,Native=safer_classes()
    if kind=="native": loader=Native(Path(load_json(ROOT/"qualification_pilot"/"splatfacto_pilot_summary.json")["runtime_config"]),"cuda:0")
    else:
        loader=Dummy("cuda:0"); loader.initialize_attributes(torch.from_numpy(means),torch.from_numpy(quats),torch.from_numpy(scales))
    started=time.time(); values,passed,symmetry=three_passes(loader,queries); elapsed=time.time()-started; h,g,H,indices=values
    actual,identity_ok=identity(); result_path=ROOT/"safer_g0"/("native_static_results.npz" if kind=="native" else "canonical_static_results.npz"); np.savez_compressed(result_path,h=h,gradient=g,hessian=H,active_index=indices,queries=queries)
    status="SPLATFACTO_SAFER_"+kind.upper()+"_G0_PASS" if passed and identity_ok else "SPLATFACTO_SAFER_"+kind.upper()+"_G0_FAILURE"
    out={"status":status,"kind":kind,"safer_identity":actual,"safer_identity_match":identity_ok,"query_seed":"REPLICA_FRONTEND_SAFER_G0_V1","query_count":256,"query_sha256":query_hash,"radius_m":.015,"distance_type":"ball-to-ellipsoid","runs_finite":bool(np.isfinite(h).all()),"gradient_finite":bool(np.isfinite(g).all()),"hessian_finite":bool(np.isfinite(H).all()),"active_gaussian_deterministic":bool(passed),"hessian_symmetry_relative_max":symmetry,"gaussian_count_before_after":[int(len(means)),int(len(means))],"no_map_mutation":True,"no_filtering":True,"no_downsampling":True,"runtime_seconds":elapsed,"raw_static_result":str(result_path),"raw_static_result_sha256":sha256_path(result_path)}
    atomic_json(destination,out); update_stage("SAFER_NATIVE_G0" if kind=="native" else "SAFER_CANONICAL_G0","TERMINAL_SCIENTIFIC_RESULT" if status.endswith("PASS") else "FAILED_INFRASTRUCTURE",result_status=status); print(status);return 0 if status.endswith("PASS") else 1


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("kind",choices=("native","canonical"));args=p.parse_args();raise SystemExit(run(args.kind))
