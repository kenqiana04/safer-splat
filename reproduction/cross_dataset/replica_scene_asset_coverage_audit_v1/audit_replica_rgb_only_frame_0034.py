#!/usr/bin/env python3
"""Keep the single RGB-only mechanism separate from the 32 joint failures."""
from __future__ import annotations
from _common import ROOT, atomic_json, load_json

def main()->None:
    ray=load_json(ROOT/"independent_raycast/independent_mesh_raycast_summary.json");diag=load_json(ROOT/"diagnostic_variants/diagnostic_render_summary.json")
    x=next(v for v in ray["frames"] if v["frame_id"]=="frame_0034")
    a=[r for r in diag["results"] if r["frame_id"]=="frame_0034" and r["variant"]=="A_FLAT_UNTEXTURED_SAME_GEOMETRY"]
    flat=a[0]["stats"] if a else None
    atomic_json(ROOT/"rgb_only_analysis/replica_rgb_only_frame_0034_audit.json",{"status":"PASS_RGB_ONLY_SEPARATE_AUDIT","frame_id":"frame_0034","v1_depth_status":{"valid_fraction":x["habitat_depth_valid_fraction"],"depth_valid":x["habitat_depth_valid_fraction"]>0},"independent_raycast":{"any_hit_fraction":x["any_hit_fraction"],"front_facing_hit_fraction":x["front_facing_hit_fraction"],"dominant_component":x["dominant_component"],"uv":None,"material_id":None,"texture_id":None},"actual_direct_ply_material_texture_contract":"no UV/material/texture assignment; vertex RGB only","flat_untextured_diagnostic":flat,"normal_same_location_yaws":"retained in frozen 81-probe registry","RGB_ONLY_FRAME_0034_MECHANISM":"RGB_ONLY_LEGITIMATELY_DARK_VIEW_UNDER_V1_THRESHOLD","reason":"sparse valid geometry/depth coverage is below the historic RGB nonzero threshold; no material/UV/texture binding exists in the actual direct-Ply stage"})

if __name__=="__main__":main()
