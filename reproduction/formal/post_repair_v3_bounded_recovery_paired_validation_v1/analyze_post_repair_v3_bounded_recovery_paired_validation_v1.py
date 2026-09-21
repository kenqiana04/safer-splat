#!/usr/bin/env python3
"""Post-collection-only formal analyzer; never called by the collection launcher."""
from __future__ import annotations
import argparse, csv, hashlib, importlib.util, json, math, os, random, statistics, sys
from pathlib import Path
from validate_post_repair_v3_bounded_recovery_paired_validation_v1 import PROTOCOL, REPO, TRIALS, ValidationPhase, read, validate_phase

BLOCK="BLOCK_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_INTEGRITY"
PASS="PASS_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_ON_FROZEN_STONEHENGE_BENCHMARK"
HARD_FAIL="FAIL_POST_REPAIR_V3_BOUNDED_RECOVERY_HARD_SAFETY_GATE"
NI_FAIL="FAIL_POST_REPAIR_V3_BOUNDED_RECOVERY_PROGRESS_NONINFERIORITY_GATE"
BOTH_FAIL="FAIL_POST_REPAIR_V3_BOUNDED_RECOVERY_HARD_SAFETY_AND_PROGRESS_NI_GATES"

def lines(path:Path):
    if not path.is_file(): raise RuntimeError("REQUIRED_IMMUTABLE_EVIDENCE_MISSING:"+str(path))
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x]
def write(path:Path,value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")
def sha(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()
def semantic(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
def frozen_reference(p):
    path=REPO/"reproduction/formal/post_repair_v3_paired_validation_v1/REFERENCE_FROZEN_OUTCOMES.json"
    d=read(path)
    if d.get("schema")!="POST_REPAIR_V3_FROZEN_REFERENCE_OUTCOMES_V1": raise RuntimeError("FROZEN_REFERENCE_SCHEMA_MISMATCH")
    if d.get("trial_order")!=list(TRIALS) or len(d.get("values",[]))!=85: raise RuntimeError("FROZEN_REFERENCE_ORDER_OR_COUNT_MISMATCH")
    if len({int(x.get("trial_id")) for x in d["values"]})!=85: raise RuntimeError("FROZEN_REFERENCE_DUPLICATE_TRIAL_ID")
    for expected,row in zip(TRIALS,d["values"]):
        if int(row.get("trial_id"))!=expected or row.get("hard_violation") is not False or row.get("unknown_segment_count")!=0:
            raise RuntimeError("FROZEN_REFERENCE_STATUS_OR_ORDER_MISMATCH")
        if not math.isfinite(float(row.get("normalized_progress"))): raise RuntimeError("FROZEN_REFERENCE_NONFINITE_PROGRESS")
    if d.get("reference_hard_violation_trials")!=0 or d.get("reference_unknown_trials")!=0 or d.get("reference_rerun_count_this_task")!=0:
        raise RuntimeError("FROZEN_REFERENCE_STATUS_COUNT_MISMATCH")
    source=Path(d["source_per_pair_path"]); summary=source.parent/"V3_PAIRED_ANALYSIS_SUMMARY.json"
    if not source.is_file() or sha(source)!=d.get("source_per_pair_sha256"): raise RuntimeError("FROZEN_REFERENCE_SOURCE_HASH_MISMATCH")
    if not summary.is_file() or sha(summary)!=d.get("source_summary_sha256"): raise RuntimeError("FROZEN_REFERENCE_SUMMARY_HASH_MISMATCH")
    if d.get("values_semantic_sha256")!=semantic(d["values"]): raise RuntimeError("FROZEN_REFERENCE_SEMANTIC_HASH_MISMATCH")
    return {int(row["trial_id"]):row for row in d["values"]}, d, path
def percentile(values,f):
    x=sorted(values); pos=f*(len(x)-1); lo,hi=math.floor(pos),math.ceil(pos)
    return x[lo] if lo==hi else x[lo]+(x[hi]-x[lo])*(pos-lo)
def bootstrap(deltas):
    if len(deltas)!=85 or any(not math.isfinite(x) for x in deltas): raise RuntimeError("PAIRED_85_FINITE_DELTAS_REQUIRED")
    rng=random.Random(20260911); means=[statistics.mean(deltas[rng.randrange(85)] for _ in range(85)) for _ in range(10000)]
    return {"resamples":10000,"seed":20260911,"lower95":percentile(means,.025),"upper95":percentile(means,.975)}
def normalized_progress(states,goal):
    d0=math.dist(states[0][:3],goal[:3]); d1=math.dist(states[-1][:3],goal[:3])
    if d0<=0 or not math.isfinite(d0) or not math.isfinite(d1): raise RuntimeError("NONFINITE_PROGRESS_INPUT")
    return (d0-d1)/d0
def active_states(observations):
    if not observations: raise RuntimeError("EMPTY_PUBLIC_CYCLE_EVIDENCE")
    states=[tuple(observations[0]["pre_state"])]
    for row in observations:
        if row["committed"]:
            if row.get("post_state") is None: raise RuntimeError("COMMITTED_POST_STATE_MISSING")
            states.append(tuple(row["post_state"]))
    return states
def hard_proxy(states_by_trial,p):
    import numpy as np, torch
    sys.path[:0]=[str(REPO/"reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1"),str(REPO)]
    from splat.gsplat_utils import GSplatLoader
    from adapters.gaussian_barrier_adapter import SourceGaussianBarrierAdapter
    spec=importlib.util.spec_from_file_location("_formal85_hard_proxy",REPO/"reproduction/pilot/active_runtime_pilot_v2/run_active_runtime_pilot_v2.py")
    module=importlib.util.module_from_spec(spec); sys.modules[spec.name]=module; spec.loader.exec_module(module)
    if not torch.cuda.is_available() or torch.cuda.device_count()!=1: raise RuntimeError("SINGLE_VISIBLE_GPU_REQUIRED")
    loader=GSplatLoader(Path(p["map"]["root"])/"config.yml",torch.device("cuda:0")); radius=.015
    def query(point,**kwargs):
        if not torch.is_tensor(point): point=torch.as_tensor(point,device=torch.device("cuda:0"),dtype=torch.float32)
        return loader.query_distance(point,**kwargs)
    provider=SourceGaussianBarrierAdapter(query,p["map"]["identity"],radius,int(loader.means.shape[0])); rows=[]
    for trial,states in states_by_trial.items():
        unsafe=unknown=0; values=[]
        for before,after in zip(states[:-1],states[1:]):
            status,value=module.certify_segment_clearance(provider,np.asarray(before[:3]),np.asarray(after[:3]),radius)
            unsafe+=status=="UNSAFE"; unknown+=status not in ("SAFE","UNSAFE")
            if value is not None and math.isfinite(float(value)): values.append(float(value))
        rows.append({"trial_id":trial,"hard_violation_segments":unsafe,"hard_unknown_segments":unknown,"minimum_hard_clearance_q":min(values) if values else None})
    return rows
def decide(integrity,unknown,active_hard,active_only,lower):
    if not integrity or unknown or lower is None or not math.isfinite(lower): return BLOCK
    hard=active_hard==0 and active_only==0; ni=lower>-0.02
    return PASS if hard and ni else HARD_FAIL if not hard and ni else NI_FAIL if hard else BOTH_FAIL

def analyze(write_outputs=True):
    os.chdir(REPO); p=read(PROTOCOL); root=Path(p["future_result_root"]); validate_phase(ValidationPhase.POSTCOLLECTION)
    complete=read(root/"BATCH_COMPLETE.json")
    if complete.get("trial_order")!=TRIALS or (root/"BATCH_STOP.json").exists(): raise RuntimeError("ANALYSIS_REQUIRES_COMPLETE_NO_STOP_BATCH")
    if any(not (root/f"trial_{t}_complete.json").is_file() or not (root/"raw"/f"trial_{t}"/"runtime_trace_lock.json").is_file() for t in TRIALS): raise RuntimeError("ANALYSIS_REQUIRES_85_OF_85_IMMUTABLE_LOCKS")
    reference, reference_manifest, reference_path=frozen_reference(p)
    old_path=Path(p["historical_active_authority"]["root"])/"POST_REPAIR_V3_PAIRED_TRIAL_RESULTS.csv"
    with old_path.open(encoding="utf-8",newline="") as f: old={int(r["trial_id"]):r for r in csv.DictReader(f)}
    if set(old)!=set(TRIALS): raise RuntimeError("HISTORICAL_ACTIVE_TRIAL_SET_MISMATCH")
    states_by_trial={}; rows=[]; boundary_rows=[]; audit={g:{"value":0,"evidence":[]} for g in p["hard_zero_integrity_gates"]}; recovery={k:0 for k in ("eligibility_events","scans","candidate_attempts","l2_enter","l2_result","l2_pass","l2_fail","l2_unknown","l2_exception","l3_result","l3_pass","l3_fail","l3_unknown","l3_exception","selected","plantcommit","rank_resume","exhaustion")}
    def add(g,v,t,src):
        audit[g]["value"]+=int(v); audit[g]["evidence"].append({"trial_id":t,"source":src,"contribution":int(v)})
    for trial in TRIALS:
        raw=root/"raw"/f"trial_{trial}"; summary=read(raw/"trial_summary.json"); obs=lines(raw/"recovery_cycle_observations.jsonl"); trace=lines(raw/"runtime_trace.jsonl"); lock=read(raw/"runtime_trace_lock.json"); complete_trial=read(root/f"trial_{trial}_complete.json")
        exit_code=int((raw/"process_exit_code.txt").read_text().strip()); attempts=[a for x in obs for a in x.get("recovery_attempts",[])]; states=active_states(obs); states_by_trial[trial]=states; goal=tuple(obs[0]["goal_state"]); progress=normalized_progress(states,goal); commits=sum(bool(x.get("committed")) for x in obs); boundaries=sum(bool(x.get("boundary")) for x in obs)
        add("process_nonzero_exit_count",exit_code!=0 or complete_trial.get("process_exit_code")!=0,trial,"process_exit_code.txt + trial_complete.json")
        add("malformed_or_finalization_error_count",summary.get("finalization_status")!="FINALIZED" or summary.get("startup_status")!="PASS" or not summary.get("trace_lock_identity"),trial,"trial_summary.json finalization/startup fields")
        card_bad=not (len(trace)==len(obs)==summary.get("completed_cycles")==summary.get("trace_record_count")==summary.get("persisted_trace_line_count")==summary.get("trace_lock_record_count")==lock.get("record_count")); add("trace_write_failure_count",card_bad,trial,"trace/observation/summary/lock cardinality")
        add("trace_commit_atomicity_violation_count",not (lock.get("locked_before_evaluation") is True and lock.get("identity") and lock.get("trace_sha256") and lock.get("record_count")==len(trace)),trial,"runtime_trace_lock.json")
        add("cert_exec_identity_mismatch_count",summary.get("selected_executed_identity_mismatch_count",0),trial,"trial_summary.json")
        facts_by_cycle={x["cycle_index"]:dict(x.get("facts",[])) for x in trace}
        add("canonical_transition_mismatch_count",sum(not (summary.get("v3_wiring_audit",{}).get("checks",{}).get("canonical_transition_is_plant_arithmetic") and facts_by_cycle.get(x.get("cycle_index"),{}).get("canonical_transition_arithmetic_identity")) for x in obs),trial,"v3_wiring_audit + runtime_trace facts")
        state_mismatch=state_unknown=0
        for prev,nxt in zip(obs,obs[1:]):
            if prev.get("committed"):
                if not prev.get("post_state_identity") or not nxt.get("pre_state_identity"): state_unknown+=1
                elif prev.get("post_state_identity")!=nxt.get("pre_state_identity"): state_mismatch+=1
        add("state_continuity_mismatch_count",state_mismatch,trial,"adjacent committed post/pre state identities"); add("state_continuity_unknown_count",state_unknown,trial,"adjacent committed post/pre state identities")
        route_bad=0
        for x in obs:
            ids=[str(r) for r in x.get("routing_rule_ids",[])]; failures=json.dumps(x.get("stage_failures",[]),sort_keys=True)
            route_bad+=sum(any(k in r for k in ("AMBIGUOUS","MISSING")) for r in ids)+int("ROUTING_RULE_AMBIGUOUS" in failures or "ROUTING_RULE_MISSING" in failures)
        add("routing_ambiguous_count",sum("AMBIGUOUS" in json.dumps(x.get("stage_failures",[])) for x in obs),trial,"routing_rule_ids/stage_failures")
        allowed=p["recovery"]["source"]; add("unauthorized_source_execution_count",sum(a.get("candidate_source")!=allowed for a in attempts),trial,"recovery_attempts.candidate_source")
        add("unverified_action_execution_count",sum(bool(x.get("committed")) and (not x.get("selected_action_identity") or x.get("selected_action_identity")!=x.get("executed_action_identity") or facts_by_cycle.get(x.get("cycle_index"),{}).get("canonical_selected_candidate_identity") is None) for x in obs),trial,"observation and trace identities")
        add("stale_backup_execution_count",sum(bool(x.get("committed")) and "BACKUP" in str(x.get("action_role")) and any(k in str(x.get("backup_status")) for k in ("STALE","INVALID","NONE")) for x in obs),trial,"backup_status/action_role")
        seen={}; dup=loops=0
        for a in attempts:
            key=a.get("exhaustion_key"); sig=(a.get("candidate_rank"),a.get("canonical_action_identity")); prev=seen.setdefault(key,set())
            if sig in prev: dup+=1
            prev.add(sig)
        loops=sum(len(v)>6 for v in seen.values()); add("same_key_duplicate_retry_count",dup,trial,"recovery attempt exhaustion_key/rank/action"); add("internal_recovery_loop_count",loops,trial,"recovery attempt bounded rank cardinality")
        add("historical_diagnostic_runtime_authority_count",summary.get("v3_wiring_audit",{}).get("historical_diagnostic_runtime_authority",False) is not False,trial,"v3_wiring_audit")
        stderr=(raw/"stderr.log").read_text(errors="replace") if (raw/"stderr.log").is_file() else ""; add("canonical_l2_evidence_rewrite_exception_count",stderr.count("CANONICAL_EVIDENCE_REWRITE_FORBIDDEN:canonical_l2_"),trial,"stderr.log")
        scoped_missing=scoped_conflict=primary_corrupt=0
        for x in obs:
            facts=facts_by_cycle.get(x.get("cycle_index"),{}); scoped_raw=facts.get("canonical_l2_candidate_evidence",[]); names=[z[0] for z in scoped_raw]; scopes={z[0]:dict(z[1]) for z in scoped_raw}
            scoped_conflict += int(len(names)!=len(set(names)) or names!=sorted(names) or any(list(dict(z[1]))!=sorted(dict(z[1])) for z in scoped_raw))
            if "PRIMARY_L2" in x.get("phase_history",[]):
                req=("canonical_l2_x_k1_identity","canonical_l2_p_k1_identity","canonical_l2_x_k2_identity","canonical_l2_p_k2_identity","canonical_l2_segment_identity","canonical_l2_status","canonical_l2_reason","canonical_l2_evidence_identity","canonical_selected_candidate_identity")
                primary=[v for v in scopes.values() if v.get("candidate_role")=="PRIMARY"]; primary_corrupt += int(not all(k in facts for k in req) or len(primary)!=1 or (primary and facts.get("canonical_selected_candidate_identity")!=primary[0].get("candidate_identity")))
            for a in x.get("recovery_attempts",[]):
                if a.get("L2_status") in ("PASS","FAIL","UNKNOWN"):
                    payload=scopes.get(a.get("candidate_id")); scoped_missing += int(payload is None or payload.get("candidate_identity")!=a.get("candidate_id") or payload.get("candidate_source_type")!=a.get("candidate_source") or payload.get("candidate_role")!="ALTERNATIVE" or payload.get("status")!=a.get("L2_status"))
        add("candidate_scoped_l2_evidence_missing_count",scoped_missing,trial,"runtime_trace canonical_l2_candidate_evidence vs recovery_attempts"); add("candidate_scoped_l2_scope_conflict_count",scoped_conflict,trial,"runtime_trace canonical_l2_candidate_evidence ordering/duplicates"); add("legacy_primary_l2_flat_evidence_corruption_count",primary_corrupt,trial,"runtime_trace legacy canonical_l2_* + PRIMARY scope")
        for gate,field in (("duplicate_plant_commit_count","duplicate_plant_commit_count"),("duplicate_trace_append_count","duplicate_trace_append_count"),("illegal_token_mutation_count","illegal_token_mutation_count"),("evidence_incomplete_count","evidence_incomplete_count"),("plant_outcome_unknown_count","plant_outcome_unknown_count"),("nonfinite_count","nonfinite_count"),("action_bound_violation_count","action_bound_violation_count"),("exception_count","exception_count"),("cuda_oom_count","cuda_oom_count"),("unintended_plant_commit_count","unintended_plant_commit_count"),("selected_executed_identity_mismatch_count","selected_executed_identity_mismatch_count")):
            add(gate,summary.get(field,0),trial,"trial_summary.json:"+field)
        recovery["eligibility_events"]+=sum(bool(x.get("recovery_attempts")) for x in obs); recovery["candidate_attempts"]+=len(attempts); recovery["selected"]+=sum(a.get("supervisor_selected") is True for a in attempts); recovery["plantcommit"]+=sum(bool(x.get("committed")) and any(a.get("supervisor_selected") is True for a in x.get("recovery_attempts",[])) for x in obs)
        for a in attempts:
            l2=a.get("L2_status"); l3=a.get("L3_status"); recovery["l2_enter"]+=a.get("C0_status")=="PASS"; recovery["l2_result"]+=l2 in ("PASS","FAIL","UNKNOWN"); recovery["l2_pass"]+=l2=="PASS"; recovery["l2_fail"]+=l2=="FAIL"; recovery["l2_unknown"]+=l2=="UNKNOWN"; recovery["l2_exception"]+=a.get("exception_stage")=="L2"; recovery["l3_result"]+=l3 in ("PASS","FAIL","UNKNOWN"); recovery["l3_pass"]+=l3=="PASS"; recovery["l3_fail"]+=l3=="FAIL"; recovery["l3_unknown"]+=l3=="UNKNOWN"; recovery["l3_exception"]+=a.get("exception_stage")=="L3"
        generation=lines(raw/"recovery_generation.jsonl") if (raw/"recovery_generation.jsonl").is_file() else []; recovery["scans"]+=len(generation); recovery["exhaustion"]+=sum(not g.get("candidates") for g in generation); recovery["rank_resume"]+=sum(a.get("candidate_rank",0)>0 for a in attempts)
        roles={"primary":0,"backup":0,"recovery":0,"terminal":0}
        for x in obs:
            selected=any(a.get("supervisor_selected") is True for a in x.get("recovery_attempts",[])); role=str(x.get("action_role") or "")
            if x.get("committed") and selected: roles["recovery"]+=1
            elif x.get("committed") and "PRIMARY" in role: roles["primary"]+=1
            elif x.get("committed") and "BACKUP" in role: roles["backup"]+=1
            elif x.get("committed") and "TERMINAL" in role: roles["terminal"]+=1
        termination=summary.get("termination_reason"); valid_boundary=(termination=="ASSURANCE_BOUNDARY" and summary.get("hard_blocker") is None and summary.get("finalization_status")=="FINALIZED" and boundaries==1 and len(obs)==commits+1 and not obs[-1].get("committed"))
        if boundaries: boundary_rows.append({"trial_id":trial,"cycle_index":obs[-1]["cycle_index"],"final_supervisor_reason":obs[-1].get("supervisor_reason"),"completed_cycles":len(obs),"plant_commit_count":commits,"last_committed_progress":progress,"reference_progress":reference[trial]["normalized_progress"],"paired_delta":progress-reference[trial]["normalized_progress"],"deadline_state_at_boundary":(obs[-1].get("deadline_observations") or [{}])[-1].get("status"),"recovery_activity_before_boundary":sum(bool(x.get("recovery_attempts")) for x in obs),"typed_boundary_contract_valid":valid_boundary})
        rows.append({"trial_id":trial,"bounded_recovery_progress":progress,"reference_progress":reference[trial]["normalized_progress"],"paired_progress_delta":progress-reference[trial]["normalized_progress"],"old_repaired_active_progress":float(old[trial]["active_progress"]),"bounded_recovery_minus_old_active":progress-float(old[trial]["active_progress"]),"completed_cycles":len(obs),"plant_commits":commits,"assurance_boundary_count":boundaries,**{f"{k}_commits":v for k,v in roles.items()}})
    hard=hard_proxy(states_by_trial,p); hard_by={x["trial_id"]:x for x in hard}
    for row in rows:
        row.update(hard_by[row["trial_id"]]); ref=reference[row["trial_id"]]; row["reference_hard_violation"]=bool(ref["hard_violation"]); row["active_only_hard_discordant"]=row["hard_violation_segments"]>0 and not row["reference_hard_violation"]
    unknown=sum(x["hard_unknown_segments"] for x in hard); active_hard=sum(x["hard_violation_segments"]>0 for x in hard); active_only=sum(x["active_only_hard_discordant"] for x in rows); audit["represented_map_hard_violation_count"]["value"]=sum(x["hard_violation_segments"] for x in hard)
    hard_zero={k:v["value"] if isinstance(v,dict) else v for k,v in audit.items()}; integrity=not any(hard_zero.values()) and recovery["l2_exception"]==recovery["l3_exception"]==0 and all(x.get("typed_boundary_contract_valid",True) for x in boundary_rows)
    deltas=[x["paired_progress_delta"] for x in rows]; ci=bootstrap(deltas) if integrity and unknown==0 else None; decision=decide(integrity,unknown,active_hard,active_only,None if ci is None else ci["lower95"])
    progress={"n":85,"mean_delta":statistics.mean(deltas),"median_delta":statistics.median(deltas),"min_delta":min(deltas),"max_delta":max(deltas),"positive_count":sum(x>0 for x in deltas),"zero_count":sum(x==0 for x in deltas),"negative_count":sum(x<0 for x in deltas),"bootstrap_percentile_95":ci,"margin":-0.02,"strict_comparator":"lower95 > -0.02","equality_at_margin":"FAIL","clipping":"NONE","strict_ni_pass":ci is not None and ci["lower95"]>-0.02}
    routing={"descriptive_only":True,"role":"DESCRIPTIVE_ONLY_NO_ROUTING_CONDITIONED_GATE_OR_TUNING","totals":{k:sum(x[f"{k}_commits"] for x in rows) for k in ("primary","backup","recovery","terminal")},"boundary_trials":len(boundary_rows),"per_trial":rows}
    hard_result={"active_hard_violation_trials":active_hard,"hard_violation_segments":sum(x["hard_violation_segments"] for x in hard),"hard_unknown_segments":unknown,"active_only_hard_discordant_pairs":active_only,"reference_hard_violation_trials":sum(bool(x["hard_violation"]) for x in reference.values()),"global_min_hard_clearance_q":min(x["minimum_hard_clearance_q"] for x in hard if x["minimum_hard_clearance_q"] is not None),"negative_tolerance":None,"epsilon":None,"hard_gate_pass":active_hard==active_only==unknown==0}
    result={"schema":"POST_REPAIR_V3_BOUNDED_RECOVERY_COLLECTION_SUMMARY_V1","status":decision,"trials_completed":85,"hard_zero_counts":hard_zero,"recovery":recovery,"historical_repaired_active_verdict":"FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE","historical_result_rewritten":False,"scientific_boundary":p["scientific_boundary"],"reference_authority_schema":reference_manifest["schema"],"reference_authority_path":str(reference_path)}
    if write_outputs:
        fields=list(rows[0]);
        with (root/"POST_REPAIR_V3_BOUNDED_RECOVERY_TRIAL_RESULTS.csv").open("w",encoding="utf-8",newline="") as f: w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
        write(root/"POST_REPAIR_V3_BOUNDED_RECOVERY_COLLECTION_SUMMARY.json",result); write(root/"POST_REPAIR_V3_BOUNDED_RECOVERY_PROGRESS_ANALYSIS.json",progress); write(root/"POST_REPAIR_V3_BOUNDED_RECOVERY_HARD_SAFETY_ANALYSIS.json",hard_result); write(root/"POST_REPAIR_V3_BOUNDED_RECOVERY_CONTINUITY_ANALYSIS.json",{"hard_zero_counts":hard_zero,"coverage":30,"unsupported":0,"evidence":audit}); write(root/"POST_REPAIR_V3_BOUNDED_RECOVERY_ROUTING_ANALYSIS.json",routing); write(root/"POST_REPAIR_V3_BOUNDED_RECOVERY_RECOVERY_ANALYSIS.json",recovery); write(root/"POST_REPAIR_V3_BOUNDED_RECOVERY_BOUNDARY_ANALYSIS.json",{"total_boundary_trials":len(boundary_rows),"trial_ids":[x["trial_id"] for x in boundary_rows],"rows":boundary_rows}); write(root/"POST_REPAIR_V3_BOUNDED_RECOVERY_HISTORICAL_ACTIVE_DIAGNOSTIC.json",{"role":"SECONDARY_DIAGNOSTIC_ONLY_NOT_PRIMARY_FORMAL_GATE","rows":[{"trial_id":x["trial_id"],"bounded_recovery_minus_old_active":x["bounded_recovery_minus_old_active"]} for x in rows]})
        (root/"POST_REPAIR_V3_BOUNDED_RECOVERY_FAILURE_REGISTER.csv").write_text("trial_id,failure_class,detail\n",encoding="utf-8")
        report=root/"report/REPORT_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_V1.md"; report.parent.mkdir(parents=True,exist_ok=True); report.write_text(f"# Post-Repair V3 Bounded Recovery Paired Validation V1\n\nNew prospective result: `{decision}`.\n\nHistorical repaired-Active result: `FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE` (unchanged).\n\nRepeatedly exposed Stonehenge benchmark; not a pristine holdout or cross-scene, physical-world safety, hard-real-time, or deployment claim.\n",encoding="utf-8")
    return result

def main()->int:
    a=argparse.ArgumentParser(description=__doc__); a.add_argument("--post-collection-authorized",action="store_true"); args=a.parse_args()
    if not args.post_collection_authorized: raise RuntimeError("POST_COLLECTION_AUTHORIZATION_REQUIRED")
    result=analyze(True); print(result["status"]); return 0 if result["status"]!=BLOCK else 2
if __name__=="__main__": raise SystemExit(main())
