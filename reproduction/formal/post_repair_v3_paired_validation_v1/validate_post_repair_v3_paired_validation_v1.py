#!/usr/bin/env python3
"""CPU-only validator for frozen protocol, authority and harness identity."""
from __future__ import annotations

import argparse
import ast
import json
import subprocess
from pathlib import Path

from freeze_authorities import TRIALS, read, semantic, sha
from run_post_repair_v3_paired_validation_v1 import (BASE, BRANCH, CHECKOUT, LOCK, ROOT, TASK,
                                                     verify_source_and_map)

HARNESS = ('run_post_repair_v3_paired_validation_v1.py',
           'launch_post_repair_v3_paired_validation_v1.sh',
           'validate_post_repair_v3_paired_validation_v1.py',
           'monitor_post_repair_v3_paired_validation_v1.py',
           'analyze_post_repair_v3_paired_validation_v1.py')


def validate(*, require_lock: bool) -> dict[str, object]:
    checks = verify_source_and_map(require_lock=require_lock, require_absent_root=True)
    p = read(TASK / 'POST_REPAIR_V3_PAIRED_PROTOCOL.json')
    for name in HARNESS:
        path = TASK / name
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError('MISSING_HARNESS:' + name)
    for name in HARNESS:
        if name.endswith('.py'):
            ast.parse((TASK / name).read_text(encoding='utf-8'), filename=name)
    analyzer = (TASK / HARNESS[-1]).read_text(encoding='utf-8')
    if ("--post-collection-authorized" not in analyzer or 'ANALYZER_FROZEN_NOT_EXECUTED' not in analyzer
            or 'certify_segment_clearance' not in analyzer or "-0.02" not in analyzer):
        raise RuntimeError('ANALYZER_FAIL_CLOSED_CONTRACT_MISSING')
    if (len(TRIALS) != 85 or len(set(TRIALS)) != 85 or p['cohort']['trial_order'] != list(TRIALS)
            or p['historical_witnesses'] != [22, 28, 57, 59]
            or p['reference_authority']['rerun_authorized'] is not False
            or p['scientific_boundaries']['scientific_analysis_performed_during_freeze'] is not False):
        raise RuntimeError('COHORT_REFERENCE_OR_WITNESS_CONTRACT_DRIFT')
    if require_lock:
        lock = read(LOCK)
        if (lock['protocol_freeze_commit'] != lock['harness_repair_commit']
                or lock['harness_sha256'] != {name: sha(TASK / name) for name in HARNESS}
                or lock['exact_trial_order'] != list(TRIALS)
                or lock['old_v3_frozen_decision'] != 'FAIL_V3_HARD_SAFETY_GATE'
                or lock['future_result_root'] != str(ROOT)
                or lock['protocol_semantic_sha256'] != semantic(p)):
            raise RuntimeError('EXECUTION_LOCK_CONTENT_DRIFT')
        if subprocess.run(['git', '-C', str(CHECKOUT), 'merge-base', '--is-ancestor',
                           lock['protocol_freeze_commit'], 'HEAD']).returncode:
            raise RuntimeError('PROTOCOL_COMMIT_NOT_ANCESTOR')
        if subprocess.run(['git', '-C', str(CHECKOUT), 'status', '--porcelain', '--',
                           'reproduction/formal/post_repair_v3_paired_validation_v1'],
                          capture_output=True, text=True, check=True).stdout.strip():
            raise RuntimeError('FROZEN_TASK_DIRECTORY_DIRTY')
    if ROOT.exists():
        raise RuntimeError('FUTURE_RESULT_ROOT_NOT_ABSENT')
    return {'status': 'PASS_POST_REPAIR_V3_PAIRED_PROTOCOL_VALIDATION_V1', 'checks': checks,
            'harness_files': list(HARNESS), 'harness_hashes': {name: sha(TASK / name) for name in HARNESS},
            'lock_present': LOCK.is_file(), 'lock_required': require_lock,
            'gpu_execution_count': 0, 'tmux_count': 0, 'active_trial_count': 0,
            'runtime_cycle_count': 0, 'plant_commit_count': 0, 'reference_rerun_count': 0,
            'scientific_analyzer_execution_count': 0, 'base_head': BASE, 'branch': BRANCH}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--pre-freeze', action='store_true')
    args = parser.parse_args()
    print(json.dumps(validate(require_lock=not args.pre_freeze), indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
