#!/usr/bin/env python3
"""Freeze the implementation payload immediately before the full validation suite."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


EVIDENCE = Path(__file__).resolve().parent
PACKAGE = EVIDENCE.parent
CORE = (
    "authority_registry.py", "runtime_types.py", "start_admission.py", "diagnostic_r0.py",
    "l1_runtime.py", "primary_proposal_adapter.py", "c0_admission.py", "l2_runtime.py",
    "l3_runtime.py", "alternative_provider.py", "backup_token_store.py", "terminal_runtime.py",
    "deadline_runtime.py", "supervisor.py", "plant_commit.py", "trace_writer.py", "active_runner.py",
)
EXTRA = (
    "implementation_evidence/RUNTIME_TRANSITION_IMPLEMENTATION_MAP_V2.csv",
    "implementation_evidence/ACTIVE_RUNTIME_IMPLEMENTATION_INVARIANTS_V2.json",
    "implementation_evidence/test_manifest.json",
    "validate_active_runtime_assurance_v2.py",
    "model_check_active_runtime_implementation_v2.py",
)


def identity(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    return {"path": path.relative_to(PACKAGE).as_posix(), "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def main() -> None:
    files = [identity(PACKAGE / path) for path in (*CORE, *EXTRA)]
    lock = {
        "schema": "ACTIVE_RUNTIME_IMPLEMENTATION_EXECUTION_LOCK_V2",
        "lock_point": "AFTER_MAJOR_IMPLEMENTATION_BEFORE_FULL_TEST_SUITE",
        "upstream_design_identity": {
            "pr": 115,
            "head": "44111d32031409338058e5da2f7e7a1f8d873323",
            "branch": "design-active-runtime-assurance-implementation-v2"
        },
        "core_module_count": 17,
        "locked_file_count": len(files),
        "files": files,
        "allowed_post_lock_change": "TASK_LOCAL_IMPLEMENTATION_BUG_CORRECTION_ONLY",
        "frozen_method_semantics_change_authority": False,
        "rollout_authority": False,
        "gpu_authority": False
    }
    material = json.dumps(lock, sort_keys=True, separators=(",", ":")).encode("utf-8")
    lock["payload_sha256"] = hashlib.sha256(material).hexdigest()
    (EVIDENCE / "ACTIVE_RUNTIME_IMPLEMENTATION_EXECUTION_LOCK.json").write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(lock["payload_sha256"])


if __name__ == "__main__":
    main()
