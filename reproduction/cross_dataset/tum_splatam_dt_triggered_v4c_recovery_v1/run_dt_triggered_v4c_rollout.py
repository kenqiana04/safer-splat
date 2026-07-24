#!/usr/bin/env python3
"""Task-owned TUM adapter: frozen CBF/QP plus frozen V4-C, strict H3 entry only."""
from __future__ import annotations
import argparse, json, sys, time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import torch

ROOT=Path('/disk1/zlab/maintenance_records/tum_splatam_dt_triggered_v4c_recovery_v1'); REPO=Path('/disk1/zlab/projects/safer-splat'); MAP=Path('/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/splatam/canonical_export/export_a'); TRANS=Path('/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room/transforms.json'); SCRIPTS=REPO/'work/risk_aware_cbf/scripts'
for p in (REPO,SCRIPTS):sys.path.insert(0,str(p))
from dynamics.systems import DoubleIntegrator, double_integrator_dynamics
from splat.gsplat_utils import DummyGSplatLoader
import run_risk_aware_v1_pre_cbf_comparison as v1
import run_v4b_corrective_dt_filter as v4b
import run_v4c_hstep_predictive_recovery as v4c

DT=.05; R=.015; MAX=800; WATCHDOG=90*60
def args_v4c(): return SimpleNamespace(horizon=3,num_sequences=128,sequence_noise_scale=.15,control_scale_list='0,0.25,0.5,0.75,1.0',include_braking_sequences=True,include_repulsive_sequences=True,include_goal_directed_sequences=True,use_cem=False,num_elites=16,cem_iters=2,w_base=1.,w_goal=.2,w_smooth=.1,w_safety=10.,dt_margin=.0005,dt=DT)
def loader(device):
 l=DummyGSplatLoader(device);l.initialize_attributes(torch.from_numpy(np.load(MAP/'means_world_m.npy')).to(device=device,dtype=torch.float32),torch.from_numpy(np.load(MAP/'quaternions_wxyz.npy')).to(device=device,dtype=torch.float32),torch.from_numpy(np.load(MAP/'scales_linear_m.npy')).to(device=device,dtype=torch.float32));return l
def positions():
 fs=json.loads(TRANS.read_text(encoding='utf-8'))['frames'];return np.asarray([[f['transform_matrix'][0][3],f['transform_matrix'][1][3],f['transform_matrix'][2][3]] for f in fs],dtype=np.float32)
def main():
 p=argparse.ArgumentParser();p.add_argument('--arm',choices=['baseline','intervention'],required=True);p.add_argument('--start',type=int,required=True);p.add_argument('--goal',type=int,required=True);p.add_argument('--label',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 out=Path(a.output);out.mkdir(parents=True,exist_ok=True);device=torch.device('cuda:0');g=loader(device);dyn=DoubleIntegrator(device=device,ndim=3);scene={'radius':R}; cbf=v1.DetailedCBF(g,dyn,5.,1.,R,distance_type='ball-to-ellipsoid'); ps=positions();x=torch.cat([torch.tensor(ps[a.start],device=device),torch.zeros(3,device=device)]).float();goal=torch.cat([torch.tensor(ps[a.goal],device=device),torch.zeros(3,device=device)]).float();x0=x.clone();vp=args_v4c();rows=[];u_prev=None;started=time.perf_counter();reason='max_steps';goal_reached=False
 for k in range(MAX):
  if time.perf_counter()-started>WATCHDOG:reason='timeout';break
  t=time.perf_counter(); xp=x.clone(); unom=v1.nominal_control(xp,goal); ubase=cbf.solve_QP(xp,unom)
  if not bool(cbf.solver_success): reason='qp_infeasible';break
  curh=v4b.query_h(g,xp[:3],R); _,h3s,h3=v4c.rollout_sequence(x=xp,controls=v4c.repeat_control(ubase,3),dt=DT,gsplat=g,scene_cfg=scene); margin=h3<.0005; strict=curh>0 and h3<0; activated=(a.arm=='intervention' and strict); uexec=ubase; rsuccess=None; rfailed=None; src='base'; rec_runtime=0.;seq_count=0
  if activated:
   tr=time.perf_counter(); cands=v4c.generate_sequences(args=vp,x=xp,goal=goal,u_base=ubase,u_nom=unom,u_prev=u_prev,gsplat=g,scene_cfg=scene,trial=a.start*10000+a.goal,step=k+1); sel,uexec,ehs,ehmin,rsuccess,rfailed,_,sid=v4c.evaluate_sequences(args=vp,scene='tum',method='safer_splat_filter',trial=a.start*10000+a.goal,step=k+1,x=xp,goal=goal,u_base=ubase,u_prev=u_prev,candidates=cands,gsplat=g,scene_cfg=scene); src=sel.source;seq_count=len(cands);rec_runtime=time.perf_counter()-tr
  x=double_integrator_dynamics(xp,uexec)*DT+xp; nexth,active=v4b.query_h_and_critical(g,x[:3],R); gd=float(torch.linalg.norm(x[:3]-goal[:3]).item()); rows.append({'step':k,'state':xp.detach().cpu().tolist(),'u_nominal':unom.detach().cpu().tolist(),'u_safe':ubase.detach().cpu().tolist(),'h1':h3s[0],'h2':min(h3s[:2]),'h3':h3,'margin_warning':margin,'strict_trigger':strict,'recovery_active':activated,'recovery_success':rsuccess,'recovery_failed':rfailed,'selected_source':src,'sequence_count':seq_count,'u_recovery':None if not activated else uexec.detach().cpu().tolist(),'u_executed':uexec.detach().cpu().tolist(),'current_h':curh,'next_h':nexth,'active_gaussian':active,'qp_status':'optimal','goal_distance':gd,'runtime_step':time.perf_counter()-t,'runtime_recovery':rec_runtime,'overlap_float32':nexth<0})
  u_prev=uexec.detach().clone()
  if not torch.isfinite(x).all():reason='nonfinite';break
  if nexth<0:reason='gsplat_overlap_stop';break
  if gd<.001:reason='reached_goal';goal_reached=True;break
 else:reason='max_steps'
 hs=[r['next_h'] for r in rows];trigs=[r for r in rows if r['strict_trigger']];acts=[r for r in rows if r['recovery_active']];progress=1-float(torch.linalg.norm(x[:3]-goal[:3]).item())/float(torch.linalg.norm(x0[:3]-goal[:3]).item())
 summary={'label':a.label,'arm':a.arm,'start_frame':a.start,'goal_frame':a.goal,'steps':len(rows),'stop_reason':reason,'goal_reached':goal_reached,'progress':progress,'min_float32_h':min(hs) if hs else None,'negative_h_step_count':sum(v<0 for v in hs),'first_strict_trigger_step':None if not trigs else trigs[0]['step'],'trigger_count':len(trigs),'recovery_activation_count':len(acts),'recovery_active_steps':len(acts),'longest_recovery_episode':1 if acts else 0,'retrigger_count':max(0,len(acts)-1),'qp_infeasible':reason=='qp_infeasible','nonfinite':reason=='nonfinite','timeout':reason=='timeout','runtime_seconds':time.perf_counter()-started,'runtime_mean':float(np.mean([r['runtime_step'] for r in rows])) if rows else None,'runtime_recovery_mean':float(np.mean([r['runtime_recovery'] for r in acts])) if acts else 0.,'control_deviation_mean':float(np.mean([np.linalg.norm(np.asarray(r['u_executed'])-np.asarray(r['u_safe'])) for r in rows])) if rows else 0.,'strict_contract_observed':all((not r['recovery_active']) or r['strict_trigger'] for r in rows),'margin_only_never_activated':all(not (r['recovery_active'] and not r['strict_trigger']) for r in rows)}
 (out/'steps.json').write_text(json.dumps(rows),encoding='utf-8');(out/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
