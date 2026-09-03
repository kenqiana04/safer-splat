#!/usr/bin/env python3
"""No-real-run Q0 gate for the frozen BYPASS equivalence protocol."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys


EXPECTED_HEAD = "a8d7a3c9522583ad61dc9bc87585e41bb71a0f77"
EXPECTED_BLOBS = {
    "run.py": "361f09fc8f37e4713ea2fc8975d82d56cb9be46a",
    "cbf/cbf_utils.py": "7c6e1300b125cc0a2a950ac2835a1fbe3d0de113",
    "dynamics/systems.py": "e58ed65e60b17840201e571d7f23ce3816b83863",
    "reproduction/runtime/active_runtime_assurance_v2/active_runner.py": "64b747656b031881123c92587d1beca6e742be5e",
    "reproduction/runtime/active_runtime_assurance_v2/supervisor.py": "b4d5863199ccbe254c6d5b0061861f4f959f552d",
    "reproduction/runtime/active_runtime_assurance_v2/plant_commit.py": "fcb89f0f54000f6d181c574046b0105013f91156",
    "reproduction/runtime/active_runtime_assurance_v2/runtime_types.py": "cfce1d4fa111fdeb50a0c225b4451daeb9ed3672",
    "reproduction/runtime/active_runtime_assurance_v2/trace_writer.py": "f7d1c768a28d36ab1ef88614bd01c8722e9ea292",
}
EXPECTED_MAP = {
    "config.yml": (6933, "cd6ea45ad01553f0ce1531ad08cfaf8359e95041b39c77291d94e75f2d2f2f8e"),
    "dataparser_transforms.json": (312, "92a1af2f195be3b32e0422418aff40cbd426c1cf9d8f7d5da87629519f5a0f8e"),
    "nerfstudio_models/step-000029999.ckpt": (92344786, "ac14f5ced354c93f26cf92404540712eff65bd02554d9e9ed0332508e290382d"),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(checkout: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=checkout, text=True, capture_output=True, check=True).stdout.strip()


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--task-code", type=Path, required=True)
    parser.add_argument("--execution-lock", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checkout, task = args.checkout.resolve(), args.task_code.resolve()
    checks = []

    def check(name: str, passed: bool, evidence):
        checks.append({"check": name, "passed": bool(passed), "evidence": evidence})

    head = git(checkout, "rev-parse", "HEAD")
    execution_lock = json.loads(args.execution_lock.read_text(encoding="utf-8"))
    check("protocol_commit_is_checkout_head", head == execution_lock["protocol_commit_sha"], head)
    check("protocol_commit_parent_is_pr116", git(checkout, "rev-parse", "HEAD^") == EXPECTED_HEAD, git(checkout, "rev-parse", "HEAD^"))
    actual_blobs = {path: git(checkout, "rev-parse", f"HEAD:{path}") for path in EXPECTED_BLOBS}
    check("protected_source_blobs_exact", actual_blobs == EXPECTED_BLOBS, actual_blobs)
    task_files = {path.name: sha256(path) for path in task.glob("*") if path.is_file()}
    mismatched_tools = {name: expected for name, expected in execution_lock["task_tool_sha256"].items() if task_files.get(name) != expected}
    check("task_tool_hashes_exact", not mismatched_tools, mismatched_tools)
    map_root = checkout / "outputs/stonehenge/splatfacto/2024-09-11_100724"
    map_evidence = {}
    map_ok = True
    for relative, (size, expected_sha) in EXPECTED_MAP.items():
        path = map_root / relative
        actual = {"size": path.stat().st_size, "sha256": sha256(path)} if path.is_file() else None
        map_evidence[relative] = actual
        map_ok &= actual == {"size": size, "sha256": expected_sha}
    check("stonehenge_assets_exact", map_ok, map_evidence)
    compile_result = subprocess.run([sys.executable, "-B", "-m", "py_compile", *[str(p) for p in task.glob("*.py")]], text=True, capture_output=True)
    check("qa_scripts_compile", compile_result.returncode == 0, compile_result.stderr)
    unit_result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", str(task / "tests"), "-v"], cwd=checkout, text=True, capture_output=True)
    check("qa_tooling_unit_tests", unit_result.returncode == 0, unit_result.stdout + unit_result.stderr)
    runtime_result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "reproduction/runtime/active_runtime_assurance_v2/tests", "-v"], cwd=checkout, text=True, capture_output=True)
    check("pr116_runtime_suite", runtime_result.returncode == 0 and "Ran 76 tests" in (runtime_result.stdout + runtime_result.stderr), runtime_result.stdout + runtime_result.stderr)
    forbidden = []
    for path in task.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        if "RuntimeMode.ACTIVE_RUNTIME_ON" in text or "evaluation_oracle" in text:
            forbidden.append(path.name)
    check("no_active_or_oracle_execution_path", not forbidden, forbidden)
    protected_diff = git(checkout, "diff", f"{EXPECTED_HEAD}..HEAD", "--", "run.py", "cbf", "dynamics", "splat", "reproduction/runtime/active_runtime_assurance_v2")
    check("protected_diff_zero", protected_diff == "", protected_diff)
    result = {
        "schema": "BYPASS_EQUIVALENCE_Q0_PREFLIGHT_V2",
        "checks": checks,
        "passed_count": sum(item["passed"] for item in checks),
        "failed_count": sum(not item["passed"] for item in checks),
        "real_qa_trial_execution_count": 0,
        "verdict": "PASS_BYPASS_EQUIVALENCE_Q0_PREFLIGHT" if all(item["passed"] for item in checks) else "BLOCKED_BYPASS_EQUIVALENCE_Q0_PREFLIGHT",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["verdict"])
    return 0 if result["failed_count"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
