#!/usr/bin/env python3
"""CPU-only validation of the frozen engineering-pilot protocol and harness."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parent
CHECKOUT = Path('/disk1/zlab/v3_repair_worktrees/safer-splat-cert-exec-identity-repair-pilot-freeze-harness-r1')
BASE = 'e859fbd48384cdcc39162f4beb26ed26c387057c'
PROTOCOL_SHA = '9fb0992b30edbb7a0a2ec48b646a8645eb93aee1805799170dd62a177a03abee'
PROTOCOL_SEMANTIC_SHA = '92e692b4996b3583c91c03faad542850c8f247ce6f26c96503ec861421baca46'
NAMES = ('run_cert_exec_identity_repair_pilot_v1.py', 'launch_cert_exec_identity_repair_pilot_v1.sh',
         'validate_cert_exec_identity_repair_pilot_v1.py', 'monitor_cert_exec_identity_repair_pilot_v1.py')


def load_runner():
    path = TASK / NAMES[0]
    spec = importlib.util.spec_from_file_location('_pilot_validation_target', path)
    if spec is None or spec.loader is None:
        raise RuntimeError('PILOT_RUNNER_IMPORT_UNAVAILABLE')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def validate(pre_freeze: bool) -> dict:
    runner = load_runner()
    failed: list[str] = []
    passed: list[str] = []
    def need(condition: bool, key: str) -> None:
        (passed if condition else failed).append(key)
    git = runner.git
    frozen = runner.protocol()
    need(git('branch', '--show-current') == 'repair-cert-exec-identity-repair-pilot-freeze-harness-r1', 'EXACT_BRANCH')
    need(subprocess.run(['git', '-C', str(CHECKOUT), 'merge-base', '--is-ancestor', BASE, 'HEAD']).returncode == 0, 'UPSTREAM_ANCESTOR')
    need(git('rev-parse', BASE + ':reproduction/pilot/certification_execution_state_identity_repair_pilot_v1/PILOT_PROTOCOL.json') ==
         git('rev-parse', 'HEAD:reproduction/pilot/certification_execution_state_identity_repair_pilot_v1/PILOT_PROTOCOL.json')
         and runner.digest(runner.PROTOCOL) == PROTOCOL_SHA
         and runner.semantic(frozen) == PROTOCOL_SEMANTIC_SHA, 'PROTOCOL_UNCHANGED')
    need(runner.digest(runner.BLOCKED_LOCK) == runner.BLOCKED_LOCK_SHA256, 'BLOCKED_FREEZE_PRESERVED')
    need(git('rev-parse', BASE + ':reproduction/pilot/certification_execution_state_identity_repair_pilot_v1/PILOT_EXECUTION_LOCK.json') ==
         git('rev-parse', 'HEAD:reproduction/pilot/certification_execution_state_identity_repair_pilot_v1/PILOT_EXECUTION_LOCK.json'), 'BLOCKED_LOCK_GIT_BLOB_PRESERVED')
    need(frozen.get('schema') == 'CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_PILOT_PROTOCOL_V1', 'PILOT_SCHEMA')
    need(frozen.get('exposure_label') == 'REUSED_ENGINEERING_COHORT_NOT_SCIENTIFIC_HOLDOUT', 'EXPOSURE_LABEL')
    need(frozen['cohort']['trial_ids'] == frozen['cohort']['trial_order'] == list(runner.TRIALS), 'COHORT_AND_ORDER')
    need(frozen['cohort']['seed'] == 0 and frozen['cohort']['maximum_completed_cycles_per_trial'] == 500, 'SEED_AND_MAX')
    need(frozen['cohort']['serial_execution'] and frozen['cohort']['separate_process_per_trial'] and not frozen['cohort']['automatic_retry'], 'PROCESS_CONTRACT')
    need(frozen['environment']['physical_gpu'] == 1 and frozen['environment']['process_visible_device'] == 'cuda:0', 'GPU_BINDING')
    g = frozen['geometry']
    need((g['hard_radius_q'], g['runtime_margin_q'], g['rho_seg_q'], g['epsilon'], g['historical_diagnostic_radius_q'], g['historical_diagnostic_runtime_authority']) == (0.015, 0.0, 0.0, None, 0.025, False), 'GEOMETRY')
    need(frozen['canonical_transition']['source_sha256'] == '437aac43c3ece27609af6339bfea6ab7b7f0248ca2738ec1691c88c84d747891', 'TRANSITION_SHA')
    need(frozen['runtime_repair_tree_sha256'] == 'e23d8cc6326d35c0f89698174a3c22cb148af41836e5a803c03cecca599316ab', 'RUNTIME_TREE_SHA')
    need(frozen['repair_protocol_sha256'] == '80b4c15413bdfa9b03b106a725af5cd97b17a51b9e81d03cfe79a7300a8077e7', 'REPAIR_PROTOCOL_SHA')
    need(frozen['historical_v3_protocol_sha256'] == 'c1dc8b3f17850267f1cb3247795bc193a8944aa59349de5019efdf4ae72b1691', 'HISTORICAL_PROTOCOL_SHA')
    need(not runner.ROOT.exists(), 'PILOT_RESULT_ROOT_ABSENT')
    need(runner.root_manifest(runner.SMOKE_ROOT) == runner.read(runner.SMOKE_MANIFEST), 'UPSTREAM_SMOKE_IMMUTABLE')
    smoke = runner.upstream_smoke_check()
    need(smoke['status'] == 'PASS_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_SMOKE_V1', 'UPSTREAM_SMOKE_PASS')
    need(smoke['trials_completed'] == [15,45,75] and smoke['completed_cycles'] == smoke['plant_commits'] == smoke['trace_records'] == smoke['trace_lock_records'] == 1500, 'UPSTREAM_SMOKE_CARDINALITY')
    pilot = runner.smoke_module()
    need(pilot.delegate_runtime_protocol(CHECKOUT)['trial_ids'] == list(runner.TRIALS), 'DELEGATE_PROTOCOL_CONTRACT')
    need(pilot.delegate_runtime_protocol(CHECKOUT)['dynamics'] == pilot.load_runtime_base_config(CHECKOUT)['dynamics'], 'CHILD_CONFIG_CONSUMPTION_REGRESSION')
    need(all(x == 'PASS' for x in pilot.synthetic_executed_action_continuity_regression().values()), 'EXECUTED_ACTION_CONTINUITY_CONTRACT')
    need(frozen['pilot_denominator_contract'] == 'applicable + not_applicable + unknown == cross_cycle_rows == max(completed_cycles - 1, 0)', 'DENOMINATOR_CONTRACT')
    need('PILOT_RAW_EVIDENCE_LOCK.json' in frozen['per_trial_required_files'] and len(frozen['per_trial_required_summary_fields']) >= 40, 'PER_TRIAL_EVIDENCE_SCHEMA')
    need(frozen['deadline']['interpretation'] == 'ENGINEERING_TELEMETRY_ONLY_NO_HARD_REALTIME_GUARANTEE' and frozen['pilot_routing_contract']['deadline_expired_is_not_automatic_failure'], 'DEADLINE_INTERPRETATION')
    need(frozen['pilot_routing_contract']['l3_fail_is_not_automatic_failure'], 'L3_ROUTING_INTERPRETATION')
    need(frozen['scientific_boundaries']['frozen_scientific_decision_remains'] == 'FAIL_V3_HARD_SAFETY_GATE' and not frozen['scientific_boundaries']['scientific_analysis_performed'], 'SCIENTIFIC_BOUNDARY')
    changed = git('diff', '--name-only', BASE).splitlines()
    prefix = 'reproduction/pilot/certification_execution_state_identity_repair_pilot_v1/'
    need(all(path.startswith(prefix) for path in changed), 'TASK_LOCAL_DIFF_ONLY')
    need(not runner.classify_changed_paths(changed)['scientific_runtime_protected']
         and not git('diff', BASE, '--', 'cbf', 'dynamics', 'splat', 'run.py', 'reproduction/runtime'), 'PROTECTED_RUNTIME_DIFF_ZERO')
    upstream = runner.upstream_r6_harness_identity()
    need(upstream['status'] == 'UPSTREAM_R6_ENGINEERING_HARNESS_IDENTITY_PASS', 'UPSTREAM_R6_ENGINEERING_HARNESS_IDENTITY_PASS')
    need(runner.classify_changed_paths([runner.SMOKE_REL])['scientific_runtime_protected'] == []
         and runner.classify_changed_paths([runner.SMOKE_REL])['upstream_engineering_harness'] == [runner.SMOKE_REL],
         'R6_HISTORICAL_CLASSIFICATION_FIXTURE')
    try:
        runner.assert_protected_runtime_diff_zero(['reproduction/runtime/fake_mutation.py'])
    except RuntimeError as exc:
        need(str(exc) == 'PROTECTED_RUNTIME_DIFF_NONZERO', 'TRUE_PROTECTED_MUTATION_FAIL_CLOSED_FIXTURE')
    else:
        need(False, 'TRUE_PROTECTED_MUTATION_FAIL_CLOSED_FIXTURE')
    need(git('check-ignore', 'outputs/stonehenge') == 'outputs/stonehenge'
         and git('check-ignore', 'data/stonehenge') == 'data/stonehenge', 'IGNORED_MAP_BINDINGS')
    launcher = (TASK / NAMES[1]).read_text()
    need('--prelaunch-check-only' in launcher and 'mkdir -p "$RESULT_ROOT"' in launcher and launcher.index('--prelaunch-check-only') < launcher.index('mkdir -p "$RESULT_ROOT"'), 'PRELAUNCH_BEFORE_RESULT_ROOT_CREATION')
    need('tmux new-session' in launcher and 'TRIALS' not in launcher, 'SINGLE_BATCH_LAUNCHER')
    if runner.LOCK.is_file():
        lock = runner.read(runner.LOCK)
        need(lock.get('schema') == 'CERT_EXEC_IDENTITY_REPAIR_PILOT_EXECUTION_LOCK_REPAIR_R1_V1', 'LOCK_SCHEMA')
        need(lock.get('base_head') == BASE and lock.get('branch') == git('branch', '--show-current') and lock.get('worktree') == str(CHECKOUT), 'LOCK_IDENTITY')
        need(lock.get('protocol_sha256') == runner.digest(runner.PROTOCOL) and lock.get('protocol_semantic_sha256') == runner.semantic(frozen), 'LOCK_PROTOCOL_HASHES')
        need(lock.get('upstream_smoke_manifest') == runner.root_manifest(runner.SMOKE_ROOT), 'LOCK_UPSTREAM_MANIFEST')
        need(lock.get('harness_sha256') == {name: runner.digest(TASK / name) for name in NAMES}, 'LOCK_HARNESS_4_OF_4')
        need(lock.get('cohort') == list(runner.TRIALS) and lock.get('seed') == 0 and lock.get('max_cycles') == 500, 'LOCK_COHORT')
        need(lock.get('geometry') == g and lock.get('future_result_root') == str(runner.ROOT) and lock.get('automatic_retry') is False, 'LOCK_GEOMETRY_AND_ROOT')
        need(lock.get('scientific_analysis_enabled') is False and lock.get('frozen_scientific_decision_remains') == 'FAIL_V3_HARD_SAFETY_GATE', 'LOCK_SCIENTIFIC_BOUNDARY')
        need(lock.get('protocol_commit') == '0e3479543419705b76b1cb0b264bbbf4c21bfa9f', 'ORIGINAL_PROTOCOL_COMMIT')
        need(lock.get('supersedes_lock_path') == runner.BLOCKED_LOCK.name
             and lock.get('supersedes_lock_sha256') == runner.BLOCKED_LOCK_SHA256
             and lock.get('blocked_freeze_head') == BASE
             and lock.get('blocked_freeze_status') == 'BLOCKED'
             and lock.get('superseded_status') == 'BLOCKED'
             and lock.get('supersession_reason') == 'TASK_LOCAL_FREEZE_HARNESS_CONTRACT_REPAIR_ONLY', 'LOCK_SUPERSESSION_CHAIN')
        commit = lock.get('harness_repair_commit')
        need(isinstance(commit, str) and len(commit) == 40
             and subprocess.run(['git', '-C', str(CHECKOUT), 'merge-base', '--is-ancestor', commit, 'HEAD']).returncode == 0
             and (pre_freeze or commit == git('rev-parse', 'HEAD^')), 'HARNESS_REPAIR_COMMIT_CONTRACT_PASS')
        need(runner.LOCK.name == 'PILOT_EXECUTION_LOCK_REPAIR_R1.json'
             and "LOCK = TASK / 'PILOT_EXECUTION_LOCK_REPAIR_R1.json'" in (TASK / NAMES[0]).read_text(),
             'ACTIVE_LOCK_POINTER_EXACT')
    elif pre_freeze:
        passed.append('REPAIRED_LOCK_PENDING_HARNESS_COMMIT')
    else:
        failed.append('PILOT_EXECUTION_LOCK_MISSING')
    result = {'schema': 'CERT_EXEC_IDENTITY_REPAIR_PILOT_PROTOCOL_VALIDATION_V1', 'status': 'PASS' if not failed else 'FAIL',
              'passed_checks': passed, 'failed_checks': failed, 'gpu_count': 0, 'tmux_count': 0,
              'pilot_trial_count': 0, 'cycle_count': 0, 'plant_commit_count': 0, 'controller_qp_count': 0}
    print(json.dumps(result, sort_keys=True))
    if failed:
        raise RuntimeError('PILOT_PROTOCOL_VALIDATION_FAILED:' + ','.join(failed))
    print('UPSTREAM_REPAIR_SMOKE_PASS')
    print('DELEGATE_PROTOCOL_CONTRACT_PASS')
    print('CHILD_CONFIG_CONSUMPTION_REGRESSION_PASS')
    print('EXECUTED_ACTION_CONTINUITY_CONTRACT_PASS')
    print('PILOT_PROTOCOL_CONTRACT_PASS')
    print('BLOCKED_FREEZE_PRESERVED')
    print('PROTOCOL_UNCHANGED')
    print('PROTECTED_RUNTIME_DIFF_ZERO')
    print('UPSTREAM_R6_ENGINEERING_HARNESS_IDENTITY_PASS')
    if not pre_freeze:
        print('HARNESS_REPAIR_COMMIT_CONTRACT_PASS')
        print('REPAIRED_EXECUTION_LOCK_CONTRACT_PASS')
    print('PILOT_FREEZE_REPAIR_VALIDATION_PASS')
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument('--pre-freeze', action='store_true')
    parser.add_argument('--prelaunch-check-only', action='store_true')
    args = parser.parse_args()
    if args.repo_root.resolve(strict=True) != CHECKOUT:
        raise RuntimeError('PILOT_REPO_ROOT_MISMATCH')
    validate(args.pre_freeze)
    print('PASS_CERT_EXEC_IDENTITY_REPAIR_PILOT_PROTOCOL_FREEZE_V1_VALIDATION')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
