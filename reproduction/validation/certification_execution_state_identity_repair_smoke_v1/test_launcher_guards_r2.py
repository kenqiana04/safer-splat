#!/usr/bin/env python3
"""CPU-only fixture regressions for the R2 launcher guard semantics."""
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("r2_validator", HERE / "validate_cert_exec_identity_repair_smoke_v1.py")
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def expect_error(fn, token: str) -> None:
    try:
        fn()
    except RuntimeError as exc:
        assert token in str(exc), (token, exc)
    else:
        raise AssertionError(f"expected {token}")


def main() -> int:
    module.validate_old_root()
    module.validate_retry_root_absent()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "old"
        root.mkdir()
        (root / "launcher.log").write_bytes((module.OLD_ROOT / "launcher.log").read_bytes())
        module.validate_old_root(root)
        expect_error(lambda: module.validate_old_root(Path(tmp) / "missing"), "OLD_FAILED_ROOT_MISSING")
        (root / "launcher.log").write_bytes(b"mutated")
        expect_error(lambda: module.validate_old_root(root), "OLD_FAILED_ROOT_IDENTITY_MISMATCH")
        retry = Path(tmp) / "retry"
        retry.mkdir()
        expect_error(lambda: module.validate_retry_root_absent(retry), "RETRY1_ROOT_MUST_BE_ABSENT")
    text = module.LAUNCHER.read_text(encoding="utf-8")
    assert not module.check_launcher_text(text)
    assert module.check_launcher_text(text.replace("safer-splat-cert-exec-identity-smoke-launcher-guards-r2", "wrong-worktree"))
    assert module.check_launcher_text(text.replace("repair-cert-exec-identity-smoke-launcher-guards-r2", "freeze-cert-exec-identity-repair-smoke-protocol-v1"))
    assert "load_runtime_base_config" in module.RUNNER.read_text(encoding="utf-8")
    print("PASS_CERT_EXEC_IDENTITY_SMOKE_LAUNCHER_GUARDS_R2_FIXTURES")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
