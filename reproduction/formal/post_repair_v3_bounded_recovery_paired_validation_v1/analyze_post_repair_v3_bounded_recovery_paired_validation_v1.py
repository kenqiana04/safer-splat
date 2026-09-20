#!/usr/bin/env python3
"""Post-collection-only formal analyzer; never called by the collection launcher."""
from __future__ import annotations
import argparse, csv, importlib.util, json, math, os, random, statistics, sys
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
    os.chdir(REPO); p=read(PROTOCOL); root=Path(p["future_result_root"])
    validate_phase(ValidationPhase.POSTCOLLECTION)
    if not (root/"BATCH_COMPLETE.json").is_file() or read(root/"BATCH_COMPLETE.json").get("trial_order")!=TRIALS: raise RuntimeError("ANALYSIS_REQUIRES_85_OF_85_IMMUTABLE_LOCKS")
    if any(not (root/f"trial_{t}_complete.json").is_file() or not (root/"raw"/f"trial_{t}"/"runtime_trace_lock.json").is_file() for t in TRIALS): raise RuntimeError("ANALYSIS_REQUIRES_85_OF_85_IMMUTABLE_LOCKS")
    reference={}
    with (Path(p["reference_authority"]["root"])/"FORMAL_PAIR_SUMMARY.csv").open(encoding="utf-8",newline="") as f:
        for row in csv.DictReader(f):
            if row["cohort"]=="primary": reference[int(row["trial_id"])]=float(row["ref_progress"])
    if set(reference)!=set(TRIALS): raise RuntimeError("FROZEN_REFERENCE_OUTCOMES_INCOMPLETE")
    old={}
    with (Path(p["historical_active_authority"]["root"])/"POST_REPAIR_V3_PAIRED_TRIAL_RESULTS.csv").open(encoding="utf-8",newline="") as f:
        old={int(r["trial_id"]):r for r in csv.DictReader(f)}
    states_by_trial={}; rows=[]; recovery={k:0 for k in ("eligibility_events","scans","candidate_attempts","l2_enter","l2_result","l2_pass","l2_fail","l2_unknown","l2_exception","l3_result","l3_pass","l3_fail","l3_unknown","l3_exception","selected","plantcommit","rank_resume","exhaustion")}; hard_zero={k:0 for k in p["hard_zero_integrity_gates"]}; boundary_rows=[]
    for trial in TRIALS:
        raw=root/"raw"/f"trial_{trial}"; summary=read(raw/"trial_summary.json"); obs=lines(raw/"recovery_cycle_observations.jsonl"); trace=lines(raw/"runtime_trace.jsonl"); lock=read(raw/"runtime_trace_lock.json")
        if int((raw/"process_exit_code.txt").read_text().strip())!=0: hard_zero["process_nonzero_exit_count"]+=1
        states=active_states(obs); states_by_trial[trial]=states; goal=tuple(obs[0]["goal_state"]); progress=normalized_progress(states,goal)
        commits=sum(bool(x.get("committed")) for x in obs); boundaries=sum(bool(x.get("boundary")) for x in obs)
        if len(trace)!=len(obs) or lock.get("record_count")!=len(trace): hard_zero["trace_write_failure_count"]+=1
        attempts=[a for x in obs for a in x.get("recovery_attempts",[])]; recovery["eligibility_events"]+=sum(bool(x.get("recovery_attempts")) for x in obs); recovery["candidate_attempts"]+=len(attempts)
        recovery["selected"]+=sum(a.get("supervisor_selected") is True for a in attempts); recovery["plantcommit"]+=sum(bool(x.get("committed")) and any(a.get("supervisor_selected") is True for a in x.get("recovery_attempts",[])) for x in obs)
        for a in attempts:
            l2=a.get("L2_status"); l3=a.get("L3_status"); recovery["l2_enter"]+=a.get("C0_status")=="PASS"; recovery["l2_result"]+=l2 in ("PASS","FAIL","UNKNOWN"); recovery["l2_pass"]+=l2=="PASS"; recovery["l2_fail"]+=l2=="FAIL"; recovery["l2_unknown"]+=l2=="UNKNOWN"; recovery["l2_exception"]+=a.get("exception_stage")=="L2"; recovery["l3_result"]+=l3 in ("PASS","FAIL","UNKNOWN"); recovery["l3_pass"]+=l3=="PASS"; recovery["l3_fail"]+=l3=="FAIL"; recovery["l3_unknown"]+=l3=="UNKNOWN"; recovery["l3_exception"]+=a.get("exception_stage")=="L3"
        generation=lines(raw/"recovery_generation.jsonl") if (raw/"recovery_generation.jsonl").is_file() else []; recovery["scans"]+=len(generation); recovery["exhaustion"]+=sum(not g.get("candidates") for g in generation)
        roles={"primary":0,"backup":0,"recovery":0,"terminal":0}
        for x in obs:
            selected=any(a.get("supervisor_selected") is True for a in x.get("recovery_attempts",[])); role=str(x.get("action_role") or "")
            if x.get("committed") and selected: roles["recovery"]+=1
            elif x.get("committed") and "PRIMARY" in role: roles["primary"]+=1
            elif x.get("committed") and "BACKUP" in role: roles["backup"]+=1
            elif x.get("committed") and "TERMINAL" in role: roles["terminal"]+=1
        termination=summary.get("termination_reason"); valid_boundary=(termination=="ASSURANCE_BOUNDARY" and summary.get("hard_blocker") is None and summary.get("finalization_status")=="FINALIZED" and boundaries==1 and len(obs)==commits+1 and not obs[-1].get("committed"))
        if boundaries: boundary_rows.append({"trial_id":trial,"cycle_index":obs[-1]["cycle_index"],"final_supervisor_reason":obs[-1].get("supervisor_reason"),"completed_cycles":len(obs),"plant_commit_count":commits,"last_committed_progress":progress,"reference_progress":reference[trial],"paired_delta":progress-reference[trial],"deadline_state_at_boundary":(obs[-1].get("deadline_observations") or [{}])[-1].get("status"),"recovery_activity_before_boundary":sum(bool(x.get("recovery_attempts")) for x in obs),"typed_boundary_contract_valid":valid_boundary})
        rows.append({"trial_id":trial,"bounded_recovery_progress":progress,"reference_progress":reference[trial],"paired_progress_delta":progress-reference[trial],"old_repaired_active_progress":float(old[trial]["active_progress"]),"bounded_recovery_minus_old_active":progress-float(old[trial]["active_progress"]),"completed_cycles":len(obs),"plant_commits":commits,"assurance_boundary_count":boundaries,**{f"{k}_commits":v for k,v in roles.items()}})
    hard=hard_proxy(states_by_trial,p); hard_by={x["trial_id"]:x for x in hard}
    for row in rows: row.update(hard_by[row["trial_id"]]); row["reference_hard_violation"]=False; row["active_only_hard_discordant"]=row["hard_violation_segments"]>0
    unknown=sum(x["hard_unknown_segments"] for x in hard); active_hard=sum(x["hard_violation_segments"]>0 for x in hard); active_only=sum(x["active_only_hard_discordant"] for x in rows)
    hard_zero["represented_map_hard_violation_count"]=sum(x["hard_violation_segments"] for x in hard); integrity=not any(hard_zero.values()) and recovery["l2_exception"]==recovery["l3_exception"]==0 and all(x.get("typed_boundary_contract_valid",True) for x in boundary_rows)
    deltas=[x["paired_progress_delta"] for x in rows]; ci=bootstrap(deltas) if integrity and unknown==0 else None; decision=decide(integrity,unknown,active_hard,active_only,None if ci is None else ci["lower95"])
    progress={"n":85,"mean_delta":statistics.mean(deltas),"median_delta":statistics.median(deltas),"min_delta":min(deltas),"max_delta":max(deltas),"positive_count":sum(x>0 for x in deltas),"zero_count":sum(x==0 for x in deltas),"negative_count":sum(x<0 for x in deltas),"bootstrap_percentile_95":ci,"margin":-0.02,"strict_comparator":"lower95 > -0.02","equality_at_margin":"FAIL","clipping":"NONE","strict_ni_pass":ci is not None and ci["lower95"]>-0.02}
    routing={"descriptive_only":True,"role":"DESCRIPTIVE_ONLY_NO_ROUTING_CONDITIONED_GATE_OR_TUNING","totals":{k:sum(x[f"{k}_commits"] for x in rows) for k in ("primary","backup","recovery","terminal")},"boundary_trials":len(boundary_rows),"per_trial":rows}
    hard_result={"active_hard_violation_trials":active_hard,"hard_violation_segments":sum(x["hard_violation_segments"] for x in hard),"hard_unknown_segments":unknown,"active_only_hard_discordant_pairs":active_only,"reference_hard_violation_trials":0,"global_min_hard_clearance_q":min(x["minimum_hard_clearance_q"] for x in hard if x["minimum_hard_clearance_q"] is not None),"negative_tolerance":None,"epsilon":None,"hard_gate_pass":active_hard==active_only==unknown==0}
    result={"schema":"POST_REPAIR_V3_BOUNDED_RECOVERY_COLLECTION_SUMMARY_V1","status":decision,"trials_completed":85,"hard_zero_counts":hard_zero,"recovery":recovery,"historical_repaired_active_verdict":"FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE","historical_result_rewritten":False,"scientific_boundary":p["scientific_boundary"]}
    if write_outputs:
        fields=list(rows[0]);
        with (root/"POST_REPAIR_V3_BOUNDED_RECOVERY_TRIAL_RESULTS.csv").open("w",encoding="utf-8",newline="") as f: w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
        write(root/"POST_REPAIR_V3_BOUNDED_RECOVERY_COLLECTION_SUMMARY.json",result); write(root/"POST_REPAIR_V3_BOUNDED_RECOVERY_PROGRESS_ANALYSIS.json",progress); write(root/"POST_REPAIR_V3_BOUNDED_RECOVERY_HARD_SAFETY_ANALYSIS.json",hard_result); write(root/"POST_REPAIR_V3_BOUNDED_RECOVERY_CONTINUITY_ANALYSIS.json",hard_zero); write(root/"POST_REPAIR_V3_BOUNDED_RECOVERY_ROUTING_ANALYSIS.json",routing); write(root/"POST_REPAIR_V3_BOUNDED_RECOVERY_RECOVERY_ANALYSIS.json",recovery); write(root/"POST_REPAIR_V3_BOUNDED_RECOVERY_BOUNDARY_ANALYSIS.json",{"total_boundary_trials":len(boundary_rows),"trial_ids":[x["trial_id"] for x in boundary_rows],"rows":boundary_rows}); write(root/"POST_REPAIR_V3_BOUNDED_RECOVERY_HISTORICAL_ACTIVE_DIAGNOSTIC.json",{"role":"SECONDARY_DIAGNOSTIC_ONLY_NOT_PRIMARY_FORMAL_GATE","rows":[{"trial_id":x["trial_id"],"bounded_recovery_minus_old_active":x["bounded_recovery_minus_old_active"]} for x in rows]})
        (root/"POST_REPAIR_V3_BOUNDED_RECOVERY_FAILURE_REGISTER.csv").write_text("trial_id,failure_class,detail\n",encoding="utf-8")
        report=root/"report/REPORT_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_V1.md"; report.parent.mkdir(parents=True,exist_ok=True); report.write_text(f"# Post-Repair V3 Bounded Recovery Paired Validation V1\n\nNew prospective result: `{decision}`.\n\nHistorical repaired-Active result: `FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE` (unchanged).\n\nRepeatedly exposed Stonehenge benchmark; not a pristine holdout or cross-scene, physical-world safety, hard-real-time, or deployment claim.\n",encoding="utf-8")
    return result

def main()->int:
    a=argparse.ArgumentParser(description=__doc__); a.add_argument("--post-collection-authorized",action="store_true"); args=a.parse_args()
    if not args.post_collection_authorized: raise RuntimeError("POST_COLLECTION_AUTHORIZATION_REQUIRED")
    result=analyze(True); print(result["status"]); return 0 if result["status"]!=BLOCK else 2
if __name__=="__main__": raise SystemExit(main())
