#!/usr/bin/env python3
"""Smoke diagnostic only: native holdout rendering plus frozen common evaluator."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from _common import PYTHON, ROOT, SPLATNAV_REPO, atomic_json, load_json, task_env, update_stage


def main():
    summary=load_json(ROOT/"smoke"/"splatfacto_smoke_summary.json")
    export=load_json(ROOT/"canonical_export"/"splatfacto_smoke_canonical_export_summary.json")
    if summary["status"]!="SPLATFACTO_SMOKE_OPERATIONAL_PASS" or not export["status"].endswith("PASS"):
        atomic_json(ROOT/"common_evaluation"/"splatfacto_smoke_geometry_diagnostic.json",{"status":"NOT_AUTHORIZED_DUE_TO_SMOKE_OR_EXPORT"}); return
    code=r'''import json,sys,numpy as np
from pathlib import Path
from nerfstudio.utils.eval_utils import eval_setup
c,p,ck,step=eval_setup(Path(sys.argv[1]),test_mode="val")
out=[]
for camera,batch in p.datamanager.fixed_indices_eval_dataloader:
 r=p.model.get_outputs_for_camera(camera); d=r.get("depth"); rgb=r.get("rgb"); out.append({"depth_finite":bool(d is not None and np.isfinite(d.detach().float().cpu().numpy()).all()),"rgb_finite":bool(rgb is not None and np.isfinite(rgb.detach().float().cpu().numpy()).all())})
print(json.dumps({"checkpoint":str(ck),"checkpoint_step":step,"holdout_render_count":len(out),"all_depth_finite":all(x["depth_finite"] for x in out),"all_rgb_finite":all(x["rgb_finite"] for x in out)}))'''
    native=subprocess.run([str(PYTHON),"-B","-c",code,summary["runtime_config"]],cwd=str(SPLATNAV_REPO),env=task_env(),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=900)
    native_out=json.loads(native.stdout.splitlines()[-1]) if native.returncode==0 else {"error":native.stdout[-4000:]}
    common=subprocess.run([str(PYTHON),"-B",str(Path(__file__).resolve().with_name("evaluate_splatfacto_common_geometry.py")),"--stage","smoke"],cwd=str(SPLATNAV_REPO),env=task_env(),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=1200)
    geometry=load_json(ROOT/"common_evaluation"/"splatfacto_smoke_geometry_diagnostic.json") if common.returncode==0 else {"error":common.stdout[-4000:]}
    operational=bool(native.returncode==0 and native_out.get("holdout_render_count")==8 and native_out.get("all_depth_finite") and native_out.get("all_rgb_finite") and common.returncode==0 and geometry["metrics"]["nonfinite_prediction_count"]==0)
    result={"status":"SPLATFACTO_SMOKE_DIAGNOSTIC_COMPLETE" if operational else "SPLATFACTO_SMOKE_RENDER_EXECUTION_FAILURE","native_renderer":native_out,"common_evaluator":geometry,"geometry_is_diagnostic_only":True,"smoke_geometry_does_not_gate_pilot":True}
    atomic_json(ROOT/"common_evaluation"/"splatfacto_smoke_geometry_diagnostic.json",result)
    update_stage("SMOKE_DIAGNOSTIC_EVALUATION","TERMINAL_SCIENTIFIC_RESULT" if operational else "FAILED_INFRASTRUCTURE",result_status=result["status"])
    print(result["status"])
    if not operational: raise SystemExit(1)


if __name__=="__main__": main()
