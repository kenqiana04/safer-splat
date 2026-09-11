#!/usr/bin/env python3
"""Final frozen analysis for Formal Paired Experiment V2."""
from __future__ import annotations
import argparse, csv, json, math, random, statistics
from collections import Counter
from pathlib import Path
from typing import Any

BOOTSTRAP_N=10000
BOOTSTRAP_SEED=20260911
NI_MARGIN=-0.02

def load_json(p): return json.loads(Path(p).read_text(encoding="utf-8"))
def write_json(p,v):
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
def qtile(xs,q):
    if not xs:return None
    s=sorted(xs); pos=q*(len(s)-1); lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    return s[lo] if lo==hi else s[lo]+(s[hi]-s[lo])*(pos-lo)
def desc(xs):
    xs=[float(x) for x in xs if x is not None]
    return {"n":len(xs),"mean":statistics.mean(xs) if xs else None,"median":statistics.median(xs) if xs else None,
            "q1":qtile(xs,.25),"q3":qtile(xs,.75),"min":min(xs) if xs else None,"max":max(xs) if xs else None}
def bootstrap(xs,stat="mean"):
    xs=[float(x) for x in xs]; rng=random.Random(BOOTSTRAP_SEED); n=len(xs)
    if not xs:return {"n":0,"lower95":None,"upper95":None}
    vals=[]
    for _ in range(BOOTSTRAP_N):
        sample=[xs[rng.randrange(n)] for _ in range(n)]
        vals.append(statistics.mean(sample) if stat=="mean" else statistics.median(sample))
    return {"resamples":BOOTSTRAP_N,"seed":BOOTSTRAP_SEED,"lower95":qtile(vals,.025),"upper95":qtile(vals,.975)}
def mcnemar_exact(b,c):
    n=b+c
    if n==0:return None
    k=min(b,c)
    tail=sum(math.comb(n,i) for i in range(k+1))/(2**n)
    return min(1.0,2*tail)
def cp_zero_upper(n):
    return None if n<=0 else 1.0 - (0.025 ** (1.0/n))  # two-sided 95% CP upper for x=0

def read_manifest(p):
    rows=[]
    with Path(p).open(encoding="utf-8",newline="") as f:
        for r in csv.DictReader(f):
            r["trial_id"]=int(r["trial_id"]); r["included_in_primary_85"]=r["included_in_primary_85"].lower()=="true"; rows.append(r)
    return rows
def read_difficulty(p):
    if not Path(p).exists():return {}
    with Path(p).open(encoding="utf-8",newline="") as f:
        return {int(r["trial_id"]):r for r in csv.DictReader(f)}
def summary_to_row(summary, cohort, stratum):
    o=summary.get("oracle") or {}; c=o.get("represented_map_collision_proxy") or {}; m=o.get("certification_margin_violation") or {}
    return {
        "trial_id":int(summary["trial_id"]),"arm":summary["arm"],"cohort":cohort,"difficulty_stratum":stratum,
        "evaluation_eligible":bool(summary.get("evaluation_eligible")),"execution_complete":bool(summary.get("execution_complete")),
        "typed_termination":summary.get("typed_termination"),"steps_executed":summary.get("steps_executed"),
        "collision_proxy_trial":bool(c.get("violation_trial")),"collision_proxy_segment_count":c.get("violation_segment_count"),
        "min_collision_clearance_m":c.get("min_clearance_m"),"margin_violation_trial":bool(m.get("violation_trial")),
        "min_margin_clearance_m":m.get("min_clearance_m"),"goal_reached":bool(o.get("goal_reached")),
        "normalized_progress":o.get("normalized_progress"),"compute_median_s":summary.get("compute_time_median_s"),
        "compute_p95_s":summary.get("compute_time_p95_s"),"compute_max_s":summary.get("compute_time_max_s"),
        "episode_wall_time_s":summary.get("episode_wall_time_s"),"hard_blocker":summary.get("hard_blocker"),
        "primary_commits":summary.get("primary_navigation_commit_count",0),"alternative_commits":summary.get("alternative_navigation_commit_count",0),
        "backup_commits":summary.get("retained_backup_commit_count",0),"terminal_commits":summary.get("terminal_commit_count",0),
        "boundary_count":summary.get("assurance_boundary_count",0),
        "deadline_open":(summary.get("deadline_status_counts") or {}).get("OPEN",0),
        "deadline_warning":(summary.get("deadline_status_counts") or {}).get("WARNING",0),
        "deadline_expired":(summary.get("deadline_status_counts") or {}).get("EXPIRED",0),
        "l1_pass":(summary.get("L1_status_counts") or {}).get("PASS",0),"l1_fail":(summary.get("L1_status_counts") or {}).get("FAIL",0),"l1_unknown":(summary.get("L1_status_counts") or {}).get("UNKNOWN",0),
        "c0_pass":(summary.get("C0_status_counts") or {}).get("PASS",0),"c0_fail":(summary.get("C0_status_counts") or {}).get("FAIL",0),"c0_unknown":(summary.get("C0_status_counts") or {}).get("UNKNOWN",0),
        "l2_pass":(summary.get("L2_status_counts") or {}).get("PASS",0),"l2_fail":(summary.get("L2_status_counts") or {}).get("FAIL",0),"l2_unknown":(summary.get("L2_status_counts") or {}).get("UNKNOWN",0),
        "l3_pass":(summary.get("L3_status_counts") or {}).get("PASS",0),"l3_fail":(summary.get("L3_status_counts") or {}).get("FAIL",0),"l3_unknown":(summary.get("L3_status_counts") or {}).get("UNKNOWN",0),
        "qp_failure":summary.get("primary_proposal_qp_failure_count",summary.get("baseline_solver_failure_count",0)),
        "token_activation":summary.get("token_activation_count",0),"token_consume":summary.get("token_consume_count",0),
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--control-dir",type=Path,required=True); ap.add_argument("--result-dir",type=Path,required=True); ap.add_argument("--plots",action="store_true")
    a=ap.parse_args(); control=a.control_dir.resolve(); result=a.result_dir.resolve()
    manifest=read_manifest(control/"FORMAL_TRIAL_MANIFEST_V2.csv"); idx=load_json(result/"FORMAL_ACCEPTED_INDEX.json")
    if len(idx.get("arms",{})) != 200: raise RuntimeError(f"FINAL_ANALYSIS_REQUIRES_200_ACCEPTED_ARMS got={len(idx.get('arms',{}))}")
    difficulty=read_difficulty(result/"FORMAL_DIFFICULTY_STRATA.csv")
    mby={r["trial_id"]:r for r in manifest}
    rows=[]; raw_manifest=[]
    for key,entry in idx["arms"].items():
        s=load_json(entry["summary_path"]); tid=int(s["trial_id"])
        if not s.get("execution_complete") or not s.get("evaluation_eligible") or s.get("hard_blocker"):
            raise RuntimeError("ACCEPTED_INDEX_CONTAINS_INELIGIBLE:"+key)
        rows.append(summary_to_row(s,mby[tid]["analysis_cohort"],difficulty.get(tid,{}).get("difficulty_stratum")))
        raw_manifest.append(entry)
    rows.sort(key=lambda r:(r["trial_id"],r["arm"]))
    arm_csv=result/"FORMAL_ARM_SUMMARY.csv"
    with arm_csv.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    by={(r["trial_id"],r["arm"]):r for r in rows}; pairs=[]
    for mr in sorted(manifest,key=lambda x:x["trial_id"]):
        tid=mr["trial_id"]; ref=by[(tid,"REFERENCE_CBF_QP")]; act=by[(tid,"ACTIVE_RUNTIME_V2")]
        pairs.append({
            "trial_id":tid,"cohort":mr["analysis_cohort"],"included_in_primary_85":mr["included_in_primary_85"],
            "difficulty_stratum":difficulty.get(tid,{}).get("difficulty_stratum"),
            "ref_progress":ref["normalized_progress"],"active_progress":act["normalized_progress"],
            "progress_delta_active_minus_ref":act["normalized_progress"]-ref["normalized_progress"],
            "ref_collision":ref["collision_proxy_trial"],"active_collision":act["collision_proxy_trial"],
            "ref_margin":ref["margin_violation_trial"],"active_margin":act["margin_violation_trial"],
            "ref_goal":ref["goal_reached"],"active_goal":act["goal_reached"],
            "ref_steps":ref["steps_executed"],"active_steps":act["steps_executed"],
            "step_delta":act["steps_executed"]-ref["steps_executed"],
            "compute_median_ratio":act["compute_median_s"]/ref["compute_median_s"] if ref["compute_median_s"] else None,
            "compute_p95_ratio":act["compute_p95_s"]/ref["compute_p95_s"] if ref["compute_p95_s"] else None,
            "termination_pair":str(ref["typed_termination"])+" | "+str(act["typed_termination"]),
        })
    with (result/"FORMAL_PAIR_SUMMARY.csv").open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(pairs[0].keys())); w.writeheader(); w.writerows(pairs)

    primary=[p for p in pairs if p["included_in_primary_85"]]; dev=[p for p in pairs if not p["included_in_primary_85"]]
    if len(primary)!=85: raise RuntimeError("PRIMARY_DENOMINATOR_NOT_85")
    deltas=[p["progress_delta_active_minus_ref"] for p in primary]
    progress_ci=bootstrap(deltas,"mean")
    ni_pass=progress_ci["lower95"] is not None and progress_ci["lower95"] > NI_MARGIN
    active_primary=[by[(p["trial_id"],"ACTIVE_RUNTIME_V2")] for p in primary]
    ref_primary=[by[(p["trial_id"],"REFERENCE_CBF_QP")] for p in primary]
    ac=sum(r["collision_proxy_trial"] for r in active_primary); rc=sum(r["collision_proxy_trial"] for r in ref_primary)
    am=sum(r["margin_violation_trial"] for r in active_primary); rm=sum(r["margin_violation_trial"] for r in ref_primary)
    active_only_collision=sum((not p["ref_collision"]) and p["active_collision"] for p in primary)
    safety_pass=(ac==0 and am==0 and active_only_collision==0)
    integrity_pass=(len(primary)==85 and all(r["evaluation_eligible"] and r["execution_complete"] and not r["hard_blocker"] for r in rows if r["cohort"]=="PRIMARY_FORMAL"))
    gate_pass=integrity_pass and safety_pass and ni_pass

    def binary_table(field_ref,field_act,subset):
        n00=n01=n10=n11=0
        for p in subset:
            r=bool(p[field_ref]); x=bool(p[field_act])
            if not r and not x:n00+=1
            elif not r and x:n01+=1
            elif r and not x:n10+=1
            else:n11+=1
        return {"n00":n00,"n01":n01,"n10":n10,"n11":n11,"mcnemar_exact_p":mcnemar_exact(n01,n10)}
    stat={
        "schema":"FORMAL_STATISTICAL_ANALYSIS_V2","primary_n":85,"development_exposed_n":15,"all100_n":100,
        "integrity_gate_pass":integrity_pass,"safety_gate_pass":safety_pass,"progress_noninferiority_pass":ni_pass,"overall_primary_gate_pass":gate_pass,
        "progress_noninferiority":{"margin":NI_MARGIN,"paired_delta":desc(deltas),"mean_delta_bootstrap95":progress_ci},
        "collision_paired_primary":binary_table("ref_collision","active_collision",primary),
        "margin_paired_primary":binary_table("ref_margin","active_margin",primary),
        "goal_paired_primary":binary_table("ref_goal","active_goal",primary),
        "zero_event_upper95_two_sided_clopper_pearson":{
            "active_collision":cp_zero_upper(85) if ac==0 else None,
            "active_margin":cp_zero_upper(85) if am==0 else None,
            "reference_collision":cp_zero_upper(85) if rc==0 else None,
            "reference_margin":cp_zero_upper(85) if rm==0 else None,
        },
        "runtime_ratios_primary":{
            "median_time_ratio":desc([p["compute_median_ratio"] for p in primary]),
            "median_time_ratio_median_bootstrap95":bootstrap([p["compute_median_ratio"] for p in primary],"median"),
            "p95_time_ratio":desc([p["compute_p95_ratio"] for p in primary]),
            "p95_time_ratio_median_bootstrap95":bootstrap([p["compute_p95_ratio"] for p in primary],"median"),
        }
    }
    write_json(result/"FORMAL_STATISTICAL_ANALYSIS.json",stat)
    write_json(result/"FORMAL_SAFETY_SUMMARY.json",{
        "primary":{"reference_collision":rc,"active_collision":ac,"reference_margin":rm,"active_margin":am,"active_only_collision_discordant":active_only_collision,"gate_pass":safety_pass},
        "all100":{"reference_collision":sum(by[(p["trial_id"],"REFERENCE_CBF_QP")]["collision_proxy_trial"] for p in pairs),"active_collision":sum(by[(p["trial_id"],"ACTIVE_RUNTIME_V2")]["collision_proxy_trial"] for p in pairs)}
    })
    write_json(result/"FORMAL_LIVENESS_SUMMARY.json",{
        "primary_progress_delta":desc(deltas),"primary_progress_delta_bootstrap95":progress_ci,"noninferiority_margin":NI_MARGIN,"noninferiority_pass":ni_pass,
        "reference_progress_primary":desc([p["ref_progress"] for p in primary]),"active_progress_primary":desc([p["active_progress"] for p in primary]),
        "reference_progress_all100":desc([p["ref_progress"] for p in pairs]),"active_progress_all100":desc([p["active_progress"] for p in pairs]),
        "goal_primary":binary_table("ref_goal","active_goal",primary)
    })
    write_json(result/"FORMAL_RUNTIME_SUMMARY.json",stat["runtime_ratios_primary"])
    active=[r for r in rows if r["arm"]=="ACTIVE_RUNTIME_V2"]
    write_json(result/"FORMAL_ACTIVE_DIAGNOSTICS.json",{
        "role_counts":{k:sum(int(r[k]) for r in active) for k in ["primary_commits","alternative_commits","backup_commits","terminal_commits","boundary_count"]},
        "deadline_counts":{"OPEN":sum(int(r["deadline_open"]) for r in active),"WARNING":sum(int(r["deadline_warning"]) for r in active),"EXPIRED":sum(int(r["deadline_expired"]) for r in active)},
        "certificate_counts":{s:{q:sum(int(r[f"{s}_{q}"]) for r in active) for q in ["pass","fail","unknown"]} for s in ["l1","c0","l2","l3"]},
        "qp_failures":sum(int(r["qp_failure"]) for r in active),"token_activation":sum(int(r["token_activation"]) for r in active),"token_consume":sum(int(r["token_consume"]) for r in active)
    })
    with (result/"FORMAL_INTEGRITY_REGISTER.csv").open("w",encoding="utf-8",newline="") as f:
        fields=["trial_id","arm","execution_complete","evaluation_eligible","hard_blocker"]; w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for r in rows:w.writerow({k:r[k] for k in fields})
    write_json(result/"FORMAL_RAW_EVIDENCE_MANIFEST.json",{"schema":"FORMAL_RAW_EVIDENCE_MANIFEST_V2","arms":raw_manifest})

    strata={}
    for name in ["HARD","MODERATE","EASY"]:
        sub=[p for p in pairs if p["difficulty_stratum"]==name]
        if sub: strata[name]={"n":len(sub),"progress_delta":desc([p["progress_delta_active_minus_ref"] for p in sub]),"runtime_median_ratio":desc([p["compute_median_ratio"] for p in sub])}
    write_json(result/"FORMAL_DIFFICULTY_ANALYSIS.json",strata)

    report=f"""# REPORT_FORMAL_PAIRED_EXPERIMENT_V2

## Primary formal cohort
- Eligible pairs: 85/85
- Integrity gate: {'PASS' if integrity_pass else 'FAIL'}
- Active represented-map collision proxy: {ac}/85
- Active certification-margin violation: {am}/85
- Safety gate: {'PASS' if safety_pass else 'FAIL'}
- Mean paired progress delta Active-Reference: {statistics.mean(deltas):.10f}
- Median paired progress delta: {statistics.median(deltas):.10f}
- 95% paired-bootstrap CI for mean delta: [{progress_ci['lower95']:.10f}, {progress_ci['upper95']:.10f}]
- Non-inferiority margin: {NI_MARGIN}
- Progress non-inferiority: {'PASS' if ni_pass else 'FAIL'}
- Overall primary protocol gate: {'PASS' if gate_pass else 'FAIL'}

## Secondary populations
- All100 descriptive pairs: {len(pairs)}
- Development-exposed secondary pairs: {len(dev)}
- Difficulty strata: {json.dumps(strata, ensure_ascii=False)}

## Claim boundary
This report concerns represented-map safety proxies, progress on the frozen Stonehenge benchmark, and measured compute overhead under the frozen engineering profile. It is not a physical collision-free, hard-real-time, deployment, global-planning, or map-independent guarantee.
"""
    (result/"REPORT_FORMAL_PAIRED_EXPERIMENT_V2.md").write_text(report,encoding="utf-8")

    if a.plots:
        import matplotlib.pyplot as plt
        # 1 scatter
        plt.figure(); plt.scatter([p["ref_progress"] for p in pairs],[p["active_progress"] for p in pairs],s=18)
        lo=min(min(p["ref_progress"] for p in pairs),min(p["active_progress"] for p in pairs)); hi=max(max(p["ref_progress"] for p in pairs),max(p["active_progress"] for p in pairs))
        plt.plot([lo,hi],[lo,hi]); plt.xlabel("Reference normalized progress"); plt.ylabel("Active normalized progress"); plt.tight_layout(); plt.savefig(result/"FIG1_PROGRESS_SCATTER.png",dpi=180); plt.close()
        plt.figure(); plt.hist([p["progress_delta_active_minus_ref"] for p in pairs],bins=20); plt.xlabel("Active - Reference normalized progress"); plt.ylabel("Count"); plt.tight_layout(); plt.savefig(result/"FIG2_PROGRESS_DELTA.png",dpi=180); plt.close()
        plt.figure(); plt.hist([p["compute_median_ratio"] for p in pairs],bins=20); plt.xlabel("Active / Reference per-trial median compute time"); plt.ylabel("Count"); plt.tight_layout(); plt.savefig(result/"FIG3_COMPUTE_RATIO.png",dpi=180); plt.close()
        labels=[x for x in ["HARD","MODERATE","EASY"] if x in strata]; vals=[strata[x]["progress_delta"]["mean"] for x in labels]
        plt.figure(); plt.bar(labels,vals); plt.xlabel("Prespecified geometry stratum"); plt.ylabel("Mean paired progress delta"); plt.tight_layout(); plt.savefig(result/"FIG4_DIFFICULTY_PROGRESS.png",dpi=180); plt.close()
    print("FORMAL_ANALYSIS_COMPLETE")
    print("overall_primary_gate_pass=",gate_pass)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
