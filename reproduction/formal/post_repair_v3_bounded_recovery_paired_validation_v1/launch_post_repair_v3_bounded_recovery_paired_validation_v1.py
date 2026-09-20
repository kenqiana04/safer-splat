#!/usr/bin/env python3
"""Future-only serial launcher; --help is safe during protocol freeze."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shlex
import subprocess
import sys

from validate_post_repair_v3_bounded_recovery_paired_validation_v1 import (
    LOCK, PROTOCOL, REPO, TASK, git, read, sha, validate_freeze,
)
from run_post_repair_v3_bounded_recovery_trial_v1 import AUTH_NAME, TOKEN_ENV

LAUNCH_MARKER = "POST_REPAIR_V3_BOUNDED_RECOVERY_LAUNCH_AUTHORIZATION.json"


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")


def launch() -> None:
    p = read(PROTOCOL)
    validate_freeze(require_lock=True, require_absent_root=True)
    root = Path(p["future_result_root"])
    session = p["future_tmux_session"]
    if subprocess.run(["tmux", "has-session", "-t", session], capture_output=True).returncode == 0:
        raise RuntimeError("TASK_TMUX_SESSION_ALREADY_EXISTS")
    token = secrets.token_hex(32)
    root.mkdir(parents=False, exist_ok=False)
    write(root / LAUNCH_MARKER, {
        "schema": "POST_REPAIR_V3_BOUNDED_RECOVERY_LAUNCH_AUTHORIZATION_V1",
        "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
        "protocol_sha256": sha(PROTOCOL), "execution_lock_sha256": sha(LOCK),
        "source_head": git("rev-parse", "HEAD"),
        "trials": p["cohort"]["trial_order"], "session": session,
    })
    command = shlex.join([p["environment"]["python"], str(Path(__file__).resolve()),
                          "--batch-internal", "--launch-token", token])
    result = subprocess.run(["tmux", "new-session", "-d", "-s", session, command],
                            text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError("TMUX_LAUNCH_FAILED_PRESERVE_RESULT_ROOT:" + result.stderr.strip())
    print(json.dumps({"status": "FUTURE_FORMAL85_COLLECTION_LAUNCHED", "session": session,
                      "result_root": str(root), "trials": p["cohort"]["trial_order"]}, sort_keys=True))


def batch_internal(token: str) -> int:
    p = read(PROTOCOL)
    root = Path(p["future_result_root"])
    marker = read(root / LAUNCH_MARKER)
    if marker != {"schema": "POST_REPAIR_V3_BOUNDED_RECOVERY_LAUNCH_AUTHORIZATION_V1",
                   "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
                   "protocol_sha256": sha(PROTOCOL), "execution_lock_sha256": sha(LOCK),
                   "source_head": git("rev-parse", "HEAD"),
                   "trials": p["cohort"]["trial_order"], "session": p["future_tmux_session"]}:
        raise RuntimeError("LAUNCH_MARKER_IDENTITY_MISMATCH")
    if os.environ.get("TMUX") is None:
        raise RuntimeError("BATCH_REQUIRES_TASK_TMUX_SESSION")
    child_script = TASK / "run_post_repair_v3_bounded_recovery_trial_v1.py"
    for trial in p["cohort"]["trial_order"]:
        raw = root / "raw" / f"trial_{trial}"
        if raw.exists():
            raise RuntimeError("NO_AUTOMATIC_RETRY_EXISTING_TRIAL:" + str(trial))
        child_token = secrets.token_hex(32)
        env = os.environ.copy()
        env.update({k: str(v) for k, v in p["environment"].items()
                    if k in ("CUDA_VISIBLE_DEVICES", "PYTHONHASHSEED", "PYTHONNOUSERSITE",
                             "PYTHONDONTWRITEBYTECODE", "CUBLAS_WORKSPACE_CONFIG")})
        env[TOKEN_ENV] = child_token
        auth = root / AUTH_NAME
        write(auth, {"trial_id": trial, "result_root": str(root),
                     "source_head": git("rev-parse", "HEAD"),
                     "protocol_sha256": sha(PROTOCOL), "execution_lock_sha256": sha(LOCK),
                     "token_sha256": hashlib.sha256(child_token.encode()).hexdigest(),
                     "parent_pid": os.getpid()})
        stdout_path = root / f"trial_{trial}.stdout.pending"
        stderr_path = root / f"trial_{trial}.stderr.pending"
        try:
            with stdout_path.open("x", encoding="utf-8") as out, stderr_path.open("x", encoding="utf-8") as err:
                proc = subprocess.Popen([p["environment"]["python"], str(child_script), "--one", str(trial)],
                                        cwd=str(REPO), env=env, stdout=out, stderr=err, text=True)
                code = proc.wait()
        finally:
            auth.unlink(missing_ok=True)
        destination = raw if raw.is_dir() else root / "parent_failures" / f"trial_{trial}"
        destination.mkdir(parents=True, exist_ok=True)
        stdout_path.replace(destination / "stdout.log")
        stderr_path.replace(destination / "stderr.log")
        (destination / "process_exit_code.txt").write_text(f"{code}\n", encoding="utf-8")
        (destination / "gpu_released.txt").write_text("true\n", encoding="utf-8")
        # A failure is evidence, never a reason to skip to the next trial.
        if code or not (raw / "runtime_trace_lock.json").is_file():
            write(root / "BATCH_STOP.json", {"trial_id": trial, "process_exit_code": code,
                                              "reason": "CHILD_FAILURE_OR_MISSING_TRACE_LOCK"})
            return code or 2
        write(root / f"trial_{trial}_complete.json", {"trial_id": trial, "process_exit_code": 0,
             "trace_lock_sha256": sha(raw / "runtime_trace_lock.json"),
             "trial_summary_sha256": sha(raw / "trial_summary.json")})
    write(root / "BATCH_COMPLETE.json", {"trial_order": p["cohort"]["trial_order"],
                                          "trials_completed": len(p["cohort"]["trial_order"])})
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--launch", action="store_true", help="Future task only; requires explicit authorization token")
    modes.add_argument("--batch-internal", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--authorize-execution", choices=("EXECUTE_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_V1",))
    parser.add_argument("--launch-token", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.launch:
        if args.authorize_execution != "EXECUTE_POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_V1":
            raise RuntimeError("FUTURE_EXECUTION_TASK_AUTHORIZATION_REQUIRED")
        launch()
        return 0
    if not args.launch_token:
        raise RuntimeError("INTERNAL_LAUNCH_TOKEN_REQUIRED")
    return batch_internal(args.launch_token)


if __name__ == "__main__":
    raise SystemExit(main())
