#!/usr/bin/env python3
"""CPU-only regressions for R1 child-root authority and early failure evidence."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile


def load_runner(task_dir: Path):
    path = task_dir / "run_active_runtime_v3_paired_validation_r1.py"
    spec = importlib.util.spec_from_file_location("_r1_runner_repair_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def expect_runtime_error(label: str, expected: str, fn) -> None:
    try:
        fn()
    except RuntimeError as exc:
        assert str(exc) == expected, f"{label}:{exc}"
    else:
        raise AssertionError(label + ":NOT_REJECTED")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task-dir", type=Path, required=True)
    args = ap.parse_args()
    runner = load_runner(args.task_dir.resolve())
    with tempfile.TemporaryDirectory(prefix="r1_child_root_repair_") as td:
        root = Path(td)
        checkout = root / "checkout"; checkout.mkdir()
        map_root = root / "map"; map_root.mkdir()
        expected = root / "expected_retry1"; expected.mkdir()
        wrong = root / "wrong"; wrong.mkdir()
        lock = root / "lock.json"; lock.write_text("{}\n", encoding="utf-8")

        original_default = runner.DEFAULT_RESULT_ROOT
        original_lock = runner.LOCK_PATH
        original_verify_lock = runner.verify_execution_lock
        original_git = runner.git
        original_run_one = runner.run_one
        original_order = runner.ORDER
        original_configure_smoke = runner.configure_smoke
        original_ensure_path_plumbing = runner.ensure_path_plumbing
        original_popen = runner.subprocess.Popen
        original_argv = sys.argv[:]
        original_token = os.environ.get("SAFER_SPLAT_R1_BATCH_CHILD_TOKEN")
        try:
            runner.DEFAULT_RESULT_ROOT = expected
            runner.LOCK_PATH = lock
            runner.verify_execution_lock = lambda *_args, **_kwargs: {}
            runner.git = lambda _checkout, *git_args, **_kwargs: (
                runner.BRANCH if git_args[:2] == ("branch", "--show-current") else "test-source-head"
            )

            token = "cpu-regression-token"
            marker = runner.write_batch_child_authorization(checkout, expected, token)
            reached: list[tuple[Path, Path, Path, int]] = []
            runner.run_one = lambda c, o, m, t: reached.append((c, o, m, t)) or 0
            os.environ["SAFER_SPLAT_R1_BATCH_CHILD_TOKEN"] = token
            sys.argv = ["runner", "--one", "66", "--batch-child", "--checkout", str(checkout),
                        "--output-dir", str(expected), "--map-source-root", str(map_root)]
            assert runner.main() == 0 and reached == [(checkout, expected, map_root, 66)]
            print("PASS_R1_BATCH_CHILD_EXISTING_ROOT_AUTHORIZATION")

            sys.argv = ["runner", "--one", "66", "--checkout", str(checkout),
                        "--output-dir", str(expected), "--map-source-root", str(map_root)]
            expect_runtime_error("UNAUTHORIZED_ONE", "FIRST_LAUNCH_RESULT_ROOT_ALREADY_EXISTS", runner.main)
            print("PASS_R1_UNAUTHORIZED_EXTERNAL_ONE_REJECTED")

            sys.argv = ["runner", "--one", "66", "--batch-child", "--checkout", str(checkout),
                        "--output-dir", str(wrong), "--map-source-root", str(map_root)]
            expect_runtime_error("WRONG_ROOT", "BATCH_CHILD_RESULT_ROOT_MISMATCH", runner.main)
            print("PASS_R1_BATCH_CHILD_WRONG_ROOT_REJECTED")

            runner.verify_fresh_result_root(expected, True)
            expect_runtime_error("FIRST_LAUNCH", "FIRST_LAUNCH_RESULT_ROOT_ALREADY_EXISTS",
                                 lambda: runner.verify_fresh_result_root(expected, False))
            runner.verify_explicit_resume_authority(checkout, expected)
            expect_runtime_error("WRONG_RESUME_ROOT", "RESUME_RESULT_ROOT_MISMATCH",
                                 lambda: runner.verify_explicit_resume_authority(checkout, wrong))
            print("PASS_R1_FIRST_LAUNCH_AND_EXPLICIT_RESUME_SEMANTICS")

            early_root = root / "early"; early_root.mkdir()
            stdout = early_root / "stdout.tmp"; stdout.write_text("child stdout\n", encoding="utf-8")
            stderr = early_root / "stderr.tmp"; stderr.write_text("child stderr\n", encoding="utf-8")
            raw, failure = runner.preserve_child_process_evidence(early_root, 66, 7, True, stdout, stderr)
            assert raw is None and failure == early_root / "parent_failures" / "trial_66"
            evidence = json.loads((failure / "EARLY_CHILD_FAILURE.json").read_text(encoding="utf-8"))
            assert evidence["process_exit_code"] == 7 and evidence["completed_scientific_trial_count"] == 0
            assert evidence["immutable_trial_evidence_lock_created"] is False
            assert not (early_root / "raw" / "trial_66").exists()
            assert not list(early_root.rglob("ACTIVE_V3_RAW_EVIDENCE_LOCK.json"))
            assert (failure / "stdout.log").read_text(encoding="utf-8") == "child stdout\n"
            assert (failure / "stderr.log").read_text(encoding="utf-8") == "child stderr\n"
            print("PASS_R1_PARENT_EARLY_CHILD_FAILURE_EVIDENCE")

            batch_root = root / "batch_early"; batch_root.mkdir()
            runner.DEFAULT_RESULT_ROOT = batch_root
            runner.ORDER = (66,)
            runner.ensure_path_plumbing = lambda *_args, **_kwargs: {}
            class FakeSmoke:
                @staticmethod
                def verify_source_and_map(*_args, **_kwargs): return None
                @staticmethod
                def gpu_pid_released(_pid): return True
            runner.configure_smoke = lambda *_args, **_kwargs: (FakeSmoke(), {"environment": {"python": sys.executable}})
            class FakeProcess:
                pid = os.getpid()
                def wait(self): return 7
            def fake_popen(_command, *, env, stdout, stderr, text):
                stdout.write("early batch child stdout\n")
                stderr.write("early batch child stderr\n")
                return FakeProcess()
            runner.subprocess.Popen = fake_popen
            code = runner.run_batch(checkout, batch_root, map_root)
            assert code == 7
            batch_failure = batch_root / "parent_failures" / "trial_66"
            assert batch_failure.is_dir() and not (batch_root / "raw" / "trial_66").exists()
            summary = json.loads((batch_root / "ACTIVE_V3_R1_COLLECTION_INTEGRITY_SUMMARY.json").read_text(encoding="utf-8"))
            assert summary["completed_trials"] == 0
            assert not list(batch_root.rglob("ACTIVE_V3_RAW_EVIDENCE_LOCK.json"))
            assert not (batch_root / runner.BATCH_AUTHORIZATION_NAME).exists()
            print("PASS_R1_PARENT_EARLY_CHILD_FAILURE_NONZERO_HARD_STOP")

            normal_root = root / "normal"; raw_dir = normal_root / "raw" / "trial_66"; raw_dir.mkdir(parents=True)
            stdout = normal_root / "stdout.tmp"; stdout.write_text("normal stdout\n", encoding="utf-8")
            stderr = normal_root / "stderr.tmp"; stderr.write_text("normal stderr\n", encoding="utf-8")
            raw, failure = runner.preserve_child_process_evidence(normal_root, 66, 0, True, stdout, stderr)
            assert raw == raw_dir and failure is None
            assert (raw_dir / "process_exit_code.txt").read_text(encoding="utf-8").strip() == "0"
            assert (raw_dir / "gpu_released.txt").read_text(encoding="utf-8").strip() == "true"
            assert (raw_dir / "stdout.log").is_file() and (raw_dir / "stderr.log").is_file()
            assert not (normal_root / "parent_failures").exists()
            print("PASS_R1_NORMAL_CHILD_RAW_PATH_UNCHANGED")

            launcher = (args.task_dir / "start_v3_paired_validation_r1_tmux.sh").read_text(encoding="utf-8")
            assert "analyze_active_runtime" not in launcher
            assert str(runner.OLD_FAILED_RESULT_ROOT) not in launcher
            assert "retry1_20260915" in launcher
            print("PASS_R1_NO_ANALYZER_AND_OLD_ROOT_NOT_REUSED")
            marker.unlink()
        finally:
            runner.DEFAULT_RESULT_ROOT = original_default
            runner.LOCK_PATH = original_lock
            runner.verify_execution_lock = original_verify_lock
            runner.git = original_git
            runner.run_one = original_run_one
            runner.ORDER = original_order
            runner.configure_smoke = original_configure_smoke
            runner.ensure_path_plumbing = original_ensure_path_plumbing
            runner.subprocess.Popen = original_popen
            sys.argv = original_argv
            if original_token is None:
                os.environ.pop("SAFER_SPLAT_R1_BATCH_CHILD_TOKEN", None)
            else:
                os.environ["SAFER_SPLAT_R1_BATCH_CHILD_TOKEN"] = original_token
    print("PASS_R1_CHILD_ROOT_AND_PARENT_PARTIAL_EVIDENCE_REGRESSIONS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
