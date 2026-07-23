#!/usr/bin/env python3
import json,time
from pathlib import Path
import numpy as np,torch
from ellipsoids.covariance_utils import compute_cov
from splat.gsplat_utils import DummyGSplatLoader
from dynamics.systems import DoubleIntegrator,double_integrator_dynamics
from cbf.cbf_utils import CBF
ROOT=Path('/disk1/zlab/maintenance_records/tum_splatam_one_shot_runtime_recovery_g1_v2/resumed_trials'); BASE=Path('/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/splatam/canonical_export/export_a'); TRANS=Path('/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room/transforms.json')
R=.015; DT=.05; STEPS=800; TOL=.001
def nominal(x,g):
 v=torch.clamp(5*(g[:3]-x[:3]),-.1,.1)-x[3:]; return torch.clamp(v-x[3:],-.1,.1)
def main():
 ROOT.mkdir(parents=True,exist_ok=True); a={k:np.load(BASE/f'{k}.npy',mmap_mode='r') for k in ('means_world_m','scales_linear_m','quaternions_wxyz')}; m=DummyGSplatLoader(torch.device('cuda:0'));m.initialize_attributes(torch.from_numpy(a['means_world_m']),torch.from_numpy(a['quaternions_wxyz']),torch.from_numpy(a['scales_linear_m']))
 f=json.loads(TRANS.read_text())['frames']; p=lambda i:torch.tensor([r[3] for r in f[i]['transform_matrix'][:3]],device='cuda'); x=torch.cat((p(0),torch.zeros(3,device='cuda'))); goal=torch.cat((p(50),torch.zeros(3,device='cuda'))); d=DoubleIntegrator(torch.device('cuda'),3); c=CBF(m,d,5.,1.,R,distance_type='ball-to-ellipsoid'); rows=[]; t=time.time(); status='max_steps'
 for step in range(1,STEPS+1):
  ud=nominal(x,goal); u=c.solve_QP(x,ud)
  if not c.solver_success or not bool(torch.isfinite(u).all()): status='TUM_SPLATAM_G1_QP_INFEASIBLE_STOP';break
  x=double_integrator_dynamics(x,u)*DT+x; h,g,H,_=m.query_distance(x[:3],radius=R,distance_type='ball-to-ellipsoid'); mh=float(h.min()); rows.append({'step':step,'min_h':mh,'goal_distance':float(torch.norm(x[:3]-goal[:3])),'active':int(torch.argmin(h)),'u':u.cpu().tolist()})
  if not bool(torch.isfinite(x).all()):status='TUM_SPLATAM_G1_NONFINITE_STOP';break
  if mh<0:status='TUM_SPLATAM_G1_COLLISION_STOP';break
  if torch.norm(x-goal)<TOL:status='reached_goal';break
 out={'status':status,'reached_goal':status=='reached_goal','collision_or_overlap':status=='TUM_SPLATAM_G1_COLLISION_STOP','qp_infeasible':status=='TUM_SPLATAM_G1_QP_INFEASIBLE_STOP','pair':[0,50],'dt':DT,'robot_radius':R,'steps':len(rows),'progress':(rows[0]['goal_distance']-rows[-1]['goal_distance'])/rows[0]['goal_distance'] if rows else 0,'min_h':min((r['min_h'] for r in rows),default=None),'runtime_s':time.time()-t};(ROOT/'one_trial_summary.json').write_text(json.dumps(out,indent=2));(ROOT/'one_trial_steps.json').write_text(json.dumps(rows));print(json.dumps(out))
if __name__=='__main__':main()
