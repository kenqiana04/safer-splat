#!/usr/bin/env python3
"""CPU-only validator for frozen-evidence diagnosis; does not run science arms."""
import csv
import hashlib
import importlib.util
import json
import math
import statistics
from pathlib import Path

H = Path(__file__).resolve().parent
P = json.loads((H/'DIAGNOSTIC_PROTOCOL.json').read_text())
O = H/'results'

def j(n): return json.loads((O/n).read_text())
def rows(n): return list(csv.DictReader((O/n).open()))
def need(c,msg):
    if not c: raise AssertionError(msg)
def close(a,b,msg): need(math.isclose(float(a),float(b),rel_tol=0,abs_tol=1e-12),msg)

def main():
    root=Path(P['post_repair_root']); manifest=json.loads((root/'POST_REPAIR_V3_ACTIVE_RAW_EVIDENCE_MANIFEST.json').read_text())
    final=json.loads((root/'POST_REPAIR_V3_FINAL_ACCEPTANCE.json').read_text())
    old=json.loads((Path(P['old_v3_root'])/'V3_PAIRED_ANALYSIS_SUMMARY.json').read_text())
    order=manifest['exact_trial_order']
    need(len(order)==len(set(order))==85,'EXACT85_ORDER')
    need(manifest['semantic_root_sha256']==P['expected_semantic_root'],'SEMANTIC_ROOT')
    need(final['new_post_repair_scientific_result']==P['expected_new_verdict'] and final['progress_ni_gate']=='FAIL','NEW_VERDICT')
    need(final['integrity_gate']==final['hard_safety_gate']=='PASS','INTEGRITY_HARD')
    need(old['final_decision']==P['expected_old_verdict'],'OLD_VERDICT')
    need(final['total_cycles']==final['total_plant_commits']==final['total_trace_records']==final['total_trace_lock_records']==42500,'CARDINALITY')
    # Revalidate the frozen raw manifest file by file; never touch source bytes.
    need(len(manifest['files'])==manifest['file_count']==769,'MANIFEST_FILE_COUNT')
    for item in manifest['files']:
        f=root/item['path']
        need(f.is_file() and f.stat().st_size==item['size'],'RAW_FILE_SIZE:'+item['path'])
        need(hashlib.sha256(f.read_bytes()).hexdigest()==item['sha256'],'RAW_FILE_HASH:'+item['path'])
    authority=j('INPUT_AUTHORITY_MANIFEST.json')
    need(authority['INPUT_MUTATION_COUNT']==0 and authority['key_authority_file_sha256_before']==authority['key_authority_file_sha256_after'],'INPUT_IMMUTABILITY')
    for name,sha in authority['key_authority_file_sha256_after'].items():
        need(hashlib.sha256(Path(name).read_bytes()).hexdigest()==sha,'KEY_AUTHORITY_HASH:'+name)
    expected=['PER_TRIAL_PROGRESS_ROUTING.csv','PROGRESS_DELTA_RANKING.csv','NEGATIVE_TAIL_CONCENTRATION.json',
              'ROUTING_PROGRESS_ASSOCIATION.json','OLD_VS_POST_REPAIR_PAIRED_CHANGE.csv','BOTTOM10_CAUSAL_DECOMPOSITION.csv',
              'HISTORICAL_WITNESS_COMPARISON.csv','LIVENESS_SEQUENCE_DIAGNOSTICS.csv','DIAGNOSTIC_FINDINGS.json',
              'report/REPORT_POST_REPAIR_V3_PROGRESS_NI_FAILURE_DIAGNOSTIC_V1.md']
    need(all((O/n).is_file() for n in expected),'OUTPUT_COVERAGE')
    master=rows('PER_TRIAL_PROGRESS_ROUTING.csv'); ranking=rows('PROGRESS_DELTA_RANKING.csv')
    liveness=rows('LIVENESS_SEQUENCE_DIAGNOSTICS.csv'); oldchange=rows('OLD_VS_POST_REPAIR_PAIRED_CHANGE.csv')
    need([int(x['trial_id']) for x in master]==order,'MASTER_ORDER')
    need(len(master)==len(ranking)==len(liveness)==len(oldchange)==85,'FULL85_TABLES')
    need(set(int(x['trial_id']) for x in ranking)==set(order),'RANKING_COHORT')
    source=list(csv.DictReader((root/'POST_REPAIR_V3_PAIRED_TRIAL_RESULTS.csv').open()))
    for a,b in zip(master,source):
        need(int(a['trial_id'])==int(b['trial_id']),'TRIAL_JOIN')
        close(a['delta_new'],b['paired_progress_delta'],'DELTA_REPRODUCTION')
        need(a['hard_violation_new']=='False','HARD_UNCHANGED')
    ds=[float(x['delta_new']) for x in master]
    close(statistics.mean(ds),P['expected_new_mean'],'MEAN')
    close(statistics.median(ds),P['expected_new_median'],'MEDIAN')
    close(min(ds),P['expected_new_min'],'MIN')
    close(max(ds),P['expected_new_max'],'MAX')
    tail=j('NEGATIVE_TAIL_CONCENTRATION.json'); findings=j('DIAGNOSTIC_FINDINGS.json')
    close(tail['bootstrap_lower95'],P['expected_new_ci'][0],'CI_LOWER')
    close(tail['bootstrap_upper95'],P['expected_new_ci'][1],'CI_UPPER')
    close(findings['mean_delta_old'],P['expected_old_mean'],'OLD_MEAN')
    need(findings['frozen_scientific_verdict']==P['expected_new_verdict'],'FINDING_VERDICT')
    need(findings['input_mutation_count']==0 and all(v==0 for v in findings['execution_counts'].values()),'NO_EXECUTION_SIDE_EFFECT')
    # Mechanism labels must exactly follow the frozen pre-outcome function.
    spec=importlib.util.spec_from_file_location('diagnosis',H/'diagnose_post_repair_v3_progress_ni_failure_v1.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    numeric=('first_terminal_cycle','longest_terminal_run','primary_count_new','terminal_count_new',
             'number_primary_to_terminal_transitions','number_terminal_to_primary_transitions')
    rates=('fraction_last_100_cycles_terminal','L3_fail_rate_new','terminal_rate_new','retained_backup_rate_new')
    for x in master:
        t={k:(int(x[k]) if x[k]!='NOT_AVAILABLE' else x[k]) for k in numeric}
        t.update({k:float(x[k]) for k in rates});t['trace_complete']=x['trace_complete']=='True'
        need(mod.mechanism(t)==x['EVIDENCE_SUPPORTED_MECHANISM_CLASS'],'MECHANISM_RULE')
    bottom=rows('BOTTOM10_CAUSAL_DECOMPOSITION.csv')
    need(len(bottom)==10 and [int(x['trial_id']) for x in bottom]==[int(x['trial_id']) for x in ranking[:10]],'BOTTOM10')
    need(len(rows('HISTORICAL_WITNESS_COMPARISON.csv'))==4,'WITNESSES')
    result={'status':'PASS_DIAGNOSE_POST_REPAIR_V3_PROGRESS_NI_FAILURE_V1','exact85':85,'raw_manifest_files_verified':769,
            'frozen_new_verdict':P['expected_new_verdict'],'frozen_old_verdict':P['expected_old_verdict'],
            'input_mutation_count':0,'execution_counts':P['execution_counts'],'mechanism_rules_verified':85}
    (O/'validation_result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(result['status'])

if __name__=='__main__': main()
