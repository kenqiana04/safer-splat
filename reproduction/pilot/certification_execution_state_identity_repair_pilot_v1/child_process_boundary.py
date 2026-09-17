#!/usr/bin/env python3
"""Task-local, CPU-only subprocess input contract for the pilot child."""
from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Mapping, Sequence


class ChildProcessSchemaError(RuntimeError):
    """A child would be launched with an invalid process-boundary value."""


def _scalar_string(value: object, location: str) -> str:
    if type(value) is str:
        result = value
    elif type(value) is bool:
        result = "true" if value else "false"
    elif type(value) is int:
        result = str(value)
    elif type(value) is float and math.isfinite(value):
        result = str(value)
    else:
        raise ChildProcessSchemaError(f"CHILD_PROCESS_ENV_SCHEMA_INVALID:{location}:{type(value).__name__}")
    if "\x00" in result:
        raise ChildProcessSchemaError(f"CHILD_PROCESS_ENV_SCHEMA_INVALID:{location}:NUL")
    return result


def normalize_env(base: Mapping[object, object], overrides: Mapping[object, object]) -> dict[str, str]:
    """Convert permitted scalar values explicitly; reject structured values and bad keys."""
    result: dict[str, str] = {}
    for source in (base, overrides):
        for key, value in source.items():
            if type(key) is not str or not key or "=" in key or "\x00" in key:
                raise ChildProcessSchemaError(f"CHILD_PROCESS_ENV_SCHEMA_INVALID:KEY:{type(key).__name__}")
            result[key] = _scalar_string(value, key)
    return result


def normalize_argv(args: Sequence[object], *, numeric_positions: frozenset[int] = frozenset()) -> list[str]:
    if isinstance(args, (str, bytes)) or not args:
        raise ChildProcessSchemaError("CHILD_PROCESS_ARGV_SCHEMA_INVALID:SEQUENCE")
    result: list[str] = []
    for index, value in enumerate(args):
        if isinstance(value, Path):
            item = os.fspath(value)
        elif type(value) is str:
            item = value
        elif index in numeric_positions and type(value) is int:
            item = str(value)
        else:
            raise ChildProcessSchemaError(f"CHILD_PROCESS_ARGV_SCHEMA_INVALID:{index}:{type(value).__name__}")
        if not item or "\x00" in item:
            raise ChildProcessSchemaError(f"CHILD_PROCESS_ARGV_SCHEMA_INVALID:{index}:EMPTY_OR_NUL")
        result.append(item)
    return result


def validate_popen_boundary(command: Sequence[object], env: Mapping[object, object], *,
                            cwd: object = None, executable: object = None) -> tuple[list[str], dict[str, str]]:
    """Return inputs that are fully valid for subprocess.Popen, without starting it."""
    argv = normalize_argv(command)
    normalized_env = normalize_env({}, env)
    for name, value in (("CWD", cwd), ("EXECUTABLE", executable)):
        if value is not None:
            if not isinstance(value, (str, Path)) or not os.fspath(value) or "\x00" in os.fspath(value):
                raise ChildProcessSchemaError(f"CHILD_PROCESS_{name}_SCHEMA_INVALID")
    return argv, normalized_env
