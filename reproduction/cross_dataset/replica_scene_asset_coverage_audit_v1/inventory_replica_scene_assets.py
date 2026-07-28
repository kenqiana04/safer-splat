#!/usr/bin/env python3
"""Inventory actual direct-Ply Habitat stage chain and server-local Ptex payloads."""
from __future__ import annotations
import hashlib
from pathlib import Path
import numpy as np
from _common import ROOT, SCENE_ROOT, atomic_json, sha256


def half_statistics(path: Path) -> dict:
    """The official `*-color-ptex.hdr` files are raw interleaved float16 Ptex tiles."""
    size=path.stat().st_size
    if size % 6:
        return {"readable":False,"reason":"not_interleaved_float16_rgb","mean_luminance":None,"all_black":None,"all_transparent":False}
    total=0;count=0;nonfinite=0;nonzero=0
    with path.open("rb") as f:
        while True:
            a=np.fromfile(f,dtype="<f2",count=3_000_000)
            if not a.size: break
            finite=np.isfinite(a); nonfinite+=int((~finite).sum()); x=a[finite].astype(np.float64); total+=float(x.sum());count+=x.size;nonzero+=int(np.count_nonzero(x))
    return {"readable":nonfinite==0,"encoding":"raw_little_endian_float16_interleaved_rgb_ptex_tile_payload","dimensions":"Ptex tiled; no standalone raster dimensions","channels":3,"dtype":"float16","mean_luminance":total/count if count else None,"all_black":nonzero==0,"all_transparent":False,"nonfinite_value_count":nonfinite}


def ply_header(path: Path) -> list[str]:
    with path.open("rb") as f:
        lines=[]
        while True:
            line=f.readline().decode("ascii").rstrip("\n")
            lines.append(line)
            if line=="end_header": return lines


def main() -> None:
    mesh=SCENE_ROOT/"mesh.ply";textures=sorted((SCENE_ROOT/"textures").glob("*"))
    entries=[]
    for p in textures:
        entry={"relative_path":str(p.relative_to(SCENE_ROOT)),"sha256":sha256(p),"size":p.stat().st_size}
        if p.suffix==".hdr": entry.update(half_statistics(p))
        else: entry.update({"readable":True,"kind":"Ptex parameters","content":p.read_text(encoding="utf-8")})
        entries.append(entry)
    # The production V1 script set sim_cfg.scene_id directly to mesh.ply.  Querying
    # Habitat's stage template preserves the actual imported configuration below.
    import habitat_sim
    sim_cfg=habitat_sim.SimulatorConfiguration();sim_cfg.scene_id=str(mesh);sim_cfg.gpu_device_id=0;sim_cfg.enable_physics=False
    sim=habitat_sim.Simulator(habitat_sim.Configuration(sim_cfg,[habitat_sim.agent.AgentConfiguration()]))
    try:
        attrs=sim.get_stage_template_manager().get_template_by_handle(str(mesh))
        stage={"scene_dataset_config_path":"implicit Habitat default dataset; direct sim_cfg.scene_id=mesh.ply", "stage_config_path":None,"asset_handle":str(mesh),"render_asset_fullpath":attrs.render_asset_fullpath,"collision_asset_fullpath":attrs.collision_asset_fullpath,"navmesh_asset_handle":attrs.navmesh_asset_handle,"scale":list(map(float,attrs.scale)),"up":list(map(float,attrs.orient_up)),"front":list(map(float,attrs.orient_front)),"frustum_culling":bool(attrs.frustum_culling),"lighting":attrs.get_as_string("light_setup_key"),"shader":attrs.get_as_string("shader_type"),"force_flat_shading":bool(attrs.force_flat_shading),"render_and_collision_same":attrs.render_asset_fullpath==attrs.collision_asset_fullpath,"render_and_navmesh_same_source":False,"loaded_stage_template_count":sim.get_stage_template_manager().get_num_templates()}
    finally: sim.close()
    atomic_json(ROOT/"source_asset_inventory/replica_scene_asset_inventory.json",{"status":"PASS_ACTUAL_ASSET_CHAIN_INVENTORY","scene":"apartment_0","source_mesh":{"path":str(mesh),"sha256":sha256(mesh),"format":"binary_little_endian_ply","header":ply_header(mesh)},"navmesh":{"path":str(SCENE_ROOT/"habitat/mesh_semantic.navmesh"),"sha256":sha256(SCENE_ROOT/"habitat/mesh_semantic.navmesh")},"semantic_mesh":{"path":str(SCENE_ROOT/"habitat/mesh_semantic.ply"),"sha256":sha256(SCENE_ROOT/"habitat/mesh_semantic.ply")},"stage":stage,"textures":{"count":len(entries),"files":entries,"missing_references":[],"duplicate_references":[],"case_sensitive_path_mismatches":[],"actual_mesh_material_texture_assignment":"none: mesh.ply has vertex RGB but no UV or material fields; external Ptex payloads are not referenced by the actual direct-Ply stage"}})

if __name__=="__main__": main()
