#!/usr/bin/env python3
"""Run the one authorized post-repair GPU regression without resuming the old cohort."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


PARENT_EXECUTION_HEAD = "bf0a0792932c02e243236f1b316a41037c95fc69"
REPAIR_BRANCH = "repair-v3-trace-cardinality-post-l2-v1"
PROTOCOL_SHA256 = "2de32310c84db49f0b8982e2bb63f15d234732250a5c3ddf859fdb75386439c5"
TRIAL_ID = 73
TASK_REL = "reproduction/validation/active_runtime_v3_trace_cardinality_repair_v1"
PAIRED_REL = "reproduction/validation/active_runtime_paired_validation_v3_execution"
PROTOCOL_REL = "reproduction/validation/active_runtime_paired_validation_v3"
ALLOWED_RUNTIME = {
    "reproduction/runtime/active_runtime_assurance_v2/active_cycle.py",
    "reproduction/runtime/active_runtime_assurance_v2/supervisor.py",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def git(checkout: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(checkout), *args],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()


def load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("MODULE_IMPORT_UNAVAILABLE:" + str(path))
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
    return module


def changed_paths(checkout: Path) -> set[str]:
    changed = set(filter(None, git(checkout, "diff", "--name-only", PARENT_EXECUTION_HEAD).splitlines()))
    for line in git(checkout, "status", "--porcelain").splitlines():
        changed.add(line[2:].lstrip().replace("\\", "/").split(" -> ")[-1])
    return changed


def static_preflight(checkout: Path, map_root: Path, paired: Any) -> dict[str, Any]:
    if git(checkout, "branch", "--show-current") != REPAIR_BRANCH:
        raise RuntimeError("REPAIR_BRANCH_MISMATCH")
    if subprocess.run(
        ["git", "-C", str(checkout), "merge-base", "--is-ancestor", PARENT_EXECUTION_HEAD, "HEAD"],
        check=False,
    ).returncode:
        raise RuntimeError("PARENT_EXECUTION_HEAD_NOT_ANCESTOR")
    protocol_path = checkout / PROTOCOL_REL / "V3_PAIRED_VALIDATION_PROTOCOL.json"
    if sha256_file(protocol_path) != PROTOCOL_SHA256:
        raise RuntimeError("FROZEN_PROTOCOL_HASH_MISMATCH")
    protocol, _input_lock, reference = paired.frozen(checkout)
    paired.verify_cohort(checkout, protocol)
    map_artifacts = paired.verify_map(protocol, map_root)
    paired.verify_reference(reference)

    changed = changed_paths(checkout)
    disallowed = sorted(
        path for path in changed
        if path not in ALLOWED_RUNTIME
        and not path.startswith(TASK_REL + "/")
    )
    if disallowed:
        raise RuntimeError("OUT_OF_SCOPE_CHANGE:" + ",".join(disallowed))

    source_hashes = {
        path: sha256_file(checkout / path)
        for path in sorted(ALLOWED_RUNTIME)
    }
    source_lock = {
        "schema": "ACTIVE_RUNTIME_V3_TRACE_CARDINALITY_REPAIR_SOURCE_LOCK_V1",
        "parent_execution_head": PARENT_EXECUTION_HEAD,
        "repair_branch": REPAIR_BRANCH,
        "git_head_before_regression": git(checkout, "rev-parse", "HEAD"),
        "protocol_sha256": PROTOCOL_SHA256,
        "trial_id": TRIAL_ID,
        "runtime_source_sha256": source_hashes,
        "allowed_runtime_changes": sorted(ALLOWED_RUNTIME),
        "disallowed_change_count": 0,
        "map_artifacts": map_artifacts,
        "scientific_analyzer_authorized": False,
        "old_cohort_resume_authorized": False,
    }
    return source_lock


def configure_regression(checkout: Path, map_root: Path, paired: Any, base_configure=None) -> tuple[Any, dict[str, Any]]:
    old_lock = json.loads((checkout / PAIRED_REL / "V3_PAIRED_EXECUTION_LOCK.json").read_text(encoding="utf-8"))
    paired.verify_execution_lock = lambda _checkout, _require_committed: old_lock
    smoke, protocol = (base_configure or paired.configure_smoke)(checkout, map_root)

    def verify_repair_source_and_map(checkout_arg: Path, protocol_arg: dict[str, Any], require_execution_lock: bool = True):
        del protocol_arg, require_execution_lock
        frozen_protocol, _input_lock, _reference = paired.frozen(checkout_arg)
        artifacts = paired.verify_map(frozen_protocol, map_root)
        geometry = frozen_protocol["v3_hard_geometry"]
        diagnostic = frozen_protocol["historical_diagnostic_shell"]
        if (geometry["r_hard_q"], geometry["m_hard_q"], geometry["rho_seg_q"]) != (0.015, 0.0, 0.0):
            raise RuntimeError("V3_HARD_GEOMETRY_DRIFT")
        if diagnostic["radius_q"] != 0.025 or diagnostic["runtime_authority"] is not False:
            raise RuntimeError("HISTORICAL_DIAGNOSTIC_AUTHORITY_DRIFT")
        return {"status": "PASS", "map_artifacts": artifacts}

    smoke.verify_source_and_map = verify_repair_source_and_map
    return smoke, protocol


def run_child(checkout: Path, output_dir: Path, map_root: Path) -> int:
    # torch multiprocessing spawn re-executes this script.  Worker re-entry
    # must not recursively launch another runtime child.
    if os.environ.get("V3_REPAIR_SPAWN_GUARD") == "1":
        return 0
    os.environ["V3_REPAIR_SPAWN_GUARD"] = "1"
    paired = load_module(
        checkout / PAIRED_REL / "run_active_runtime_v3_paired_validation.py",
        "_v3_paired_repair_child",
    )
    static_preflight(checkout, map_root, paired)
    old_lock = json.loads((checkout / PAIRED_REL / "V3_PAIRED_EXECUTION_LOCK.json").read_text(encoding="utf-8"))
    paired.verify_execution_lock = lambda _checkout, _require_committed: old_lock
    original_configure = paired.configure_smoke

    def configure(checkout_arg: Path, map_root_arg: Path):
        return configure_regression(checkout_arg, map_root_arg, paired, original_configure)

    paired.configure_smoke = configure
    return int(paired.run_one(checkout, output_dir, map_root, TRIAL_ID))


def run_parent(checkout: Path, output_dir: Path, map_root: Path) -> int:
    if output_dir.exists():
        raise RuntimeError("REGRESSION_OUTPUT_ROOT_ALREADY_EXISTS")
    output_dir.mkdir(parents=True)
    paired = load_module(
        checkout / PAIRED_REL / "run_active_runtime_v3_paired_validation.py",
        "_v3_paired_repair_parent",
    )
    source_lock = static_preflight(checkout, map_root, paired)
    write_json(output_dir / "REPAIR_RUNTIME_SOURCE_LOCK.json", source_lock)
    protocol = paired.frozen(checkout)[0]
    env = os.environ.copy()
    env.update(protocol["environment"])
    env["V3_REPAIR_SPAWN_GUARD"] = "0"
    command = [
        protocol["environment"]["python"],
        str(Path(__file__).resolve()),
        "--child",
        "--checkout", str(checkout),
        "--output-dir", str(output_dir),
        "--map-source-root", str(map_root),
    ]
    stdout_path = output_dir / "trial_73_launcher_stdout.tmp"
    stderr_path = output_dir / "trial_73_launcher_stderr.tmp"
    with stdout_path.open("w", encoding="utf-8", newline="\n") as stdout, stderr_path.open("w", encoding="utf-8", newline="\n") as stderr:
        process = subprocess.Popen(command, env=env, stdout=stdout, stderr=stderr, text=True)
        code = process.wait()

    raw = output_dir / "raw" / "trial_73"
    raw.mkdir(parents=True, exist_ok=True)
    stdout_path.replace(raw / "stdout.log")
    stderr_path.replace(raw / "stderr.log")
    smoke, _ = configure_regression(checkout, map_root, paired)
    released = smoke.gpu_pid_released(process.pid)
    (raw / "process_exit_code.txt").write_text(f"{code}\n", encoding="utf-8", newline="\n")
    (raw / "gpu_released.txt").write_text(("true" if released else "false") + "\n", encoding="utf-8", newline="\n")
    lock = paired.freeze_trial_evidence(raw)
    complete = paired.complete_evidence(output_dir, TRIAL_ID)
    summary = json.loads((raw / "trial_summary.json").read_text(encoding="utf-8"))
    trace_lock = json.loads((raw / "runtime_trace_lock.json").read_text(encoding="utf-8"))
    persisted_lines = len((raw / "runtime_trace.jsonl").read_text(encoding="utf-8").splitlines())
    regression = {
        "schema": "ACTIVE_RUNTIME_V3_TRACE_CARDINALITY_GPU_REGRESSION_V1",
        "trial_id": TRIAL_ID,
        "process_exit_code": code,
        "gpu_released": released,
        "immutable_raw_evidence_lock": lock["identity"],
        "completed_cycles": summary.get("completed_cycles"),
        "trace_record_count": summary.get("trace_record_count"),
        "trace_lock_record_count": trace_lock.get("record_count"),
        "persisted_trace_lines": persisted_lines,
        "plant_commits": summary.get("plant_commit_count"),
        "finalization_status": summary.get("finalization_status"),
        "hard_blocker": summary.get("hard_blocker"),
        "evaluation_eligible": summary.get("evaluation_eligible"),
        "trace_cardinality_pass": summary.get("completed_cycles") == summary.get("trace_record_count") == trace_lock.get("record_count") == persisted_lines,
        "paired_complete_evidence_check": complete,
        "hard_runtime_radius_q": summary.get("v3_wiring_audit", {}).get("hard_runtime_radius_q"),
        "historical_diagnostic_runtime_authority": summary.get("v3_wiring_audit", {}).get("historical_diagnostic_runtime_authority"),
        "scientific_analyzer_run": False,
        "old_primary_trials_reused": False,
    }
    write_json(output_dir / "TRIAL_73_TRACE_CARDINALITY_REGRESSION.json", regression)
    print(json.dumps(regression, sort_keys=True), flush=True)
    return 0 if code == 0 and released and complete and regression["trace_cardinality_pass"] else (code or 2)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--child", action="store_true")
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--map-source-root", type=Path, required=True)
    args = parser.parse_args()
    checkout = args.checkout.resolve(strict=True)
    output_dir = args.output_dir.resolve()
    map_root = args.map_source_root.resolve(strict=True)
    if args.child:
        return run_child(checkout, output_dir, map_root)
    return run_parent(checkout, output_dir, map_root)


if __name__ == "__main__":
    raise SystemExit(main())
