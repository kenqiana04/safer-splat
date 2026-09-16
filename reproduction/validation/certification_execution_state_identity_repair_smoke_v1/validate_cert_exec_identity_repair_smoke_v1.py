#!/usr/bin/env python3
"""CPU-only validator for the frozen repair smoke protocol."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


TASK_DIR = Path(__file__).resolve().parent
PROTOCOL = TASK_DIR / "SMOKE_REPAIR_V1_PROTOCOL.json"
LOCK = TASK_DIR / "SMOKE_REPAIR_V1_EXECUTION_LOCK.json"
RUNNER = TASK_DIR / "run_cert_exec_identity_repair_smoke_v1.py"
LAUNCHER = TASK_DIR / "launch_cert_exec_identity_repair_smoke_v1.sh"
MONITOR = TASK_DIR / "monitor_cert_exec_identity_repair_smoke_v1.py"
BRANCH = "freeze-cert-exec-identity-repair-smoke-protocol-v1"
BASE = "546598a70e12fa99f9153f1927d0542ca27862b4"
RESULT_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_20260916")
ALLOWED = "reproduction/validation/certification_execution_state_identity_repair_smoke_v1/"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, text=True, capture_output=True).stdout.strip()


def need(condition: bool, name: str, checks: list[str], failures: list[str]) -> None:
    (checks if condition else failures).append(name)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--pre-freeze", action="store_true")
    args = parser.parse_args(); root = args.repo_root.resolve(strict=True)
    checks: list[str] = []; failures: list[str] = []
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8")); lock = json.loads(LOCK.read_text(encoding="utf-8"))
    runner = RUNNER.read_text(encoding="utf-8"); launcher = LAUNCHER.read_text(encoding="utf-8"); monitor = MONITOR.read_text(encoding="utf-8")

    need(git(root, "branch", "--show-current") == BRANCH, "EXACT_BRANCH", checks, failures)
    for ancestor, name in (("50cadfe614da70ce0345c4b1789c787dc529287e", "RUNTIME_AUTHORITY_ANCESTRY"), ("77f8e52c2a2252fe651e4a13e3e30ada25168eb7", "REPAIR_SPEC_ANCESTRY"), (BASE, "IMPLEMENTATION_HEAD_ANCESTRY")):
        need(subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", ancestor, "HEAD"]).returncode == 0, name, checks, failures)
    need(protocol["implementation_authority"]["head"] == BASE, "EXACT_IMPLEMENTATION_HEAD", checks, failures)
    need(protocol["implementation_authority"]["implementation_final_status"] == "PASS_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_V1_IMPLEMENTATION", "IMPLEMENTATION_FINAL_STATUS_PASS", checks, failures)
    need(protocol["implementation_authority"]["repair_spec_sha256"] == "5a0365c0d55376406fdd5b9181ef1b551ec29f30a5a96c41f96038e2d7dd0bc4", "REPAIR_SPEC_SHA", checks, failures)
    need(protocol["implementation_authority"]["root_cause_evidence_lock_sha256"] == "bc4b790ea7a893725249c5ca1e4a097379c88d431a97ec5a2469a19fcb857186", "ROOT_CAUSE_LOCK_SHA", checks, failures)
    need(protocol["implementation_authority"]["implementation_evidence_lock_sha256"] == "ae4dd993dde0eb51c15f30a612c34f7de5ae2ec952c1dfaa17b3396c5e26c105", "IMPLEMENTATION_EVIDENCE_LOCK_SHA", checks, failures)
    need(protocol["implementation_authority"]["implementation_validation_lock_sha256"] == "ba86ceddc2e91fbeaf2e9d7e30e9aaadf9b73395a7d8f6ad1acd1a8e30efc61c", "IMPLEMENTATION_VALIDATION_LOCK_SHA", checks, failures)
    need(protocol["canonical_transition"]["identity"] == "canonical-transition:sha256:188eae47698febcd0d5492c1c0df2ea456a2fce23a83a616e28089f0e2f46d5d", "CANONICAL_TRANSITION_IDENTITY", checks, failures)
    need(protocol["canonical_transition"]["epsilon_or_tolerance_allowed"] is False, "NO_EPSILON", checks, failures)
    geometry = protocol["geometry"]
    need((geometry["hard_radius_q"], geometry["runtime_margin_q"], geometry["rho_seg_q"]) == (0.015, 0.0, 0.0), "FROZEN_GEOMETRY", checks, failures)
    need(geometry["historical_diagnostic_radius_q"] == 0.025 and geometry["historical_diagnostic_runtime_authority"] is False, "DIAGNOSTIC_ZERO_AUTHORITY", checks, failures)
    cohort = protocol["cohort"]
    need(cohort["trial_ids"] == [15, 45, 75] and cohort["trial_order"] == [15, 45, 75], "EXACT_DEV15_COHORT_AND_ORDER", checks, failures)
    need(not set(cohort["trial_ids"]) & {22, 28, 57, 59}, "OLD_PRIMARY_FAILURES_EXCLUDED", checks, failures)
    need(cohort["maximum_completed_cycles_per_trial"] == 500 and cohort["seed"] == 0, "LIMITS_AND_SEED", checks, failures)
    need(cohort["serial_execution"] and cohort["separate_process_per_trial"] and not cohort["automatic_retry"], "SERIAL_ISOLATED_NO_RETRY", checks, failures)
    need(protocol["future_result_root"] == str(RESULT_ROOT), "EXACT_RESULT_ROOT", checks, failures)
    need(not RESULT_ROOT.exists(), "RESULT_ROOT_ABSENT", checks, failures)
    science = protocol["scientific_boundaries"]
    need(not any(science[name] for name in ("scientific_analysis_performed", "reference_arm_enabled", "paired_validation_enabled", "official100_enabled", "formal_enabled", "collision_or_progress_gate", "efficacy_claim_authorized")), "NO_SCIENTIFIC_GATE_OR_ARM", checks, failures)
    need(science["frozen_scientific_decision_remains"] == "FAIL_V3_HARD_SAFETY_GATE", "FROZEN_SCIENTIFIC_DECISION", checks, failures)
    need(lock["protocol_sha256"] == sha256(PROTOCOL), "PROTOCOL_LOCK_HASH", checks, failures)
    need(lock["implementation_head"] == BASE and lock["trial_order"] == [15, 45, 75], "LOCK_CORE_IDENTITIES", checks, failures)
    if args.pre_freeze:
        need(lock["protocol_freeze_commit"] == "PENDING_PROTOCOL_FREEZE_COMMIT", "PREFREEZE_LOCK_TEMPLATE", checks, failures)
    else:
        commit = lock["protocol_freeze_commit"]
        need(isinstance(commit, str) and len(commit) == 40 and subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", commit, "HEAD"]).returncode == 0, "PROTOCOL_FREEZE_COMMIT_ANCESTOR", checks, failures)
        need(all(sha256(TASK_DIR / name) == digest for name, digest in lock["harness_sha256"].items()), "LOCKED_HARNESS_HASHES", checks, failures)
    changed = git(root, "diff", "--name-only", BASE)
    paths = [line for line in changed.splitlines() if line]
    need(all(path.startswith(ALLOWED) for path in paths), "ONLY_TASK_LOCAL_CHANGED", checks, failures)
    protected = git(root, "diff", "--name-only", BASE, "--", "cbf", "dynamics", "splat", "run.py", "reproduction/runtime", "reproduction/design/certification_execution_state_identity_repair_v1", "reproduction/implementation/certification_execution_state_identity_repair_v1", "reproduction/validation/certification_execution_state_identity_repair_v1", "reproduction/smoke", "reproduction/pilot", "reproduction/formal")
    need(not protected, "PROTECTED_UPSTREAM_DIFF_ZERO", checks, failures)
    ast.parse(runner); ast.parse(MONITOR.read_text(encoding="utf-8"))
    need(all(marker in runner for marker in ("--cpu-static-preflight", "--gpu-preflight", "--one", "--batch")), "RUNNER_MODES", checks, failures)
    need(all(marker in runner for marker in ("parent_pid", "result_root", "source_head", "protocol_sha256", "execution_lock_sha256", "trial_id", "token_sha256", "CHILD_AUTHORIZATION_PARENT_NOT_ALIVE")), "CHILD_AUTHORIZATION_BOUND", checks, failures)
    need("automatic_retry\": False" in runner and "parent_failures" in runner and "EARLY_CHILD_FAILURE.json" in runner, "NO_RETRY_AND_EARLY_FAILURE_EVIDENCE", checks, failures)
    need("build_repaired_v3_stack" in runner and "build_v3_stack_from_frozen_v2" not in runner, "REPAIRED_STACK_FACTORY_REUSED", checks, failures)
    need("scientific_analysis_performed\": False" in runner and "analyze_" not in launcher.lower(), "NO_ANALYZER", checks, failures)
    need("CERT_EXEC_STATE_IDENTITY_MISMATCH" in runner and "plant.commit_count != 0" in runner and "no_action_trace" in runner, "SYNTHETIC_MISMATCH_GUARD", checks, failures)
    need("completed_cycles\"] == boundary_fixture[\"trace_records" in runner and "plant_commits\"] == 0" in runner, "BOUNDARY_TRACE_NO_COMMIT_SEMANTICS", checks, failures)
    summary_fields = set(protocol["summary_continuity_fields"])
    need(summary_fields == {"canonical_transition_drift_count", "cert_exec_identity_mismatch_count", "l1_actual_continuity_mismatch_count", "l2_next_l1_continuity_mismatch_count", "backup_token_continuity_mismatch_count", "forbidden_diagnostic_authority_event_count"}, "SUMMARY_CONTINUITY_FIELDS", checks, failures)
    markers = ["echo RESULT_ROOT_ABSENT", "--cpu-static-preflight", "\"$PYTHON\" \"$VALIDATOR\" --repo-root", "mkdir -p", "COMMAND=", "tmux new-session"]
    command = launcher[launcher.index("COMMAND="):launcher.index("tmux new-session")]
    need(all(marker in launcher for marker in markers) and [launcher.index(marker) for marker in markers] == sorted(launcher.index(marker) for marker in markers) and command.index("--gpu-preflight") < command.index("--batch"), "FIRST_LAUNCH_ORDER", checks, failures)
    need("COLLECTION_COMPLETE_OR_STOPPED_REVIEW_BEFORE_ANY_SCIENTIFIC_ANALYSIS" in launcher, "STOP_BEFORE_ANALYSIS", checks, failures)
    need("SMOKE_REPAIR_V1_COLLECTION_SUMMARY.json" in monitor and "nvidia-smi" in monitor, "COMPACT_MONITOR", checks, failures)
    counts = lock["execution_counts_at_freeze"]
    need(all(int(value) == 0 for value in counts.values()), "ZERO_EXECUTION_COUNTS", checks, failures)
    result = {"schema": "CERT_EXEC_IDENTITY_REPAIR_SMOKE_PROTOCOL_VALIDATION_V1", "status": "PASS" if not failures else "FAIL", "passed_checks": checks, "failed_checks": failures, "check_count": len(checks) + len(failures), "gpu_execution_count": 0, "trial_execution_count": 0}
    print(json.dumps(result, sort_keys=True))
    if failures:
        print("FAILED:" + ",".join(failures), file=sys.stderr); return 2
    print("PASS_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_SMOKE_PROTOCOL_V1_VALIDATION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
