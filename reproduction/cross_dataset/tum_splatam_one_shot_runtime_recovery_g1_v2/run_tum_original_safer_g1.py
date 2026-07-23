#!/usr/bin/env python3
"""Task-owned exact-map original-SAFER G1 continuation runner."""
import gc,json,time
from pathlib import Path
import numpy as np, torch
from ellipsoids.covariance_utils import compute_cov
from splat.gsplat_utils import DummyGSplatLoader
from dynamics.systems import DoubleIntegrator
from cbf.cbf_utils import CBF

ROOT=Path('/disk1/zlab/maintenance_records/tum_splatam_one_shot_runtime_recovery_g1_v2/resumed_trials'); ROOT.mkdir(parents=True,exist_ok=True)
BASE=Path('/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/splatam/canonical_export/export_a')
TRANS=Path('/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room/transforms.json')
RADIUS=.015; ALPHA=5.; BETA=1.; DT=.01; MAX_STEPS=800; GOAL_TOL=.001
def control(x,g):
 v=torch.clamp(5*(g[:3]-x[:3]),-.1,.1)+(-x[3:]); return torch.clamp(v-x[3:],-.1,.1)
def main():
 t=time.time(); a={k:np.load(BASE/f'{k}.npy',mmap_mode='r') for k in ('means_world_m','scales_linear_m','quaternions_wxyz')}; d=DummyGSplatLoader(torch.device('cuda:0')); d.initialize_attributes(torch.from_numpy(a['means_world_m']),torch.from_numpy(a['quaternions_wxyz']),torch.from_numpy(a['scales_linear_m']))
 frames=json.loads(TRANS.read_text())['frames']; ids=[0,25,50,75,100,125,150,175,200,225,250,275,299]; pts=np.asarray([[row[3] for row in frames[i]['transform_matrix'][:3]] for i in ids],np.float32)
 # Full-map radius query gives the original CBF's unfiltered safety values.
 diag=[]
 for i,p in zip(ids,pts):
  h,g,H,info=d.query_distance(torch.from_numpy(p).cuda(),distance_type='ball-to-ellipsoid',radius=RADIUS); j=int(torch.argmin(h)); diag.append({'frame':i,'h':float(h[j]),'active_index':j,'finite':bool(torch.isfinite(h).all() and torch.isfinite(g).all() and torch.isfinite(H).all())})
 pairs=[]
 for si in range(len(ids)):
  for gi in range(si+1,len(ids)):
   sep=float(np.linalg.norm(pts[si]-pts[gi]));
   if sep>=.5 and diag[si]['h']>0 and diag[gi]['h']>0 and diag[si]['finite'] and diag[gi]['finite']: pairs.append((si,gi,sep))
 if not pairs:
  (ROOT/'trial_registry_summary.json').write_text(json.dumps({'status':'BLOCKED_BY_NO_CERTIFIED_SAFE_SPLATAM_SMOKE_PAIR','diagnosis':diag},indent=2)); return
 si,gi,sep=pairs[0]; dyn=DoubleIntegrator(device=torch.device('cuda:0'),ndim=3); x=torch.cat((torch.from_numpy(pts[si]).cuda(),torch.zeros(3,device='cuda'))); goal=torch.cat((torch.from_numpy(pts[gi]).cuda(),torch.zeros(3,device='cuda'))); cbf=CBF(d,dyn,ALPHA,BETA,RADIUS,distance_type='ball-to-ellipsoid'); udes=control(x,goal)
 try:
  u=cbf.solve_QP(x,udes); qp={'status':'PASS' if cbf.solver_success and bool(torch.isfinite(u).all()) else 'TUM_SPLATAM_G1_ONE_STEP_QP_INFEASIBLE_STOP','desired':udes.cpu().tolist(),'safe':u.cpu().tolist()}
 except Exception as e: qp={'status':'TUM_SPLATAM_G1_ONE_STEP_QP_NONFINITE_STOP','error':repr(e)}
 out={'radius':RADIUS,'alpha':ALPHA,'beta':BETA,'dt':DT,'max_steps':MAX_STEPS,'goal_tolerance':GOAL_TOL,'map_count':int(d.means.shape[0]),'diagnosis':diag,'safe_pair':[ids[si],ids[gi],sep],'diagnostic_pairs':[[ids[x],ids[y],z] for x,y,z in pairs[:3]],'one_step_qp':qp,'runtime_s':time.time()-t}
 (ROOT/'g1_continuation_result.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out))
if __name__=='__main__': main()
