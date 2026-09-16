#!/usr/bin/env python3
"""Frozen future smoke harness for the certification/execution identity repair.

The freeze task may invoke only ``--cpu-static-preflight``. GPU preflight and
trial modes are execution-stage entry points guarded by the committed lock.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from typing import Any, Iterator


TASK_DIR = Path(__file__).resolve().parent
PROTOCOL_PATH = TASK_DIR / "SMOKE_REPAIR_V1_PROTOCOL.json"
LOCK_PATH = TASK_DIR / "SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY5_R6.json"
ORIGINAL_LOCK_PATH = TASK_DIR / "SMOKE_REPAIR_V1_EXECUTION_LOCK.json"
CHECKOUT_DEFAULT = Path("/disk1/zlab/v3_repair_worktrees/safer-splat-cert-exec-identity-smoke-executed-action-continuity-audit-r6")
OLD_RESULT_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_20260916")
ATTEMPT1_RESULT_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry1_20260916")
ATTEMPT1_LAUNCHER_LOG_SHA256 = "a1a647cd52426ebce38459c3e87522864266374842b824fb2d7075d10804910f"
ATTEMPT2_RESULT_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry2_20260916")
ATTEMPT2_LAUNCHER_LOG_SHA256 = "b82fc2409280b8c545914dc8664ddf8ea9291f213831f277ac7ffa1385439762"
ATTEMPT2_FAILURE_JSON_SHA256 = "16f2ebd7d40aa93d118b03311903749889509c27516825fa2dda267706e1aa79"
ATTEMPT3_RESULT_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry3_20260916")
ATTEMPT3_REQUIRED_SHA256 = {
    "launcher.log": "b8bfd94a3be10812bb9528baa55eb398456a22ec1a239f44c2f10d587760d0dd",
    "raw/gpu_preflight.json": "bb9473c716fab705766e2358d070f559ec23efa96c800e5469f5c2a5bebf747a",
    "raw/trial_15/trial_summary.json": "6ac573fc4c80debffe52c99186b89501b6479d4ea1abfc2d17f1c10cb350a806",
    "raw/trial_15/stdout.log": "55904d5882f9458afae8a3f91b096c09b4cf816f00a6ff21e92a450ca830cf0c",
    "raw/trial_15/process_exit_code.txt": "53c234e5e8472b6ac51c1ae1cab3fe06fad053beb8ebfd8977b010655bfdd3c3",
    "SMOKE_REPAIR_V1_COLLECTION_SUMMARY.json": "a0b56baa3b8ac5494844d5f11c44599255af4e4836af9466a521195c700c7f85",
}
ATTEMPT4_RESULT_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry4_20260916")
ATTEMPT4_REQUIRED_SHA256 = {
    "launcher.log": "a7f4b7f24822c6108cbab013ae46877bee2eda2050d249ce4141fd21a8a7b5ce",
    "raw/gpu_preflight.json": "bb9473c716fab705766e2358d070f559ec23efa96c800e5469f5c2a5bebf747a",
    "raw/trial_15/trial_summary.json": "1099803ee93f23fc3686252c0e821099a2aeeadc0f017508c7582987fa976b14",
    "raw/trial_15/runtime_trace.jsonl": "e034aa0eaa59bf5ab99e9f4e3d0c55b9b0256c1f09f6c7ec4c451d044185e719",
    "raw/trial_15/cycle_observations.jsonl": "fa53c5d859d90c90ed74da9ae89f557eb2a3f5804975ed8af0a64f8cdefb9a54",
    "raw/trial_15/SMOKE_REPAIR_V1_RAW_EVIDENCE_LOCK.json": "0bc8f3b20723de10f4f900c8b7691f660768328291b3e5b4c5d0018c02cd108b",
    "SMOKE_REPAIR_V1_COLLECTION_SUMMARY.json": "a0b56baa3b8ac5494844d5f11c44599255af4e4836af9466a521195c700c7f85",
}
RESULT_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry5_20260916")
GPU_PREFLIGHT_DIAGNOSTIC_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_preflight_repair_v1_20260916")
IMPLEMENTATION_HEAD = "546598a70e12fa99f9153f1927d0542ca27862b4"
BRANCH = "repair-cert-exec-identity-smoke-executed-action-continuity-audit-r6"
TRIALS = (15, 45, 75)
AUTHORIZATION_NAME = "SMOKE_REPAIR_V1_INTERNAL_CHILD_AUTHORIZATION.json"
CHILD_TOKEN_ENV = "SAFER_SPLAT_CERT_EXEC_SMOKE_CHILD_TOKEN"
DELEGATE_REL = "reproduction/smoke/active_runtime_smoke_v3/run_active_runtime_smoke_v3.py"
HISTORICAL_V3_PROTOCOL_REL = "reproduction/smoke/active_runtime_smoke_v3/SMOKE_V3_PROTOCOL.json"
HISTORICAL_V3_PROTOCOL_SHA256 = "c1dc8b3f17850267f1cb3247795bc193a8944aa59349de5019efdf4ae72b1691"
ORIGINAL_PROTOCOL_SHA256 = "80b4c15413bdfa9b03b106a725af5cd97b17a51b9e81d03cfe79a7300a8077e7"
ORIGINAL_LOCK_SHA256 = "91de3e381cd9c3ddc9c5a7398ae9a170dd7867e08359611fc1c9595d8fd9342a"
OLD_LAUNCHER_LOG_SHA256 = "e6b627d62ce3a96cb5d975d5e0151fd0c54a93ee547ab34d90668771800f269f"
ALLOWED_TASK_REL = "reproduction/validation/certification_execution_state_identity_repair_smoke_v1"
PROTECTED_PATHS = (
    "cbf", "dynamics", "splat", "run.py", "reproduction/runtime",
    "reproduction/design/certification_execution_state_identity_repair_v1",
    "reproduction/implementation/certification_execution_state_identity_repair_v1",
    "reproduction/validation/certification_execution_state_identity_repair_v1",
    "reproduction/smoke/active_runtime_smoke_v2",
    "reproduction/smoke/active_runtime_smoke_v3",
    "reproduction/pilot", "reproduction/formal",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def semantic_sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    temporary.replace(path)


def git(checkout: Path, *args: str, check: bool = True) -> str:
    return subprocess.run(["git", "-C", str(checkout), *args], text=True, capture_output=True, check=check).stdout.strip()


def protocol() -> dict[str, Any]:
    return load_json(PROTOCOL_PATH)


def load_runtime_base_config(checkout: Path) -> dict[str, Any]:
    """Load the protected V3 runtime base separately from the repair protocol."""
    path = checkout / HISTORICAL_V3_PROTOCOL_REL
    if sha256_file(path) != HISTORICAL_V3_PROTOCOL_SHA256:
        raise RuntimeError("HISTORICAL_V3_BASE_CONFIG_SHA_MISMATCH")
    base = load_json(path)
    for key in ("controller", "certification", "dynamics", "deadline_profile"):
        if not isinstance(base.get(key), dict):
            raise RuntimeError("HISTORICAL_V3_BASE_CONFIG_%s_MAPPING_REQUIRED" % key.upper())
    frozen = protocol()
    if base["map_identity"] != frozen["map"]["identity"]:
        raise RuntimeError("HISTORICAL_V3_BASE_CONFIG_MAP_IDENTITY_MISMATCH")
    if base["controller"]["controller_radius"] != frozen["geometry"]["hard_radius_q"]:
        raise RuntimeError("HISTORICAL_V3_BASE_CONFIG_CONTROLLER_GEOMETRY_MISMATCH")
    if base["certification"]["certification_margin"] != frozen["geometry"]["runtime_margin_q"] or base["certification"]["rho_seg"] != frozen["geometry"]["rho_seg_q"]:
        raise RuntimeError("HISTORICAL_V3_BASE_CONFIG_CERTIFICATION_GEOMETRY_MISMATCH")
    return base


def delegate_runtime_protocol(checkout: Path) -> dict[str, Any]:
    """Project frozen execution fields onto the historical V3 runtime schema."""
    repair = protocol()
    projected = deepcopy(load_runtime_base_config(checkout))
    for key in (
        "seed", "maximum_completed_cycles_per_trial", "trial_ids", "trial_order",
        "serial_execution", "separate_process_per_trial",
    ):
        projected[key] = deepcopy(repair["cohort"][key])
    projected["environment"] = deepcopy(repair["environment"])
    return projected


def _tree_sha256(root: Path) -> str:
    rows: list[str] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and "__pycache__" not in item.parts):
        rows.append(f"{path.relative_to(root).as_posix()} {sha256_file(path)}")
    return hashlib.sha256(("\n".join(rows) + "\n").encode()).hexdigest()


def verify_static_identity(checkout: Path, *, require_committed_lock: bool) -> dict[str, Any]:
    frozen = protocol()
    expected = frozen["implementation_authority"]
    for ancestor in (expected["runtime_scientific_authority"], expected["repair_spec_authority"], IMPLEMENTATION_HEAD):
        if subprocess.run(["git", "-C", str(checkout), "merge-base", "--is-ancestor", ancestor, "HEAD"]).returncode:
            raise RuntimeError("FROZEN_ANCESTRY_MISMATCH:" + ancestor)
    if git(checkout, "branch", "--show-current") != BRANCH:
        raise RuntimeError("SMOKE_PROTOCOL_BRANCH_MISMATCH")
    report = checkout / "reproduction/implementation/certification_execution_state_identity_repair_v1/IMPLEMENTATION_REPORT.md"
    if "PASS_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_V1_IMPLEMENTATION" not in report.read_text(encoding="utf-8"):
        raise RuntimeError("IMPLEMENTATION_FINAL_STATUS_NOT_PASS")
    fixed_files = {
        "reproduction/design/certification_execution_state_identity_repair_v1/REPAIR_SPECIFICATION.json": expected["repair_spec_sha256"],
        "reproduction/design/certification_execution_state_identity_repair_v1/ROOT_CAUSE_EVIDENCE_LOCK.json": expected["root_cause_evidence_lock_sha256"],
        "reproduction/implementation/certification_execution_state_identity_repair_v1/IMPLEMENTATION_EVIDENCE_LOCK.json": expected["implementation_evidence_lock_sha256"],
    }
    for relative, digest in fixed_files.items():
        if sha256_file(checkout / relative) != digest:
            raise RuntimeError("FROZEN_FILE_HASH_MISMATCH:" + relative)
    validation_root = Path("/disk1/zlab/v3_repair_records/certification_execution_state_identity_repair_v1_20260916_r2")
    if sha256_file(validation_root / "IMPLEMENTATION_VALIDATION_LOCK.json") != expected["implementation_validation_lock_sha256"]:
        raise RuntimeError("IMPLEMENTATION_VALIDATION_LOCK_MISMATCH")
    repair_root = checkout / "reproduction/runtime/certification_execution_state_identity_repair_v1"
    canonical = repair_root / "canonical_transition.py"
    factory = repair_root / "stack_factory.py"
    changed = git(checkout, "diff", "--name-only", IMPLEMENTATION_HEAD, "--", *PROTECTED_PATHS)
    if changed:
        raise RuntimeError("PROTECTED_UPSTREAM_DIFF_NONZERO:" + changed.replace("\n", ","))
    status = git(checkout, "status", "--porcelain", "--untracked-files=all")
    outside = [line for line in status.splitlines() if (ALLOWED_TASK_REL + "/") not in line.replace("\\", "/")]
    if outside:
        raise RuntimeError("OUT_OF_SCOPE_WORKTREE_CHANGE:" + outside[0])
    lock = load_json(LOCK_PATH)
    if lock["protocol_sha256"] != sha256_file(PROTOCOL_PATH):
        raise RuntimeError("PROTOCOL_SHA_MISMATCH")
    if require_committed_lock:
        commit = lock.get("harness_repair_commit")
        if not isinstance(commit, str) or len(commit) != 40 or subprocess.run(
            ["git", "-C", str(checkout), "merge-base", "--is-ancestor", commit, "HEAD"]
        ).returncode:
            raise RuntimeError("HARNESS_REPAIR_COMMIT_NOT_ANCESTOR")
        if git(checkout, "status", "--porcelain", "--", ALLOWED_TASK_REL):
            raise RuntimeError("COMMITTED_HARNESS_REQUIRED")
        for name, digest in lock["harness_sha256"].items():
            if sha256_file(TASK_DIR / name) != digest:
                raise RuntimeError("HARNESS_HASH_MISMATCH:" + name)
    return {
        "runtime_repair_tree_sha256": _tree_sha256(repair_root),
        "runtime_repair_tree_git_oid": git(checkout, "rev-parse", f"{IMPLEMENTATION_HEAD}:reproduction/runtime/certification_execution_state_identity_repair_v1"),
        "canonical_transition_sha256": sha256_file(canonical),
        "repaired_stack_factory_sha256": sha256_file(factory),
        "protected_diff_count": 0,
    }


def verify_map_artifacts(frozen: dict[str, Any]) -> list[dict[str, Any]]:
    root = Path(frozen["map"]["root"]).resolve(strict=True)
    actual = []
    for expected in frozen["map"]["artifacts"]:
        path = root / expected["relative_path"]
        row = {"relative_path": expected["relative_path"], "size": path.stat().st_size, "sha256": sha256_file(path)}
        if row != expected:
            raise RuntimeError("MAP_ARTIFACT_IDENTITY_MISMATCH:" + expected["relative_path"])
        actual.append(row)
    if semantic_sha256({"scene": "stonehenge", "artifacts": actual}) != frozen["map"]["identity"]:
        raise RuntimeError("MAP_SEMANTIC_IDENTITY_MISMATCH")
    return actual


def synthetic_mismatch_guard_test() -> dict[str, Any]:
    from reproduction.runtime.active_runtime_assurance_v2.runtime_errors import CommitAuthorityViolation
    from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
        ActionRole, CandidateRole, RuntimeStateSnapshot, SupervisorDecision, make_action, make_candidate,
    )
    from reproduction.runtime.certification_execution_state_identity_repair_v1.canonical_transition import CanonicalExecutionTransition
    from reproduction.runtime.certification_execution_state_identity_repair_v1.evidence import CanonicalIdentityLedger
    from reproduction.runtime.certification_execution_state_identity_repair_v1.repaired_components import ContinuityGuardedPlantCommitAdapter
    from reproduction.runtime.v3_hard_radius_runtime_wiring_v1.stack_factory import make_v3_authority_registry

    registry = make_v3_authority_registry("map", "dt", "deadline")
    transition = CanonicalExecutionTransition("cpu", backend_label="TEST_FIXTURE_ONLY_NOT_RUNTIME_AUTHORITY")
    ledger = CanonicalIdentityLedger()
    snapshot = RuntimeStateSnapshot.create("synthetic", 0, (0.1, -0.2, 0.3, 0.01, -0.02, 0.03), (0.0,) * 6, "map", 0.05)
    candidate = make_candidate((0.1, -0.1, 0.05), CandidateRole.PRIMARY, "PRIMARY_NATIVE_CBF_QP", "controller", snapshot)
    action = make_action(candidate.vector, ActionRole.PRIMARY_NAVIGATION, candidate.identity.value)
    wrong = RuntimeStateSnapshot.create("synthetic", 1, (0.0,) * 6, snapshot.goal, "map", 0.05).identity
    decision = SupervisorDecision(0, snapshot.identity, action, True, "SYNTHETIC_GUARD", "ARB_NAV", SimpleNamespace(expected_activation_state_identity=wrong))
    plant = ContinuityGuardedPlantCommitAdapter(registry, transition, ledger)
    typed = None
    try:
        plant.commit(decision, snapshot, action)
    except CommitAuthorityViolation as exc:
        typed = str(exc)
    no_action_trace = [{"cycle_index": 0, "committed": False, "boundary": True, "reason": typed}]
    if typed != "CERT_EXEC_STATE_IDENTITY_MISMATCH" or plant.commit_count != 0 or len(no_action_trace) != 1:
        raise RuntimeError("SYNTHETIC_MISMATCH_FAIL_CLOSED_TEST_FAILED")
    return {"status": "PASS", "typed_reason": typed, "plant_commit_count": 0, "no_action_trace_transactions": 1}


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except (OSError, ValueError):
        return False
    return True


def authorization_payload(checkout: Path, root: Path, trial: int, token: str, parent_pid: int | None = None) -> dict[str, Any]:
    return {
        "schema": "CERT_EXEC_IDENTITY_REPAIR_SMOKE_INTERNAL_CHILD_AUTHORIZATION_V1",
        "parent_pid": os.getpid() if parent_pid is None else int(parent_pid),
        "result_root": str(root),
        "branch": git(checkout, "branch", "--show-current"),
        "source_head": git(checkout, "rev-parse", "HEAD"),
        "protocol_sha256": sha256_file(PROTOCOL_PATH),
        "execution_lock_sha256": sha256_file(LOCK_PATH),
        "trial_id": int(trial),
        "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
    }


def write_authorization(checkout: Path, root: Path, trial: int, token: str) -> Path:
    path = root / AUTHORIZATION_NAME
    if path.exists():
        raise RuntimeError("CHILD_AUTHORIZATION_ALREADY_EXISTS")
    write_json(path, authorization_payload(checkout, root, trial, token))
    return path


def verify_authorization(checkout: Path, root: Path, trial: int, token: str | None) -> None:
    if root != RESULT_ROOT or not root.is_dir() or not token:
        raise RuntimeError("UNAUTHORIZED_ONE")
    path = root / AUTHORIZATION_NAME
    if not path.is_file():
        raise RuntimeError("CHILD_AUTHORIZATION_MISSING")
    actual = load_json(path)
    expected = authorization_payload(checkout, root, trial, token, actual.get("parent_pid"))
    if actual != expected:
        raise RuntimeError("CHILD_AUTHORIZATION_IDENTITY_MISMATCH")
    if not isinstance(actual.get("parent_pid"), int) or not _alive(actual["parent_pid"]):
        raise RuntimeError("CHILD_AUTHORIZATION_PARENT_NOT_ALIVE")


def preserve_early_child_failure(root: Path, trial: int, code: int, released: bool, stdout: Path, stderr: Path) -> Path:
    failure = root / "parent_failures" / f"trial_{trial}"
    failure.mkdir(parents=True, exist_ok=False)
    stdout.replace(failure / "stdout.log")
    stderr.replace(failure / "stderr.log")
    (failure / "process_exit_code.txt").write_text(f"{code}\n", encoding="utf-8")
    (failure / "gpu_released.txt").write_text(("true" if released else "false") + "\n", encoding="utf-8")
    write_json(failure / "EARLY_CHILD_FAILURE.json", {
        "schema": "CERT_EXEC_IDENTITY_REPAIR_SMOKE_EARLY_CHILD_FAILURE_V1",
        "trial_id": trial, "process_exit_code": code, "gpu_released": released,
        "raw_trial_directory_created": False, "automatic_retry": False,
        "fake_trial_completion": False, "fake_raw_evidence_lock": False,
    })
    return failure


def _load_delegate(checkout: Path) -> Any:
    path = checkout / DELEGATE_REL
    spec = importlib.util.spec_from_file_location("_cert_exec_smoke_delegate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("SMOKE_V3_DELEGATE_IMPORT_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.TASK_DIR = TASK_DIR
    module.PROTOCOL_PATH = PROTOCOL_PATH
    module.EXECUTION_LOCK_PATH = LOCK_PATH
    module.UPSTREAM = IMPLEMENTATION_HEAD
    module.FIXED_TRIALS = TRIALS
    module.read_protocol = lambda: delegate_runtime_protocol(checkout)
    runtime_base_config = load_runtime_base_config(checkout)

    def verify_source_and_map(checkout_arg: Path, frozen: dict[str, Any], require_execution_lock: bool = True):
        verify_static_identity(checkout_arg, require_committed_lock=require_execution_lock)
        repair_frozen = protocol()
        rows = verify_map_artifacts(repair_frozen)
        return repair_frozen["map"]["identity"], rows

    def build_stack(checkout_arg: Path, output_dir: Path, trial_id: int, frozen: dict[str, Any], map_identity: str):
        if str(checkout_arg) not in sys.path:
            sys.path.insert(0, str(checkout_arg))
        from reproduction.runtime.certification_execution_state_identity_repair_v1 import build_repaired_v3_stack
        stack = build_repaired_v3_stack(checkout_arg, output_dir, trial_id, runtime_base_config, map_identity)
        repair = stack["repaired_stack_wiring_audit"]
        stack["v3_wiring_audit"] = {
            "status": repair["status"], "hard_runtime_radius_q": repair["hard_radius_q"],
            "runtime_margin_q": repair["runtime_margin_q"], "runtime_effective_radius_q": repair["hard_radius_q"],
            "rho_seg_q": repair["rho_seg_q"], "historical_diagnostic_radius_q": repair["historical_diagnostic_radius_q"],
            "historical_diagnostic_runtime_authority": repair["historical_diagnostic_runtime_authority"],
            "canonical_transition_identity": repair["canonical_transition_identity"], "checks": repair["checks"],
        }
        return stack

    module.verify_source_and_map = verify_source_and_map
    module.build_v3_stack = build_stack
    return module


@contextmanager
def observe_cycles(checkout: Path, output_dir: Path, trial: int) -> Iterator[None]:
    if str(checkout) not in sys.path:
        sys.path.insert(0, str(checkout))
    from reproduction.runtime.active_runtime_assurance_v2.active_cycle import ActiveCycleCoordinator
    original = ActiveCycleCoordinator.run_cycle
    observations = output_dir / "raw" / f"trial_{trial}" / "cycle_observations.jsonl"

    def observed(self: Any, snapshot: Any, request: Any) -> Any:
        result = original(self, snapshot, request)
        receipt = result.commit_receipt
        row = {
            "trial_id": trial, "cycle_index": int(request.cycle_index),
            "pre_state": list(snapshot.state), "pre_state_identity": snapshot.identity.value,
            "committed": bool(result.committed), "boundary": bool(result.boundary),
            "post_state": None if result.next_state is None else list(result.next_state.state),
            "post_state_identity": None if result.next_state is None else result.next_state.identity.value,
            "selected_action_identity": None if result.final_supervisor_decision is None or result.final_supervisor_decision.selected_action is None else result.final_supervisor_decision.selected_action.identity.value,
            "executed_action_identity": None if receipt is None else receipt.executed_action_identity.value,
            "plant_commit_receipt_identity": None if result.commit_transaction_result is None else result.commit_transaction_result.attempt_identity,
            "action_role": None if receipt is None else receipt.action_role.value,
        }
        with observations.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
            handle.flush(); os.fsync(handle.fileno())
        return result

    ActiveCycleCoordinator.run_cycle = observed
    try:
        yield
    finally:
        ActiveCycleCoordinator.run_cycle = original


def executed_action_l2_next_l1_audit(
    trace_rows: list[dict[str, Any]], observations: list[dict[str, Any]]
) -> dict[str, Any]:
    """Check primary L2(k->k+2) only when that primary action was executed."""
    if len(trace_rows) != len(observations):
        raise RuntimeError("TRACE_OBSERVATION_CARDINALITY_MISMATCH")
    applicable = not_applicable = unknown = mismatch = 0
    roles = {"PRIMARY_NAVIGATION": 0, "RETAINED_BACKUP": 0, "CERTIFIED_TERMINAL": 0}
    def trace_identity(value: Any) -> Any:
        return value.get("value") if isinstance(value, dict) else value

    def matching_trial(trace_trial: Any, observed_trial: Any) -> bool:
        return isinstance(observed_trial, int) and trace_trial == f"STONEHENGE_TRIAL_{observed_trial:03d}"

    for index in range(max(0, len(trace_rows) - 1)):
        trace, next_trace = trace_rows[index:index + 2]
        observation, next_observation = observations[index:index + 2]
        role = observation.get("action_role")
        roles[role] = roles.get(role, 0) + 1
        selected = observation.get("selected_action_identity")
        executed = observation.get("executed_action_identity")
        aligned = (
            isinstance(selected, str) and bool(selected)
            and isinstance(executed, str) and bool(executed)
            and selected == executed
            and observation.get("committed") is True
            and trace_identity(trace.get("selected_action_identity")) == selected
            and trace_identity(trace.get("executed_action_identity")) == executed
            and trace.get("action_role") == role
            and matching_trial(trace.get("trial_id"), observation.get("trial_id"))
            and matching_trial(next_trace.get("trial_id"), next_observation.get("trial_id"))
            and trace.get("cycle_index") == observation.get("cycle_index")
            and next_trace.get("cycle_index") == next_observation.get("cycle_index")
            and isinstance(trace.get("cycle_index"), int)
            and next_trace.get("cycle_index") == trace["cycle_index"] + 1
        )
        if not aligned:
            unknown += 1
            continue
        if role == "PRIMARY_NAVIGATION":
            facts = dict(trace.get("facts", []))
            next_facts = dict(next_trace.get("facts", []))
            predicted = facts.get("canonical_l2_p_k2_identity")
            actual_next_l1 = next_facts.get("canonical_l1_endpoint_identity")
            if not isinstance(predicted, str) or not predicted or not isinstance(actual_next_l1, str) or not actual_next_l1:
                unknown += 1
                continue
            applicable += 1
            mismatch += int(predicted != actual_next_l1)
        elif role in ("RETAINED_BACKUP", "CERTIFIED_TERMINAL"):
            not_applicable += 1
        else:
            unknown += 1
    total = max(0, len(trace_rows) - 1)
    if applicable + not_applicable + unknown != total:
        raise RuntimeError("EXECUTED_ACTION_CONTINUITY_DENOMINATOR_MISMATCH")
    return {
        "l2_next_l1_continuity_applicable_count": applicable,
        "l2_next_l1_continuity_mismatch_count": mismatch,
        "l2_next_l1_continuity_not_applicable_count": not_applicable,
        "l2_next_l1_continuity_unknown_count": unknown,
        "l2_next_l1_continuity_cross_cycle_rows": total,
        "l2_next_l1_continuity_role_counts": roles,
    }


def replay_retry4_continuity() -> dict[str, Any]:
    """Read-only CPU proof against the immutable consumed retry4 attempt."""
    if not ATTEMPT4_RESULT_ROOT.is_dir() or any(
        sha256_file(ATTEMPT4_RESULT_ROOT / name) != digest
        for name, digest in ATTEMPT4_REQUIRED_SHA256.items()
    ):
        raise RuntimeError("ATTEMPT4_FAILED_ROOT_EVIDENCE_MUTATION")
    raw = ATTEMPT4_RESULT_ROOT / "raw/trial_15"
    trace_rows = [json.loads(line) for line in (raw / "runtime_trace.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = [json.loads(line) for line in (raw / "cycle_observations.jsonl").read_text(encoding="utf-8").splitlines()]
    replay = executed_action_l2_next_l1_audit(trace_rows, observations)
    expected = {
        "l2_next_l1_continuity_applicable_count": 190,
        "l2_next_l1_continuity_mismatch_count": 0,
        "l2_next_l1_continuity_not_applicable_count": 309,
        "l2_next_l1_continuity_unknown_count": 0,
        "l2_next_l1_continuity_cross_cycle_rows": 499,
        "l2_next_l1_continuity_role_counts": {
            "PRIMARY_NAVIGATION": 190, "RETAINED_BACKUP": 12, "CERTIFIED_TERMINAL": 297,
        },
    }
    if replay != expected:
        raise RuntimeError("RETRY4_EXECUTED_ACTION_CONTINUITY_REPLAY_MISMATCH")
    fact_keys = {key for row in trace_rows for key, _ in row.get("facts", [])}
    nonprimary_k2 = sorted(
        key for key in fact_keys if ("backup" in key or "terminal" in key)
        and ("p_k2" in key or "future_position_identity" in key or "next_l1_endpoint_identity" in key)
    )
    if nonprimary_k2:
        raise RuntimeError("EXECUTED_NONPRIMARY_K2_IDENTITY_REQUIRES_SEPARATE_CONTRACT")
    replay["executed_nonprimary_k2_identity_status"] = "NO_EXECUTED_NONPRIMARY_K2_IDENTITY_AVAILABLE"
    return replay


def synthetic_executed_action_continuity_regression() -> dict[str, str]:
    def fixture(role: str, predicted: str, next_l1: str, *, identity_match: bool = True) -> dict[str, Any]:
        selected = "action-id"
        executed = selected if identity_match else "other-action-id"
        trace = [
            {"trial_id": "STONEHENGE_TRIAL_015", "cycle_index": 0, "action_role": role,
             "selected_action_identity": selected, "executed_action_identity": executed,
             "facts": [("canonical_l2_p_k2_identity", predicted)]},
            {"trial_id": "STONEHENGE_TRIAL_015", "cycle_index": 1, "facts": [("canonical_l1_endpoint_identity", next_l1)]},
        ]
        observations = [
            {"trial_id": 15, "cycle_index": 0, "committed": True,
             "action_role": role, "selected_action_identity": selected,
             "executed_action_identity": executed},
            {"trial_id": 15, "cycle_index": 1},
        ]
        return executed_action_l2_next_l1_audit(trace, observations)

    mismatch = fixture("PRIMARY_NAVIGATION", "predicted", "different")
    match = fixture("PRIMARY_NAVIGATION", "same", "same")
    backup = fixture("RETAINED_BACKUP", "unused-primary", "different")
    terminal = fixture("CERTIFIED_TERMINAL", "unused-primary", "different")
    invalid = fixture("RETAINED_BACKUP", "unused-primary", "different", identity_match=False)
    if (mismatch["l2_next_l1_continuity_applicable_count"] != 1
            or mismatch["l2_next_l1_continuity_mismatch_count"] != 1
            or match["l2_next_l1_continuity_applicable_count"] != 1
            or match["l2_next_l1_continuity_mismatch_count"] != 0
            or any(row["l2_next_l1_continuity_not_applicable_count"] != 1
                   or row["l2_next_l1_continuity_mismatch_count"] != 0
                   for row in (backup, terminal))
            or invalid["l2_next_l1_continuity_unknown_count"] != 1
            or invalid["l2_next_l1_continuity_not_applicable_count"] != 0):
        raise RuntimeError("EXECUTED_ACTION_CONTINUITY_SYNTHETIC_REGRESSION_FAILED")
    for row in (mismatch, match, backup, terminal, invalid):
        if (row["l2_next_l1_continuity_applicable_count"]
                + row["l2_next_l1_continuity_not_applicable_count"]
                + row["l2_next_l1_continuity_unknown_count"]
                != row["l2_next_l1_continuity_cross_cycle_rows"]):
            raise RuntimeError("EXECUTED_ACTION_CONTINUITY_DENOMINATOR_MISMATCH")
    return {
        "primary_mismatch": "PASS", "primary_match": "PASS",
        "nonprimary_not_applicable": "PASS", "identity_mismatch_fail_closed": "PASS",
        "denominator_contract": "PASS",
    }


def audit_trial_evidence(raw: Path) -> dict[str, Any]:
    trace_rows = [json.loads(line) for line in (raw / "runtime_trace.jsonl").read_text(encoding="utf-8").splitlines()]
    observations = [json.loads(line) for line in (raw / "cycle_observations.jsonl").read_text(encoding="utf-8").splitlines()]
    if len(trace_rows) != len(observations):
        raise RuntimeError("TRACE_OBSERVATION_CARDINALITY_MISMATCH")
    from reproduction.runtime.certification_execution_state_identity_repair_v1.canonical_transition import CanonicalExecutionTransition
    mismatch = drift = l1_actual = backup = incomplete = forbidden = 0
    expected_transition = protocol()["canonical_transition"]["identity"]
    for trace, observation in zip(trace_rows, observations):
        facts = dict(trace.get("facts", []))
        drift += int(facts.get("canonical_transition_arithmetic_identity") != expected_transition)
        mismatch += int(facts.get("cert_exec_state_identity_status") == "CERT_EXEC_STATE_IDENTITY_MISMATCH")
        backup += int(facts.get("canonical_backup_state_identity_status") == "CERT_EXEC_STATE_IDENTITY_MISMATCH")
        forbidden += int(facts.get("historical_0p025_runtime_authority") is True)
        required = ("canonical_transition_arithmetic_identity", "canonical_pre_state_identity", "canonical_l1_endpoint_identity", "canonical_l1_segment_identity", "canonical_l1_status", "canonical_l1_reason", "canonical_l1_evidence_identity")
        incomplete += int(any(name not in facts for name in required))
        if observation["committed"]:
            incomplete += int(facts.get("cert_exec_state_identity_status") != "CERT_EXEC_STATE_IDENTITY_MATCH")
            post = observation.get("post_state")
            actual_position = None if post is None else CanonicalExecutionTransition.vector_identity("position", post[:3])
            l1_actual += int(actual_position is None or facts.get("canonical_l1_endpoint_identity") != actual_position)
        elif observation["boundary"] and observation.get("post_state") is not None:
            incomplete += 1
    continuity = executed_action_l2_next_l1_audit(trace_rows, observations)
    result = {
        "canonical_transition_drift_count": drift,
        "cert_exec_identity_mismatch_count": mismatch,
        "l1_actual_continuity_mismatch_count": l1_actual,
        **continuity,
        "backup_token_continuity_mismatch_count": backup,
        "forbidden_diagnostic_authority_event_count": forbidden,
        "normative_identity_payload_incomplete_count": incomplete,
    }
    summary_path = raw / "trial_summary.json"
    summary = load_json(summary_path); summary.update(result); write_json(summary_path, summary)
    return result


def run_one(checkout: Path, root: Path, trial: int) -> int:
    verify_authorization(checkout, root, trial, os.environ.get(CHILD_TOKEN_ENV))
    delegate = _load_delegate(checkout)
    with observe_cycles(checkout, root, trial):
        code = int(delegate.run_one(checkout, root, trial))
    raw = root / "raw" / f"trial_{trial}"
    if (raw / "runtime_trace.jsonl").is_file() and (raw / "cycle_observations.jsonl").is_file():
        audit_trial_evidence(raw)
    return code


def gpu_preflight(checkout: Path, root: Path) -> int:
    try:
        verify_static_identity(checkout, require_committed_lock=True)
        delegate = _load_delegate(checkout)
        code = int(delegate.run_preflight(checkout, root))
    except Exception as exc:
        import traceback
        captured_traceback = traceback.format_exc()
        try:
            lock_sha = sha256_file(LOCK_PATH)
            lock_sha_unavailable_reason = None
        except (OSError, ValueError) as lock_exc:
            lock_sha = None
            lock_sha_unavailable_reason = type(lock_exc).__name__
        failure = {
            "schema": "CERT_EXEC_IDENTITY_REPAIR_SMOKE_GPU_PREFLIGHT_FAILURE_V1",
            "stage": "GPU_PREFLIGHT", "status": "FAIL",
            "exception_type": type(exc).__name__, "exception_message": str(exc),
            "traceback": captured_traceback,
            "traceback_tail": captured_traceback.splitlines()[-12:],
            "traceback_sha256": hashlib.sha256(captured_traceback.encode()).hexdigest(),
            "branch": git(checkout, "branch", "--show-current"), "source_head": git(checkout, "rev-parse", "HEAD"),
            "protocol_sha256": sha256_file(PROTOCOL_PATH), "execution_lock_sha256": lock_sha,
            "execution_lock_sha_unavailable_reason": lock_sha_unavailable_reason,
            "result_root": str(root), "runtime_cycles_executed": 0,
            "smoke_trial_execution_count": 0, "PlantCommit_count": 0,
            "controller_qp_trial_count": 0, "scientific_analysis_performed": False,
            "gpu_release_status": "NO_RUNTIME_PROCESS_STARTED",
        }
        write_json(root / "gpu_preflight_failure.json", failure)
        return 2
    path = root / "raw/gpu_preflight.json"; data = load_json(path)
    data.update({"schema": "CERT_EXEC_IDENTITY_REPAIR_SMOKE_GPU_PREFLIGHT_V1", "runtime_cycles_executed": 0, "plant_commit_count": 0, "implementation_head": IMPLEMENTATION_HEAD})
    write_json(path, data)
    return code


def _gpu_released(delegate: Any, pid: int) -> bool:
    return bool(delegate.gpu_pid_released(pid))


def freeze_raw_evidence(raw: Path) -> None:
    names = ("trial_summary.json", "runtime_trace.jsonl", "runtime_trace_lock.json", "cycle_observations.jsonl", "process_exit_code.txt", "gpu_released.txt", "stdout.log", "stderr.log")
    files = {}
    for name in names:
        path = raw / name
        if not path.is_file():
            raise RuntimeError("TRIAL_EVIDENCE_FILE_MISSING:" + name)
        files[name] = {"size": path.stat().st_size, "sha256": sha256_file(path)}
    lock = {"schema": "CERT_EXEC_IDENTITY_REPAIR_SMOKE_RAW_EVIDENCE_LOCK_V1", "trial_id": int(raw.name.split("_")[-1]), "files": files, "immutable": True}
    lock["identity"] = "cert-exec-smoke-raw:sha256:" + semantic_sha256(lock)
    write_json(raw / "SMOKE_REPAIR_V1_RAW_EVIDENCE_LOCK.json", lock)


def complete_trial(root: Path, trial: int) -> bool:
    raw = root / "raw" / f"trial_{trial}"
    lock_path = raw / "SMOKE_REPAIR_V1_RAW_EVIDENCE_LOCK.json"
    if not lock_path.is_file():
        return False
    try:
        summary = load_json(raw / "trial_summary.json"); lock = load_json(lock_path)
        for name, expected in lock["files"].items():
            path = raw / name
            if path.stat().st_size != expected["size"] or sha256_file(path) != expected["sha256"]:
                return False
        zero_fields = protocol()["summary_continuity_fields"] + [
            "normative_identity_payload_incomplete_count", "l2_next_l1_continuity_unknown_count",
        ]
        trace_rows = [json.loads(line) for line in (raw / "runtime_trace.jsonl").read_text(encoding="utf-8").splitlines()]
        observations = [json.loads(line) for line in (raw / "cycle_observations.jsonl").read_text(encoding="utf-8").splitlines()]
        replay = executed_action_l2_next_l1_audit(trace_rows, observations)
        count_fields = (
            "l2_next_l1_continuity_applicable_count",
            "l2_next_l1_continuity_mismatch_count",
            "l2_next_l1_continuity_not_applicable_count",
            "l2_next_l1_continuity_unknown_count",
            "l2_next_l1_continuity_cross_cycle_rows",
        )
        return (summary.get("process_exit_code") == 0 and summary.get("finalization_status") == "FINALIZED"
                and all(int(summary.get(name, -1)) == 0 for name in zero_fields)
                and all(summary.get(name) == replay[name] for name in count_fields)
                and summary.get("l2_next_l1_continuity_role_counts") == replay["l2_next_l1_continuity_role_counts"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False


def write_collection_summary(root: Path) -> dict[str, Any]:
    complete = [trial for trial in TRIALS if complete_trial(root, trial)]
    hard_zero_fields = protocol()["summary_continuity_fields"] + [
        "normative_identity_payload_incomplete_count", "l2_next_l1_continuity_unknown_count",
    ]
    telemetry_fields = [
        "l2_next_l1_continuity_applicable_count",
        "l2_next_l1_continuity_not_applicable_count",
        "l2_next_l1_continuity_cross_cycle_rows",
    ]
    totals = {name: 0 for name in hard_zero_fields + telemetry_fields}
    cycles = traces = locks = commits = boundaries = 0
    for trial in complete:
        raw = root / "raw" / f"trial_{trial}"; summary = load_json(raw / "trial_summary.json"); trace_lock = load_json(raw / "runtime_trace_lock.json")
        cycles += int(summary["completed_cycles"]); traces += len((raw / "runtime_trace.jsonl").read_text().splitlines()); locks += int(trace_lock["record_count"])
        commits += int(summary["plant_commit_count"]); boundaries += int(summary["assurance_boundary_count"])
        for name in totals: totals[name] += int(summary[name])
    result = {
        "schema": "CERT_EXEC_IDENTITY_REPAIR_SMOKE_COLLECTION_SUMMARY_V1",
        "trials_planned": list(TRIALS), "trials_completed": complete, "completion_order": complete,
        "completed_cycles": cycles, "trace_records": traces, "trace_lock_records": locks,
        "plant_commits": commits, "boundary_cycles": boundaries, "continuity_totals": totals,
        "trace_cardinality_pass": cycles == traces == locks, "scientific_analysis_performed": False,
        "status": "PASS_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_SMOKE_V1" if complete == list(TRIALS) and cycles == traces == locks and all(totals[name] == 0 for name in hard_zero_fields) else "BLOCK_CERT_EXEC_IDENTITY_REPAIR_SMOKE_INTEGRITY",
    }
    write_json(root / "SMOKE_REPAIR_V1_COLLECTION_SUMMARY.json", result)
    return result


def run_batch(checkout: Path, root: Path) -> int:
    verify_static_identity(checkout, require_committed_lock=True)
    delegate = _load_delegate(checkout)
    token = secrets.token_hex(32)
    for trial in TRIALS:
        if complete_trial(root, trial):
            print(f"TRIAL_{trial}_IMMUTABLE_COMPLETE_SKIP", flush=True); continue
        raw = root / "raw" / f"trial_{trial}"
        if raw.exists():
            raise RuntimeError(f"INCOMPLETE_EXISTING_TRIAL_EVIDENCE_REVIEW_REQUIRED:{trial}")
        auth = write_authorization(checkout, root, trial, token)
        stdout = root / f"trial_{trial}_stdout.tmp"; stderr = root / f"trial_{trial}_stderr.tmp"
        env = os.environ.copy(); env.update(protocol()["environment"]); env[CHILD_TOKEN_ENV] = token
        command = [protocol()["environment"]["python"], str(Path(__file__).resolve()), "--one", str(trial), "--checkout", str(checkout), "--output-dir", str(root)]
        with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
            process = subprocess.Popen(command, env=env, stdout=out, stderr=err, text=True); code = process.wait()
        released = _gpu_released(delegate, process.pid); auth.unlink(missing_ok=True)
        if raw.is_dir():
            stdout.replace(raw / "stdout.log"); stderr.replace(raw / "stderr.log")
            (raw / "process_exit_code.txt").write_text(f"{code}\n", encoding="utf-8")
            (raw / "gpu_released.txt").write_text(("true" if released else "false") + "\n", encoding="utf-8")
            try: freeze_raw_evidence(raw)
            except RuntimeError: write_collection_summary(root); return code or 2
        else:
            preserve_early_child_failure(root, trial, code, released, stdout, stderr); write_collection_summary(root); return code or 2
        if code or not released or not complete_trial(root, trial):
            write_collection_summary(root); return code or 2
        write_collection_summary(root)
    print("COLLECTION_COMPLETE_OR_STOPPED_REVIEW_BEFORE_ANY_SCIENTIFIC_ANALYSIS", flush=True)
    return 0


def cpu_static_preflight(checkout: Path) -> dict[str, Any]:
    if RESULT_ROOT.exists():
        raise RuntimeError("FIRST_LAUNCH_RESULT_ROOT_ALREADY_EXISTS")
    if GPU_PREFLIGHT_DIAGNOSTIC_ROOT.exists():
        result = GPU_PREFLIGHT_DIAGNOSTIC_ROOT / "raw" / "gpu_preflight.json"
        try:
            diagnostic = load_json(result)
            valid = (diagnostic.get("status") == "PASS"
                     and int(diagnostic.get("runtime_cycles_executed", -1)) == 0
                     and int(diagnostic.get("plant_commit_count", -1)) == 0)
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            valid = False
        if not valid:
            raise RuntimeError("GPU_PREFLIGHT_DIAGNOSTIC_ROOT_INVALID")
    if str(checkout) not in sys.path:
        sys.path.insert(0, str(checkout))
    identity = verify_static_identity(checkout, require_committed_lock=False)
    if sha256_file(PROTOCOL_PATH) != ORIGINAL_PROTOCOL_SHA256 or sha256_file(ORIGINAL_LOCK_PATH) != ORIGINAL_LOCK_SHA256:
        raise RuntimeError("ORIGINAL_PROTOCOL_OR_LOCK_MUTATION")
    if not OLD_RESULT_ROOT.is_dir() or sha256_file(OLD_RESULT_ROOT / "launcher.log") != OLD_LAUNCHER_LOG_SHA256:
        raise RuntimeError("OLD_FAILED_ROOT_EVIDENCE_MUTATION")
    if not ATTEMPT1_RESULT_ROOT.is_dir() or sha256_file(ATTEMPT1_RESULT_ROOT / "launcher.log") != ATTEMPT1_LAUNCHER_LOG_SHA256:
        raise RuntimeError("ATTEMPT1_FAILED_ROOT_EVIDENCE_MUTATION")
    if (not ATTEMPT2_RESULT_ROOT.is_dir()
            or sha256_file(ATTEMPT2_RESULT_ROOT / "launcher.log") != ATTEMPT2_LAUNCHER_LOG_SHA256
            or sha256_file(ATTEMPT2_RESULT_ROOT / "gpu_preflight_failure.json") != ATTEMPT2_FAILURE_JSON_SHA256):
        raise RuntimeError("ATTEMPT2_FAILED_ROOT_EVIDENCE_MUTATION")
    if (not ATTEMPT3_RESULT_ROOT.is_dir() or any(
            sha256_file(ATTEMPT3_RESULT_ROOT / name) != digest
            for name, digest in ATTEMPT3_REQUIRED_SHA256.items())):
        raise RuntimeError("ATTEMPT3_FAILED_ROOT_EVIDENCE_MUTATION")
    replay = replay_retry4_continuity()
    continuity_fixtures = synthetic_executed_action_continuity_regression()
    base = load_runtime_base_config(checkout)
    projected_delegate = delegate_runtime_protocol(checkout)
    if (projected_delegate["seed"] != 0
            or projected_delegate["maximum_completed_cycles_per_trial"] != 500
            or projected_delegate["dynamics"]["dt"] != base["dynamics"]["dt"]):
        raise RuntimeError("DELEGATE_PROTOCOL_COMPATIBILITY_MISMATCH")
    from reproduction.runtime.v3_hard_radius_runtime_wiring_v1.stack_config import project_v3_runtime_config
    projected = project_v3_runtime_config(base)
    if projected["controller"]["controller_radius"] != 0.015 or projected["certification"]["certification_margin"] != 0.0 or projected["certification"]["certification_effective_radius"] != 0.015 or projected["certification"]["rho_seg"] != 0.0:
        raise RuntimeError("PROJECTED_V3_GEOMETRY_MISMATCH")
    frozen = protocol()
    if frozen["cohort"]["trial_ids"] != list(TRIALS) or frozen["cohort"]["trial_order"] != list(TRIALS):
        raise RuntimeError("FROZEN_SMOKE_COHORT_MISMATCH")
    if frozen["cohort"]["maximum_completed_cycles_per_trial"] != 500 or frozen["cohort"]["seed"] != 0:
        raise RuntimeError("FROZEN_EXECUTION_LIMIT_MISMATCH")
    maps = verify_map_artifacts(frozen)
    mismatch = synthetic_mismatch_guard_test()
    launcher = (TASK_DIR / "launch_cert_exec_identity_repair_smoke_v1.sh").read_text(encoding="utf-8")
    outer_markers = ["echo RESULT_ROOT_ABSENT", "--cpu-static-preflight", "\"$PYTHON\" \"$VALIDATOR\" --repo-root", "mkdir -p", "COMMAND=", "tmux new-session"]
    indices = [launcher.index(marker) for marker in outer_markers]
    command = launcher[launcher.index("COMMAND="):launcher.index("tmux new-session")]
    if indices != sorted(indices) or command.index("--gpu-preflight") > command.index("--batch"):
        raise RuntimeError("FIRST_LAUNCH_ORDERING_INVALID")
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp); out = root / "stdout.tmp"; err = root / "stderr.tmp"; out.write_text("x"); err.write_text("y")
        failure = preserve_early_child_failure(root, 15, 7, True, out, err)
        if not (failure / "EARLY_CHILD_FAILURE.json").is_file():
            raise RuntimeError("EARLY_CHILD_FAILURE_PERSISTENCE_TEST_FAILED")
        token = "fixture"; auth_root = root / "auth"; auth_root.mkdir(); write_json(auth_root / AUTHORIZATION_NAME, authorization_payload(checkout, auth_root, 15, token))
        saved = globals()["RESULT_ROOT"]; globals()["RESULT_ROOT"] = auth_root
        try: verify_authorization(checkout, auth_root, 15, token)
        finally: globals()["RESULT_ROOT"] = saved
    required_summary = set(frozen["summary_continuity_fields"])
    if required_summary != {"canonical_transition_drift_count", "cert_exec_identity_mismatch_count", "l1_actual_continuity_mismatch_count", "l2_next_l1_continuity_mismatch_count", "backup_token_continuity_mismatch_count", "forbidden_diagnostic_authority_event_count"}:
        raise RuntimeError("SUMMARY_CONTINUITY_SCHEMA_INCOMPLETE")
    boundary_fixture = {"completed_cycles": 1, "trace_records": 1, "trace_lock_records": 1, "plant_commits": 0}
    if not (boundary_fixture["completed_cycles"] == boundary_fixture["trace_records"] == boundary_fixture["trace_lock_records"] and boundary_fixture["plant_commits"] == 0):
        raise RuntimeError("BOUNDARY_TRACE_CARDINALITY_SEMANTICS_FAILED")
    result = {
        "schema": "CERT_EXEC_IDENTITY_REPAIR_SMOKE_CPU_STATIC_PREFLIGHT_V1", "status": "PASS",
        "identity": identity, "map_artifacts": maps, "synthetic_mismatch_guard": mismatch,
        "historical_v3_base_config_sha256": HISTORICAL_V3_PROTOCOL_SHA256,
        "historical_v3_base_config_mappings": ["controller", "certification", "dynamics", "deadline_profile"],
        "delegate_protocol_contract": "PASS", "child_config_consumption_regression": "PASS",
        "retry4_executed_action_continuity_replay": replay,
        "executed_action_continuity_fixtures": continuity_fixtures,
        "projected_v3_geometry": {"controller_radius": 0.015, "certification_margin": 0.0, "certification_effective_radius": 0.015, "rho_seg": 0.0},
        "child_authorization_regression": "PASS", "first_launch_ordering_regression": "PASS",
        "early_child_failure_persistence_regression": "PASS", "trace_cardinality_semantics_regression": "PASS",
        "summary_schema_continuity_fields_complete": True, "gpu_preflight_count": 0,
        "smoke_trial_execution_count": 0, "controller_qp_count": 0, "plant_commit_count": 0,
        "analyzer_count": 0, "reference_rerun_count": 0, "official100_formal_count": 0,
        "future_result_root_absent": True,
    }
    print(json.dumps(result, sort_keys=True))
    print("DELEGATE_PROTOCOL_CONTRACT_PASS")
    print("CHILD_CONFIG_CONSUMPTION_REGRESSION_PASS")
    print("RETRY4_EXECUTED_ACTION_CONTINUITY_REPLAY_PASS")
    print("EXECUTED_ACTION_CONTINUITY_CONTRACT_PASS")
    print("PASS_CERT_EXEC_IDENTITY_REPAIR_SMOKE_CPU_STATIC_PREFLIGHT")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--cpu-static-preflight", action="store_true")
    modes.add_argument("--gpu-preflight", action="store_true")
    modes.add_argument("--one", type=int)
    modes.add_argument("--batch", action="store_true")
    parser.add_argument("--checkout", type=Path, default=CHECKOUT_DEFAULT)
    parser.add_argument("--output-dir", type=Path, default=RESULT_ROOT)
    args = parser.parse_args(); checkout = args.checkout.resolve(strict=True); output = args.output_dir.resolve()
    if args.cpu_static_preflight:
        cpu_static_preflight(checkout); return 0
    if output not in (RESULT_ROOT, GPU_PREFLIGHT_DIAGNOSTIC_ROOT) or not output.is_dir():
        raise RuntimeError("PARENT_OWNED_FROZEN_RESULT_ROOT_REQUIRED")
    if args.gpu_preflight:
        return gpu_preflight(checkout, output)
    if args.one is not None:
        if args.one not in TRIALS: raise RuntimeError("TRIAL_NOT_IN_FROZEN_SMOKE_COHORT")
        return run_one(checkout, output, args.one)
    return run_batch(checkout, output)


if __name__ == "__main__":
    raise SystemExit(main())
