#!/usr/bin/env python3
"""Read-only provenance capture for the completed Pilot and immutable Reference."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

TASK = Path(__file__).resolve().parent
CHECKOUT = Path('/disk1/zlab/v3_repair_worktrees/safer-splat-post-repair-v3-paired-validation-protocol-v1')
PILOT_ROOT = Path('/disk1/zlab/v3_repair_records/cert_exec_identity_repair_pilot_v1_retry1_20260917')
REFERENCE_ROOT = Path('/disk1/zlab/formal_execution_records/formal_paired_v2_20260911')
OLD_V3_ANALYSIS_ROOT = Path('/disk1/zlab/v3_execution_records/active_runtime_paired_validation_v3_r1_retry1_20260915')
REUSE_LOCK = CHECKOUT / 'reproduction/validation/active_runtime_paired_validation_v3/V3_REFERENCE_REUSE_LOCK.json'
TRIALS = (66,74,9,12,73,26,79,31,54,18,19,88,38,8,28,29,0,24,37,98,27,91,2,78,76,80,82,99,56,21,33,44,14,16,61,23,6,96,43,47,51,69,59,63,42,13,4,93,39,49,97,60,83,36,67,86,3,81,87,71,20,53,7,58,40,89,94,68,48,92,34,72,17,32,62,41,52,64,22,84,11,57,1,46,77)
PILOT_HARD_ZERO = (
    'canonical_transition_drift_count', 'cert_exec_identity_mismatch_count',
    'l1_actual_continuity_mismatch_count', 'l2_next_l1_continuity_mismatch_count',
    'l2_next_l1_continuity_unknown_count', 'backup_token_continuity_mismatch_count',
    'selected_executed_identity_mismatch_count', 'forbidden_diagnostic_authority_event_count',
    'normative_identity_payload_incomplete_count', 'duplicate_plant_commit_count',
    'duplicate_trace_append_count', 'illegal_token_mutation_count', 'evidence_incomplete_count',
    'recovery_required_count', 'plant_outcome_unknown_count', 'nonfinite_count',
    'action_bound_violation_count', 'exception_count', 'cuda_oom_count',
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def semantic(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding='utf-8'))


def write_once(path: Path, value: object) -> None:
    if path.exists():
        raise RuntimeError('FROZEN_AUTHORITY_FILE_ALREADY_EXISTS:' + path.name)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')


def inventory(root: Path) -> dict:
    if not root.is_dir():
        raise RuntimeError('FROZEN_ROOT_MISSING:' + str(root))
    files = [{'path': p.relative_to(root).as_posix(), 'size': p.stat().st_size, 'sha256': sha(p)}
             for p in sorted(x for x in root.rglob('*') if x.is_file())]
    return {'file_count': len(files), 'files': files, 'semantic_root_sha256': semantic(files)}


def pilot_manifest() -> dict:
    summary = read(PILOT_ROOT / 'PILOT_COLLECTION_SUMMARY.json')
    if (summary['status'] != 'PASS_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_PILOT_V1'
            or summary['trials_completed'] != [5,15,25,35,45,55,65,75,85,95]
            or any(summary[key] != 5000 for key in ('completed_cycles', 'plant_commits', 'trace_records', 'trace_lock_records'))
            or summary['scientific_analysis_count'] != 0
            or any(summary['continuity_totals'].get(key, 0) != 0 or summary['integrity_totals'].get(key, 0) != 0
                   for key in PILOT_HARD_ZERO)):
        raise RuntimeError('PILOT_AUTHORITY_NOT_PASS_OR_HARD_ZERO_DRIFT')
    return {'schema': 'POST_REPAIR_V3_PILOT_AUTHORITY_MANIFEST_V1', 'root': str(PILOT_ROOT),
            'active_lock_sha256': sha(CHECKOUT / 'reproduction/pilot/certification_execution_state_identity_repair_pilot_v1/PILOT_EXECUTION_LOCK_LAUNCH_REPAIR_R2.json'),
            'summary_sha256': sha(PILOT_ROOT / 'PILOT_COLLECTION_SUMMARY.json'),
            'status': summary['status'], 'trials_completed': summary['trials_completed'],
            'completed_cycles': 5000, 'plant_commits': 5000, 'trace_records': 5000,
            'trace_lock_records': 5000, 'continuity_hard_zero': True, 'integrity_hard_zero': True,
            'scientific_analysis_count': 0, 'inventory': inventory(PILOT_ROOT)}


def reference_manifests() -> tuple[dict, dict]:
    reuse = read(REUSE_LOCK)
    if (reuse['formal_v2_result_root'] != str(REFERENCE_ROOT)
            or reuse['reference_arm_count'] != 85
            or reuse['reference_rerun_authorized'] is not False
            or reuse['reference_rerun_count'] != 0
            or reuse['all_immutable_complete_identity_compatible'] is not True
            or len(reuse['records']) != 85):
        raise RuntimeError('FROZEN_REFERENCE_REUSE_LOCK_INVALID')
    records = {int(row['trial_id']): row for row in reuse['records']}
    if set(records) != set(TRIALS):
        raise RuntimeError('FROZEN_REFERENCE_COHORT_NOT_EXACT_85')
    for tid, record in records.items():
        if record['arm'] != 'REFERENCE_CBF_QP' or not record['evaluation_eligible'] or not record['execution_complete']:
            raise RuntimeError('REFERENCE_RECORD_NOT_ELIGIBLE:' + str(tid))
        raw = REFERENCE_ROOT / record['accepted_attempt_relative_path'] / 'raw' / f'trial_{tid:03d}' / 'reference_cbf_qp'
        for name, expected in record['locked_files'].items():
            path = raw / name
            if path.stat().st_size != expected['size'] or sha(path) != expected['sha256']:
                raise RuntimeError('REFERENCE_LOCKED_FILE_DRIFT:' + str(tid) + ':' + name)
    old_pairs_path = OLD_V3_ANALYSIS_ROOT / 'V3_PAIRED_PER_PAIR_ANALYSIS.json'
    old_summary_path = OLD_V3_ANALYSIS_ROOT / 'V3_PAIRED_ANALYSIS_SUMMARY.json'
    old_pairs = read(old_pairs_path)
    old_summary = read(old_summary_path)
    if (len(old_pairs) != 85 or {int(p['trial_id']) for p in old_pairs} != set(TRIALS)
            or old_summary['final_decision'] != 'FAIL_V3_HARD_SAFETY_GATE'
            or old_summary['reference_hard_violation_trials'] != 0
            or old_summary['active_hard_violation_trials'] != 4):
        raise RuntimeError('HISTORICAL_V3_REFERENCE_OUTCOME_SOURCE_INVALID')
    pair_by_id = {int(p['trial_id']): p for p in old_pairs}
    values = []
    for tid in TRIALS:
        hard = pair_by_id[tid]['reference_hard']
        progress = hard['normalized_progress']
        if (hard['radius_q'] != 0.015 or hard['violation_trial'] is not False
                or hard['unknown_segment_count'] != 0 or not isinstance(progress, (int, float))
                or not math.isfinite(float(progress))):
            raise RuntimeError('REFERENCE_HARD_OR_PROGRESS_INVALID:' + str(tid))
        values.append({'trial_id': tid, 'normalized_progress': progress,
                       'hard_violation': False, 'unknown_segment_count': 0,
                       'minimum_hard_clearance_q': hard['min_clearance_q']})
    ref = {'schema': 'POST_REPAIR_V3_REFERENCE_AUTHORITY_MANIFEST_V1', 'root': str(REFERENCE_ROOT),
           'worktree': '/disk1/zlab/formal_execution_worktrees/safer-splat-formal-v2',
           'reuse_lock_sha256': sha(REUSE_LOCK), 'reference_records': 85,
           'reference_rerun_count_this_task': 0, 'reference_hard_violation_trials': 0,
           'source_v3_per_pair_sha256': sha(old_pairs_path),
           'source_v3_summary_sha256': sha(old_summary_path),
           'inventory': inventory(REFERENCE_ROOT)}
    outcomes = {'schema': 'POST_REPAIR_V3_FROZEN_REFERENCE_OUTCOMES_V1',
                'source_per_pair_path': str(old_pairs_path), 'source_per_pair_sha256': sha(old_pairs_path),
                'source_summary_sha256': sha(old_summary_path), 'trial_order': list(TRIALS),
                'reference_hard_violation_trials': 0, 'reference_unknown_trials': 0,
                'reference_rerun_count_this_task': 0, 'values': values,
                'values_semantic_sha256': semantic(values)}
    return ref, outcomes


def main() -> None:
    TASK.mkdir(parents=True, exist_ok=True)
    pilot = pilot_manifest()
    reference, outcomes = reference_manifests()
    write_once(TASK / 'PILOT_AUTHORITY_MANIFEST.json', pilot)
    write_once(TASK / 'REFERENCE_AUTHORITY_MANIFEST.json', reference)
    write_once(TASK / 'REFERENCE_FROZEN_OUTCOMES.json', outcomes)
    print(json.dumps({'pilot_files': pilot['inventory']['file_count'],
                      'pilot_semantic_root': pilot['inventory']['semantic_root_sha256'],
                      'reference_files': reference['inventory']['file_count'],
                      'reference_semantic_root': reference['inventory']['semantic_root_sha256'],
                      'reference_outcomes': len(outcomes['values'])}, sort_keys=True))


if __name__ == '__main__':
    main()
