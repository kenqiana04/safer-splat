#!/usr/bin/env python3
"""Freeze the implemented V2R1 source identities after CPU tests pass."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[5]
RUNTIME = REPO / "reproduction/runtime/active_runtime_assurance_v2"
DESIGN = REPO / "reproduction/design/active_runtime_trace_commit_atomicity_v2r1"

IMPLEMENTED = [
    "runtime_types.py",
    "active_runner.py",
    "active_cycle.py",
    "trace_writer.py",
    "commit_transaction.py",
    "tests/test_trace_commit_atomicity_v2r1.py",
    "tests/test_existing_runtime_regression.py",
]
PROTECTED = [
    "plant_commit.py",
    "backup_token_store.py",
    "supervisor.py",
    "alternative_provider.py",
    "authority_registry.py",
    "deadline_runtime.py",
    "start_admission.py",
    "diagnostic_r0.py",
    "l1_runtime.py",
    "primary_proposal_adapter.py",
    "c0_admission.py",
    "l2_runtime.py",
    "l3_runtime.py",
]
DESIGN_ARTIFACTS = [
    "TRACE_COMMIT_ARCHITECTURE_DECISION_V2R1.json",
    "TRACE_COMMIT_IMPLEMENTATION_CHANGE_MANIFEST_V2R1.csv",
    "TRACE_COMMIT_FAULT_MATRIX_V2R1.csv",
    "TRACE_COMMIT_CONSISTENCY_INVARIANTS_V2R1.json",
    "TRACE_COMMIT_IMPLEMENTATION_TEST_PLAN_V2R1.json",
    "TRACE_FINALIZATION_RETRY_CONTRACT_V2R1.json",
    "TRACE_COMMIT_BYPASS_IMPACT_V2R1.json",
    "TRACE_COMMIT_ORACLE_COMPATIBILITY_V2R1.json",
    "NO_SILENT_UNTRACED_COMMIT_PROPERTY_V2R1.md",
    "TRACE_COMMIT_CONSISTENCY_PROPERTY_V2R1.md",
    "TRACE_COMMIT_AUTHORITY_OWNERSHIP_V2R1.json",
    "report/REPORT_DESIGN_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1.md",
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def entry(path: Path) -> dict[str, object]:
    rel = path.relative_to(REPO).as_posix()
    blob = subprocess.check_output(["git", "rev-parse", f"HEAD:{rel}"], cwd=REPO, text=True).strip()
    return {"path": rel, "sha256": sha(path), "git_blob_sha1": blob, "size": path.stat().st_size}


def main() -> None:
    payload = {
        "schema": "TRACE_COMMIT_IMPLEMENTATION_V2R1_SOURCE_FREEZE",
        "upstream_pr": 128,
        "upstream_head": "d7d2703f305d43661cf24bb818d846a092a67066",
        "implementation_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "architecture": "OPTION_B_SOFTWARE_TRANSACTION_STATE_MACHINE",
        "capability": "MEMORY_ONLY_CONSISTENCY",
        "runtime_correction_quota_after_freeze": 0,
        "tests_passed_before_freeze": {"new": 28, "runtime_total": 161},
        "implemented_files": [entry(RUNTIME / item) for item in IMPLEMENTED],
        "protected_runtime_files": [entry(RUNTIME / item) for item in PROTECTED],
        "design_artifacts": [entry(DESIGN / item) for item in DESIGN_ARTIFACTS],
        "commit_journal_absent": not (RUNTIME / "commit_journal.py").exists(),
        "real_execution_counts": {
            "active": 0,
            "gpu": 0,
            "smoke": 0,
            "oracle": 0,
            "official100": 0,
            "real_bypass": 0,
        },
    }
    (HERE / "TRACE_COMMIT_IMPLEMENTATION_V2R1_SOURCE_FREEZE.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    main()
