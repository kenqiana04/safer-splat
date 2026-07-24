#!/usr/bin/env python3
"""Freeze three transform-sequence held-out pairs before any intervention run."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import numpy as np
import torch

ROOT=Path('/disk1/zlab/maintenance_records/tum_splatam_dt_triggered_v4c_recovery_v1')
REPO=Path('/disk1/zlab/projects/safer-splat'); MAP=Path('/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/splatam/canonical_export/export_a'); TRANS=Path('/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room/transforms.json')
sys.path.insert(0,str(REPO)); from splat.gsplat_utils import DummyGSplatLoader

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def main()->None:
    device=torch.device('cuda:0'); loader=DummyGSplatLoader(device)
    loader.initialize_attributes(torch.from_numpy(np.load(MAP/'means_world_m.npy')).to(device=device,dtype=torch.float32),torch.from_numpy(np.load(MAP/'quaternions_wxyz.npy')).to(device=device,dtype=torch.float32),torch.from_numpy(np.load(MAP/'scales_linear_m.npy')).to(device=device,dtype=torch.float32))
    frames=json.loads(TRANS.read_text(encoding='utf-8'))['frames']; positions=np.asarray([[r[0][3],r[1][3],r[2][3]] for r in (f['transform_matrix'] for f in frames)],dtype=np.float32)
    bbox_ok=bool(np.isfinite(positions).all() and np.all(positions>=positions.min(axis=0)) and np.all(positions<=positions.max(axis=0)))
    pairs=[]
    for start in range(1,len(positions)-50):
        goal=start+50; sep=float(np.linalg.norm(positions[goal]-positions[start]))
        if sep < .50: continue
        with torch.no_grad():
            hs,_,_,_=loader.query_distance(torch.tensor(positions[start],device=device),radius=.015,distance_type='ball-to-ellipsoid'); hg,_,_,_=loader.query_distance(torch.tensor(positions[goal],device=device),radius=.015,distance_type='ball-to-ellipsoid')
        sh=float(hs.min().item()); gh=float(hg.min().item())
        if sh>0 and gh>0 and bbox_ok:
            pairs.append({'label':f'HELDOUT_PAIR_{len(pairs)+1}','start_frame':start,'goal_frame':goal,'start_h_float32':sh,'goal_h_float32':gh,'separation_m':sep,'initial_safe':True,'finite':True,'bbox_valid':True})
        if len(pairs)==3:break
    if len(pairs)!=3: raise RuntimeError(f'only {len(pairs)} eligible pairs')
    data={'registry_source':'PR47 frozen transforms sequence reconstructed before intervention; no standalone PR47 registry file was retained','transforms_sha256':sha(TRANS),'map_count':5464102,'selection_rule':'ascending start frame; pair=(start,start+50); exclude 0->50; require INITIAL_SAFE, goal_h>0, separation>=0.50m, finite, bbox valid; take first three','pairs':pairs}
    out=ROOT/'heldout_registry';out.mkdir(parents=True,exist_ok=True);(out/'heldout_pair_registry.json').write_text(json.dumps(data,indent=2),encoding='utf-8');print(json.dumps(data,indent=2))
if __name__=='__main__':main()
