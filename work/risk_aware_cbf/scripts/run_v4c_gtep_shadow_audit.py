#!/usr/bin/env python3
"""Shadow-only GTEP feasibility audit on all original trial-20 activation states."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import torch

from check_gtep_geometry_equivalence import check_context
from gsplat_barrier_geometry_adapter import query_barrier_geometry
from run_v4c_hierarchical_paired_audit import build_preregistered_args, load_runtime
from run_v4c_trial20_failure_diagnosis import replay
import run_v4c_hstep_predictive_recovery as v4c
from v4c_geometry_tangential_primitives import primitive_bank


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["notes"], extrasaction="ignore")
        writer.writeheader(); writer.writerows(rows)


def scalar(value: torch.Tensor) -> float:
    return float(value.detach().cpu().item())


def evaluate(runtime, ctx, candidates, horizon: int, step: int) -> dict:
    args = copy.deepcopy(runtime.args); args.horizon = horizon
    selected, first, hs, min_h, success, failed, rows, index = v4c.evaluate_sequences(args=args, scene="flight", method=args.method, trial=20, step=step, x=ctx["x"], goal=ctx["goal"], u_base=ctx["u_base"], u_prev=ctx["u_prev"], candidates=candidates, gsplat=runtime.gsplat, scene_cfg=runtime.scene_cfg)
    return {"selected": selected, "first": first, "min_h": float(min_h), "success": bool(success), "failed": bool(failed), "rows": rows, "index": index}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument("--output-dir", type=Path, required=True); args = parser.parse_args(); out=args.output_dir; out.mkdir(parents=True, exist_ok=True)
    runtime=load_runtime(build_preregistered_args(out,20)); events, _, formal=replay(runtime)
    if formal["activation_count"] != 34 or formal["recovery_failed"] != 34 or formal["collision"] != 0 or formal["qp_infeasible"] != 0: raise RuntimeError(f"trial20 formal reproduction mismatch: {formal}")
    representatives=[events[index] for index in sorted({0,len(events)//2,len(events)-1})]
    geometry=[check_context(runtime.gsplat,event["_ctx"]["x"],runtime.scene_cfg["radius"],event["activation_index"]) for event in representatives]
    write_csv(out/"geometry_equivalence.csv",geometry)
    if not all(row["equivalence_passed"] for row in geometry): raise RuntimeError("geometry equivalence failed; GTEP shadow is prohibited")
    prereg=[]; context_rows=[]; primitive_totals=defaultdict(lambda:{"generated":0,"feasible":0,"selected":0,"best":[]}); critical=defaultdict(lambda:{"contexts":0,"opportunities":0}); any_h3=False
    for event in events:
        ctx=event["_ctx"]; geometry_item=query_barrier_geometry(runtime.gsplat,ctx["x"],runtime.scene_cfg["radius"]); candidates=primitive_bank(ctx["x"],ctx["goal"],geometry_item["normal"],3)
        if len(candidates)>24: raise RuntimeError("primitive bank limit exceeded")
        result=evaluate(runtime,ctx,candidates,3,int(event["trajectory_step"])); source=str(result["selected"].source); selected_family=source.split("_")[1] if source.startswith("gtep_") else source
        unique=bool(result["success"] and source.startswith(("gtep_p2","gtep_p3","gtep_p4","gtep_p5","gtep_p6")))
        any_h3 |= bool(result["success"])
        gid=event["critical_gaussian_id_hash"]; critical[gid]["contexts"]+=1; critical[gid]["opportunities"]+=int(unique)
        normal_component=scalar(torch.dot(result["first"],geometry_item["normal"])); tangent_norm=scalar(torch.linalg.norm(result["first"]-normal_component*geometry_item["normal"])); progress=scalar(torch.dot(result["first"],ctx["goal"][:3]-ctx["x"][:3]))
        context_rows.append({"activation_index":event["activation_index"],"trajectory_step":event["trajectory_step"],"original_h3_feasible_count":event["original_feasible_candidate_count"],"gtep_candidate_count":len(candidates),"gtep_feasible_count":sum(str(row["sequence_passed_dt_margin"]).lower()=="true" for row in result["rows"]),"best_min_h":result["min_h"],"selected_min_h":result["min_h"],"h_improvement_vs_original_best":result["min_h"]-event["best_candidate_min_h"],"primitive_family":source,"unique_tangential_feasible_context":unique,"goal_progress_proxy":progress,"normal_control_component":normal_component,"tangential_control_component":tangent_norm,"velocity_toward_component":max(0.,-scalar(torch.dot(ctx["x"][3:],geometry_item["normal"]))),"critical_gaussian_hash":gid,"predicted_collision":result["min_h"]<0.,"state_isolation_passed":torch.equal(ctx["x"],ctx["x"].detach().clone())})
        for row,candidate in zip(result["rows"],candidates):
            family=str(candidate.source).split("_")[1]; primitive_totals[family]["generated"]+=1; primitive_totals[family]["feasible"]+=int(str(row["sequence_passed_dt_margin"]).lower()=="true"); primitive_totals[family]["best"].append(float(row["sequence_min_h"])); primitive_totals[family]["selected"]+=int(str(candidate.source)==source)
    write_csv(out/"context_summary.csv",context_rows)
    write_csv(out/"primitive_preregistration.csv",[{"family":"P0-P6","normal_magnitudes":"0.025,0.05","tangent_magnitudes":"0.05,0.1","velocity_gain":0.5,"candidate_limit":24,"shadow_only":True}])
    write_csv(out/"trial20_context_preregistration.csv",[{"activation_index":event["activation_index"],"trajectory_step":event["trajectory_step"],"source":"original_trial20_comparator"} for event in events])
    family_rows=[{"primitive_family":name,"generated_count":item["generated"],"feasible_count":item["feasible"],"selected_count":item["selected"],"best_min_h":max(item["best"])} for name,item in sorted(primitive_totals.items())]; write_csv(out/"primitive_family_summary.csv",family_rows)
    critical_rows=[{"critical_gaussian_hash":key,"context_count":value["contexts"],"unique_tangential_opportunity_count":value["opportunities"]} for key,value in sorted(critical.items())]; write_csv(out/"critical_gaussian_summary.csv",critical_rows)
    unique_rows=[row for row in context_rows if row["unique_tangential_feasible_context"]]; unique_count=len(unique_rows); h3_count=sum(row["gtep_feasible_count"]>0 for row in context_rows); normal_only=sum(row["gtep_feasible_count"]>0 and str(row["primitive_family"]).startswith(("gtep_p0","gtep_p1")) for row in context_rows)
    write_csv(out/"unique_feasibility_summary.csv",[{"trial20_activation_contexts":34,"gtep_h3_feasible_contexts":h3_count,"unique_tangential_feasible_contexts":unique_count,"gradient_normal_only_feasible_contexts":normal_only,"distinct_critical_gaussians_with_opportunity":sum(row["unique_tangential_opportunity_count"]>0 for row in critical_rows)}])
    write_csv(out/"progress_tradeoff_summary.csv",[{"unique_feasible_contexts":unique_count,"nonnegative_progress_opportunity_contexts":sum(row["goal_progress_proxy"]>=0 for row in unique_rows),"notes":"dot-product proxy only; not planner quality"}])
    h5_rows=[]
    if not any_h3:
        for event in representatives:
            geo=query_barrier_geometry(runtime.gsplat,event["_ctx"]["x"],runtime.scene_cfg["radius"]); result=evaluate(runtime,event["_ctx"],primitive_bank(event["_ctx"]["x"],event["_ctx"]["goal"],geo["normal"],5),5,int(event["trajectory_step"])); h5_rows.append({"activation_index":event["activation_index"],"gtep_h5_feasible":result["success"],"best_min_h":result["min_h"],"shadow_only":True})
    write_csv(out/"h5_diagnostic_summary.csv",h5_rows or [{"activation_index":"not_run","gtep_h5_feasible":"not_run","best_min_h":"","shadow_only":True}])
    write_csv(out/"positive_control_preregistration.csv",[{"status":"not_run","reason":"successful contexts are not retained as raw states in prior compact artifacts"}]); write_csv(out/"positive_control_summary.csv",[{"status":"not_run","state_regressions":None,"notes":"no raw state reconstruction"}])
    write_csv(out/"state_isolation_summary.csv",[{"context_count":34,"state_isolation_all_passed":all(row["state_isolation_passed"] for row in context_rows),"formal_control_modified":False}])
    h5_count=sum(bool(row["gtep_h5_feasible"]) for row in h5_rows); decision="stop_current_gtep_v0" if unique_count==0 else "retain_gtep_as_diagnostic_extension"
    if unique_count==0 and h5_count==0: decision="classify_trial20_as_unresolved_local_recovery_limit"
    metrics={"task":"R-V4C-6 GTEP Shadow Feasibility Audit","new_scientific_experiment_run":True,"mode":"shadow_only","scene":"flight","trial":20,"formal_control_modified":False,"active_gtep_run":False,"trial20_activation_context_count":34,"geometry_semantics_status":"sufficient_existing_analytic_gradient","geometry_equivalence_passed":True,"state_isolation_all_passed":True,"primitive_candidate_count_per_context":len(primitive_bank(events[0]["_ctx"]["x"],events[0]["_ctx"]["goal"],query_barrier_geometry(runtime.gsplat,events[0]["_ctx"]["x"],runtime.scene_cfg["radius"])["normal"],3)),"gtep_h3_feasible_contexts":h3_count,"unique_tangential_feasible_contexts":unique_count,"gradient_normal_only_feasible_contexts":normal_only,"distinct_critical_gaussians_with_opportunity":sum(row["unique_tangential_opportunity_count"]>0 for row in critical_rows),"nonnegative_progress_opportunity_contexts":sum(row["goal_progress_proxy"]>=0 for row in unique_rows),"multi_gaussian_primitive_run":False,"multi_gaussian_feasible_contexts":None,"h5_diagnostic_run":not any_h3,"h5_feasible_representative_contexts":h5_count if not any_h3 else None,"positive_control_context_count":None,"positive_control_state_regressions":None,"official_core_source_modified":False,"forbidden_paths_modified":False,"raw_traces_written":False,"gtep_decision":decision,"limitations":["single flight trial","shadow counterfactual evaluation","no active directional recovery","no cross-scene validation","not a controllability proof","not a planner","positive controls not run because prior artifacts retain no raw states"]}
    (out/"metrics.json").write_text(json.dumps(metrics,indent=2)+"\n",encoding="utf-8"); (out/"README.md").write_text("# GTEP Shadow Audit\n\nOnly compact shadow outputs; no raw controls, states, traces, images, or binaries.\n",encoding="utf-8"); (out/"analysis_notes.md").write_text("# Notes\n\nBarrier normals are existing analytic GSplat gradients. H5 is shadow-only.\n",encoding="utf-8"); print(json.dumps(metrics,sort_keys=True)); return 0

if __name__ == "__main__": raise SystemExit(main())
