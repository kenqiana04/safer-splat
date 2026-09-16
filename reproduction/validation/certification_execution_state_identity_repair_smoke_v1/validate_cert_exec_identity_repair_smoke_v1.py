#!/usr/bin/env python3
"""CPU-only validator for the retry4 delegate-protocol projection R5."""
from __future__ import annotations

import argparse
import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
PROTOCOL = TASK_DIR / "SMOKE_REPAIR_V1_PROTOCOL.json"
ORIGINAL_LOCK = TASK_DIR / "SMOKE_REPAIR_V1_EXECUTION_LOCK.json"
RETRY1_LOCK = TASK_DIR / "SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY1.json"
R2_LOCK = TASK_DIR / "SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY1_R2.json"
R3_LOCK = TASK_DIR / "SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY2_R3.json"
R4_LOCK = TASK_DIR / "SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY3_R4.json"
R5_LOCK = TASK_DIR / "SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY4_R5.json"
RUNNER = TASK_DIR / "run_cert_exec_identity_repair_smoke_v1.py"
VALIDATOR = TASK_DIR / "validate_cert_exec_identity_repair_smoke_v1.py"
LAUNCHER = TASK_DIR / "launch_cert_exec_identity_repair_smoke_v1.sh"
MONITOR = TASK_DIR / "monitor_cert_exec_identity_repair_smoke_v1.py"

BRANCH = "repair-cert-exec-identity-smoke-delegate-protocol-projection-r5"
BASE = "e51f30ee3ca58ce15c9c90642260e76f34b83143"
IMPLEMENTATION_HEAD = "546598a70e12fa99f9153f1927d0542ca27862b4"
OLD_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_20260916")
ATTEMPT1_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry1_20260916")
ATTEMPT2_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry2_20260916")
ATTEMPT3_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry3_20260916")
RETRY_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry4_20260916")
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
ATTEMPT1_LOG_SHA = "a1a647cd52426ebce38459c3e87522864266374842b824fb2d7075d10804910f"
ATTEMPT1_ROOT_MANIFEST = {
    "file_count": 1,
    "files": [{"path": "launcher.log", "size": 1355, "sha256": ATTEMPT1_LOG_SHA}],
    "semantic_root_sha256": "60f7e2ff29fea94ea5daf63bff1578b02afc14901e161623ea51b4455a221379",
}
ATTEMPT2_ROOT_MANIFEST = {
    "file_count": 2,
    "files": [
        {"path": "gpu_preflight_failure.json", "size": 5175, "sha256": "16f2ebd7d40aa93d118b03311903749889509c27516825fa2dda267706e1aa79"},
        {"path": "launcher.log", "size": 304, "sha256": "b82fc2409280b8c545914dc8664ddf8ea9291f213831f277ac7ffa1385439762"},
    ],
    "semantic_root_sha256": "0261351b99b4ab7425cd81bf1200d25bd518cd2c7295ac34955dd6b0b84b27f5",
}
ATTEMPT3_ROOT_MANIFEST = {
    "file_count": 8,
    "files": [
        {"path": "SMOKE_REPAIR_V1_COLLECTION_SUMMARY.json", "size": 744, "sha256": "a0b56baa3b8ac5494844d5f11c44599255af4e4836af9466a521195c700c7f85"},
        {"path": "launcher.log", "size": 655, "sha256": "b8bfd94a3be10812bb9528baa55eb398456a22ec1a239f44c2f10d587760d0dd"},
        {"path": "raw/gpu_preflight.json", "size": 2030, "sha256": "bb9473c716fab705766e2358d070f559ec23efa96c800e5469f5c2a5bebf747a"},
        {"path": "raw/trial_15/gpu_released.txt", "size": 5, "sha256": "a17fcf0a2f50e2d495e4f90ce263410edc183add6c62699a2facbccf60410f74"},
        {"path": "raw/trial_15/process_exit_code.txt", "size": 2, "sha256": "53c234e5e8472b6ac51c1ae1cab3fe06fad053beb8ebfd8977b010655bfdd3c3"},
        {"path": "raw/trial_15/stderr.log", "size": 0, "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
        {"path": "raw/trial_15/stdout.log", "size": 111, "sha256": "55904d5882f9458afae8a3f91b096c09b4cf816f00a6ff21e92a450ca830cf0c"},
        {"path": "raw/trial_15/trial_summary.json", "size": 1765, "sha256": "6ac573fc4c80debffe52c99186b89501b6479d4ea1abfc2d17f1c10cb350a806"},
    ],
    "semantic_root_sha256": "0313cdb555dcb8f0cdabdf8832441595777b832b4dc4bb51963d30ea12c68d12",
}
MAP_ROOT = Path("/disk1/zlab/datasets/safer_splat_gdrive/outputs/stonehenge/splatfacto/2024-09-11_100724")
MAP_FILES = {
    "config.yml": (6933, "cd6ea45ad01553f0ce1531ad08cfaf8359e95041b39c77291d94e75f2d2f2f8e"),
    "dataparser_transforms.json": (312, "92a1af2f195be3b32e0422418aff40cbd426c1cf9d8f7d5da87629519f5a0f8e"),
    "nerfstudio_models/step-000029999.ckpt": (92344786, "ac14f5ced354c93f26cf92404540712eff65bd02554d9e9ed0332508e290382d"),
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


def validate_old_root(root: Path = OLD_ROOT, expected: dict[str, object] = OLD_ROOT_MANIFEST) -> None:
    if not root.is_dir():
        raise RuntimeError("OLD_FAILED_ROOT_MISSING")
    if not (root / "launcher.log").is_file():
        raise RuntimeError("OLD_FAILED_ROOT_LAUNCHER_LOG_MISSING")
    if manifest(root) != expected:
        raise RuntimeError("OLD_FAILED_ROOT_IDENTITY_MISMATCH")


def validate_retry_root_absent(root: Path = RETRY_ROOT) -> None:
    if root.exists():
        raise RuntimeError("RETRY4_ROOT_MUST_BE_ABSENT")


def validate_attempt3_outcome() -> None:
    validate_old_root(ATTEMPT3_ROOT, ATTEMPT3_ROOT_MANIFEST)
    preflight = json.loads((ATTEMPT3_ROOT / "raw/gpu_preflight.json").read_text(encoding="utf-8"))
    trial = json.loads((ATTEMPT3_ROOT / "raw/trial_15/trial_summary.json").read_text(encoding="utf-8"))
    collection = json.loads((ATTEMPT3_ROOT / "SMOKE_REPAIR_V1_COLLECTION_SUMMARY.json").read_text(encoding="utf-8"))
    if preflight.get("status") != "PASS" or preflight.get("runtime_cycles_executed") != 0 or preflight.get("plant_commit_count") != 0:
        raise RuntimeError("ATTEMPT3_GPU_PREFLIGHT_EVIDENCE_MISMATCH")
    if (trial.get("hard_blocker") != "BLOCKED_ACTIVE_RUNTIME_SMOKE_V3_BY_CORE_RUNTIME:KeyError:'seed'"
            or trial.get("process_exit_code") != 2 or trial.get("startup_status") != "NOT_RUN"
            or any(trial.get(k) != 0 for k in ("completed_cycles", "plant_commit_count", "trace_record_count"))
            or (ATTEMPT3_ROOT / "raw/trial_15/process_exit_code.txt").read_text().strip() != "2"
            or (ATTEMPT3_ROOT / "raw/trial_15/gpu_released.txt").read_text().strip() != "true"):
        raise RuntimeError("ATTEMPT3_TRIAL15_EVIDENCE_MISMATCH")
    if (collection.get("scientific_analysis_performed") is not False
            or collection.get("completed_cycles") != 0 or collection.get("plant_commits") != 0):
        raise RuntimeError("ATTEMPT3_COLLECTION_EVIDENCE_MISMATCH")


def load_runner():
    spec = importlib.util.spec_from_file_location("_r5_runner_validation", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("RUNNER_IMPORT_UNAVAILABLE")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def delegate_protocol_access_contract(source: str) -> tuple[set[str], set[str]]:
    tree = ast.parse(source)
    paths: set[str] = set()
    dynamic: set[str] = set()
    for function in (n for n in tree.body if isinstance(n, ast.FunctionDef)):
        if function.name not in {"run_one", "run_preflight", "run_batch", "verify_environment", "verify_source_and_map"}:
            continue
        for node in ast.walk(function):
            if isinstance(node, ast.Subscript):
                keys = []
                cursor = node
                while isinstance(cursor, ast.Subscript):
                    if isinstance(cursor.slice, ast.Constant) and isinstance(cursor.slice.value, str):
                        keys.append(cursor.slice.value)
                    else:
                        keys.append("*")
                    cursor = cursor.value
                if isinstance(cursor, ast.Name) and cursor.id == "protocol":
                    path = ".".join(reversed(keys))
                    paths.add(path)
                    if "*" in keys:
                        dynamic.add(path)
            elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                  and isinstance(node.func.value, ast.Name) and node.func.value.id == "protocol"
                  and node.func.attr == "get"):
                if not node.args or not isinstance(node.args[0], ast.Constant) or not isinstance(node.args[0].value, str):
                    dynamic.add("protocol.get(*)")
                else:
                    paths.add(node.args[0].value)
    return paths, dynamic


def delegate_projection_contract_sha256(paths: list[str]) -> str:
    return semantic({
        "historical_v3_protocol_sha256": HISTORICAL_SHA,
        "repair_protocol_sha256": PROTOCOL_SHA,
        "historical_delegate_protocol_access_paths": paths,
        "allowed_execution_overrides": [
            "seed", "maximum_completed_cycles_per_trial", "trial_ids", "trial_order",
            "serial_execution", "separate_process_per_trial", "environment",
        ],
        "map_authority_source": "REPAIR_PROTOCOL_ONLY",
        "runtime_base_source": "HISTORICAL_V3_PROTOCOL_ONLY",
    })


def projected_path_exists(projected: dict[str, object], path: str) -> bool:
    value: object = projected
    for key in path.split("."):
        if key == "*":
            return True
        if not isinstance(value, dict) or key not in value:
            return False
        value = value[key]
    return True


def validate_local_bindings(root: Path) -> None:
    for rel in ("outputs/stonehenge", "data/stonehenge"):
        local = root / rel
        main = Path("/disk1/zlab/projects/safer-splat") / rel
        if not local.is_symlink() or local.resolve(strict=True) != main.resolve(strict=True):
            raise RuntimeError("LOCAL_STONEHENGE_BINDING_MISMATCH:" + rel)
        if subprocess.run(["git", "-C", str(root), "check-ignore", "-q", rel]).returncode != 0:
            raise RuntimeError("LOCAL_STONEHENGE_BINDING_NOT_IGNORED:" + rel)
    if (root / "outputs/stonehenge/splatfacto/2024-09-11_100724").resolve(strict=True) != MAP_ROOT.resolve(strict=True):
        raise RuntimeError("LOCAL_MAP_RESOLUTION_MISMATCH")
    for rel, (size, digest) in MAP_FILES.items():
        path = MAP_ROOT / rel
        if path.stat().st_size != size or sha256(path) != digest:
            raise RuntimeError("FROZEN_MAP_ARTIFACT_MISMATCH:" + rel)


def active_lock_basename(source: str) -> str | None:
    for node in ast.parse(source).body:
        if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == "LOCK_PATH" for target in node.targets):
            value = node.value
            if (isinstance(value, ast.BinOp) and isinstance(value.op, ast.Div)
                    and isinstance(value.left, ast.Name) and value.left.id == "TASK_DIR"
                    and isinstance(value.right, ast.Constant) and isinstance(value.right.value, str)):
                return value.right.value
    return None


def preflight_identity_is_caught(source: str) -> bool:
    function = next((node for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == "gpu_preflight"), None)
    if function is None:
        return False
    for node in function.body:
        if not isinstance(node, ast.Try):
            continue
        names = {call.func.id for statement in node.body for call in ast.walk(statement)
                 if isinstance(call, ast.Call) and isinstance(call.func, ast.Name)}
        if {"verify_static_identity", "_load_delegate"}.issubset(names) and any(isinstance(handler.type, ast.Name) and handler.type.id == "Exception" for handler in node.handlers):
            return True
    return False


def check_launcher_text(text: str) -> list[str]:
    failures: list[str] = []
    required = (
        'CHECKOUT="/disk1/zlab/v3_repair_worktrees/safer-splat-cert-exec-identity-smoke-delegate-protocol-projection-r5"',
        'ACTIVE_BRANCH="repair-cert-exec-identity-smoke-delegate-protocol-projection-r5"',
        'RESULT_ROOT="/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry4_20260916"',
        'OLD_FAILED_ROOT="/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_20260916"',
        'OLD_FAILED_ROOT_MISSING', 'OLD_FAILED_ROOT_LAUNCHER_LOG_MISSING', 'OLD_FAILED_ROOT_IDENTITY_MISMATCH',
        'ATTEMPT1_FAILED_ROOT="/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry1_20260916"',
        'ATTEMPT1_FAILED_ROOT_MISSING', 'ATTEMPT1_LAUNCHER_LOG_MISSING', 'ATTEMPT1_ROOT_IDENTITY_MISMATCH',
        'ATTEMPT2_FAILED_ROOT="/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry2_20260916"',
        'ATTEMPT2_FAILED_ROOT_MISSING', 'ATTEMPT2_EVIDENCE_FILE_MISSING', 'ATTEMPT2_ROOT_IDENTITY_MISMATCH',
        'ATTEMPT3_FAILED_ROOT="/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry3_20260916"',
        'ATTEMPT3_FAILED_ROOT_MISSING', 'ATTEMPT3_EVIDENCE_FILE_MISSING', 'ATTEMPT3_ROOT_IDENTITY_MISMATCH',
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
        'ACTIVE_BRANCH="repair-cert-exec-identity-smoke-lock-pointer-r3"',
        'ACTIVE_BRANCH="repair-cert-exec-identity-smoke-retry3-rollover-r4"',
    )
    for marker in forbidden:
        if marker in text:
            failures.append("FORBIDDEN:" + marker)
    if text.count("--gpu-preflight") != 1:
        failures.append("GPU_PREFLIGHT_COUNT_INVALID")
    if text.find("--gpu-preflight") > text.find("--batch"):
        failures.append("GPU_BEFORE_BATCH_ORDER_INVALID")
    for line in text.splitlines():
        if any(root_name in line for root_name in ("OLD_FAILED_ROOT", "ATTEMPT1_FAILED_ROOT", "ATTEMPT2_FAILED_ROOT", "ATTEMPT3_FAILED_ROOT")) and any(token in line for token in ("rm ", "mv ", "chmod ", "touch ", ">>", "> ")):
            failures.append("OLD_ROOT_WRITE_OPERATION")
    pre = text.split('if [[ "${1:-}" == "--prelaunch-check-only" ]]', 1)[-1].split("fi", 1)[0]
    if any(token in pre for token in ("mkdir", "tmux", "--gpu-preflight", "--batch")):
        failures.append("PRELAUNCH_SIDE_EFFECT_OR_GPU")
    if 'TASK="$CHECKOUT/reproduction/validation/certification_execution_state_identity_repair_smoke_v1"' not in text:
        failures.append("TASK_NOT_DERIVED_FROM_CHECKOUT")
    return failures


def need(condition: bool, name: str, passed: list[str], failed: list[str]) -> None:
    (passed if condition else failed).append(name)


def validate_delegate_contract(root: Path, passed: list[str], failed: list[str]) -> list[str]:
    runner = load_runner()
    repair = runner.protocol()
    base = runner.load_runtime_base_config(root)
    projected = runner.delegate_runtime_protocol(root)
    delegate = runner._load_delegate(root)
    need(delegate.read_protocol is not runner.protocol and delegate.read_protocol() == projected,
         "DELEGATE_READ_PROTOCOL_CLOSURE_NOT_REPAIR_SCHEMA", passed, failed)
    overrides = (
        "seed", "maximum_completed_cycles_per_trial", "trial_ids", "trial_order",
        "serial_execution", "separate_process_per_trial",
    )
    expected = deepcopy(base)
    for key in overrides:
        expected[key] = deepcopy(repair["cohort"][key])
    expected["environment"] = deepcopy(repair["environment"])
    need(projected == expected, "NON_OVERRIDDEN_HISTORICAL_FIELDS_EXACT", passed, failed)
    need(projected["seed"] == 0 and projected["maximum_completed_cycles_per_trial"] == 500
         and projected["trial_ids"] == projected["trial_order"] == [15, 45, 75],
         "PROJECTED_SEED_MAX_COHORT", passed, failed)
    need(isinstance(projected.get("dynamics"), dict)
         and projected["dynamics"]["dt"] == base["dynamics"]["dt"]
         and projected["environment"] == repair["environment"],
         "PROJECTED_DYNAMICS_ENVIRONMENT", passed, failed)
    source = (root / "reproduction/smoke/active_runtime_smoke_v3/run_active_runtime_smoke_v3.py").read_text(encoding="utf-8")
    paths, dynamic = delegate_protocol_access_contract(source)
    tops = {path.split(".", 1)[0] for path in paths}
    frozen_tops = {
        "seed", "environment", "dynamics", "maximum_completed_cycles_per_trial",
        "map_relative_path", "map_artifacts", "map_identity",
    }
    need(tops == frozen_tops and dynamic <= {"environment.*"}
         and {"dynamics.dt", "environment.python", "environment.*"} <= paths
         and all(projected_path_exists(projected, path) for path in paths)
         and all(key in projected["environment"] for key in
                 ("CUDA_VISIBLE_DEVICES", "PYTHONHASHSEED", "PYTHONNOUSERSITE",
                  "PYTHONDONTWRITEBYTECODE", "CUBLAS_WORKSPACE_CONFIG", "python")),
         "HISTORICAL_V3_PROTOCOL_ACCESS_CONTRACT_COMPLETE", passed, failed)
    import numpy as np
    np.random.seed(projected["seed"])
    _ = projected["dynamics"]["dt"]
    _ = range(projected["maximum_completed_cycles_per_trial"])
    _ = projected["environment"]["CUDA_VISIBLE_DEVICES"]
    passed.append("CHILD_CONFIG_CONSUMPTION_REGRESSION_PASS")
    need("module.read_protocol = lambda: delegate_runtime_protocol(checkout)" in RUNNER.read_text(encoding="utf-8")
         and "repair_frozen = protocol()" in RUNNER.read_text(encoding="utf-8")
         and "verify_map_artifacts(repair_frozen)" in RUNNER.read_text(encoding="utf-8"),
         "REPAIR_MAP_AUTHORITY_SEPARATE_FROM_DELEGATE_VIEW", passed, failed)
    return sorted(paths)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--prelaunch-check-only", action="store_true")
    parser.add_argument("--pre-freeze", action="store_true")
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

    need(git(root, "branch", "--show-current") == BRANCH, "EXACT_R5_BRANCH", passed, failed)
    need(subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", BASE, "HEAD"]).returncode == 0, "R4_ANCESTRY", passed, failed)
    need(subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", IMPLEMENTATION_HEAD, "HEAD"]).returncode == 0, "IMPLEMENTATION_ANCESTRY", passed, failed)
    need(sha256(PROTOCOL) == PROTOCOL_SHA, "ORIGINAL_PROTOCOL_UNCHANGED", passed, failed)
    need(sha256(ORIGINAL_LOCK) == ORIGINAL_LOCK_SHA, "ORIGINAL_LOCK_UNCHANGED", passed, failed)
    try:
        validate_old_root()
        validate_old_root(ATTEMPT1_ROOT, ATTEMPT1_ROOT_MANIFEST)
        validate_old_root(ATTEMPT2_ROOT, ATTEMPT2_ROOT_MANIFEST)
        validate_attempt3_outcome()
        passed.append("FOUR_OLD_ROOTS_IMMUTABLE_AND_ATTEMPT3_TYPED")
    except RuntimeError as exc:
        failed.append(str(exc))
    try:
        validate_retry_root_absent()
        passed.append("ACTUAL_RETRY_ROOT_ABSENT")
    except RuntimeError as exc:
        failed.append(str(exc))
    try:
        validate_local_bindings(root)
        passed.append("LOCAL_BINDINGS_IGNORED_MAP_HASHES_PASS")
    except (RuntimeError, OSError) as exc:
        failed.append(str(exc))
    launcher_failures = check_launcher_text(launcher_text)
    need(not launcher_failures, "LAUNCHER_R5_GUARDS", passed, failed)
    need(sha256(historical_path) == HISTORICAL_SHA, "HISTORICAL_V3_BASE_CONFIG_SHA", passed, failed)
    need(all(isinstance(historical.get(k), dict) for k in ("controller", "certification", "dynamics", "deadline_profile")), "HISTORICAL_REQUIRED_MAPPINGS", passed, failed)
    need(historical["controller"]["controller_radius"] == 0.015 and historical["certification"]["certification_margin"] == 0.0 and historical["certification"]["rho_seg"] == 0.0, "HISTORICAL_GEOMETRY", passed, failed)
    need("load_runtime_base_config" in runner_text and "runtime_base_config" in runner_text and "build_repaired_v3_stack(checkout_arg, output_dir, trial_id, runtime_base_config" in runner_text, "BASE_CONFIG_SEPARATION", passed, failed)
    need("BRANCH = \"repair-cert-exec-identity-smoke-delegate-protocol-projection-r5\"" in runner_text and "TRIALS = (15, 45, 75)" in runner_text and "10, 50, 90" not in runner_text and "200" not in runner_text, "R5_RUNNER_FROZEN_COHORT", passed, failed)
    need(active_lock_basename(runner_text) == R5_LOCK.name, "ACTIVE_LOCK_PATH_EXACT_R5", passed, failed)
    need(preflight_identity_is_caught(runner_text), "IDENTITY_EXCEPTION_CAUGHT_BY_GPU_PREFLIGHT", passed, failed)
    need("GPU_PREFLIGHT_DIAGNOSTIC_ROOT_INVALID" in runner_text and "historical_v3_base_config_mappings" in runner_text, "CPU_PREFLIGHT_DIAGNOSTIC_REUSE", passed, failed)
    need("gpu_preflight_failure.json" in runner_text and "scientific_analysis_performed" in runner_text, "GPU_FAILURE_PERSISTENCE", passed, failed)
    try:
        delegate_access_paths = validate_delegate_contract(root, passed, failed)
    except (RuntimeError, KeyError, TypeError, ValueError) as exc:
        failed.append("DELEGATE_PROTOCOL_CONTRACT:" + str(exc))
        delegate_access_paths = []
    need(retry1["original_protocol_sha256"] == PROTOCOL_SHA and retry1["original_execution_lock_sha256"] == ORIGINAL_LOCK_SHA, "RETRY1_LOCK_PRESERVED", passed, failed)
    need(retry1["trial_ids"] == [15, 45, 75] and retry1["maximum_completed_cycles_per_trial"] == 500 and retry1["failure_classification"] == "PRE_TRIAL_GPU_PREFLIGHT_BASE_CONFIG_PLUMBING_FAILURE", "RETRY1_SEMANTICS", passed, failed)
    need(protocol["scientific_boundaries"]["frozen_scientific_decision_remains"] == "FAIL_V3_HARD_SAFETY_GATE", "SCIENTIFIC_DECISION_FROZEN", passed, failed)
    need("cert_exec_identity_repair_smoke_v1_retry4_20260916" in monitor_text, "MONITOR_RETRY4_ROOT", passed, failed)
    need(all(marker in validator_text for marker in ("OLD_FAILED_ROOT_MISSING", "OLD_FAILED_ROOT_LAUNCHER_LOG_MISSING", "OLD_FAILED_ROOT_IDENTITY_MISMATCH", "RETRY4_ROOT_MUST_BE_ABSENT", "--prelaunch-check-only")), "VALIDATOR_TYPED_GUARDS", passed, failed)
    ast.parse(runner_text); ast.parse(validator_text); ast.parse(monitor_text)
    protected = git(root, "diff", "--name-only", BASE, "--", "cbf", "dynamics", "splat", "run.py", "reproduction/runtime", "reproduction/smoke/active_runtime_smoke_v3", "reproduction/validation/certification_execution_state_identity_repair_v1")
    need(not protected, "PROTECTED_DIFF_ZERO", passed, failed)

    need(sha256(R2_LOCK) == "745fd8326affc230ea8fc629edc12e36be618f5b23a9de2a8199f18c1777e8ec", "SUPERSEDED_R2_LOCK_PRESERVED", passed, failed)
    need(sha256(RETRY1_LOCK) == "b26bba30304e641ce7b4eca9fe4d367b0cf90b65d262545a3c5085d8e9b7ff8e", "SUPERSEDED_RETRY1_LOCK_PRESERVED", passed, failed)
    need(sha256(R3_LOCK) == "f3a6171b6add8da2c6ab9cd2eae699357ac6d095ca8308b349b985185ddc2348", "SUPERSEDED_R3_LOCK_PRESERVED", passed, failed)
    need(sha256(R4_LOCK) == "fdc00c63b967b5920b250edeabebb225c1509fea1cd8455de9f168e796b4e3ab", "SUPERSEDED_R4_LOCK_PRESERVED", passed, failed)
    if R5_LOCK.is_file():
        r5 = json.loads(R5_LOCK.read_text(encoding="utf-8"))
        need(r5.get("schema") == "CERT_EXECUTION_IDENTITY_REPAIR_SMOKE_EXECUTION_LOCK_RETRY4_R5_V1", "R5_LOCK_SCHEMA", passed, failed)
        if args.pre_freeze and r5.get("freeze_stage") == "TASK_LOCAL_PLACEHOLDER_BEFORE_CODE_COMMIT":
            need(r5.get("protocol_sha256") == PROTOCOL_SHA, "R5_TEMPLATE_PROTOCOL_SHA", passed, failed)
            passed.append("R5_LOCK_PENDING_CODE_COMMIT")
        else:
            need(r5.get("branch") == BRANCH and r5.get("worktree") == str(root) and r5.get("base_head") == BASE, "R5_LOCK_IDENTITY", passed, failed)
            code_commit = r5.get("harness_repair_commit")
            need(isinstance(code_commit, str) and len(code_commit) == 40 and subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", code_commit, "HEAD"]).returncode == 0, "R5_LOCK_CODE_COMMIT_ANCESTOR", passed, failed)
            need(r5.get("protocol_sha256") == PROTOCOL_SHA and r5.get("historical_v3_base_config_sha256") == HISTORICAL_SHA
                 and r5.get("retry_result_root") == str(RETRY_ROOT), "R5_LOCK_PROTOCOL_AND_ROOT", passed, failed)
            need(r5.get("attempt0_root_manifest") == OLD_ROOT_MANIFEST
                 and r5.get("attempt1_root_manifest") == ATTEMPT1_ROOT_MANIFEST
                 and r5.get("attempt2_root_manifest") == ATTEMPT2_ROOT_MANIFEST
                 and r5.get("attempt3_root_manifest") == ATTEMPT3_ROOT_MANIFEST, "R5_LOCK_IMMUTABLE_ROOTS", passed, failed)
            need(r5.get("attempt3_failure_classification") == "TRIAL15_PRE_RUNTIME_DELEGATE_PROTOCOL_SCHEMA_MISMATCH_SEED", "R5_LOCK_RETRY3_CLASSIFICATION", passed, failed)
            need(r5.get("delegate_protocol_access_paths") == delegate_access_paths
                 and r5.get("delegate_projection_allowed_overrides") ==
                 ["seed", "maximum_completed_cycles_per_trial", "trial_ids", "trial_order",
                  "serial_execution", "separate_process_per_trial", "environment"]
                 and r5.get("delegate_projection_contract_sha256") == delegate_projection_contract_sha256(delegate_access_paths),
                 "R5_LOCK_DELEGATE_COMPATIBILITY_CONTRACT", passed, failed)
            hashes = r5.get("harness_sha256", {})
            names = (RUNNER.name, LAUNCHER.name, VALIDATOR.name, MONITOR.name)
            need(set(hashes) == set(names) and all(sha256(TASK_DIR / name) == hashes[name] for name in names), "R5_LOCK_HARNESS_HASHES", passed, failed)
            geometry = r5.get("geometry", {})
            need(r5.get("trial_ids") == [15, 45, 75] and r5.get("trial_order") == [15, 45, 75] and r5.get("maximum_completed_cycles_per_trial") == 500 and r5.get("seed") == 0, "R5_LOCK_COHORT", passed, failed)
            need(geometry.get("hard_radius_q") == 0.015 and geometry.get("runtime_margin_q") == 0.0 and geometry.get("rho_seg_q") == 0.0 and geometry.get("epsilon") is None and geometry.get("historical_diagnostic_runtime_authority") is False, "R5_LOCK_GEOMETRY", passed, failed)
    elif args.pre_freeze:
        passed.append("R5_LOCK_PENDING_CODE_COMMIT")
    else:
        failed.append("R5_EXECUTION_LOCK_MISSING")

    result = {"schema": "CERT_EXEC_IDENTITY_SMOKE_DELEGATE_PROTOCOL_PROJECTION_R5_VALIDATION_V1", "status": "PASS" if not failed else "FAIL", "passed_checks": passed, "failed_checks": failed, "delegate_protocol_access_paths": delegate_access_paths, "delegate_projection_contract_sha256": delegate_projection_contract_sha256(delegate_access_paths), "gpu_count": 0, "tmux_start_count": 0, "smoke_trial_count": 0, "cycle_count": 0, "PlantCommit_count": 0}
    print(json.dumps(result, sort_keys=True))
    if failed:
        print("FAILED:" + ",".join(failed), file=sys.stderr)
        return 2
    print("DELEGATE_PROTOCOL_CONTRACT_PASS")
    print("CHILD_CONFIG_CONSUMPTION_REGRESSION_PASS")
    print("PASS_CERT_EXEC_IDENTITY_SMOKE_DELEGATE_PROTOCOL_PROJECTION_R5_VALIDATION")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
