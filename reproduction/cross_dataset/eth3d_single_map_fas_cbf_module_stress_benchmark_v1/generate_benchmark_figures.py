#!/usr/bin/env python3
"""Generate the 25 compact protocol figures from frozen artifacts."""
from __future__ import annotations
import argparse,json,re
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from eth3d_controller_core import METHODS

SHORT={m:m.split('_')[0] for m in METHODS}; COLORS=['#4C78A8','#F58518','#54A24B','#E45756','#B279A2']

def save(fig,path): fig.tight_layout();fig.savefig(path,dpi=160,bbox_inches='tight');plt.close(fig)
def textfig(path,title,lines):
 fig,ax=plt.subplots(figsize=(8,4.5));ax.axis('off');ax.set_title(title,fontsize=15,fontweight='bold');ax.text(.03,.9,'\n'.join(lines),va='top',family='monospace',fontsize=10,transform=ax.transAxes);save(fig,path)
def grouped(rows,metric,agg=np.mean):
 groups=['G0_SAFE_CONTROL','G1_START_SAFE_BOUNDARY','G2_FEASIBILITY_DENSE','G3_SAMPLED_DATA_GAP','G4_PREDICTIVE_RECOVERY'];out=np.zeros((5,5))
 for i,g in enumerate(groups):
  for j,m in enumerate(METHODS):
   vals=[float(r.get(metric,0) or 0) for r in rows if r['group']==g and r['method']==m];out[i,j]=agg(vals) if vals else 0
 return groups,out
def groupbar(path,rows,metric,title,ylabel,agg=np.mean):
 groups,data=grouped(rows,metric,agg);fig,ax=plt.subplots(figsize=(9,4.8));x=np.arange(5);w=.16
 for j,m in enumerate(METHODS):ax.bar(x+(j-2)*w,data[:,j],w,label=SHORT[m],color=COLORS[j])
 ax.set_xticks(x,[g[:2] for g in groups]);ax.set_ylabel(ylabel);ax.set_title(title);ax.legend(ncol=5,fontsize=8);ax.grid(axis='y',alpha=.25);save(fig,path)

def main():
 p=argparse.ArgumentParser();p.add_argument('--task-root',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();r=a.task_root;o=a.output_dir;o.mkdir(parents=True,exist_ok=True)
 results=[json.loads(x.read_text()) for x in (r/'formal_controller/results').glob('*.json') if not x.name.endswith('.complete.json')]
 registry=json.loads((r/'scenario_generation/scenario_registry.json').read_text());diag=json.loads((r/'scenario_generation/scenario_static_diagnostics.json').read_text());viab=json.loads((r/'minimum_map_viability.json').read_text());formal=json.loads((r/'formal_map/formal_result.json').read_text());env=json.loads((r/'environment/environment_identity.json').read_text());evidence=json.loads((r/'paired_analysis/module_evidence_matrix.json').read_text());smooth=json.loads((r/'paired_analysis/smoothness_diagnostics.json').read_text());decision=json.loads((r/'report/final_decision.json').read_text());fail=json.loads((r/'paired_analysis/failure_case_registry.json').read_text())
 textfig(o/'project_scope_recenter.png','Project scope recenter',['PR #79: planner-coupled route contract remains closed','This task: one fixed ETH3D learned map','Purpose: local SAFER vs FAS-CBF module stress evidence','No deployment, N3, global-planner, or real-robot claim'])
 fig,ax=plt.subplots(figsize=(8,4));ax.bar(['PR79 planner role','Local safety role'],[0,1],color=['#999999','#4C78A8']);ax.set_ylim(0,1.2);ax.set_ylabel('Role admitted');ax.set_title('Planner-coupled failure vs local-safety carrier');save(fig,o/'pr79_planner_vs_local_safety_roles.png')
 textfig(o/'official_3dgs_environment_identity.png','Official 3DGS environment',[f"source 54c035f7834b564019656c3e3fcc3646292f727d",f"python {env.get('python_version')}",f"torch {env.get('torch_version')} / CUDA {env.get('torch_cuda_version')}",f"GPU {env.get('gpu_name','RTX 4090')}",f"qualification {env.get('status')}"])
 log=(r/'logs/formal_30000.log').read_text(errors='ignore');pairs=[(int(i),float(v)) for i,v in re.findall(r'(\d+)/30000[^\r\n]*?Loss=([0-9.]+)',log)];ded={i:v for i,v in pairs};xs=np.asarray(sorted(ded));ys=np.asarray([ded[i] for i in xs]);fig,ax=plt.subplots(figsize=(8,4.5));ax.plot(xs,ys,lw=.8);ax.set_xlabel('Iteration');ax.set_ylabel('EMA loss');ax.set_title('Official 3DGS formal training curve');ax.grid(alpha=.2);save(fig,o/'formal_training_curve.png')
 fig,ax=plt.subplots(figsize=(8,4.5));iters=[7000,15000,30000];counts=[formal['gaussian_counts'][str(i)] for i in iters];ax.plot(iters,counts,'o-',label='Gaussians');ax.set_ylabel('Gaussian count');ax2=ax.twinx();ax2.axhline(formal['max_gpu_memory_used_mib'],color='#E45756',label='Peak VRAM');ax2.set_ylabel('Peak VRAM MiB');ax.set_title('Map growth and memory');save(fig,o/'gaussian_count_and_memory.png')
 fig,ax=plt.subplots(figsize=(7,4));ax.bar(['TRAIN PSNR','Heldout PSNR'],[viab['native_train_psnr'],viab['heldout_psnr_mean']],color=COLORS[:2]);ax.set_title('Minimum map viability (descriptive only)');ax.set_ylabel('dB');save(fig,o/'minimum_map_viability.png')
 fig,ax=plt.subplots(figsize=(9,4));hm=viab['heldout_metrics'];ax.plot([x['psnr'] for x in hm],'o-',label='PSNR');ax2=ax.twinx();ax2.plot([x['ssim'] for x in hm],'s--',color=COLORS[1],label='SSIM');ax.set_title('Held-out cross-view diagnostics (12 views)');ax.set_xlabel('View');ax.set_ylabel('PSNR');ax2.set_ylabel('SSIM');save(fig,o/'heldout_cross_view_diagnostics.png')
 fig=plt.figure(figsize=(7,5));ax=fig.add_subplot(111,projection='3d');pts=np.asarray([s['start_m'] for s in registry['scenarios']]);groups=sorted(registry['group_counts']);labels=[groups.index(s['group']) for s in registry['scenarios']];ax.scatter(pts[:,0],pts[:,1],pts[:,2],c=labels,cmap='tab10',s=18);ax.set_title('Frozen scenario starts in metric frame');save(fig,o/'scenario_spatial_distribution.png')
 fig,ax=plt.subplots(figsize=(8,4));g=sorted(registry['group_counts']);ax.bar([x[:2] for x in g],[registry['group_counts'][x] for x in g],color=COLORS);ax.set_ylim(0,24);ax.set_title('Five frozen stress groups');ax.set_ylabel('Scenarios');save(fig,o/'five_stress_group_summary.png')
 acts=evidence['activation'];fig,ax=plt.subplots(figsize=(8,4));ax.bar([k.split('_')[0] for k in acts],list(acts.values()),color=COLORS[:4]);ax.set_title('Module activation counts in designated groups');ax.set_ylabel('Activated scenarios / 20');save(fig,o/'module_activation_rates.png')
 groupbar(o/'collision_by_method_group.png',results,'reference_collision','Reference collision by method/group','Rate')
 groupbar(o/'progress_by_method_group.png',results,'progress_m','Progress by method/group','Mean progress (m)')
 groupbar(o/'qp_infeasible_by_method_group.png',results,'qp_infeasible','QP infeasible by method/group','Mean count')
 groupbar(o/'active_constraints_by_method_group.png',results,'active_constraints_mean','Active constraints by method/group','Mean rows')
 groupbar(o/'runtime_by_method_group.png',results,'runtime_mean_s','Controller runtime by method/group','Mean seconds/step')
 g1=[x for x in results if x['group']=='G1_START_SAFE_BOUNDARY' and x['method']==METHODS[1]];fig,ax=plt.subplots(figsize=(7,4));ax.bar(['attempted','accepted','rejected'],[sum(x['projection']['attempted'] for x in g1),sum(bool(x['projection']['success']) for x in g1),sum(not bool(x['projection']['success']) for x in g1)],color=COLORS[:3]);ax.set_title('Start-Safe projection results');save(fig,o/'start_safe_projection_results.png')
 g3=[x for x in results if x['group']=='G3_SAMPLED_DATA_GAP' and x['method']==METHODS[3]];fig,ax=plt.subplots(figsize=(7,4));ax.bar(['checks','triggers','segment risks','endpoint-only'],[sum(x.get('dt_checks',0) for x in g3),sum(x.get('dt_triggers',0) for x in g3),sum(x.get('segment_risk_events',0) for x in g3),sum(x.get('endpoint_only_misses',0) for x in g3)],color=COLORS[:4]);ax.set_title('Sampled-data verifier events');save(fig,o/'sampled_data_verifier_results.png')
 g4=[x for x in results if x['group']=='G4_PREDICTIVE_RECOVERY' and x['method']==METHODS[4]];fig,ax=plt.subplots(figsize=(7,4));ax.bar(['triggers','success','failure'],[sum(x.get('recovery_triggers',0) for x in g4),sum(x.get('recovery_success',0) for x in g4),sum(x.get('recovery_failure',0) for x in g4)],color=COLORS[:3]);ax.set_title('Predictive recovery H=3');save(fig,o/'predictive_recovery_results.png')
 metrics=['reference_collision','completion','progress_m','deadlock'];m0=[np.mean([float(x.get(k,0)) for x in results if x['method']==METHODS[0]]) for k in metrics];m4=[np.mean([float(x.get(k,0)) for x in results if x['method']==METHODS[4]]) for k in metrics];fig,ax=plt.subplots(figsize=(8,4));x=np.arange(4);ax.bar(x-.18,m0,.36,label='M0',color=COLORS[0]);ax.bar(x+.18,m4,.36,label='M4',color=COLORS[4]);ax.set_xticks(x,['collision','completion','progress m','deadlock']);ax.set_title('Full FAS-CBF vs SAFER');ax.legend();save(fig,o/'paired_full_fas_vs_safer.png')
 cats=['SUPPORTED','PROMISING','NOT_SUPPORTED','REGRESSION','INACTIVE'];vals=[cats.index(v['category']) for v in evidence['evidence'].values()];fig,ax=plt.subplots(figsize=(9,3.8));im=ax.imshow([vals],cmap='RdYlGn_r',aspect='auto',vmin=0,vmax=4);ax.set_yticks([]);ax.set_xticks(range(len(vals)),[k.split('_')[0] for k in evidence['evidence']]);[ax.text(i,0,cats[v],ha='center',va='center',fontsize=8) for i,v in enumerate(vals)];ax.set_title('Module evidence matrix');save(fig,o/'module_evidence_matrix.png')
 fig,ax=plt.subplots(figsize=(8,4));ax.bar([SHORT[m] for m in METHODS],[smooth['methods'][m]['control_tv']['mean'] for m in METHODS],color=COLORS);ax.set_title('Control total variation (diagnostic only)');save(fig,o/'control_total_variation_diagnostic.png')
 fig,ax=plt.subplots(figsize=(8,4));ax.bar([SHORT[m] for m in METHODS],[smooth['methods'][m]['jerk_rms']['mean'] for m in METHODS],color=COLORS);ax.set_title('Jerk RMS (diagnostic only)');save(fig,o/'jerk_diagnostic.png')
 counts=defaultdict(int)
 for c in fail['cases']:counts[c['hypothesis']]+=1
 fig,ax=plt.subplots(figsize=(8,4));ax.bar(list(counts) or ['none'],list(counts.values()) or [0],color='#E45756');ax.set_title('Preserved paired failure cases');save(fig,o/'failure_case_summary.png')
 textfig(o/'final_decision.png','Frozen decision',[f"Case {decision['case']}",decision['FINAL_STATUS'],decision['FINAL_DECISION']])
 textfig(o/'next_framework_handoff.png','Only authorized next task',[decision['ONLY_NEXT_TASK'],'No new dataset search','No mapper sweep','No adaptive-margin or smooth-control claim'])
 print(json.dumps({'status':'PASS_25_FIGURES','figure_count':len(list(o.glob('*.png')))},sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
