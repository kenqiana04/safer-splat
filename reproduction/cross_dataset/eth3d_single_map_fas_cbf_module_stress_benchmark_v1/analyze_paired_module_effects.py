#!/usr/bin/env python3
"""Scenario-level paired analysis for the frozen ETH3D controller matrix."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from eth3d_controller_core import METHODS, atomic_json


COMPARISONS = (
    ("H1_START_SAFE", METHODS[0], METHODS[1], "G1_START_SAFE_BOUNDARY"),
    ("H2_FEASIBILITY_AWARE", METHODS[1], METHODS[2], "G2_FEASIBILITY_DENSE"),
    ("H3_DISCRETE_TIME", METHODS[2], METHODS[3], "G3_SAMPLED_DATA_GAP"),
    ("H4_PREDICTIVE_RECOVERY", METHODS[3], METHODS[4], "G4_PREDICTIVE_RECOVERY"),
    ("H5_FULL", METHODS[0], METHODS[4], "OVERALL"),
)
METRICS = ("reference_collision", "completion", "progress_m", "qp_infeasible",
           "deadlock", "min_segment_clearance", "runtime_mean_s",
           "active_constraints_mean", "forced_candidate_count_mean",
           "fallback_count", "segment_risk_events", "recovery_success")


def bootstrap_ci(values: np.ndarray, rng: np.random.Generator, n: int = 10000) -> list[float]:
    values = np.asarray(values, dtype=np.float64)
    if len(values) == 0: return [float("nan"), float("nan")]
    means = np.empty(n)
    for start in range(0, n, 500):
        count = min(500, n-start)
        indices = rng.integers(0, len(values), size=(count, len(values)))
        means[start:start+count] = values[indices].mean(axis=1)
    return [float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))]


def numeric(row: dict, metric: str) -> float:
    value = row.get(metric)
    if value is None: return float("nan")
    return float(value)


def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--results",type=Path,required=True); parser.add_argument("--output-dir",type=Path,required=True)
    args=parser.parse_args(); args.output_dir.mkdir(parents=True,exist_ok=True)
    rows=[json.loads(path.read_text()) for path in sorted(args.results.glob("*.json")) if not path.name.endswith(".complete.json")]
    if len(rows)!=500: raise RuntimeError(f"expected 500 results, found {len(rows)}")
    by={(row["scenario_id"],row["method"]):row for row in rows}
    if len(by)!=500: raise RuntimeError("duplicate paired result identity")
    rng=np.random.default_rng(20260804); paired={}; flat=[]; failures=[]
    for hypothesis, older, newer, group in COMPARISONS:
        scenario_ids=sorted({row["scenario_id"] for row in rows if group=="OVERALL" or row["group"]==group})
        metrics={}
        for metric in METRICS:
            old=np.asarray([numeric(by[(sid,older)],metric) for sid in scenario_ids]); new=np.asarray([numeric(by[(sid,newer)],metric) for sid in scenario_ids])
            valid=np.isfinite(old)&np.isfinite(new); diff=new[valid]-old[valid]
            wins=int(np.sum(diff>1e-12)); losses=int(np.sum(diff<-1e-12)); ties=int(np.sum(np.abs(diff)<=1e-12))
            metrics[metric]={"n":int(len(diff)),"mean_new_minus_old":float(np.mean(diff)) if len(diff) else None,
                             "median_new_minus_old":float(np.median(diff)) if len(diff) else None,
                             "bootstrap_95_ci":bootstrap_ci(diff,rng) if len(diff) else [None,None],
                             "newer_mean":float(np.mean(new[valid])) if np.any(valid) else None,
                             "older_mean":float(np.mean(old[valid])) if np.any(valid) else None,
                             "win_tie_loss_raw_direction":[wins,ties,losses]}
            if metric == "reference_collision":
                metrics[metric]["newer_only"] = int(np.sum((old == 0) & (new == 1)))
                metrics[metric]["older_only"] = int(np.sum((old == 1) & (new == 0)))
        paired[hypothesis]={"older":older,"newer":newer,"group":group,"scenario_count":len(scenario_ids),"metrics":metrics}
        for sid in scenario_ids:
            old,new=by[(sid,older)],by[(sid,newer)]
            row={"hypothesis":hypothesis,"scenario_id":sid,"group":old["group"],"older":older,"newer":newer}
            for metric in METRICS: row[f"older_{metric}"]=old.get(metric); row[f"newer_{metric}"]=new.get(metric)
            flat.append(row)
            if ((not bool(old.get("reference_collision"))) and bool(new.get("reference_collision"))) or (bool(old.get("completion")) and not bool(new.get("completion"))) or float(new.get("progress_m",0))-float(old.get("progress_m",0)) < -0.05:
                failures.append({"hypothesis":hypothesis,"scenario_id":sid,"group":old["group"],
                                 "older_status":old["status"],"newer_status":new["status"],
                                 "older_collision":bool(old.get("reference_collision")),"newer_collision":bool(new.get("reference_collision")),
                                 "progress_difference_m":float(new.get("progress_m",0))-float(old.get("progress_m",0))})

    activation={
        "H1_START_SAFE":sum(bool(by[(sid,METHODS[1])].get("projection",{}).get("attempted")) for sid in {r['scenario_id'] for r in rows if r['group']=='G1_START_SAFE_BOUNDARY'}),
        "H2_FEASIBILITY_AWARE":sum(by[(sid,METHODS[2])].get("active_constraints_mean",2000)<by[(sid,METHODS[1])].get("active_constraints_mean",2000) for sid in {r['scenario_id'] for r in rows if r['group']=='G2_FEASIBILITY_DENSE'}),
        "H3_DISCRETE_TIME":sum(by[(sid,METHODS[3])].get("dt_triggers",0)>0 for sid in {r['scenario_id'] for r in rows if r['group']=='G3_SAMPLED_DATA_GAP'}),
        "H4_PREDICTIVE_RECOVERY":sum(by[(sid,METHODS[4])].get("recovery_triggers",0)>0 for sid in {r['scenario_id'] for r in rows if r['group']=='G4_PREDICTIVE_RECOVERY'}),
    }
    evidence={}
    collision_regression=False
    for hypothesis,older,newer,group in COMPARISONS:
        stats=paired[hypothesis]["metrics"]
        collision_delta=stats["reference_collision"]["mean_new_minus_old"] or 0.0
        newer_only_collision = int(stats["reference_collision"].get("newer_only", 0))
        collision_regression = collision_regression or newer_only_collision > 0
        if hypothesis=="H1_START_SAFE": primary=-(stats["qp_infeasible"]["mean_new_minus_old"] or 0.0); activated=activation[hypothesis]
        elif hypothesis=="H2_FEASIBILITY_AWARE": primary=-(stats["active_constraints_mean"]["mean_new_minus_old"] or 0.0); activated=activation[hypothesis]
        elif hypothesis=="H3_DISCRETE_TIME": primary=(stats["min_segment_clearance"]["mean_new_minus_old"] or 0.0); activated=activation[hypothesis]
        elif hypothesis=="H4_PREDICTIVE_RECOVERY": primary=-(stats["deadlock"]["mean_new_minus_old"] or 0.0); activated=activation[hypothesis]
        else: primary=-(stats["deadlock"]["mean_new_minus_old"] or 0.0); activated=sum(activation.values())
        ci_key="active_constraints_mean" if hypothesis=="H2_FEASIBILITY_AWARE" else ("min_segment_clearance" if hypothesis=="H3_DISCRETE_TIME" else "deadlock" if hypothesis in {"H4_PREDICTIVE_RECOVERY","H5_FULL"} else "qp_infeasible")
        ci=stats[ci_key]["bootstrap_95_ci"]
        direction_ci_excludes_zero=(ci[0] is not None and (ci[1]<0 if ci_key!="min_segment_clearance" else ci[0]>0))
        if newer_only_collision > 0: category="REGRESSION"
        elif activated==0: category="INACTIVE"
        elif primary>0 and direction_ci_excludes_zero: category="SUPPORTED"
        elif primary>0: category="PROMISING"
        else: category="NOT_SUPPORTED"
        evidence[hypothesis]={"category":category,"designated_group":group,"activation_count":int(activated),
                              "primary_effect_direction_value":float(primary),"collision_delta":float(collision_delta),
                              "ci_metric":ci_key,"bootstrap_95_ci":ci}

    method_summary={}
    for method in METHODS:
        method_rows=[row for row in rows if row["method"]==method]
        method_summary[method]={"runs":len(method_rows),"status_counts":dict(Counter(r["status"] for r in method_rows)),
            "reference_collisions":sum(bool(r.get("reference_collision")) for r in method_rows),
            "completions":sum(bool(r.get("completion")) for r in method_rows),
            "mean_progress_m":float(np.mean([r.get("progress_m",0) for r in method_rows])),
            "qp_infeasible":sum(int(r.get("qp_infeasible",0)) for r in method_rows),
            "mean_runtime_s":float(np.mean([r.get("runtime_mean_s",0) for r in method_rows])),
            "mean_active_constraints":float(np.mean([r.get("active_constraints_mean",0) for r in method_rows]))}
    atomic_json(args.output_dir/"paired_statistics.json",{"unit":"SCENARIO","bootstrap_resamples":10000,"bootstrap_seed":20260804,"comparisons":paired})
    atomic_json(args.output_dir/"module_evidence_matrix.json",{"evidence":evidence,"activation":activation,"collision_regression":collision_regression})
    atomic_json(args.output_dir/"failure_case_registry.json",{"failure_case_count":len(failures),"cases":failures,"no_case_deleted":True})
    atomic_json(args.output_dir/"method_summary.json",method_summary)
    atomic_json(args.output_dir/"per_run_results_compact.json", [
        {key: value for key, value in row.items() if not isinstance(value, (dict, list))}
        for row in rows
    ])
    with (args.output_dir/"per_run_results.csv").open("w",newline="",encoding="utf-8") as stream:
        fields=sorted({key for row in rows for key,value in row.items() if not isinstance(value,(dict,list))}); writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader(); writer.writerows({key:row.get(key) for key in fields} for row in rows)
    with (args.output_dir/"per_scenario_paired_table.csv").open("w",newline="",encoding="utf-8") as stream:
        fields=list(flat[0]); writer=csv.DictWriter(stream,fieldnames=fields); writer.writeheader(); writer.writerows(flat)
    print(json.dumps({"status":"PASS_PAIRED_SCENARIO_ANALYSIS","runs":len(rows),"evidence":{k:v['category'] for k,v in evidence.items()},"failures":len(failures)},sort_keys=True)); return 0


if __name__=="__main__": raise SystemExit(main())
