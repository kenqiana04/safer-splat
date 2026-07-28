#!/usr/bin/env python3
"""Directly load the pilot checkpoint with SAFER's native Nerfstudio loader."""
from __future__ import annotations

import sys

import numpy as np

from _common import ROOT, SAFER_REPO, atomic_json, load_json, sha256_path, update_stage


def main():
    pilot=load_json(ROOT/"qualification_pilot"/"splatfacto_pilot_summary.json"); export=load_json(ROOT/"canonical_export"/"splatfacto_pilot_canonical_export_summary.json")
    destination=ROOT/"safer_native_loader"/"splatfacto_safer_native_loader_summary.json"
    if pilot.get("status")!="SPLATFACTO_PILOT_COMPLETE" or not export.get("status","").endswith("PASS"):
        atomic_json(destination,{"status":"NOT_AUTHORIZED_DUE_TO_PILOT_OR_EXPORT"});return
    sys.path.insert(0,str(SAFER_REPO)); from splat.gsplat_utils import GSplatLoader
    loader=GSplatLoader(__import__("pathlib").Path(pilot["runtime_config"]),"cuda:0")
    native={"means":loader.means.detach().float().cpu().numpy(),"scales":loader.scales.detach().float().cpu().numpy(),"quats":loader.rots.detach().float().cpu().numpy(),"opacities":loader.opacities.detach().float().cpu().numpy().reshape(-1)}
    native["quats"] /= np.linalg.norm(native["quats"], axis=1, keepdims=True)
    root=__import__("pathlib").Path(export["canonical_root"]); canonical={"means":np.load(root/"means_world_m.npy"),"scales":np.load(root/"scales_linear_m.npy"),"quats":np.load(root/"quaternions_wxyz.npy"),"opacities":np.load(root/"opacities.npy")}
    equal={k:bool(v.shape==canonical[k].shape and np.allclose(v,canonical[k],atol=1e-7,rtol=0.)) for k,v in native.items()}; finite=bool(all(np.isfinite(v).all() for v in native.values()))
    status="SPLATFACTO_SAFER_NATIVE_LOADER_PASS" if finite and all(equal.values()) else "SPLATFACTO_SAFER_NATIVE_LOADER_MISMATCH"
    out={"status":status,"loader":"splat.gsplat_utils.GSplatLoader.load_gsplat_from_nerfstudio","runtime_config":pilot["runtime_config"],"runtime_config_sha256":pilot["runtime_config_sha256"],"source_checkpoint":pilot["checkpoints"][-1],"loaded_gaussian_count":int(native["means"].shape[0]),"array_shapes":{k:list(v.shape) for k,v in native.items()},"source_to_canonical_exact_array_match":equal,"finite":finite,"scale_representation":"native log scales exponentiated by SAFER loader; canonical export uses the same exp conversion","quaternion_order":"WXYZ", "opacity_representation":"native sigmoid(logit opacity); canonical export uses same sigmoid conversion","world_frame":"Replica V3 metric world; no coordinate conversion","peak_gpu_memory_not_sampled":"loader-only task; no navigation","safer_core_modified":False}
    atomic_json(destination,out); update_stage("SAFER_NATIVE_LOADER","TERMINAL_SCIENTIFIC_RESULT" if status.endswith("PASS") else "FAILED_INFRASTRUCTURE",result_status=status); print(status)


if __name__=="__main__": main()
