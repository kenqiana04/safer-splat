#!/usr/bin/env python3
"""Build exact 41x31 float64 rays from frozen c2w/intrinsics, not observations."""
from __future__ import annotations
import csv
import numpy as np
from _common import MANIFEST, ROOT, V2_ROOT, atomic_json, load_json, sha256


def main() -> None:
    probes = load_json(V2_ROOT / "anomaly_registry/diagnostic_probe_registry.json")["probes"]
    manifest = {r["frame_id"]: r for r in csv.DictReader(MANIFEST.open(encoding="utf-8"))}
    grid = {(round(x), round(y)): {"main_grid"} for y in np.linspace(0, 479, 31) for x in np.linspace(0, 639, 41)}
    for xy, tag in {(320,240):"center", (160,120):"quarter", (480,120):"quarter", (160,360):"quarter", (480,360):"quarter", (0,240):"border", (639,240):"border", (320,0):"border", (320,479):"border"}.items(): grid.setdefault(xy, set()).add(tag)
    rows=[]
    for p in probes:
        m=manifest[p["frame_id"]]; c2w=np.array([[float(m[f"c2w_{r}{c}"]) for c in range(4)] for r in range(4)], dtype=np.float64)
        for (x,y),tags in grid.items():
            d=np.array([(x-320.)/320., -(y-240.)/320., -1.],dtype=np.float64);d/=np.linalg.norm(d);d=c2w[:3,:3]@d;d/=np.linalg.norm(d)
            rows.append({"frame_id":p["frame_id"],"pixel_x":x,"pixel_y":y,"tags":"+".join(sorted(tags)),"role":p["role"],"joint_bad":str(bool(p["rgb_bad"] and p["depth_bad"])).lower(),"rgb_only":str(bool(p["rgb_bad"] and not p["depth_bad"])).lower(),"origin_x":format(c2w[0,3],".17g"),"origin_y":format(c2w[1,3],".17g"),"origin_z":format(c2w[2,3],".17g"),"dir_x":format(d[0],".17g"),"dir_y":format(d[1],".17g"),"dir_z":format(d[2],".17g"),"reference_b_key":str(p["frame_id"] in {"frame_0000","frame_0001","frame_0020","frame_0034"} and (x,y)==(320,240)).lower()})
    out=ROOT/"independent_raycast/rays.csv";out.parent.mkdir(parents=True,exist_ok=True)
    with out.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    atomic_json(ROOT/"independent_raycast/replica_probe_raycast_registry.json", {"status":"PASS_FROZEN_PINHOLE_RAY_REGISTRY","probe_count":len(probes),"main_grid":[41,31],"main_grid_ray_count_per_probe":1271,"total_ray_count_per_probe":len(grid),"total_ray_count":len(rows),"intrinsics":{"width":640,"height":480,"fx":320.,"fy":320.,"cx":320.,"cy":240.,"hfov_deg":90.,"near_m":.05,"far_m":20.,"camera_forward":"negative_z_opengl_from_frozen_c2w"},"source_registry_sha256":sha256(V2_ROOT/"anomaly_registry/diagnostic_probe_registry.json"),"rows_csv_server_only":str(out),"rows_sha256":sha256(out)})

if __name__ == "__main__": main()
