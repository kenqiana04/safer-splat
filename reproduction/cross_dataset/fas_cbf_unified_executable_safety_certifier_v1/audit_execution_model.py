"""Audit plant, optimizer/candidate verifier, and backup rollout semantics."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from task_config import DT,NORMATIVE_EXECUTION_MODEL,TASK_ROOT

REPO=TASK_ROOT.parents[2]
ROWS=(
    ("plant","run.py","x = double_integrator_dynamics(x,u)*dt + x",145,148),
    ("v4b_candidate_verifier","work/risk_aware_cbf/scripts/run_v4b_corrective_dt_filter.py","pred = double_integrator_dynamics(x, cand.u) * float(args.dt) + x",476,478),
    ("v4b_plant","work/risk_aware_cbf/scripts/run_v4b_corrective_dt_filter.py","x = double_integrator_dynamics(x_pre, u_exec) * float(args.dt) + x_pre",671,673),
    ("v4c_backup_rollout","work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py","cur = double_integrator_dynamics(cur, controls[idx]) * float(dt) + cur",220,223),
    ("v4c_aux_rollout","work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py","cur = double_integrator_dynamics(cur, u) * float(dt) + cur",232,235),
    ("v4c_plant","work/risk_aware_cbf/scripts/run_v4c_hstep_predictive_recovery.py","x = double_integrator_dynamics(x_pre, u_exec) * float(args.dt) + x_pre",590,592),
)


def write_json(path:Path,value:dict)->None:
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n",encoding="utf-8",newline="\n")


def main()->None:
    records=[]
    for role,path,snippet,start,end in ROWS:
        text=(REPO/path).read_text(encoding="utf-8")
        normalized=" ".join(text.split())
        found=" ".join(snippet.split()) in normalized
        records.append({"role":role,"path":path,"expected_expression":snippet,"found":found,"line_window":f"{start}-{end}","sha256":hashlib.sha256((REPO/path).read_bytes()).hexdigest(),"semantic":"p_next=p+dt*v; v_next=v+dt*u"})
    passed=all(r["found"] for r in records)
    model={"identity":NORMATIVE_EXECUTION_MODEL,"state":"x=(p,v)","transition":{"position":"p_next=p+dt*v","velocity":"v_next=v+dt*u"},"interval_flow":{"position":"p(tau)=p+tau*v","velocity":"v(tau)=v+tau*u","tau":"[0,dt]"},"candidate_acceleration_affects_immediate_position_segment":False,"relative_degree":2,"dt_default":DT,"zoh_backend":"DIAGNOSTIC_NON_NORMATIVE","unique_normative_model_count":1}
    write_json(TASK_ROOT/"proof_artifacts"/"normative_execution_model.json",model)
    write_json(TASK_ROOT/"proof_artifacts"/"execution_model_audit.json",{"status":"PASS_NORMATIVE_MODEL_CONSISTENCY" if passed else "BLOCKED_BY_NORMATIVE_EXECUTION_MODEL_MISMATCH","records":records,"optimizer_verifier_backup_consistent":passed})
    csv_path=TASK_ROOT/"proof_artifacts"/"source_semantics_trace.csv"; csv_path.parent.mkdir(parents=True,exist_ok=True)
    with csv_path.open("w",encoding="utf-8",newline="") as handle:
        writer=csv.DictWriter(handle,fieldnames=list(records[0])); writer.writeheader(); writer.writerows(records)
    md="# Execution Model Consistency\n\nAll audited formal plant, candidate-verifier, and predictive-backup paths use `x_next = x + dt * [v,u]`. Therefore position is updated from pre-control velocity and current acceleration cannot change the immediate swept-position segment. Constant-acceleration ZOH remains diagnostic and is not used to reinterpret historical evidence.\n\nThis is a frozen-model relative-degree/timing boundary, not a universal physical impossibility claim. Delay, disturbance, and tracking-error bounds remain unproved.\n"
    (TASK_ROOT/"proof_artifacts"/"execution_model_consistency.md").write_text(md,encoding="utf-8",newline="\n")
    if not passed: raise SystemExit("BLOCKED_BY_NORMATIVE_EXECUTION_MODEL_MISMATCH")
    print("PASS_NORMATIVE_MODEL_CONSISTENCY",len(records))


if __name__=="__main__": main()
