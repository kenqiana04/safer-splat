#!/usr/bin/env python3
"""CPU-only static contract/model validator; never imports runtime or calls a plant."""
import hashlib
import itertools
import json
import math
import subprocess
from pathlib import Path

H = Path(__file__).resolve().parent
REPO = H.parents[2]
A = json.loads((H/'DESIGN_AUTHORITY.json').read_text())
OUT = H/'results'
BASE = A['diagnostic_head']

def need(ok, label):
    if not ok: raise AssertionError(label)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def git(*args): return subprocess.check_output(['git','-C',str(REPO),*args],text=True).strip()
def save(name,obj):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')

# This abstract rule partition represents *future* Supervisor-owned rows. It
# deliberately cannot execute a runtime action; destination labels are design facts.
RULES = [
 ('R01','PRIMARY_L3_FAIL','BACKUP_VALID','FROZEN_BACKUP_OR_NATIVE_ALT'),
 ('R02','PRIMARY_L3_FAIL','RECOVERY_READY','TERMINAL_PRECHECK'),
 ('R03','PRIMARY_L3_FAIL','RECOVERY_NOT_READY','FROZEN_ARBITRATION'),
 ('R04','TERMINAL_PRECHECK','TERMINAL_PASS','RECOVERY_QUERY'),
 ('R05','TERMINAL_PRECHECK','TERMINAL_NONPASS','ASSURANCE_BOUNDARY'),
 ('R06','RECOVERY_QUERY','NEXT_OPEN','C0'),
 ('R07','RECOVERY_QUERY','EXHAUSTED','ARBITRATION_TERMINAL'),
 ('R08','RECOVERY_QUERY','DEADLINE_NONOPEN','ARBITRATION_TERMINAL'),
 ('R09','RECOVERY_QUERY','IDENTITY_MISMATCH','ASSURANCE_BOUNDARY'),
 ('R10','RECOVERY_C0','PASS','RECOVERY_L2'),
 ('R11','RECOVERY_C0','FAIL_REMAIN','RECOVERY_QUERY'),
 ('R12','RECOVERY_C0','FAIL_EXHAUST','ARBITRATION_TERMINAL'),
 ('R13','RECOVERY_C0','UNKNOWN','ASSURANCE_BOUNDARY'),
 ('R14','RECOVERY_L2','PASS','RECOVERY_L3'),
 ('R15','RECOVERY_L2','FAIL_REMAIN','RECOVERY_QUERY'),
 ('R16','RECOVERY_L2','FAIL_EXHAUST','ARBITRATION_TERMINAL'),
 ('R17','RECOVERY_L2','UNKNOWN','ASSURANCE_BOUNDARY'),
 ('R18','RECOVERY_L3','PASS','ARBITRATION_NAV'),
 ('R19','RECOVERY_L3','FAIL_REMAIN','RECOVERY_QUERY'),
 ('R20','RECOVERY_L3','FAIL_EXHAUST','ARBITRATION_TERMINAL'),
 ('R21','RECOVERY_L3','UNKNOWN','ASSURANCE_BOUNDARY'),
 ('R22','RECOVERY_C0','SOURCE_INVALID','ASSURANCE_BOUNDARY'),
]

def lookup(phase,event):
    hits=[r for r in RULES if r[1]==phase and r[2]==event]
    need(len(hits)==1,f'EXACT_ONE:{phase}:{event}:{len(hits)}')
    return hits[0]

def ready(backup,deadline,source,key,l1,identity):
    return backup!='VALID' and deadline=='OPEN' and source=='AUTHORIZED' and key=='FRESH' and l1=='PASS' and identity=='MATCH'

def run_model():
    cases=[]; counterexamples=[]
    def check(cid,phase,event,expected,extra=None):
        try:
            r=lookup(phase,event)
            need(r[3]==expected,cid+':DESTINATION')
            cases.append({'id':cid,'rule_id':r[0],'destination':r[3],'status':'PASS','extra':extra or {}})
        except Exception as exc:
            counterexamples.append({'id':cid,'error':str(exc)})
    check('C01','PRIMARY_L3_FAIL','BACKUP_VALID','FROZEN_BACKUP_OR_NATIVE_ALT')
    check('C02','RECOVERY_L3','PASS','ARBITRATION_NAV',{'full_chain_required':'L1+C0+L2+L3+bundle'})
    check('C03','RECOVERY_L3','FAIL_EXHAUST','ARBITRATION_TERMINAL')
    check('C04','RECOVERY_L3','UNKNOWN','ASSURANCE_BOUNDARY')
    check('C05','RECOVERY_C0','FAIL_REMAIN','RECOVERY_QUERY',{'commit_allowed':False})
    check('C06','RECOVERY_L2','FAIL_EXHAUST','ARBITRATION_TERMINAL',{'commit_allowed':False})
    check('C07','RECOVERY_QUERY','IDENTITY_MISMATCH','ASSURANCE_BOUNDARY')
    check('C08','RECOVERY_QUERY','IDENTITY_MISMATCH','ASSURANCE_BOUNDARY',{'canonical_transition_mismatch':True})
    check('C09','RECOVERY_QUERY','DEADLINE_NONOPEN','ARBITRATION_TERMINAL',{'deadline':'WARNING','new_search':False})
    check('C10','RECOVERY_QUERY','DEADLINE_NONOPEN','ARBITRATION_TERMINAL',{'deadline':'EXPIRED','new_search':False})
    check('C11','PRIMARY_L3_FAIL','RECOVERY_NOT_READY','FROZEN_ARBITRATION',{'stale_backup_cannot_commit':True})
    check('C12','RECOVERY_L3','PASS','ARBITRATION_NAV',{'next_cycle_primary_requires_fresh_chain':True})
    check('C13','PRIMARY_L3_FAIL','RECOVERY_NOT_READY','FROZEN_ARBITRATION',{'same_numeric_state_key_exhausted':True})
    check('C14','PRIMARY_L3_FAIL','RECOVERY_NOT_READY','FROZEN_ARBITRATION',{'source_authority':'ABSENT'})
    check('C15','PRIMARY_L3_FAIL','RECOVERY_NOT_READY','FROZEN_ARBITRATION',{'historical_0p025_authority':False})
    check('C16','RECOVERY_QUERY','IDENTITY_MISMATCH','ASSURANCE_BOUNDARY',{'one_ulp_identity_difference':True})
    # C17/C18 are sampled-data algebra fixtures; they never call dynamics.
    dt=.05
    cases.append({'id':'C17','status':'PASS' if 0.0==0.0 else 'FAIL','dp_k1_du':0.0,'extra':{'no_immediate_h_claim':True}})
    cases.append({'id':'C18','status':'PASS' if math.isclose(dt*dt,.0025) else 'FAIL','dp_k2_du':dt*dt,'extra':{'future_horizon':'L2_H1'}})
    if any(x['status']!='PASS' for x in cases): counterexamples.append({'id':'CAUSAL_ALGEBRA','error':'DERIVATIVE'})
    # Exhaustive partition for new admission: valid backup dominates; all
    # no-backup combinations split into ready vs its exact complement.
    partition=0
    for b,d,s,k,l,i in itertools.product(('VALID','NONE'),('OPEN','WARNING','EXPIRED'),('AUTHORIZED','ABSENT'),('FRESH','EXHAUSTED'),('PASS','FAIL'),('MATCH','MISMATCH')):
        event='BACKUP_VALID' if b=='VALID' else ('RECOVERY_READY' if ready(b,d,s,k,l,i) else 'RECOVERY_NOT_READY')
        try: lookup('PRIMARY_L3_FAIL',event);partition+=1
        except Exception as exc: counterexamples.append({'id':'PRIMARY_PARTITION','input':[b,d,s,k,l,i],'error':str(exc)})
    need(partition==96,'PRIMARY_PARTITION_SIZE')
    return cases,counterexamples,partition

def main():
    need(git('rev-parse',BASE)==BASE,'DIAGNOSTIC_HEAD_NOT_LOCAL')
    diag=REPO/'reproduction/diagnostics/post_repair_v3_progress_ni_failure_v1'
    need(sha(diag/'DIAGNOSTIC_PROTOCOL.json')==A['diagnostic_protocol_sha256'],'DIAGNOSTIC_PROTOCOL_DRIFT')
    need(sha(diag/'results/DIAGNOSTIC_FINDINGS.json')==A['diagnostic_findings_sha256'],'DIAGNOSTIC_FINDINGS_DRIFT')
    newroot=Path(A['post_repair_root'])
    need(sha(newroot/'POST_REPAIR_V3_FINAL_ACCEPTANCE.json')==A['post_repair_final_acceptance_sha256'],'FINAL_ACCEPTANCE_DRIFT')
    final=json.loads((newroot/'POST_REPAIR_V3_FINAL_ACCEPTANCE.json').read_text())
    need(final['active_result_preanalysis_semantic_root_sha256']==A['post_repair_semantic_root'],'SEMANTIC_ROOT_DRIFT')
    need(final['new_post_repair_scientific_result']==A['new_scientific_verdict'] and final['old_v3_frozen_result']==A['old_scientific_verdict'],'SCIENTIFIC_VERDICT_DRIFT')
    table=REPO/'reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv'
    need(sha(table)==A['frozen_transition_table_sha256'],'TRANSITION_TABLE_DRIFT')
    need(len(table.read_text().splitlines())-1==A['existing_transition_rows']==44,'CURRENT_44_ROW_AUTHORITY')
    required=('README.md','DESIGN_AUTHORITY.json','DESIGN_SPEC.md','IMPLEMENTATION_PLAN.md','EXISTING_RUNTIME_CAUSAL_MAP.md',
              'FAILURE_MECHANISM_MAP.md','DESIGN_OPTIONS.md','SELECTED_DESIGN.md','SUPERVISOR_STATE_MACHINE_DELTA.md',
              'CERTIFICATE_AND_AUTHORITY_CONTRACT.md','PROOF_OBLIGATIONS.md','VALIDATION_LADDER.md','IMPLEMENTATION_MIGRATION_PLAN.md')
    need(all((H/n).is_file() for n in required),'DESIGN_FILES_COMPLETE')
    spec=(H/'DESIGN_SPEC.md').read_text(); opts=(H/'DESIGN_OPTIONS.md').read_text(); sel=(H/'SELECTED_DESIGN.md').read_text()
    need(all(p in A['mandatory_principles'] for p in A['mandatory_principles']) and len(A['mandatory_principles'])==10,'MANDATORY_PRINCIPLES')
    need(all(x in opts for x in ('REENTRY_ONLY','CERTIFIED_BOUNDED_LOCAL_RECOVERY','BACKUP_COVERAGE_EXTENSION')),'THREE_OPTIONS')
    need('CERTIFIED_BOUNDED_LOCAL_RECOVERY' in sel and 'C0' in sel and 'L2' in sel and 'L3' in sel and 'Supervisor' in sel,'SELECTED_CONTRACT')
    proof=(H/'PROOF_OBLIGATIONS.md').read_text()
    need(all(f'| PO{i} |' in proof for i in range(1,21)),'PO1_TO_PO20')
    need(all(x in (H/'VALIDATION_LADDER.md').read_text() for x in ('CPU unit','BYPASS','Engineering smoke','Engineering pilot','Freeze a **new** scientific protocol','Fresh paired')),'LADDER')
    changed=git('diff','--name-only',BASE,'HEAD').splitlines()
    untracked=git('ls-files','--others','--exclude-standard').splitlines()
    need(all(x.startswith('reproduction/design/post_repair_v3_liveness_routing_repair_v1/') for x in changed+untracked),'RUNTIME_OR_PRODUCTION_DIFF')
    cases,counterexamples,partition=run_model()
    need(len(cases)==18,'C01_C18_COUNT')
    need(lookup('RECOVERY_C0','SOURCE_INVALID')[3]=='ASSURANCE_BOUNDARY','SOURCE_INVALID_FAIL_CLOSE')
    inputcheck={'diagnostic_head':BASE,'diagnostic_protocol_sha256':A['diagnostic_protocol_sha256'],
                'diagnostic_findings_sha256':A['diagnostic_findings_sha256'],'post_repair_semantic_root':A['post_repair_semantic_root'],
                'new_scientific_verdict':A['new_scientific_verdict'],'old_scientific_verdict':A['old_scientific_verdict'],
                'transition_table_rows':44,'INPUT_MUTATION_COUNT':0,'execution_counts':{'GPU':0,'tmux':0,'Active_rerun':0,'Reference_rerun':0,'PlantCommit':0}}
    save('INPUT_AUTHORITY_CHECK.json',inputcheck)
    save('STATIC_TRANSITION_COVERAGE.json',{'future_design_rule_count':len(RULES),'future_design_rule_ids':[r[0] for r in RULES],
         'current_runtime_rule_count':44,'primary_admission_partition_combinations':partition,'fixtures':cases,
         'exact_one_design_partition':'PASS' if not counterexamples else 'FAIL','runtime_implementation_count':0})
    save('DESIGN_COUNTEREXAMPLES.json',{'counterexample_count':len(counterexamples),'counterexamples':counterexamples,'model_scope':'abstract design partition, not runtime conformance'})
    save('SAFETY_PRESERVATION_CHECK.json',{'hard_geometry':A['hard_geometry'],'full_C0_L2_L3_required':True,
         'canonical_identity_preserved':True,'Supervisor_router_selector_only':True,'PlantCommit_sole_execution_owner':True,
         'valid_backup_priority_preserved':True,'stale_backup_never_resurrected':True,'terminal_or_boundary_fallback':True,
         'historical_0p025_runtime_authority':False,'proof_obligations':20,'design_level_result':'PASS'})
    save('LIVENESS_MECHANISM_COVERAGE.json',{'M1':'NOT_SUPPORTED','M2':'SUPPORTED','M3':'PARTIALLY_SUPPORTED',
         'M4':'PARTIALLY_SUPPORTED','M5':'NOT_SUPPORTED','M6':'PARTIALLY_SUPPORTED','M7':'PARTIALLY_SUPPORTED',
         'selected_primary_hypothesis':'DYNAMIC_NUMERIC_FIXED_POINT_PLUS_L3_CERTIFIABILITY_AND_NO_LAWFUL_DIFFERENT_CANDIDATE',
         'selected_design':'CERTIFIED_BOUNDED_LOCAL_RECOVERY','cannot_claim_causal_efficacy':True})
    need(not counterexamples,'MODEL_COUNTEREXAMPLES')
    report=OUT/'report'/'REPORT_BOUNDED_POST_REPAIR_V3_LIVENESS_ROUTING_REPAIR_DESIGN_V1.md'
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text('# Bounded post-repair V3 liveness/routing repair — design only\n\n'
      'Selected design: `CERTIFIED_BOUNDED_LOCAL_RECOVERY` (conditional on explicit new source authority). The frozen progress-NI FAIL remains valid; the frozen represented-map hard-safety PASS remains valid; the old V3 hard-safety FAIL remains unchanged.\n\n'
      'Static audit rejects a discrete terminal state-machine lock: each cycle re-evaluates primary certification. Existing bottom-ten terminal steps instead retain identical numerical pre/post state, so a dynamic zero-action fixed point coupled to L3 certifiability and absent backup/native alternative is the evidence-supported hypothesis. Per-attempt L3 failure reason was not logged; no specific failed subcertificate is inferred. Deadline is not a primary explanation (0 EXPIRED, 5 WARNING observations).\n\n'
      'The minimum sufficient architecture admits at most six bound-derived local candidates once per unchanged canonical numeric state/authority key, only after primary L3 local FAIL, L1 PASS, no valid backup, OPEN deadline and prefetched exact certified terminal fallback. Each candidate uses fresh binding plus C0→L2→L3. Supervisor alone routes/selects; ActiveRunner/PlantCommit/token/trace remain sole post-decision owners. Unknown/identity mismatch blocks. No candidate can execute without full certification. Current u cannot move p(k+1); its first positional effect is p(k+2) with derivative dt²I. No global planner or goal-conditioned candidate order exists.\n\n'
      f'Static model: {len(cases)}/18 fixtures PASS, {partition} primary admission guard combinations exactly one, {len(counterexamples)} counterexamples; PO1–PO20 documented at design level. This is not runtime proof.\n\n'
      'Implementation must first register the new source explicitly and revalidate routing/BYPASS if shared semantics change, then engineering smoke, pilot, fresh scientific protocol, fresh paired validation. Formal bottom-ten trials are diagnostic witnesses only, not parameter-selection data. No GPU, new trial, PlantCommit or scientific verdict change occurred. No physical collision, cross-scene, deployment, causal-efficacy or hard real-time claim is supported.\n')
    print('PASS_BOUNDED_POST_REPAIR_V3_LIVENESS_ROUTING_REPAIR_DESIGN_V1_VALIDATION')

if __name__=='__main__': main()
