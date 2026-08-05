#!/usr/bin/env python3
import json
from task_config_v2 import TASK_ROOT,atomic_json
def main():
 e=json.loads((TASK_ROOT/"paired_analysis/module_evidence_matrix.json").read_text()); cats=[x["category"] for x in e["evidence"].values()]
 if e["collision_regression"]:
  status="FAS_CBF_SAFETY_REGRESSION_ON_ACTIVATED_ETH3D_V2"; decision="DEBUG_FAS_CBF_SAFETY_REGRESSION_WITH_FROZEN_FAILURE_CASES"; nxt="DEBUG_FAS_CBF_SAFETY_REGRESSION_ON_FROZEN_ETH3D_V2_V1"
 elif sum(x in {"SUPPORTED","PROMISING"} for x in cats)>=2:
  status="PASS_ETH3D_FAS_CBF_STRESS_SCENARIO_ACTIVATION_V2"; decision="FREEZE_ACTIVATED_FAS_CBF_MODULE_EVIDENCE_AND_PROCEED_TO_FRAMEWORK_INTEGRATION"; nxt="INTEGRATE_FAS_CBF_FULL_FRAMEWORK_AND_FORMALIZE_THEORY_ABLATION_V1"
 else:
  status="PASS_ACTIVATED_ETH3D_BENCHMARK_WITHOUT_FAS_CBF_ADVANTAGE"; decision="DEBUG_OR_REVISE_FAS_CBF_MODULES_USING_FROZEN_PAIRED_CASES"; nxt="DIAGNOSE_FAS_CBF_MODULE_EFFECT_FAILURES_ON_FROZEN_ETH3D_V2_CASES_V1"
 out={"FINAL_STATUS":status,"FINAL_DECISION":decision,"ONLY_NEXT_TASK":nxt,"module_categories":cats}; atomic_json(TASK_ROOT/"report/final_decision.json",out); print(json.dumps(out,sort_keys=True)); return 0
if __name__=="__main__": raise SystemExit(main())
