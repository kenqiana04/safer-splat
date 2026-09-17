#!/usr/bin/env python3
"""CPU-only regression for the exact attempt0 subprocess boundary failure."""
from __future__ import annotations

import os
from pathlib import Path

from child_process_boundary import (ChildProcessSchemaError, normalize_argv,
                                    normalize_env, validate_popen_boundary)
import run_cert_exec_identity_repair_pilot_v1 as pilot


def rejects(callback, reason: str) -> None:
    try:
        callback()
    except ChildProcessSchemaError as exc:
        assert str(exc).startswith(reason), str(exc)
    else:
        raise AssertionError('invalid child-process value passed')


def main() -> None:
    # Replay only the attempt0 input construction; never spawn a child or use GPU.
    original_env = pilot.protocol()['environment']
    assert {key: type(value).__name__ for key, value in original_env.items()
            if type(value) is not str} == {'physical_gpu': 'int'}
    assert original_env['physical_gpu'] == 1
    try:
        os.fsencode(original_env['physical_gpu'])
    except TypeError:
        pass
    else:
        raise AssertionError('attempt0 Popen fsencode failure not reproduced')
    assert pilot.attempt0_immutable_check()['inventory'] == pilot.root_manifest(pilot.ATTEMPT0_ROOT)

    values = normalize_env({'BASE': 'unchanged'}, {'I': 1, 'B': True, 'F': 0.05, 'S': 'same'})
    assert values == {'BASE': 'unchanged', 'I': '1', 'B': 'true', 'F': '0.05', 'S': 'same'}
    assert normalize_env({}, {'B': False})['B'] == 'false'
    for bad in (None, {}, [], set(), (1,)):
        rejects(lambda bad=bad: normalize_env({}, {'BAD': bad}), 'CHILD_PROCESS_ENV_SCHEMA_INVALID:BAD:')
    rejects(lambda: normalize_env({}, {1: 'value'}), 'CHILD_PROCESS_ENV_SCHEMA_INVALID:KEY:')
    rejects(lambda: normalize_env({}, {'BAD=KEY': 'value'}), 'CHILD_PROCESS_ENV_SCHEMA_INVALID:KEY:')
    rejects(lambda: normalize_env({}, {'BAD': float('nan')}), 'CHILD_PROCESS_ENV_SCHEMA_INVALID:BAD:')
    rejects(lambda: normalize_env({}, {'BAD': 'nul\x00value'}), 'CHILD_PROCESS_ENV_SCHEMA_INVALID:BAD:')

    assert normalize_argv([Path('/bin/true'), '--one', '5']) == ['/bin/true', '--one', '5']
    assert normalize_argv(['/bin/true', '--one', 5], numeric_positions=frozenset({2})) == ['/bin/true', '--one', '5']
    rejects(lambda: normalize_argv(['/bin/true', '--one', 5]), 'CHILD_PROCESS_ARGV_SCHEMA_INVALID:2:')
    rejects(lambda: normalize_argv(['/bin/true', {}]), 'CHILD_PROCESS_ARGV_SCHEMA_INVALID:1:')
    rejects(lambda: normalize_argv(['/bin/true', 'bad\x00arg']), 'CHILD_PROCESS_ARGV_SCHEMA_INVALID:1:')

    command = normalize_argv([original_env['python'], Path(__file__), '--one', '5'])
    env = normalize_env(os.environ.copy(), {**original_env, pilot.TOKEN_ENV: 'fixture'})
    checked_argv, checked_env = validate_popen_boundary(command, env, cwd=Path('/tmp'), executable=None)
    assert checked_argv == command and checked_env['physical_gpu'] == '1'
    assert all(type(key) is str and type(value) is str for key, value in checked_env.items())
    rejects(lambda: validate_popen_boundary(['/bin/true'], {'BAD': None}),
            'CHILD_PROCESS_ENV_SCHEMA_INVALID:BAD:')
    rejects(lambda: validate_popen_boundary(['/bin/true'], {'OK': '1'}, cwd=5),
            'CHILD_PROCESS_CWD_SCHEMA_INVALID')

    assert pilot.digest(pilot.PROTOCOL) == '9fb0992b30edbb7a0a2ec48b646a8645eb93aee1805799170dd62a177a03abee'
    assert pilot.semantic(pilot.protocol()) == '92e692b4996b3583c91c03faad542850c8f247ce6f26c96503ec861421baca46'
    assert not pilot.ROOT.exists()
    assert pilot.classify_changed_paths(['reproduction/runtime/fake_mutation.py'])['scientific_runtime_protected']
    print('PASS_CERT_EXEC_IDENTITY_PILOT_CHILD_PROCESS_BOUNDARY_CPU_REGRESSION')


if __name__ == '__main__':
    main()
