#!/usr/bin/env python3
"""Select and freeze the 100-scenario V2 registry from shadow-only evidence."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from task_config_v2 import *  # noqa: F403

def pick(rows: list[dict], predicate, count: int, used: set[str], key) -> list[dict]:
    eligible=[r for r in rows if predicate(r) and r["candidate_id"] not in used]
    eligible.sort(key=key); chosen=eligible[:count]
    if len(chosen)!=count: raise RuntimeError(f"selection deficit {len(chosen)}/{count}")
    used.update(r["candidate_id"] for r in chosen); return chosen

def main() -> int:
    parser=argparse.ArgumentParser(); parser.add_argument("--output",type=Path,required=True); args=parser.parse_args()
    rows=json.loads((TASK_ROOT/"candidate_pool/candidate_pool_qualified.json").read_text()); freeze=json.loads((TASK_ROOT/"input_freeze/pr80_frozen_input_identity.json").read_text())
    used:set[str]=set(); groups:dict[str,list[dict]]={}
    cid=lambda r:r["candidate_id"]
    groups[GROUPS[0]]=pick(rows,lambda r:not r.get("S1",{}).get("projection_attempted") and r.get("S2",{}).get("m1_qp_feasible") and not r.get("S3",{}).get("verifier_trigger") and not r.get("S4",{}).get("recovery_trigger") and r.get("reference_clearance_lower_bound_m",0)>=.30,20,used,cid)
    g1=[]
    g1+=pick(rows,lambda r:r.get("S1",{}).get("classification")=="MAP_UNSAFE" and r.get("S1",{}).get("projection_success"),12,used,lambda r:(r["S1"]["projected_displacement_m"],cid(r)))
    g1+=pick(rows,lambda r:r.get("S1",{}).get("classification")=="NEAR_BOUNDARY" and r.get("S1",{}).get("projection_success"),4,used,lambda r:(r["S1"]["projected_displacement_m"],cid(r)))
    g1+=pick(rows,lambda r:r.get("S1",{}).get("projection_attempted") and not r.get("S1",{}).get("projection_success"),4,used,cid)
    groups[GROUPS[1]]=g1
    groups[GROUPS[2]]=pick(rows,lambda r:r.get("S2",{}).get("m1_qp_feasible") and r.get("S2",{}).get("m2_qp_feasible") and r.get("S2",{}).get("H2_DOMINANCE_ACTIVE") and r.get("S2",{}).get("feasible_control_set_parity"),20,used,
        lambda r:(-r["S2"]["dominance_removal_ratio"],-r["S2"]["original_constraint_population"],-r["S2"]["multi_direction_constraint_rank"],cid(r)))
    g3=[]
    g3+=pick(rows,lambda r:r.get("S3",{}).get("trigger_type")=="ENDPOINT_UNSAFE",min(4,sum(x.get("S3",{}).get("trigger_type")=="ENDPOINT_UNSAFE" and x["candidate_id"] not in used for x in rows)),used,cid)
    g3+=pick(rows,lambda r:r.get("S3",{}).get("trigger_type")=="ENDPOINT_SAFE_SEGMENT_UNSAFE",1,used,cid)
    remaining=20-len(g3)
    g3+=pick(rows,lambda r:r.get("S3",{}).get("trigger_type") in {"MARGIN_VIOLATION_NO_COLLISION","SEGMENT_UNSAFE"} and not r.get("S3",{}).get("unavoidable_immediate_segment"),remaining,used,lambda r:(abs(r["S3"]["segment_h"]),cid(r)))
    groups[GROUPS[3]]=g3
    g4=[]
    g4+=pick(rows,lambda r:r.get("S4",{}).get("recovery_trigger") and r.get("S4",{}).get("recovery_recoverable"),14,used,lambda r:(-r["S4"]["predicted_min_h"],cid(r)))
    g4+=pick(rows,lambda r:r.get("S4",{}).get("recovery_trigger") and not r.get("S4",{}).get("recovery_recoverable"),6,used,lambda r:(r["S4"]["predicted_min_h"],cid(r)))
    groups[GROUPS[4]]=g4
    scenarios=[]
    for group in GROUPS:
        for ordinal,row in enumerate(groups[group]):
            scenario_id=f"{group[:2]}_{ordinal:02d}_{row['candidate_id']}"
            shadow={key:value for key,value in row.items() if key.startswith("S") or key in {"reason_codes","reference_valid","reference_clearance_lower_bound_m","generation_source","source_tags","source_node_id","candidate_id","velocity_source","goal_source"}}
            scenarios.append({"scenario_id":scenario_id,"group":group,"group_ordinal":ordinal,"candidate_id":row["candidate_id"],
                "start_m":row["p"],"initial_velocity_mps":row["v"],"goal_m":row["goal"],
                "seed":int.from_bytes(hashlib.sha256(f"{SEED}:{scenario_id}".encode()).digest()[:8],"big"),
                "dt":DT,"max_steps":MAX_STEPS,"candidate_budget":CANDIDATE_BUDGET,
                "activation_reason":row["reason_codes"],"shadow_stage_reachability":shadow,
                "frozen_identities":freeze["identities"],"reference_used_for_generation_and_evaluation_only":True,
                "reference_oracle_controller_input_count":0,"formal_rollout_metric_read_count":0})
    core={"schema_version":2,"id":"ETH3D_FAS_CBF_STRESS_SCENARIO_REGISTRY_V2","seed":SEED,"method_independent":True,
        "method_matrix":list(METHODS),"groups":list(GROUPS),"group_counts":{g:20 for g in GROUPS},"scenarios":scenarios,
        "map_ply_sha256":EXPECTED["map_ply_sha256"],"canonical_tree_sha256":EXPECTED["canonical_tree_sha256"],
        "reference_mesh_sha256":EXPECTED["reference_mesh_sha256"],"v1_registry_logical_sha256":EXPECTED["v1_registry_logical_sha256"],
        "controller_rollout_result_read_count":0,"scenario_selection_metric":"shadow_stage_reachability_only","locked":True}
    registry=dict(core); registry["registry_sha256"]=sha256_json(core); registry["status"]="PASS_LOCKED_ETH3D_FAS_CBF_STRESS_SCENARIO_REGISTRY_V2"
    atomic_json(args.output,registry); print(json.dumps({"status":registry["status"],"count":len(scenarios),"sha256":registry["registry_sha256"]},sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
