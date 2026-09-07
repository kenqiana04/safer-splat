"""Freeze PR #121 and pre-edit runtime identities before implementation."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path


EVIDENCE = Path(__file__).resolve().parent
PACKAGE = EVIDENCE.parent
REPO = PACKAGE.parents[2]
DESIGN = REPO / "reproduction" / "design" / "active_runtime_public_cycle_composition_v2"
PR120 = REPO / "reproduction" / "validation" / "active_runtime_contract_conformance_v2"

DESIGN_FILES = (
    "PUBLIC_CYCLE_IMPLEMENTATION_MANIFEST_V2.csv",
    "PUBLIC_CYCLE_RUNTIME_CHANGE_MATRIX_V2.csv",
    "PUBLIC_CYCLE_COMPOSITION_CONTRACT_V2.md",
    "PUBLIC_CYCLE_API_V2.json",
    "SUPERVISOR_ROUTING_AUTHORITY_V2.md",
    "EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json",
    "PUBLIC_ACTIVE_CYCLE_PHASES_V2.json",
    "ACTIVE_CYCLE_CONTEXT_SCHEMA_V2.json",
    "ACTIVE_CYCLE_RESULT_SCHEMA_V2.json",
    "PUBLIC_CYCLE_EVENT_SCHEMA_V2.json",
    "DEADLINE_STAGE_ADMISSION_INTERFACE_V2.md",
    "PRIMARY_CYCLE_INTEGRATION_V2.md",
    "ALTERNATIVE_CYCLE_INTEGRATION_V2.md",
    "BACKUP_CYCLE_INTEGRATION_V2.md",
    "TERMINAL_CYCLE_INTEGRATION_V2.md",
    "PUBLIC_CYCLE_TRACE_CONTRACT_V2.md",
    "FIRST_AND_SUBSEQUENT_CYCLE_SEMANTICS_V2.md",
    "PUBLIC_CYCLE_EXCEPTION_ROUTING_V2.json",
    "BYPASS_EVIDENCE_PRESERVATION_V2.md",
    "PUBLIC_CYCLE_COMPOSITION_INVARIANTS_V2.json",
    "PUBLIC_CYCLE_DESIGN_SCENARIOS_V2.json",
    "POST_COMPOSITION_VALIDATION_LADDER_V2.md",
)

RUNTIME_MODULES = (
    "authority_registry.py", "runtime_types.py", "start_admission.py", "diagnostic_r0.py",
    "l1_runtime.py", "primary_proposal_adapter.py", "c0_admission.py", "l2_runtime.py",
    "l3_runtime.py", "alternative_provider.py", "backup_token_store.py", "terminal_runtime.py",
    "deadline_runtime.py", "supervisor.py", "plant_commit.py", "trace_writer.py", "active_runner.py",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    rel = path.relative_to(REPO).as_posix()
    return subprocess.run(["git", "hash-object", rel], cwd=REPO, check=True, text=True, capture_output=True).stdout.strip()


def identity(path: Path) -> dict[str, object]:
    return {
        "path": path.relative_to(REPO).as_posix(),
        "sha256": sha256(path),
        "git_blob_sha1": git_blob(path),
        "size": path.stat().st_size,
    }


def method_identity(path: Path, class_name: str, method_name: str) -> dict[str, str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and item.name == method_name:
                    segment = ast.get_source_segment(source, item) or ""
                    dump = ast.dump(item, annotate_fields=True, include_attributes=False)
                    return {
                        "source_sha256": hashlib.sha256(segment.encode("utf-8")).hexdigest(),
                        "ast_sha256": hashlib.sha256(dump.encode("utf-8")).hexdigest(),
                    }
    raise RuntimeError(f"method not found: {class_name}.{method_name}")


def main() -> None:
    supervisor = PACKAGE / "supervisor.py"
    lock = {
        "schema": "PUBLIC_CYCLE_IMPLEMENTATION_INPUT_LOCK_V2",
        "task_type": "PUBLIC_CYCLE_IMPLEMENTATION_CPU_ONLY_NO_ROLLOUT",
        "direct_upstream": {
            "repository": "kenqiana04/safer-splat",
            "pr": 121,
            "state": "OPEN_DRAFT",
            "title": "[Draft] Design active runtime public cycle composition V2",
            "branch": "design-active-runtime-public-cycle-composition-v2",
            "head": "4148e671128444d357ea33f6e5c15d0dd2928411",
            "base": "validate-active-runtime-contract-conformance-v2",
            "base_sha": "6c5c59dd083dc83661e56c4ddd3e62fa12497652",
        },
        "pr120_blocker": {
            "status": "BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP",
            "gap": "MISSING_PUBLIC_ACTIVE_CYCLE_ORCHESTRATION",
            "artifact": identity(PR120 / "FINAL_DECISION.json"),
        },
        "pr107_transition_table": identity(REPO / "reproduction" / "specification" / "method_logic_closure_v2" / "STATE_TRANSITION_TABLE_V2.csv"),
        "pr121_design_artifacts": [identity(DESIGN / name) for name in DESIGN_FILES],
        "pre_edit_runtime_modules": [identity(PACKAGE / name) for name in RUNTIME_MODULES],
        "must_remain_unchanged": [identity(PACKAGE / name) for name in ("active_runner.py", "plant_commit.py", "backup_token_store.py", "terminal_runtime.py", "trace_writer.py")],
        "supervisor_method_identities": {
            name: method_identity(supervisor, "Supervisor", name)
            for name in ("bypass_decision", "arbitrate", "certify_candidate")
        },
        "baseline_regression": {"suite": "PR116_RUNTIME_CPU_UNIT_TESTS", "tests": 78, "status": "PASS"},
        "authorizations": {
            "runtime_files": ["active_cycle.py", "runtime_types.py", "supervisor.py"],
            "real_active_rollout": False,
            "gpu": False,
            "smoke": False,
            "scientific_oracle": False,
            "official100": False,
            "real_bypass_pair": False,
        },
    }
    target = EVIDENCE / "PUBLIC_CYCLE_IMPLEMENTATION_INPUT_LOCK.json"
    target.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(target)
    print(sha256(target))


if __name__ == "__main__":
    main()
