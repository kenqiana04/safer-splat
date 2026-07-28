#!/usr/bin/env python3
"""Validate the compact topology result emitted by the independent CPU auditor."""
from __future__ import annotations
from _common import ROOT, atomic_json, load_json

def main() -> None:
    p=ROOT/"mesh_structure/replica_mesh_structure_summary.json"; x=load_json(p)
    required={"vertex_count","face_count","bbox","connected_component_count","boundary_edge_count","non_manifold_edge_count","uv_available","reference_a","reference_b"}
    missing=sorted(required-set(x))
    if missing: raise SystemExit("mesh_structure_missing_fields:"+",".join(missing))
    x["status"]="PASS_READ_ONLY_MESH_STRUCTURE_AUDIT";x["component_id_sidecar"] = str(p.with_name(p.name+".vertex_component_u32.bin"))
    atomic_json(p,x)

if __name__=="__main__": main()
