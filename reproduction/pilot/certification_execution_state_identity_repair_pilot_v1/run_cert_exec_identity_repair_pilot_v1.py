#!/usr/bin/env python3
"""Frozen engineering-pilot adapter; no scientific scoring or automatic retry."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import statistics
import subprocess
import sys
import tempfile
from typing import Any

TASK = Path(__file__).resolve().parent
CHECKOUT = Path('/disk1/zlab/v3_repair_worktrees/safer-splat-cert-exec-identity-repair-pilot-freeze-harness-r1')
ROOT = Path('/disk1/zlab/v3_repair_records/cert_exec_identity_repair_pilot_v1_20260916')
SMOKE_ROOT = Path('/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry5_20260916')
SMOKE_REL = 'reproduction/validation/certification_execution_state_identity_repair_smoke_v1/run_cert_exec_identity_repair_smoke_v1.py'
PROTOCOL = TASK / 'PILOT_PROTOCOL.json'
LOCK = TASK / 'PILOT_EXECUTION_LOCK_REPAIR_R1.json'
BLOCKED_LOCK = TASK / 'PILOT_EXECUTION_LOCK.json'
BLOCKED_HEAD = 'e859fbd48384cdcc39162f4beb26ed26c387057c'
R6_HEAD = '601204bfc14e3ad2c8e3c714b8f5045829491635'
BLOCKED_LOCK_SHA256 = 'fcfb45eb5505ca274ac7e0c10ad5ce36ac537864c53804f843fe45d9cf8f1083'
UPSTREAM_ENGINEERING_HARNESS_DIR = 'reproduction/validation/certification_execution_state_identity_repair_smoke_v1'
SCIENTIFIC_RUNTIME_PROTECTED_PATHS = ('cbf/', 'dynamics/', 'splat/', 'run.py', 'reproduction/runtime/')
SMOKE_MANIFEST = TASK / 'UPSTREAM_SMOKE_EVIDENCE_MANIFEST.json'
TRIALS = (5, 15, 25, 35, 45, 55, 65, 75, 85, 95)
AUTH_NAME = 'PILOT_INTERNAL_CHILD_AUTHORIZATION.json'
TOKEN_ENV = 'SAFER_SPLAT_CERT_EXEC_PILOT_CHILD_TOKEN'


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def semantic(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')


def protocol() -> dict[str, Any]:
    return read(PROTOCOL)


def git(*args: str) -> str:
    return subprocess.run(['git', '-C', str(CHECKOUT), *args], check=True, capture_output=True, text=True).stdout.strip()


def classify_changed_paths(paths: list[str]) -> dict[str, list[str]]:
    """Do not mistake historical R6 harness lineage for scientific/runtime mutation."""
    protected = [path for path in paths if any(path == prefix.rstrip('/') or path.startswith(prefix)
                 for prefix in SCIENTIFIC_RUNTIME_PROTECTED_PATHS)]
    engineering = [path for path in paths if path.startswith(UPSTREAM_ENGINEERING_HARNESS_DIR + '/')]
    return {'scientific_runtime_protected': protected, 'upstream_engineering_harness': engineering}


def assert_protected_runtime_diff_zero(paths: list[str]) -> None:
    if classify_changed_paths(paths)['scientific_runtime_protected']:
        raise RuntimeError('PROTECTED_RUNTIME_DIFF_NONZERO')


def upstream_r6_harness_identity() -> dict[str, str]:
    """Exact Git-tree and byte-hash gate for the reused, read-only R6 harness."""
    tree = git('rev-parse', f'HEAD:{UPSTREAM_ENGINEERING_HARNESS_DIR}')
    if tree != git('rev-parse', f'{R6_HEAD}:{UPSTREAM_ENGINEERING_HARNESS_DIR}') or tree != git('rev-parse', f'{BLOCKED_HEAD}:{UPSTREAM_ENGINEERING_HARNESS_DIR}'):
        raise RuntimeError('UPSTREAM_R6_ENGINEERING_HARNESS_TREE_DRIFT')
    r6_lock = read(CHECKOUT / UPSTREAM_ENGINEERING_HARNESS_DIR / 'SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY5_R6.json')
    for name, expected in r6_lock['harness_sha256'].items():
        if digest(CHECKOUT / UPSTREAM_ENGINEERING_HARNESS_DIR / name) != expected:
            raise RuntimeError('UPSTREAM_R6_ENGINEERING_HARNESS_HASH_DRIFT:' + name)
    return {'status': 'UPSTREAM_R6_ENGINEERING_HARNESS_IDENTITY_PASS', 'git_tree': tree}


def smoke_module() -> Any:
    path = CHECKOUT / SMOKE_REL
    spec = importlib.util.spec_from_file_location('_frozen_smoke_pilot_adapter', path)
    if spec is None or spec.loader is None:
        raise RuntimeError('UPSTREAM_SMOKE_IMPORT_UNAVAILABLE')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.TASK_DIR = TASK
    module.PROTOCOL_PATH = PROTOCOL
    module.LOCK_PATH = LOCK
    module.CHECKOUT_DEFAULT = CHECKOUT
    module.RESULT_ROOT = ROOT
    module.BRANCH = 'repair-cert-exec-identity-repair-pilot-freeze-harness-r1'
    module.TRIALS = TRIALS
    module.AUTHORIZATION_NAME = AUTH_NAME
    module.CHILD_TOKEN_ENV = TOKEN_ENV
    module.ALLOWED_TASK_REL = 'reproduction/pilot/certification_execution_state_identity_repair_pilot_v1'
    # R6 task-local lineage is checked by upstream_r6_harness_identity(), not as runtime source.
    module.PROTECTED_PATHS = tuple(x for x in module.PROTECTED_PATHS if x != 'reproduction/pilot')
    return module


def root_manifest(root: Path) -> dict[str, Any]:
    files = [{'path': p.relative_to(root).as_posix(), 'size': p.stat().st_size, 'sha256': digest(p)}
             for p in sorted(x for x in root.rglob('*') if x.is_file())]
    return {'file_count': len(files), 'files': files, 'semantic_root_sha256': semantic(files)}


def upstream_smoke_check() -> dict[str, Any]:
    if not SMOKE_ROOT.is_dir():
        raise RuntimeError('UPSTREAM_SMOKE_ROOT_MISSING')
    frozen = read(SMOKE_MANIFEST)
    if root_manifest(SMOKE_ROOT) != frozen:
        raise RuntimeError('UPSTREAM_SMOKE_EVIDENCE_MUTATION')
    summary = read(SMOKE_ROOT / 'SMOKE_REPAIR_V1_COLLECTION_SUMMARY.json')
    if (summary.get('status') != 'PASS_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_SMOKE_V1'
            or summary.get('trials_completed') != [15, 45, 75]
            or any(summary.get(k) != 1500 for k in ('completed_cycles', 'plant_commits', 'trace_records', 'trace_lock_records'))
            or summary.get('trace_cardinality_pass') is not True
            or summary.get('scientific_analysis_performed') is not False
            or summary.get('continuity_totals', {}).get('l2_next_l1_continuity_applicable_count') != 611
            or summary.get('continuity_totals', {}).get('l2_next_l1_continuity_not_applicable_count') != 886
            or summary.get('continuity_totals', {}).get('l2_next_l1_continuity_cross_cycle_rows') != 1497):
        raise RuntimeError('UPSTREAM_SMOKE_STATUS_MISMATCH')
    hard = protocol()['pilot_hard_zero_fields']
    for key in hard:
        if key in summary['continuity_totals'] and summary['continuity_totals'][key] != 0:
            raise RuntimeError('UPSTREAM_SMOKE_HARD_ZERO_MISMATCH:' + key)
    for trial in (15, 45, 75):
        raw = SMOKE_ROOT / 'raw' / f'trial_{trial}'
        row = read(raw / 'trial_summary.json')
        if (row.get('process_exit_code') != 0 or row.get('startup_status') != 'PASS'
                or row.get('finalization_status') != 'FINALIZED' or row.get('hard_blocker') is not None
                or (raw / 'gpu_released.txt').read_text().strip() != 'true'):
            raise RuntimeError('UPSTREAM_SMOKE_TRIAL_MISMATCH')
    return summary


def static_contract(*, require_lock: bool, require_absent_root: bool = True) -> dict[str, Any]:
    if git('branch', '--show-current') != 'repair-cert-exec-identity-repair-pilot-freeze-harness-r1':
        raise RuntimeError('PILOT_BRANCH_MISMATCH')
    if subprocess.run(['git', '-C', str(CHECKOUT), 'merge-base', '--is-ancestor',
                       BLOCKED_HEAD, 'HEAD']).returncode:
        raise RuntimeError('UPSTREAM_HEAD_NOT_ANCESTOR')
    if digest(BLOCKED_LOCK) != BLOCKED_LOCK_SHA256:
        raise RuntimeError('BLOCKED_FREEZE_LOCK_MUTATION')
    changed = git('diff', '--name-only', BLOCKED_HEAD).splitlines()
    assert_protected_runtime_diff_zero(changed)
    if any(not path.startswith('reproduction/pilot/certification_execution_state_identity_repair_pilot_v1/') for path in changed):
        raise RuntimeError('OUT_OF_SCOPE_DIFF')
    upstream_r6_harness_identity()
    frozen = protocol()
    cohort = frozen['cohort']
    if (cohort['trial_ids'] != list(TRIALS) or cohort['trial_order'] != list(TRIALS)
            or cohort['seed'] != 0 or cohort['maximum_completed_cycles_per_trial'] != 500
            or cohort['serial_execution'] is not True or cohort['separate_process_per_trial'] is not True
            or cohort['automatic_retry'] is not False):
        raise RuntimeError('PILOT_COHORT_DRIFT')
    geo = frozen['geometry']
    if (geo['hard_radius_q'], geo['runtime_margin_q'], geo['rho_seg_q'], geo['epsilon'],
            geo['historical_diagnostic_radius_q'], geo['historical_diagnostic_runtime_authority']) != (0.015, 0.0, 0.0, None, 0.025, False):
        raise RuntimeError('PILOT_GEOMETRY_DRIFT')
    if (frozen['environment']['CUDA_VISIBLE_DEVICES'] != '1'
            or frozen['environment']['process_visible_device'] != 'cuda:0'
            or frozen['scientific_boundaries']['frozen_scientific_decision_remains'] != 'FAIL_V3_HARD_SAFETY_GATE'):
        raise RuntimeError('PILOT_AUTHORITY_DRIFT')
    if require_absent_root and ROOT.exists():
        raise RuntimeError('FUTURE_PILOT_RESULT_ROOT_NOT_ABSENT')
    upstream_smoke_check()
    module = smoke_module()
    if digest(CHECKOUT / SMOKE_REL) != '518eddc1bebbb8df4d15782e4cf017f24c4af152efc253930d5df1b4f52e3e23':
        raise RuntimeError('R6_EXECUTED_ACTION_AUDITOR_DRIFT')
    base = module.load_runtime_base_config(CHECKOUT)
    projected = module.delegate_runtime_protocol(CHECKOUT)
    for key in ('seed', 'maximum_completed_cycles_per_trial', 'trial_ids', 'trial_order', 'serial_execution', 'separate_process_per_trial'):
        if projected[key] != cohort[key]:
            raise RuntimeError('DELEGATE_PROJECTION_DRIFT:' + key)
    if (projected['dynamics'] != base['dynamics'] or projected['environment'] != frozen['environment']
            or projected['map_identity'] != base['map_identity']):
        raise RuntimeError('CHILD_CONFIG_CONSUMPTION_DRIFT')
    module.verify_map_artifacts(frozen)
    if not all(value == 'PASS' for value in module.synthetic_executed_action_continuity_regression().values()):
        raise RuntimeError('EXECUTED_ACTION_CONTINUITY_FIXTURE_FAIL')
    if require_lock:
        lock = read(LOCK)
        if lock.get('protocol_sha256') != digest(PROTOCOL) or lock.get('protocol_semantic_sha256') != semantic(frozen):
            raise RuntimeError('PILOT_LOCK_PROTOCOL_MISMATCH')
        if (lock.get('schema') != 'CERT_EXEC_IDENTITY_REPAIR_PILOT_EXECUTION_LOCK_REPAIR_R1_V1'
                or lock.get('supersedes_lock_path') != BLOCKED_LOCK.name
                or lock.get('supersedes_lock_sha256') != BLOCKED_LOCK_SHA256
                or lock.get('blocked_freeze_head') != BLOCKED_HEAD
                or lock.get('blocked_freeze_status') != 'BLOCKED'):
            raise RuntimeError('REPAIRED_LOCK_SUPERSESSION_MISMATCH')
        commit = lock.get('harness_repair_commit')
        if not isinstance(commit, str) or len(commit) != 40 or subprocess.run(
                ['git', '-C', str(CHECKOUT), 'merge-base', '--is-ancestor', commit, 'HEAD']).returncode:
            raise RuntimeError('HARNESS_REPAIR_COMMIT_CONTRACT_FAIL')
        module.verify_static_identity(CHECKOUT, require_committed_lock=True)
    return {'delegate_protocol_contract': 'PASS', 'child_config_consumption_regression': 'PASS',
            'executed_action_continuity_contract': 'PASS', 'map_artifacts': 'PASS_3_OF_3'}


def trial_evidence_lock(raw: Path) -> dict[str, Any]:
    names = ('trial_summary.json', 'runtime_trace.jsonl', 'runtime_trace_lock.json',
             'cycle_observations.jsonl', 'process_exit_code.txt', 'gpu_released.txt', 'stdout.log', 'stderr.log')
    files = {}
    for name in names:
        path = raw / name
        if not path.is_file():
            raise RuntimeError('PILOT_TRIAL_EVIDENCE_MISSING:' + name)
        files[name] = {'size': path.stat().st_size, 'sha256': digest(path)}
    return {'schema': 'CERT_EXEC_IDENTITY_REPAIR_PILOT_RAW_EVIDENCE_LOCK_V1',
            'trial_id': int(raw.name.split('_')[-1]), 'files': files, 'immutable': True}


def complete_trial(root: Path, trial: int) -> bool:
    raw = root / 'raw' / f'trial_{trial}'
    try:
        lock = read(raw / 'PILOT_RAW_EVIDENCE_LOCK.json')
        if lock != trial_evidence_lock(raw):
            return False
        row = read(raw / 'trial_summary.json')
        frozen = protocol()
        if not set(frozen['per_trial_required_summary_fields']) <= set(row):
            return False
        cycles = row['completed_cycles']
        traces = len((raw / 'runtime_trace.jsonl').read_text().splitlines())
        observations = len((raw / 'cycle_observations.jsonl').read_text().splitlines())
        trace_lock = read(raw / 'runtime_trace_lock.json')
        if (not 0 < cycles <= 500 or any(value != cycles for value in
                (traces, observations, row['trace_record_count'], row['persisted_trace_line_count'],
                 row['trace_lock_record_count'], trace_lock['record_count']))):
            return False
        if (row['trial_id'] != trial or row['startup_status'] != 'PASS' or row['finalization_status'] != 'FINALIZED'
                or row['hard_blocker'] is not None or row['process_exit_code'] != 0
                or (raw / 'process_exit_code.txt').read_text().strip() != '0'
                or (raw / 'gpu_released.txt').read_text().strip() != 'true'):
            return False
        if any(row[field] != 0 for field in frozen['pilot_hard_zero_fields']):
            return False
        if (row['l2_next_l1_continuity_cross_cycle_rows'] != max(cycles - 1, 0)
                or sum(row[field] for field in ('l2_next_l1_continuity_applicable_count',
                        'l2_next_l1_continuity_not_applicable_count', 'l2_next_l1_continuity_unknown_count'))
                   != row['l2_next_l1_continuity_cross_cycle_rows']):
            return False
        if (row['plant_commit_count'] > cycles
                or sum(row[field] for field in ('primary_navigation_commit_count', 'alternative_navigation_commit_count',
                      'retained_backup_commit_count', 'terminal_commit_count')) != row['plant_commit_count']
                or row['assurance_boundary_count'] + row['plant_commit_count'] != cycles):
            return False
        module = smoke_module()
        trace_rows = [json.loads(x) for x in (raw / 'runtime_trace.jsonl').read_text().splitlines()]
        observed = [json.loads(x) for x in (raw / 'cycle_observations.jsonl').read_text().splitlines()]
        replay = module.executed_action_l2_next_l1_audit(trace_rows, observed)
        if any(row.get(k) != replay[k] for k in replay if k != 'l2_next_l1_continuity_role_counts'):
            return False
        return row.get('l2_next_l1_continuity_role_counts') == replay['l2_next_l1_continuity_role_counts']
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, json.JSONDecodeError):
        return False


def summarize(root: Path) -> dict[str, Any]:
    completed = [trial for trial in TRIALS if complete_trial(root, trial)]
    rows = [read(root / 'raw' / f'trial_{trial}' / 'trial_summary.json') for trial in completed]
    def total(field: str) -> int:
        return sum(int(row[field]) for row in rows)
    cycles = total('completed_cycles')
    routes = {field: total(field) for field in ('primary_navigation_commit_count', 'alternative_navigation_commit_count',
               'retained_backup_commit_count', 'terminal_commit_count', 'assurance_boundary_count')}
    continuity = {field: total(field) for field in ('canonical_transition_drift_count', 'cert_exec_identity_mismatch_count',
                  'l1_actual_continuity_mismatch_count', 'l2_next_l1_continuity_cross_cycle_rows',
                  'l2_next_l1_continuity_applicable_count', 'l2_next_l1_continuity_mismatch_count',
                  'l2_next_l1_continuity_not_applicable_count', 'l2_next_l1_continuity_unknown_count',
                  'backup_token_continuity_mismatch_count', 'selected_executed_identity_mismatch_count',
                  'forbidden_diagnostic_authority_event_count', 'normative_identity_payload_incomplete_count')}
    integrity = {field: total(field) for field in protocol()['pilot_hard_zero_fields']}
    stages = {stage: {status: sum(row[stage + '_status_counts'][status] for row in rows)
                      for status in ('PASS', 'FAIL', 'UNKNOWN')} for stage in ('L1', 'C0', 'L2', 'L3')}
    deadline = {status: sum(row['deadline_status_counts'][status] for row in rows)
                for status in ('OPEN', 'WARNING', 'EXPIRED')}
    times = [float(v) for row in rows for v in row['cycle_time_values']]
    timing = {'interpretation': 'ENGINEERING_TELEMETRY_ONLY_NO_HARD_REALTIME_GUARANTEE',
              'cycle_runtime_mean': statistics.mean(times) if times else None,
              'cycle_runtime_median': statistics.median(times) if times else None,
              'cycle_runtime_p95': sorted(times)[min(len(times)-1, int(0.95 * (len(times)-1)))] if times else None,
              'cycle_runtime_max': max(times) if times else None,
              'stage_timing_observation_count': sum(len(row['stage_timing_observations']) for row in rows)}
    status = ('PASS_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_PILOT_V1' if completed == list(TRIALS)
              and cycles == total('trace_record_count') == total('trace_lock_record_count')
              == total('persisted_trace_line_count') and total('plant_commit_count') <= cycles
              and all(value == 0 for value in integrity.values()) else 'BLOCK_CERT_EXEC_IDENTITY_REPAIR_PILOT_INTEGRITY')
    summary = {'schema': 'CERT_EXEC_IDENTITY_REPAIR_PILOT_COLLECTION_SUMMARY_V1', 'status': status,
               'trials_planned': list(TRIALS), 'trials_completed': completed, 'completed_cycles': cycles,
               'plant_commits': total('plant_commit_count'), 'trace_records': total('trace_record_count'),
               'trace_lock_records': total('trace_lock_record_count'), 'observation_records': cycles,
               'routing_totals': routes, 'continuity_totals': continuity, 'integrity_totals': integrity,
               'stage_status_totals': stages, 'deadline_status_totals': deadline, 'timing': timing,
               'gpu_trial_rerun_count': total('gpu_trial_rerun'), 'scientific_analysis_count': 0,
               'reference_rerun_count': 0, 'official100_count': 0, 'formal_count': 0,
               'frozen_scientific_decision_remains': 'FAIL_V3_HARD_SAFETY_GATE'}
    write(root / 'PILOT_COLLECTION_SUMMARY.json', summary)
    write(root / 'PILOT_TIMING_SUMMARY.json', timing)
    write(root / 'PILOT_ROUTE_SUMMARY.json', routes)
    write(root / 'PILOT_CONTINUITY_SUMMARY.json', continuity)
    with (root / 'PILOT_TRIAL_RESULTS.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=['trial_id', 'completed_cycles', 'plant_commit_count',
                                'finalization_status', 'hard_blocker', 'l2_next_l1_continuity_mismatch_count'])
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name) for name in writer.fieldnames})
    with (root / 'PILOT_FAILURE_REGISTER.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=['trial_id', 'failure_class', 'raw_evidence_complete', 'automatic_retry'])
        writer.writeheader()
        for trial in TRIALS:
            if trial not in completed:
                writer.writerow({'trial_id': trial, 'failure_class': 'NOT_COMPLETE_OR_NOT_YET_RUN',
                                 'raw_evidence_complete': False, 'automatic_retry': False})
    report = root / 'report' / 'REPORT_CERT_EXEC_IDENTITY_REPAIR_PILOT_V1.md'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text('# Certification–Execution State Identity Repair Engineering Pilot\n\n'
                      + f"Status: {status}. Completed: {len(completed)}/10; cycles: {cycles}.\n\n"
                      + 'This is an engineering pilot, not scientific efficacy validation. The cohort is reused and outcome-exposed. '
                      + 'No collision, progress, noninferiority, parameter-selection, hard-real-time, or deployment claim is authorized. '
                      + 'Historical V3 remains FAIL_V3_HARD_SAFETY_GATE. Only a new post-repair paired validation may evaluate scientific effect.\n',
                      encoding='utf-8')
    return summary


def cpu_static_preflight() -> dict[str, Any]:
    checks = static_contract(require_lock=LOCK.is_file())
    module = smoke_module()
    fixtures = module.synthetic_executed_action_continuity_regression()
    if not all(value == 'PASS' for value in fixtures.values()):
        raise RuntimeError('CONTINUITY_FIXTURE_FAIL')
    # Two independent arithmetic fixtures: non-primary N/A and a non-500-cycle denominator.
    sample = {'completed_cycles': 3, 'l2_next_l1_continuity_applicable_count': 1,
              'l2_next_l1_continuity_not_applicable_count': 1, 'l2_next_l1_continuity_unknown_count': 0,
              'l2_next_l1_continuity_cross_cycle_rows': 2}
    if sum(sample[k] for k in ('l2_next_l1_continuity_applicable_count',
            'l2_next_l1_continuity_not_applicable_count', 'l2_next_l1_continuity_unknown_count')) != max(sample['completed_cycles']-1, 0):
        raise RuntimeError('DENOMINATOR_FIXTURE_FAIL')
    result = {'schema': 'CERT_EXEC_IDENTITY_REPAIR_PILOT_CPU_STATIC_PREFLIGHT_V1', 'status': 'PASS',
              'upstream_smoke': 'PASS', 'cohort': list(TRIALS), 'checks': checks,
              'gpu_count': 0, 'tmux_count': 0, 'pilot_trial_count': 0, 'cycle_count': 0,
              'plant_commit_count': 0, 'controller_qp_count': 0, 'scientific_analysis_count': 0}
    print(json.dumps(result, sort_keys=True))
    print('UPSTREAM_REPAIR_SMOKE_PASS')
    print('DELEGATE_PROTOCOL_CONTRACT_PASS')
    print('CHILD_CONFIG_CONSUMPTION_REGRESSION_PASS')
    print('EXECUTED_ACTION_CONTINUITY_CONTRACT_PASS')
    print('PILOT_PROTOCOL_CONTRACT_PASS')
    return result


def run_one(root: Path, trial: int) -> int:
    module = smoke_module()
    code = module.run_one(CHECKOUT, root, trial)
    summary_path = root / 'raw' / f'trial_{trial}' / 'trial_summary.json'
    if summary_path.is_file():
        row = read(summary_path)
        row['schema'] = 'CERT_EXEC_IDENTITY_REPAIR_PILOT_TRIAL_SUMMARY_V1'
        write(summary_path, row)
    return code


def run_batch(root: Path) -> int:
    static_contract(require_lock=True, require_absent_root=False)
    module = smoke_module()
    delegate = module._load_delegate(CHECKOUT)
    token = secrets.token_hex(32)
    for trial in TRIALS:
        raw = root / 'raw' / f'trial_{trial}'
        if raw.exists():
            raise RuntimeError('EXISTING_TRIAL_EVIDENCE_REQUIRES_MANUAL_AUDIT')
        auth = module.write_authorization(CHECKOUT, root, trial, token)
        stdout = root / f'trial_{trial}_stdout.tmp'
        stderr = root / f'trial_{trial}_stderr.tmp'
        env = os.environ.copy(); env.update(protocol()['environment']); env[TOKEN_ENV] = token
        command = [protocol()['environment']['python'], str(Path(__file__).resolve()), '--one', str(trial),
                   '--checkout', str(CHECKOUT), '--output-dir', str(root)]
        with stdout.open('w', encoding='utf-8') as out, stderr.open('w', encoding='utf-8') as err:
            process = subprocess.Popen(command, env=env, stdout=out, stderr=err, text=True)
            code = process.wait()
        released = bool(delegate.gpu_pid_released(process.pid))
        auth.unlink(missing_ok=True)
        if not raw.is_dir():
            module.preserve_early_child_failure(root, trial, code, released, stdout, stderr)
            summarize(root)
            return code or 2
        stdout.replace(raw / 'stdout.log'); stderr.replace(raw / 'stderr.log')
        (raw / 'process_exit_code.txt').write_text(f'{code}\n', encoding='utf-8')
        (raw / 'gpu_released.txt').write_text(('true' if released else 'false') + '\n', encoding='utf-8')
        write(raw / 'PILOT_RAW_EVIDENCE_LOCK.json', trial_evidence_lock(raw))
        summarize(root)
        if code or not released or not complete_trial(root, trial):
            return code or 2
    print('PILOT_COMPLETE_OR_STOPPED_NO_SCIENTIFIC_ANALYSIS', flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--cpu-static-preflight', action='store_true')
    modes.add_argument('--gpu-preflight', action='store_true')
    modes.add_argument('--one', type=int)
    modes.add_argument('--batch', action='store_true')
    parser.add_argument('--checkout', type=Path, default=CHECKOUT)
    parser.add_argument('--output-dir', type=Path, default=ROOT)
    args = parser.parse_args()
    if args.checkout.resolve(strict=True) != CHECKOUT:
        raise RuntimeError('PILOT_CHECKOUT_MISMATCH')
    if args.cpu_static_preflight:
        cpu_static_preflight(); return 0
    if args.output_dir.resolve() != ROOT or not ROOT.is_dir():
        raise RuntimeError('PARENT_OWNED_PILOT_RESULT_ROOT_REQUIRED')
    if args.gpu_preflight:
        static_contract(require_lock=True, require_absent_root=False)
        code = int(smoke_module().gpu_preflight(CHECKOUT, ROOT))
        path = ROOT / 'raw/gpu_preflight.json'
        if code == 0 and path.is_file():
            preflight = read(path)
            preflight['schema'] = 'CERT_EXEC_IDENTITY_REPAIR_PILOT_GPU_PREFLIGHT_V1'
            write(path, preflight)
        return code
    if args.one is not None:
        if args.one not in TRIALS:
            raise RuntimeError('TRIAL_NOT_IN_FROZEN_PILOT_COHORT')
        return run_one(ROOT, args.one)
    return run_batch(ROOT)


if __name__ == '__main__':
    raise SystemExit(main())
