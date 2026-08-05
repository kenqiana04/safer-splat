#!/usr/bin/env python3
"""Reconcile 50 smoke records with locked shadow activation and identities."""
import json
from task_config_v2 import *  # noqa: F403
def main():
 reg=json.loads((TASK_ROOT/"scenario_registry_v2/scenario_registry.json").read_text()); selected=[x for g in GROUPS for x in [r for r in reg["scenarios"] if r["group"]==g][:2]]
 rows=[json.loads(p.read_text()) for p in sorted((TASK_ROOT/"smoke/results").glob("*.json"))];by={(r["scenario_id"],r["method"]):r for r in rows}; mismatches=[]
 for s in selected:
  sid=s["scenario_id"]; sh=s["shadow_stage_reachability"]
  if s["group"]==GROUPS[0]:
   for m in METHODS[1:]:
    r=by[(sid,m)];
    if r.get("projection",{}).get("attempted") or int(r.get("dt_triggers",0)) or int(r.get("recovery_triggers",0)):mismatches.append([sid,m,"G0_NONTRIGGER"])
  if s["group"]==GROUPS[1]:
   r=by[(sid,METHODS[1])]; expected=(sh["S1"]["projection_attempted"],sh["S1"]["projection_success"]);actual=(bool(r.get("projection",{}).get("attempted")),bool(r.get("projection",{}).get("success")))
   if expected!=actual:mismatches.append([sid,METHODS[1],"H1",expected,actual])
  if s["group"]==GROUPS[2]:
   r=by[(sid,METHODS[2])]; actual=float(r.get("reduced_constraint_population_mean",0))<float(r.get("original_constraint_population_mean",0))
   if not actual:mismatches.append([sid,METHODS[2],"H2"])
  if s["group"]==GROUPS[3]:
   r=by[(sid,METHODS[3])]
   if int(r.get("dt_triggers",0))<=0:mismatches.append([sid,METHODS[3],"H3"])
  if s["group"]==GROUPS[4]:
   r=by[(sid,METHODS[4])]
   if int(r.get("recovery_triggers",0))<=0:mismatches.append([sid,METHODS[4],"H4"])
 gates={"records":len(rows)==50,"no_infrastructure":all(r["terminal_state"]!="INFRASTRUCTURE_FAILURE" for r in rows),"identity":all(r["scenario_registry_sha256"]==reg["registry_sha256"] and r["map_ply_sha256"]==EXPECTED["map_ply_sha256"] for r in rows),"shadow_actual_match":not mismatches,"no_reference_leakage":all(int(r.get("reference_oracle_controller_input_count",0))==0 for r in rows),"no_map_mutation":all(int(r.get("map_mutation_count",0))==0 for r in rows)}
 out={"status":"PASS_V2_SMOKE_GATE" if all(gates.values()) else "V2_SMOKE_GATE_FAILED","gates":gates,"mismatches":mismatches,"records":len(rows)};atomic_json(TASK_ROOT/"smoke/smoke_validation.json",out);print(json.dumps(out,sort_keys=True))
 if not all(gates.values()):raise RuntimeError(out)
 return 0
if __name__=="__main__":raise SystemExit(main())
