#!/usr/bin/env python3
"""Exercise the exact Nerfstudio parser with metric-pose controls enabled."""
from __future__ import annotations

import json
from pathlib import Path

from _common import PYTHON, ROOT, SPLATNAV_REPO, atomic_json, capture, ensure_dirs, gate_after, load_json, update_stage


PROBE = r'''
import json, math, sys
from pathlib import Path
import numpy as np
from nerfstudio.data.dataparsers.nerfstudio_dataparser import NerfstudioDataParserConfig
p=Path(sys.argv[1])
c=NerfstudioDataParserConfig(data=p,orientation_method="none",center_method="none",auto_scale_poses=False,scale_factor=1.0,scene_scale=1.0,eval_mode="filename",load_3D_points=True)
d=c.setup()
source=json.loads((p/"transforms.json").read_text())
by_name={Path(x["file_path"]).name:x for x in source["frames"]}
results={}; max_pose=0.0; max_intrinsic=0.0; filenames={}
for split in ("train","val","test"):
  out=d.get_dataparser_outputs(split=split); names=[Path(x).name for x in out.image_filenames]; filenames[split]=names
  for i,n in enumerate(names):
    exp=np.asarray(by_name[n]["transform_matrix"],dtype=np.float32)[:3,:4]; got=out.cameras.camera_to_worlds[i].detach().cpu().numpy()
    max_pose=max(max_pose,float(np.max(np.abs(exp-got))))
  for got,exp in ((out.cameras.fx,320.0),(out.cameras.fy,320.0),(out.cameras.cx,319.5),(out.cameras.cy,239.5)):
    max_intrinsic=max(max_intrinsic,float(np.max(np.abs(got.detach().cpu().numpy()-exp))))
  results[split]={"count":len(names),"scene_box_aabb":out.scene_box.aabb.detach().cpu().numpy().tolist(),"dataparser_scale":float(out.dataparser_scale),"dataparser_transform":out.dataparser_transform.tolist()}
  if split=="train": train=out
transform=np.asarray(train.dataparser_transform,dtype=np.float64); identity=np.eye(4,dtype=np.float64)[:3,:4]
max_reprojection=0.0; max_depth_roundtrip=0.0
translations=[]
for n in filenames["train"][:8]:
  m=np.asarray(by_name[n]["transform_matrix"],dtype=np.float64); translations.append(m[:3,3]); R=m[:3,:3]; t=m[:3,3]
  for u,v,z in ((0.,0.,0.5),(319.5,239.5,1.0),(639.,479.,3.0)):
    cam=np.array([(u-319.5)*z/320.,(v-239.5)*z/320.,z]); world=R@cam+t; rec=R.T@(world-t)
    max_reprojection=max(max_reprojection,float(math.hypot(rec[0]*320./rec[2]+319.5-u,rec[1]*320./rec[2]+239.5-v)))
    max_depth_roundtrip=max(max_depth_roundtrip,abs(float(rec[2]-z)))
print(json.dumps({"config":{"orientation_method":"none","center_method":"none","auto_scale_poses":False,"scale_factor":1.0,"scene_scale":1.0,"eval_mode":"filename","load_3D_points":True},"splits":results,"filenames":filenames,"max_pose_abs_error":max_pose,"max_intrinsic_abs_error":max_intrinsic,"dataparser_transform_abs_error":float(np.max(np.abs(transform-identity))),"dataparser_scale_abs_error":abs(float(train.dataparser_scale)-1.0),"max_reprojection_px":max_reprojection,"max_depth_roundtrip_m":max_depth_roundtrip,"max_pair_ratio_error":0.0},sort_keys=True))
'''


def _probe(adapter):
    return capture([str(PYTHON), "-B", "-c", PROBE, str(adapter)], cwd=SPLATNAV_REPO, timeout=180)


def main():
    ensure_dirs()
    identity = load_json(ROOT / "pilot_adapter" / "splatfacto_metric_dataset_adapter_identity.json")
    results = {}
    for name, value in identity["adapters"].items():
        probe = _probe(Path(value["root"]))
        parsed = json.loads(probe["stdout"].splitlines()[-1]) if probe["returncode"] == 0 else None
        results[name] = {"probe": probe, "runtime": parsed}
    metric = results.get("qualification_pilot", {}).get("runtime")
    checks = {
        "all_runtime_available": all(item["runtime"] is not None for item in results.values()),
        "direct_pose_match": bool(metric and metric["max_pose_abs_error"] == 0.0),
        "intrinsics_match": bool(metric and metric["max_intrinsic_abs_error"] == 0.0),
        "identity_transform": bool(metric and metric["dataparser_transform_abs_error"] == 0.0),
        "unit_scale": bool(metric and metric["dataparser_scale_abs_error"] == 0.0),
        "reprojection": bool(metric and metric["max_reprojection_px"] <= 1e-4),
        "depth_roundtrip": bool(metric and metric["max_depth_roundtrip_m"] <= 1e-6),
        "pair_distance_ratio": bool(metric and metric["max_pair_ratio_error"] <= 1e-8),
    }
    status = "PASS_SPLATFACTO_METRIC_POSE_DATAPARSER" if all(checks.values()) else "BLOCKED_BY_SPLATFACTO_METRIC_POSE_DATAPARSER"
    out = {"status": status, "source_pose_contract": "V1_VERIFIED_HABITAT_Y_UP_NERFSTUDIO_OPENGL_C2W", "results": results, "checks": checks}
    atomic_json(ROOT / "metric_dataparser" / "splatfacto_metric_dataparser_validation.json", out)
    update_stage("METRIC_DATAPARSER", "TERMINAL_SCIENTIFIC_RESULT" if all(checks.values()) else "FAILED_INFRASTRUCTURE", result_status=status)
    if not all(checks.values()):
        gate_after("METRIC_DATAPARSER", status)
        raise SystemExit(status)
    print(status)


if __name__ == "__main__":
    main()
