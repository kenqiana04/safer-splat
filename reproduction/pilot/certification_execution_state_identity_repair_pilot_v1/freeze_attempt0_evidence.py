#!/usr/bin/env python3
"""Freeze the failed, pre-runtime attempt without writing to its result root."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

import run_cert_exec_identity_repair_pilot_v1 as pilot


def main() -> None:
    root = pilot.ATTEMPT0_ROOT
    target = pilot.ATTEMPT0_MANIFEST
    if target.exists() or not root.is_dir():
        raise RuntimeError('ATTEMPT0_FREEZE_TARGET_OR_SOURCE_INVALID')
    log = (root / 'launcher.log').read_text(encoding='utf-8')
    if ('PASS_ACTIVE_RUNTIME_SMOKE_V3_GPU_PREFLIGHT' not in log
            or 'TypeError: expected str, bytes or os.PathLike object, not int' not in log
            or (root / 'raw/trial_5').exists()
            or (root / 'trial_5_stdout.tmp').stat().st_size
            or (root / 'trial_5_stderr.tmp').stat().st_size):
        raise RuntimeError('ATTEMPT0_FAILURE_CLASSIFICATION_NOT_SUPPORTED')
    environment = pilot.protocol()['environment']
    invalid = {key: type(value).__name__ for key, value in environment.items() if type(value) is not str}
    if invalid != {'physical_gpu': 'int'} or environment['physical_gpu'] != 1:
        raise RuntimeError('ATTEMPT0_CHILD_ENV_ROOT_CAUSE_NOT_EXACT')
    try:
        os.fsencode(environment['physical_gpu'])
    except TypeError:
        pass
    else:
        raise RuntimeError('ATTEMPT0_POPEN_TYPE_FAILURE_NOT_REPRODUCED')
    tmux_stopped = subprocess.run(['tmux', 'has-session', '-t', 'cert-exec-identity-repair-pilot-v1'],
                                  capture_output=True).returncode != 0
    if not tmux_stopped:
        raise RuntimeError('ATTEMPT0_TMUX_STILL_RUNNING')
    gpu = subprocess.run(['nvidia-smi', '-i', '1', '--query-compute-apps=pid,used_gpu_memory',
                          '--format=csv,noheader'], check=True, capture_output=True, text=True)
    manifest = {
        'schema': 'CERT_EXEC_IDENTITY_REPAIR_PILOT_ATTEMPT0_IMMUTABLE_EVIDENCE_V1',
        'root': str(root),
        'classification': 'TRIAL5_PRE_RUNTIME_CHILD_ENV_VALUE_TYPE_FAILURE',
        'inventory': pilot.root_manifest(root),
        'launcher_log_sha256': pilot.digest(root / 'launcher.log'),
        'gpu_preflight_sha256': pilot.digest(root / 'raw/gpu_preflight.json'),
        'child_authorization_sha256': pilot.digest(root / pilot.AUTH_NAME),
        'stdout_tmp_sha256': pilot.digest(root / 'trial_5_stdout.tmp'),
        'stderr_tmp_sha256': pilot.digest(root / 'trial_5_stderr.tmp'),
        'tmux_stopped_at_freeze': True,
        'gpu1_compute_processes_at_freeze': gpu.stdout.strip().splitlines(),
        'gpu1_idle_at_freeze': not bool(gpu.stdout.strip()),
        'trial_process_count': 0, 'cycles': 0, 'plant_commits': 0,
        'scientific_analysis_count': 0,
        'child_env_root_cause': {'key': 'physical_gpu', 'type': 'int',
                                 'value': 1, 'source': 'PILOT_PROTOCOL.json.environment.physical_gpu',
                                 'path': 'run_batch env.update(protocol()[environment]) -> subprocess.Popen(env)',
                                 'os_fsencode_type_error_reproduced_cpu_only': True},
        'attempt0_root_mutated': False,
    }
    pilot.write(target, manifest)
    print(json.dumps({'status': 'ATTEMPT0_IMMUTABLE_EVIDENCE_FROZEN',
                      'file_count': manifest['inventory']['file_count'],
                      'semantic_root_sha256': manifest['inventory']['semantic_root_sha256'],
                      'gpu1_idle_at_freeze': manifest['gpu1_idle_at_freeze']}, sort_keys=True))


if __name__ == '__main__':
    main()
