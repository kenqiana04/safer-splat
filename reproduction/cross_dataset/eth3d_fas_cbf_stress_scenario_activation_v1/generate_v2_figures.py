#!/usr/bin/env python3
"""Generate the 24 preregistered evidence figures from compact artifacts."""
from __future__ import annotations
import json
from collections import Counter
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from task_config_v2 import GROUPS,METHODS,TASK_ROOT

NAMES=("v1_terminal_semantics.png","v1_activation_stage_reachability.png","v1_h2_constraint_reduction_reconciliation.png",
"candidate_pool_funnel.png","stage_reachability_funnel.png","v2_scenario_spatial_distribution.png","v2_activation_by_group.png",
"start_safe_projectable_vs_unprojectable.png","feasibility_dominance_reduction.png","dt_trigger_types.png","recovery_trigger_recoverability.png",
"terminal_transition_g1.png","terminal_transition_g2.png","terminal_transition_g3.png","terminal_transition_g4.png","paired_progress.png",
"paired_qp_infeasible.png","paired_constraints.png","paired_runtime.png","paired_full_fas_vs_safer.png","module_evidence_matrix_v2.png",
"smoothness_diagnostics_v2.png","failure_case_summary_v2.png","final_decision_v2.png")

def save(fig,name):
 fig.tight_layout(); fig.savefig(TASK_ROOT/"figures"/name,dpi=170,bbox_inches="tight"); plt.close(fig)
def bar(name,title,labels,values,y="count",colors=None):
 fig,ax=plt.subplots(figsize=(8,4.5)); ax.bar(labels,values,color=colors or "#377eb8"); ax.set_title(title); ax.set_ylabel(y); ax.tick_params(axis="x",rotation=25); save(fig,name)
def heat(name,title,rows):
 states=sorted({x["older_terminal"] for x in rows}|{x["newer_terminal"] for x in rows}); mat=np.zeros((len(states),len(states)))
 for x in rows: mat[states.index(x["older_terminal"]),states.index(x["newer_terminal"])]=x["count"]
 fig,ax=plt.subplots(figsize=(7,6)); im=ax.imshow(mat,cmap="Blues"); ax.set_xticks(range(len(states)),states,rotation=35,ha="right"); ax.set_yticks(range(len(states)),states); ax.set_xlabel("newer");ax.set_ylabel("older");ax.set_title(title)
 for i in range(len(states)):
  for j in range(len(states)): ax.text(j,i,int(mat[i,j]),ha="center",va="center")
 fig.colorbar(im,ax=ax);save(fig,name)
def main():
 v1=json.loads((TASK_ROOT/"v1_semantic_audit/v1_terminal_semantics.json").read_text()); act1=json.loads((TASK_ROOT/"v1_semantic_audit/v1_activation_semantics.json").read_text())
 cand=json.loads((TASK_ROOT/"candidate_pool/candidate_pool_summary.json").read_text()); reg=json.loads((TASK_ROOT/"scenario_registry_v2/scenario_registry.json").read_text())
 rows=json.loads((TASK_ROOT/"paired_analysis/per_run_compact_records.json").read_text()); stats=json.loads((TASK_ROOT/"paired_analysis/paired_statistics.json").read_text())["comparisons"]
 trans=json.loads((TASK_ROOT/"paired_analysis/terminal_transition_matrices.json").read_text()); evidence=json.loads((TASK_ROOT/"paired_analysis/module_evidence_matrix.json").read_text()); smooth=json.loads((TASK_ROOT/"paired_analysis/smoothness_diagnostics.json").read_text())
 final=json.loads((TASK_ROOT/"report/final_decision.json").read_text()); failures=json.loads((TASK_ROOT/"failure_forensics/failure_case_registry.json").read_text())
 bar(NAMES[0],"V1 completions by method",list(METHODS),[v1["method_summary"][m]["completion_count"] for m in METHODS])
 bar(NAMES[1],"V1 designated-stage activation",["H1","H2","H3","H4"],[14,0,0,0])
 bar(NAMES[2],"V1 global active constraints",["M1","M2","M3","M4"],[v1["method_summary"][m]["active_constraints_mean_all_100_terminal_records"] for m in METHODS[1:]])
 q=cand["qualified_pool_counts"]; bar(NAMES[3],"Candidate pool qualified strata",list(q),list(q.values()))
 activation=evidence["activation"]; bar(NAMES[4],"V2 stage-reachability funnel",list(activation),list(activation.values()))
 fig,ax=plt.subplots(figsize=(7,6)); colors={g:i for i,g in enumerate(GROUPS)}
 for g in GROUPS:
  p=np.asarray([s["start_m"] for s in reg["scenarios"] if s["group"]==g]); ax.scatter(p[:,0],p[:,2],s=22,label=g[:2])
 ax.set_title("V2 spatial distribution (x-z)");ax.set_xlabel("x (m)");ax.set_ylabel("z (m)");ax.legend();save(fig,NAMES[5])
 bar(NAMES[6],"V2 activation by module",list(activation),list(activation.values()))
 g1=[s for s in reg["scenarios"] if s["group"]==GROUPS[1]]; c1=Counter("unprojectable" if not s["shadow_stage_reachability"]["S1"]["projection_success"] else "near" if s["shadow_stage_reachability"]["S1"]["classification"]=="NEAR_BOUNDARY" else "projectable" for s in g1);bar(NAMES[7],"Start-Safe strata",list(c1),list(c1.values()))
 g2=[s["shadow_stage_reachability"]["S2"] for s in reg["scenarios"] if s["group"]==GROUPS[2]];bar(NAMES[8],"Feasibility dominance",["original","reduced"],[np.mean([x["original_constraint_population"] for x in g2]),np.mean([x["reduced_constraint_population"] for x in g2])],"constraints")
 g3=Counter(s["shadow_stage_reachability"]["S3"]["trigger_type"] for s in reg["scenarios"] if s["group"]==GROUPS[3]);bar(NAMES[9],"DT trigger types",list(g3),list(g3.values()))
 g4=Counter("recoverable" if s["shadow_stage_reachability"]["S4"]["recovery_recoverable"] else "unrecoverable" for s in reg["scenarios"] if s["group"]==GROUPS[4]);bar(NAMES[10],"Recovery trigger strata",list(g4),list(g4.values()))
 for name,key,title in zip(NAMES[11:15],("H1_START_SAFE","H2_FEASIBILITY_AWARE","H3_DISCRETE_TIME","H4_PREDICTIVE_RECOVERY"),("G1 terminal transitions","G2 terminal transitions","G3 terminal transitions","G4 terminal transitions")): heat(name,title,trans[key])
 def deltas(metric): return [stats[k]["metrics"][metric]["mean_new_minus_old"] for k in ("H1_START_SAFE","H2_FEASIBILITY_AWARE","H3_DISCRETE_TIME","H4_PREDICTIVE_RECOVERY")]
 labels=["H1","H2","H3","H4"]
 bar(NAMES[15],"Paired progress differences",labels,deltas("progress_m"),"new-old (m)")
 bar(NAMES[16],"Paired QP infeasible differences",labels,deltas("qp_infeasible"),"new-old")
 bar(NAMES[17],"Paired reduced-constraint differences",labels,deltas("reduced_constraint_population_mean"),"new-old")
 bar(NAMES[18],"Paired runtime differences",labels,deltas("runtime_mean_s"),"new-old (s)")
 full=stats["H5_FULL"]["metrics"];bar(NAMES[19],"Full FAS versus SAFER",["completion","progress","QP infeasible","collision"],[full[x]["mean_new_minus_old"] for x in ("completion","progress_m","qp_infeasible","reference_collision")],"M4-M0")
 cats=[evidence["evidence"][k]["category"] for k in ("H1_START_SAFE","H2_FEASIBILITY_AWARE","H3_DISCRETE_TIME","H4_PREDICTIVE_RECOVERY")]; score={"REGRESSION":-1,"INACTIVE":0,"NOT_SUPPORTED":0,"PROMISING":1,"SUPPORTED":2};bar(NAMES[20],"Module evidence matrix",labels,[score[x] for x in cats],"evidence score")
 sm=smooth["method_summary"];bar(NAMES[21],"Smoothness diagnostics: control TV",list(METHODS),[sm[m]["control_tv"] for m in METHODS],"mean TV(u)")
 fc=Counter(x["terminal_state"] for x in failures["cases"]);bar(NAMES[22],"Failure terminals",list(fc),list(fc.values()))
 bar(NAMES[23],final["FINAL_STATUS"],["SUPPORTED/PROMISING","OTHER"],[sum(x in {"SUPPORTED","PROMISING"} for x in cats),sum(x not in {"SUPPORTED","PROMISING"} for x in cats)])
 assert all((TASK_ROOT/"figures"/n).exists() for n in NAMES); print(json.dumps({"status":"PASS_24_V2_FIGURES","count":len(NAMES)},sort_keys=True));return 0
if __name__=="__main__": raise SystemExit(main())
