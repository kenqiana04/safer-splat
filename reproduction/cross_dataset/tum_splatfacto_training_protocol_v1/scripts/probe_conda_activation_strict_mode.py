#!/usr/bin/env python3
"""Run an isolated activation-only strict-mode probe; never launch training."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("before", "after"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "before":
        shell = """set -euo pipefail
source ~/anaconda3/etc/profile.d/conda.sh
conda activate safer_splat_official
printf 'UNEXPECTED_PASS\\n'
"""
    else:
        shell = """set -eo pipefail
source ~/anaconda3/etc/profile.d/conda.sh
conda activate safer_splat_official
set -u
printf 'CONDA_DEFAULT_ENV=%s\\n' "$CONDA_DEFAULT_ENV"
printf 'CONDA_PREFIX=%s\\n' "$CONDA_PREFIX"
which python
python --version
which ns-train
ns-train --help >/dev/null
ns-eval --help >/dev/null
ns-render dataset --help >/dev/null
printf 'ACTIVATION_PROBE_PASS\\n'
"""
    completed = subprocess.run(
        ["bash", "--noprofile", "--norc", "-c", shell],
        capture_output=True,
        text=True,
        check=False,
        env=os.environ.copy(),
    )
    stdout, stderr = completed.stdout, completed.stderr
    payload = {
        "mode": args.mode,
        "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "hostname": os.uname().nodename,
        "exit_code": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "gfortran_defined_before_probe": "GFORTRAN" in os.environ,
        "unexpected_pass": "UNEXPECTED_PASS" in stdout,
        "activation_probe_pass": "ACTIVATION_PROBE_PASS" in stdout,
        "failure_hook": (re.search(r"[^/\n]*deactivate[^/\n]*\.sh", stderr) or [None])[0],
        "unbound_gfortran_detected": "GFORTRAN" in stderr,
        "nounset_error_detected": "unbound" in stderr or "未绑定的变量" in stderr,
    }
    if args.mode == "before":
        payload["status"] = (
            "REPRODUCED_PRE_ACTIVATION_NOUNSET_FAILURE"
            if completed.returncode != 0 and not payload["unexpected_pass"] and payload["failure_hook"] and payload["nounset_error_detected"]
            else "BLOCKED_BY_UNREPRODUCED_LAUNCH_FAILURE"
        )
    else:
        payload["status"] = (
            "PASS_CONDA_ACTIVATION_THEN_NOUNSET"
            if completed.returncode == 0 and payload["activation_probe_pass"]
            else "BLOCKED_BY_ACTIVATION_PROBE"
        )
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
