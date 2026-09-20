#!/usr/bin/env python3
"""CPU-only Retry1 freeze/prelaunch validator; never executes a trial."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, os, subprocess, sys, tempfile
from pathlib import Path

TASK=Path(__file__).resolve().parent; REPO=TASK.parents[2]
PROTOCOL=TASK/"POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_PROTOCOL.json"
CANONICAL_LOCK_BASENAME="POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_EXECUTION_LOCK.json"
WRONG_LOCK_BASENAME="POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_EXECUTION_LOCK.json"
LOCK=TASK/CANONICAL_LOCK_BASENAME
BASE="6f6ac91be5ffa4ad7c0b8ed3d3851f3293c4979b"; PILOT_FREEZE="9ab6ad224f0deefbbbdc34f165281a562c0b19cf"
REPAIR="2102c8401b61ca8fe74123ab51e8fc9c27ed0895"; IMPL="8184b0ecec20b6e84b1745518903b87bbb5cde8f"; GATE0="18ba8ed8aa3b4acc326426e05808bd5abe67561c"; RETRY2="abea482dc5bf49ed09cc224dedb7019acba67515"
BRANCH="repair-post-repair-v3-bounded-recovery-formal85-lock-path-r1"
ORIGIN="git@github-kenqiana04-safer-splat-current:kenqiana04/safer-splat.git"
TOKEN="EXECUTE_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_V1_R1"
RESULT_ROOT=Path("/disk1/zlab/v3_repair_records/post_repair_v3_bounded_recovery_paired_validation_v1_retry1_20260920")
SESSION="post_repair_v3_bounded_recovery_paired_validation_v1_retry1"
ATTEMPT0_ROOT=Path("/disk1/zlab/v3_repair_records/post_repair_v3_bounded_recovery_paired_validation_v1_20260920")
TASK_PREFIX="reproduction/formal/post_repair_v3_bounded_recovery_paired_validation_v1/"
SOURCE_PROTOCOL="reproduction/formal/post_repair_v3_paired_validation_v1/POST_REPAIR_V3_PAIRED_PROTOCOL.json"
TRIALS=[66,74,9,12,73,26,79,31,54,18,19,88,38,8,28,29,0,24,37,98,27,91,2,78,76,80,82,99,56,21,33,44,14,16,61,23,6,96,43,47,51,69,59,63,42,13,4,93,39,49,97,60,83,36,67,86,3,81,87,71,20,53,7,58,40,89,94,68,48,92,34,72,17,32,62,41,52,64,22,84,11,57,1,46,77]
HARNESS=("run_post_repair_v3_bounded_recovery_trial_v1.py","launch_post_repair_v3_bounded_recovery_paired_validation_v1.py","monitor_post_repair_v3_bounded_recovery_paired_validation_v1.py","analyze_post_repair_v3_bounded_recovery_paired_validation_v1.py","validate_post_repair_v3_bounded_recovery_paired_validation_v1.py","freeze_post_repair_v3_bounded_recovery_paired_validation_v1.py")
ATTEMPT0_FILES={
 "BATCH_STOP.json":(98,"430595f6e5bb87d6fd473ae3880e8fa847acc69a406f02a41c7f4c061e6919a8"),
 "POST_REPAIR_V3_BOUNDED_RECOVERY_LAUNCH_AUTHORIZATION.json":(1163,"5adf09483c65e7c92ebab5c2f79ec9d19d66c5ed10fe65fe61f2ea975f697a87"),
 "parent_failures/trial_66/stdout.log":(0,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
 "parent_failures/trial_66/stderr.log":(1732,"c4a98cbe4b13e47b7e6ed9eac68b71b6c179ade38970bb37ae49d9f75783a34e"),
 "parent_failures/trial_66/process_exit_code.txt":(2,"4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865"),
 "parent_failures/trial_66/gpu_released.txt":(5,"a17fcf0a2f50e2d495e4f90ce263410edc183add6c62699a2facbccf60410f74")}

def read(path:Path): return json.loads(path.read_text(encoding="utf-8"))
def sha(path:Path)->str: return hashlib.sha256(path.read_bytes()).hexdigest()
def semantic_hash(value)->str: return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def git(*args:str,binary:bool=False):
    r=subprocess.run(["git","-C",str(REPO),*args],check=True,capture_output=True,text=not binary); return r.stdout if binary else r.stdout.strip()
def tmux_active(session:str=SESSION)->bool: return subprocess.run(["tmux","has-session","-t",session],capture_output=True).returncode==0
def load_module(name:str,path:Path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError("MODULE_SPEC_UNAVAILABLE:"+str(path))
    module=importlib.util.module_from_spec(spec); sys.modules[name]=module; spec.loader.exec_module(module); return module

def validate_freeze(*,require_lock:bool,require_absent_root:bool=True,require_clean:bool=False)->dict:
    p=read(PROTOCOL); checks={}
    def need(name,ok):
        checks[name]="PASS" if ok else "FAIL"
        if not ok: raise RuntimeError("FORMAL85_R1_"+name.upper()+"_FAIL")
    need("schema",p["schema"]=="POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_PROTOCOL_V1")
    need("branch",git("branch","--show-current")==BRANCH); need("origin",git("remote","get-url","origin")==ORIGIN)
    need("base",git("merge-base",BASE,"HEAD")==BASE and p["base_head"]==BASE)
    need("lineage",[p["implementation_head"],p["original_bounded_recovery_implementation_head"],p["gate0_head"],p["retry2_freeze_head"],p["engineering_pilot_freeze_head"]]==[REPAIR,IMPL,GATE0,RETRY2,PILOT_FREEZE])
    source_bytes=git("show",f"{BASE}:{SOURCE_PROTOCOL}",binary=True); source=json.loads(source_bytes)
    need("formal85_source_sha",hashlib.sha256(source_bytes).hexdigest()==p["cohort"]["source_sha256"])
    need("formal85_order",source["cohort"]["trial_order"]==p["cohort"]["trial_order"]==p["cohort"]["trial_ids"]==TRIALS)
    need("formal85_order_hash",semantic_hash(TRIALS)=="307359644268a4c06c102442cebbd99f9dcb42e9c7917ba752aa01ef6349b12c"==p["cohort"]["source_trial_order_sha256"])
    c=p["cohort"]; need("cohort_execution",len(set(TRIALS))==85 and c["seed"]==0 and c["maximum_completed_cycles_per_trial"]==500 and c["serial_execution"] and c["separate_process_per_trial"] and not c["automatic_retry"])
    need("future_identity",str(RESULT_ROOT)==p["future_result_root"] and p["future_tmux_session"]==SESSION and p["execution_authorization_token"]==TOKEN)
    need("canonical_lock_protocol",p["canonical_execution_lock_basename"]==CANONICAL_LOCK_BASENAME)
    need("result_root_state",(not RESULT_ROOT.exists()) if require_absent_root else RESULT_ROOT.is_dir()); need("tmux_absent",not tmux_active())
    need("attempt0_tmux_absent",not tmux_active("post_repair_v3_bounded_recovery_paired_validation_v1")); need("freeze_counts",set(p["freeze_execution_counts"].values())=={0})
    attempt=p["execution_attempt"]["attempt0"]
    need("attempt0_lineage",attempt["root"]==str(ATTEMPT0_ROOT) and attempt["trial_id"]==66 and attempt["process_exit_code"]==1 and attempt["completed_public_cycles"]==attempt["plant_commit_count"]==0 and attempt["scientific_authority"]=="NONE_PRE_CYCLE_FAILURE" and not attempt["mutation_authority"])
    need("attempt0_root_distinct",ATTEMPT0_ROOT!=RESULT_ROOT and ATTEMPT0_ROOT.is_dir())
    for rel,(size,digest) in ATTEMPT0_FILES.items():
        path=ATTEMPT0_ROOT/rel; need("attempt0_"+rel.replace("/","_").replace(".","_"),path.is_file() and path.stat().st_size==size and sha(path)==digest)
    need("attempt0_no_raw_trial",not (ATTEMPT0_ROOT/"raw/trial_66").exists()); need("attempt0_no_complete",not (ATTEMPT0_ROOT/"BATCH_COMPLETE.json").exists())
    e=p["environment"]; need("environment",e["python"]=="/disk1/zlab/conda_envs/safer_splat_official/bin/python" and e["CUDA_VISIBLE_DEVICES"]=="1" and e["process_visible_device"]=="cuda:0" and e["PYTHONHASHSEED"]=="0" and e["PYTHONNOUSERSITE"]==e["PYTHONDONTWRITEBYTECODE"]=="1" and e["CUBLAS_WORKSPACE_CONFIG"]==":4096:8")
    for item in p["local_infrastructure_bindings"]:
        path=REPO/item["path"]; need("binding_"+item["path"].replace("/","_"),path.is_symlink() and os.readlink(path)==item["target"] and Path(item["target"]).exists() and bool(git("check-ignore",item["path"])))
    need("binding_authority",p["local_binding_authority"]=="EXECUTION_HARNESS_ONLY_NO_SCIENTIFIC_AUTHORITY")
    for item in p["map"]["artifacts"]:
        path=Path(p["map"]["root"])/item["relative_path"]; need("map_"+item["relative_path"].replace("/","_"),path.stat().st_size==item["size"] and sha(path)==item["sha256"])
    need("map_identity",p["map"]["identity"]=="c9eade9ca89b741768a0ca33b3a755b2656402864f121aefdceaed4b0174f7c8")
    need("geometry",p["geometry"]=={"coordinate_unit":"q","hard_radius_q":0.015,"runtime_margin_q":0.0,"effective_radius_q":0.015,"rho_seg_q":0.0,"epsilon":None,"historical_diagnostic_radius_q":0.025,"historical_diagnostic_runtime_authority":False})
    d=p["dynamics"]; need("dynamics",d["identity"]=="POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1" and d["dt"]==0.05 and d["proposal_source"]=="CURRENT_PRIMARY_CBF_QP" and d["actuator_bounds"]==d["velocity_bounds"]==[-0.1,0.1])
    r=p["recovery"]; need("recovery",(r["source"],r["generator"],r["family"],r["M"],r["candidate_order"])==("SOURCE_BOUNDED_LOCAL_RECOVERY_V1","AXIS_EXTREMA_F32_V1","F1_AXIS_EXTREMA_ONLY",6,["+x","-x","+y","-y","+z","-z"]) and not r["parameter_tuning_authorized"])
    pilot=p["engineering_pilot_authority"]; ps=read(Path(pilot["root"])/"PILOT_SUMMARY.json")
    need("pilot_authority",ps["status"]==pilot["status"]=="PASS_BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_V1" and ps["engineering_decision_signal"]==pilot["engineering_decision"]=="READY_FOR_FORMAL_PAIRED_VALIDATION" and not pilot["source_mutation_authority"] and not pilot["scientific_parameter_selection_authority"])
    ref=p["reference_authority"]; reuse=json.loads(git("show",f"{BASE}:{ref['reuse_lock']}",binary=True))
    need("reference_authority",reuse["status"]=="PASS_REFERENCE_REUSE_IDENTITY_RESOLVED" and reuse["reference_arm_count"]==85 and set(reuse["reference_trial_ids"])==set(TRIALS) and reuse["reference_rerun_authorized"] is False and ref["hard_violation_trials"]==ref["unknown_segments"]==0)
    hist=p["historical_active_authority"]; old=read(Path(hist["root"])/"POST_REPAIR_V3_FINAL_ACCEPTANCE.json")
    need("historical_active",old["new_post_repair_scientific_result"]==hist["verdict"]=="FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE" and hist["role"]=="HISTORICAL_REPAIRED_ACTIVE_DIAGNOSTIC_ONLY" and not hist["historical_result_rewritten"])
    hs=p["primary_scientific_gates"]["hard_safety"]; need("hard_safety_contract",hs["radius_q"]==0.015 and hs["epsilon"] is None and hs["negative_clearance_rule"]=="ANY_EXACT_NEGATIVE_IS_UNSAFE_NO_CLAMP_OR_ULP_TOLERANCE" and all(hs[k]==0 for k in hs if k.endswith("_required")))
    ni=p["primary_scientific_gates"]["progress_noninferiority"]
    need("ni_contract",ni["paired_delta"]=="normalized_progress_bounded_recovery_active - normalized_progress_frozen_reference" and ni["clipping"]=="NONE" and (ni["pairs"],ni["resamples"],ni["seed"],ni["margin"],ni["comparator"],ni["equality"])==(85,10000,20260911,-0.02,"STRICT_GREATER_THAN","FAIL"))
    b=p["boundary_contract"]; need("boundary_contract",b["typed_assurance_boundary_is_valid_complete_trial"] and b["progress_final_state"]=="LAST_ACTUALLY_COMMITTED_STATE" and b["hard_safety_segments"]=="ACTUALLY_COMMITTED_TRAJECTORY_SEGMENTS_ONLY" and not b["uncommitted_boundary_segment_fabricated"] and b["imputation"]==b["exclusion"]=="NONE")
    need("hard_zero_contract",len(p["hard_zero_integrity_gates"])==30 and len(set(p["hard_zero_integrity_gates"]))==30)
    need("analysis_boundary",p["analysis_authority"]["authorization_flag"]=="--post-collection-authorized" and not p["analysis_authority"]["during_collection"] and not p["analysis_authority"]["reference_rerun"])
    need("decision_labels",set(p["decision_contract"].values())=={"BLOCK_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_INTEGRITY","PASS_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_ON_FROZEN_STONEHENGE_BENCHMARK","FAIL_POST_REPAIR_V3_BOUNDED_RECOVERY_HARD_SAFETY_GATE","FAIL_POST_REPAIR_V3_BOUNDED_RECOVERY_PROGRESS_NONINFERIORITY_GATE","FAIL_POST_REPAIR_V3_BOUNDED_RECOVERY_HARD_SAFETY_AND_PROGRESS_NI_GATES"})
    sb=p["scientific_boundary"]; need("scientific_boundary",sb["new_bounded_recovery_formal_result"]=="NOT_RUN" and not any(sb[k] for k in ("pristine_holdout","cross_scene_generalization","physical_world_safety_claim","hard_real_time_guarantee","deployment_claim")))
    need("harness_present",all((TASK/name).is_file() for name in HARNESS))
    monitor=(TASK/HARNESS[2]).read_text(encoding="utf-8"); launcher_source=(TASK/HARNESS[1]).read_text(encoding="utf-8"); analyzer=(TASK/HARNESS[3]).read_text(encoding="utf-8")
    need("monitor_percent",all(x in monitor for x in ("BAR_WIDTH = 30","TRIAL COMPLETION","CYCLE BUDGET","CURRENT TRIAL","DONE-BOUNDARY","--json","--all-trials")))
    need("launcher_contract",TOKEN in launcher_source and "cwd=str(REPO)" in launcher_source and "BATCH_STOP.json" in launcher_source and "BATCH_COMPLETE.json" in launcher_source)
    need("analyzer_contract","--post-collection-authorized" in analyzer and "ANALYSIS_REQUIRES_85_OF_85_IMMUTABLE_LOCKS" in analyzer and all(x in analyzer for x in p["decision_contract"].values()))
    runner=load_module("formal85_r1_runner_validation",TASK/HARNESS[0]); launcher=load_module("formal85_r1_launcher_validation",TASK/HARNESS[1])
    need("validator_lock_basename",LOCK.name==CANONICAL_LOCK_BASENAME); need("runner_lock_binding",runner.LOCK.resolve()==LOCK.resolve()); need("launcher_lock_binding",launcher.LOCK.resolve()==LOCK.resolve())
    need("lock_file_uniqueness",sorted(TASK.glob("*EXECUTION_LOCK*.json"))==[LOCK]); need("wrong_lock_absent",not (TASK/WRONG_LOCK_BASENAME).exists())
    with tempfile.TemporaryDirectory(prefix="formal85_r1_lock_") as directory:
        fixture=Path(directory)/CANONICAL_LOCK_BASENAME; fixture.write_bytes(LOCK.read_bytes()); need("synthetic_hash_path",runner.sha(fixture)==sha(LOCK))
    protected=("cbf","splat","dynamics","run.py","reproduction/runtime","reproduction/formal/post_repair_v3_paired_validation_v1","reproduction/formal/bounded_local_recovery_smoke_v1","reproduction/formal/bounded_local_recovery_smoke_retry2_v1","reproduction/formal/bounded_local_recovery_engineering_pilot_v1","reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1")
    need("protected_diff_zero",not git("diff","--name-only",BASE,"--",*protected)); changed=[x for x in git("diff","--name-only",BASE).splitlines() if x]; need("task_scope_only",all(x.startswith(TASK_PREFIX) for x in changed))
    if require_lock:
        need("lock_exists",LOCK.is_file()); lock=read(LOCK)
        need("lock_schema",lock["schema"]=="POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_EXECUTION_LOCK_V1"); need("lock_canonical_basename",lock["canonical_execution_lock_basename"]==CANONICAL_LOCK_BASENAME)
        need("lock_protocol",lock["protocol_sha256"]==sha(PROTOCOL) and lock["semantic_protocol_sha256"]==semantic_hash(p)); need("lock_harness",lock["harness_sha256"]=={name:sha(TASK/name) for name in HARNESS})
        need("lock_order",lock["trial_order"]==TRIALS and lock["trial_order_sha256"]==semantic_hash(TRIALS)); need("lock_counts",set(lock["freeze_execution_counts"].values())=={0})
        need("authorization_consistency",lock["execution_authorization_token"]==p["execution_authorization_token"]==TOKEN and launcher_source.count(TOKEN)>=2)
        need("lock_retry1_identity",lock["future_result_root"]==str(RESULT_ROOT) and lock["future_tmux_session"]==SESSION)
        need("lock_attempt0_lineage",lock["attempt0"]["root"]==str(ATTEMPT0_ROOT) and lock["attempt0"]["mutation_authority"] is False)
        committed=git("show",f"{lock['protocol_commit']}:{TASK_PREFIX}{PROTOCOL.name}",binary=True); need("protocol_before_lock",hashlib.sha256(committed).hexdigest()==sha(PROTOCOL))
        equivalence=read(TASK/"repair_r1/SCIENTIFIC_SEMANTICS_EQUIVALENCE_AUDIT.json"); need("scientific_equivalence",equivalence["status"]=="PASS_SCIENTIFIC_SEMANTICS_EQUIVALENCE_R1" and equivalence["scientific_diff_count"]==0)
    if require_clean: need("worktree_clean",not git("status","--short"))
    return {"schema":"POST_REPAIR_V3_BOUNDED_RECOVERY_FORMAL85_R1_VALIDATION_V1","status":"PASS_REPAIR_POST_REPAIR_V3_BOUNDED_RECOVERY_FORMAL85_LOCK_PATH_R1_VALIDATION","check_count":len(checks),"checks":checks,"gpu_run_count":0,"tmux_created_count":0,"real_trial_run_count":0,"real_plantcommit_count":0}

def main()->int:
    a=argparse.ArgumentParser(description=__doc__); a.add_argument("--mode",choices=("freeze","prelaunch"),default="freeze"); a.add_argument("--require-clean",action="store_true"); args=a.parse_args()
    print(json.dumps(validate_freeze(require_lock=args.mode=="prelaunch",require_absent_root=True,require_clean=args.require_clean),sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
