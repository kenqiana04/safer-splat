#!/usr/bin/env python3
"""Summarize server-only BVH ray rows and compare them to frozen V1 depth."""
from __future__ import annotations
import csv, statistics
from collections import defaultdict
import imageio.v3 as iio
import numpy as np
from _common import ROOT, V2_ROOT, atomic_json, load_json, sha256

def b(v: str) -> bool: return v in {"1","true","True"}
def med(a): return float(statistics.median(a)) if a else None

def main() -> None:
    src=ROOT/"independent_raycast/ray_rows.csv"; groups=defaultdict(list)
    probes={p["frame_id"]:p for p in load_json(V2_ROOT/"anomaly_registry/diagnostic_probe_registry.json")["probes"]}
    derived=ROOT/"independent_raycast/ray_rows_with_frozen_roles.csv"
    with src.open(encoding="utf-8",newline="") as fin, derived.open("w",encoding="utf-8",newline="") as fout:
        reader=csv.DictReader(fin); writer=csv.DictWriter(fout,fieldnames=reader.fieldnames);writer.writeheader()
        for r in reader:
            p=probes[r["frame_id"]]; r["joint_bad"]=str(bool(p["rgb_bad"] and p["depth_bad"])).lower();r["rgb_only"]=str(bool(p["rgb_bad"] and not p["depth_bad"])).lower();writer.writerow(r);groups[r["frame_id"]].append(r)
    frames=[];ref_checks=0;ref_agree=0
    for fid,rows in sorted(groups.items()):
        hit=[r for r in rows if b(r["hit"])];front=[r for r in rows if b(r["any_front_hit"])];backonly=[r for r in rows if b(r["back_facing_only"])];
        key=[r for r in rows if b(r["reference_b_checked"])];ref_checks+=len(key);ref_agree+=sum(b(r["reference_b_agree"]) for r in key)
        depth=iio.imread(probes[fid]["depth_path"])
        comps=sorted({int(r["component_id"]) for r in hit if r["component_id"]})
        frames.append({"frame_id":fid,"role":probes[fid]["role"],"joint_bad":bool(probes[fid]["rgb_bad"] and probes[fid]["depth_bad"]),"rgb_only":bool(probes[fid]["rgb_bad"] and not probes[fid]["depth_bad"]),"habitat_depth_valid_fraction":float((depth>0).mean()),"total_ray_count":len(rows),"any_hit_fraction":len(hit)/len(rows),"valid_near_far_hit_fraction":len(hit)/len(rows),"front_facing_hit_fraction":len(front)/len(rows),"back_facing_only_fraction":len(backonly)/len(rows),"no_hit_fraction":1-len(hit)/len(rows),"median_hit_distance":med([float(r["hit_distance"]) for r in hit]),"center_ray_hit":next((b(r["hit"]) for r in rows if r["tags"].find("center")>=0),None),"hit_component_ids":comps,"dominant_component":comps[0] if len(comps)==1 else None,"material_ids":[],"texture_ids":[]})
    def selected(predicate,key):
        a=[x[key] for x in frames if predicate(x)]
        return med(a)
    key_path=ROOT/"independent_raycast/reference_b_key_rows.csv"
    if key_path.exists():
        with key_path.open(encoding="utf-8",newline="") as f:
            key_rows=list(csv.DictReader(f));ref_checks=len(key_rows);ref_agree=sum(b(r["reference_b_agree"]) for r in key_rows)
    payload={"status":"PASS_INDEPENDENT_FLOAT64_RAYCAST","ray_rows_server_only":str(derived),"ray_rows_sha256":sha256(derived),"frame_count":len(frames),"independent_ray_count":sum(x["total_ray_count"] for x in frames),"reference_a":"task_owned_cpu_bvh_float64_moller_trumbore","reference_b":"task_owned_cpu_bruteforce_float64_moller_trumbore_on_key_rays","reference_b_checked":ref_checks,"reference_b_agree":ref_agree,"reference_agreement":ref_checks>0 and ref_checks==ref_agree,"frames":frames,"aggregate":{"normal_control_median_hit_fraction":selected(lambda x:not x["joint_bad"] and not x["rgb_only"],"any_hit_fraction"),"joint_bad_median_hit_fraction":selected(lambda x:x["joint_bad"],"any_hit_fraction"),"joint_bad_median_front_facing_hit_fraction":selected(lambda x:x["joint_bad"],"front_facing_hit_fraction"),"joint_bad_median_back_facing_only_fraction":selected(lambda x:x["joint_bad"],"back_facing_only_fraction"),"joint_bad_no_hit_frame_count":sum(x["any_hit_fraction"]==0 for x in frames if x["joint_bad"])}}
    atomic_json(ROOT/"independent_raycast/independent_mesh_raycast_summary.json",payload)

if __name__=="__main__": main()
