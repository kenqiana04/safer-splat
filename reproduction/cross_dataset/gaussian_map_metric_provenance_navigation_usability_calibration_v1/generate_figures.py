#!/usr/bin/env python3
"""Generate the twenty required static, source-backed audit figures."""
from __future__ import annotations
import json, math
from collections import Counter
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT=Path(__file__).resolve().parent; OUT=ROOT/"figures"; OUT.mkdir(exist_ok=True)
BLUE="#2F6B9A"; TEAL="#2A9D8F"; GOLD="#E9C46A"; ORANGE="#F4A261"; RED="#C85C5C"; GREY="#7A7A7A"; LIGHT="#E8EEF3"; PURPLE="#7B61A8"

def load(name): return json.loads((ROOT/name).read_text(encoding="utf-8"))
def finish(fig,ax,name,foot):
    ax.spines[["top","right"]].set_visible(False); fig.text(.01,.01,foot,fontsize=7,color="#555")
    fig.tight_layout(rect=(0,.045,1,1)); fig.savefig(OUT/name,dpi=180,bbox_inches="tight"); plt.close(fig)
def blank(title,xlabel="",ylabel="",size=(9,5)):
    fig,ax=plt.subplots(figsize=size); ax.set_title(title,loc="left",fontweight="bold",fontsize=13); ax.set_xlabel(xlabel); ax.set_ylabel(ylabel); return fig,ax

ledger=load("legacy_threshold_ledger/legacy_metric_threshold_ledger.json")["rows"]
conflicts=load("legacy_threshold_ledger/threshold_conflict_registry.json")["conflicts"]
maps=load("map_inventory/historical_map_inventory.json")["maps"]
avail={x["map_id"]:x["available"] for x in load("map_inventory/map_artifact_availability.json")["maps"]}
refs={x["map_id"]:x for x in load("reference_authority/reference_authority_registry.json")["rows"]}
risk=load("risk_coverage/risk_coverage_results.json")
spatial=load("spatial_missingness/spatial_missingness_results.json")["maps"]
parity=load("common_evaluator/native_common_semantic_parity.json")["rows"]
profiles=load("calibration/provisional_evidence_profiles.json")["profiles"]
budgets=load("physical_derivation/physical_map_error_budget.json")["maps"]
SHORT={"REPLICA_GT_FINE":"GT-FINE","TUM_SPLATFACTO_NEGATIVE":"TUM-Sf","REPLICA_SPLATFACTO":"Replica-Sf","TUM_SPLATAM_FORMAL":"TUM-ST","TUM_GAUSSIAN_SLAM":"TUM-GSLAM","REPLICA_SPLATAM_60":"Replica-ST","ARKITSCENES_M1_SPLATAM":"ARKit-M1","SAFER_OFFICIAL_FLIGHT":"SAFER-flight","SAFER_OFFICIAL_OLD_UNION2":"SAFER-union","SAFER_OFFICIAL_STATUES":"SAFER-statues","SAFER_OFFICIAL_STONEHENGE":"SAFER-stone"}

# 1 lineage
fig,ax=blank("Historical pipeline and gate lineage",size=(12,4)); ax.axis("off")
labels=["TUM\nmap routes","Replica\nmap routes","ARKitScenes\nM1 / PR #74","Legacy global\nhard gates","Metric provenance\naudit V1","Layered\nProtocol V2"]
for i,l in enumerate(labels):
    ax.text(i,0,l,ha="center",va="center",bbox=dict(boxstyle="round,pad=.5",fc=LIGHT if i<4 else "#DDF3EE",ec=BLUE),fontsize=9)
    if i<len(labels)-1: ax.annotate("",(i+.72,0),(i+.28,0),arrowprops=dict(arrowstyle="->",color=GREY,lw=1.5))
ax.set_xlim(-.6,len(labels)-.4); ax.set_ylim(-.8,.8)
finish(fig,ax,"historical_pipeline_and_gate_lineage.png","Old statuses are preserved; V2 changes interpretation and future evaluation, not history.")

# 2 formula vs threshold provenance
fcount=Counter(r["formula_source"] for r in ledger); tcount=Counter(r["threshold_source"] for r in ledger)
fig,ax=blank("Formula provenance is not threshold provenance","rows","source class",(11,6)); labels=list(fcount)+[x for x in tcount if x not in fcount]; y=np.arange(len(labels)); ax.barh(y,[fcount[x] for x in labels],label="formula rows",color=BLUE); ax.barh(y,[tcount[x] for x in labels],left=[fcount[x] for x in labels],label="threshold rows",color=ORANGE); ax.set_yticks(y,labels); ax.legend();
finish(fig,ax,"metric_formula_vs_threshold_provenance.png","One row contributes separately to formula-source and threshold-source counts.")

# 3 threshold dist
fig,ax=blank("Threshold-source distribution","ledger rows","threshold source",(10,5.5)); names,vals=zip(*tcount.most_common()); ax.barh(range(len(names)),vals,color=[ORANGE if n in {"PROJECT_HEURISTIC","UNDOCUMENTED_OR_UNRESOLVED"} else TEAL for n in names]); ax.set_yticks(range(len(names)),names); ax.invert_yaxis()
finish(fig,ax,"threshold_source_distribution.png","Heuristic/unresolved rows are audited, not retained as universal navigation gates.")

# 4 conflicts
top=sorted(conflicts,key=lambda x:x["variant_count"],reverse=True)[:14]; fig,ax=blank("Threshold version conflicts","numeric/comparator variants","metric",(10,5.5)); ax.barh(range(len(top)),[x["variant_count"] for x in top],color=PURPLE); ax.set_yticks(range(len(top)),[x["metric_name"] for x in top]); ax.invert_yaxis()
finish(fig,ax,"threshold_version_conflicts.png","A variant is not automatically a contradiction; applicability and provenance must be resolved.")

# 5 map inventory
fig,ax=blank("Historical map inventory and reference authority","map","evidence code",(12,5)); ids=[m["map_id"].replace("_","\n",1) for m in maps]; x=np.arange(len(ids)); refcode={"A_INDEPENDENT_METRIC_GEOMETRY":3,"B_INDEPENDENT_OBSERVABLE_RAYS":2,"C_INTERFACE_OR_UNRESOLVED":1}; ax.bar(x,[refcode[refs[m["map_id"]]["authority_level"]] for m in maps],color=[TEAL if avail[m["map_id"]] else GREY for m in maps]); ax.set_xticks(x,ids,rotation=45,ha="right",fontsize=7); ax.set_yticks([1,2,3],["C interface/unresolved","B observable rays","A metric geometry"])
finish(fig,ax,"map_inventory_and_reference_authority.png","Teal=artifact path currently accessible; grey=not available at the audited path.")

# 6 coverage decomposition
fig,ax=blank("Coverage definition decomposition",size=(11,4)); ax.axis("off"); parts=[("Reference\ntarget",BLUE),("Renderer\nalpha ≥ τ",ORANGE),("Finite positive\ndepth",TEAL),("Accepted set\nKτ",PURPLE),("Rejected =\nUNKNOWN",GREY)]
for i,(lab,c) in enumerate(parts):
    ax.text(i,0,lab,ha="center",va="center",color="white",bbox=dict(boxstyle="round,pad=.6",fc=c,ec="none"));
    if i<len(parts)-1: ax.annotate("",(i+.65,0),(i+.35,0),arrowprops=dict(arrowstyle="->",color="#444"))
ax.set_xlim(-.6,4.6); ax.set_ylim(-.7,.7)
finish(fig,ax,"coverage_definition_decomposition.png","Coverage is support at a renderer working point; conditional errors are computed only inside Kτ.")

# 7 risk curves
fig,ax=blank("Risk–coverage: complete curve only where observed","global coverage","conditional AbsRel",(9,5.5));
for item in risk["maps"]:
    pts=[p for p in item["alpha_grid"] if p.get("global_coverage") is not None and p.get("AbsRel") is not None]
    if not pts: continue
    xs=[p["global_coverage"] for p in pts]; ys=[p["AbsRel"] for p in pts]
    if item["complete_curve"]: ax.plot(xs,ys,"o-",label=item["map_id"],color=BLUE)
    else: ax.scatter(xs,ys,s=65,label=item["map_id"]+" (one point)")
ax.legend(fontsize=8); ax.grid(alpha=.25)
finish(fig,ax,"risk_coverage_curves.png","No interpolation: ARKit M1 was rerendered read-only on all 11 fixed alpha points; retained Replica summaries provide one point only.")

# 8 conditional errors
fig,ax=blank("Conditional error versus retained coverage","coverage","AbsRel",(8,5));
for item in risk["maps"]:
    for p in item["alpha_grid"]:
        if p.get("global_coverage") is not None and p.get("AbsRel") is not None:
            ax.scatter(p["global_coverage"],p["AbsRel"],s=28 if item["complete_curve"] else 90,label=item["map_id"] if not any(t.get_label()==item["map_id"] for t in ax.collections) else None)
ax.grid(alpha=.25); ax.legend(fontsize=8)
finish(fig,ax,"conditional_error_vs_coverage.png","Lower conditional error at lower coverage can reflect selective rejection, not better global geometry.")

# 9 parity
fig,ax=blank("Native/common renderer parity status","map","channel availability",(11,5)); ids=[p["map_id"] for p in parity]; y=np.arange(len(ids)); ax.barh(y,[1 if p["native_available"] else 0 for p in parity],label="native",color=BLUE); ax.barh(y,[1 if p["common_available"] else 0 for p in parity],left=[1 if p["native_available"] else 0 for p in parity],label="common",color=TEAL); ax.set_yticks(y,ids,fontsize=7); ax.set_xticks([0,1,2]); ax.legend(); ax.invert_yaxis()
finish(fig,ax,"native_vs_common_renderer_parity.png","Availability is not numeric parity. No favorable channel was selected.")

# 10 tolerances
fig,ax=blank("Multi-tolerance geometry evidence availability","tolerance (m)","map",(10,6)); ids=[m["map_id"] for m in maps[:7]]; mat=np.zeros((len(ids),6)); mat[0,:]=.5; ax.imshow(mat,aspect="auto",vmin=0,vmax=1,cmap=matplotlib.colors.ListedColormap(["#D9D9D9",GOLD,TEAL])); ax.set_xticks(range(6),[".01",".02",".03",".05",".10",".20"]); ax.set_yticks(range(len(ids)),ids,fontsize=8); ax.text(2.5,0,"support certificate only",ha="center",va="center",fontsize=8)
finish(fig,ax,"multi_tolerance_accuracy_completeness.png","Grey=retained bidirectional samples unavailable. Replica GT-FINE support proof is not an accuracy/completeness curve.")

# 11 spatial
usable=[x for x in spatial if "global_missing_fraction" in x]; fig,ax=blank("Observable spatial missingness at retained working point","missing fraction","map",(9,4.5)); yy=np.arange(len(usable)); ax.barh(yy,[x["global_missing_fraction"] for x in usable],label="global",color=BLUE); ax.barh(yy,[x["worst_5pct_frame_missing_fraction"] for x in usable],alpha=.45,label="worst 5% frames",color=RED); ax.set_yticks(yy,[x["map_id"] for x in usable]); ax.legend(); ax.invert_yaxis()
finish(fig,ax,"spatial_missing_component_summary.png","Frame summaries do not retain binary masks, so 2D/3D connected components are explicitly not evaluable.")

# 12 unknown policies
fig,ax=blank("Unknown-policy comparison",size=(9,4.5)); pol=["UNKNOWN→FREE","UNKNOWN→OCCUPIED","UNKNOWN→HIGH COST"]; vals=[3,1,2]; colors=[RED,TEAL,GOLD]; ax.bar(pol,vals,color=colors); ax.set_yticks([1,2,3],["conservative","contract-dependent","dangerous"]); ax.text(0,3.05,"FORBIDDEN",ha="center",fontweight="bold",color=RED)
finish(fig,ax,"unknown_policy_comparison.png","Unknown-as-high-cost remains diagnostic until a frozen planner/cost contract exists.")

# 13 global/nav
fig,ax=blank("Global evidence and navigation evaluability are orthogonal","global reconstruction evidence level","navigation evidence level",(8,6)); rc={"R0_INVALID":0,"R1_DIAGNOSTIC_RECONSTRUCTION":1,"R2_GLOBAL_RECONSTRUCTION_CANDIDATE":2,"R3_GLOBAL_DENSE_RECONSTRUCTION_QUALIFIED":3}; nc={"N0_NOT_EVALUABLE":0,"N1_NAVIGATION_DIAGNOSTIC_ONLY":1,"N2_LIMITED_DOMAIN_UNKNOWN_AWARE_NAVIGATION_CANDIDATE":2,"N3_LIMITED_DOMAIN_NAVIGATION_QUALIFIED":3}
coord_count=Counter((rc[p["reconstruction_axis"]],nc[p["navigation_axis"]]) for p in profiles); coord_seen=Counter()
for number,p in enumerate(profiles,1):
    base=(rc[p["reconstruction_axis"]],nc[p["navigation_axis"]]); idx=coord_seen[base]; coord_seen[base]+=1; span=coord_count[base]
    dx=((idx%4)-min(span,4)/2+.5)*.12 if span>3 else (idx-(span-1)/2)*.09; dy=(idx//4)*.11 if span>3 else (idx%2)*.055
    ax.scatter(base[0]+dx,base[1]+dy,s=80); ax.annotate(str(number),(base[0]+dx+.025,base[1]+dy+.025),fontsize=7)
ax.text(2.28,2.72,"\n".join(f"{i+1}  {SHORT[p['map_id']]}" for i,p in enumerate(profiles)),va="top",fontsize=7,bbox=dict(fc="white",ec=LIGHT,alpha=.92))
ax.set_xticks(range(4),["R0","R1","R2","R3"]); ax.set_yticks(range(4),["N0","N1","N2","N3"]); ax.grid(alpha=.3)
finish(fig,ax,"global_vs_navigation_conditioned_metrics.png","Profiles are provisional V2 evidence labels; they do not grant new map PASS status.")

# 14 budget
fig,ax=blank("Physical map-error budget decomposition",size=(11,4)); ax.axis("off"); labels=["d_ref − r_robot\n(reference margin)","− ε_loc","− ε_shape","− ε_sampled","− ε_stop","− ε_tracking","= B_map_available"]
for i,l in enumerate(labels):
    c=TEAL if i in {0,6} else GOLD; ax.text(i,0,l,ha="center",va="center",bbox=dict(boxstyle="round,pad=.45",fc=c,ec="none"),fontsize=8)
    if i<len(labels)-1: ax.annotate("",(i+.68,0),(i+.32,0),arrowprops=dict(arrowstyle="->",color=GREY))
ax.set_xlim(-.6,6.6); ax.set_ylim(-.8,.8)
finish(fig,ax,"physical_error_budget_decomposition.png","Missing allowance provenance yields PHYSICAL_ERROR_BUDGET_UNRESOLVED; p99 is not a certificate.")

# 15 axes
fig,ax=blank("Two-axis provisional map evidence profiles","Reconstruction axis","Navigation axis",(9,6));
coord_count=Counter((rc[p["reconstruction_axis"]],nc[p["navigation_axis"]]) for p in profiles); coord_seen=Counter()
for number,p in enumerate(profiles,1):
    base=(rc[p["reconstruction_axis"]],nc[p["navigation_axis"]]); idx=coord_seen[base]; coord_seen[base]+=1; span=coord_count[base]
    x=base[0]+(((idx%4)-min(span,4)/2+.5)*.13 if span>3 else (idx-(span-1)/2)*.10); y=base[1]+((idx//4)*.12 if span>3 else (idx%2)*.06)
    ax.scatter(x,y,s=90,color=TEAL if p["SAFETY_QUERY_COMPATIBLE"] else GREY); ax.annotate(str(number),(x+.025,y+.025),fontsize=7)
ax.text(2.28,2.72,"\n".join(f"{i+1}  {SHORT[p['map_id']]}" for i,p in enumerate(profiles)),va="top",fontsize=7,bbox=dict(fc="white",ec=LIGHT,alpha=.92))
ax.set_xticks(range(4),["R0","R1","R2","R3"]); ax.set_yticks(range(4),["N0","N1","N2","N3"]); ax.grid(alpha=.25)
finish(fig,ax,"two_axis_map_evidence_profiles.png","Query compatibility is shown by teal and is independent of both axes.")

# 16 reinterpretation
fig,ax=blank("Legacy failure reinterpretation",size=(12,4)); ax.axis("off"); boxes=[("Historical status\npreserved",BLUE),("Identify gate\nsource",ORANGE),("Global dense\nlegacy failure",PURPLE),("Navigation\nnot determined",GREY),("V2 requalification\nrequired",TEAL)]
for i,(l,c) in enumerate(boxes): ax.text(i,0,l,ha="center",va="center",color="white",bbox=dict(boxstyle="round,pad=.6",fc=c,ec="none"));
for i in range(4): ax.annotate("",(i+.7,0),(i+.3,0),arrowprops=dict(arrowstyle="->",color="#444"))
ax.set_xlim(-.6,4.6); ax.set_ylim(-.8,.8)
finish(fig,ax,"legacy_failure_reinterpretation.png","No old PR or formal status is rewritten.")

# 17 flow
fig,ax=blank("Protocol V2 decision flow",size=(11,5)); ax.axis("off"); nodes=[(.1,.72,"Identity / semantics\nintegrity gates"),(.5,.72,"Descriptive fixed-grid\nreconstruction"),(.9,.72,"R-axis profile"),(.3,.28,"Reference + robot + route"),(.7,.28,"Unknown-aware physical\nroute-tube budget"),(.9,.28,"N-axis profile")]
for x,y,l in nodes: ax.text(x,y,l,ha="center",va="center",transform=ax.transAxes,bbox=dict(boxstyle="round,pad=.45",fc=LIGHT,ec=BLUE),fontsize=9)
for a,b in [((.2,.72),(.4,.72)),((.6,.72),(.8,.72)),((.4,.28),(.6,.28)),((.8,.28),(.86,.28))]: ax.annotate("",b,a,xycoords=ax.transAxes,arrowprops=dict(arrowstyle="->",color=GREY))
finish(fig,ax,"protocol_v2_decision_flow.png","Integrity can stop qualification; attribution diagnostics may continue read-only.")

# 18 checklist
fig,ax=blank("New-dataset entry checklist before formal training",size=(11,6)); ax.axis("off"); items=["reference authority","units / poses / intrinsics","spatial split leakage","native/common semantics","unknown policy","robot + route contract","formula + threshold sources","physical error budget","seed + uncertainty","claim + publication boundary"]
for i,item in enumerate(items): x=.08+(i%2)*.48; y=.88-(i//2)*.17; ax.text(x,y,"□  "+item,transform=ax.transAxes,fontsize=11,va="center")
finish(fig,ax,"new_dataset_entry_checklist.png","Any missing item blocks the associated formal claim; it does not authorize repair or threshold relaxation.")

# 19 claims
fig,ax=blank("Claim boundary",size=(8,6)); ax.axis("off"); circles=[(.42,"Global reconstruction",LIGHT),(.30,"Limited-domain navigation","#DDF3EE"),(.18,"Physical route certificate","#FCECC9")]
for r,l,c in circles: ax.add_patch(plt.Circle((.5,.5),r,transform=ax.transAxes,fc=c,ec=BLUE,alpha=.9)); ax.text(.5,.5+r-.055,l,ha="center",va="center",transform=ax.transAxes,fontsize=9,fontweight="bold")
ax.text(.5,.46,"Each inner claim needs\nadditional independent evidence",ha="center",va="center",transform=ax.transAxes)
finish(fig,ax,"claim_boundary.png","Passing an outer descriptive layer never implies an inner physical-safety claim.")

# 20 priority
priority=[("Replica GT-FINE control",1),("Replica Splatfacto control",2),("TUM Splatfacto control",3),("ARKitScenes M1",4),("Replica SplaTAM",5),("TUM SplaTAM",6),("TUM Gaussian-SLAM",7)]
fig,ax=blank("Retrospective requalification priority","priority order","map / control",(9,5)); ax.barh(range(len(priority)),[8-x[1] for x in priority],color=[TEAL if "control" in x[0].lower() else BLUE for x in priority]); ax.set_yticks(range(len(priority)),[x[0] for x in priority]); ax.invert_yaxis()
finish(fig,ax,"requalification_priority.png","Controls precede candidates. Missing artifacts are marked NOT_EVALUABLE and are not retrained.")

required=["historical_pipeline_and_gate_lineage.png","metric_formula_vs_threshold_provenance.png","threshold_source_distribution.png","threshold_version_conflicts.png","map_inventory_and_reference_authority.png","coverage_definition_decomposition.png","risk_coverage_curves.png","conditional_error_vs_coverage.png","native_vs_common_renderer_parity.png","multi_tolerance_accuracy_completeness.png","spatial_missing_component_summary.png","unknown_policy_comparison.png","global_vs_navigation_conditioned_metrics.png","physical_error_budget_decomposition.png","two_axis_map_evidence_profiles.png","legacy_failure_reinterpretation.png","protocol_v2_decision_flow.png","new_dataset_entry_checklist.png","claim_boundary.png","requalification_priority.png"]
chart_map={n:{"sha256":__import__("hashlib").sha256((OUT/n).read_bytes()).hexdigest(),"bytes":(OUT/n).stat().st_size,"source":"compact tracked audit JSON/CSV","no_threshold_pass_fail_plot":True} for n in required}
(OUT/"chart_map.json").write_text(json.dumps({"figures":chart_map},indent=2,sort_keys=True)+"\n",encoding="utf-8")
print("FIGURES_PASS",len(required))
