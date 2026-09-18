#!/usr/bin/env python3
"""Read-only, CPU-only diagnosis of frozen paired evidence; never invokes runtime."""
import csv
import hashlib
import json
import math
import random
import statistics as stats
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = json.loads((HERE / 'DIAGNOSTIC_PROTOCOL.json').read_text())
OUT = HERE / 'results'
NA = 'NOT_AVAILABLE'


def readj(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def writej(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def writecsv(name, rows):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise RuntimeError('EMPTY_OUTPUT_' + name)
    fields = list(rows[0])
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def percentile(values, fraction):
    ordered = sorted(values)
    idx = fraction * (len(ordered) - 1)
    lo, hi = math.floor(idx), math.ceil(idx)
    return ordered[lo] if lo == hi else ordered[lo] + (ordered[hi] - ordered[lo]) * (idx - lo)


def pearson(a, b):
    if len(a) != len(b) or len(a) < 2:
        return None
    am, bm = stats.mean(a), stats.mean(b)
    aa = sum((x-am)**2 for x in a)
    bb = sum((x-bm)**2 for x in b)
    return sum((x-am)*(y-bm) for x,y in zip(a,b)) / math.sqrt(aa*bb) if aa and bb else None


def ranks(a):
    order = sorted(range(len(a)), key=lambda i:a[i])
    result = [0.0]*len(a)
    j = 0
    while j < len(a):
        k = j+1
        while k < len(a) and a[order[k]] == a[order[j]]:
            k += 1
        for t in range(j,k):
            result[order[t]] = (j+k-1)/2 + 1
        j = k
    return result


def corr(a,b):
    return {'pearson':pearson(a,b), 'spearman':pearson(ranks(a),ranks(b))}


def role(role):
    if role == 'PRIMARY_NAVIGATION': return 'PRIMARY'
    if role == 'RETAINED_BACKUP': return 'BACKUP'
    if role == 'CERTIFIED_TERMINAL': return 'TERMINAL'
    return role


def runs(seq, kind):
    lengths=[]; n=0
    for x in seq:
        if x == kind: n+=1
        elif n: lengths.append(n); n=0
    if n: lengths.append(n)
    return max(lengths,default=0),len(lengths)


def seqdata(trace):
    seq=[role(x['action_role']) for x in trace]
    term=[i for i,x in enumerate(seq) if x=='TERMINAL']
    prim=[i for i,x in enumerate(seq) if x=='PRIMARY']
    lt,nt=runs(seq,'TERMINAL');lp,np=runs(seq,'PRIMARY')
    return {'first_primary_cycle':prim[0] if prim else NA,'first_terminal_cycle':term[0] if term else NA,
            'longest_primary_run':lp,'longest_terminal_run':lt,'number_primary_runs':np,'number_terminal_runs':nt,
            'last_cycle_leaving_terminal':max((i for i in range(len(seq)-1) if seq[i]=='TERMINAL' and seq[i+1]!='TERMINAL'),default=NA),
            'number_primary_to_terminal_transitions':sum(a=='PRIMARY' and b=='TERMINAL' for a,b in zip(seq,seq[1:])),
            'number_terminal_to_primary_transitions':sum(a=='TERMINAL' and b=='PRIMARY' for a,b in zip(seq,seq[1:])),
            'final_action_role':seq[-1] if seq else NA,
            'fraction_last_100_cycles_terminal':seq[-100:].count('TERMINAL')/min(len(seq),100),
            'fraction_last_100_cycles_primary':seq[-100:].count('PRIMARY')/min(len(seq),100),
            'terminal_fraction_first100':seq[:100].count('TERMINAL')/min(len(seq),100),
            'terminal_fraction_middle100':seq[200:300].count('TERMINAL')/len(seq[200:300]) if len(seq)>200 else NA,
            'primary_fraction_first100':seq[:100].count('PRIMARY')/min(len(seq),100)}


def mechanism(row):
    if not row['trace_complete']: return 'INSUFFICIENT_TYPED_EVIDENCE'
    if row['first_terminal_cycle'] != NA and row['first_terminal_cycle'] <= 100 and row['fraction_last_100_cycles_terminal'] >= .9 and row['longest_terminal_run'] >= 250: return 'EARLY_TERMINAL_LOCK_IN'
    if row['L3_fail_rate_new'] >= .5 and row['terminal_rate_new'] >= .5: return 'L3_FAIL_TERMINAL_DOMINANT'
    if row['L3_fail_rate_new'] >= .5 and row['retained_backup_rate_new'] <= .05 and row['terminal_rate_new'] >= .4: return 'BACKUP_SPARSE_AFTER_L3_FAILURE'
    if row['primary_count_new'] > 0 and row['terminal_rate_new'] >= .5: return 'PRIMARY_AVAILABLE_BUT_TERMINAL_DOMINANT'
    if row['primary_count_new'] > 0 and row['terminal_count_new'] > 0 and row['number_primary_to_terminal_transitions'] and row['number_terminal_to_primary_transitions']: return 'MIXED_ROUTING_LIVENESS_LOSS'
    return 'NO_CLEAR_ROUTING_MECHANISM'


def main():
    newroot=Path(P['post_repair_root']); oldroot=Path(P['old_v3_root']); ref=Path(P['reference_root'])
    assert ref.is_dir() and newroot.is_dir() and oldroot.is_dir()
    keyfiles=[newroot/x for x in ('POST_REPAIR_V3_FINAL_ACCEPTANCE.json','POST_REPAIR_V3_PAIRED_TRIAL_RESULTS.csv','POST_REPAIR_V3_PAIRED_PROGRESS_ANALYSIS.json','POST_REPAIR_V3_ACTIVE_RAW_EVIDENCE_MANIFEST.json')]
    keyfiles += [oldroot/x for x in ('V3_PAIRED_ANALYSIS_SUMMARY.json','V3_PAIRED_PER_PAIR_ANALYSIS.json')]
    before={str(x):digest(x) for x in keyfiles}
    final=readj(keyfiles[0]); manifest=readj(keyfiles[3]); oldsummary=readj(keyfiles[4])
    assert final['new_post_repair_scientific_result']==P['expected_new_verdict'] and oldsummary['final_decision']==P['expected_old_verdict']
    assert final['integrity_gate']=='PASS' and final['hard_safety_gate']=='PASS' and final['progress_ni_gate']=='FAIL'
    assert final['active_result_preanalysis_semantic_root_sha256']==manifest['semantic_root_sha256']==P['expected_semantic_root']
    assert manifest['exact_85_complete'] and len(manifest['exact_trial_order'])==85 and len(set(manifest['exact_trial_order']))==85
    assert final['total_cycles']==final['total_plant_commits']==final['total_trace_records']==final['total_trace_lock_records']==42500
    rows=list(csv.DictReader(keyfiles[1].open())); assert [int(x['trial_id']) for x in rows]==manifest['exact_trial_order']
    oldrows={int(x['trial_id']):x for x in readj(keyfiles[5])}; assert set(oldrows)==set(manifest['exact_trial_order'])
    master=[]; liveness=[]; bottom_details={}
    for rank,x in enumerate(rows):
        tid=int(x['trial_id']); newdir=newroot/'raw'/f'trial_{tid}'; olddir=oldroot/'raw'/f'trial_{tid}'
        ns=readj(newdir/'trial_summary.json'); os=readj(olddir/'trial_summary.json'); old=oldrows[tid]
        trace=[json.loads(line) for line in (newdir/'runtime_trace.jsonl').open()]
        seq=seqdata(trace); n=int(ns['completed_cycles']); on=int(os['completed_cycles'])
        assert len(trace)==n==500 and ns['trace_record_count']==n and len({z['cycle_index'] for z in trace})==n
        pc=int(ns['primary_navigation_commit_count']);bc=int(ns['retained_backup_commit_count']);tc=int(ns['terminal_commit_count'])
        assert pc+bc+tc+int(ns['alternative_navigation_commit_count'])==n
        op=int(os['primary_navigation_commit_count']);ob=int(os['retained_backup_commit_count']);ot=int(os['terminal_commit_count'])
        # Names, action roles and unit definitions are frozen; rates use each run's own completed-cycle denominator.
        delta=float(x['paired_progress_delta']); od=float(old['paired_progress_difference'])
        row={'trial_id':tid,'frozen_order_rank':rank,'historical_witness':tid in P['witness_ids'],
             'active_progress_new':float(x['active_progress']),'reference_progress':float(x['reference_progress']),'delta_new':delta,
             'hard_violation_new':x['active_hard_violation']=='True','min_hard_h_new':float(x['active_min_hard_clearance_q']),
             'completed_cycles_new':n,'primary_count_new':pc,'primary_rate_new':pc/n,'retained_backup_count_new':bc,'retained_backup_rate_new':bc/n,
             'terminal_count_new':tc,'terminal_rate_new':tc/n,'alternative_count_new':int(ns['alternative_navigation_commit_count']),
             'L3_pass_count_new':int(ns['L3_status_counts']['PASS']),'L3_fail_count_new':int(ns['L3_status_counts']['FAIL']),
             'L3_fail_rate_new':int(ns['L3_status_counts']['FAIL'])/n,
             'deadline_open_new':int(ns['deadline_status_counts']['OPEN']),'deadline_warning_new':int(ns['deadline_status_counts']['WARNING']),
             'deadline_expired_new':int(ns['deadline_status_counts']['EXPIRED']),**seq,
             'active_progress_old':float(old['active_hard']['normalized_progress']),'delta_old':od,
             'hard_violation_old':bool(old['active_hard']['violation_trial']),'min_hard_h_old':float(old['active_hard']['min_clearance_q']),
             'completed_cycles_old':on,'primary_count_old':op,'retained_backup_count_old':ob,'terminal_count_old':ot,
             'L3_fail_count_old':int(os['L3_status_counts']['FAIL']),
             'primary_rate_old':op/on,'backup_rate_old':ob/on,'terminal_rate_old':ot/on,
             'L3_fail_rate_old':int(os['L3_status_counts']['FAIL'])/on,
             'active_progress_change_new_minus_old':float(x['active_progress'])-float(old['active_hard']['normalized_progress']),
             'delta_change_new_minus_old':delta-od,'primary_rate_change':pc/n-op/on,
             'backup_rate_change':bc/n-ob/on,'terminal_rate_change':tc/n-ot/on,
             'L3_fail_rate_change':int(ns['L3_status_counts']['FAIL'])/n-int(os['L3_status_counts']['FAIL'])/on,
             'hard_outcome_change':f"{old['active_hard']['violation_trial']}->{x['active_hard_violation']}",
             'trace_complete':True}
        assert math.isclose(row['active_progress_new']-row['reference_progress'],delta,abs_tol=1e-12)
        assert math.isclose(row['reference_progress'],float(old['reference_hard']['normalized_progress']),abs_tol=1e-12)
        row['EVIDENCE_SUPPORTED_MECHANISM_CLASS']=mechanism(row)
        master.append(row)
        liveness.append({'trial_id':tid,'delta_new':delta,**seq})
        facts=[dict(z.get('facts',[])) for z in trace]
        bottom_details[tid]={'runtime_reasons':Counter(f.get('runtime_reason',NA) for f in facts),
                             'L1_reasons':Counter(f.get('canonical_l1_reason',NA) for f in facts),
                             'L2_reasons':Counter(f.get('canonical_l2_reason',NA) for f in facts)}
    after={str(x):digest(x) for x in keyfiles}; assert before==after
    writej('INPUT_AUTHORITY_MANIFEST.json',{'source_commit':P['source_commit'],'protocol_commit':'e883f3a5faed78fea91a21a078b50e7e60aa27e4',
           'post_repair_root':str(newroot),'post_repair_semantic_root':manifest['semantic_root_sha256'],'reference_root':str(ref),
           'old_v3_root':str(oldroot),'exact85_order_sha256':hashlib.sha256(json.dumps(manifest['exact_trial_order'],separators=(',',':')).encode()).hexdigest(),
           'key_authority_file_sha256_before':before,'key_authority_file_sha256_after':after,'INPUT_MUTATION_COUNT':0,
           'input_manifest_file_count':manifest['file_count'],'frozen_new_verdict':final['new_post_repair_scientific_result'],
           'frozen_old_verdict':oldsummary['final_decision'],'execution_counts':P['execution_counts']})
    writecsv('PER_TRIAL_PROGRESS_ROUTING.csv',master); writecsv('LIVENESS_SEQUENCE_DIAGNOSTICS.csv',liveness)
    ranked=sorted(master,key=lambda z:(z['delta_new'],z['trial_id']))
    fullmean=stats.mean(z['delta_new'] for z in master)
    writecsv('PROGRESS_DELTA_RANKING.csv',[{'rank':i+1,'trial_id':z['trial_id'],'delta_new':z['delta_new'],
             'mean_without_trial_i_minus_full_mean':(sum(q['delta_new'] for q in master)-z['delta_new'])/84-fullmean} for i,z in enumerate(ranked)])
    neg=sum(-z['delta_new'] for z in master if z['delta_new']<0)
    tails={str(k):{'trial_ids':[z['trial_id'] for z in ranked[:k]],'deltas':[z['delta_new'] for z in ranked[:k]],
                   'sum_delta':sum(z['delta_new'] for z in ranked[:k]),'mean_delta':stats.mean(z['delta_new'] for z in ranked[:k]),
                   'share_of_total_negative_magnitude':sum(-z['delta_new'] for z in ranked[:k] if z['delta_new']<0)/neg} for k in P['bottom_k']}
    deltas=[z['delta_new'] for z in master]
    rng=random.Random(P['bootstrap']['seed'])
    means=[stats.mean(deltas[rng.randrange(85)] for _ in range(85)) for _ in range(10000)]
    lo,hi=percentile(means,.025),percentile(means,.975)
    assert math.isclose(lo,P['expected_new_ci'][0],abs_tol=1e-14) and math.isclose(hi,P['expected_new_ci'][1],abs_tol=1e-14)
    tail={'negative_delta_trial_count':sum(x<0 for x in deltas),'zero_delta_trial_count':sum(x==0 for x in deltas),
          'positive_delta_trial_count':sum(x>0 for x in deltas),'negative_delta_trial_fraction':sum(x<0 for x in deltas)/85,
          'quantiles':{f'Q{q:02d}':percentile(deltas,q/100) for q in (5,10,25,50,75,90,95)},
          'mean':fullmean,'median':stats.median(deltas),'std_sample':stats.stdev(deltas),'MAD':stats.median(abs(x-stats.median(deltas)) for x in deltas),
          'standard_error':stats.stdev(deltas)/math.sqrt(85),'min':min(deltas),'max':max(deltas),
          'total_negative_magnitude':neg,'bottom_k':tails,'bootstrap_lower95':lo,'bootstrap_upper95':hi,
          'bootstrap_fraction_mean_le_margin':sum(x<=-.02 for x in means)/10000,'full_mean_minus_NI_margin':fullmean+.02}
    writej('NEGATIVE_TAIL_CONCENTRATION.json',tail)
    metrics=('terminal_rate_new','primary_rate_new','retained_backup_rate_new','L3_fail_rate_new','fraction_last_100_cycles_terminal')
    associations={m:corr(deltas,[z[m] for z in master]) for m in metrics}
    associations['longest_terminal_run_fraction']=corr(deltas,[z['longest_terminal_run']/z['completed_cycles_new'] for z in master])
    groups={label:{'n':len(g),'median_terminal_rate':stats.median(z['terminal_rate_new'] for z in g),
                   'median_primary_rate':stats.median(z['primary_rate_new'] for z in g),
                   'median_L3_fail_rate':stats.median(z['L3_fail_rate_new'] for z in g),
                   'median_backup_rate':stats.median(z['retained_backup_rate_new'] for z in g),
                   'median_longest_terminal_run_fraction':stats.median(z['longest_terminal_run']/z['completed_cycles_new'] for z in g)}
            for label,g in [('negative',[z for z in master if z['delta_new']<0]),('nonnegative',[z for z in master if z['delta_new']>=0])]}
    byterm=sorted(master,key=lambda z:(z['terminal_rate_new'],z['trial_id']))
    quartiles=[]
    for i in range(4):
        g=byterm[round(i*85/4):round((i+1)*85/4)]
        quartiles.append({'quartile':i+1,'n':len(g),'mean_delta':stats.mean(z['delta_new'] for z in g),
                          'median_delta':stats.median(z['delta_new'] for z in g),'negative_delta_fraction':sum(z['delta_new']<0 for z in g)/len(g)})
    writej('ROUTING_PROGRESS_ASSOCIATION.json',{'associations':associations,'negative_vs_nonnegative':groups,'terminal_rate_quartiles':quartiles,
           'interpretation':'descriptive association only; trial-level correlation is not causal proof'})
    bot=[]
    for z in ranked[:10]:
        tid=z['trial_id']; reasons=bottom_details[tid]
        bot.append({'trial_id':tid,'delta_new':z['delta_new'],'reference_progress':z['reference_progress'],'active_progress_new':z['active_progress_new'],
                    'terminal_rate':z['terminal_rate_new'],'primary_rate':z['primary_rate_new'],'backup_rate':z['retained_backup_rate_new'],
                    'L3_fail_rate':z['L3_fail_rate_new'],'longest_terminal_run':z['longest_terminal_run'],
                    'first_terminal_cycle':z['first_terminal_cycle'],'first_primary_cycle':z['first_primary_cycle'],
                    **{f'{stage}_{status}':readj(newroot/'raw'/f'trial_{tid}'/'trial_summary.json')[f'{stage}_status_counts'][status]
                       for stage in ('L1','C0','L2','L3') for status in ('PASS','FAIL','UNKNOWN')},
                    'top_L3_fail_reasons':NA,'arbitration_destination_counts':json.dumps(reasons['runtime_reasons'].most_common(),separators=(',',':')),
                    'terminal_route_reasons':json.dumps([(k,v) for k,v in reasons['runtime_reasons'].most_common() if 'TERMINAL' in k],separators=(',',':')),
                    'retained_backup_unavailable_reasons':NA,'backup_selected_reasons':json.dumps([(k,v) for k,v in reasons['runtime_reasons'].most_common() if 'BACKUP' in k],separators=(',',':')),
                    'boundary_count':0,'boundary_reasons':NA,'deadline_warning_context_count':z['deadline_warning_new'],
                    'deadline_expired_context_count':z['deadline_expired_new'],
                    'EVIDENCE_SUPPORTED_MECHANISM_CLASS':z['EVIDENCE_SUPPORTED_MECHANISM_CLASS']})
    writecsv('BOTTOM10_CAUSAL_DECOMPOSITION.csv',bot)
    oldchange=[{'trial_id':z['trial_id'],'delta_old':z['delta_old'],'delta_new':z['delta_new'],'delta_change':z['delta_change_new_minus_old'],
                'hard_old':z['hard_violation_old'],'hard_new':z['hard_violation_new'],
                'completed_cycles_old':z['completed_cycles_old'],'completed_cycles_new':z['completed_cycles_new'],
                'primary_count_old':z['primary_count_old'],'primary_count_new':z['primary_count_new'],
                'backup_count_old':z['retained_backup_count_old'],'backup_count_new':z['retained_backup_count_new'],
                'terminal_count_old':z['terminal_count_old'],'terminal_count_new':z['terminal_count_new'],
                'L3_fail_count_old':z['L3_fail_count_old'],'L3_fail_count_new':z['L3_fail_count_new'],
                'terminal_rate_change':z['terminal_rate_change'],'primary_rate_change':z['primary_rate_change'],
                'L3_fail_rate_change':z['L3_fail_rate_change']} for z in master]
    writecsv('OLD_VS_POST_REPAIR_PAIRED_CHANGE.csv',oldchange)
    witnesses=[{'trial_id':z['trial_id'],'old_hard_violation':z['hard_violation_old'],'old_min_h':z['min_hard_h_old'],
                'new_hard_violation':z['hard_violation_new'],'new_min_h':z['min_hard_h_new'],
                'old_delta':z['delta_old'],'new_delta':z['delta_new'],'delta_change':z['delta_change_new_minus_old'],
                'new_primary':z['primary_count_new'],'new_backup':z['retained_backup_count_new'],'new_terminal':z['terminal_count_new'],
                'new_L3_PASS':z['L3_pass_count_new'],'new_L3_FAIL':z['L3_fail_count_new'],'longest_terminal_run':z['longest_terminal_run'],
                'mechanism_class':z['EVIDENCE_SUPPORTED_MECHANISM_CLASS']} for z in master if z['trial_id'] in P['witness_ids']]
    writecsv('HISTORICAL_WITNESS_COMPARISON.csv',witnesses)
    oldnew={k:corr([z['delta_change_new_minus_old'] for z in master],[z[k] for z in master]) for k in ('terminal_rate_change','primary_rate_change','L3_fail_rate_change')}
    strong={k:abs(v['spearman'])>=.5 if v['spearman'] is not None else False for k,v in associations.items()}
    negtail=tails['5']['share_of_total_negative_magnitude']>=.5
    broad=tail['negative_delta_trial_fraction']>=.4 and not negtail
    oldnewstrong=any(abs(oldnew[k]['spearman'])>=.5 for k in ('terminal_rate_change','primary_rate_change') if oldnew[k]['spearman'] is not None)
    routingstrong=any(strong[k] for k in ('terminal_rate_new','primary_rate_new','L3_fail_rate_new'))
    classification=('D POST_REPAIR_ROUTING_SHIFT_ASSOCIATED_WITH_PROGRESS_CHANGE' if oldnewstrong else
                    'A TAIL_CONCENTRATED_ROUTING_ASSOCIATED_PROGRESS_NI_FAILURE' if negtail and routingstrong else
                    'B BROAD_ROUTING_ASSOCIATED_PROGRESS_NI_FAILURE' if broad and routingstrong else
                    'C HETEROGENEOUS_PROGRESS_FAILURE_WITH_WEAK_ROUTING_ASSOCIATION' if not routingstrong else
                    'E INSUFFICIENT_EVIDENCE_FOR_PROGRESS_CAUSAL_ATTRIBUTION')
    classes=Counter(z['EVIDENCE_SUPPORTED_MECHANISM_CLASS'] for z in bot)
    dominant=classes.most_common(1)[0]
    causal=('EVIDENCE_SUPPORTS_ROUTING_LIVENESS_MECHANISM_AS_PRIMARY_PROGRESS_FAILURE_HYPOTHESIS'
            if (negtail or broad) and routingstrong and dominant[1]>=6 and dominant[0] not in ('NO_CLEAR_ROUTING_MECHANISM','INSUFFICIENT_TYPED_EVIDENCE')
            and (not oldnewstrong or (oldnew['terminal_rate_change']['spearman'] is not None and oldnew['terminal_rate_change']['spearman']<0))
            else 'NO_SINGLE_CAUSAL_ROOT_ESTABLISHED')
    findings={'frozen_scientific_verdict':P['expected_new_verdict'],'frozen_hard_safety_gate':'PASS','negative_tail_concentrated':negtail,
              'broad_negative_distribution':broad,'strong_associations':strong,'old_new_routing_change_associated':oldnewstrong,
              'old_new_trial_level_comparability':'COMPARABLE_NAMED_PROGRESS_ACTION_ROLE_L3_WITH_OWN_CYCLE_DENOMINATOR',
              'old_new_associations':oldnew,'mean_delta_old':stats.mean(z['delta_old'] for z in master),
              'mean_delta_new':fullmean,'mean_delta_change':stats.mean(z['delta_change_new_minus_old'] for z in master),
              'median_delta_change':stats.median(z['delta_change_new_minus_old'] for z in master),
              'trials_improved':sum(z['delta_change_new_minus_old']>0 for z in master),
              'trials_worsened':sum(z['delta_change_new_minus_old']<0 for z in master),
              'trials_unchanged':sum(z['delta_change_new_minus_old']==0 for z in master),
              'bottom10_mechanism_counts':dict(classes),'diagnostic_classification':classification,'causal_root_claim':causal,
              'next_recommended_task':('DESIGN_BOUNDED_POST_REPAIR_V3_LIVENESS_ROUTING_REPAIR_V1' if causal.startswith('EVIDENCE_SUPPORTS') else 'DIAGNOSE_POST_REPAIR_V3_PROGRESS_HETEROGENEITY_V2'),
              'input_mutation_count':0,'execution_counts':P['execution_counts']}
    assert math.isclose(findings['mean_delta_old'],P['expected_old_mean'],abs_tol=1e-15)
    assert math.isclose(fullmean,P['expected_new_mean'],abs_tol=1e-15)
    writej('DIAGNOSTIC_FINDINGS.json',findings)
    report=OUT/'report'/'REPORT_POST_REPAIR_V3_PROGRESS_NI_FAILURE_DIAGNOSTIC_V1.md'
    report.parent.mkdir(parents=True,exist_ok=True)
    report.write_text(f"# Post-repair V3 progress NI failure diagnosis\n\n"
        f"Frozen scientific verdict: `{P['expected_new_verdict']}`; integrity and represented-map hard-safety gates remain PASS. "
        f"This is a post-hoc, read-only descriptive diagnosis, not a reanalysis of the gate.\n\n"
        f"## Distribution\n{tail['negative_delta_trial_count']}/85 negative trials ({tail['negative_delta_trial_fraction']:.3%}); "
        f"bottom-five negative magnitude share {tails['5']['share_of_total_negative_magnitude']:.3%}. "
        f"Sample SD {tail['std_sample']:.6f}, SE {tail['standard_error']:.6f}; frozen CI [{lo:.6f}, {hi:.6f}], "
        f"bootstrap mean <= -0.02 frequency {tail['bootstrap_fraction_mean_le_margin']:.3%}. "
        f"Mean is positive but frozen lower CI does not exceed the -0.02 margin. Bottom ten: "
        f"{[(z['trial_id'],round(z['delta_new'],6)) for z in ranked[:10]]}.\n\n"
        f"## Routing associations\n"
        + '\n'.join(f"- {m}: Pearson {v['pearson']}, Spearman {v['spearman']}" for m,v in associations.items())
        + f"\nThese correlations are descriptive, not causal. The trace does not expose per-attempt L3 FAIL reasons; they are `NOT_AVAILABLE`, not inferred. "
          f"Bottom-ten typed pattern counts: {dict(classes)}.\n\n"
        + f"## Old to new\nOld frozen verdict `{P['expected_old_verdict']}` remains unchanged. Mean paired delta "
          f"{findings['mean_delta_old']:.6f} to {fullmean:.6f}; mean change {findings['mean_delta_change']:.6f}; "
          f"improved/worsened/unchanged {findings['trials_improved']}/{findings['trials_worsened']}/{findings['trials_unchanged']}. "
          f"Like-named routing and L3 rates are compared using each run's completed-cycle denominator; old and new trial lengths differ. "
          f"Old/new change Spearman: {oldnew}. This does not establish that the repair caused the progress change.\n\n"
        + f"## Historical witnesses\n{witnesses}\n\n"
        + f"## Interpretation\nDiagnostic classification: `{classification}`. Causal-root boundary: `{causal}`. "
          f"A safety-certified terminal action is not itself unsafe or erroneous. No trial was excluded, no threshold tuned, no arm rerun, and no scientific verdict changed. "
          f"Next recommended task: `{findings['next_recommended_task']}`.\n")
    print(classification,causal)

if __name__=='__main__': main()
