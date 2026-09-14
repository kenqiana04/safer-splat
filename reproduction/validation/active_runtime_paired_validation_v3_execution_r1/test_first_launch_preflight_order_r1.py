#!/usr/bin/env python3
"""CPU-only regression for R1 first-launch result-root sequencing."""
from __future__ import annotations
import argparse
from pathlib import Path

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--task-dir", type=Path, required=True); args = ap.parse_args()
    launcher = (args.task_dir / "start_v3_paired_validation_r1_tmux.sh").read_text(encoding="utf-8")
    lines = launcher.splitlines()
    static = launcher.index("--static-preflight")
    validator = launcher.index('"$VALIDATOR" --repo-root')
    mkdir = launcher.index('mkdir -p "$RESULT_ROOT"')
    gpu = launcher.index("--gpu-preflight")
    batch = launcher.index("--batch")
    assert static < validator < mkdir < gpu < batch, "FIRST_LAUNCH_ORDER_INVALID"
    assert "verify_fresh_result_root(DEFAULT_RESULT_ROOT, False)" in (args.task_dir / "run_active_runtime_v3_paired_validation_r1.py").read_text(encoding="utf-8")
    assert "FIRST_LAUNCH_RESULT_ROOT_ALREADY_EXISTS" in launcher
    assert "--resume" not in launcher[static:validator] and "--resume" not in launcher[validator:mkdir]
    assert "--resume" in launcher[gpu:batch] and "--resume" in launcher[batch:]
    assert "analyze_active_runtime" not in launcher
    assert "launcher.log" in launcher
    print("PASS_R1_FIRST_LAUNCH_PREFLIGHT_ORDER_REGRESSION")
    print("GPU_PREFLIGHT_EXECUTED=0")
    print("ACTIVE_R1_TRIAL_EXECUTED=0")
    print("ANALYZER_EXECUTED=0")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
