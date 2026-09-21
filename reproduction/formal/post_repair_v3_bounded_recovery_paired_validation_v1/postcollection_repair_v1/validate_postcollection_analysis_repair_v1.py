#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys
from pathlib import Path

REPO=Path(__file__).resolve().parents[4]
TASK=REPO/'reproduction/formal/post_repair_v3_bounded_recovery_paired_validation_v1'
REPAIR=TASK/'postcollection_repair_v1'
PROTOCOL=TASK/'POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_PROTOCOL.json'
P=json.loads(PROTOCOL.read_text()); ROOT=Path(P['future_result_root']); TRIALS=tuple(P['cohort']['trial_order']); BASE='a06c08820eff5bd1f2a2fae7569f7d87bed9013c'; EXPECT_SOURCE='a06c08820eff5bd1f2a2fae7569f7d87bed9013c'
OUTPUTS=["POST_REPAIR_V3_BOUNDED_RECOVERY_COLLECTION_SUMMARY.json","POST_REPAIR_V3_BOUNDED_RECOVERY_TRIAL_RESULTS.csv","POST_REPAIR_V3_BOUNDED_RECOVERY_PROGRESS_ANALYSIS.json","POST_REPAIR_V3_BOUNDED_RECOVERY_HARD_SAFETY_ANALYSIS.json","POST_REPAIR_V3_BOUNDED_RECOVERY_CONTINUITY_ANALYSIS.json","POST_REPAIR_V3_BOUNDED_RECOVERY_ROUTING_ANALYSIS.json","POST_REPAIR_V3_BOUNDED_RECOVERY_RECOVERY_ANALYSIS.json","POST_REPAIR_V3_BOUNDED_RECOVERY_BOUNDARY_ANALYSIS.json","POST_REPAIR_V3_BOUNDED_RECOVERY_HISTORICAL_ACTIVE_DIAGNOSTIC.json","POST_REPAIR_V3_BOUNDED_RECOVERY_FAILURE_REGISTER.csv"]
def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def semantic(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def raw_manifest():
 rows=[]
 for p in sorted(x for x in (ROOT/'raw').rglob('*') if x.is_file()): rows.append({'path':p.relative_to(ROOT/'raw').as_posix(),'size':p.stat().st_size,'sha256':sha(p)})
 return {'schema':'POSTCOLLECTION_RAW_EVIDENCE_MANIFEST_V1','file_count':len(rows),'files':rows,'semantic_root_sha256':semantic(rows)}
def fail(msg): raise RuntimeError(msg)
def main():
 ap=argparse.ArgumentParser(); ap.add_argument('--phase',choices=('preanalysis','postanalysis'),required=True); a=ap.parse_args(); checks=[]
 def need(name,ok,detail): checks.append({'name':name,'pass':bool(ok),'detail':detail});
 need('collection_head_ancestor',subprocess.run(['git','merge-base','--is-ancestor',BASE,'HEAD'],cwd=REPO).returncode==0,'analysis HEAD retains a06c088 collection provenance as an ancestor')
 need('batch_complete',(ROOT/'BATCH_COMPLETE.json').is_file() and read(ROOT/'BATCH_COMPLETE.json').get('trial_order')==list(TRIALS) and read(ROOT/'BATCH_COMPLETE.json').get('trials_completed')==85,'BATCH_COMPLETE exact order and count')
 need('no_batch_stop',not (ROOT/'BATCH_STOP.json').exists(),'BATCH_STOP absent')
 marker=ROOT/'POST_REPAIR_V3_BOUNDED_RECOVERY_RETRY3_LAUNCH_AUTHORIZATION.json'; need('launch_marker',marker.is_file() and read(marker).get('source_head')==EXPECT_SOURCE,'Retry3 launch marker source HEAD')
 need('trial_complete_locks',all((ROOT/f'trial_{t}_complete.json').is_file() for t in TRIALS),'85 completion markers')
 need('runtime_trace_locks',all((ROOT/'raw'/f'trial_{t}'/'runtime_trace_lock.json').is_file() for t in TRIALS),'85 runtime_trace_lock files')
 need('reference_audit',read(REPAIR/'REFERENCE_FROZEN_OUTCOMES_AUTHORITY_AUDIT.json').get('trial_count')==85 and read(REPAIR/'REFERENCE_FROZEN_OUTCOMES_AUTHORITY_AUDIT.json').get('reuse_lock_pass') is True,'canonical frozen reference authority')
 dry=read(REPAIR/'ANALYZER_DRY_PARSE_AUDIT.json'); need('dry_parse',dry.get('status')=='PASS_ANALYZER_DRY_PARSE_85_OF_85' and dry.get('trials')==85,'read-only dry parse 85/85')
 hz=read(REPAIR/'HARD_ZERO_COVERAGE_AUDIT.json'); need('hard_zero_coverage',hz.get('coverage')==30 and hz.get('unsupported')==0 and set(hz.get('values',{}))>=set(P['hard_zero_integrity_gates']),'30/30 supported hard-zero gates plus formal safety oracle slot')
 sem=read(REPAIR/'SCIENTIFIC_SEMANTICS_EQUIVALENCE.json'); need('scientific_equivalence',sem.get('scientific_diff_count')==0 and sem.get('status')=='PASS_SCIENTIFIC_SEMANTICS_EQUIVALENCE','scientific contract unchanged except reference implementation binding')
 names=subprocess.check_output(['git','diff','--name-only',BASE],cwd=REPO,text=True).splitlines(); allowed_prefix='reproduction/formal/post_repair_v3_bounded_recovery_paired_validation_v1/'; need('task_scope',all(n.startswith(allowed_prefix) for n in names),'only task-local analyzer/evidence files changed')
 need('protected_runtime_diff',not subprocess.check_output(['git','diff',BASE,'--','reproduction/runtime','cbf','splat','dynamics','run.py'],cwd=REPO,text=True).strip(),'protected runtime diff zero')
 need('outputs_absent_preanalysis',not any((ROOT/n).exists() for n in OUTPUTS),'formal outputs absent before official analysis') if a.phase=='preanalysis' else None
 if a.phase=='postanalysis':
  need('outputs_present',all((ROOT/n).is_file() for n in OUTPUTS),'formal output set generated')
  summary=read(ROOT/'POST_REPAIR_V3_BOUNDED_RECOVERY_COLLECTION_SUMMARY.json'); need('analysis_status',summary.get('status') in ('PASS_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_ON_FROZEN_STONEHENGE_BENCHMARK','FAIL_POST_REPAIR_V3_BOUNDED_RECOVERY_PROGRESS_NONINFERIORITY_GATE','FAIL_POST_REPAIR_V3_BOUNDED_RECOVERY_HARD_SAFETY_GATE','FAIL_POST_REPAIR_V3_BOUNDED_RECOVERY_HARD_SAFETY_AND_PROGRESS_NI_GATES'),'formal decision is typed')
  need('raw_unchanged',read(REPAIR/'RAW_EVIDENCE_MANIFEST.json').get('semantic_root_sha256')==raw_manifest().get('semantic_root_sha256'),'raw evidence semantic manifest unchanged')
 else:
  manifest=raw_manifest(); (REPAIR/'RAW_EVIDENCE_MANIFEST.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n',encoding='utf-8')
 need('gpu1_available',not subprocess.run(['nvidia-smi','-i','1','--query-compute-apps=pid','--format=csv,noheader'],capture_output=True,text=True).stdout.strip(),'GPU1 has no task-owned compute process')
 result={'schema':'POSTCOLLECTION_ANALYSIS_REPAIR_VALIDATION_V1','phase':a.phase,'check_count':len(checks),'checks':checks,'status':'PASS_POSTCOLLECTION_ANALYSIS_REPAIR_PREVALIDATION' if a.phase=='preanalysis' and all(x['pass'] for x in checks) else ('PASS_POSTCOLLECTION_ANALYSIS_REPAIR_VALIDATION' if a.phase=='postanalysis' and all(x['pass'] for x in checks) else 'BLOCKED_POSTCOLLECTION_ANALYSIS_REPAIR_VALIDATION'),'collection_head':BASE,'retry3_root':str(ROOT),'gpu_run_count':0,'trial_rerun_count':0,'reference_rerun_count':0}
 (REPAIR/'VALIDATION_RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8'); print(json.dumps({'status':result['status'],'check_count':len(checks),'failed':[x['name'] for x in checks if not x['pass']]},sort_keys=True)); return 0 if result['status'].startswith('PASS_') else 2
if __name__=='__main__': raise SystemExit(main())
