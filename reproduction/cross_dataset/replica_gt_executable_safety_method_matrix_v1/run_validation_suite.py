"""Compile sources without bytecode and run the complete task-local pytest suite."""
from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import sys

from common import write_json
from task_config import TASK_ROOT


def main() -> None:
    sources = sorted(TASK_ROOT.rglob("*.py"))
    for path in sources:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    pytest_support = "C:\\Users\\zlab\\AppData\\Local\\Temp\\fas_cbf_unified_certifier_v1_pytest"
    environment = {**os.environ, "PYTHONPATH": pytest_support, "PYTHONDONTWRITEBYTECODE": "1"}
    completed = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", str(TASK_ROOT / "tests")], cwd=TASK_ROOT.parents[2], env=environment, capture_output=True, text=True)
    match = re.search(r"(\d+) passed", completed.stdout)
    result = {"source_compile": {"status": "PASS_COMPILEALL_EQUIVALENT_NO_PYCACHE", "exit_code": 0, "source_count": len(sources)}, "pytest": {"exit_code": completed.returncode, "passed_count": int(match.group(1)) if match else 0, "stdout": completed.stdout[-2000:], "stderr": completed.stderr[-2000:]}}
    write_json(TASK_ROOT / "report/test_execution.json", result)
    if completed.returncode:
        raise SystemExit("PYTEST_FAILED")
    print("PASS_SOURCE_COMPILE_AND_PYTEST", len(sources), result["pytest"]["passed_count"])


if __name__ == "__main__":
    main()
