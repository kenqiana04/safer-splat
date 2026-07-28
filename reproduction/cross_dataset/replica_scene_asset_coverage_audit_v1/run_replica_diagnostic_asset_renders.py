#!/usr/bin/env python3
"""Run the fixed diagnostic-only render budget with a fresh Python/Simulator per frame."""
from __future__ import annotations
import argparse, csv, hashlib, json, os, subprocess, sys
from pathlib import Path
import imageio.v3 as iio
import numpy as np
from _common import MANIFEST, ROOT, SCENE_ROOT, V2_ROOT, atomic_json, diagnostic_marker, load_json, sha256

VARIANTS={
    "A_FLAT_UNTEXTURED_SAME_GEOMETRY": ROOT/"diagnostic_variants/flat_untextured_same_geometry.ply",
    "B_DOUBLE_SIDED_DIAGNOSTIC": ROOT/"diagnostic_variants/double_sided_diagnostic.ply",
    "C_COMPONENT_FLAT_ID": ROOT/"diagnostic_variants/component_flat_id.ply",
    "D_OFFICIAL_ALTERNATE_ASSET_HANDLE": SCENE_ROOT/"habitat/mesh_semantic.ply",
}

def stats(rgb,depth):
    return {"rgb_shape":list(rgb.shape),"depth_shape":list(depth.shape),"rgb_max":int(rgb.max()),"rgb_nonzero_fraction":float((rgb[:,:,:3]>0).mean()),"depth_max_m":float(depth.max()),"depth_valid_fraction":float((depth>0).mean()),"rgb_checker_bad":not(tuple(rgb[:,:,:3].shape)==(480,640,3) and int(rgb.max())>0 and float((rgb[:,:,:3]>0).mean())>.01),"depth_checker_bad":not(tuple(depth.shape)==(480,640) and float(depth.max())>0)}

def one(args):
    import habitat_sim, quaternion
    rows={r["frame_id"]:r for r in csv.DictReader(MANIFEST.open(encoding="utf-8"))};row=rows[args.frame]
    sc=habitat_sim.SimulatorConfiguration();sc.scene_id=str(VARIANTS[args.variant]);sc.gpu_device_id=0;sc.enable_physics=False
    ac=habitat_sim.agent.AgentConfiguration();specs=[]
    for uuid,typ in (("rgba",habitat_sim.SensorType.COLOR),("depth",habitat_sim.SensorType.DEPTH)):
        s=habitat_sim.CameraSensorSpec();s.uuid=uuid;s.sensor_type=typ;s.sensor_subtype=habitat_sim.SensorSubType.PINHOLE;s.resolution=[480,640];s.position=[0.,1.5,0.];s.hfov=90.;s.near=.05;s.far=20.;specs.append(s)
    ac.sensor_specifications=specs;sim=habitat_sim.Simulator(habitat_sim.Configuration(sc,[ac]))
    try:
        if not sim.pathfinder.load_nav_mesh(str(SCENE_ROOT/"habitat/mesh_semantic.navmesh")):raise RuntimeError("official_navmesh_load_failed")
        agent=sim.initialize_agent(0);state=agent.get_state();state.position=np.array([float(row[f"source_navmesh_point_{q}"]) for q in "xyz"],dtype=np.float32);state.rotation=np.quaternion(float(row["quat_w"]),float(row["quat_x"]),float(row["quat_y"]),float(row["quat_z"]));agent.set_state(state);o=sim.get_sensor_observations();rgb=o["rgba"].astype(np.uint8);depth=o["depth"].astype(np.float32)
        out=ROOT/"diagnostic_variants"/"captures"/args.variant;out.mkdir(parents=True,exist_ok=True);iio.imwrite(out/(args.frame+".png"),rgb[:,:,:3]);np.save(out/(args.frame+"_depth.npy"),depth)
        result={"marker":diagnostic_marker(),"variant":args.variant,"frame_id":args.frame,"scene_id":str(VARIANTS[args.variant]),"scene_sha256":sha256(VARIANTS[args.variant]),"fresh_subprocess":True,"fresh_simulator":True,"stats":stats(rgb,depth),"rgb_capture":str(out/(args.frame+".png")),"depth_capture":str(out/(args.frame+"_depth.npy"))}
        (out/(args.frame+".json")).write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    finally:sim.close()

def schedule():
    probes=load_json(V2_ROOT/"anomaly_registry/diagnostic_probe_registry.json")["probes"]
    joint=[p["frame_id"] for p in probes if p["rgb_bad"] and p["depth_bad"]];anomaly=[p["frame_id"] for p in probes if p["rgb_bad"]]
    controls=[p["frame_id"] for p in probes if p["role"]=="deterministic_good_control"]
    return {"A_FLAT_UNTEXTURED_SAME_GEOMETRY":anomaly+controls,"B_DOUBLE_SIDED_DIAGNOSTIC":joint+controls[:8],"C_COMPONENT_FLAT_ID":joint+controls[:8],"D_OFFICIAL_ALTERNATE_ASSET_HANDLE":joint+["frame_0034"]+controls[:8]}

def run_all():
    out=ROOT/"diagnostic_variants/diagnostic_render_summary.json"
    if out.exists():raise SystemExit("diagnostic_render_summary_exists_refuse_rerun")
    all_results=[];plan=schedule();env={**os.environ,"CUDA_VISIBLE_DEVICES":"1","PYTHONNOUSERSITE":"1","PYTHONDONTWRITEBYTECODE":"1"}
    for variant,frames in plan.items():
        for fid in frames:
            cp=subprocess.run([sys.executable,__file__,"--one","--variant",variant,"--frame",fid],env=env,capture_output=True,text=True)
            capture=ROOT/"diagnostic_variants/captures"/variant/(fid+".json")
            if cp.returncode or not capture.exists():raise RuntimeError(f"diagnostic_render_failed:{variant}:{fid}:{cp.stderr[-600:]}")
            all_results.append(json.loads(capture.read_text(encoding="utf-8")))
    atomic_json(out,{"status":"PASS_FIXED_DIAGNOSTIC_RENDER_BUDGET","marker":diagnostic_marker(),"fresh_subprocess_and_simulator_per_frame":True,"budget":{"A":45,"B":40,"C":40,"D":41,"total":166},"counts":{k:len(v) for k,v in plan.items()},"results":all_results,"formal_dataset_output_created":False})

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--one",action="store_true");p.add_argument("--variant",choices=VARIANTS);p.add_argument("--frame");a=p.parse_args();one(a) if a.one else run_all()
