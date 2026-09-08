#!/usr/bin/env python3
"""CPU-only implementation precheck; this is not targeted final validation."""

from __future__ import annotations

import ast
import hashlib
import json
import subprocess
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[5]
RUNTIME = REPO / "reproduction/runtime/active_runtime_assurance_v2"
UPSTREAM = "d7d2703f305d43661cf24bb818d846a092a67066"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def method_ast(source: str, name: str) -> str:
    node = next(item for item in ast.walk(ast.parse(source)) if isinstance(item, ast.FunctionDef) and item.name == name)
    return ast.dump(node, include_attributes=False)


def main() -> None:
    checks: list[dict[str, object]] = []

    def check(identifier: str, condition: bool, detail: str) -> None:
        checks.append({"id": identifier, "passed": bool(condition), "detail": detail})

    input_lock = json.loads((HERE / "TRACE_COMMIT_IMPLEMENTATION_V2R1_INPUT_LOCK.json").read_text(encoding="utf-8"))
    freeze = json.loads((HERE / "TRACE_COMMIT_IMPLEMENTATION_V2R1_SOURCE_FREEZE.json").read_text(encoding="utf-8"))
    diff_audit = json.loads((HERE / "TRACE_COMMIT_IMPLEMENTATION_V2R1_DIFF_AUDIT.json").read_text(encoding="utf-8"))
    tests = json.loads((HERE / "TRACE_COMMIT_IMPLEMENTATION_TEST_RESULTS_V2R1.json").read_text(encoding="utf-8"))
    manifest = json.loads((HERE / "TRACE_COMMIT_IMPLEMENTATION_TEST_MANIFEST_V2R1.json").read_text(encoding="utf-8"))
    model = json.loads((HERE / "TRACE_COMMIT_IMPLEMENTATION_MODEL_V2R1.json").read_text(encoding="utf-8"))
    bypass = json.loads((HERE / "TRACE_COMMIT_BYPASS_IMPACT_IMPLEMENTATION_V2R1.json").read_text(encoding="utf-8"))
    handoff = json.loads((HERE / "downstream_handoff.json").read_text(encoding="utf-8"))

    try:
        live = json.loads(subprocess.check_output(["gh", "pr", "view", "128", "--repo", "kenqiana04/safer-splat", "--json", "state,isDraft,title,headRefName,headRefOid,baseRefName"], cwd=REPO, text=True))
    except Exception:
        live = {}
    check("PC-01", live.get("state") == "OPEN" and live.get("isDraft") is True, "PR #128 is an open draft")
    check("PC-02", live.get("title") == "[Draft] Design active runtime trace/commit consistency V2R1", "PR #128 title exact")
    check("PC-03", live.get("headRefName") == "design-active-runtime-trace-commit-atomicity-v2r1" and live.get("headRefOid") == UPSTREAM, "PR #128 branch/head exact")
    check("PC-04", live.get("baseRefName") == "revalidate-active-runtime-contract-conformance-v2-post-r2", "PR #128 base exact")
    check("PC-05", input_lock["selected_architecture"] == "OPTION_B_SOFTWARE_TRANSACTION_STATE_MACHINE", "Option B exact")
    check("PC-06", input_lock["journal"] == "JOURNAL_NOT_REQUIRED_FOR_CURRENT_CONTRACT", "journal decision exact")
    check("PC-07", diff_audit["changed_runtime_subset_allowed"], "runtime diff is within the frozen manifest")
    check("PC-08", diff_audit["protected_blob_diff_count"] == 0, "protected diff is zero")
    check("PC-09", not (RUNTIME / "commit_journal.py").exists(), "commit_journal.py absent")

    types = (RUNTIME / "runtime_types.py").read_text(encoding="utf-8")
    transaction = (RUNTIME / "commit_transaction.py").read_text(encoding="utf-8")
    runner = (RUNTIME / "active_runner.py").read_text(encoding="utf-8")
    coordinator = (RUNTIME / "active_cycle.py").read_text(encoding="utf-8")
    writer = (RUNTIME / "trace_writer.py").read_text(encoding="utf-8")
    check("PC-10", all(name in types for name in ("CommitTransactionState", "PlantOutcome", "TokenMutationStatus", "TraceStatus", "EvidenceStatus")), "typed transaction enums implemented")
    check("PC-11", "class CommitTransactionResult" in types and "@dataclass(frozen=True)" in types, "immutable CommitTransactionResult implemented")
    check("PC-12", "PLANT_OUTCOME_UNRESOLVED" in transaction, "unresolved plant outcome implemented")
    check("PC-13", "COMMITTED_TOKEN_INCOMPLETE" in transaction, "token incomplete implemented")
    check("PC-14", "COMMITTED_TRACE_INCOMPLETE" in transaction, "trace incomplete implemented")
    check("PC-15", "NO_ACTION_TRACE_INCOMPLETE" in transaction, "no-action trace incomplete implemented")
    check("PC-16", "class ActiveCommitTransaction" in transaction, "transaction component exists")
    check("PC-17", "self._active_commit_transaction.execute" in runner, "ActiveRunner delegates ACTIVE sequencing")
    check("PC-18", subprocess.check_output(["git", "rev-parse", f"HEAD:reproduction/runtime/active_runtime_assurance_v2/supervisor.py"], cwd=REPO, text=True).strip() == input_lock["protected_runtime_blob_sha1"]["supervisor.py"], "Supervisor exact")
    check("PC-19", subprocess.check_output(["git", "rev-parse", f"HEAD:reproduction/runtime/active_runtime_assurance_v2/plant_commit.py"], cwd=REPO, text=True).strip() == input_lock["protected_runtime_blob_sha1"]["plant_commit.py"], "PlantCommit exact")
    check("PC-20", subprocess.check_output(["git", "rev-parse", f"HEAD:reproduction/runtime/active_runtime_assurance_v2/backup_token_store.py"], cwd=REPO, text=True).strip() == input_lock["protected_runtime_blob_sha1"]["backup_token_store.py"], "BackupTokenStore exact")
    f02 = json.loads((HERE / "TRACE_F02_IMPLEMENTATION_CLOSURE_V2R1.json").read_text(encoding="utf-8"))
    f03 = json.loads((HERE / "TRACE_F03_IMPLEMENTATION_CLOSURE_V2R1.json").read_text(encoding="utf-8"))
    check("PC-21", f02["receipt_preserved"], "TRACE-F02 receipt preserved")
    check("PC-22", f02["post_state_preserved"], "TRACE-F02 post-state preserved")
    check("PC-23", f02["session"] == "EVIDENCE_INCOMPLETE", "TRACE-F02 session non-ready")
    check("PC-24", writer.index("self._persist(current_lines, candidate_lock)") < writer.index("self._lock = candidate_lock"), "lock publication follows persistence")
    check("PC-25", "self._records_frozen" in writer and "TRACE_RECORD_SET_FROZEN" in writer, "append frozen after finalize attempt")
    check("PC-26", f03["session"] == "FINALIZATION_FAILED", "TRACE-F03 finalization failure state")
    check("PC-27", f03["retry_same_content"] and f03["retry_identity_mismatch"] == "RECOVERY_REQUIRED", "idempotent retry contract implemented")
    check("PC-28", "self.plant_commit.commit" in transaction and transaction.count("self.plant_commit.commit") == 1, "no automatic plant retry path")
    check("PC-29", "rollback" not in transaction.lower(), "no fake rollback")
    check("PC-30", bypass["BYPASS_REVALIDATION_REQUIRED"] is True, "fresh BYPASS revalidation required")
    upstream_runner = subprocess.check_output(["git", "show", f"{UPSTREAM}:reproduction/runtime/active_runtime_assurance_v2/active_runner.py"], cwd=REPO, text=True)
    check("PC-31", method_ast(runner, "commit_bypass") == method_ast(upstream_runner, "commit_bypass"), "commit_bypass execution body preserved")
    check("PC-32", manifest["implemented_task_test_count"] >= 24, ">=24 implementation tests")
    check("PC-33", model["counterexample_count"] == 0, "model counterexamples zero")
    check("PC-34", tests["new_tests"]["passed"] and tests["runtime_suite"]["passed"] and tests["post_r2_source_independent"]["passed"], "applicable CPU regressions pass")
    check("PC-35", all(value == 0 for value in freeze["real_execution_counts"].values()), "all real execution counts zero")
    check("PC-36", handoff["only_authorized_next_task"] == "VALIDATE_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1", "next task exact")
    check("PC-37", all(sha(REPO / item["path"]) == item["sha256"] for item in freeze["implemented_files"]), "implemented source still matches source freeze")
    check("PC-38", all(sha(REPO / item["path"]) == item["sha256"] for item in freeze["protected_runtime_files"]), "protected source still matches source freeze")
    check("PC-39", "if session.status != TrialSessionStatus.READY" in coordinator, "run_cycle has READY-only guard")
    check("PC-40", input_lock["capability"] == "MEMORY_ONLY_CONSISTENCY", "no durability overclaim")

    passed = sum(1 for item in checks if item["passed"])
    result = {
        "schema": "TRACE_COMMIT_ATOMICITY_IMPLEMENTATION_PRECHECK_V2R1",
        "check_count": len(checks),
        "passed_count": passed,
        "failed_count": len(checks) - passed,
        "checks": checks,
        "verdict": "PASS_TRACE_COMMIT_ATOMICITY_V2R1_IMPLEMENTATION_PRECHECK" if passed == len(checks) else "FAIL_TRACE_COMMIT_ATOMICITY_V2R1_IMPLEMENTATION_PRECHECK",
        "is_targeted_final_validation": False,
    }
    (HERE / "validation_precheck.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    if passed != len(checks):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
