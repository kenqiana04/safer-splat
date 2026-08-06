"""Run exactly three fresh pure-generator processes and record their canonical identities."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from common import write_json
from task_config import TASK_ROOT


def main() -> None:
    code = "from alternative_library.directional_library import build_directional_library; from alternative_library.canonical_serialization import canonical_sha256; import numpy as n; r=build_directional_library((1.,0.,0.),(-.02,0.,0.),(1.,2.,0.),'FINITE',(0,),n.array(((0.,0.,0.),))); print(canonical_sha256({'slots':[(s.candidate_id,s.availability.value,s.acceleration,s.duplicate_of) for s in r.slots]}))"
    environment = {**os.environ, "PYTHONPATH": str(TASK_ROOT), "PYTHONDONTWRITEBYTECODE": "1"}
    values = [subprocess.run([sys.executable, "-B", "-c", code], check=True, capture_output=True, text=True, env=environment).stdout.strip() for _ in range(3)]
    mismatch = max(0, len(set(values)) - 1)
    result = {"status": "PASS_THREE_PROCESS_DETERMINISM" if mismatch == 0 else "BLOCKED_BY_ALTERNATIVE_LIBRARY_NONDETERMINISM", "process_determinism_run_count": 3, "process_determinism_mismatch_count": mismatch, "canonical_sha256_values": values}
    write_json(TASK_ROOT / "audits/three_process_determinism.json", result)
    if mismatch:
        raise SystemExit(result["status"])
    print(result["status"], values[0])


if __name__ == "__main__":
    main()
