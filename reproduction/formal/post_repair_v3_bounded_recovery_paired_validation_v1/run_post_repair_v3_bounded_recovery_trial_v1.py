#!/usr/bin/env python3
"""Future one-trial GPU adapter. Importing this module never starts a trial."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
PROTOCOL = TASK / "POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_PROTOCOL.json"
LOCK = TASK / "POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_EXECUTION_LOCK.json"
BASE_V3 = REPO / "reproduction/smoke/active_runtime_smoke_v3/SMOKE_V3_PROTOCOL.json"
V3_RUNNER = REPO / "reproduction/smoke/active_runtime_smoke_v3/run_active_runtime_smoke_v3.py"
AUTH_NAME = "POST_REPAIR_V3_BOUNDED_RECOVERY_INTERNAL_CHILD_AUTHORIZATION.json"
TOKEN_ENV = "SAFER_SPLAT_POST_REPAIR_V3_BOUNDED_RECOVERY_CHILD_TOKEN"


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args], check=True, capture_output=True, text=True).stdout.strip()


def projected_v3_protocol() -> dict:
    """Keep frozen V3 controller/dynamics/deadline; project only cohort/environment."""
    p = read(PROTOCOL)
    base = deepcopy(read(BASE_V3))
    cohort = p["cohort"]
    for field in ("seed", "maximum_completed_cycles_per_trial", "trial_ids", "trial_order",
                  "serial_execution", "separate_process_per_trial"):
        base[field] = cohort[field]
    base["environment"] = {k: v for k, v in p["environment"].items()
                           if k not in ("physical_gpu", "process_visible_device", "conda_environment", "python")}
    base["map_relative_path"] = p["map"]["root"]
    base["map_identity"] = p["map"]["identity"]
    base["map_artifacts"] = p["map"]["artifacts"]
    return base


def verify_child_authorization(trial: int, root: Path) -> None:
    p = read(PROTOCOL)
    if trial not in p["cohort"]["trial_ids"] or root != Path(p["future_result_root"]):
        raise RuntimeError("UNFROZEN_TRIAL_OR_RESULT_ROOT")
    token = os.environ.get(TOKEN_ENV)
    auth = root / AUTH_NAME
    if not token or not auth.is_file():
        raise RuntimeError("UNAUTHORIZED_DIRECT_CHILD_EXECUTION")
    data = read(auth)
    expected = {"trial_id": trial, "result_root": str(root), "source_head": git("rev-parse", "HEAD"),
                "protocol_sha256": sha(PROTOCOL), "execution_lock_sha256": sha(LOCK),
                "token_sha256": hashlib.sha256(token.encode()).hexdigest()}
    if any(data.get(k) != v for k, v in expected.items()):
        raise RuntimeError("CHILD_AUTHORITY_IDENTITY_MISMATCH")
    parent = data.get("parent_pid")
    if not isinstance(parent, int) or parent <= 0 or not Path(f"/proc/{parent}").exists():
        raise RuntimeError("CHILD_PARENT_NOT_ALIVE")
    if (root / "raw" / f"trial_{trial}").exists():
        raise RuntimeError("IMMUTABLE_TRIAL_EVIDENCE_ALREADY_EXISTS_NO_RERUN")


def load_delegate():
    spec = importlib.util.spec_from_file_location("_bounded_recovery_frozen_v3_delegate", V3_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("V3_DELEGATE_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.UPSTREAM = read(PROTOCOL)["implementation_head"]
    module.FIXED_TRIALS = tuple(read(PROTOCOL)["cohort"]["trial_ids"])
    module.PROTOCOL_PATH = PROTOCOL
    module.EXECUTION_LOCK_PATH = LOCK
    module.read_protocol = projected_v3_protocol
    module.PROTECTED_PATHS = tuple(x for x in module.PROTECTED_PATHS if x != "reproduction/formal")

    def verify_source_and_map(checkout: Path, _projected: dict, require_execution_lock: bool = True):
        from validate_post_repair_v3_bounded_recovery_paired_validation_v1 import validate_freeze
        validate_freeze(require_lock=require_execution_lock, require_absent_root=False)
        p = read(PROTOCOL)
        return p["map"]["identity"], p["map"]["artifacts"]

    def build_stack(checkout: Path, output_dir: Path, trial_id: int, _projected: dict, map_identity: str):
        if str(checkout) not in sys.path:
            sys.path.insert(0, str(checkout))
        from reproduction.runtime.certification_execution_state_identity_repair_v1 import build_repaired_v3_stack
        from reproduction.runtime.active_runtime_assurance_v2.bounded_recovery import (
            BoundedRecoveryProvider, RecoveryExhaustionRegister, SOURCE, GENERATOR, DIRECTIONS)
        from reproduction.runtime.active_runtime_assurance_v2.runtime_types import canonical_sha256
        p = read(PROTOCOL)
        if (SOURCE, GENERATOR, list(DIRECTIONS)) != (p["recovery"]["source"],
                p["recovery"]["generator"], p["recovery"]["candidate_order"]):
            raise RuntimeError("RECOVERY_PROVIDER_SOURCE_OR_ORDER_DRIFT")
        base = deepcopy(read(BASE_V3))
        stack = build_repaired_v3_stack(checkout, output_dir, trial_id, base, map_identity)
        coordinator = stack["coordinator"]
        if coordinator.recovery_provider is not None or coordinator.recovery_register is not None:
            raise RuntimeError("RECOVERY_PROVIDER_ALREADY_WIRED_UNEXPECTEDLY")
        transition = stack["canonical_transition"].identity.value
        backend = "backend:sha256:" + canonical_sha256((map_identity,
            type(stack["canonical_swept_certifier"]).__module__,
            type(stack["canonical_swept_certifier"]).__qualname__))
        coordinator.recovery_provider = BoundedRecoveryProvider(stack["registry"], transition, backend)
        coordinator.recovery_register = RecoveryExhaustionRegister()
        if coordinator.recovery_provider.registry is not coordinator.registry:
            raise RuntimeError("RECOVERY_PROVIDER_REGISTRY_IDENTITY_MISMATCH")
        provider = coordinator.recovery_provider
        native_enumerate = provider.enumerate
        generation_path = output_dir / "raw" / f"trial_{trial_id}" / "recovery_generation.jsonl"

        def observe_enumeration(snapshot, grant, primary=None):
            inventory = native_enumerate(snapshot, grant, primary)
            row = {"trial_id": trial_id, "cycle_index": snapshot.cycle_index,
                   "state_identity": snapshot.identity.value, "grant_identity": grant.identity,
                   "status": inventory.status, "skipped_duplicate_ranks": list(inventory.skipped_duplicate_ranks),
                   "candidates": [{"candidate_id": item.candidate.identity.value,
                                   "candidate_rank": item.generation_rank, "direction": item.direction,
                                   "vector": list(item.candidate.vector),
                                   "canonical_control_identity": item.canonical_control_identity}
                                  for item in inventory.candidates]}
            generation_path.parent.mkdir(parents=True, exist_ok=True)
            with generation_path.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            return inventory

        provider.enumerate = observe_enumeration
        audit = stack["repaired_stack_wiring_audit"]
        if audit.get("status") != "PASS" or not all(audit.get("checks", {}).values()):
            raise RuntimeError("REPAIRED_V3_STACK_WIRING_FAILED")
        stack["v3_wiring_audit"] = {
            "status": "PASS", "hard_runtime_radius_q": 0.015, "runtime_margin_q": 0.0,
            "runtime_effective_radius_q": 0.015, "rho_seg_q": 0.0,
            "historical_diagnostic_radius_q": 0.025,
            "historical_diagnostic_runtime_authority": False,
            "canonical_transition_identity": transition, "checks": audit["checks"],
            "recovery_source": SOURCE, "recovery_generator": GENERATOR,
            "recovery_provider_registry_identity": "MATCH",
        }
        return stack

    module.verify_source_and_map = verify_source_and_map
    module.build_v3_stack = build_stack
    return module


@contextmanager
def capture_recovery_cycles(root: Path, trial: int):
    """Append QA observations after commit; never feed observations into policy."""
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from reproduction.runtime.active_runtime_assurance_v2.active_cycle import ActiveCycleCoordinator
    original = ActiveCycleCoordinator.run_cycle
    path = root / "raw" / f"trial_{trial}" / "recovery_cycle_observations.jsonl"

    def observed(self, snapshot, request):
        result = original(self, snapshot, request)
        receipt = result.commit_receipt
        row = {
            "trial_id": trial, "cycle_index": int(request.cycle_index),
            "pre_state": list(snapshot.state), "goal_state": list(snapshot.goal),
            "pre_state_identity": snapshot.identity.value,
            "post_state": None if result.next_state is None else list(result.next_state.state),
            "post_state_identity": None if result.next_state is None else result.next_state.identity.value,
            "committed": bool(result.committed), "boundary": bool(result.boundary),
            "routing_rule_ids": list(result.routing_rule_ids),
            "phase_history": [x.value for x in result.phase_history],
            "stage_failures": [{"stage": x.stage_name, "reason": x.typed_reason,
                                "scope": x.reason_scope.value, "phase": x.source_phase.value}
                               for x in result.stage_failures],
            "deadline_observations": [{"stage": x.stage, "status": x.status.value} for x in result.deadline_observations],
            "l1_status": None if result.l1_result is None else result.l1_result.status.value,
            "backup_status": result.backup_status, "terminal_status": result.terminal_status,
            "supervisor_reason": result.supervisor_reason,
            "selected_action_identity": None if result.final_supervisor_decision is None or result.final_supervisor_decision.selected_action is None else result.final_supervisor_decision.selected_action.identity.value,
            "selected_action_source_identity": None if result.final_supervisor_decision is None or result.final_supervisor_decision.selected_action is None else result.final_supervisor_decision.selected_action.source_identity,
            "executed_action_identity": None if receipt is None else receipt.executed_action_identity.value,
            "action_role": None if receipt is None else receipt.action_role.value,
            "recovery_attempts": [dict(item) for item in result.recovery_attempts],
            "trace_ref": result.trace_ref,
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        return result

    ActiveCycleCoordinator.run_cycle = observed
    try:
        yield
    finally:
        ActiveCycleCoordinator.run_cycle = original


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--one", type=int, required=True, help="One frozen trial ID; requires launcher authorization")
    args = parser.parse_args()
    p = read(PROTOCOL)
    root = Path(p["future_result_root"])
    verify_child_authorization(args.one, root)
    from validate_post_repair_v3_bounded_recovery_paired_validation_v1 import validate_freeze
    validate_freeze(require_lock=True, require_absent_root=False)
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "1":
        raise RuntimeError("PHYSICAL_GPU1_ONLY")
    delegate = load_delegate()
    with capture_recovery_cycles(root, args.one):
        code = int(delegate.run_one(REPO, root, args.one))
    metadata = {
        "schema": "POST_REPAIR_V3_BOUNDED_RECOVERY_TRIAL_PROCESS_METADATA_V1", "trial_id": args.one,
        "source_head": git("rev-parse", "HEAD"), "map_identity": p["map"]["identity"],
        "map_artifacts": p["map"]["artifacts"], "geometry": p["geometry"],
        "recovery": p["recovery"], "process_id": os.getpid(), "exit_code": code,
    }
    destination = root / "raw" / f"trial_{args.one}" / "bounded_recovery_process_metadata.json"
    destination.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
