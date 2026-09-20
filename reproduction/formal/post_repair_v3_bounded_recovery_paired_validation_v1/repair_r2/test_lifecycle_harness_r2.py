#!/usr/bin/env python3
"""CPU/static/integration tests for the Formal85 R2 execution harness."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, subprocess, sys, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent; TASK=HERE.parent; REPO=TASK.parents[2]
if str(TASK) not in sys.path: sys.path.insert(0,str(TASK))
if str(REPO) not in sys.path: sys.path.insert(0,str(REPO))
BASE="bc96a745af658aa2c8df404fba403dbed4c7b7fe"
PROTOCOL=TASK/"POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_PROTOCOL.json"; LOCK=TASK/"POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_EXECUTION_LOCK.json"
TOKEN="EXECUTE_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_V1_R3"
SCIENTIFIC_KEYS=("cohort","environment","local_infrastructure_bindings","local_binding_authority","map","geometry","dynamics","recovery","engineering_pilot_authority","reference_authority","historical_active_authority","primary_scientific_gates","boundary_contract","hard_zero_integrity_gates","recovery_unknown_and_exception_policy","routing_diagnostics_role","historical_active_diagnostic_role","analysis_authority","decision_contract","scientific_boundary","freeze_execution_counts")

def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git(*args,binary=False):
    r=subprocess.run(["git","-C",str(REPO),*args],check=True,capture_output=True,text=not binary); return r.stdout if binary else r.stdout.strip()
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec); sys.modules[name]=module; spec.loader.exec_module(module); return module
def write(path,value): Path(path).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")

def equivalence():
    current=read(PROTOCOL); original=json.loads(git("show",f"{BASE}:reproduction/formal/post_repair_v3_bounded_recovery_paired_validation_v1/{PROTOCOL.name}",binary=True))
    comparisons={key:{"equal":original[key]==current[key],"base_sha256":hashlib.sha256(json.dumps(original[key],sort_keys=True,separators=(",",":")).encode()).hexdigest(),"retry2_sha256":hashlib.sha256(json.dumps(current[key],sort_keys=True,separators=(",",":")).encode()).hexdigest()} for key in SCIENTIFIC_KEYS}
    diffs=[key for key,value in comparisons.items() if not value["equal"]]
    result={"schema":"FORMAL85_R2_SCIENTIFIC_SEMANTICS_EQUIVALENCE_AUDIT_V1","status":"PASS_SCIENTIFIC_SEMANTICS_EQUIVALENCE_R2" if not diffs else "FAIL_SCIENTIFIC_SEMANTICS_DRIFT_R2","base_head":BASE,"scientific_fields":list(SCIENTIFIC_KEYS),"comparisons":comparisons,"scientific_diff_fields":diffs,"scientific_diff_count":len(diffs),"allowed_execution_identity_changes":["task_type","base_head","future_result_root","future_tmux_session","execution_authorization_token","execution_attempt","only_next_task_after_freeze_pass"],"scientific_semantics_changed":bool(diffs)}
    write(HERE/"SCIENTIFIC_SEMANTICS_EQUIVALENCE_AUDIT.json",result); return result

def run_tests():
    import validate_post_repair_v3_bounded_recovery_paired_validation_v1 as validator
    p=read(PROTOCOL); lock=read(LOCK); runner=load("formal85_r2_runner_test",TASK/"run_post_repair_v3_bounded_recovery_trial_v1.py"); launcher=load("formal85_r2_launcher_test",TASK/"launch_post_repair_v3_bounded_recovery_paired_validation_v1.py")
    retry1=read(HERE/"RETRY1_FAILURE_AUTHORITY.json"); retry2=read(HERE/"RETRY2_FAILURE_AUTHORITY.json"); eq=read(HERE/"SCIENTIFIC_SEMANTICS_EQUIVALENCE_AUDIT.json")
    runner_text=(TASK/"run_post_repair_v3_bounded_recovery_trial_v1.py").read_text(encoding="utf-8"); launcher_text=(TASK/"launch_post_repair_v3_bounded_recovery_paired_validation_v1.py").read_text(encoding="utf-8"); monitor=(TASK/"monitor_post_repair_v3_bounded_recovery_paired_validation_v1.py").read_text(encoding="utf-8"); analyzer=(TASK/"analyze_post_repair_v3_bounded_recovery_paired_validation_v1.py").read_text(encoding="utf-8")
    P=validator.ValidationPhase; errors=validator.phase_state_errors
    matrix_ok=(not errors(P.FREEZE,root_exists=False,tmux_is_active=False,caller_in_tmux=False,marker_exists=False,batch_stop_exists=False,batch_complete_exists=False,immutable_locks=0,child_auth_exists=False) and not errors(P.PRELAUNCH,root_exists=False,tmux_is_active=False,caller_in_tmux=False,marker_exists=False,batch_stop_exists=False,batch_complete_exists=False,immutable_locks=0,child_auth_exists=False) and not errors(P.BATCH_RUNTIME,root_exists=True,tmux_is_active=True,caller_in_tmux=True,marker_exists=True,batch_stop_exists=False,batch_complete_exists=False,immutable_locks=0,child_auth_exists=False) and not errors(P.CHILD_RUNTIME,root_exists=True,tmux_is_active=True,caller_in_tmux=True,marker_exists=True,batch_stop_exists=False,batch_complete_exists=False,immutable_locks=0,child_auth_exists=True) and not errors(P.POSTCOLLECTION,root_exists=True,tmux_is_active=False,caller_in_tmux=False,marker_exists=True,batch_stop_exists=False,batch_complete_exists=True,immutable_locks=85,child_auth_exists=False))
    child_auth_ok=False; child_auth_bad=False; original_root=validator.RESULT_ROOT; original_token=os.environ.get(validator.CHILD_TOKEN_ENV)
    with tempfile.TemporaryDirectory(prefix="formal85_r2_child_") as temp:
        root=Path(temp); validator.RESULT_ROOT=root; token="fixture-token"; os.environ[validator.CHILD_TOKEN_ENV]=token
        auth={"trial_id":66,"result_root":str(root),"source_head":validator.git("rev-parse","HEAD"),"protocol_sha256":validator.sha(validator.PROTOCOL),"execution_lock_sha256":validator.sha(validator.LOCK),"token_sha256":hashlib.sha256(token.encode()).hexdigest(),"parent_pid":os.getpid()}
        (root/validator.CHILD_AUTH).write_text(json.dumps(auth),encoding="utf-8"); (root/"raw/trial_66").mkdir(parents=True); child_auth_ok=validator._validate_child_authority(p,66); (root/"raw/trial_66/runtime_trace_lock.json").write_text("{}",encoding="utf-8"); child_auth_bad=not validator._validate_child_authority(p,66)
    validator.RESULT_ROOT=original_root
    if original_token is None: os.environ.pop(validator.CHILD_TOKEN_ENV,None)
    else: os.environ[validator.CHILD_TOKEN_ENV]=original_token
    delegate=runner.load_delegate(66)
    from reproduction.runtime.active_runtime_assurance_v2.bounded_recovery import SOURCE, GENERATOR, DIRECTIONS
    protected=("cbf","splat","dynamics","run.py","reproduction/runtime")
    checks={
      "T01_failed_attempt_authority":retry1["root_cause"]=="FORMAL85_RETRY1_CHILD_RUNTIME_VALIDATOR_PHASE_MISMATCH" and retry2["root_cause"]=="FORMAL85_RETRY2_CHILD_RUNTIME_RAW_DIRECTORY_PHASE_MISMATCH" and retry1["completed_public_cycles"]==retry1["plant_commit_count"]==retry2["completed_public_cycles"]==retry2["plant_commit_count"]==0,
      "T02_phase_matrix":matrix_ok and set(validator.PHASE_CONTRACT)==set(P),
      "T03_prelaunch_active_tmux_fails":"TMUX_STATE" in errors(P.PRELAUNCH,root_exists=False,tmux_is_active=True,caller_in_tmux=True,marker_exists=False,batch_stop_exists=False,batch_complete_exists=False,immutable_locks=0,child_auth_exists=False),
      "T04_child_active_tmux_passes":not errors(P.CHILD_RUNTIME,root_exists=True,tmux_is_active=True,caller_in_tmux=True,marker_exists=True,batch_stop_exists=False,batch_complete_exists=False,immutable_locks=0,child_auth_exists=True),
      "T05_child_root_contract":"ROOT_STATE" in errors(P.CHILD_RUNTIME,root_exists=False,tmux_is_active=True,caller_in_tmux=True,marker_exists=True,batch_stop_exists=False,batch_complete_exists=False,immutable_locks=0,child_auth_exists=True),
      "T06_child_authority_fixture":child_auth_ok and child_auth_bad,
      "T07_canonical_lock_consistency":runner.LOCK.resolve()==launcher.LOCK.resolve()==validator.LOCK.resolve()==LOCK.resolve() and delegate.EXECUTION_LOCK_PATH.resolve()==LOCK.resolve(),
      "T08_retry3_token_consistency":p["execution_authorization_token"]==lock["execution_authorization_token"]==validator.TOKEN==TOKEN and launcher_text.count(TOKEN)>=2,
      "T09_runtime_callsites_explicit":runner_text.count("ValidationPhase.CHILD_RUNTIME")>=2 and "require_absent_root=False" not in runner_text and "validate_freeze(" not in runner_text,
      "T10_imports_no_execution":callable(runner.main) and callable(delegate.run_one) and not Path(p["future_result_root"]).exists(),
      "T11_projected_protocol_semantics":runner.projected_v3_protocol()["maximum_completed_cycles_per_trial"]==500 and runner.projected_v3_protocol()["trial_order"]==validator.TRIALS,
      "T12_local_bindings":all((REPO/item["path"]).is_symlink() and (REPO/item["path"]).resolve()==Path(item["target"]).resolve() for item in p["local_infrastructure_bindings"]),
      "T13_startup_prerequisites":delegate.PROTOCOL_PATH.resolve()==PROTOCOL.resolve() and callable(delegate.build_v3_stack) and (SOURCE,GENERATOR,list(DIRECTIONS))==(p["recovery"]["source"],p["recovery"]["generator"],p["recovery"]["candidate_order"]),
      "T14_scientific_equivalence":eq["scientific_diff_count"]==0 and eq["status"]=="PASS_SCIENTIFIC_SEMANTICS_EQUIVALENCE_R2",
      "T15_protected_runtime_diff":not git("diff","--name-only",BASE,"--",*protected),
      "T16_percent_monitor":all(x in monitor for x in ("BAR_WIDTH = 30","TRIAL COMPLETION","CYCLE BUDGET","CURRENT TRIAL","DONE-MAX","DONE-BOUNDARY","--json","--all-trials")),
      "T17_analyzer_postcollection_only":"ValidationPhase.POSTCOLLECTION" in analyzer and "--post-collection-authorized" in analyzer and "ANALYSIS_REQUIRES_85_OF_85_IMMUTABLE_LOCKS" in analyzer,
      "T18_failed_attempt_hashes_immutable":all(path.is_file() and path.stat().st_size==size and sha(path)==digest for root,files in validator.ATTEMPT_FILES.items() for rel,(size,digest) in files.items() for path in [root/rel]),
    }
    failed=[name for name,ok in checks.items() if not ok]; result={"schema":"FORMAL85_R2_CPU_STATIC_INTEGRATION_RESULTS_V1","status":"PASS_FORMAL85_R2_CPU_STATIC_INTEGRATION" if not failed else "FAIL_FORMAL85_R2_CPU_STATIC_INTEGRATION","test_count":len(checks),"pass_count":sum(checks.values()),"failed":failed,"tests":{name:"PASS" if ok else "FAIL" for name,ok in checks.items()},"gpu_run_count":0,"tmux_created_count":0,"real_trial_run_count":0,"real_plantcommit_count":0}
    write(HERE/"CPU_STATIC_INTEGRATION_RESULTS.json",result)
    if failed: raise RuntimeError("CPU_STATIC_INTEGRATION_FAILURE:"+",".join(failed))
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--equivalence-only",action="store_true"); args=parser.parse_args(); eq=equivalence()
    if eq["scientific_diff_count"]: raise RuntimeError("SCIENTIFIC_SEMANTICS_DRIFT")
    print(json.dumps(eq if args.equivalence_only else run_tests(),sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
