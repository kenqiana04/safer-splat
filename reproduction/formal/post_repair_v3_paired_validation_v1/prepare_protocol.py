#!/usr/bin/env python3
"""One-time mechanical projection of frozen Pilot/V3 contracts; never a runtime entry point."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

CHECKOUT = Path('/disk1/zlab/v3_repair_worktrees/safer-splat-post-repair-v3-paired-validation-protocol-v1')
TASK = Path(__file__).resolve().parent
PILOT = CHECKOUT / 'reproduction/pilot/certification_execution_state_identity_repair_pilot_v1/PILOT_PROTOCOL.json'
V3 = CHECKOUT / 'reproduction/validation/active_runtime_paired_validation_v3/V3_PAIRED_VALIDATION_PROTOCOL.json'
OUT = TASK / 'POST_REPAIR_V3_PAIRED_PROTOCOL.json'
ORDER = [66,74,9,12,73,26,79,31,54,18,19,88,38,8,28,29,0,24,37,98,27,91,2,78,76,80,82,99,56,21,33,44,14,16,61,23,6,96,43,47,51,69,59,63,42,13,4,93,39,49,97,60,83,36,67,86,3,81,87,71,20,53,7,58,40,89,94,68,48,92,34,72,17,32,62,41,52,64,22,84,11,57,1,46,77]
WITNESSES = [22, 28, 57, 59]
RESULT_ROOT = '/disk1/zlab/v3_repair_records/post_repair_v3_paired_validation_v1_20260917'


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if OUT.exists():
        raise RuntimeError('PROTOCOL_ALREADY_FROZEN_REFUSE_REGENERATION')
    pilot = json.loads(PILOT.read_text(encoding='utf-8'))
    v3 = json.loads(V3.read_text(encoding='utf-8'))
    if (sha(PILOT) != '9fb0992b30edbb7a0a2ec48b646a8645eb93aee1805799170dd62a177a03abee'
            or v3['study_design']['execution_order'] != ORDER or len(ORDER) != len(set(ORDER))
            or len(ORDER) != 85):
        raise RuntimeError('FROZEN_INPUT_OR_85_ORDER_DRIFT')
    p = copy.deepcopy(pilot)
    p['schema'] = 'POST_REPAIR_V3_PAIRED_SCIENTIFIC_VALIDATION_PROTOCOL_V1'
    p['role'] = 'PROSPECTIVE_REPAIRED_ACTIVE_V3_ON_OUTCOME_EXPOSED_FROZEN_STONEHENGE_85'
    p['source_protocols'] = {'pilot_protocol_sha256': sha(PILOT), 'historical_v3_paired_protocol_sha256': sha(V3),
                             'formal_v2_reference_reuse_lock': 'reproduction/validation/active_runtime_paired_validation_v3/V3_REFERENCE_REUSE_LOCK.json'}
    p['cohort'].update({'source': 'FROZEN_V3_PRIMARY_85', 'trial_ids': ORDER, 'trial_order': ORDER,
                        'automatic_retry': False})
    p['future_result_root'] = RESULT_ROOT
    p['reference_authority'] = {
        'root': '/disk1/zlab/formal_execution_records/formal_paired_v2_20260911',
        'worktree': '/disk1/zlab/formal_execution_worktrees/safer-splat-formal-v2',
        'rerun_authorized': False, 'immutable_manifest': 'REFERENCE_AUTHORITY_MANIFEST.json',
        'frozen_outcomes': 'REFERENCE_FROZEN_OUTCOMES.json',
        'outcomes_source': '/disk1/zlab/v3_execution_records/active_runtime_paired_validation_v3_r1_retry1_20260915/V3_PAIRED_PER_PAIR_ANALYSIS.json',
        'exact_primary_count': 85, 'hard_violation_trials_required': 0,
    }
    p['pilot_authority'] = {
        'root': '/disk1/zlab/v3_repair_records/cert_exec_identity_repair_pilot_v1_retry1_20260917',
        'active_lock_sha256': '6be496873f56abcadfbc3fbed659224958ec09c0a63c5358104b067f713f5db1',
        'status': 'PASS_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_PILOT_V1',
        'trials': 10, 'cycles': 5000, 'plant_commits': 5000, 'trace_records': 5000,
        'immutable_manifest': 'PILOT_AUTHORITY_MANIFEST.json', 'scientific_analysis_count': 0,
    }
    p['scientific_question'] = {
        'hard_zero': 'active_hard_violation_trials==0 && active_only_hard_discordant_pairs==0 && unresolved_hard_safety_unknown_trials==0',
        'progress_noninferiority': 'paired_bootstrap_percentile95_lower>-0.02',
        'integrity': 'all_85_active_trials_locked_and_all_hard_zero_fields_zero',
        'old_v3_result_rewritten': False,
    }
    p['hard_safety_gate'] = {
        'oracle': 'FROZEN_V3_1_LIPSCHITZ_SWEPT_SEGMENT_REPRESENTED_MAP_PROXY',
        'source_helper': 'reproduction/pilot/active_runtime_pilot_v2/run_active_runtime_pilot_v2.py:certify_segment_clearance',
        'radius_q': 0.015, 'runtime_margin_q': 0.0, 'rho_seg_q': 0.0, 'epsilon': None,
        'negative_clearance_rule': 'ANY_EXACT_NEGATIVE_IS_UNSAFE_NO_CLAMP_OR_ULP_TOLERANCE',
        'active_violation_trials_required': 0, 'active_only_discordant_pairs_required': 0,
        'reference_violation_trials_required': 0, 'unresolved_unknown_trials_required': 0,
    }
    p['progress_noninferiority_gate'] = {
        'delta': 'normalized_progress_active_post_repair - normalized_progress_frozen_reference',
        'normalized_progress': '(d_start_to_goal - d_final_to_goal)/d_start_to_goal',
        'progress_clipping': 'NONE', 'pairs': 85, 'bootstrap': 'PAIRED_PERCENTILE',
        'resamples': 10000, 'seed': 20260911, 'confidence_interval': '95_PERCENT_PERCENTILE',
        'margin': -0.02, 'pass_comparator': 'STRICT_GREATER_THAN', 'equality_at_margin': 'FAIL',
    }
    p['historical_witnesses'] = WITNESSES
    p['historical_v3_frozen_result'] = {
        'analysis_status': 'ACTIVE_RUNTIME_V3_PAIRED_ANALYSIS_COMPLETE',
        'decision': 'FAIL_V3_HARD_SAFETY_GATE', 'paired_trials': 85,
        'active_hard_violation_trials': 4, 'active_only_discordant_pairs': 4,
        'reference_hard_violation_trials': 0, 'unresolved_unknown': 0,
        'witness_trials': WITNESSES, 'root_cause': 'COMMON_FLOAT32_REALIZATION_IDENTITY_GAP',
        'mean_progress_delta': 0.1828291222975633, 'median_progress_delta': 0.03983521018634763,
        'progress_bootstrap95': [0.12993732817874704, 0.23831804476014906],
        'progress_noninferiority': 'PASS', 'retroactive_reinterpretation_authorized': False,
    }
    p['exposure_statement'] = ('Stonehenge benchmark and 85-trial cohort are repeatedly exposed; '
                               'this post-repair runtime validation is prospective for the repaired implementation '
                               'but not a pristine holdout and does not support cross-scene generalization.')
    p['routing_diagnostics'] = {'fields': ['primary_navigation_commit_count', 'retained_backup_commit_count',
                                             'terminal_commit_count', 'alternative_navigation_commit_count',
                                             'assurance_boundary_count', 'L3_status_counts', 'deadline_status_counts'],
                                'role': 'DESCRIPTIVE_ONLY_NO_ROUTING_CONDITIONED_GATE_OR_TUNING'}
    p['analyzer_outputs'] = [
        'POST_REPAIR_V3_PAIRED_COLLECTION_SUMMARY.json', 'POST_REPAIR_V3_PAIRED_TRIAL_RESULTS.csv',
        'POST_REPAIR_V3_PAIRED_PROGRESS_ANALYSIS.json', 'POST_REPAIR_V3_PAIRED_HARD_SAFETY_ANALYSIS.json',
        'POST_REPAIR_V3_PAIRED_CONTINUITY_ANALYSIS.json', 'POST_REPAIR_V3_PAIRED_ROUTING_ANALYSIS.json',
        'POST_REPAIR_V3_PAIRED_WITNESS_ANALYSIS.json', 'POST_REPAIR_V3_PAIRED_FAILURE_REGISTER.csv',
        'report/REPORT_POST_REPAIR_V3_PAIRED_VALIDATION_V1.md',
    ]
    p['analysis_authority'] = {'during_freeze': False, 'during_collection': False,
                               'post_collection_only_after_85_immutable_locks': True,
                               'reference_rerun': False, 'scientific_oracle_feedback': False}
    p['per_trial_required_files'] = [name.replace('PILOT_RAW_EVIDENCE_LOCK.json', 'POST_REPAIR_V3_RAW_EVIDENCE_LOCK.json')
                                     for name in p['per_trial_required_files']]
    p['integrity_hard_zero_fields'] = p.pop('pilot_hard_zero_fields')
    p['continuity_denominator_contract'] = p.pop('pilot_denominator_contract')
    p['routing_contract'] = p.pop('pilot_routing_contract')
    p['decision_contract'] = {
        'integrity_or_unknown': 'BLOCK_POST_REPAIR_V3_PAIRED_VALIDATION_INTEGRITY',
        'hard_pass_ni_pass': 'PASS_POST_REPAIR_V3_PAIRED_VALIDATION_ON_FROZEN_STONEHENGE_BENCHMARK',
        'hard_fail_ni_pass': 'FAIL_POST_REPAIR_V3_HARD_SAFETY_GATE',
        'hard_pass_ni_fail': 'FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE',
        'hard_fail_ni_fail': 'FAIL_POST_REPAIR_V3_HARD_SAFETY_AND_PROGRESS_NI_GATES',
    }
    p['scientific_boundaries'] = {
        'scientific_analysis_performed_during_freeze': False, 'reference_rerun_enabled': False,
        'official100_enabled': False, 'formal_active_execution_enabled_during_freeze': False,
        'frozen_scientific_decision_remains': 'FAIL_V3_HARD_SAFETY_GATE',
        'post_repair_scientific_result_is_new': True, 'physical_world_safety_claim': False,
        'hard_realtime_guarantee_authorized': False, 'deployment_claim_authorized': False,
        'parameter_selection_authorized': False,
    }
    p['future_modes'] = ['--cpu-static-preflight', '--gpu-preflight', '--one TRIAL_ID', '--batch']
    p['first_launch_order'] = ['ASSERT_EXACT_BRANCH_AND_CLEAN_TREE', 'ASSERT_FUTURE_RESULT_ROOT_ABSENT',
                               'CPU_STATIC_PREFLIGHT', 'CPU_VALIDATOR', 'CREATE_RESULT_ROOT',
                               'LAUNCH_TMUX', 'GPU_PREFLIGHT', 'SERIAL_85_ACTIVE_BATCH',
                               'POST_COLLECTION_ANALYSIS_SEPARATE_AND_EXPLICIT']
    p.pop('success_status', None)
    p.pop('failure_status', None)
    p.pop('only_next_task_after_freeze', None)
    p.pop('upstream_smoke_evidence', None)
    TASK.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(p, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')
    print('POST_REPAIR_V3_PROTOCOL_PROJECTED_FROM_FROZEN_INPUTS')


if __name__ == '__main__':
    main()
