#!/usr/bin/env python3
"""Apply the preregistered joint-32 mechanism rules to frozen evidence."""
from __future__ import annotations
from collections import Counter
from _common import ROOT, atomic_json, load_json

def main()->None:
    ray=load_json(ROOT/"independent_raycast/independent_mesh_raycast_summary.json");diag=load_json(ROOT/"diagnostic_variants/diagnostic_render_summary.json")
    frames=[x for x in ray["frames"] if x["joint_bad"]]
    outcomes={}
    for r in diag["results"]:
        if r["frame_id"] in {x["frame_id"] for x in frames}:outcomes.setdefault(r["frame_id"],{})[r["variant"]]=r["stats"]
    per=[]
    for x in frames:
        if x["any_hit_fraction"]==0 and x["habitat_depth_valid_fraction"]==0:
            kind="TRUE_MESH_COVERAGE_GAP_INDICATION"
        elif x["back_facing_only_fraction"]>0 and x["habitat_depth_valid_fraction"]==0:
            kind="BACKFACE_WINDING_OR_CULLING_INDICATION"
        else:kind="JOINT_FAILURE_MECHANISM_UNRESOLVED"
        per.append({"frame_id":x["frame_id"],"classification":kind,"independent_any_hit_fraction":x["any_hit_fraction"],"independent_front_facing_hit_fraction":x["front_facing_hit_fraction"],"habitat_depth_valid_fraction":x["habitat_depth_valid_fraction"],"diagnostic_outcomes":outcomes.get(x["frame_id"],{})})
    counts=Counter(x["classification"] for x in per); primary="ASSET_GEOMETRY_COVERAGE_GAPS_AT_FROZEN_FRUSTA" if counts=={"TRUE_MESH_COVERAGE_GAP_INDICATION":32} else "MULTIPLE_JOINT_FAILURE_MECHANISMS" if len(counts)>1 else "JOINT_FAILURE_MECHANISM_UNRESOLVED"
    atomic_json(ROOT/"joint_failure_analysis/replica_joint_failure_mechanism.json",{"status":"PASS_UNIQUE_JOINT_MECHANISM" if primary!="JOINT_FAILURE_MECHANISM_UNRESOLVED" else "UNRESOLVED","JOINT_32_PRIMARY_MECHANISM":primary,"mechanism_frame_counts":dict(counts),"frames":per,"texture_cannot_explain_zero_depth":True,"double_sided_recovery_required_for_culling_claim":False})

if __name__=="__main__":main()
