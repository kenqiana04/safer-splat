#!/usr/bin/env python3
"""CPU-only validator for retry1 launcher-guard repair R2."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import subprocess
import sys
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
PROTOCOL = TASK_DIR / "SMOKE_REPAIR_V1_PROTOCOL.json"
ORIGINAL_LOCK = TASK_DIR / "SMOKE_REPAIR_V1_EXECUTION_LOCK.json"
RETRY1_LOCK = TASK_DIR / "SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY1.json"
R2_LOCK = TASK_DIR / "SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY1_R2.json"
RUNNER = TASK_DIR / "run_cert_exec_identity_repair_smoke_v1.py"
VALIDATOR = TASK_DIR / "validate_cert_exec_identity_repair_smoke_v1.py"
LAUNCHER = TASK_DIR / "launch_cert_exec_identity_repair_smoke_v1.sh"
MONITOR = TASK_DIR / "monitor_cert_exec_identity_repair_smoke_v1.py"

BRANCH = "repair-cert-exec-identity-smoke-launcher-guards-r2"
BASE = "c19ffc3571771a16ae85e63b29f877be4c8cc02a"
IMPLEMENTATION_HEAD = "546598a70e12fa99f9153f1927d0542ca27862b4"
OLD_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_20260916")
RETRY_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry1_20260916")
DIAGNOSTIC_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_preflight_repair_v1_20260916")
PROTOCOL_SHA = "80b4c15413bdfa9b03b106a725af5cd97b17a51b9e81d03cfe79a7300a8077e7"
ORIGINAL_LOCK_SHA = "91de3e381cd9c3ddc9c5a7398ae9a170dd7867e08359611fc1c9595d8fd9342a"
HISTORICAL_SHA = "c1dc8b3f17850267f1cb3247795bc193a8944aa59349de5019efdf4ae72b1691"
OLD_LOG_SHA = "e6b627d62ce3a96cb5d975d5e0151fd0c54a93ee547ab34d90668771800f269f"
OLD_ROOT_MANIFEST = {
    "file_count": 1,
    "files": [{"path": "launcher.log", "size": 2982, "sha256": OLD_LOG_SHA}],
    "semantic_root_sha256": "439f9fdfe0ac095430dc02f1d9db84cbe5977b1f41e5c9cb4d37250735341e89",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def semantic(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, text=True, capture_output=True).stdout.strip()


def manifest(root: Path) -> dict[str, object]:
    if not root.is_dir():
        raise RuntimeError("OLD_FAILED_ROOT_MISSING")
    rows = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        data = path.read_bytes()
        rows.append({"path": path.relative_to(root).as_posix(), "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    result = {"file_count": len(rows), "files": rows}
    result["semantic_root_sha256"] = semantic(rows)
    return result


def validate_old_root(root: Path = OLD_ROOT) -> None:
    if not root.is_dir():
        raise RuntimeError("OLD_FAILED_ROOT_MISSING")
    if not (root / "launcher.log").is_file():
        raise RuntimeError("OLD_FAILED_ROOT_LAUNCHER_LOG_MISSING")
    if manifest(root) != OLD_ROOT_MANIFEST:
        raise RuntimeError("OLD_FAILED_ROOT_IDENTITY_MISMATCH")


def validate_retry_root_absent(root: Path = RETRY_ROOT) -> None:
    if root.exists():
        raise RuntimeError("RETRY1_ROOT_MUST_BE_ABSENT")


def check_launcher_text(text: str) -> list[str]:
    failures: list[str] = []
    required = (
        'CHECKOUT="/disk1/zlab/v3_repair_worktrees/safer-splat-cert-exec-identity-smoke-launcher-guards-r2"',
        'ACTIVE_BRANCH="repair-cert-exec-identity-smoke-launcher-guards-r2"',
        'OLD_FAILED_ROOT="/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_20260916"',
        'OLD_FAILED_ROOT_MISSING', 'OLD_FAILED_ROOT_LAUNCHER_LOG_MISSING', 'OLD_FAILED_ROOT_IDENTITY_MISMATCH',
        'RESULT_ROOT_ABSENT_CHECK_FAILED', '[[ ! -e "$RESULT_ROOT" ]]',
        'if [[ "${1:-}" == "--prelaunch-check-only" ]]', 'PRELAUNCH_CHECK_ONLY_PASS',
    )
    for marker in required:
        if marker not in text:
            failures.append("MISSING:" + marker)
    forbidden = (
        "/disk1/zlab/v3_repair_worktrees/safer-splat-cert-exec-identity-repair-smoke-protocol-v1",
        "freeze-cert-exec-identity-repair-smoke-protocol-v1",
        "OLD_FAILED_ROOT_MUST_REMAIN_READ_ONLY",
    )
    for marker in forbidden:
        if marker in text:
            failures.append("FORBIDDEN:" + marker)
    if text.count("--gpu-preflight") != 1:
        failures.append("GPU_PREFLIGHT_COUNT_INVALID")
    if text.find("--gpu-preflight") > text.find("--batch"):
        failures.append("GPU_BEFORE_BATCH_ORDER_INVALID")
    for line in text.splitlines():
        if "OLD_FAILED_ROOT" in line and any(token in line for token in ("rm ", "mv ", "chmod ", "touch ", ">>", "> ")):
            failures.append("OLD_ROOT_WRITE_OPERATION")
    pre = text.split('if [[ "${1:-}" == "--prelaunch-check-only" ]]', 1)[-1].split("fi", 1)[0]
    if any(token in pre for token in ("mkdir", "tmux", "--gpu-preflight", "--batch")):
        failures.append("PRELAUNCH_SIDE_EFFECT_OR_GPU")
    if 'TASK="$CHECKOUT/reproduction/validation/certification_execution_state_identity_repair_smoke_v1"' not in text:
        failures.append("TASK_NOT_DERIVED_FROM_CHECKOUT")
    return failures


def need(condition: bool, name: str, passed: list[str], failed: list[str]) -> None:
    (passed if condition else failed).append(name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--prelaunch-check-only", action="store_true")
    args = parser.parse_args()
    root = args.repo_root.resolve(strict=True)
    passed: list[str] = []
    failed: list[str] = []
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    original = json.loads(ORIGINAL_LOCK.read_text(encoding="utf-8"))
    retry1 = json.loads(RETRY1_LOCK.read_text(encoding="utf-8"))
    runner_text = RUNNER.read_text(encoding="utf-8")
    validator_text = VALIDATOR.read_text(encoding="utf-8")
    launcher_text = LAUNCHER.read_text(encoding="utf-8")
    monitor_text = MONITOR.read_text(encoding="utf-8")
    historical_path = root / "reproduction/smoke/active_runtime_smoke_v3/SMOKE_V3_PROTOCOL.json"
    historical = json.loads(historical_path.read_text(encoding="utf-8"))

    need(git(root, "branch", "--show-current") == BRANCH, "EXACT_R2_BRANCH", passed, failed)
    need(subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", BASE, "HEAD"]).returncode == 0, "C19FFC_ANCESTRY", passed, failed)
    need(subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", IMPLEMENTATION_HEAD, "HEAD"]).returncode == 0, "IMPLEMENTATION_ANCESTRY", passed, failed)
    need(sha256(PROTOCOL) == PROTOCOL_SHA, "ORIGINAL_PROTOCOL_UNCHANGED", passed, failed)
    need(sha256(ORIGINAL_LOCK) == ORIGINAL_LOCK_SHA, "ORIGINAL_LOCK_UNCHANGED", passed, failed)
    try:
        validate_old_root()
        passed.append("ACTUAL_OLD_ROOT_POSITIVE")
    except RuntimeError as exc:
        failed.append(str(exc))
    try:
        validate_retry_root_absent()
        passed.append("ACTUAL_RETRY_ROOT_ABSENT")
    except RuntimeError as exc:
        failed.append(str(exc))
    launcher_failures = check_launcher_text(launcher_text)
    need(not launcher_failures, "LAUNCHER_R2_GUARDS", passed, failed)
    need(sha256(historical_path) == HISTORICAL_SHA, "HISTORICAL_V3_BASE_CONFIG_SHA", passed, failed)
    need(all(isinstance(historical.get(k), dict) for k in ("controller", "certification", "dynamics", "deadline_profile")), "HISTORICAL_REQUIRED_MAPPINGS", passed, failed)
    need(historical["controller"]["controller_radius"] == 0.015 and historical["certification"]["certification_margin"] == 0.0 and historical["certification"]["rho_seg"] == 0.0, "HISTORICAL_GEOMETRY", passed, failed)
    need("load_runtime_base_config" in runner_text and "runtime_base_config" in runner_text and "build_repaired_v3_stack(checkout_arg, output_dir, trial_id, runtime_base_config" in runner_text, "BASE_CONFIG_SEPARATION", passed, failed)
    need("BRANCH = \"repair-cert-exec-identity-smoke-launcher-guards-r2\"" in runner_text and "TRIALS = (15, 45, 75)" in runner_text and "10, 50, 90" not in runner_text and "200" not in runner_text, "R2_RUNNER_FROZEN_COHORT", passed, failed)
    need("GPU_PREFLIGHT_DIAGNOSTIC_ROOT_INVALID" in runner_text and "historical_v3_base_config_mappings" in runner_text, "CPU_PREFLIGHT_DIAGNOSTIC_REUSE", passed, failed)
    need("gpu_preflight_failure.json" in runner_text and "scientific_analysis_performed" in runner_text, "GPU_FAILURE_PERSISTENCE", passed, failed)
    need(retry1["original_protocol_sha256"] == PROTOCOL_SHA and retry1["original_execution_lock_sha256"] == ORIGINAL_LOCK_SHA, "RETRY1_LOCK_PRESERVED", passed, failed)
    need(retry1["trial_ids"] == [15, 45, 75] and retry1["maximum_completed_cycles_per_trial"] == 500 and retry1["failure_classification"] == "PRE_TRIAL_GPU_PREFLIGHT_BASE_CONFIG_PLUMBING_FAILURE", "RETRY1_SEMANTICS", passed, failed)
    need(protocol["scientific_boundaries"]["frozen_scientific_decision_remains"] == "FAIL_V3_HARD_SAFETY_GATE", "SCIENTIFIC_DECISION_FROZEN", passed, failed)
    need("SMOKE_REPAIR_V1_COLLECTION_SUMMARY.json" in monitor_text, "MONITOR_RETRY_ROOT", passed, failed)
    need(all(marker in validator_text for marker in ("OLD_FAILED_ROOT_MISSING", "OLD_FAILED_ROOT_LAUNCHER_LOG_MISSING", "OLD_FAILED_ROOT_IDENTITY_MISMATCH", "RETRY1_ROOT_MUST_BE_ABSENT", "--prelaunch-check-only")), "VALIDATOR_TYPED_GUARDS", passed, failed)
    ast.parse(runner_text); ast.parse(validator_text); ast.parse(monitor_text)
    protected = git(root, "diff", "--name-only", BASE, "--", "cbf", "dynamics", "splat", "run.py", "reproduction/runtime", "reproduction/smoke/active_runtime_smoke_v3", "reproduction/validation/certification_execution_state_identity_repair_v1")
    need(not protected, "PROTECTED_DIFF_ZERO", passed, failed)

    if R2_LOCK.is_file():
        r2 = json.loads(R2_LOCK.read_text(encoding="utf-8"))
        need(r2.get("schema") == "CERT_EXECUTION_IDENTITY_REPAIR_SMOKE_EXECUTION_LOCK_RETRY1_R2_V1", "R2_LOCK_SCHEMA", passed, failed)
        need(r2.get("branch") == BRANCH and r2.get("base_head") == BASE, "R2_LOCK_IDENTITY", passed, failed)
        need(r2.get("old_failed_root_manifest") == OLD_ROOT_MANIFEST, "R2_LOCK_OLD_ROOT_MANIFEST", passed, failed)
        need(r2.get("retry_result_root") == str(RETRY_ROOT) and r2.get("trial_ids") == [15, 45, 75], "R2_LOCK_COHORT", passed, failed)
        need(all(sha256(TASK_DIR / name) == digest for name, digest in r2.get("harness_sha256", {}).items()), "R2_LOCK_HARNESS_HASHES", passed, failed)
    elif args.prelaunch_check_only:
        passed.append("R2_LOCK_PENDING_FOR_COMMIT2")
    else:
        failed.append("R2_EXECUTION_LOCK_MISSING")

    result = {"schema": "CERT_EXEC_IDENTITY_SMOKE_LAUNCHER_GUARDS_R2_VALIDATION_V1", "status": "PASS" if not failed else "FAIL", "passed_checks": passed, "failed_checks": failed, "gpu_count": 0, "tmux_start_count": 0, "smoke_trial_count": 0, "cycle_count": 0, "PlantCommit_count": 0}
    print(json.dumps(result, sort_keys=True))
    if failed:
        print("FAILED:" + ",".join(failed), file=sys.stderr)
        return 2
    print("PASS_CERT_EXEC_IDENTITY_SMOKE_LAUNCHER_GUARDS_R2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
