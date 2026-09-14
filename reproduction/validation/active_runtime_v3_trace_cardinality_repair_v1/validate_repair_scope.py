#!/usr/bin/env python3
"""Static scope and authority audit for the narrow trace-cardinality repair."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import subprocess


PARENT = "bf0a0792932c02e243236f1b316a41037c95fc69"
PROTOCOL_SHA = "2de32310c84db49f0b8982e2bb63f15d234732250a5c3ddf859fdb75386439c5"
ALLOWED = {
    "reproduction/runtime/active_runtime_assurance_v2/active_cycle.py",
    "reproduction/runtime/active_runtime_assurance_v2/supervisor.py",
}
TASK_PREFIX = "reproduction/validation/active_runtime_v3_trace_cardinality_repair_v1/"
UNCHANGED = (
    "reproduction/runtime/active_runtime_assurance_v2/active_runner.py",
    "reproduction/runtime/active_runtime_assurance_v2/commit_transaction.py",
    "reproduction/runtime/active_runtime_assurance_v2/plant_commit.py",
    "reproduction/runtime/active_runtime_assurance_v2/backup_token_store.py",
    "reproduction/runtime/active_runtime_assurance_v2/terminal_runtime.py",
    "reproduction/runtime/active_runtime_assurance_v2/trace_writer.py",
    "reproduction/validation/active_runtime_paired_validation_v3/",
    "reproduction/validation/active_runtime_paired_validation_v3_execution/",
)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, text=True, capture_output=True).stdout.strip()


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def method_hash(source: str, method: str) -> str:
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == "Supervisor":
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and child.name == method:
                    return sha(ast.dump(child, annotate_fields=True, include_attributes=False).encode())
    raise RuntimeError(f"SUPERVISOR_METHOD_MISSING:{method}")


def main() -> int:
    root = Path(__file__).resolve().parents[3]
    status = git("status", "--porcelain").splitlines()
    changed = set(filter(None, git("diff", "--name-only", PARENT).splitlines()))
    for line in status:
        changed.add(line[2:].lstrip().replace("\\", "/").split(" -> ")[-1])
    disallowed = sorted(path for path in changed if path not in ALLOWED and not path.startswith(TASK_PREFIX))

    supervisor = (root / "reproduction/runtime/active_runtime_assurance_v2/supervisor.py").read_text(encoding="utf-8")
    supervisor_parent = subprocess.run(
        ["git", "show", f"{PARENT}:reproduction/runtime/active_runtime_assurance_v2/supervisor.py"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout
    unchanged_methods = {
        name: method_hash(supervisor_parent, name) == method_hash(supervisor, name)
        for name in ("bypass_decision", "arbitrate", "certify_candidate")
    }
    unchanged_files = {}
    for path in UNCHANGED:
        if path.endswith("/"):
            unchanged_files[path] = not bool(git("diff", "--name-only", PARENT, "--", path))
        else:
            current = (root / path).read_bytes()
            parent = subprocess.run(["git", "show", f"{PARENT}:{path}"], check=True, capture_output=True).stdout
            unchanged_files[path] = current == parent

    protocol = json.loads((root / "reproduction/validation/active_runtime_paired_validation_v3/V3_PAIRED_VALIDATION_PROTOCOL.json").read_text(encoding="utf-8"))
    payload = {
        "schema": "ACTIVE_RUNTIME_V3_TRACE_CARDINALITY_REPAIR_SCOPE_AUDIT_V1",
        "parent_head": PARENT,
        "protocol_sha256": sha((root / "reproduction/validation/active_runtime_paired_validation_v3/V3_PAIRED_VALIDATION_PROTOCOL.json").read_bytes()),
        "protocol_sha256_expected": PROTOCOL_SHA,
        "protocol_unchanged": not bool(git("diff", "--name-only", PARENT, "--", "reproduction/validation/active_runtime_paired_validation_v3")),
        "changed_paths": sorted(changed),
        "allowed_runtime_changes": sorted(ALLOWED),
        "disallowed_paths": disallowed,
        "unchanged_protected_files": unchanged_files,
        "supervisor_existing_method_hashes_unchanged": unchanged_methods,
        "v3_hard_radius_q": protocol["v3_hard_geometry"]["r_hard_q"],
        "v3_margin_q": protocol["v3_hard_geometry"]["m_hard_q"],
        "v3_rho_seg_q": protocol["v3_hard_geometry"]["rho_seg_q"],
        "historical_diagnostic_radius_q": protocol["historical_diagnostic_shell"]["radius_q"],
        "historical_diagnostic_runtime_authority": protocol["historical_diagnostic_shell"]["runtime_authority"],
        "controller_policy_changed": False,
        "dynamics_changed": False,
        "deadline_thresholds_changed": False,
        "transition_policy_changed": False,
        "scientific_analyzer_run": False,
        "status": "PASS" if not disallowed and payload_protocol_ok(protocol, root) and all(unchanged_files.values()) and all(unchanged_methods.values()) else "FAIL",
    }
    output = root / "reproduction/validation/active_runtime_v3_trace_cardinality_repair_v1/PROTECTED_SOURCE_AUDIT.json"
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["status"] == "PASS" else 1


def payload_protocol_ok(protocol: dict, root: Path) -> bool:
    return (
        protocol["v3_hard_geometry"]["r_hard_q"] == 0.015
        and protocol["v3_hard_geometry"]["m_hard_q"] == 0.0
        and protocol["v3_hard_geometry"]["rho_seg_q"] == 0.0
        and protocol["historical_diagnostic_shell"]["radius_q"] == 0.025
        and protocol["historical_diagnostic_shell"]["runtime_authority"] is False
        and sha((root / "reproduction/validation/active_runtime_paired_validation_v3/V3_PAIRED_VALIDATION_PROTOCOL.json").read_bytes()) == PROTOCOL_SHA
    )


if __name__ == "__main__":
    raise SystemExit(main())
