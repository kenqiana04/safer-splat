#!/usr/bin/env python3
"""Frozen post-repair Active collector; Reference and scientific oracle are never run here."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from typing import Any

from freeze_authorities import (PILOT_ROOT, REFERENCE_ROOT, REUSE_LOCK, TRIALS,
                                inventory, read, semantic, sha)

TASK = Path(__file__).resolve().parent
CHECKOUT = Path('/disk1/zlab/v3_repair_worktrees/safer-splat-post-repair-v3-paired-validation-protocol-v1')
ROOT = Path('/disk1/zlab/v3_repair_records/post_repair_v3_paired_validation_v1_20260917')
PROTOCOL = TASK / 'POST_REPAIR_V3_PAIRED_PROTOCOL.json'
LOCK = TASK / 'POST_REPAIR_V3_PAIRED_EXECUTION_LOCK.json'
PILOT_MANIFEST = TASK / 'PILOT_AUTHORITY_MANIFEST.json'
REFERENCE_MANIFEST = TASK / 'REFERENCE_AUTHORITY_MANIFEST.json'
REFERENCE_OUTCOMES = TASK / 'REFERENCE_FROZEN_OUTCOMES.json'
BASE = '0ccec8d5eb2b4adc553767d55ba35172cb890410'
BRANCH = 'freeze-post-repair-v3-paired-scientific-validation-protocol-v1'
TASK_REL = 'reproduction/formal/post_repair_v3_paired_validation_v1'
SMOKE_REL = 'reproduction/validation/certification_execution_state_identity_repair_smoke_v1/run_cert_exec_identity_repair_smoke_v1.py'
CHILD_ENV_REL = 'reproduction/pilot/certification_execution_state_identity_repair_pilot_v1/child_process_boundary.py'
AUTH_NAME = 'POST_REPAIR_V3_INTERNAL_CHILD_AUTHORIZATION.json'
TOKEN_ENV = 'SAFER_SPLAT_POST_REPAIR_V3_CHILD_TOKEN'
PROTECTED = ('cbf', 'dynamics', 'splat', 'run.py', 'reproduction/runtime',
             'reproduction/pilot', 'reproduction/validation', 'reproduction/smoke')
HARD_ZERO = (
    'canonical_transition_drift_count', 'cert_exec_identity_mismatch_count',
    'l1_actual_continuity_mismatch_count', 'l2_next_l1_continuity_mismatch_count',
    'l2_next_l1_continuity_unknown_count', 'backup_token_continuity_mismatch_count',
    'selected_executed_identity_mismatch_count', 'forbidden_diagnostic_authority_event_count',
    'normative_identity_payload_incomplete_count', 'duplicate_plant_commit_count',
    'duplicate_trace_append_count', 'illegal_token_mutation_count', 'evidence_incomplete_count',
    'recovery_required_count', 'plant_outcome_unknown_count', 'nonfinite_count',
    'action_bound_violation_count', 'exception_count', 'cuda_oom_count',
    'unintended_plant_commit_count',
)


def git(*args: str) -> str:
    return subprocess.run(['git', '-C', str(CHECKOUT), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')


def protocol() -> dict[str, Any]:
    return read(PROTOCOL)


def import_file(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError('FROZEN_IMPORT_UNAVAILABLE:' + str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def smoke_module() -> Any:
    module = import_file(CHECKOUT / SMOKE_REL, '_post_repair_v3_frozen_r6_smoke_adapter')
    module.TASK_DIR = TASK
    module.PROTOCOL_PATH = PROTOCOL
    module.LOCK_PATH = LOCK
    module.CHECKOUT_DEFAULT = CHECKOUT
    module.RESULT_ROOT = ROOT
    module.BRANCH = BRANCH
    module.TRIALS = TRIALS
    module.AUTHORIZATION_NAME = AUTH_NAME
    module.CHILD_TOKEN_ENV = TOKEN_ENV
    module.ALLOWED_TASK_REL = TASK_REL
    # Only this newly added task directory is writable; all other R6 protected paths remain read-only.
    module.PROTECTED_PATHS = tuple(x for x in module.PROTECTED_PATHS if x != 'reproduction/formal')
    return module


def verify_protocol() -> dict[str, Any]:
    p = protocol()
    c, g = p['cohort'], p['geometry']
    if (p['schema'] != 'POST_REPAIR_V3_PAIRED_SCIENTIFIC_VALIDATION_PROTOCOL_V1'
            or c['trial_ids'] != list(TRIALS) or c['trial_order'] != list(TRIALS)
            or len(set(TRIALS)) != 85 or c['seed'] != 0
            or c['maximum_completed_cycles_per_trial'] != 500
            or c['serial_execution'] is not True or c['separate_process_per_trial'] is not True
            or c['automatic_retry'] is not False):
        raise RuntimeError('EXACT_85_COHORT_OR_ORDER_DRIFT')
    if (g['hard_radius_q'], g['runtime_margin_q'], g['rho_seg_q'], g['epsilon'],
            g['historical_diagnostic_radius_q'], g['historical_diagnostic_runtime_authority']) != (0.015, 0.0, 0.0, None, 0.025, False):
        raise RuntimeError('POST_REPAIR_HARD_GEOMETRY_DRIFT')
    if (p['environment']['physical_gpu'] != 1 or p['environment']['process_visible_device'] != 'cuda:0'
            or p['future_result_root'] != str(ROOT)
            or p['scientific_boundaries']['frozen_scientific_decision_remains'] != 'FAIL_V3_HARD_SAFETY_GATE'
            or p['progress_noninferiority_gate']['resamples'] != 10000
            or p['progress_noninferiority_gate']['seed'] != 20260911
            or p['progress_noninferiority_gate']['margin'] != -0.02
            or p['progress_noninferiority_gate']['pass_comparator'] != 'STRICT_GREATER_THAN'
            or p['historical_witnesses'] != [22, 28, 57, 59]):
        raise RuntimeError('SCIENTIFIC_PROTOCOL_CONTRACT_DRIFT')
    if (p['canonical_transition']['source_sha256'] != '437aac43c3ece27609af6339bfea6ab7b7f0248ca2738ec1691c88c84d747891'
            or p['runtime_repair_tree_sha256'] != 'e23d8cc6326d35c0f89698174a3c22cb148af41836e5a803c03cecca599316ab'
            or p['repair_protocol_sha256'] != '80b4c15413bdfa9b03b106a725af5cd97b17a51b9e81d03cfe79a7300a8077e7'
            or p['historical_v3_protocol_sha256'] != 'c1dc8b3f17850267f1cb3247795bc193a8944aa59349de5019efdf4ae72b1691'):
        raise RuntimeError('REPAIRED_ACTIVE_SOURCE_IDENTITY_DRIFT')
    return p


def verify_authority_manifests() -> dict[str, Any]:
    pilot = read(PILOT_MANIFEST)
    reference = read(REFERENCE_MANIFEST)
    outcomes = read(REFERENCE_OUTCOMES)
    if pilot['inventory'] != inventory(PILOT_ROOT) or reference['inventory'] != inventory(REFERENCE_ROOT):
        raise RuntimeError('PILOT_OR_REFERENCE_ROOT_MUTATION')
    if (pilot['status'] != 'PASS_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_PILOT_V1'
            or any(pilot[name] != 5000 for name in ('completed_cycles', 'plant_commits',
                    'trace_records', 'trace_lock_records'))
            or pilot['continuity_hard_zero'] is not True or pilot['integrity_hard_zero'] is not True
            or pilot['scientific_analysis_count'] != 0
            or pilot['active_lock_sha256'] != sha(CHECKOUT / 'reproduction/pilot/certification_execution_state_identity_repair_pilot_v1/PILOT_EXECUTION_LOCK_LAUNCH_REPAIR_R2.json')):
        raise RuntimeError('PILOT_AUTHORITY_MISMATCH')
    current_pilot = read(PILOT_ROOT / 'PILOT_COLLECTION_SUMMARY.json')
    if any(current_pilot['continuity_totals'].get(name, 0) != 0 or current_pilot['integrity_totals'].get(name, 0) != 0 for name in HARD_ZERO):
        raise RuntimeError('PILOT_HARD_ZERO_DRIFT')
    reuse = read(REUSE_LOCK)
    if (reference['reuse_lock_sha256'] != sha(REUSE_LOCK) or reuse['reference_arm_count'] != 85
            or reuse['all_immutable_complete_identity_compatible'] is not True
            or reuse['reference_rerun_authorized'] is not False or reuse['reference_rerun_count'] != 0
            or reference['reference_hard_violation_trials'] != 0):
        raise RuntimeError('REFERENCE_AUTHORITY_MISMATCH')
    source = Path(outcomes['source_per_pair_path'])
    if (source != Path(protocol()['reference_authority']['outcomes_source'])
            or outcomes['source_per_pair_sha256'] != sha(source)
            or outcomes['trial_order'] != list(TRIALS)
            or len(outcomes['values']) != 85
            or outcomes['values_semantic_sha256'] != semantic(outcomes['values'])
            or outcomes['reference_hard_violation_trials'] != 0
            or outcomes['reference_unknown_trials'] != 0):
        raise RuntimeError('FROZEN_REFERENCE_OUTCOMES_DRIFT')
    if any(row['trial_id'] != tid or row['hard_violation'] is not False or row['unknown_segment_count'] != 0
           for tid, row in zip(TRIALS, outcomes['values'])):
        raise RuntimeError('FROZEN_REFERENCE_85_ORDER_OR_HARD_DRIFT')
    return {'pilot': pilot, 'reference': reference, 'reference_outcomes': outcomes}


def verify_source_and_map(*, require_lock: bool, require_absent_root: bool) -> dict[str, Any]:
    if git('branch', '--show-current') != BRANCH or subprocess.run(
            ['git', '-C', str(CHECKOUT), 'merge-base', '--is-ancestor', BASE, 'HEAD']).returncode:
        raise RuntimeError('POST_REPAIR_UPSTREAM_BRANCH_OR_HEAD_DRIFT')
    changed = git('diff', '--name-only', BASE).splitlines()
    if any(not path.startswith(TASK_REL + '/') for path in changed):
        raise RuntimeError('OUT_OF_TASK_SCOPE_DIFF')
    if git('diff', BASE, '--', *PROTECTED):
        raise RuntimeError('PROTECTED_RUNTIME_DIFF_NONZERO')
    if require_absent_root and ROOT.exists():
        raise RuntimeError('FUTURE_RESULT_ROOT_NOT_ABSENT')
    p = verify_protocol()
    identities = verify_authority_manifests()
    module = smoke_module()
    module.verify_map_artifacts(p)
    if git('rev-parse', 'HEAD:reproduction/validation/certification_execution_state_identity_repair_smoke_v1') != git(
            'rev-parse', '601204bfc14e3ad2c8e3c714b8f5045829491635:reproduction/validation/certification_execution_state_identity_repair_smoke_v1'):
        raise RuntimeError('R6_REPAIRED_DELEGATE_TREE_DRIFT')
    if (CHECKOUT / 'outputs/stonehenge').resolve(strict=True) != Path('/disk1/zlab/datasets/safer_splat_gdrive/outputs/stonehenge'):
        raise RuntimeError('OUTPUTS_MAP_BINDING_DRIFT')
    if (CHECKOUT / 'data/stonehenge').resolve(strict=True) != Path('/disk1/zlab/datasets/safer_splat_gdrive/data/stonehenge'):
        raise RuntimeError('DATA_MAP_BINDING_DRIFT')
    if git('check-ignore', 'outputs/stonehenge') != 'outputs/stonehenge' or git('check-ignore', 'data/stonehenge') != 'data/stonehenge':
        raise RuntimeError('MAP_BINDING_NOT_IGNORED')
    if require_lock:
        lock = read(LOCK)
        if (lock['protocol_sha256'] != sha(PROTOCOL)
                or lock['protocol_semantic_sha256'] != semantic(p)
                or lock['branch'] != BRANCH or lock['worktree'] != str(CHECKOUT)
                or lock['base_head'] != BASE or lock['future_result_root'] != str(ROOT)
                or lock['pilot_semantic_root_sha256'] != identities['pilot']['inventory']['semantic_root_sha256']
                or lock['reference_semantic_root_sha256'] != identities['reference']['inventory']['semantic_root_sha256']
                or lock['harness_sha256'] != {name: sha(TASK / name) for name in lock['harness_sha256']}):
            raise RuntimeError('POST_REPAIR_EXECUTION_LOCK_MISMATCH')
        commit = lock.get('harness_repair_commit')
        if not isinstance(commit, str) or subprocess.run(
                ['git', '-C', str(CHECKOUT), 'merge-base', '--is-ancestor', commit, 'HEAD']).returncode:
            raise RuntimeError('PROTOCOL_FREEZE_COMMIT_NOT_ANCESTOR')
        module.verify_static_identity(CHECKOUT, require_committed_lock=True)
    return {'pilot': 'PILOT_AUTHORITY_PASS', 'reference': 'REFERENCE_AUTHORITY_PASS',
            'active': 'POST_REPAIR_ACTIVE_IDENTITY_PASS', 'cohort': 'EXACT_85_COHORT_PASS',
            'map': 'MAP_ARTIFACTS_3_OF_3_PASS', 'protected': 'PROTECTED_RUNTIME_DIFF_ZERO'}


def trial_evidence_lock(raw: Path) -> dict[str, Any]:
    names = ('trial_summary.json', 'runtime_trace.jsonl', 'runtime_trace_lock.json',
             'cycle_observations.jsonl', 'process_exit_code.txt', 'gpu_released.txt', 'stdout.log', 'stderr.log')
    files = {}
    for name in names:
        path = raw / name
        if not path.is_file():
            raise RuntimeError('POST_REPAIR_TRIAL_EVIDENCE_MISSING:' + name)
        files[name] = {'size': path.stat().st_size, 'sha256': sha(path)}
    return {'schema': 'POST_REPAIR_V3_PAIRED_RAW_EVIDENCE_LOCK_V1',
            'trial_id': int(raw.name.split('_')[-1]), 'files': files, 'immutable': True}


def complete_trial(root: Path, trial: int) -> bool:
    raw = root / 'raw' / f'trial_{trial}'
    try:
        if read(raw / 'POST_REPAIR_V3_RAW_EVIDENCE_LOCK.json') != trial_evidence_lock(raw):
            return False
        row = read(raw / 'trial_summary.json')
        cycles = int(row['completed_cycles'])
        traces = [json.loads(x) for x in (raw / 'runtime_trace.jsonl').read_text().splitlines()]
        observations = [json.loads(x) for x in (raw / 'cycle_observations.jsonl').read_text().splitlines()]
        trace_lock = read(raw / 'runtime_trace_lock.json')
        if (not 0 < cycles <= 500 or any(value != cycles for value in
                (len(traces), len(observations), row['trace_record_count'], row['persisted_trace_line_count'],
                 row['trace_lock_record_count'], trace_lock['record_count']))):
            return False
        if (row['trial_id'] != trial or row['startup_status'] != 'PASS'
                or row['finalization_status'] != 'FINALIZED' or row['hard_blocker'] is not None
                or row['process_exit_code'] != 0 or (raw / 'process_exit_code.txt').read_text().strip() != '0'
                or (raw / 'gpu_released.txt').read_text().strip() != 'true'):
            return False
        if any(row.get(field) != 0 for field in HARD_ZERO):
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
        replay = smoke_module().executed_action_l2_next_l1_audit(traces, observations)
        return all(row.get(k) == value for k, value in replay.items())
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, json.JSONDecodeError):
        return False


def summarize_collection(root: Path) -> dict[str, Any]:
    completed = [trial for trial in TRIALS if complete_trial(root, trial)]
    rows = [read(root / 'raw' / f'trial_{trial}' / 'trial_summary.json') for trial in completed]
    def total(name: str) -> int:
        return sum(int(row[name]) for row in rows)
    cycles = total('completed_cycles')
    continuity = {name: total(name) for name in ('canonical_transition_drift_count', 'cert_exec_identity_mismatch_count',
        'l1_actual_continuity_mismatch_count', 'l2_next_l1_continuity_cross_cycle_rows',
        'l2_next_l1_continuity_applicable_count', 'l2_next_l1_continuity_not_applicable_count',
        'l2_next_l1_continuity_mismatch_count', 'l2_next_l1_continuity_unknown_count',
        'backup_token_continuity_mismatch_count', 'selected_executed_identity_mismatch_count',
        'forbidden_diagnostic_authority_event_count', 'normative_identity_payload_incomplete_count')}
    routing = {name: total(name) for name in ('primary_navigation_commit_count', 'alternative_navigation_commit_count',
        'retained_backup_commit_count', 'terminal_commit_count', 'assurance_boundary_count')}
    integrity = {name: total(name) for name in HARD_ZERO}
    status = ('PASS_POST_REPAIR_V3_PAIRED_COLLECTION_INTEGRITY' if completed == list(TRIALS)
              and all(value == 0 for value in integrity.values())
              and cycles == total('trace_record_count') == total('trace_lock_record_count')
              else 'INCOMPLETE_OR_BLOCKED_POST_REPAIR_V3_PAIRED_COLLECTION')
    summary = {'schema': 'POST_REPAIR_V3_PAIRED_COLLECTION_SUMMARY_V1', 'status': status,
               'trials_planned': list(TRIALS), 'trials_completed': completed, 'completed_cycles': cycles,
               'plant_commits': total('plant_commit_count'), 'trace_records': total('trace_record_count'),
               'trace_lock_records': total('trace_lock_record_count'), 'continuity_totals': continuity,
               'routing_totals': routing, 'integrity_totals': integrity,
               'scientific_analysis_count': 0, 'reference_rerun_count': 0,
               'frozen_scientific_decision_remains': 'FAIL_V3_HARD_SAFETY_GATE'}
    write(root / 'POST_REPAIR_V3_PAIRED_COLLECTION_SUMMARY.json', summary)
    with (root / 'POST_REPAIR_V3_PAIRED_FAILURE_REGISTER.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=['trial_id', 'failure_class', 'raw_evidence_complete', 'automatic_retry'])
        writer.writeheader()
        for trial in TRIALS:
            if trial not in completed:
                writer.writerow({'trial_id': trial, 'failure_class': 'NOT_COMPLETE_OR_NOT_YET_RUN',
                                 'raw_evidence_complete': False, 'automatic_retry': False})
    return summary


def cpu_static_preflight() -> dict[str, Any]:
    checks = verify_source_and_map(require_lock=LOCK.is_file(), require_absent_root=True)
    module = smoke_module()
    projected = module.delegate_runtime_protocol(CHECKOUT)
    if projected['trial_order'] != list(TRIALS) or projected['trial_ids'] != list(TRIALS):
        raise RuntimeError('DELEGATE_85_ORDER_DRIFT')
    if not all(value == 'PASS' for value in module.synthetic_executed_action_continuity_regression().values()):
        raise RuntimeError('DELEGATE_EXECUTED_ACTION_CONTINUITY_FIXTURE_FAIL')
    child = import_file(CHECKOUT / CHILD_ENV_REL, '_post_repair_child_boundary')
    env = child.normalize_env({}, protocol()['environment'])
    child.validate_popen_boundary([env['python'], Path(__file__), '--one', '66'], env)
    if env['physical_gpu'] != '1':
        raise RuntimeError('CHILD_ENV_GPU_SCALAR_NOT_NORMALIZED')
    result = {'status': 'PASS', 'checks': checks, 'gpu_execution_count': 0, 'tmux_count': 0,
              'active_trial_count': 0, 'runtime_cycle_count': 0, 'plant_commit_count': 0,
              'reference_rerun_count': 0, 'scientific_analyzer_execution_count': 0}
    print(json.dumps(result, sort_keys=True))
    for value in checks.values():
        print(value)
    print('HARD_SAFETY_CONTRACT_PASS')
    print('PROGRESS_NI_CONTRACT_PASS')
    print('WITNESS_REGISTRATION_PASS')
    print('FUTURE_RESULT_ROOT_ABSENT')
    return result


def run_one(root: Path, trial: int) -> int:
    code = int(smoke_module().run_one(CHECKOUT, root, trial))
    summary_path = root / 'raw' / f'trial_{trial}' / 'trial_summary.json'
    if summary_path.is_file():
        row = read(summary_path)
        v2 = import_file(CHECKOUT / 'reproduction/pilot/active_runtime_pilot_v2/run_active_runtime_pilot_v2.py',
                         '_post_repair_v3_frozen_trial_geometry')
        start, goal = v2.trial_geometry(trial)
        row['start_state'] = [float(x) for x in start.astype('float32')] + [0.0, 0.0, 0.0]
        row['goal_state'] = [float(x) for x in goal.astype('float32')] + [0.0, 0.0, 0.0]
        row['schema'] = 'POST_REPAIR_V3_PAIRED_ACTIVE_TRIAL_SUMMARY_V1'
        row['posthoc_scientific_outcome_pending'] = True
        row['reference_arm_rerun'] = False
        row['source_git_identity'] = git('rev-parse', 'HEAD')
        write(summary_path, row)
    return code


def run_batch(root: Path) -> int:
    verify_source_and_map(require_lock=True, require_absent_root=False)
    module = smoke_module()
    delegate = module._load_delegate(CHECKOUT)
    child = import_file(CHECKOUT / CHILD_ENV_REL, '_post_repair_child_boundary')
    token = secrets.token_hex(32)
    for trial in TRIALS:
        raw = root / 'raw' / f'trial_{trial}'
        if raw.exists():
            raise RuntimeError('EXISTING_ACTIVE_TRIAL_EVIDENCE_NO_AUTO_RERUN:' + str(trial))
        stdout, stderr = root / f'trial_{trial}_stdout.tmp', root / f'trial_{trial}_stderr.tmp'
        env = child.normalize_env(os.environ.copy(), {**protocol()['environment'], TOKEN_ENV: token})
        command = child.normalize_argv([protocol()['environment']['python'], Path(__file__).resolve(),
                                        '--one', str(trial), '--checkout', CHECKOUT, '--output-dir', root])
        command, env = child.validate_popen_boundary(command, env)
        authorization = module.write_authorization(CHECKOUT, root, trial, token)
        with stdout.open('w', encoding='utf-8') as out, stderr.open('w', encoding='utf-8') as err:
            process = subprocess.Popen(command, env=env, stdout=out, stderr=err, text=True)
            code = process.wait()
        released = bool(delegate.gpu_pid_released(process.pid))
        authorization.unlink(missing_ok=True)
        if not raw.is_dir():
            module.preserve_early_child_failure(root, trial, code, released, stdout, stderr)
            summarize_collection(root)
            return code or 2
        stdout.replace(raw / 'stdout.log')
        stderr.replace(raw / 'stderr.log')
        (raw / 'process_exit_code.txt').write_text(f'{code}\n', encoding='utf-8')
        (raw / 'gpu_released.txt').write_text(('true' if released else 'false') + '\n', encoding='utf-8')
        write(raw / 'POST_REPAIR_V3_RAW_EVIDENCE_LOCK.json', trial_evidence_lock(raw))
        summarize_collection(root)
        if code or not released or not complete_trial(root, trial):
            return code or 2
    print('POST_REPAIR_V3_ACTIVE_COLLECTION_COMPLETE_NO_SCIENTIFIC_ANALYSIS', flush=True)
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
    if args.checkout.resolve(strict=True) != CHECKOUT or args.output_dir.resolve() != ROOT:
        raise RuntimeError('EXACT_CHECKOUT_OR_RESULT_ROOT_REQUIRED')
    if args.cpu_static_preflight:
        cpu_static_preflight()
        return 0
    if not ROOT.is_dir():
        raise RuntimeError('PARENT_OWNED_FRESH_RESULT_ROOT_REQUIRED')
    if args.gpu_preflight:
        verify_source_and_map(require_lock=True, require_absent_root=False)
        return int(smoke_module().gpu_preflight(CHECKOUT, ROOT))
    if args.one is not None:
        if args.one not in TRIALS:
            raise RuntimeError('TRIAL_NOT_IN_FROZEN_PRIMARY_85')
        return run_one(ROOT, args.one)
    return run_batch(ROOT)


if __name__ == '__main__':
    raise SystemExit(main())
