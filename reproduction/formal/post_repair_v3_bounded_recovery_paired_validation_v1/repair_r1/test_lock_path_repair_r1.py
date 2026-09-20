#!/usr/bin/env python3
"""CPU-only R1 lock-path tests and frozen scientific-semantics comparison."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, subprocess, sys
from pathlib import Path

REPAIR_DIR=Path(__file__).resolve().parent; TASK=REPAIR_DIR.parent; REPO=TASK.parents[2]
if str(TASK) not in sys.path: sys.path.insert(0,str(TASK))
BASE="6f6ac91be5ffa4ad7c0b8ed3d3851f3293c4979b"
TOKEN="EXECUTE_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_V1_R1"
CANONICAL="POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_EXECUTION_LOCK.json"
WRONG="POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_EXECUTION_LOCK.json"
PROTOCOL=TASK/"POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_PROTOCOL.json"; LOCK=TASK/CANONICAL
ATTEMPT0=Path("/disk1/zlab/v3_repair_records/post_repair_v3_bounded_recovery_paired_validation_v1_20260920")
RETRY1=Path("/disk1/zlab/v3_repair_records/post_repair_v3_bounded_recovery_paired_validation_v1_retry1_20260920")
SCIENTIFIC_KEYS=("cohort","environment","local_infrastructure_bindings","local_binding_authority","map","geometry","dynamics","recovery","engineering_pilot_authority","reference_authority","historical_active_authority","primary_scientific_gates","boundary_contract","hard_zero_integrity_gates","recovery_unknown_and_exception_policy","routing_diagnostics_role","historical_active_diagnostic_role","analysis_authority","decision_contract","scientific_boundary","freeze_execution_counts","only_next_task_after_freeze_pass")

def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git(*args,binary=False):
    r=subprocess.run(["git","-C",str(REPO),*args],check=True,capture_output=True,text=not binary); return r.stdout if binary else r.stdout.strip()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec); sys.modules[name]=module; spec.loader.exec_module(module); return module
def write(path,value): Path(path).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")

def equivalence():
    current=read(PROTOCOL); original=json.loads(git("show",f"{BASE}:reproduction/formal/post_repair_v3_bounded_recovery_paired_validation_v1/{PROTOCOL.name}",binary=True))
    comparisons={key:{"equal":original[key]==current[key],"original_sha256":hashlib.sha256(json.dumps(original[key],sort_keys=True,separators=(",",":")).encode()).hexdigest(),"retry1_sha256":hashlib.sha256(json.dumps(current[key],sort_keys=True,separators=(",",":")).encode()).hexdigest()} for key in SCIENTIFIC_KEYS}
    diffs=[key for key,value in comparisons.items() if not value["equal"]]
    result={"schema":"FORMAL85_R1_SCIENTIFIC_SEMANTICS_EQUIVALENCE_AUDIT_V1","status":"PASS_SCIENTIFIC_SEMANTICS_EQUIVALENCE_R1" if not diffs else "FAIL_SCIENTIFIC_SEMANTICS_DRIFT_R1","base_head":BASE,"scientific_fields":list(SCIENTIFIC_KEYS),"comparisons":comparisons,"scientific_diff_fields":diffs,"scientific_diff_count":len(diffs),"allowed_execution_identity_changes":["base_head","future_result_root","future_tmux_session","execution_authorization_token","canonical_execution_lock_basename","execution_attempt"],"scientific_semantics_changed":False if not diffs else True}
    write(REPAIR_DIR/"SCIENTIFIC_SEMANTICS_EQUIVALENCE_AUDIT.json",result); return result

def run_tests():
    p=read(PROTOCOL); lock=read(LOCK); validation=load("formal85_r1_validator_test",TASK/"validate_post_repair_v3_bounded_recovery_paired_validation_v1.py")
    runner=load("formal85_r1_runner_test",TASK/"run_post_repair_v3_bounded_recovery_trial_v1.py"); launcher=load("formal85_r1_launcher_test",TASK/"launch_post_repair_v3_bounded_recovery_paired_validation_v1.py")
    pre=read(REPAIR_DIR/"PRE_REPAIR_LOCK_PATH_REPRODUCTION.json"); eq=read(REPAIR_DIR/"SCIENTIFIC_SEMANTICS_EQUIVALENCE_AUDIT.json")
    launcher_text=(TASK/"launch_post_repair_v3_bounded_recovery_paired_validation_v1.py").read_text(encoding="utf-8"); monitor=(TASK/"monitor_post_repair_v3_bounded_recovery_paired_validation_v1.py").read_text(encoding="utf-8"); analyzer=(TASK/"analyze_post_repair_v3_bounded_recovery_paired_validation_v1.py").read_text(encoding="utf-8")
    checks={
      "T01_pre_repair_reproduction":pre["status"]=="PASS_REPRODUCE_FORMAL85_LOCK_PATH_MISMATCH_R1",
      "T02_runner_validator_lock":runner.LOCK.resolve()==validation.LOCK.resolve(),
      "T03_canonical_lock_exactly_once":sorted(TASK.glob("*EXECUTION_LOCK*.json"))==[LOCK],
      "T04_wrong_basename_absent":not (TASK/WRONG).exists(),
      "T05_runner_lock_hash":runner.sha(runner.LOCK)==sha(LOCK),
      "T06_launcher_lock_binding":launcher.LOCK.resolve()==LOCK.resolve(),
      "T07_authorization_consistency":p["execution_authorization_token"]==lock["execution_authorization_token"]==validation.TOKEN==TOKEN and launcher_text.count(TOKEN)>=2,
      "T08_retry1_root_session":p["future_result_root"]==lock["future_result_root"]==str(RETRY1) and p["future_tmux_session"]==lock["future_tmux_session"]==validation.SESSION,
      "T09_attempt0_immutable_not_selected":ATTEMPT0.is_dir() and str(ATTEMPT0)!=p["future_result_root"] and p["execution_attempt"]["attempt0"]["mutation_authority"] is False,
      "T10_formal85_order":p["cohort"]["trial_order"]==validation.TRIALS and lock["trial_order_sha256"]=="307359644268a4c06c102442cebbd99f9dcb42e9c7917ba752aa01ef6349b12c",
      "T11_scientific_equivalence":eq["scientific_diff_count"]==0 and eq["status"]=="PASS_SCIENTIFIC_SEMANTICS_EQUIVALENCE_R1",
      "T12_map_geometry_dynamics_recovery":all(eq["comparisons"][key]["equal"] for key in ("map","geometry","dynamics","recovery")),
      "T13_reference_authority":eq["comparisons"]["reference_authority"]["equal"],
      "T14_historical_active_authority":eq["comparisons"]["historical_active_authority"]["equal"],
      "T15_monitor_percentage_contract":all(x in monitor for x in ("BAR_WIDTH = 30","TRIAL COMPLETION","CYCLE BUDGET","CURRENT TRIAL","DONE-BOUNDARY","--json","--all-trials")),
      "T16_analyzer_contract":all(x in analyzer for x in ("--post-collection-authorized","ANALYSIS_REQUIRES_85_OF_85_IMMUTABLE_LOCKS","10000","20260911","-0.02")),
      "T17_protected_runtime_diff":not git("diff","--name-only",BASE,"--","cbf","splat","dynamics","run.py","reproduction/runtime"),
      "T18_no_execution":set(p["freeze_execution_counts"].values())=={0} and not RETRY1.exists() and subprocess.run(["tmux","has-session","-t",p["future_tmux_session"]],capture_output=True).returncode!=0,
    }
    failed=[name for name,ok in checks.items() if not ok]
    result={"schema":"FORMAL85_R1_CPU_TEST_RESULTS_V1","status":"PASS_FORMAL85_R1_CPU_TESTS" if not failed else "FAIL_FORMAL85_R1_CPU_TESTS","test_count":len(checks),"pass_count":sum(checks.values()),"failed":failed,"tests":{name:"PASS" if ok else "FAIL" for name,ok in checks.items()},"gpu_run_count":0,"tmux_created_count":0,"real_trial_run_count":0,"real_plantcommit_count":0}
    write(REPAIR_DIR/"CPU_TEST_RESULTS.json",result)
    if failed: raise RuntimeError("CPU_TEST_FAILURE:"+",".join(failed))
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--equivalence-only",action="store_true"); args=parser.parse_args()
    eq=equivalence()
    if eq["scientific_diff_count"]: raise RuntimeError("SCIENTIFIC_SEMANTICS_DRIFT")
    print(json.dumps(eq if args.equivalence_only else run_tests(),sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
