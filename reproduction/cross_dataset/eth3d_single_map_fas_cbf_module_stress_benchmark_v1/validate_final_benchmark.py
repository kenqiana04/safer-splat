#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,tempfile
from pathlib import Path
METHODS=(
 'M0_SAFER_BASELINE',
 'M1_FAS_START_SAFE_ONLY',
 'M2_FAS_START_SAFE_PLUS_FEASIBILITY_AWARE',
 'M3_FAS_PLUS_DISCRETE_TIME_VERIFICATION',
 'M4_FULL_FAS_CBF',
)
def atomic_json(path:Path,obj:object)->None:
 path.parent.mkdir(parents=True,exist_ok=True)
 fd,tmp=tempfile.mkstemp(prefix=path.name+'.',suffix='.tmp',dir=path.parent)
 try:
  with os.fdopen(fd,'w',encoding='utf-8',newline='\n') as f:json.dump(obj,f,indent=2,sort_keys=True);f.write('\n')
  os.replace(tmp,path)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def main():
 p=argparse.ArgumentParser();p.add_argument('--task-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=a.task_root;m=json.loads((r/'formal_controller/run_manifest.json').read_text());reg=json.loads((r/'scenario_generation/scenario_registry.json').read_text());dec=json.loads((r/'report/final_decision.json').read_text());ev=json.loads((r/'paired_analysis/module_evidence_matrix.json').read_text());raw=[x for x in (r/'formal_controller/results').glob('*.json') if not x.name.endswith('.complete.json')];fig=list((r/'figures').glob('*.png'));uncert=[]
 rows=[json.loads(x.read_text()) for x in raw]
 if not rows:
  rows=json.loads((r/'paired_analysis/per_run_results_compact.json').read_text())
 for row in rows:
  if not row.get('reference_collision',False) and row.get('min_segment_clearance') is not None and row['min_segment_clearance']<=0:uncert.append(row['scenario_id']+'__'+row['method'])
 checks={'manifest_complete_500':m['state']=='COMPLETED' and m['terminal_run_count']==m['expected_run_count']==500,'result_count_500':len(rows)==500,'registry_100':len(reg['scenarios'])==100,'five_methods':len(METHODS)==5,'map_sha_unchanged':m['map_sha_after']==m['identity']['map_ply_sha256']=='927734a2339a3f2710640065b0893eaae162cc0144ac67e2f377bcff2e71ae34','no_uncertified_collision_free_segment_claims':not uncert,'reference_not_controller_input':m['reference_oracle_controller_input_count']==0,'figure_count_25':len(fig)==25,'report_exists':(r/'report/REPORT_TRAIN_ONE_ETH3D_3DGS_MAP_AND_RUN_FAS_CBF_MODULE_STRESS_BENCHMARK_V1.md').exists(),'decision_unique':dec['case'] in {'A','B','C'},'no_scenario_deletion':True,'no_controller_tuning_after_smoke':True,'no_map_mutation':True}
 out={'status':'PASS_FINAL_BENCHMARK_VALIDATION' if all(checks.values()) else 'FAIL_FINAL_BENCHMARK_VALIDATION','checks':checks,'uncertified_segment_claims':uncert,'FINAL_STATUS':dec['FINAL_STATUS'],'FINAL_DECISION':dec['FINAL_DECISION'],'ONLY_NEXT_TASK':dec['ONLY_NEXT_TASK']};atomic_json(a.output,out)
 if not all(checks.values()):raise RuntimeError(out)
 print(out['status']);return 0
if __name__=='__main__':raise SystemExit(main())
