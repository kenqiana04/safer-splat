"""Compile all task Python files and execute the local blocker-contract tests."""
from __future__ import annotations

import os
from pathlib import Path
import py_compile
import re
import shutil
import subprocess
import sys
import tempfile

from common import write_json
from task_config import TASK_ROOT


def main() -> None:
    compile_root = Path(tempfile.mkdtemp(prefix="repact_compile_"))
    sources = sorted(TASK_ROOT.rglob("*.py"))
    errors = []
    try:
        for index, source in enumerate(sources):
            try:
                py_compile.compile(str(source), cfile=str(compile_root / f"{index:04d}.pyc"), doraise=True)
            except py_compile.PyCompileError as exc:
                errors.append(f"{source.relative_to(TASK_ROOT)}: {exc.msg}")
    finally:
        shutil.rmtree(compile_root, ignore_errors=True)
    tested = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", str(TASK_ROOT / "tests"), "--disable-warnings"], capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    match = re.search(r"(\d+) passed", tested.stdout)
    evidence = {"syntax_compile": {"exit_code": 1 if errors else 0, "source_count": len(sources), "errors": errors, "temporary_outputs_removed": not compile_root.exists()},
                "pytest": {"exit_code": tested.returncode, "passed_count": int(match.group(1)) if match else None, "stdout": tested.stdout.strip(), "stderr": tested.stderr.strip()},
                "repository_pycache_written": False}
    write_json(TASK_ROOT / "report/test_execution.json", evidence)
    if errors or tested.returncode:
        raise SystemExit("VALIDATION_SUITE_FAILED")
    print("PASS_SYNTAX_AND_PYTEST", len(sources), evidence["pytest"]["passed_count"])


if __name__ == "__main__":
    main()
