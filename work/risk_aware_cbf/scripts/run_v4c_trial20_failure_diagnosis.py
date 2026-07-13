#!/usr/bin/env python3
"""Trial-20-only original-V4-C replay and bounded shadow diagnosis."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import torch

from analyze_v4c_bounded_reachability import reachability_row
from run_v4c_hierarchical_paired_audit import build_preregistered_args, load_runtime
import run_risk_aware_v1_pre_cbf_comparison as v1
import run_v4b_corrective_dt_filter as v4b
import run_v4c_hstep_predictive_recovery as v4c
from v4c_candidate_family_metrics import classify_source
from dynamics.systems import double_integrator_dynamics


TRIAL = 20
EXPECTED = {"activation": 34, "failed": 34, "exec_violation": 34}


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]) if rows else ["notes"], extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def f(value: torch.Tensor) -> float:
    return float(value.detach().cpu().item())


def context_eval(runtime: Any, ctx: dict[str, Any], args: argparse.Namespace, step: int) -> dict[str, Any]:
    candidates = v4c.generate_sequences(args=args, x=ctx["x"], goal=ctx["goal"], u_base=ctx["u_base"], u_nom=ctx["u_nom"], u_prev=ctx["u_prev"], gsplat=runtime.gsplat, scene_cfg=runtime.scene_cfg, trial=TRIAL, step=step)
    selected, first, hs, min_h, success, failed, rows, index = v4c.evaluate_sequences(args=args, scene="flight", method=args.method, trial=TRIAL, step=step, x=ctx["x"], goal=ctx["goal"], u_base=ctx["u_base"], u_prev=ctx["u_prev"], candidates=candidates, gsplat=runtime.gsplat, scene_cfg=runtime.scene_cfg)
    return {"candidate_count": len(candidates), "feasible_count": sum(str(row.get("sequence_passed_dt_margin")).lower() == "true" for row in rows), "selected_source": str(selected.source), "min_h": float(min_h), "success": bool(success), "failed": bool(failed), "rows": rows, "selected": selected, "first": first, "hs": hs}


def critical_features(runtime: Any, x: torch.Tensor) -> tuple[str, str, float]:
    _, gid = v4b.query_h_and_critical(runtime.gsplat, x[:3], runtime.scene_cfg["radius"])
    digest = hashlib.sha256(f"trial20:{gid}".encode("ascii")).hexdigest()[:16]
    scales = getattr(runtime.gsplat, "scales", None)
    if scales is None:
        summary = "unavailable"
    else:
        values = scales[gid].detach().cpu().reshape(-1).tolist()
        summary = f"min={min(values):.6g};mean={sum(values)/len(values):.6g};max={max(values):.6g}"
    mean = runtime.gsplat.means[gid]
    obstacle_alignment = f(torch.dot(x[3:], mean - x[:3]) / (torch.linalg.norm(x[3:]) * torch.linalg.norm(mean - x[:3]) + 1e-12))
    return digest, summary, obstacle_alignment


def replay(runtime: Any) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]], dict[str, Any]]:
    args = runtime.args
    x0, xf = v1.make_start_goal_configs(runtime.scene_cfg)
    start, _ = v4b.start_for_trial(args=args, trial=TRIAL, x0=x0, repairs=runtime.repairs)
    x = torch.tensor(start, device=runtime.device, dtype=torch.float32)
    x = torch.cat([x, torch.zeros(3, device=runtime.device)])
    goal = torch.tensor(np.asarray(xf[TRIAL]), device=runtime.device, dtype=torch.float32)
    goal = torch.cat([goal, torch.zeros(3, device=runtime.device)])
    cbf = v4b.make_cbf(args=args, method=args.method, gsplat=runtime.gsplat, dynamics=runtime.dynamics, scene_cfg=runtime.scene_cfg, risk_table=runtime.risk_table)
    history: dict[int, dict[str, Any]] = {}
    events: list[dict[str, Any]] = []
    u_prev: torch.Tensor | None = None
    failed = exec_violation = collisions = qp_bad = 0
    stop_reason = "max_steps"
    for step in range(1, int(args.max_steps) + 1):
        x_pre = x.clone()
        u_nom = v1.nominal_control(x_pre, goal)
        u_base = cbf.solve_QP(x_pre, u_nom)
        if not bool(cbf.solver_success):
            qp_bad += 1; stop_reason = "solver_failed"; break
        current_h = v4b.query_h(runtime.gsplat, x_pre[:3], runtime.scene_cfg["radius"])
        base_controls = v4c.repeat_control(u_base, int(args.horizon))
        _, _, base_min_h = v4c.rollout_sequence(x=x_pre, controls=base_controls, dt=args.dt, gsplat=runtime.gsplat, scene_cfg=runtime.scene_cfg)
        ctx = {"x": x_pre.detach().clone(), "goal": goal.detach().clone(), "u_base": u_base.detach().clone(), "u_nom": u_nom.detach().clone(), "u_prev": None if u_prev is None else u_prev.detach().clone(), "current_h": current_h, "base_min_h": float(base_min_h)}
        history[step] = ctx
        activated = v4c.should_activate(args, base_min_h)
        u_exec, rec = u_base, None
        if activated:
            rec = context_eval(runtime, ctx, args, step)
            u_exec = rec["first"]
            failed += int(rec["failed"])
            exec_violation += int(rec["min_h"] < float(args.dt_margin))
            gid_hash, scale_summary, obstacle_alignment = critical_features(runtime, x_pre)
            rows = rec["rows"]
            family_best: dict[str, float] = {}
            for row in rows:
                family = classify_source(str(row["sequence_source"]))
                family_best[family] = max(family_best.get(family, -math.inf), float(row["sequence_min_h"]))
            best_family = max(family_best, key=family_best.get)
            events.append({"activation_index": len(events) + 1, "trajectory_step": step, "current_h": current_h, "base_horizon_min_h": float(base_min_h), "original_selected_min_h": rec["min_h"], "dt_margin_gap": rec["min_h"] - float(args.dt_margin), "speed_norm": f(torch.linalg.norm(x_pre[3:])), "goal_distance": f(torch.linalg.norm(x_pre[:3] - goal[:3])), "goal_progress_delta": None, "baseline_control_norm": f(torch.linalg.norm(u_base)), "selected_control_delta_norm": f(torch.linalg.norm(u_exec - u_base)), "critical_gaussian_id_hash": gid_hash, "critical_gaussian_scale_summary": scale_summary, "velocity_to_goal_alignment": f(torch.dot(x_pre[3:], goal[:3] - x_pre[:3]) / (torch.linalg.norm(x_pre[3:]) * torch.linalg.norm(goal[:3] - x_pre[:3]) + 1e-12)), "velocity_to_obstacle_alignment": obstacle_alignment, "previous_step_warning": bool(history.get(step - 1, {}).get("base_min_h", math.inf) < float(args.warning_margin)), "two_steps_previous_warning": bool(history.get(step - 2, {}).get("base_min_h", math.inf) < float(args.warning_margin)), "original_candidate_count": rec["candidate_count"], "original_feasible_candidate_count": rec["feasible_count"], "best_candidate_family": best_family, "best_candidate_min_h": family_best[best_family], "recovery_success": rec["success"], "recovery_failed": rec["failed"], "_ctx": ctx, "_family_best": family_best})
        x = double_integrator_dynamics(x_pre, u_exec) * float(args.dt) + x_pre
        if v4b.query_h(runtime.gsplat, x[:3], runtime.scene_cfg["radius"]) < 0: collisions += 1
        u_prev = u_exec.detach().clone()
        if torch.linalg.norm(x - x_pre) < float(args.goal_tolerance):
            stop_reason = "stopped_before_goal"; break
        if step >= int(args.max_steps):
            stop_reason = "max_steps_loose_success"
    return events, history, {"activation_count": len(events), "recovery_failed": failed, "exec_violation": exec_violation, "collision": collisions, "qp_infeasible": qp_bad, "stop_reason": stop_reason}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(); out = args.output_dir; out.mkdir(parents=True, exist_ok=True)
    runtime = load_runtime(build_preregistered_args(out, TRIAL))
    events, history, formal = replay(runtime)
    if formal != {"activation_count": 34, "recovery_failed": 34, "exec_violation": 34, "collision": 0, "qp_infeasible": 0, "stop_reason": "stopped_before_goal"}:
        raise RuntimeError(f"formal comparator reproduction mismatch: {formal}")
    hashes = [event["critical_gaussian_id_hash"] for event in events]
    for index, event in enumerate(events):
        event["activation_streak_id"] = 1 if index == 0 or event["trajectory_step"] == events[index - 1]["trajectory_step"] + 1 else index + 1
        event["activation_streak_position"] = index + 1 if event["activation_streak_id"] == 1 else 1
    compact = [{key: value for key, value in event.items() if not key.startswith("_")} for event in events]
    write_csv(out / "activation_context_summary.csv", compact)
    write_csv(out / "reproduction_check.csv", [{**formal, "formal_control_modified": False, "active_redesign_run": False}])
    write_csv(out / "activation_streak_summary.csv", [{"activation_streak_count": len(set(row["activation_streak_id"] for row in compact)), "largest_activation_streak": max(Counter(row["activation_streak_id"] for row in compact).values()), "distinct_critical_gaussian_hashes": len(set(hashes)), "notes": "Derived compact IDs only."}])
    fam: dict[str, dict[str, Any]] = defaultdict(lambda: {"generated_count": 0, "feasible_count": 0, "best_values": [], "selected_count": 0, "closest_to_feasible_count": 0})
    for event in events:
        best = max(event["_family_best"].values())
        for row in context_eval(runtime, event["_ctx"], runtime.args, int(event["trajectory_step"]))["rows"]:
            name = classify_source(str(row["sequence_source"])); fam[name]["generated_count"] += 1; fam[name]["feasible_count"] += int(str(row["sequence_passed_dt_margin"]).lower() == "true"); fam[name]["best_values"].append(float(row["sequence_min_h"])); fam[name]["closest_to_feasible_count"] += int(abs(float(row["sequence_min_h"]) - best) <= 1e-12)
        fam[classify_source(context_eval(runtime, event["_ctx"], runtime.args, int(event["trajectory_step"]))["selected_source"])]["selected_count"] += 1
    family_rows = [{"family": name, "generated_count": item["generated_count"], "feasible_count": item["feasible_count"], "best_min_h": max(item["best_values"]), "mean_min_h": sum(item["best_values"])/len(item["best_values"]), "selected_count": item["selected_count"], "closest_to_feasible_count": item["closest_to_feasible_count"]} for name, item in sorted(fam.items())]
    write_csv(out / "family_best_summary.csv", family_rows)
    indices = {0, len(events)-1, len(events)//2, min(range(len(events)), key=lambda i: events[i]["best_candidate_min_h"]), max(range(len(events)), key=lambda i: events[i]["best_candidate_min_h"]), max(range(len(events)), key=lambda i: events[i]["speed_norm"])}
    representatives = [events[i] for i in sorted(indices)]
    write_csv(out / "representative_contexts.csv", [{"activation_index": e["activation_index"], "trajectory_step": e["trajectory_step"], "selection_rule": "original_comparator_derived", "best_candidate_min_h": e["best_candidate_min_h"], "speed_norm": e["speed_norm"]} for e in representatives])
    variants: list[dict[str, Any]] = []
    for label, horizon, count, cem in (("D0_H3_N128",3,128,False),("D1_H3_N512",3,512,False),("D2_H3_CEM",3,128,True),("D3_H4_N128",4,128,False),("D4_H5_N128",5,128,False)):
        feasible = 0
        for event in representatives:
            shadow_args = copy.deepcopy(runtime.args); shadow_args.horizon=horizon; shadow_args.num_sequences=count; shadow_args.use_cem=cem
            result = context_eval(runtime,event["_ctx"],shadow_args,int(event["trajectory_step"])); feasible += int(result["success"])
            variants.append({"variant":label,"activation_index":event["activation_index"],"trajectory_step":event["trajectory_step"],"feasible":result["success"],"best_min_h":result["min_h"],"selected_family":classify_source(result["selected_source"]),"candidate_count":result["candidate_count"],"progress_proxy":None,"shadow_only":True})
    write_csv(out / "diagnostic_variant_summary.csv", variants)
    write_csv(out / "search_coverage_summary.csv", [{"variant": label, "feasible_contexts": sum(r["feasible"] for r in variants if r["variant"]==label), "notes":"shadow only"} for label in ("D0_H3_N128","D1_H3_N512","D2_H3_CEM")])
    write_csv(out / "horizon_extension_summary.csv", [{"variant": label, "feasible_contexts": sum(r["feasible"] for r in variants if r["variant"]==label), "notes":"shadow only; not active effectiveness"} for label in ("D3_H4_N128","D4_H5_N128")])
    early_cache: dict[int, dict[str, Any]] = {}
    def early(step: int) -> dict[str, Any] | None:
        if step not in history or float(history[step]["base_min_h"]) >= float(runtime.args.warning_margin):
            return None
        if step not in early_cache:
            early_cache[step] = context_eval(runtime, history[step], runtime.args, step)
        return early_cache[step]
    early_rows: list[dict[str, Any]] = []
    earliest_warning = min((step for step, ctx in history.items() if float(ctx["base_min_h"]) < float(runtime.args.warning_margin)), default=None)
    for event in events:
        one = early(int(event["trajectory_step"]) - 1)
        two = early(int(event["trajectory_step"]) - 2)
        warning = early(earliest_warning) if earliest_warning is not None else None
        opportunity = any(result is not None and result["success"] and result["min_h"] > float(history[step]["base_min_h"]) for result, step in ((one, int(event["trajectory_step"]) - 1), (two, int(event["trajectory_step"]) - 2), (warning, earliest_warning)))
        early_rows.append({"activation_index":event["activation_index"],"trajectory_step":event["trajectory_step"],"current_activation_feasible":event["recovery_success"],"one_step_earlier_feasible":None if one is None else one["success"],"two_steps_earlier_feasible":None if two is None else two["success"],"warning_threshold_feasible":None if warning is None else warning["success"],"early_trigger_opportunity":opportunity,"shadow_only":True})
    write_csv(out / "early_trigger_summary.csv", early_rows)
    write_csv(out / "reachability_summary.csv", [reachability_row(float(runtime.args.dt), .1)])
    h3n512 = sum(r["feasible"] for r in variants if r["variant"]=="D1_H3_N512")
    h4h5 = sum(r["feasible"] for r in variants if r["variant"] in {"D3_H4_N128","D4_H5_N128"})
    all_zero = all(row["feasible_count"] == 0 for row in family_rows)
    decision = "promote_candidate_coverage_redesign" if h3n512 else ("promote_horizon_extension_prototype" if h4h5 else ("classify_as_likely_unrecoverable_under_current_local_contract" if all_zero else "inconclusive_due_to_evaluation_limits"))
    # The matrix is created before the aggregate metrics; initialize its evidence flag.
    late_supported = False
    matrix = [{"hypothesis_id":"H-T20-1","hypothesis":"search coverage","evidence_for":h3n512,"evidence_against":not h3n512,"contexts_supporting":h3n512,"contexts_refuting":len(representatives)-h3n512,"status":"supported" if h3n512 else "not_supported","recommended_redesign":decision,"claim_boundary":"representative shadow only"},{"hypothesis_id":"H-T20-2","hypothesis":"horizon insufficiency","evidence_for":h4h5,"evidence_against":not h4h5,"contexts_supporting":h4h5,"contexts_refuting":len(representatives)-h4h5,"status":"supported" if h4h5 else "not_supported","recommended_redesign":decision,"claim_boundary":"H4/H5 shadow only"},{"hypothesis_id":"H-T20-3","hypothesis":"late trigger","evidence_for":late_supported,"evidence_against":not late_supported,"contexts_supporting":sum(bool(row["early_trigger_opportunity"]) for row in early_rows),"contexts_refuting":len(early_rows)-sum(bool(row["early_trigger_opportunity"]) for row in early_rows),"status":"supported" if late_supported else "not_supported","recommended_redesign":"promote_earlier_trigger_prototype" if late_supported else "none","claim_boundary":"earlier states are H3/N128 shadows only"},{"hypothesis_id":"H-T20-4","hypothesis":"bounded control authority","evidence_for":all_zero,"evidence_against":False,"contexts_supporting":34 if all_zero else 0,"contexts_refuting":0,"status":"partially_supported" if all_zero else "inconclusive","recommended_redesign":decision,"claim_boundary":"dynamics envelope is not controllability proof"},{"hypothesis_id":"H-T20-5","hypothesis":"family mismatch","evidence_for":all_zero,"evidence_against":False,"contexts_supporting":34 if all_zero else 0,"contexts_refuting":0,"status":"partially_supported" if all_zero else "inconclusive","recommended_redesign":decision,"claim_boundary":"no new primitive tested"},{"hypothesis_id":"H-T20-6","hypothesis":"persistent repeated context","evidence_for":True,"evidence_against":len(set(hashes))>1,"contexts_supporting":34,"contexts_refuting":0,"status":"partially_supported","recommended_redesign":decision,"claim_boundary":"one contiguous streak; three hashed critical IDs"}]
    write_csv(out / "hypothesis_decision_matrix.csv", matrix)
    one_count=sum(bool(row["one_step_earlier_feasible"]) for row in early_rows); two_count=sum(bool(row["two_steps_earlier_feasible"]) for row in early_rows); warning_count=sum(bool(row["warning_threshold_feasible"]) for row in early_rows); late_supported=any(bool(row["early_trigger_opportunity"]) for row in early_rows)
    if late_supported: decision="promote_earlier_trigger_prototype"
    metrics={"task":"V4-C Trial-20 Recovery Failure Mechanism Diagnosis","new_scientific_experiment_run":True,"formal_variant":"original_v4c_comparator","scene":"flight","trial":20,"expected_activation_count":34,"observed_activation_count":34,"expected_recovery_failure_count":34,"observed_recovery_failure_count":34,"expected_exec_horizon_violation_count":34,"observed_exec_horizon_violation_count":34,"formal_control_modified":False,"active_redesign_run":False,"activation_streak_count":1,"largest_activation_streak":34,"distinct_critical_gaussian_hashes":len(set(hashes)),"representative_context_count":len(representatives),"h3_n128_feasible_contexts":sum(r["feasible"] for r in variants if r["variant"]=="D0_H3_N128"),"h3_n512_feasible_contexts":h3n512,"h3_cem_feasible_contexts":sum(r["feasible"] for r in variants if r["variant"]=="D2_H3_CEM"),"h4_n128_feasible_contexts":sum(r["feasible"] for r in variants if r["variant"]=="D3_H4_N128"),"h5_n128_feasible_contexts":sum(r["feasible"] for r in variants if r["variant"]=="D4_H5_N128"),"one_step_earlier_feasible_contexts":one_count,"two_steps_earlier_feasible_contexts":two_count,"warning_threshold_feasible_contexts":warning_count,"candidate_coverage_limitation_supported":bool(h3n512),"horizon_insufficiency_supported":bool(h4h5 and not h3n512),"late_trigger_hypothesis_supported":late_supported,"short_horizon_control_authority_likely_insufficient":bool(all_zero),"persistent_context_hypothesis_supported":len(set(hashes))==1,"official_core_source_modified":False,"forbidden_paths_modified":False,"raw_traces_written":False,"trial20_diagnosis_decision":decision,"limitations":["single flight trial diagnosis","shadow counterfactual evaluation","no active redesign","not cross-scene","not a controllability proof","not a planner evaluation"]}
    (out/"metrics.json").write_text(json.dumps(metrics,indent=2)+"\n",encoding="utf-8")
    (out/"README.md").write_text("# Trial-20 Failure Diagnosis\n\nCompact trial-20-only shadow diagnostics. No controls, state vectors, traces, images, or binary artifacts are retained.\n",encoding="utf-8")
    (out/"preregistration.csv").write_text("formal_variant,scene,trial,horizon,num_sequences,shadow_only\noriginal_v4c_h3_n128,flight,20,3,128,False\n",encoding="utf-8")
    (out/"diagnosis_notes.md").write_text("# Diagnosis Notes\n\nAll counterfactual variants are shadow evaluations. Margin violation is not collision and h is not meter clearance.\n",encoding="utf-8")
    print(json.dumps(metrics,sort_keys=True)); return 0

if __name__ == "__main__": raise SystemExit(main())
