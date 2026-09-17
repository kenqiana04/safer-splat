#!/usr/bin/env python3
"""Post-collection-only oracle; never called by the collection launcher."""
from __future__ import annotations

import argparse
import csv
import json
import math
import random
import statistics
import sys
from pathlib import Path
from typing import Any

from freeze_authorities import TRIALS, read
from run_post_repair_v3_paired_validation_v1 import (CHECKOUT, ROOT, TASK, complete_trial,
                                                     verify_authority_manifests, verify_protocol)


def hard_from_clearance(value: float) -> str:
    if not math.isfinite(value):
        return 'UNKNOWN'
    return 'UNSAFE' if value < 0.0 else 'SAFE'


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = fraction * (len(ordered) - 1)
    lo, hi = math.floor(index), math.ceil(index)
    return ordered[lo] if lo == hi else ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo)


def bootstrap(deltas: list[float]) -> dict[str, float | int]:
    if len(deltas) != 85 or any(not math.isfinite(x) for x in deltas):
        raise RuntimeError('PAIRED_85_FINITE_DELTAS_REQUIRED')
    rng = random.Random(20260911)
    means = [statistics.mean(deltas[rng.randrange(85)] for _ in range(85)) for _ in range(10000)]
    return {'resamples': 10000, 'seed': 20260911, 'lower95': percentile(means, .025),
            'upper95': percentile(means, .975)}


def decide(*, integrity: bool, unknown: int, active_hard: int, active_only: int,
           ni_lower: float | None) -> str:
    if not integrity or unknown or ni_lower is None or not math.isfinite(ni_lower):
        return 'BLOCK_POST_REPAIR_V3_PAIRED_VALIDATION_INTEGRITY'
    hard_pass = active_hard == 0 and active_only == 0
    ni_pass = ni_lower > -0.02
    if hard_pass and ni_pass:
        return 'PASS_POST_REPAIR_V3_PAIRED_VALIDATION_ON_FROZEN_STONEHENGE_BENCHMARK'
    if not hard_pass and not ni_pass:
        return 'FAIL_POST_REPAIR_V3_HARD_SAFETY_AND_PROGRESS_NI_GATES'
    return ('FAIL_POST_REPAIR_V3_HARD_SAFETY_GATE' if not hard_pass else
            'FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE')


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n', encoding='utf-8')


def active_states(raw: Path) -> list[tuple[float, ...]]:
    rows = [json.loads(line) for line in (raw / 'cycle_observations.jsonl').read_text(encoding='utf-8').splitlines()]
    if not rows:
        raise RuntimeError('ACTIVE_STATE_EVIDENCE_EMPTY')
    states = [tuple(rows[0]['pre_state'])]
    for row in rows:
        if row['committed']:
            if row['post_state'] is None:
                raise RuntimeError('COMMITTED_POST_STATE_MISSING')
            states.append(tuple(row['post_state']))
    return states


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--post-collection-authorized', action='store_true')
    args = parser.parse_args()
    if not args.post_collection_authorized:
        print('ANALYZER_FROZEN_NOT_EXECUTED')
        return 3
    if not ROOT.is_dir() or any(not complete_trial(ROOT, trial) for trial in TRIALS):
        raise RuntimeError('ANALYSIS_REQUIRES_85_OF_85_IMMUTABLE_ACTIVE_LOCKS')
    collection = read(ROOT / 'POST_REPAIR_V3_PAIRED_COLLECTION_SUMMARY.json')
    if collection['status'] != 'PASS_POST_REPAIR_V3_PAIRED_COLLECTION_INTEGRITY' or collection['trials_completed'] != list(TRIALS):
        raise RuntimeError('COLLECTION_INTEGRITY_NOT_PASS')
    protocol = verify_protocol()
    reference = verify_authority_manifests()['reference_outcomes']
    ref_by_id = {row['trial_id']: row for row in reference['values']}
    if len(ref_by_id) != 85 or any(ref_by_id[t]['unknown_segment_count'] for t in TRIALS):
        raise RuntimeError('FROZEN_REFERENCE_OUTCOMES_INCOMPLETE')

    # GPU oracle imports happen only after all 85 immutable Active locks pass.
    import numpy as np
    import torch
    sys.path[:0] = [str(CHECKOUT / 'reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1'), str(CHECKOUT)]
    from splat.gsplat_utils import GSplatLoader
    from adapters.gaussian_barrier_adapter import SourceGaussianBarrierAdapter
    from run_post_repair_v3_paired_validation_v1 import import_file
    v2 = import_file(CHECKOUT / 'reproduction/pilot/active_runtime_pilot_v2/run_active_runtime_pilot_v2.py',
                     '_post_repair_v3_frozen_hard_oracle')
    loader = GSplatLoader((CHECKOUT / 'outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml').resolve(strict=True),
                         torch.device('cuda:0'))
    radius = 0.015

    def query(point: Any, **kwargs: Any) -> Any:
        if not torch.is_tensor(point):
            point = torch.as_tensor(point, device=torch.device('cuda:0'), dtype=torch.float32)
        return loader.query_distance(point, **kwargs)

    provider = SourceGaussianBarrierAdapter(query, protocol['map']['identity'], radius, int(loader.means.shape[0]))
    rows: list[dict[str, Any]] = []
    for trial in TRIALS:
        raw = ROOT / 'raw' / f'trial_{trial}'
        summary = read(raw / 'trial_summary.json')
        states = active_states(raw)
        if len(states) != summary['plant_commit_count'] + 1 or tuple(summary['start_state']) != states[0]:
            raise RuntimeError('ACTIVE_STATE_SEQUENCE_OR_START_IDENTITY_MISMATCH:' + str(trial))
        violations = unknown = 0
        clearances: list[float] = []
        for before, after in zip(states[:-1], states[1:]):
            status, clearance = v2.certify_segment_clearance(provider, np.asarray(before[:3]),
                                                               np.asarray(after[:3]), radius)
            violations += status == 'UNSAFE'
            unknown += status not in ('SAFE', 'UNSAFE')
            if clearance is not None:
                clearances.append(float(clearance))
        start, final, goal = (np.asarray(states[0][:3]), np.asarray(states[-1][:3]),
                              np.asarray(summary['goal_state'][:3]))
        d0 = float(np.linalg.norm(start - goal))
        d1 = float(np.linalg.norm(final - goal))
        if d0 <= 0 or not math.isfinite(d0) or not math.isfinite(d1):
            raise RuntimeError('PROGRESS_DENOMINATOR_OR_DISTANCE_INVALID:' + str(trial))
        progress = (d0 - d1) / d0
        ref = ref_by_id[trial]
        delta = progress - float(ref['normalized_progress'])
        rows.append({'trial_id': trial, 'active_hard_violation': violations > 0,
                     'active_hard_violation_segments': violations, 'active_unknown_segments': unknown,
                     'active_min_hard_clearance_q': min(clearances) if clearances else None,
                     'reference_hard_violation': bool(ref['hard_violation']),
                     'active_only_hard_discordant': violations > 0 and not ref['hard_violation'],
                     'active_progress': progress, 'reference_progress': ref['normalized_progress'],
                     'paired_progress_delta': delta, 'primary_commits': summary['primary_navigation_commit_count'],
                     'backup_commits': summary['retained_backup_commit_count'],
                     'terminal_commits': summary['terminal_commit_count'],
                     'l3_status_counts': summary['L3_status_counts'],
                     'deadline_status_counts': summary['deadline_status_counts']})
    unknown = sum(row['active_unknown_segments'] for row in rows)
    active_hard = sum(row['active_hard_violation'] for row in rows)
    active_only = sum(row['active_only_hard_discordant'] for row in rows)
    deltas = [row['paired_progress_delta'] for row in rows]
    ci = bootstrap(deltas) if unknown == 0 else None
    decision = decide(integrity=True, unknown=unknown, active_hard=active_hard, active_only=active_only,
                      ni_lower=None if ci is None else float(ci['lower95']))
    fields = ('trial_id', 'active_hard_violation', 'active_hard_violation_segments', 'active_unknown_segments',
              'active_min_hard_clearance_q', 'reference_hard_violation', 'active_only_hard_discordant',
              'active_progress', 'reference_progress', 'paired_progress_delta', 'primary_commits',
              'backup_commits', 'terminal_commits', 'l3_status_counts', 'deadline_status_counts')
    with (ROOT / 'POST_REPAIR_V3_PAIRED_TRIAL_RESULTS.csv').open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    write_json(ROOT / 'POST_REPAIR_V3_PAIRED_PROGRESS_ANALYSIS.json',
               {'n': 85, 'mean_delta': statistics.mean(deltas), 'median_delta': statistics.median(deltas),
                'min_delta': min(deltas), 'max_delta': max(deltas), 'bootstrap_percentile_95': ci,
                'margin': -0.02, 'strict_ni_pass': ci is not None and ci['lower95'] > -0.02})
    write_json(ROOT / 'POST_REPAIR_V3_PAIRED_HARD_SAFETY_ANALYSIS.json',
               {'active_hard_violation_trials': active_hard, 'active_only_hard_discordant_pairs': active_only,
                'reference_hard_violation_trials': 0, 'unresolved_hard_safety_unknown_segments': unknown,
                'hard_gate_pass': active_hard == active_only == unknown == 0,
                'zero_threshold_tolerance': True, 'old_v3_decision_unchanged': 'FAIL_V3_HARD_SAFETY_GATE',
                'new_post_repair_decision': decision})
    write_json(ROOT / 'POST_REPAIR_V3_PAIRED_CONTINUITY_ANALYSIS.json', collection['continuity_totals'])
    write_json(ROOT / 'POST_REPAIR_V3_PAIRED_ROUTING_ANALYSIS.json',
               {'descriptive_only': True, 'aggregate': collection['routing_totals'],
                'per_trial': [{k: row[k] for k in ('trial_id', 'primary_commits', 'backup_commits',
                           'terminal_commits', 'l3_status_counts', 'deadline_status_counts',
                           'paired_progress_delta', 'active_hard_violation')} for row in rows]})
    write_json(ROOT / 'POST_REPAIR_V3_PAIRED_WITNESS_ANALYSIS.json',
               {'pre_registered_trials': [22, 28, 57, 59],
                'descriptive_only': True, 'rows': [row for row in rows if row['trial_id'] in (22, 28, 57, 59)]})
    report = ROOT / 'report' / 'REPORT_POST_REPAIR_V3_PAIRED_VALIDATION_V1.md'
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(f'# Post-Repair V3 paired validation\n\nOld frozen V3: FAIL_V3_HARD_SAFETY_GATE (unchanged).\n'
                      f'New post-repair result: {decision}.\n\n85 known, repeatedly exposed Stonehenge trials; '
                      'not a pristine holdout or cross-scene generalization.\n'
                      f'Active hard violations: {active_hard}; active-only discordance: {active_only}; '
                      f'unknown segments: {unknown}.\nProgress delta mean: {statistics.mean(deltas)}; '
                      f'95% paired bootstrap: {ci}.\nNo radius tuning or Reference rerun.\n', encoding='utf-8')
    print(decision)
    return 0 if decision.startswith(('PASS_', 'FAIL_')) else 2


if __name__ == '__main__':
    raise SystemExit(main())
