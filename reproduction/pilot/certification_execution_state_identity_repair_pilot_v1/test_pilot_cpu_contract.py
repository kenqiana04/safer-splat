#!/usr/bin/env python3
"""Task-local CPU fixtures: acceptance, denominator, aggregation, and fail-close."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

import run_cert_exec_identity_repair_pilot_v1 as pilot


def fixture(root: Path) -> Path:
    raw = root / 'raw/trial_15'
    raw.mkdir(parents=True)
    trace = [
        {'trial_id': 'STONEHENGE_TRIAL_015', 'cycle_index': 0, 'action_role': 'PRIMARY_NAVIGATION',
         'selected_action_identity': {'value': 'a0'}, 'executed_action_identity': {'value': 'a0'},
         'facts': [['canonical_l2_p_k2_identity', 'p1']]},
        {'trial_id': 'STONEHENGE_TRIAL_015', 'cycle_index': 1, 'action_role': 'RETAINED_BACKUP',
         'selected_action_identity': {'value': 'a1'}, 'executed_action_identity': {'value': 'a1'},
         'facts': [['canonical_l1_endpoint_identity', 'p1']]},
        {'trial_id': 'STONEHENGE_TRIAL_015', 'cycle_index': 2, 'action_role': 'CERTIFIED_TERMINAL',
         'selected_action_identity': {'value': 'a2'}, 'executed_action_identity': {'value': 'a2'},
         'facts': [['canonical_l1_endpoint_identity', 'unused']]},
    ]
    observations = [
        {'trial_id': 15, 'cycle_index': i, 'committed': True,
         'action_role': role, 'selected_action_identity': f'a{i}', 'executed_action_identity': f'a{i}'}
        for i, role in enumerate(('PRIMARY_NAVIGATION', 'RETAINED_BACKUP', 'CERTIFIED_TERMINAL'))
    ]
    continuity = pilot.smoke_module().executed_action_l2_next_l1_audit(trace, observations)
    assert continuity['l2_next_l1_continuity_applicable_count'] == 1
    assert continuity['l2_next_l1_continuity_not_applicable_count'] == 1
    assert continuity['l2_next_l1_continuity_unknown_count'] == 0
    row = {field: 0 for field in pilot.protocol()['per_trial_required_summary_fields']
           + pilot.protocol()['pilot_hard_zero_fields']}
    row.update(continuity)
    row.update({'trial_id': 15, 'startup_status': 'PASS', 'completed_cycles': 3,
                'plant_commit_count': 3, 'finalization_status': 'FINALIZED',
                'termination_reason': 'MAX_COMPLETED_CYCLES', 'hard_blocker': None,
                'process_exit_code': 0, 'trace_record_count': 3,
                'persisted_trace_line_count': 3, 'trace_lock_record_count': 3,
                'primary_navigation_commit_count': 1, 'retained_backup_commit_count': 1,
                'terminal_commit_count': 1, 'assurance_boundary_count': 0,
                'L1_status_counts': {'PASS': 3, 'FAIL': 0, 'UNKNOWN': 0},
                'C0_status_counts': {'PASS': 3, 'FAIL': 0, 'UNKNOWN': 0},
                'L2_status_counts': {'PASS': 3, 'FAIL': 0, 'UNKNOWN': 0},
                'L3_status_counts': {'PASS': 2, 'FAIL': 1, 'UNKNOWN': 0},
                'deadline_status_counts': {'OPEN': 3, 'WARNING': 1, 'EXPIRED': 1},
                'cycle_time_values': [0.1, 0.2, 0.3], 'stage_timing_observations': [],
                'gpu_trial_rerun': 0})
    pilot.write(raw / 'trial_summary.json', row)
    pilot.write(raw / 'runtime_trace_lock.json', {'record_count': 3})
    for name, rows in (('runtime_trace.jsonl', trace), ('cycle_observations.jsonl', observations)):
        (raw / name).write_text(''.join(json.dumps(item) + '\n' for item in rows), encoding='utf-8')
    for name, value in (('process_exit_code.txt', '0\n'), ('gpu_released.txt', 'true\n'),
                        ('stdout.log', ''), ('stderr.log', '')):
        (raw / name).write_text(value, encoding='utf-8')
    pilot.write(raw / 'PILOT_RAW_EVIDENCE_LOCK.json', pilot.trial_evidence_lock(raw))
    return raw


def main() -> None:
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        raw = fixture(root)
        assert pilot.complete_trial(root, 15)
        original = pilot.TRIALS
        pilot.TRIALS = (15,)
        try:
            result = pilot.summarize(root)
        finally:
            pilot.TRIALS = original
        assert result['status'] == 'PASS_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_PILOT_V1'
        assert result['continuity_totals']['l2_next_l1_continuity_not_applicable_count'] == 1
        assert result['deadline_status_totals']['EXPIRED'] == 1
        assert result['stage_status_totals']['L3']['FAIL'] == 1
        row = pilot.read(raw / 'trial_summary.json')
        row['l2_next_l1_continuity_mismatch_count'] = 1
        pilot.write(raw / 'trial_summary.json', row)
        pilot.write(raw / 'PILOT_RAW_EVIDENCE_LOCK.json', pilot.trial_evidence_lock(raw))
        assert not pilot.complete_trial(root, 15)
        row['l2_next_l1_continuity_mismatch_count'] = 0
        row['l2_next_l1_continuity_cross_cycle_rows'] = 500
        pilot.write(raw / 'trial_summary.json', row)
        pilot.write(raw / 'PILOT_RAW_EVIDENCE_LOCK.json', pilot.trial_evidence_lock(raw))
        assert not pilot.complete_trial(root, 15)
    assert all(x == 'PASS' for x in pilot.smoke_module().synthetic_executed_action_continuity_regression().values())
    print('PASS_CERT_EXEC_IDENTITY_REPAIR_PILOT_CPU_FIXTURES')


if __name__ == '__main__':
    main()
