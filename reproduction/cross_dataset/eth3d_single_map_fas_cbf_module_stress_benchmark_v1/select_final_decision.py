#!/usr/bin/env python3
from __future__ import annotations
import argparse,json
from pathlib import Path
from eth3d_controller_core import atomic_json

def main():
 p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);p.add_argument('--registry',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 e=json.loads(a.evidence.read_text());r=json.loads(a.registry.read_text());cats=[v['category'] for k,v in e['evidence'].items() if k!='H5_FULL'];qualified=sum(c in {'SUPPORTED','PROMISING'} for c in cats)
 if e['collision_regression']:
  case='C';status='FAS_CBF_MODULE_REGRESSION_DETECTED_ON_FROZEN_ETH3D_BENCHMARK';decision='DEBUG_FAS_CBF_MODULE_WITH_PAIRED_FAILURE_CASES';next_task='DEBUG_FAS_CBF_MODULE_REGRESSIONS_ON_FROZEN_ETH3D_CASES_V1'
 elif len(r['scenarios'])>=70 and qualified>=2:
  case='A';status='PASS_ETH3D_SINGLE_MAP_FAS_CBF_MODULE_STRESS_BENCHMARK_V1';decision='FREEZE_FAS_CBF_MODULE_EVIDENCE_AND_PROCEED_TO_FULL_FRAMEWORK_INTEGRATION';next_task='INTEGRATE_FAS_CBF_FULL_FRAMEWORK_AND_FORMALIZE_THEORY_ABLATION_V1'
 else:
  case='B';status='PASS_ETH3D_MAP_WITH_INSUFFICIENT_FAS_CBF_STRESS_ACTIVATION';decision='REPAIR_METHOD_INDEPENDENT_STRESS_SCENARIO_GENERATOR';next_task='REFINE_FAS_CBF_STRESS_SCENARIO_ACTIVATION_ON_FROZEN_ETH3D_MAP_V1'
 out={'case':case,'FINAL_STATUS':status,'FINAL_DECISION':decision,'ONLY_NEXT_TASK':next_task,'registry_count':len(r['scenarios']),'supported_or_promising_core_module_count':qualified,'module_categories':cats,'collision_regression':e['collision_regression']}
 atomic_json(a.output,out);print(json.dumps(out,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
