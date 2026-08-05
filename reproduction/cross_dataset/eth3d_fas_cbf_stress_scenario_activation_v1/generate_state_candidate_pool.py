#!/usr/bin/env python3
"""Deterministically search plant-free candidate states and freeze compact stage pools."""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from task_config_v2 import *  # noqa: F403
from build_shadow_stage_reachability import ShadowEvaluator, normalized

if str(PR80_ROOT) not in sys.path: sys.path.insert(0,str(PR80_ROOT))
from eth3d_controller_core import LearnedEllipsoidMap  # type: ignore  # noqa: E402
from fas_cbf_modules import project_start_safe  # type: ignore  # noqa: E402

def orthogonal(direction: np.ndarray) -> tuple[np.ndarray,np.ndarray]:
    d=normalized(direction); axis=np.asarray([1.,0.,0.]) if abs(d[0])<0.8 else np.asarray([0.,1.,0.])
    t1=normalized(np.cross(d,axis)); return t1,normalized(np.cross(d,t1))

def compact(record: dict) -> dict:
    return record

def qualified_counts(pools: dict[str,list[dict]]) -> dict:
    return {key:len(value) for key,value in pools.items()}

def enough(pools: dict[str,list[dict]]) -> bool:
    return (len(pools["G0"])>=28 and len(pools["G1_PROJECTABLE"])>=16 and len(pools["G1_NEAR"])>=6 and
            len(pools["G1_UNPROJECTABLE"])>=6 and len(pools["G2"])>=30 and
            len(pools["G3_MARGIN"])>=16 and len(pools["G3_ENDPOINT_UNSAFE"])>=1 and
            len(pools["G3_ENDPOINT_ONLY"])>=1 and len(pools["G4_RECOVERABLE"])>=18 and len(pools["G4_UNRECOVERABLE"])>=8)

def only_g3_strata_missing(pools: dict[str,list[dict]]) -> bool:
    return (len(pools["G0"])>=28 and len(pools["G1_PROJECTABLE"])>=16 and len(pools["G1_NEAR"])>=6 and
            len(pools["G1_UNPROJECTABLE"])>=6 and len(pools["G2"])>=30 and len(pools["G3_MARGIN"])>=16 and
            len(pools["G4_RECOVERABLE"])>=18 and len(pools["G4_UNRECOVERABLE"])>=8 and
            (len(pools["G3_ENDPOINT_UNSAFE"])<1 or len(pools["G3_ENDPOINT_ONLY"])<1))

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--output-root",type=Path,default=TASK_ROOT); args=parser.parse_args()
    if __import__("os").environ.get("CUDA_VISIBLE_DEVICES")!="1": raise RuntimeError("physical GPU 1 pin required")
    args.output_root.mkdir(parents=True,exist_ok=True)
    graph=json.loads(PRM_GRAPH.read_text()); nodes={int(r["id"]):r for r in graph["nodes"]}
    diagnostics=json.loads((PR80_ROOT/"scenario_generation/scenario_static_diagnostics.json").read_text())
    v1=json.loads(V1_REGISTRY.read_text()); v1_by_node={int(r["source_node_id"]):r for r in v1["scenarios"]}
    learned=LearnedEllipsoidMap(CANONICAL_ROOT,SOURCE_ROOT,CONTROLLER_SNAPSHOT)
    evaluator=ShadowEvaluator(learned); pools=defaultdict(list); seen_state=set(); position_count=0
    ordered=sorted(diagnostics,key=lambda r:(abs(float(r["min_map_h"])), -int(r["near_active_count"]), int(r["node_id"])))
    for diag in ordered:
        node_id=int(diag["node_id"]); base=np.asarray(diag["point_m"],dtype=np.float64); ref=float(diag["reference_clearance_m"])
        toward=normalized(np.asarray(diag["nearest_obstacle_direction"],dtype=np.float64)); t1,t2=orthogonal(toward)
        h0=float(diag["min_map_h"])
        offsets=[0.0]
        for target in (-0.05,-0.015,-0.005,-0.001,0.0001,0.0002,0.0005,0.00055,0.0008,0.0012,0.0015,0.002,0.003,0.006,0.012): offsets.append(h0-target)
        offsets.extend([-0.05,-0.025,0.025,0.05])
        position_specs=[]
        for ordinal,delta in enumerate(sorted(set(round(float(x),9) for x in offsets))):
            if abs(delta)>min(0.20,ref-0.25): continue
            source="A_PR79_QUALIFIED_NODE" if delta==0 else "C_CRITICAL_GAUSSIAN_OFFSET"
            position_specs.append((source,ordinal,base+delta*toward,ref-abs(delta),["A_PR80_OR_PR79" if node_id in v1_by_node else "A_PR79_512_NODES"]))
        for target_index,target in enumerate((0.0002,0.0005,0.0008,0.0012,0.002)):
            delta=h0-target
            if abs(delta)>min(0.20,ref-0.25): continue
            radial=base+delta*toward
            for tangent_index,tangent_offset in enumerate((-0.005,-0.0025,0.0025,0.005)):
                position_specs.append(("D_GAUSSIAN_BARRIER_EQUIVALUE_CHORD",target_index*4+tangent_index,
                    radial+tangent_offset*t1,ref-abs(delta)-abs(tangent_offset),["D_BARRIER_EQUIVALUE_BAND","D_TANGENTIAL_CHORD_OFFSET"]))
        if node_id%8==0:
            # Reference-surface direction from the graph's conservative node clearance; no controller use.
            reference_direction=normalized(np.asarray([0.0,0.0,-1.0]))
            for ordinal,delta in enumerate((0.05,0.10)):
                position_specs.append(("B_REFERENCE_SURFACE_OFFSET",ordinal,base+delta*reference_direction,ref-delta,["B_REFERENCE_DIRECTION"]))
        if int(diag["near_active_count"])>=50:
            position_specs.append(("F_HIGH_CONSTRAINT_DENSITY",0,base,ref,["F_HIGH_CONSTRAINT_DENSITY"]))
        preferred_targets=(0.006,0.0002,-0.001,-0.015,-0.05)
        def position_priority(spec):
            source,ordinal,point,_,_=spec
            if source=="C_CRITICAL_GAUSSIAN_OFFSET":
                estimated_h=h0-float((np.asarray(point)-base)@toward)
                distances=[abs(estimated_h-target) for target in preferred_targets]
                best=int(np.argmin(distances))
                if distances[best]<1e-7: return (best,ordinal)
                return (6,abs(estimated_h),ordinal)
            if source=="D_GAUSSIAN_BARRIER_EQUIVALUE_CHORD": return (5,ordinal)
            return (6,ordinal)
        position_specs.sort(key=position_priority)
        for source,pos_ord,p,ref_lb,tags in position_specs:
            position_count+=1
            base_query=learned.query(p)
            if not bool(np.all(base_query["finite"])): continue
            min_h=float(np.min(base_query["h"])); local_toward=normalized(-base_query["grad"][int(np.argmin(base_query["h"]))]); lt1,lt2=orthogonal(local_toward)
            tags=list(tags)
            if -0.002<=min_h<=0.012: tags.append("D_GAUSSIAN_BARRIER_EQUIVALUE_BAND")
            if min_h<0.005 and ref_lb>0.20: tags.append("E_REFERENCE_SAFE_MAP_UNSAFE_OR_NEAR")
            if int(np.sum(base_query["h"]<=0.02))>=50: tags.append("F_LOCAL_HIGH_CONSTRAINT_DENSITY")
            specs=[]
            # One zero-velocity tangent-goal state probes G0/G2.
            specs.append((np.zeros(3),lt1,0.12,"ZERO_VELOCITY","BARRIER_TANGENT_GOAL"))
            velocity_directions=[(local_toward,"TOWARD_CRITICAL_GAUSSIAN"),(lt1,"BARRIER_TANGENT_1"),(lt2,"BARRIER_TANGENT_2"),
                (t1,"SOURCE_NODE_CHORD_AXIS_POSITIVE"),(-t1,"SOURCE_NODE_CHORD_AXIS_NEGATIVE"),(t2,"SOURCE_NODE_CHORD_NORMAL_POSITIVE"),(-t2,"SOURCE_NODE_CHORD_NORMAL_NEGATIVE"),
                (normalized(local_toward+0.25*lt1),"SHALLOW_DIAGONAL_TOWARD_BARRIER_1"),(normalized(local_toward-0.25*lt1),"SHALLOW_DIAGONAL_TOWARD_BARRIER_2"),
                (normalized(local_toward+0.50*lt1),"DIAGONAL_TOWARD_BARRIER_1"),(normalized(local_toward-0.50*lt1),"DIAGONAL_TOWARD_BARRIER_2"),
                (normalized(local_toward+0.50*lt2),"DIAGONAL_TOWARD_BARRIER_3"),(normalized(local_toward-0.50*lt2),"DIAGONAL_TOWARD_BARRIER_4")]
            for axis in range(3):
                for sign in (-1.,1.):
                    d=np.zeros(3);d[axis]=sign;velocity_directions.append((d,f"FROZEN_AXIS_{axis}_{int(sign)}"))
            targeted_g3=only_g3_strata_missing(pools) and len(pools["G3_ENDPOINT_ONLY"])>=1
            if targeted_g3:
                # Once every non-G3 quota and the segment-chord stratum are frozen in
                # the growing pool, spend the remaining bounded tuple budget on wider
                # position coverage. The endpoint is independent of control under the
                # frozen forward-Euler integrator, so the most adverse admissible
                # velocity directions are the original and post-projection critical-
                # Gaussian normals. This is an enumeration optimization only.
                projected=project_start_safe(p,learned.query)
                projected_toward=local_toward
                if projected.get("accepted"):
                    entry=np.asarray(projected["position"],dtype=np.float64);entry_query=learned.query(entry)
                    projected_toward=normalized(-entry_query["grad"][int(np.argmin(entry_query["h"]))])
                    evaluator.last_position_key=p.tobytes()
                    evaluator.last_position_stage={"query0":base_query,"projected":projected,"entry":entry,"query":entry_query}
                velocity_directions=[(projected_toward,"TOWARD_POST_PROJECTION_CRITICAL_GAUSSIAN"),(local_toward,"TOWARD_CRITICAL_GAUSSIAN")]
            goal_options=((local_toward,"CROSS_LOCAL_BARRIER"),(lt1,"BARRIER_TANGENT_GOAL"),(-local_toward,"REFERENCE_FREE_SHORT_GOAL"))
            for mag_index,mag in enumerate((0.01,0.02,0.03,0.04,0.05,0.06,0.07,0.08,0.09,0.10)):
                for direction_index,(vdir,vlabel) in enumerate(velocity_directions):
                    active_goals=goal_options
                    if only_g3_strata_missing(pools):
                        active_goals=(goal_options[(node_id+mag_index+direction_index)%len(goal_options)],)
                    for gdir,glabel in active_goals:
                        specs.append((mag*vdir,gdir,0.12,vlabel,glabel))
            for spec_ord,(v,gdir,goal_dist,vlabel,glabel) in enumerate(specs):
                if evaluator.shadow_probe_count>=CANDIDATE_STATE_LIMIT: break
                goal=p+goal_dist*normalized(gdir); goal_ref_lb=ref_lb-goal_dist
                if goal_ref_lb<=0: continue
                key=np.round(np.concatenate((p,v,goal)),12).tobytes()
                if key in seen_state: continue
                seen_state.add(key); cid=f"C{evaluator.shadow_probe_count:06d}_N{node_id:03d}_P{pos_ord:02d}_S{spec_ord:02d}"
                rec=evaluator.evaluate(cid,p,v,goal,min(ref_lb,goal_ref_lb),source,tags,node_id,
                                       stop_after_s3=only_g3_strata_missing(pools))
                rec["velocity_source"]=vlabel; rec["goal_source"]=glabel
                s1=rec.get("S1",{}); s2=rec.get("S2",{}); s3=rec.get("S3",{}); s4=rec.get("S4",{})
                if s2.get("m1_qp_feasible") and not s1.get("projection_attempted") and not s3.get("verifier_trigger") and not s4.get("recovery_trigger") and rec["reference_clearance_lower_bound_m"]>=0.30: pools["G0"].append(rec)
                if s1.get("projection_attempted") and s1.get("projection_success"):
                    if s1.get("classification")=="NEAR_BOUNDARY": pools["G1_NEAR"].append(rec)
                    elif s1.get("classification")=="MAP_UNSAFE": pools["G1_PROJECTABLE"].append(rec)
                if s1.get("projection_attempted") and not s1.get("projection_success"): pools["G1_UNPROJECTABLE"].append(rec)
                if s2.get("m1_qp_feasible") and s2.get("m2_qp_feasible") and s2.get("H2_DOMINANCE_ACTIVE") and s2.get("feasible_control_set_parity"): pools["G2"].append(rec)
                if s2.get("m2_qp_feasible") and s3.get("current_h",-1)>=0.0005 and s3.get("verifier_trigger"):
                    typ=s3.get("trigger_type")
                    if typ=="ENDPOINT_UNSAFE": pools["G3_ENDPOINT_UNSAFE"].append(rec)
                    elif typ=="ENDPOINT_SAFE_SEGMENT_UNSAFE": pools["G3_ENDPOINT_ONLY"].append(rec)
                    elif typ in {"MARGIN_VIOLATION_NO_COLLISION","SEGMENT_UNSAFE"}: pools["G3_MARGIN"].append(rec)
                if s2.get("m2_qp_feasible") and s3.get("passed") and s4.get("recovery_trigger"):
                    pools["G4_RECOVERABLE" if s4.get("recovery_recoverable") else "G4_UNRECOVERABLE"].append(rec)
                if evaluator.shadow_probe_count % 250 == 0:
                    progress={"candidate_state_count":evaluator.shadow_probe_count,"candidate_position_count":position_count,
                              "qualified_pool_counts":qualified_counts(pools),"formal_rollout_result_read_count":0}
                    atomic_json(args.output_root/"tmp/candidate_search_progress.json",progress)
                    print(json.dumps({"progress":progress},sort_keys=True),flush=True)
                if enough(pools): break
            if evaluator.shadow_probe_count>=CANDIDATE_STATE_LIMIT or enough(pools): break
        if evaluator.shadow_probe_count>=CANDIDATE_STATE_LIMIT or enough(pools): break
    # Keep only qualified compact candidates plus a deterministic diagnostic sample.
    qualified={r["candidate_id"]:r for values in pools.values() for r in values}
    stage_records=[qualified[key] for key in sorted(qualified)]
    atomic_json(args.output_root/"candidate_pool/candidate_pool_qualified.json",stage_records)
    summary={"status":"PASS_CANDIDATE_POOL_SEARCH" if enough(pools) else "CANDIDATE_POOL_EXHAUSTED_WITH_STAGE_DEFICIT",
        "seed":SEED,"candidate_state_limit":CANDIDATE_STATE_LIMIT,"candidate_state_count":evaluator.shadow_probe_count,
        "candidate_position_count":position_count,"shadow_probe_count":evaluator.shadow_probe_count,"qualified_pool_counts":qualified_counts(pools),
        "generation_sources":["A_PR80_100_AND_PR79_512","B_REFERENCE_SURFACE_OFFSETS","C_CRITICAL_GAUSSIAN_OFFSETS","D_BARRIER_EQUIVALUE_BANDS","E_REFERENCE_SAFE_MAP_UNSAFE","F_HIGH_CONSTRAINT_DENSITY"],
        "formal_rollout_result_read_count":0,"plant_execution_count":0,"map_mutation_count":0}
    atomic_json(args.output_root/"candidate_pool/candidate_pool_summary.json",summary)
    flat=[]
    for r in stage_records:
        flat.append({"candidate_id":r["candidate_id"],"generation_source":r["generation_source"],"source_node_id":r["source_node_id"],
          "reference_valid":r["reference_valid"],"s1_class":r.get("S1",{}).get("classification"),"s1_attempted":r.get("S1",{}).get("projection_attempted"),
          "s1_success":r.get("S1",{}).get("projection_success"),"h2_active":r.get("S2",{}).get("H2_DOMINANCE_ACTIVE"),
          "m2_qp_feasible":r.get("S2",{}).get("m2_qp_feasible"),"dt_trigger":r.get("S3",{}).get("verifier_trigger"),
          "dt_type":r.get("S3",{}).get("trigger_type"),"recovery_trigger":r.get("S4",{}).get("recovery_trigger"),
          "recovery_recoverable":r.get("S4",{}).get("recovery_recoverable"),"reason_codes":";".join(r.get("reason_codes",[]))})
    if flat:
        with (args.output_root/"stage_reachability/stage_reachability_table.csv").open("w",encoding="utf-8",newline="") as stream:
            w=csv.DictWriter(stream,fieldnames=list(flat[0])); w.writeheader(); w.writerows(flat)
    print(json.dumps(summary,sort_keys=True)); return 0 if enough(pools) else 2

if __name__=="__main__": raise SystemExit(main())
