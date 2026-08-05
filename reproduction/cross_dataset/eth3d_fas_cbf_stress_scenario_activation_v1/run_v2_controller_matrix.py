#!/usr/bin/env python3
"""Run exact PR #80 controls and add post-hoc V2 semantic logging only."""
from __future__ import annotations
import argparse,json,os,sys,time,traceback
from pathlib import Path
from task_config_v2 import *  # noqa: F403

if str(PR80_ROOT) not in sys.path: sys.path.insert(0,str(PR80_ROOT))
from eth3d_controller_core import LearnedEllipsoidMap,ReferenceMeshOracle  # type: ignore  # noqa: E402
from run_formal_paired_controller_benchmark import run_scenario  # type: ignore  # noqa: E402

STATUS_MAP={"SUCCESS":"SUCCESS","TIMEOUT":"TIMEOUT","START_STATE_REJECTED":"START_STATE_REJECTED","QP_INFEASIBLE":"QP_INFEASIBLE",
 "DT_VERIFICATION_BLOCKED":"DISCRETE_VERIFICATION_FAILED","RECOVERY_FAILED":"RECOVERY_FAILED","REFERENCE_COLLISION":"REFERENCE_COLLISION",
 "NUMERICAL_FAILURE":"NONFINITE","BOUND_VIOLATION":"NONFINITE","UNKNOWN_STOP":"TIMEOUT"}

def canonicalize(raw: dict, scenario: dict) -> dict:
 out=dict(raw); out["status_pr80"]=raw["status"]; out["terminal_state"]=STATUS_MAP.get(raw["status"],raw["status"])
 out["completion"]=out["terminal_state"]=="SUCCESS"; out["original_constraint_population_mean"]=float(raw.get("candidate_count_mean",0) or 0)
 out["reduced_constraint_population_mean"]=float(raw.get("active_constraints_mean",0) or 0)
 out["constraint_reduction_mean"]=out["original_constraint_population_mean"]-out["reduced_constraint_population_mean"]
 out["shadow_activation_reason"]=scenario["activation_reason"]; out["logger_only_posthoc_fields_added"]=True
 return out

def main() -> int:
 p=argparse.ArgumentParser(); p.add_argument("--mode",choices=("smoke","formal"),required=True); p.add_argument("--registry",type=Path,required=True); a=p.parse_args()
 if os.environ.get("CUDA_VISIBLE_DEVICES")!="1": raise RuntimeError("physical GPU 1 pin required")
 registry=json.loads(a.registry.read_text()); scenarios=registry["scenarios"]
 selected=([x for g in GROUPS for x in [r for r in scenarios if r["group"]==g][:2]] if a.mode=="smoke" else scenarios)
 out=TASK_ROOT/a.mode; results=out/"results"; results.mkdir(parents=True,exist_ok=True)
 identity={"map_ply_sha256":EXPECTED["map_ply_sha256"],"canonical_tree_sha256":EXPECTED["canonical_tree_sha256"],
  "scenario_registry_sha256":registry["registry_sha256"],"scenario_registry_raw_sha256":sha256_file(a.registry),"source_commit":EXPECTED["official_3dgs_commit"],
  "method_code_sha256":sha256_file(PR80_ROOT/"fas_cbf_modules.py"),"baseline_core_sha256":sha256_file(PR80_ROOT/"eth3d_controller_core.py"),
  "scientific_runner_sha256":sha256_file(PR80_ROOT/"run_formal_paired_controller_benchmark.py"),"logger_control_path_modified":False}
 manifest={"mode":a.mode,"state":"RUNNING","expected_run_count":len(selected)*len(METHODS),"terminal_run_count":0,"infrastructure_failure_count":0,
  "identity":identity,"methods":list(METHODS),"scenario_ids":[x["scenario_id"] for x in selected],"reference_reads_during_controller_decision":0}
 atomic_json(out/"run_manifest.json",manifest); learned=LearnedEllipsoidMap(CANONICAL_ROOT,SOURCE_ROOT,CONTROLLER_SNAPSHOT); oracle=ReferenceMeshOracle(REFERENCE_MESH)
 terminal=0
 for scenario in selected:
  for method in METHODS:
   trial=f"{scenario['scenario_id']}__{method}"; path=results/f"{trial}.json"
   try: raw=run_scenario(learned,oracle,scenario,method,identity); result=canonicalize(raw,scenario)
   except Exception as exc:
    result={**identity,"scenario_id":scenario["scenario_id"],"group":scenario["group"],"method":method,"terminal_state":"INFRASTRUCTURE_FAILURE",
      "status_pr80":"INFRASTRUCTURE_FAILURE","completion":False,"error":repr(exc),"traceback":traceback.format_exc(),"reference_oracle_controller_input_count":0}
    manifest["infrastructure_failure_count"]+=1
   atomic_json(path,result); terminal+=1; manifest["terminal_run_count"]=terminal; manifest["last_trial_id"]=trial; atomic_json(out/"run_manifest.json",manifest)
   print(json.dumps({"terminal":terminal,"expected":manifest["expected_run_count"],"trial":trial,"status":result["terminal_state"]}),flush=True)
   if result["terminal_state"]=="INFRASTRUCTURE_FAILURE": manifest["state"]="BLOCKED"; atomic_json(out/"run_manifest.json",manifest); return 2
 manifest["state"]="COMPLETED"; manifest["map_sha_after"]=sha256_file(MAP_PLY); atomic_json(out/"run_manifest.json",manifest)
 print(json.dumps({"status":f"PASS_V2_{a.mode.upper()}_CONTROLLER_MATRIX","terminal":terminal},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
