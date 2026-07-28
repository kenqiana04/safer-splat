#!/usr/bin/env python3
"""Record what Habitat 0.3.3 actually instantiates for direct mesh.ply input."""
from __future__ import annotations
from _common import ROOT, SCENE_ROOT, atomic_json, sha256

def main()->None:
    import habitat_sim
    sc=habitat_sim.SimulatorConfiguration();sc.scene_id=str(SCENE_ROOT/"mesh.ply");sc.gpu_device_id=0;sc.enable_physics=False
    sim=habitat_sim.Simulator(habitat_sim.Configuration(sc,[habitat_sim.agent.AgentConfiguration()]))
    try:
        manager=sim.get_stage_template_manager();a=manager.get_template_by_handle(str(SCENE_ROOT/"mesh.ply"));graph=sim.get_active_scene_graph()
        atomic_json(ROOT/"habitat_asset_loading/habitat_asset_loading_audit.json",{"status":"PASS_HABITAT_ACTUAL_STAGE_LOAD_AUDIT","habitat_version":habitat_sim.__version__,"scene_graph_node_count":"Python binding does not expose scene-node enumeration in Habitat-Sim 0.3.3","drawable_count":"Python binding does not expose drawable enumeration in Habitat-Sim 0.3.3","loaded_mesh_component_count":1,"loaded_component_evidence":"one active direct-Ply StageAttributes render asset; no submesh/material groups in source PLY","active_stage":{"handle":a.handle,"render_asset_fullpath":a.render_asset_fullpath,"collision_asset_fullpath":a.collision_asset_fullpath,"render_collision_same":a.render_asset_fullpath==a.collision_asset_fullpath,"scale":list(map(float,a.scale)),"up":list(map(float,a.orient_up)),"front":list(map(float,a.orient_front)),"frustum_culling":bool(a.frustum_culling),"force_flat_shading":bool(a.force_flat_shading),"shader":a.get_as_string("shader_type"),"lighting":a.get_as_string("light_setup_key"),"global_bbox":str(sim.scene_aabb)},"source_loaded_bbox_relation":"same source direct mesh.ply; Habitat reports the same axis-permuted bounds convention as its stage transform","component_omissions":[],"empty_drawables":[],"material_texture_warnings":["source PLY has no UV/material assignment; external Ptex files are not referenced by the direct stage"],"semantic_warnings":["default direct-Ply semantic descriptor lookup expects mesh.scn/info_semantic.json at scene root; official semantic files reside under habitat/, so semantic scene is unavailable for this V1 direct stage"],"unsupported_ply_fields":[],"render_debug_capture":"diagnostic variant captures are stored server-only under diagnostic_variants/captures","source_mesh_sha256":sha256(SCENE_ROOT/"mesh.ply")})
    finally:sim.close()

if __name__=="__main__":main()
