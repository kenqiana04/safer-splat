#!/usr/bin/env python3
"""Create the ten compact figures and the tracked evidence-boundary report."""
from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from _common import ROOT, atomic_json, load_json

def save(name, draw):
    p=ROOT/"figures"/name;p.parent.mkdir(parents=True,exist_ok=True);fig,ax=plt.subplots(figsize=(7,4));draw(ax);fig.tight_layout();fig.savefig(p,dpi=150);plt.close(fig)
def text(ax,title,lines):ax.axis("off");ax.set_title(title);ax.text(.02,.92,"\n".join(lines),va="top",family="monospace",fontsize=9)

def main()->None:
    ray=load_json(ROOT/"independent_raycast/independent_mesh_raycast_summary.json");joint=load_json(ROOT/"joint_failure_analysis/replica_joint_failure_mechanism.json");rgb=load_json(ROOT/"rgb_only_analysis/replica_rgb_only_frame_0034_audit.json");c=load_json(ROOT/"classification/replica_asset_failure_classification.json");r=load_json(ROOT/"classification/replica_asset_repair_feasibility.json");d=load_json(ROOT/"diagnostic_variants/diagnostic_render_summary.json")
    f=ray["frames"];jointf=[x for x in f if x["joint_bad"]];controls=[x for x in f if not x["joint_bad"] and not x["rgb_only"]];rgbf=next(x for x in f if x["rgb_only"])
    save("probe_independent_hit_fraction.png",lambda a:(a.scatter(range(len(f)),[x["any_hit_fraction"] for x in f],c=["crimson" if x["joint_bad"] else "orange" if x["rgb_only"] else "steelblue" for x in f]),a.set(xlabel="frozen probe index",ylabel="independent hit fraction",title="Frozen-probe independent mesh coverage")))
    save("joint_bad_vs_control_raycast.png",lambda a:(a.bar(["normal controls","joint 32"],[np.median([x["any_hit_fraction"] for x in controls]),np.median([x["any_hit_fraction"] for x in jointf])],color=["steelblue","crimson"]),a.set(ylabel="median hit fraction",title="Joint failures versus frozen normal controls")))
    save("front_vs_back_facing_hit_fraction.png",lambda a:(a.bar(["front","back-only","no hit"],[np.median([x["front_facing_hit_fraction"] for x in jointf]),np.median([x["back_facing_only_fraction"] for x in jointf]),np.median([x["no_hit_fraction"] for x in jointf])],color=["green","orange","crimson"]),a.set(title="Joint-32 facing/coverage fractions",ylabel="median fraction")))
    save("hit_distance_distribution.png",lambda a:(a.hist([x["median_hit_distance"] for x in controls if x["median_hit_distance"] is not None],bins=20,color="steelblue"),a.set(title="Normal-control hit-distance distribution",xlabel="metres")))
    save("mesh_component_hit_map.png",lambda a:(a.bar(*zip(*sorted({z:sum(z in x["hit_component_ids"] for x in f) for z in sorted({z for x in f for z in x["hit_component_ids"]})}.items()))),a.set(title="Hit components across frozen probes",xlabel="component ID",ylabel="probe count")))
    save("habitat_vs_independent_coverage.png",lambda a:(a.scatter([x["any_hit_fraction"] for x in f],[x["habitat_depth_valid_fraction"] for x in f],c=["crimson" if x["joint_bad"] else "orange" if x["rgb_only"] else "steelblue" for x in f]),a.set(xlabel="independent hit fraction",ylabel="Habitat valid-depth fraction",title="Habitat versus independent coverage")))
    by={};
    for x in d["results"]:by.setdefault(x["variant"],[]).append(x["stats"]["depth_valid_fraction"])
    save("diagnostic_variant_outcomes.png",lambda a:(a.bar(list(by),[np.median(v) for v in by.values()]),a.tick_params(axis="x",rotation=20),a.set(title="Diagnostic-only variant depth outcomes",ylabel="median valid-depth fraction")))
    save("frame_0034_material_texture_audit.png",lambda a:text(a,"frame_0034 independent audit",["depth valid fraction: %.6f"%rgbf["habitat_depth_valid_fraction"],"independent hit fraction: %.6f"%rgbf["any_hit_fraction"],"actual PLY UV/material: none","external Ptex referenced: no",rgb["RGB_ONLY_FRAME_0034_MECHANISM"]]))
    save("failure_mechanism_by_frame.png",lambda a:(a.bar(["joint 32","frame_0034"],[32,1],color=["crimson","orange"]),a.set(title="Separated failure mechanisms",ylabel="frame count")))
    save("asset_repair_decision_summary.png",lambda a:text(a,"Repair feasibility gate",[c["OVERALL_ASSET_AUDIT_CLASSIFICATION"],r["REPAIR_FEASIBILITY"],r["recommended_next_task"],r["status"]]))
    report=f"""# Replica Scene Asset Geometry, Culling, Material and Render-Coverage Audit V1

## Result

`{r['status']}`

The upstream V2 diagnosis is preserved: 33 RGB exceptions, 32 depth exceptions, 32 joint exceptions, and one separate RGB-only frame (`frame_0034`). Texture cannot explain the 32 joint failures because their Habitat depth is zero and the independent CPU float64 triangle raycaster has zero valid hit fraction for every one of the 32, while normal frozen controls have a median hit fraction of {ray['aggregate']['normal_control_median_hit_fraction']:.6f}.

The direct V1 Habitat stage is `mesh.ply`, with unit scale, material shader, force-flat-shading and frustum culling. The source PLY has vertex RGB, stored vertex normals, no UVs and no material/texture assignment; its external Ptex payloads are not referenced by the direct stage. Habitat's Python binding exposes one active stage asset but not individual drawable enumeration.

## Independent geometry evidence

Reference A was the task-owned accelerated CPU BVH float64 Moller-Trumbore implementation. Reference B was a separate brute-force float64 Moller-Trumbore execution on four frozen key center rays; agreement was {ray['reference_b_agree']}/{ray['reference_b_checked']}. The 32 joint frames have zero independent any-hit, front-facing-hit and back-facing-only fractions. Therefore they meet the preregistered true coverage-gap indication, not a texture, culling, import or clipping claim.

`frame_0034` has sparse valid depth and a {rgbf['any_hit_fraction']:.6f} independent hit fraction. It is classified separately as `{rgb['RGB_ONLY_FRAME_0034_MECHANISM']}`. It does not explain the joint failures.

## Diagnostic variants and boundaries

The fixed 166 terminal fresh-subprocess diagnostic results used only task-owned variants marked `DIAGNOSTIC_ONLY_NOT_A_FORMAL_REPLICA_ASSET`: flat-untextured same geometry, reversed-face double sided diagnostic, connected-component flat IDs, and the existing official semantic mesh comparison. A/B/C retain zero depth on all joint failures. The semantic-mesh comparison does produce depth, but it is a distinct semantic asset, not a qualified RGB render replacement; it demonstrates that a geometry substitute would change the V1 asset contract rather than repair the frozen direct-Ply source. The initial first-frame capture had a task-owned NPY writer failure after observation but before any terminal JSON/depth record; it is preserved in the server log and the terminal schedule contains exactly 166 results. None was made a formal asset and none changes V1 staging, manifest, poses, scale, resolution, HFOV, near/far, height or split.

The conclusion is `{c['OVERALL_ASSET_AUDIT_CLASSIFICATION']}`. Repair feasibility is `{r['REPAIR_FEASIBILITY']}`. The only next task is `{r['recommended_next_task']}`.

No 300-frame rerender, dataset publication, Gaussian training, SAFER/CBF, Start-Safe/Risk-Aware/Recovery, or TUM execution occurred. Replica scene-asset qualification is not RGB-D dataset qualification, Gaussian mapping qualification, SAFER baseline qualification, or FAS-CBF evaluation. TUM remains `CLOSE_TUM_NAVIGATION_BENCHMARK_KEEP_SAFETY_CASE_STUDY`.
"""
    (ROOT/"report/REPORT_REPLICA_SCENE_ASSET_COVERAGE_AUDIT_V1.md").write_text(report,encoding="utf-8")

if __name__=="__main__":main()
