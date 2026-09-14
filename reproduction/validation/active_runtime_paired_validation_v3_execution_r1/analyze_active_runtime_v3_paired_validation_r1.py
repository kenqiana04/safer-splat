#!/usr/bin/env python3
"""Post-collection V3 paired analysis. Never imported by the execution launcher."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, random, statistics, sys
from pathlib import Path
from typing import Any

PRIMARY=(0,1,2,3,4,6,7,8,9,11,12,13,14,16,17,18,19,20,21,22,23,24,26,27,28,29,31,32,33,34,36,37,38,39,40,41,42,43,44,46,47,48,49,51,52,53,54,56,57,58,59,60,61,62,63,64,66,67,68,69,71,72,73,74,76,77,78,79,80,81,82,83,84,86,87,88,89,91,92,93,94,96,97,98,99)
BOOTSTRAP_N=10000; BOOTSTRAP_SEED=20260911; NI_MARGIN=-0.02

def load_json(p: Path) -> dict[str,Any]: return json.loads(p.read_text(encoding="utf-8"))
def write_json(p: Path,v: Any)->None: p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8",newline="\n")
def sha(p: Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()
def qtile(xs:list[float],q:float)->float:
    s=sorted(xs); x=q*(len(s)-1); lo=math.floor(x); hi=math.ceil(x)
    return s[lo] if lo==hi else s[lo]+(s[hi]-s[lo])*(x-lo)
def bootstrap(xs:list[float])->dict[str,Any]:
    rng=random.Random(BOOTSTRAP_SEED); n=len(xs); vals=[statistics.mean([xs[rng.randrange(n)] for _ in range(n)]) for _ in range(BOOTSTRAP_N)]
    return {"resamples":BOOTSTRAP_N,"seed":BOOTSTRAP_SEED,"lower95":qtile(vals,.025),"upper95":qtile(vals,.975)}
def import_file(path:Path,name:str)->Any:
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError("IMPORT_FAILED:"+str(path))
    m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m

def read_active_states(raw:Path)->list[tuple[float,...]]:
    rows=[json.loads(x) for x in (raw/"cycle_observations.jsonl").read_text().splitlines() if x]
    if not rows: raise RuntimeError("ACTIVE_STATE_EVIDENCE_EMPTY")
    states=[tuple(rows[0]["pre_state"])]
    for row in rows:
        if row["committed"]:
            if row["post_state"] is None: raise RuntimeError("COMMITTED_POST_STATE_MISSING")
            states.append(tuple(row["post_state"]))
    return states
def read_reference_states(root:Path,record:dict[str,Any])->list[tuple[float,...]]:
    tid=int(record["trial_id"])
    p=root/record["accepted_attempt_relative_path"]/"raw"/f"trial_{tid:03d}"/"reference_cbf_qp"/"trajectory_states.jsonl"
    if sha(p)!=record["locked_files"]["trajectory_states.jsonl"]["sha256"]: raise RuntimeError("REFERENCE_TRAJECTORY_DRIFT")
    rows=[json.loads(x) for x in p.read_text().splitlines() if x]
    return [tuple(r.get("state",r.get("x",r))) for r in rows]

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--checkout",type=Path,required=True); ap.add_argument("--result-root",type=Path,required=True); ap.add_argument("--map-source-root",type=Path,required=True); ap.add_argument("--post-collection-authorized",action="store_true"); a=ap.parse_args()
    if not a.post_collection_authorized:
        print("ANALYZER_FROZEN_NOT_EXECUTED"); return 3
    checkout=a.checkout.resolve(strict=True); result=a.result_root.resolve(strict=True); task=Path(__file__).resolve().parent
    runner=import_file(task/"run_active_runtime_v3_paired_validation_r1.py","_paired_runner_r1")
    if any(not runner.complete_evidence(result,t) for t in PRIMARY): raise RuntimeError("ANALYSIS_REQUIRES_85_OF_85_COMPLETE_ACTIVE_LOCKS")
    protocol,_,reuse=runner.frozen(checkout); runner.verify_reference(reuse); runner.verify_map(protocol,a.map_source_root)
    # The oracle is constructed only after all immutable execution evidence exists.
    import numpy as np, torch
    sys.path[:0]=[str(checkout/"reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1"),str(checkout)]
    from splat.gsplat_utils import GSplatLoader
    from adapters.gaussian_barrier_adapter import SourceGaussianBarrierAdapter
    v2=import_file(checkout/"reproduction/pilot/active_runtime_pilot_v2/run_active_runtime_pilot_v2.py","_paired_oracle_helpers")
    loader=GSplatLoader((a.map_source_root/"config.yml").resolve(strict=True),torch.device("cuda:0")); map_id=protocol["map"]["identity"]
    def evaluate(states:list[tuple[float,...]],goal:list[float],radius:float)->dict[str,Any]:
        def query(point:Any,**kwargs:Any):
            if not torch.is_tensor(point): point=torch.as_tensor(point,device=torch.device("cuda:0"),dtype=torch.float32)
            return loader.query_distance(point,**kwargs)
        provider=SourceGaussianBarrierAdapter(query,map_id,radius,int(loader.means.shape[0])); violations=unknown=0; clear=[]
        for x,y in zip(states[:-1],states[1:]):
            status,c=v2.certify_segment_clearance(provider,np.asarray(x[:3]),np.asarray(y[:3]),radius)
            violations+=int(status=="UNSAFE"); unknown+=int(status not in {"SAFE","UNSAFE"}); clear.extend([] if c is None else [float(c)])
        start=np.asarray(states[0][:3]); final=np.asarray(states[-1][:3]); target=np.asarray(goal[:3]); d0=float(np.linalg.norm(start-target)); d1=float(np.linalg.norm(final-target))
        return {"radius_q":radius,"violation_segment_count":violations,"violation_trial":violations>0,"unknown_segment_count":unknown,"min_clearance_q":min(clear) if clear else None,"normalized_progress":None if d0==0 else (d0-d1)/d0}
    records={int(x["trial_id"]):x for x in reuse["records"]}; refroot=Path(reuse["formal_v2_result_root"]); pairs=[]
    for tid in PRIMARY:
        summary=load_json(result/"raw"/f"trial_{tid}"/"trial_summary.json"); active=read_active_states(result/"raw"/f"trial_{tid}"); ref=read_reference_states(refroot,records[tid]); goal=summary["goal_state"]
        a15=evaluate(active,goal,.015); r15=evaluate(ref,goal,.015); a25=evaluate(active,goal,.025); r25=evaluate(ref,goal,.025)
        pairs.append({"trial_id":tid,"active_hard":a15,"reference_hard":r15,"active_historical_diagnostic":a25,"reference_historical_diagnostic":r25,"paired_progress_difference":a15["normalized_progress"]-r15["normalized_progress"],"historical_0p025_diagnostic_only":True,"oracle_feedback":False})
    if len(pairs)!=85: raise RuntimeError("PAIR_DENOMINATOR_NOT_85")
    active_violation=sum(p["active_hard"]["violation_trial"] for p in pairs); reference_violation=sum(p["reference_hard"]["violation_trial"] for p in pairs)
    active_only=sum(p["active_hard"]["violation_trial"] and not p["reference_hard"]["violation_trial"] for p in pairs); unknown=sum(p["active_hard"]["unknown_segment_count"]+p["reference_hard"]["unknown_segment_count"] for p in pairs)
    deltas=[float(p["paired_progress_difference"]) for p in pairs]; ci=bootstrap(deltas); integrity=True; safety=active_violation==0 and active_only==0 and unknown==0; ni=ci["lower95"]>NI_MARGIN
    decision="PASS_V3_PAIRED_VALIDATION_ON_FROZEN_STONEHENGE_BENCHMARK" if integrity and safety and ni else ("FAIL_V3_HARD_SAFETY_GATE" if not safety else "FAIL_V3_PROGRESS_NONINFERIORITY")
    out={"schema":"ACTIVE_RUNTIME_V3_PAIRED_ANALYSIS_V1","paired_eligible_count":85,"active_hard_violation_trials":active_violation,"reference_hard_violation_trials":reference_violation,"active_only_hard_discordant_pairs":active_only,"unresolved_oracle_unknown":unknown,"mean_paired_progress_difference":statistics.mean(deltas),"median_paired_progress_difference":statistics.median(deltas),"pair_bootstrap_percentile_CI_95":ci,"noninferiority_margin":NI_MARGIN,"progress_noninferiority_pass":ni,"hard_safety_gate_pass":safety,"final_decision":decision,"historical_0p025_primary_authority":False,"claim_boundary":protocol["claim_boundary"]}
    write_json(result/"V3_PAIRED_PER_PAIR_ANALYSIS.json",pairs); write_json(result/"V3_PAIRED_ANALYSIS_SUMMARY.json",out)
    print("ACTIVE_RUNTIME_V3_PAIRED_ANALYSIS_COMPLETE"); print(decision); return 0
if __name__=="__main__": raise SystemExit(main())
