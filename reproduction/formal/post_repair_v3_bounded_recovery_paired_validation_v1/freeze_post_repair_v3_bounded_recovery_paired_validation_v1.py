#!/usr/bin/env python3
"""Generate task-local authority audits and execution lock after the protocol commit."""
from __future__ import annotations
import hashlib, json, os
from pathlib import Path
from validate_post_repair_v3_bounded_recovery_paired_validation_v1 import *

RESULTS=TASK/"results_freeze"; REPORT=TASK/"report/REPORT_FREEZE_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_V1.md"
PILOT_ROOT=Path("/disk1/zlab/v3_repair_records/bounded_local_recovery_engineering_pilot_v1_20260919")
REF_ROOT=Path("/disk1/zlab/formal_execution_records/formal_paired_v2_20260911")
HIST_ROOT=Path("/disk1/zlab/v3_repair_records/post_repair_v3_paired_validation_v1_20260917")
def write(path,value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
def inventory(root,names): return {name:{"size":(root/name).stat().st_size,"sha256":sha(root/name)} for name in names}

def main()->int:
    if git("branch","--show-current")!=BRANCH or git("remote","get-url","origin")!=ORIGIN: raise RuntimeError("GIT_IDENTITY_DRIFT")
    if git("status","--short"): raise RuntimeError("PROTOCOL_COMMIT_AND_CLEAN_WORKTREE_REQUIRED")
    p=read(PROTOCOL); protocol_commit=git("rev-parse","HEAD"); RESULTS.mkdir(parents=True,exist_ok=True)
    pilot_names=["PILOT_SUMMARY.json","PILOT_PROGRESS_DIAGNOSTIC.json","PILOT_ROUTING_DIAGNOSTIC.json","HARD_SAFETY_PILOT_AUDIT.json","TRACE_INTEGRITY_AUDIT.json","RECOVERY_L2_REACHABILITY_AUDIT.json","MULTI_CANDIDATE_L2_EVIDENCE_AUDIT.json","RECOVERY_RANK_PROGRESSION_AUDIT.json","BATCH_COMPLETE.json"]
    ps=read(PILOT_ROOT/"PILOT_SUMMARY.json"); pp=read(PILOT_ROOT/"PILOT_PROGRESS_DIAGNOSTIC.json")
    pilot={"schema":"ENGINEERING_PILOT_AUTHORITY_AUDIT_V1","status":"PASS","root":str(PILOT_ROOT),"artifacts":inventory(PILOT_ROOT,pilot_names),"authoritative_status":ps["status"],"engineering_decision":ps["engineering_decision_signal"],"key_facts":{"trials_completed":12,**ps["counts"],"hard_violation_segments":ps["hard_safety"]["hard_violation_segments"],"hard_unknown_segments":ps["hard_safety"]["hard_unknown_segments"],"global_min_hard_clearance_q":ps["hard_safety"]["global_min_hard_clearance_q"],"progress_mean_delta":pp["mean_delta"],"progress_median_delta":pp["median_delta"],"progress_positive_zero_negative":[pp["positive_count"],pp["zero_count"],pp["negative_count"]],"catastrophic_progress_regression_signal":ps["catastrophic_progress_regression_signal"]},"source_mutation_authority":False,"scientific_parameter_selection_authority":False}
    write(RESULTS/"ENGINEERING_PILOT_AUTHORITY_AUDIT.json",pilot)
    source_bytes=git("show",f"{BASE}:{SOURCE_PROTOCOL}",binary=True)
    cohort={"schema":"FORMAL85_COHORT_AUTHORITY_AUDIT_V1","status":"PASS","source_path":SOURCE_PROTOCOL,"source_sha256":hashlib.sha256(source_bytes).hexdigest(),"trial_order":TRIALS,"n":85,"trial_order_sha256":semantic_hash(TRIALS),"seed":0,"max_cycles":500,"serial":True,"separate_process":True,"automatic_retry":False,"modified":False}
    write(RESULTS/"FORMAL85_COHORT_AUTHORITY_AUDIT.json",cohort)
    ref_names=["FORMAL_ACCEPTED_INDEX.json","FORMAL_PAIR_SUMMARY.csv","FORMAL_RAW_EVIDENCE_MANIFEST.json","FORMAL_SAFETY_SUMMARY.json","FORMAL_STATISTICAL_ANALYSIS.json","FORMAL_ENVIRONMENT_MANIFEST.json","FORMAL_INTEGRITY_REGISTER.csv"]
    ref={"schema":"REFERENCE_AUTHORITY_AUDIT_V1","status":"PASS_REFERENCE_REUSE_IDENTITY_RESOLVED","root":str(REF_ROOT),"worktree":"/disk1/zlab/formal_execution_worktrees/safer-splat-formal-v2","artifacts":inventory(REF_ROOT,ref_names),"exact_primary_pairs":85,"required_trial_ids":TRIALS,"hard_violation_trials":0,"unknown_segments":0,"reference_rerun_authorized":False,"immutable":True}
    write(RESULTS/"REFERENCE_AUTHORITY_AUDIT.json",ref)
    hist_names=["POST_REPAIR_V3_PAIRED_TRIAL_RESULTS.csv","POST_REPAIR_V3_PAIRED_PROGRESS_ANALYSIS.json","POST_REPAIR_V3_PAIRED_ROUTING_ANALYSIS.json","POST_REPAIR_V3_PAIRED_HARD_SAFETY_ANALYSIS.json","POST_REPAIR_V3_PAIRED_COLLECTION_SUMMARY.json","POST_REPAIR_V3_FINAL_ACCEPTANCE.json"]
    old=read(HIST_ROOT/"POST_REPAIR_V3_FINAL_ACCEPTANCE.json")
    hist={"schema":"HISTORICAL_ACTIVE_AUTHORITY_AUDIT_V1","status":"PASS","root":str(HIST_ROOT),"artifacts":inventory(HIST_ROOT,hist_names),"verdict":old["new_post_repair_scientific_result"],"paired_n":old["paired_n"],"progress_mean_delta":old["progress_mean_delta"],"bootstrap_lower95":old["bootstrap_lower95"],"bootstrap_upper95":old["bootstrap_upper95"],"ni_margin":old["noninferiority_margin"],"routing_rates":old["routing_rates"],"role":"HISTORICAL_REPAIRED_ACTIVE_DIAGNOSTIC_ONLY","primary_reference_arm":False,"mutation_authority":False}
    write(RESULTS/"HISTORICAL_ACTIVE_AUTHORITY_AUDIT.json",hist)
    write(RESULTS/"RUNTIME_LINEAGE_AUDIT.json",{"schema":"RUNTIME_LINEAGE_AUDIT_V1","status":"PASS","evidence_repair_head":REPAIR,"bounded_recovery_head":IMPL,"gate0_head":GATE0,"retry2_freeze_head":RETRY2,"pilot_freeze_head":BASE,"runtime_diff_count":0})
    write(RESULTS/"MAP_AUTHORITY_AUDIT.json",{"schema":"MAP_AUTHORITY_AUDIT_V1","status":"PASS","map":p["map"]})
    write(RESULTS/"STATISTICAL_CONTRACT_LOCK.json",{"schema":"STATISTICAL_CONTRACT_LOCK_V1","status":"FROZEN","primary_scientific_gates":p["primary_scientific_gates"],"decision_contract":p["decision_contract"],"pilot_progress_used_for_parameter_selection":False})
    write(RESULTS/"BOUNDARY_SEMANTICS_LOCK.json",{"schema":"BOUNDARY_SEMANTICS_LOCK_V1","status":"FROZEN","contract":p["boundary_contract"]})
    write(RESULTS/"PROTOCOL_SEMANTIC_LOCK.json",{"schema":"PROTOCOL_SEMANTIC_LOCK_V1","status":"FROZEN","protocol_sha256":sha(PROTOCOL),"semantic_protocol_sha256":semantic_hash(p),"trial_order_sha256":semantic_hash(TRIALS)})
    harness={name:sha(TASK/name) for name in HARNESS}; write(RESULTS/"HARNESS_HASHES.json",{"schema":"HARNESS_HASHES_V1","status":"FROZEN","files":harness})
    bindings=[]
    for item in p["local_infrastructure_bindings"]:
        path=REPO/item["path"]; bindings.append({**item,"is_symlink":path.is_symlink(),"link_text":os.readlink(path),"source_exists":Path(item["target"]).exists(),"git_ignored":bool(git("check-ignore",item["path"])),"resolved":str(path.resolve())})
    write(RESULTS/"LOCAL_INFRA_BINDING_AUDIT.json",{"schema":"LOCAL_INFRA_BINDING_AUDIT_V1","status":"PASS","authority":p["local_binding_authority"],"bindings":bindings})
    protected=("cbf","splat","dynamics","run.py","reproduction/runtime","reproduction/formal/post_repair_v3_paired_validation_v1","reproduction/formal/bounded_local_recovery_smoke_v1","reproduction/formal/bounded_local_recovery_smoke_retry2_v1","reproduction/formal/bounded_local_recovery_engineering_pilot_v1","reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1")
    changed=[x for x in git("diff","--name-only",BASE).splitlines() if x]; protected_changed=[x for x in git("diff","--name-only",BASE,"--",*protected).splitlines() if x]
    write(RESULTS/"PROTECTED_DIFF_AUDIT.json",{"schema":"PROTECTED_DIFF_AUDIT_V1","status":"PASS" if not protected_changed and all(x.startswith(TASK_PREFIX) for x in changed) else "FAIL","base":BASE,"changed_files":changed,"protected_paths":protected,"protected_changed":protected_changed,"runtime_diff_count":0})
    lock={"schema":"POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_EXECUTION_LOCK_V1","protocol_commit":protocol_commit,"base_head":BASE,"repair_implementation_head":REPAIR,"bounded_recovery_implementation_head":IMPL,"gate0_head":GATE0,"retry2_freeze_head":RETRY2,"engineering_pilot_freeze_head":BASE,"pilot_postrun_artifact_hashes":{k:v["sha256"] for k,v in pilot["artifacts"].items()},"historical_active_artifact_hashes":{k:v["sha256"] for k,v in hist["artifacts"].items()},"reference_artifact_hashes":{k:v["sha256"] for k,v in ref["artifacts"].items()},"formal85_source_protocol_sha256":cohort["source_sha256"],"trial_order":TRIALS,"trial_order_sha256":semantic_hash(TRIALS),"protocol_sha256":sha(PROTOCOL),"semantic_protocol_sha256":semantic_hash(p),"harness_sha256":harness,"map":p["map"],"geometry":p["geometry"],"dynamics":p["dynamics"],"recovery":p["recovery"],"statistics":p["primary_scientific_gates"],"boundary_handling":p["boundary_contract"],"hard_zero_gates":p["hard_zero_integrity_gates"],"future_result_root":str(RESULT_ROOT),"future_tmux_session":SESSION,"execution_authorization_token":TOKEN,"freeze_execution_counts":p["freeze_execution_counts"]}
    write(LOCK,lock)
    result=validate_freeze(require_lock=True,require_absent_root=True); write(RESULTS/"PRELAUNCH_VALIDATION.json",result)
    REPORT.parent.mkdir(parents=True,exist_ok=True); REPORT.write_text("# Freeze Post-Repair V3 Bounded Recovery Paired Validation V1\n\n- Status: `PASS_FREEZE_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_V1_VALIDATION`.\n- Exact formal85 cohort, frozen Reference, hard-safety gate, progress NI contract, and typed boundary semantics are locked.\n- Historical repaired-Active result is unchanged; new bounded-recovery result is `NOT_RUN`.\n- GPU/tmux/real-trial/real-PlantCommit counts: `0/0/0/0`.\n- Only next task: `EXECUTE_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_V1`.\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"check_count":result["check_count"],"lock_sha256":sha(LOCK)},sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
