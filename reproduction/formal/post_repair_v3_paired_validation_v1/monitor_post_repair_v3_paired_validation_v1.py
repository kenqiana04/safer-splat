#!/usr/bin/env python3
"""Compact read-only progress; never opens scientific outcome distributions."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path('/disk1/zlab/v3_repair_records/post_repair_v3_paired_validation_v1_20260917')


def main() -> int:
    if not ROOT.is_dir():
        print(json.dumps({'status': 'NOT_LAUNCHED', 'completed_trial_count': 0}))
        return 0
    summary = ROOT / 'POST_REPAIR_V3_PAIRED_COLLECTION_SUMMARY.json'
    if not summary.is_file():
        print(json.dumps({'status': 'ROOT_EXISTS_NO_COLLECTION_SUMMARY', 'completed_trial_count': 0}))
        return 0
    record = json.loads(summary.read_text(encoding='utf-8'))
    print(json.dumps({'status': record['status'], 'completed_trial_count': len(record['trials_completed']),
                      'latest_trial_id': record['trials_completed'][-1] if record['trials_completed'] else None,
                      'planned_trial_count': len(record['trials_planned'])}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
