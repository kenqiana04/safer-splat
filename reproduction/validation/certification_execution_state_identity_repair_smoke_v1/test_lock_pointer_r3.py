#!/usr/bin/env python3
"""CPU-only lock-pointer and failure-persistence regressions."""
from __future__ import annotations

import importlib.util
import hashlib
import json
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_error(fn, token: str) -> None:
    try:
        fn()
    except RuntimeError as exc:
        assert token in str(exc), (token, exc)
    else:
        raise AssertionError(f"expected {token}")


def check_nonprimary_summary_acceptance(runner, root: Path) -> None:
    raw = root / "raw/trial_15"
    raw.mkdir(parents=True)
    trace = [
        {"trial_id": "STONEHENGE_TRIAL_015", "cycle_index": 0, "action_role": "RETAINED_BACKUP",
         "selected_action_identity": "a", "executed_action_identity": "a",
         "facts": [["canonical_l2_p_k2_identity", "unused-primary"]]},
        {"trial_id": "STONEHENGE_TRIAL_015", "cycle_index": 1,
         "facts": [["canonical_l1_endpoint_identity", "actual-backup"]]},
    ]
    observations = [
        {"trial_id": 15, "cycle_index": 0, "committed": True,
         "action_role": "RETAINED_BACKUP", "selected_action_identity": "a",
         "executed_action_identity": "a"},
        {"trial_id": 15, "cycle_index": 1},
    ]
    continuity = runner.executed_action_l2_next_l1_audit(trace, observations)
    assert continuity["l2_next_l1_continuity_not_applicable_count"] == 1
    summary = {name: 0 for name in runner.protocol()["summary_continuity_fields"]}
    summary.update(continuity)
    summary.update({
        "normative_identity_payload_incomplete_count": 0,
        "process_exit_code": 0, "finalization_status": "FINALIZED",
        "completed_cycles": 2, "plant_commit_count": 2, "assurance_boundary_count": 0,
    })
    runner.write_json(raw / "trial_summary.json", summary)
    runner.write_json(raw / "runtime_trace_lock.json", {"record_count": 2})
    for name, rows in (("runtime_trace.jsonl", trace), ("cycle_observations.jsonl", observations)):
        (raw / name).write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    names = ("trial_summary.json", "runtime_trace_lock.json", "runtime_trace.jsonl", "cycle_observations.jsonl")
    files = {
        name: {"size": (raw / name).stat().st_size, "sha256": hashlib.sha256((raw / name).read_bytes()).hexdigest()}
        for name in names
    }
    runner.write_json(raw / "SMOKE_REPAIR_V1_RAW_EVIDENCE_LOCK.json", {"files": files})
    assert runner.complete_trial(root, 15)
    original_trials = runner.TRIALS
    runner.TRIALS = (15,)
    try:
        collection = runner.write_collection_summary(root)
    finally:
        runner.TRIALS = original_trials
    assert collection["status"] == "PASS_CERTIFICATION_EXECUTION_STATE_IDENTITY_REPAIR_SMOKE_V1"
    assert collection["continuity_totals"]["l2_next_l1_continuity_not_applicable_count"] == 1


def main() -> int:
    validator = load("r6_validator", HERE / "validate_cert_exec_identity_repair_smoke_v1.py")
    runner = load("r6_runner", HERE / "run_cert_exec_identity_repair_smoke_v1.py")
    source = validator.RUNNER.read_text(encoding="utf-8")
    assert validator.active_lock_basename(source) == "SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY5_R6.json"
    assert validator.preflight_identity_is_caught(source)
    for obsolete in ("SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY1.json", "SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY1_R2.json", "SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY2_R3.json", "SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY3_R4.json", "SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY4_R5.json"):
        simulated = source.replace("SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY5_R6.json", obsolete, 1)
        assert validator.active_lock_basename(simulated) != validator.R6_LOCK.name
    validator.validate_old_root()
    validator.validate_old_root(validator.ATTEMPT1_ROOT, validator.ATTEMPT1_ROOT_MANIFEST)
    validator.validate_old_root(validator.ATTEMPT2_ROOT, validator.ATTEMPT2_ROOT_MANIFEST)
    validator.validate_attempt3_outcome()
    replay = validator.validate_attempt4_outcome()
    assert replay["l2_next_l1_continuity_applicable_count"] == 190
    assert replay["l2_next_l1_continuity_not_applicable_count"] == 309
    assert all(value == "PASS" for value in runner.synthetic_executed_action_continuity_regression().values())
    validator.validate_retry_root_absent()
    checkout = Path(__file__).resolve().parents[3]
    passed, failed = [], []
    accesses = validator.validate_delegate_contract(checkout, passed, failed)
    assert not failed and "seed" in accesses and "dynamics.dt" in accesses
    assert runner.delegate_runtime_protocol(checkout)["seed"] == 0
    delegate = runner._load_delegate(checkout)
    original_static = runner.verify_static_identity
    original_map = runner.verify_map_artifacts
    seen = []
    runner.verify_static_identity = lambda *args, **kwargs: {}
    runner.verify_map_artifacts = lambda frozen: seen.append(frozen) or []
    try:
        identity, rows = delegate.verify_source_and_map(checkout, delegate.read_protocol(), False)
    finally:
        runner.verify_static_identity = original_static
        runner.verify_map_artifacts = original_map
    assert seen == [runner.protocol()] and identity == runner.protocol()["map"]["identity"] and rows == []
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        old = root / "old"
        old.mkdir()
        (old / "launcher.log").write_bytes((validator.OLD_ROOT / "launcher.log").read_bytes())
        validator.validate_old_root(old)
        (old / "launcher.log").write_bytes(b"changed")
        expect_error(lambda: validator.validate_old_root(old), "OLD_FAILED_ROOT_IDENTITY_MISMATCH")
        retry = root / "retry5"
        retry.mkdir()
        expect_error(lambda: validator.validate_retry_root_absent(retry), "RETRY5_ROOT_MUST_BE_ABSENT")
        check_nonprimary_summary_acceptance(runner, root)
        original_verify = runner.verify_static_identity
        original_delegate = runner._load_delegate
        original_lock = runner.LOCK_PATH
        def mismatch(*args, **kwargs):
            raise RuntimeError("HARNESS_HASH_MISMATCH:run_cert_exec_identity_repair_smoke_v1.py")
        def forbidden_delegate(*args, **kwargs):
            raise AssertionError("delegate must not load after identity failure")
        runner.verify_static_identity = mismatch
        runner._load_delegate = forbidden_delegate
        runner.LOCK_PATH = root / "unavailable-lock.json"
        try:
            assert runner.gpu_preflight(Path(__file__).resolve().parents[3], root) == 2
        finally:
            runner.verify_static_identity = original_verify
            runner._load_delegate = original_delegate
            runner.LOCK_PATH = original_lock
        failure = json.loads((root / "gpu_preflight_failure.json").read_text(encoding="utf-8"))
        assert failure["stage"] == "GPU_PREFLIGHT" and failure["status"] == "FAIL"
        assert failure["exception_type"] == "RuntimeError"
        assert "HARNESS_HASH_MISMATCH" in failure["exception_message"]
        assert failure["execution_lock_sha256"] is None
        assert failure["execution_lock_sha_unavailable_reason"] == "FileNotFoundError"
        assert failure["smoke_trial_execution_count"] == failure["runtime_cycles_executed"] == failure["PlantCommit_count"] == failure["controller_qp_trial_count"] == 0
        assert failure["scientific_analysis_performed"] is False
    print("DELEGATE_PROTOCOL_CONTRACT_PASS")
    print("CHILD_CONFIG_CONSUMPTION_REGRESSION_PASS")
    print("RETRY4_EXECUTED_ACTION_CONTINUITY_REPLAY_PASS")
    print("EXECUTED_ACTION_CONTINUITY_CONTRACT_PASS")
    print("PASS_CERT_EXEC_IDENTITY_SMOKE_EXECUTED_ACTION_CONTINUITY_AUDIT_R6_CPU_FIXTURES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
