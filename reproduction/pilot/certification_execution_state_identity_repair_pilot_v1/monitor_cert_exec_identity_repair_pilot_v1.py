#!/usr/bin/env python3
"""Read-only compact progress snapshot; never starts, retries, or analyzes trials."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

ROOT = Path('/disk1/zlab/v3_repair_records/cert_exec_identity_repair_pilot_v1_20260916')
SESSION = 'cert-exec-identity-repair-pilot-v1'


def main() -> None:
    active = subprocess.run(['tmux', 'has-session', '-t', SESSION], capture_output=True).returncode == 0
    summary = ROOT / 'PILOT_COLLECTION_SUMMARY.json'
    data = json.loads(summary.read_text()) if summary.is_file() else {}
    print(json.dumps({'schema': 'CERT_EXEC_IDENTITY_REPAIR_PILOT_PROGRESS_V1',
                      'tmux_active': active, 'result_root_exists': ROOT.exists(),
                      'trials_completed': data.get('trials_completed', []),
                      'completed_cycles': data.get('completed_cycles', 0),
                      'status': data.get('status', 'NOT_STARTED_OR_NOT_SUMMARIZED')}, sort_keys=True))


if __name__ == '__main__':
    main()
