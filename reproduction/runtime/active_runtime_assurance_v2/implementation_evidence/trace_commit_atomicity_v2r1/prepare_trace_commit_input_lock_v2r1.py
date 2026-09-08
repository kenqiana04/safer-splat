from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


EVIDENCE = Path(__file__).resolve().parent
ROOT = EVIDENCE.parents[4]
UPSTREAM = "d7d2703f305d43661cf24bb818d846a092a67066"


def sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def blob(path: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"{UPSTREAM}:{path}"], cwd=ROOT, text=True).strip()


design_root = "reproduction/design/active_runtime_trace_commit_atomicity_v2r1"
design = [
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
runtime_root = "reproduction/runtime/active_runtime_assurance_v2"
allowed = ["runtime_types.py", "active_runner.py", "active_cycle.py", "trace_writer.py"]
protected = [
    "plant_commit.py", "backup_token_store.py", "supervisor.py", "alternative_provider.py",
    "authority_registry.py", "deadline_runtime.py", "start_admission.py", "diagnostic_r0.py",
    "l1_runtime.py", "primary_proposal_adapter.py", "c0_admission.py", "l2_runtime.py", "l3_runtime.py",
]
external_protected = ["run.py"]
lock = {
    "schema": "TRACE_COMMIT_IMPLEMENTATION_V2R1_INPUT_LOCK",
    "task_type": "OPTION_B_MEMORY_ONLY_TRACE_COMMIT_IMPLEMENTATION",
    "pr128": {
        "number": 128,
        "state": "OPEN",
        "draft": True,
        "title": "[Draft] Design active runtime trace/commit consistency V2R1",
        "branch": "design-active-runtime-trace-commit-atomicity-v2r1",
        "head": UPSTREAM,
        "base_branch": "revalidate-active-runtime-contract-conformance-v2-post-r2",
        "base_sha": "72215ffb1b0a0bc9e7cc94155117ac8624ed0aa6",
    },
    "selected_architecture": "OPTION_B_SOFTWARE_TRANSACTION_STATE_MACHINE",
    "capability": "MEMORY_ONLY_CONSISTENCY",
    "journal": "JOURNAL_NOT_REQUIRED_FOR_CURRENT_CONTRACT",
    "bypass_revalidation_required": True,
    "design_artifact_sha256": {name: sha(f"{design_root}/{name}") for name in design},
    "allowed_runtime_blob_sha1": {name: blob(f"{runtime_root}/{name}") for name in allowed},
    "protected_runtime_blob_sha1": {name: blob(f"{runtime_root}/{name}") for name in protected},
    "external_protected_blob_sha1": {name: blob(name) for name in external_protected},
    "upstream_evidence_sha256": {
        "pr127_report": sha("reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/report/REPORT_REVALIDATE_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2_POST_R2.md"),
        "pr127_failure_register": sha("reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/POST_R2_CONFORMANCE_FAILURE_REGISTER_V2.csv"),
        "pr127_trace_faults": sha("reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/POST_R2_TRACE_FAULT_SEMANTICS_V2.json"),
        "pr119_summary": sha("reproduction/validation/execute_refrozen_bypass_equivalence_v2r1/BYPASS_EQUIVALENCE_V2R1_SUMMARY.json"),
        "pr119_execution_lock": sha("reproduction/validation/execute_refrozen_bypass_equivalence_v2r1/BYPASS_EQUIVALENCE_V2R1_EXECUTION_LOCK.json"),
    },
    "execution_counts": {"real_active": 0, "gpu": 0, "smoke": 0, "oracle": 0, "official100": 0, "real_bypass": 0},
}
(EVIDENCE / "TRACE_COMMIT_IMPLEMENTATION_V2R1_INPUT_LOCK.json").write_text(
    json.dumps(lock, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
)
