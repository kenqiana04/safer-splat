#!/usr/bin/env python3
"""Model-check the frozen implementation against memory-level invariants."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path(__file__).resolve().parents[5]
RUNTIME = REPO / "reproduction/runtime/active_runtime_assurance_v2"
sys.path.insert(0, str(REPO))

from reproduction.runtime.active_runtime_assurance_v2.commit_transaction import ActiveCommitTransaction
from reproduction.runtime.active_runtime_assurance_v2.runtime_types import (
    EvidenceStatus,
    FinalizationStatus,
    TrialSessionStatus,
)
from reproduction.runtime.active_runtime_assurance_v2.tests.public_cycle_test_support import build_public_cycle, start_and_run
from reproduction.runtime.active_runtime_assurance_v2.tests.test_trace_commit_atomicity_v2r1 import (
    AlwaysFailPersistTraceWriter,
    RaisingPlant,
    RaisingTokenStore,
    RaisingTraceWriter,
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inject_writer(system, writer) -> None:
    runner = system["runner"]
    runner.trace_writer = writer
    runner._active_commit_transaction = ActiveCommitTransaction(runner.plant_commit, runner.token_store, writer)


def main() -> None:
    checks: list[dict[str, object]] = []
    counterexamples: list[dict[str, str]] = []

    def check(identifier: str, condition: bool, detail: str) -> None:
        checks.append({"id": identifier, "passed": bool(condition), "detail": detail})
        if not condition:
            counterexamples.append({"id": identifier, "detail": detail})

    normal = build_public_cycle()
    _, normal_result = start_and_run(normal)
    tx = normal_result.commit_transaction_result
    check("MC-01", tx is not None and tx.committed is True and tx.evidence_status == EvidenceStatus.COMPLETE, "confirmed normal commit is complete")
    check("MC-02", normal["coordinator"].session.status == TrialSessionStatus.READY, "only complete evidence advances a normal session")

    f02 = build_public_cycle()
    writer = RaisingTraceWriter(f02["state"].trial_id)
    inject_writer(f02, writer)
    _, f02_result = start_and_run(f02)
    tx = f02_result.commit_transaction_result
    check("MC-03", tx.committed is True and tx.commit_receipt is not None and tx.post_state is not None, "TRACE-F02 retains receipt and post-state")
    check("MC-04", tx.evidence_status == EvidenceStatus.COMMITTED_TRACE_INCOMPLETE and f02["coordinator"].session.status != TrialSessionStatus.READY, "committed trace-incomplete cannot remain READY")

    token = build_public_cycle()
    token_store = RaisingTokenStore()
    token["runner"].token_store = token_store
    token["runner"]._active_commit_transaction = ActiveCommitTransaction(token["plant"], token_store, token["trace_writer"])
    token["coordinator"].backup_token_store = token_store
    _, token_result = start_and_run(token)
    check("MC-05", token_result.commit_transaction_result.evidence_status == EvidenceStatus.COMMITTED_TOKEN_INCOMPLETE, "token failure is typed")
    check("MC-06", token["coordinator"].session.status != TrialSessionStatus.READY, "token-incomplete cannot remain READY")

    unresolved = build_public_cycle()
    plant = RaisingPlant()
    unresolved["runner"].plant_commit = plant
    unresolved["runner"]._active_commit_transaction = ActiveCommitTransaction(plant, unresolved["token_store"], unresolved["trace_writer"])
    _, unresolved_result = start_and_run(unresolved)
    check("MC-07", unresolved_result.commit_transaction_result.evidence_status == EvidenceStatus.PLANT_OUTCOME_UNRESOLVED, "plant exception is unresolved rather than false")
    check("MC-08", plant.commit_count == 1 and unresolved["coordinator"].session.status == TrialSessionStatus.RECOVERY_REQUIRED, "unresolved plant is not retried and requires recovery")

    boundary = build_public_cycle({"proposal": "FAIL"})
    _, boundary_result = start_and_run(boundary)
    check("MC-09", boundary["plant"].commit_count == 0 and boundary_result.committed is False and boundary_result.next_state is None, "boundary has no plant or fake state")

    f03 = build_public_cycle()
    final_writer = AlwaysFailPersistTraceWriter(f03["state"].trial_id)
    inject_writer(f03, final_writer)
    start_and_run(f03)
    final_result = f03["coordinator"].finalize_trial()
    check("MC-10", final_result.status == FinalizationStatus.FINALIZATION_INCOMPLETE and final_writer._lock is None, "lock is not published before persistence")
    check("MC-11", f03["coordinator"].session.status == TrialSessionStatus.FINALIZATION_FAILED, "finalize failure is non-ready")
    check("MC-12", final_writer.frozen_trace_sha256 == final_result.content_hash, "frozen retry identity is retained")

    source = (RUNTIME / "commit_transaction.py").read_text(encoding="utf-8")
    runner_source = (RUNTIME / "active_runner.py").read_text(encoding="utf-8")
    check("MC-13", "rollback" not in source.lower(), "no false rollback path exists")
    check("MC-14", "commit_journal" not in source and not (RUNTIME / "commit_journal.py").exists(), "no journal or WAL creep")
    check("MC-15", "ActiveCommitTransaction" in runner_source and "commit_bypass" in runner_source, "ACTIVE delegates while BYPASS remains separate")

    freeze = json.loads((HERE / "TRACE_COMMIT_IMPLEMENTATION_V2R1_SOURCE_FREEZE.json").read_text(encoding="utf-8"))
    protected_ok = all(sha(REPO / item["path"]) == item["sha256"] for item in freeze["protected_runtime_files"])
    check("MC-16", protected_ok, "all protected owners match the source freeze")

    model = {
        "schema": "TRACE_COMMIT_IMPLEMENTATION_MODEL_V2R1",
        "model_scope": "ACTUAL_IMPLEMENTED_MEMORY_LEVEL_CLASSES",
        "check_count": len(checks),
        "checks": checks,
        "counterexample_count": len(counterexamples),
        "verdict": "PASS" if not counterexamples else "FAIL",
        "physical_atomicity_claim": False,
        "crash_restart_recovery_claim": False,
    }
    (HERE / "TRACE_COMMIT_IMPLEMENTATION_MODEL_V2R1.json").write_text(json.dumps(model, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (HERE / "TRACE_COMMIT_IMPLEMENTATION_COUNTEREXAMPLES_V2R1.json").write_text(
        json.dumps({"schema": "TRACE_COMMIT_IMPLEMENTATION_COUNTEREXAMPLES_V2R1", "count": len(counterexamples), "counterexamples": counterexamples}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    if counterexamples:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
