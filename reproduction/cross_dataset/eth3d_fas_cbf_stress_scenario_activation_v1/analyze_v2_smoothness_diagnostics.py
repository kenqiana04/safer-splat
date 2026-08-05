#!/usr/bin/env python3
import json
import numpy as np
from task_config_v2 import METHODS,TASK_ROOT,atomic_json
def main():
 rows=json.loads((TASK_ROOT/"paired_analysis/per_run_compact_records.json").read_text()); out={}
 for m in METHODS:
  rr=[r for r in rows if r["method"]==m]
  out[m]={k:float(np.mean([float(x.get(k,0) or 0) for x in rr])) for k in ("control_tv","jerk_rms","intervention_switches","active_set_switch_rate")}
 atomic_json(TASK_ROOT/"paired_analysis/smoothness_diagnostics.json",{"role":"DIAGNOSTIC_ONLY","method_summary":out,"smoothness_penalty_added":False,"adaptive_margin_added":False})
 print("PASS_V2_SMOOTHNESS_DIAGNOSTICS"); return 0
if __name__=="__main__": raise SystemExit(main())
