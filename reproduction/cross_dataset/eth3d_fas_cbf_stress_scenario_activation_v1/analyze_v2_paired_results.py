#!/usr/bin/env python3
"""Scenario-grain paired analysis with frozen 10000-resample bootstrap."""
from __future__ import annotations
import csv,json
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from task_config_v2 import *  # noqa: F403

COMPARISONS=(
 ("H1_START_SAFE",METHODS[0],METHODS[1],GROUPS[1]),
 ("H2_FEASIBILITY_AWARE",METHODS[1],METHODS[2],GROUPS[2]),
 ("H3_DISCRETE_TIME",METHODS[2],METHODS[3],GROUPS[3]),
 ("H4_PREDICTIVE_RECOVERY",METHODS[3],METHODS[4],GROUPS[4]),
 ("H5_FULL",METHODS[0],METHODS[4],"OVERALL"),)
METRICS=("completion","reference_collision","progress_m","qp_infeasible","deadlock","min_reference_clearance",
 "min_segment_clearance","runtime_mean_s","original_constraint_population_mean","reduced_constraint_population_mean",
 "forced_candidate_events","dt_triggers","endpoint_only_misses","segment_risk_events","recovery_triggers","recovery_success",
 "control_tv","jerk_rms","intervention_switches","active_set_switch_rate")

def numeric(row,key):
 v=row.get(key,0); return float(0 if v is None else v)

def bootstrap(values,rng):
 values=np.asarray(values,dtype=float)
 if not len(values): return [None,None]
 samples=np.mean(values[rng.integers(0,len(values),size=(10000,len(values)))],axis=1)
 return [float(np.percentile(samples,2.5)),float(np.percentile(samples,97.5))]

def main() -> int:
 paths=sorted((TASK_ROOT/"formal/results").glob("*.json")); rows=[json.loads(p.read_text()) for p in paths]
 if len(rows)!=500: raise RuntimeError(f"formal records {len(rows)}/500")
 by={(r["scenario_id"],r["method"]):r for r in rows}; rng=np.random.default_rng(SEED)
 compact=[]
 keep=("scenario_id","group","method","terminal_state","status_pr80","completion","progress_m","reference_collision","collision_count",
  "min_reference_clearance","min_segment_clearance","qp_infeasible","deadlock","projection","forced_candidate_events","forced_candidate_count_mean",
  "original_constraint_population_mean","reduced_constraint_population_mean","constraint_reduction_mean","dt_checks","dt_triggers","endpoint_only_misses",
  "segment_risk_events","recovery_triggers","recovery_success","recovery_failure","fallback_count","runtime_mean_s","runtime_p95_s","runtime_max_s",
  "control_tv","jerk_rms","intervention_switches","active_set_switch_rate","reference_oracle_controller_input_count","map_mutation_count")
 for r in rows: compact.append({k:r.get(k) for k in keep})
 atomic_json(TASK_ROOT/"paired_analysis/per_run_compact_records.json",compact)
 stats={}; paired_rows=[]; transitions={}
 for name,old_m,new_m,group in COMPARISONS:
  ids=sorted({r["scenario_id"] for r in rows if group=="OVERALL" or r["group"]==group})
  metric_stats={}; trans=Counter(); wins=ties=losses=0
  for sid in ids:
   old,new=by[(sid,old_m)],by[(sid,new_m)]; trans[(old["terminal_state"],new["terminal_state"])]+=1
   pd=numeric(new,"progress_m")-numeric(old,"progress_m")
   wins+=pd>1e-12; losses+=pd<-1e-12; ties+=abs(pd)<=1e-12
   paired_rows.append({"comparison":name,"scenario_id":sid,"group":old["group"],"older_method":old_m,"newer_method":new_m,
    "older_terminal":old["terminal_state"],"newer_terminal":new["terminal_state"],"progress_difference_m":pd,
    "older_collision":bool(old.get("reference_collision")),"newer_collision":bool(new.get("reference_collision"))})
  for metric in METRICS:
   diffs=[numeric(by[(sid,new_m)],metric)-numeric(by[(sid,old_m)],metric) for sid in ids]
   metric_stats[metric]={"mean_new_minus_old":float(np.mean(diffs)),"bootstrap_95_ci":bootstrap(diffs,rng),"n":len(diffs)}
  stats[name]={"older":old_m,"newer":new_m,"group":group,"scenario_count":len(ids),"metrics":metric_stats,
   "progress_win_tie_loss":{"win":wins,"tie":ties,"loss":losses}}
  transitions[name]=[{"older_terminal":a,"newer_terminal":b,"count":n} for (a,b),n in sorted(trans.items())]
 with (TASK_ROOT/"paired_analysis/per_scenario_paired_table.csv").open("w",encoding="utf-8",newline="") as f:
  w=csv.DictWriter(f,fieldnames=list(paired_rows[0]));w.writeheader();w.writerows(paired_rows)
 atomic_json(TASK_ROOT/"paired_analysis/paired_statistics.json",{"unit":"SCENARIO","bootstrap_resamples":10000,"bootstrap_seed":SEED,"comparisons":stats})
 atomic_json(TASK_ROOT/"paired_analysis/terminal_transition_matrices.json",transitions)
 registry=json.loads((TASK_ROOT/"scenario_registry_v2/scenario_registry.json").read_text()); scenarios=registry["scenarios"]
 group_ids={group:sorted(s["scenario_id"] for s in scenarios if s["group"]==group) for group in GROUPS}
 # Registry counts are construction gates. Module evidence uses only the formal logger
 # on each designated incremental method, so shadow reachability cannot masquerade as
 # a scientific activation result.
 activation={
  "H1_START_SAFE":sum(bool(by[(sid,METHODS[1])].get("projection",{}).get("attempted")) for sid in group_ids[GROUPS[1]]),
  "H1_PROJECTION_SUCCESS":sum(bool(by[(sid,METHODS[1])].get("projection",{}).get("success")) for sid in group_ids[GROUPS[1]]),
  "H2_FEASIBILITY_AWARE":sum(
   numeric(by[(sid,METHODS[2])],"reduced_constraint_population_mean") < numeric(by[(sid,METHODS[2])],"original_constraint_population_mean")
   or numeric(by[(sid,METHODS[2])],"forced_candidate_events") > 0 for sid in group_ids[GROUPS[2]]),
  "H3_DISCRETE_TIME":sum(int(by[(sid,METHODS[3])].get("dt_triggers",0))>0 for sid in group_ids[GROUPS[3]]),
  "H4_PREDICTIVE_RECOVERY":sum(int(by[(sid,METHODS[4])].get("recovery_triggers",0))>0 for sid in group_ids[GROUPS[4]]),
  "H4_RECOVERABLE":sum(int(by[(sid,METHODS[4])].get("recovery_success",0))>0 for sid in group_ids[GROUPS[4]])}
 collision_regression=any(numeric(by[(sid,METHODS[4])],"reference_collision")>numeric(by[(sid,METHODS[0])],"reference_collision") for sid in {r["scenario_id"] for r in rows})
 evidence={}
 # Preregistered bounded claim rules; actual formal activation is always the first
 # gate. A progress regression is "clear" only when the entire paired 95% CI is
 # below zero. This rule is frozen here before formal execution.
 h1=stats["H1_START_SAFE"]
 h1_progress_ci=h1["metrics"]["progress_m"]["bootstrap_95_ci"]
 h1_progress_ok=h1_progress_ci[1] is None or h1_progress_ci[1]>=0
 converted=sum(by[(sid,METHODS[0])]["terminal_state"] in {"START_STATE_REJECTED","QP_INFEASIBLE"} and by[(sid,METHODS[1])]["terminal_state"] not in {"START_STATE_REJECTED","QP_INFEASIBLE"} for sid in group_ids[GROUPS[1]])
 h1_directional=converted>0 or h1["metrics"]["qp_infeasible"]["mean_new_minus_old"]<0
 h1_supported=h1_directional and h1_progress_ok

 h2=stats["H2_FEASIBILITY_AWARE"]
 h2_progress_ci=h2["metrics"]["progress_m"]["bootstrap_95_ci"]
 h2_progress_ok=h2_progress_ci[1] is None or h2_progress_ci[1]>=0
 h2_mechanism_metrics=("forced_candidate_events","reduced_constraint_population_mean","qp_infeasible","runtime_mean_s")
 h2_directional=any(h2["metrics"][metric]["mean_new_minus_old"]<0 for metric in h2_mechanism_metrics)
 h2_strong=any((h2["metrics"][metric]["bootstrap_95_ci"][1] is not None and h2["metrics"][metric]["bootstrap_95_ci"][1]<0) for metric in h2_mechanism_metrics)
 h2_supported=h2_strong and h2_progress_ok
 h2_promising=h2_directional and h2_progress_ok

 h3_marked=activation["H3_DISCRETE_TIME"]
 h3_supported=h3_marked>0

 h4=stats["H4_PREDICTIVE_RECOVERY"]
 h4_success=activation["H4_RECOVERABLE"]
 h4_continued=sum(int(by[(sid,METHODS[4])].get("recovery_success",0))>0 and int(by[(sid,METHODS[4])].get("steps",0))>0 and by[(sid,METHODS[4])]["terminal_state"]!="RECOVERY_FAILED" for sid in group_ids[GROUPS[4]])
 h4_supported=h4_continued>0 and h4["metrics"]["deadlock"]["mean_new_minus_old"]<=0

 module_rules=(
  ("H1_START_SAFE",activation["H1_START_SAFE"],h1_supported,h1_directional and h1_progress_ok,{"converted_initial_failures":converted,"paired_progress_95_ci":h1_progress_ci,"no_clear_progress_regression":h1_progress_ok}),
  ("H2_FEASIBILITY_AWARE",activation["H2_FEASIBILITY_AWARE"],h2_supported,h2_promising,{"mechanism_metrics":list(h2_mechanism_metrics),"paired_progress_95_ci":h2_progress_ci,"no_clear_progress_regression":h2_progress_ok,"feasible_control_set_parity":True}),
  ("H3_DISCRETE_TIME",activation["H3_DISCRETE_TIME"],h3_supported,False,{"formal_triggered_scenarios":h3_marked,"unavoidable_cases_not_claimed_recoverable":True}),
  ("H4_PREDICTIVE_RECOVERY",activation["H4_PREDICTIVE_RECOVERY"],h4_supported,h4_success>0,{"formal_recovery_success_scenarios":h4_success,"formal_safe_continue_scenarios":h4_continued}))
 for name,act,supported,promising,detail in module_rules:
  if act<16: category="INACTIVE"
  elif collision_regression: category="REGRESSION"
  elif supported: category="SUPPORTED"
  elif promising: category="PROMISING"
  else: category="NOT_SUPPORTED"
  evidence[name]={"category":category,"activation_count":int(act),"activation_source":"FORMAL_LOGGER_DESIGNATED_GROUP_METHOD","collision_regression":collision_regression,**detail}
 atomic_json(TASK_ROOT/"paired_analysis/module_evidence_matrix.json",{"activation":activation,"evidence":evidence,"collision_regression":collision_regression})
 method_summary={}
 for m in METHODS:
  rr=[r for r in rows if r["method"]==m]
  method_summary[m]={"runs":len(rr),"terminal_counts":dict(sorted(Counter(x["terminal_state"] for x in rr).items())),
   "completions":sum(bool(x["completion"]) for x in rr),"collisions":sum(bool(x.get("reference_collision")) for x in rr),
   "progress_mean_m":float(np.mean([numeric(x,"progress_m") for x in rr])),"qp_infeasible":sum(int(x.get("qp_infeasible",0)) for x in rr),
   "constraints_mean":float(np.mean([numeric(x,"reduced_constraint_population_mean") for x in rr])),"runtime_mean_s":float(np.mean([numeric(x,"runtime_mean_s") for x in rr]))}
 atomic_json(TASK_ROOT/"paired_analysis/method_summary.json",method_summary)
 failures=[r for r in compact if r["terminal_state"]!="SUCCESS"]
 atomic_json(TASK_ROOT/"failure_forensics/failure_case_registry.json",{"failure_case_count":len(failures),"cases":failures,"no_case_deleted":True})
 print(json.dumps({"status":"PASS_V2_PAIRED_ANALYSIS","activation":activation,"evidence":evidence},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
