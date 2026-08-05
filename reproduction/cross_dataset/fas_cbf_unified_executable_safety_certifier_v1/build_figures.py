"""Generate compact task figures with explicit evidence-status legends."""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image,ImageDraw,ImageFont

ROOT=Path(__file__).resolve().parent; OUT=ROOT/"figures"; OUT.mkdir(parents=True,exist_ok=True)
STATUS=[("DESIGN CONTRACT","#355C7D"),("IMPLEMENTED","#2A9D8F"),("PROVED UNDER ASSUMPTIONS","#1B7F3A"),("TESTED","#457B9D"),("DIAGNOSTIC ONLY","#E9C46A"),("UNPROVED","#E76F51"),("DEFERRED","#8D6A9F")]
FIGURES={
 "normative_execution_model.png":("Normative execution model",["p_next = p + dt v","v_next = v + dt u","p(tau) = p + tau v","current u cannot change immediate position segment"]),
 "candidate_level_u_exec.png":("Candidate-level U_exec",["ACTUATOR","CURRENT FULL QUERY","SWEPT SEGMENT","TERMINAL BACKUP","commit only at four-way intersection"]),
 "actuator_certificate.png":("Actuator admission",["componentwise inclusive hard bounds","no hidden clipping","new identity for clipped alternative","nonfinite => fail closed"]),
 "endpoint_vs_swept_segment.png":("Endpoint vs continuous segment",["endpoint-only: DIAGNOSTIC ONLY","interior collision can be missed","continuous minimum required"]),
 "analytic_segment_minimum.png":("Exact primitive segment minimum",["sphere: closest line parameter","quadratic ellipsoid: stationary point","full represented obstacle aggregation"]),
 "conservative_interval_branching.png":("Conservative interval bound",["signed distance is 1-Lipschitz","midpoint minus interval radius","safe / unsafe witness / inconclusive"]),
 "braking_backup_policy.png":("Deterministic braking policy",["clip(-v/dt, u_min, u_max)","never reverse velocity sign","no goal or reference input"]),
 "braking_terminal_set.png":("Braking-to-rest terminal set",["||v||_inf <= 1e-12","finite full map query","one certified zero-hold segment","sufficient, not maximal"]),
 "terminal_backup_witness.png":("Terminal-backup witness",["candidate segment","bounded braking segments","terminal certificate","zero-hold verification"]),
 "tail_witness_property.png":("Tail-witness property",["execute certified prefix exactly","remaining suffix stays valid","same model and snapshot","not global recursive feasibility"]),
 "unified_certifier_state_machine.png":("Unified certifier state machine",["diagnose -> generate -> actuator -> current","segment -> backup -> commit","every output returns next cycle"]),
 "typed_fail_closed_outputs.png":("Typed fail-closed outputs",["UNKNOWN / NONFINITE","UNSAFE / INCONCLUSIVE","BUDGET / INFRASTRUCTURE","never CERTIFIED_UNRECOVERABLE"]),
 "synthetic_case_matrix.png":("Synthetic analytic matrix",["15 preregistered cases","exact expected status and reason","no reference input","all tested"]),
 "segment_property_test_summary.png":("Segment property validation",["seed 20260805","10,000 cases","false-safe = 0","dense oracle is diagnostic only"]),
 "backup_property_test_summary.png":("Backup property validation",["2,000 braking cases","finite stop = 2,000","typed fail-closed = 1,000/1,000"]),
 "replica_map_smoke_summary.png":("Replica GT-FINE map smoke",["25 plant-free single-cycle states","2,285,656 primitives","reference online reads = 0","formal navigation rollouts = 0"]),
 "timing_breakdown.png":("Compatibility-smoke timing",["actuator / current / segment","backup / terminal / total","mean p50 p95 max retained","no real-time claim"]),
 "proof_status_map.png":("Proof-status map",["S1 B1 R1 F1 under assumptions","implementation consistency tested","deployment and global claims unproved"]),
 "claim_boundary.png":("Claim boundary",["candidate-level executable certification","represented Gaussian field only","no exact continuous U_exec","no full-stack superiority claim"]),
 "final_decision.png":("Final decision gate",["normative model consistent","formal segment backend available","synthetic false-safe = 0","bounded map smoke passed"]),
}


def font(size:int,bold:bool=False):
    candidates=["C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf","DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for path in candidates:
        try:return ImageFont.truetype(path,size)
        except OSError:pass
    return ImageFont.load_default()


def draw_figure(path:Path,title:str,items:list[str],subtitle:str="FAS-CBF Unified Executable Safety Certifier V1"):
    image=Image.new("RGB",(1600,900),"#F7F8FA"); draw=ImageDraw.Draw(image)
    draw.rectangle((0,0,1600,120),fill="#14213D"); draw.text((70,30),title,font=font(46,True),fill="white"); draw.text((72,88),subtitle,font=font(20),fill="#DDE7F2")
    n=len(items); width=1380/max(n,1); y=250
    for i,item in enumerate(items):
        x=110+i*width; box=(int(x),y,int(x+width-30),560)
        draw.rounded_rectangle(box,radius=18,fill="#FFFFFF",outline="#2A9D8F",width=4)
        words=item.split(); lines=[]; current=""
        for word in words:
            test=(current+" "+word).strip()
            if draw.textlength(test,font=font(24))>width-70 and current: lines.append(current); current=word
            else: current=test
        if current: lines.append(current)
        for j,line in enumerate(lines): draw.text((x+25,y+55+j*38),line,font=font(24, j==0),fill="#1E2A38")
        if i<n-1:
            draw.line((x+width-25,405,x+width+5,405),fill="#355C7D",width=5); draw.polygon([(x+width+5,405),(x+width-8,397),(x+width-8,413)],fill="#355C7D")
    x=45; y=735
    for label,color in STATUS:
        w=draw.textlength(label,font=font(16))+42
        if x+w>1560: x=45; y+=55
        draw.rounded_rectangle((x,y,x+w,y+34),radius=8,fill=color)
        draw.text((x+12,y+8),label,font=font(16,True),fill="white"); x+=w+12
    draw.text((45,850),"Scope: frozen Euler model + static represented Gaussian snapshot; reference oracle excluded online.",font=font(19),fill="#4B5563")
    image.save(path,"PNG",optimize=True)


for name,(title,items) in FIGURES.items(): draw_figure(OUT/name,title,items)
for path in sorted((ROOT/"synthetic_cases").glob("SYN-*.json")):
    case=json.loads(path.read_text(encoding="utf-8"))
    draw_figure(OUT/f"synthetic_{case['case_id']}.png",f"{case['case_id']}: {case['description']}",["INPUT CONTRACT",case["analytic_expected_status"],case["exact_reason_code"],"NO REFERENCE INPUT"],"Deterministic synthetic case")
print("PASS_FIGURE_BUILD",len(list(OUT.glob("*.png"))))
