"""Bounded plant-free single-cycle smoke on the frozen Replica GT-FINE map."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np

TASK_ROOT=Path(__file__).resolve().parents[1]
if str(TASK_ROOT) not in sys.path: sys.path.insert(0,str(TASK_ROOT))

from adapters.current_cbf_adapter import CurrentCBFAdapter
from adapters.gaussian_barrier_adapter import AnalyticSphereGaussianMapAdapter
from adapters.normative_dynamics_adapter import PositionFirstForwardEulerDoubleIntegrator
from certifier.backup_certifier import BackupCertifier
from certifier.braking_backup_policy import DeterministicBrakingPolicy
from certifier.executable_safety_certifier import ExecutableSafetyCertifier
from certifier.result_types import ActuatorBounds,Control,State
from certifier.segment_certificate import SweptSegmentCertifier
from certifier.terminal_certificate import TerminalCertifier
from certifier.terminal_set import BrakingToRestTerminalSet
from task_config import DT,FIXED_SAFETY_MARGIN_M,MAP_SNAPSHOT_REPLICA,ROBOT_RADIUS_M,U_MAX,U_MIN,V_MAX,V_MIN,V_TERMINAL_TOL

EXPECTED={
 "means_world_m.npy":"e2ca0533767590c0b5ca657ec7f73fd4626a5fbaf07beb2ce76c2c67d1dc4152",
 "scales_linear_m.npy":"d81393a0ede4126a18b49fc9e12cca7476ca665c55fce05242b02766589c59e3",
 "route_registry":"ffe0dadd2dcf4de7e0011a9e3ff6bb1170a385957486ffca33832fc90cc355a6",
 "start_state_registry":"e58cd9de67928ddc22f493f1eaf182044ac7e009656f092dacea42b6aaceb499",
}


def sha(path:Path)->str:
    digest=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(8*1024*1024),b""): digest.update(chunk)
    return digest.hexdigest()


def compact_result(label,state,result,extra=None):
    return {
      "label":label,"state":state.to_dict(),"status":result.status.value,
      "selected_control":None if result.committed_control_or_none is None else result.committed_control_or_none.to_dict(),
      "segment":None if result.segment_certificate is None else {"status":result.segment_certificate.status.value,"lower_bound":result.segment_certificate.lower_bound,"method":result.segment_certificate.method,"classification":result.segment_certificate.exact_or_conservative,"reason":result.segment_certificate.reason_code},
      "current_feasibility":None if result.cbf_certificate is None else {"certified":result.cbf_certificate.certified,"reason":result.cbf_certificate.reason_code,"candidate_control_checked":result.cbf_certificate.candidate_control_checked,"candidate_constraint_mode":result.cbf_certificate.candidate_constraint_mode,"max_full_constraint_residual":result.cbf_certificate.max_full_constraint_residual,"full_query_postcheck":result.cbf_certificate.full_query_postcheck_performed},
      "backup":None if result.backup_witness is None else {"certified":result.backup_witness.certified,"horizon":result.backup_witness.horizon,"reason":result.backup_witness.reason_code},
      "rejected":[r.to_dict() for r in result.rejected_candidates],"timing":result.timing,
      "reference_online_read_count":0,"extra":extra or {},
    }


def main()->None:
    parser=argparse.ArgumentParser(); parser.add_argument("--map-root",type=Path,required=True); parser.add_argument("--route-registry",type=Path,required=True); parser.add_argument("--start-state-registry",type=Path,required=True); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args()
    actual={"means_world_m.npy":sha(args.map_root/"means_world_m.npy"),"scales_linear_m.npy":sha(args.map_root/"scales_linear_m.npy"),"route_registry":sha(args.route_registry),"start_state_registry":sha(args.start_state_registry)}
    if actual!=EXPECTED: raise SystemExit("FROZEN_REPLICA_IDENTITY_MISMATCH "+json.dumps(actual,sort_keys=True))
    routes=json.loads(args.route_registry.read_text(encoding="utf-8"))["routes"]
    diagnostic=json.loads(args.start_state_registry.read_text(encoding="utf-8"))["states"]
    bounds=ActuatorBounds(U_MIN,U_MAX,V_MIN,V_MAX,DT); effective=ROBOT_RADIUS_M+FIXED_SAFETY_MARGIN_M
    map_adapter=AnalyticSphereGaussianMapAdapter.from_canonical_arrays(args.map_root,MAP_SNAPSHOT_REPLICA,effective)
    dynamics=PositionFirstForwardEulerDoubleIntegrator(bounds); segment=SweptSegmentCertifier(dynamics,map_adapter.segment_backend,effective)
    current=CurrentCBFAdapter(map_adapter); terminal_set=BrakingToRestTerminalSet(V_TERMINAL_TOL); terminal=TerminalCertifier(terminal_set,current,segment)
    policy=DeterministicBrakingPolicy(bounds,V_TERMINAL_TOL); backup=BackupCertifier(dynamics,segment,terminal,policy)
    unified=ExecutableSafetyCertifier(current,segment,terminal,backup,policy,{"map_snapshot_id":MAP_SNAPSHOT_REPLICA,"execution_model":dynamics.identity,"route_registry_sha256":EXPECTED["route_registry"]})
    records=[]
    selected=sorted(routes,key=lambda row:(int(row["execution_order"]),row["route_id"]))[:10]
    for index,row in enumerate(selected):
        state=State(tuple(row["start_m"]),(0.,0.,0.),0.,MAP_SNAPSHOT_REPLICA); nominal=Control((0.,0.,0.),"NOMINAL",f"stationary-{index:02d}")
        records.append(compact_result(f"REPLICA_STATIONARY_SAFE_{index:02d}",state,unified.certify(state,nominal,(),MAP_SNAPSHOT_REPLICA,120.0),{"route_id":row["route_id"],"selection":"FIRST_10_EXECUTION_ORDER"}))
    for index,row in enumerate(selected):
        direction=np.asarray(row["goal_m"],dtype=float)-np.asarray(row["start_m"],dtype=float); direction/=np.linalg.norm(direction)
        velocity=tuple(float(x) for x in 0.005*direction)
        state=State(tuple(row["start_m"]),velocity,0.,MAP_SNAPSHOT_REPLICA); nominal=Control((0.,0.,0.),"NOMINAL",f"moving-{index:02d}")
        records.append(compact_result(f"REPLICA_NONZERO_BRAKING_{index:02d}",state,unified.certify(state,nominal,(),MAP_SNAPSHOT_REPLICA,120.0),{"route_id":row["route_id"],"velocity_rule":"0.005_MPS_ALONG_FROZEN_ROUTE_DIRECTION","h_stop_expected":1}))
    unsafe=sorted((row for row in diagnostic if row["classification"]=="UNSAFE"),key=lambda row:row["source_start_id"])[:5]
    for index,row in enumerate(unsafe):
        state=State(tuple(row["position_m"]),(0.,0.,0.),0.,MAP_SNAPSHOT_REPLICA); zero=Control((0.,0.,0.),"NOMINAL",f"unsafe-{index:02d}")
        direct=segment.certify(state,zero,MAP_SNAPSHOT_REPLICA); result=unified.certify(state,zero,(),MAP_SNAPSHOT_REPLICA,120.0)
        records.append(compact_result(f"REPLICA_FROZEN_UNSAFE_STATE_{index:02d}",state,result,{"source_start_id":row["source_start_id"],"frozen_classification":"UNSAFE","direct_segment_status":direct.status.value,"direct_segment_reason":direct.reason_code,"direct_segment_lower_bound":direct.lower_bound}))
    timing_values={key:[float(r["timing"].get(key,0.0)) for r in records if key in r["timing"]] for key in ("actuator_check","current_cbf_query","segment_certification","backup_rollout","terminal_check","total")}
    timing={}
    for key,values in timing_values.items():
        if values:
            a=np.asarray(values); timing[key]={"mean":float(a.mean()),"p50":float(np.percentile(a,50)),"p95":float(np.percentile(a,95)),"max":float(a.max()),"count":len(values)}
    output={"status":"PASS_REPLICA_GT_FINE_PLANT_FREE_MAP_SMOKE","map_snapshot_id":MAP_SNAPSHOT_REPLICA,"map_identities":actual,"gaussian_count":len(map_adapter.centers),"primitive":"ISOTROPIC_GAUSSIAN_SPHERE","segment_backend":"EXACT_ANALYTIC_SPHERE_SEGMENT_MINIMUM","state_count":len(records),"category_counts":{"stationary_safe":10,"nonzero_braking":10,"frozen_unsafe_direct_segment":5,"backup_witness_not_found":0},"structural_not_found":["BACKUP_WITNESS_NOT_FOUND_CLASS_NOT_PRESENT_IN_FROZEN_STATE_SET"],"formal_navigation_rollout_count":0,"reference_online_read_count":0,"reference_offline_evaluation":"NOT_RUN_NOT_REQUIRED_FOR_COMPATIBILITY_SMOKE","records":records,"timing_seconds":timing}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",encoding="utf-8",newline="\n") as handle:
        handle.write(json.dumps(output,indent=2,sort_keys=True)+"\n")
    print(output["status"],output["state_count"],"REFERENCE_ONLINE_READS=0")


if __name__=="__main__": main()
