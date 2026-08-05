#!/usr/bin/env python3
"""Plant-free stage-reachability predicates using the exact PR #80 methods."""
from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import numpy as np

from task_config_v2 import PR80_ROOT

if str(PR80_ROOT) not in sys.path: sys.path.insert(0, str(PR80_ROOT))
from eth3d_controller_core import nominal_control  # type: ignore  # noqa: E402
from fas_cbf_modules import (DT_MARGIN, feasibility_aware_rows, project_start_safe,  # type: ignore  # noqa: E402
    solve_bounded_qp, verify_discrete_step)
from run_formal_paired_controller_benchmark import predictive_recovery  # type: ignore  # noqa: E402

RUNTIME_DT_SAMPLES = 5

def normalized(value: np.ndarray) -> np.ndarray:
    value=np.asarray(value,dtype=np.float64); norm=float(np.linalg.norm(value))
    return value/norm if norm>1e-12 else np.asarray([1.0,0.0,0.0])

def directional_rank(grad: np.ndarray, h: np.ndarray) -> int:
    active=np.asarray(grad)[np.asarray(h)<=0.02]
    if not len(active): return 0
    unit=active/np.maximum(np.linalg.norm(active,axis=1,keepdims=True),1e-12)
    return int(np.sum(np.linalg.svd(unit,compute_uv=False)>1e-3))

class ShadowEvaluator:
    """Evaluates S0-S4 without integrating the plant or reading formal results."""
    def __init__(self, learned: Any) -> None:
        self.learned=learned; self.scalar_cache: dict[bytes,float]={}; self.shadow_probe_count=0
        self.last_position_key: bytes|None=None; self.last_position_stage: dict[str,Any]|None=None

    def min_h(self, point: np.ndarray) -> float:
        key=np.asarray(point,dtype=np.float64).tobytes()
        if key not in self.scalar_cache: self.scalar_cache[key]=float(self.learned.min_h(point))
        return self.scalar_cache[key]

    def evaluate(self, candidate_id: str, position: np.ndarray, velocity: np.ndarray,
                 goal: np.ndarray, reference_clearance_lower_bound_m: float,
                 generation_source: str, source_tags: list[str], source_node_id: int|None,
                 stop_after_s3: bool=False) -> dict:
        self.shadow_probe_count+=1
        p=np.asarray(position,dtype=np.float64); v=np.asarray(velocity,dtype=np.float64); goal=np.asarray(goal,dtype=np.float64)
        record={"candidate_id":candidate_id,"p":p.tolist(),"v":v.tolist(),"goal":goal.tolist(),
                "generation_source":generation_source,"source_tags":source_tags,
                "source_node_id":source_node_id,"reference_clearance_lower_bound_m":float(reference_clearance_lower_bound_m),
                "reference_valid":bool(reference_clearance_lower_bound_m>0.0),"reference_used_for_controller_decision":False,
                "formal_rollout_metric_read_count":0,"reason_codes":[]}
        if reference_clearance_lower_bound_m<=0:
            record["reason_codes"].append("REFERENCE_INVALID"); return record
        pkey=p.tobytes()
        if self.last_position_key!=pkey:
            query0=self.learned.query(p)
            if bool(np.all(query0["finite"])):
                projected=project_start_safe(p,self.learned.query)
                entry=np.asarray(projected["position"],dtype=np.float64) if projected["accepted"] else None
                entry_query=self.learned.query(entry) if entry is not None else None
            else:
                projected=None; entry=None; entry_query=None
            self.last_position_key=pkey; self.last_position_stage={"query0":query0,"projected":projected,"entry":entry,"query":entry_query}
        cached=self.last_position_stage; assert cached is not None
        query0=cached["query0"]
        if not bool(np.all(query0["finite"])):
            record["reason_codes"].append("MAP_QUERY_INVALID"); return record
        min_h0=float(np.min(query0["h"])); record["S0"]={"passed":True,"map_query_finite":True,"min_h":min_h0,
            "unknown_contract_recorded":True,"candidate_population":int(len(query0["h"]))}
        projected=cached["projected"]; assert projected is not None
        attempted=projected["classification"]!="SAFE"; accepted=bool(projected["accepted"])
        disp=float(projected["displacement_m"]); projected_ref_lb=reference_clearance_lower_bound_m-disp
        reason=("START_SAFE_NOT_TRIGGERED" if not attempted else "START_SAFE_PROJECTABLE" if accepted else "START_SAFE_UNPROJECTABLE")
        record["reason_codes"].append(reason)
        record["S1"]={"passed":accepted,"classification":projected["classification"],"projection_attempted":attempted,
            "projection_success":accepted,"projected_displacement_m":disp,"projected_full_map_verification":bool(accepted and projected["final_min_h"]>=DT_MARGIN),
            "initial_min_h":float(projected["initial_min_h"]),"projected_min_h":float(projected["final_min_h"]),
            "projected_reference_clearance_lower_bound_m":float(projected_ref_lb),"projected_reference_free":bool(projected_ref_lb>0)}
        if not accepted or projected_ref_lb<=0: return record
        entry=np.asarray(cached["entry"],dtype=np.float64); query=cached["query"]
        a1,b1=self.learned.cbf_rows(query,v); u_des=nominal_control(entry,v,goal); qp1=solve_bounded_qp(a1,b1,u_des,v)
        a2,b2,ids2,reduction=feasibility_aware_rows(a1,b1,query["h"],query["candidate_ids"])
        qp2=solve_bounded_qp(a2,b2,u_des,v)
        dominance=bool(reduction["output_constraint_count"]<reduction["input_constraint_count"])
        record["S2"]={"passed":qp2.control is not None,"m1_qp_status":qp1.status,"m1_qp_feasible":qp1.control is not None,
            "m2_qp_status":qp2.status,"m2_qp_feasible":qp2.control is not None,"candidate_population":int(len(query["h"])),
            "forced_candidates":int(reduction["forced_candidate_count"]),"original_constraint_population":int(reduction["input_constraint_count"]),
            "reduced_constraint_population":int(reduction["output_constraint_count"]),"provably_redundant_count":int(reduction["provably_redundant_count"]),
            "dominance_removal_ratio":float(reduction["provably_redundant_count"]/max(1,reduction["input_constraint_count"])),
            "multi_direction_constraint_rank":directional_rank(query["grad"],query["h"]),"H2_DOMINANCE_ACTIVE":dominance,
            "feasible_control_set_parity":bool(reduction["hidden_relaxation_count"]==0 and reduction["same_control_bounds"]),
            "hidden_relaxation_count":int(reduction["hidden_relaxation_count"]),"entry_position":entry.tolist(),"u_des":u_des.tolist(),
            "m2_control":None if qp2.control is None else qp2.control.tolist()}
        record["reason_codes"].append("H2_DOMINANCE_ACTIVE" if dominance else "H2_DOMINANCE_INACTIVE")
        if qp1.control is None or qp2.control is None:
            record["reason_codes"].append("QP_INFEASIBLE_BEFORE_H2"); return record
        control=np.asarray(qp2.control,dtype=np.float64); verifier=verify_discrete_step(entry,v,control,self.min_h,samples=RUNTIME_DT_SAMPLES)
        endpoint_h=float(verifier["endpoint_h"]); segment_h=float(verifier["segment_h"]); triggered=not bool(verifier["passed"])
        trigger_type=("NONE" if not triggered else "ENDPOINT_UNSAFE" if endpoint_h<0 else
                      "ENDPOINT_SAFE_SEGMENT_UNSAFE" if endpoint_h>=DT_MARGIN and segment_h<DT_MARGIN else
                      "MARGIN_VIOLATION_NO_COLLISION" if segment_h>=0 else "SEGMENT_UNSAFE")
        unavoidable_severe=bool(triggered and segment_h<0)
        record["S3"]={"passed":bool(verifier["passed"]),"current_h":float(np.min(query["h"])),"endpoint_h":endpoint_h,
            "segment_h":segment_h,"verifier_trigger":triggered,"endpoint_only_miss":bool(verifier["endpoint_only_miss"]),
            "trigger_type":trigger_type,"unavoidable_immediate_segment":unavoidable_severe,
            "immediate_position_segment_control_invariant_under_frozen_forward_euler":True,
            "control_finite":bool(np.isfinite(control).all()),"control_bounded":bool(np.max(np.abs(control))<=0.1+1e-10)}
        record["reason_codes"].append("IMMEDIATE_DT_TRIGGERED" if triggered else "IMMEDIATE_DT_SAFE")
        if unavoidable_severe: record["reason_codes"].append("UNAVOIDABLE_IMMEDIATE_SEGMENT")
        if triggered:
            record["S4"]={"eligible":False,"recovery_trigger":False,"reason":"IMMEDIATE_VERIFIER_DID_NOT_PASS"}; return record
        if stop_after_s3:
            record["S4"]={"eligible":False,"recovery_trigger":False,"reason":"TARGETED_G3_SEARCH_STOP_AFTER_S3"}; return record
        predicted_p=entry.copy(); predicted_v=v.copy(); predicted_min=float(np.min(query["h"])); predicted=[]
        from fas_cbf_modules import integrate  # type: ignore
        for _ in range(3):
            predicted_p,predicted_v=integrate(predicted_p,predicted_v,control); value=self.min_h(predicted_p)
            predicted.append(value); predicted_min=min(predicted_min,value)
        recovery_trigger=predicted_min<DT_MARGIN
        if recovery_trigger:
            recovery=predictive_recovery(self.learned,entry,v,goal,a2,b2,u_des,float(np.min(query["h"])),[])
            recoverable=bool(recovery["success"])
            reason4="H3_RECOVERY_TRIGGERED_RECOVERABLE" if recoverable else "H3_RECOVERY_TRIGGERED_UNRECOVERABLE"
        else:
            recovery={"success":False,"minimum_h":None,"candidate_count":0}; recoverable=False; reason4="H3_RECOVERY_NOT_TRIGGERED"
        record["reason_codes"].append(reason4)
        record["S4"]={"eligible":True,"immediate_verifier_passed":True,"predicted_h":predicted,"predicted_min_h":float(predicted_min),
            "recovery_trigger":recovery_trigger,"recovery_recoverable":recoverable,"candidate_library_count":int(recovery.get("candidate_count",0)),
            "recovery_candidate_success":bool(recovery.get("success")),"recovery_minimum_h":recovery.get("minimum_h")}
        return record

def main() -> int:
    print("PASS_SHADOW_STAGE_REACHABILITY_MODULE_IMPORT")
    return 0

if __name__=="__main__": raise SystemExit(main())
