#!/usr/bin/env python3
"""CPU-only lock-pointer and failure-persistence regressions."""
from __future__ import annotations

import importlib.util
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


def main() -> int:
    validator = load("r3_validator", HERE / "validate_cert_exec_identity_repair_smoke_v1.py")
    runner = load("r3_runner", HERE / "run_cert_exec_identity_repair_smoke_v1.py")
    source = validator.RUNNER.read_text(encoding="utf-8")
    assert validator.active_lock_basename(source) == "SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY2_R3.json"
    assert validator.preflight_identity_is_caught(source)
    for obsolete in ("SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY1.json", "SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY1_R2.json"):
        simulated = source.replace("SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY2_R3.json", obsolete, 1)
        assert validator.active_lock_basename(simulated) != validator.R3_LOCK.name
    validator.validate_old_root()
    validator.validate_old_root(validator.ATTEMPT1_ROOT, validator.ATTEMPT1_ROOT_MANIFEST)
    validator.validate_retry_root_absent()
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        old = root / "old"
        old.mkdir()
        (old / "launcher.log").write_bytes((validator.OLD_ROOT / "launcher.log").read_bytes())
        validator.validate_old_root(old)
        (old / "launcher.log").write_bytes(b"changed")
        expect_error(lambda: validator.validate_old_root(old), "OLD_FAILED_ROOT_IDENTITY_MISMATCH")
        retry = root / "retry2"
        retry.mkdir()
        expect_error(lambda: validator.validate_retry_root_absent(retry), "RETRY2_ROOT_MUST_BE_ABSENT")
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
    print("PASS_CERT_EXEC_IDENTITY_SMOKE_LOCK_POINTER_R3_CPU_FIXTURES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
