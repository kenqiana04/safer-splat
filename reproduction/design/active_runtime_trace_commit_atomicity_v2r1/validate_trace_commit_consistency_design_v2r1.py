from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path


TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
UPSTREAM = "72215ffb1b0a0bc9e7cc94155117ac8624ed0aa6"


def load(name: str):
    return json.loads((TASK / name).read_text(encoding="utf-8"))


def digest(name: str) -> str:
    return hashlib.sha256((TASK / name).read_bytes()).hexdigest()


def main() -> int:
    checks: list[dict[str, object]] = []

    def check(name: str, passed: bool, detail: object = None) -> None:
        checks.append({"name": name, "passed": bool(passed), "detail": detail})

    input_lock = load("TRACE_COMMIT_DESIGN_V2R1_INPUT_LOCK.json")
    execution_lock = load("TRACE_COMMIT_DESIGN_V2R1_EXECUTION_LOCK.json")
    current_order = load("CURRENT_ACTIVE_COMMIT_TRACE_ORDER_V2R1.json")
    finalize_order = load("CURRENT_TRACE_FINALIZATION_ORDER_V2R1.json")
    failures = load("TRACE_COMMIT_FAILURE_MODEL_V2R1.json")
    decision = load("TRACE_COMMIT_ARCHITECTURE_DECISION_V2R1.json")
    hazard = load("TRACE_FINALIZE_IN_MEMORY_DURABILITY_HAZARD_V2R1.json")
    retry = load("TRACE_FINALIZATION_RETRY_CONTRACT_V2R1.json")
    smoke = load("TRACE_COMMIT_SMOKE_DURABILITY_DECISION_V2R1.json")
    owners = load("TRACE_COMMIT_AUTHORITY_OWNERSHIP_V2R1.json")
    bypass = load("TRACE_COMMIT_BYPASS_IMPACT_V2R1.json")
    oracle = load("TRACE_COMMIT_ORACLE_COMPATIBILITY_V2R1.json")
    invariants = load("TRACE_COMMIT_CONSISTENCY_INVARIANTS_V2R1.json")
    tests = load("TRACE_COMMIT_IMPLEMENTATION_TEST_PLAN_V2R1.json")
    model = load("TRACE_COMMIT_DESIGN_MODEL_CHECK_V2R1.json")
    trace_faults = json.loads((ROOT / "reproduction/validation/revalidate_active_runtime_contract_conformance_v2_post_r2/POST_R2_TRACE_FAULT_SEMANTICS_V2.json").read_text())
    scenarios = list(csv.DictReader((TASK / "TRACE_COMMIT_DESIGN_SCENARIO_MATRIX_V2R1.csv").open(encoding="utf-8")))
    faults = list(csv.DictReader((TASK / "TRACE_COMMIT_FAULT_MATRIX_V2R1.csv").open(encoding="utf-8")))
    architectures = list(csv.DictReader((TASK / "TRACE_COMMIT_ARCHITECTURE_COMPARISON_V2R1.csv").open(encoding="utf-8")))
    changes = list(csv.DictReader((TASK / "TRACE_COMMIT_IMPLEMENTATION_CHANGE_MANIFEST_V2R1.csv").open(encoding="utf-8")))

    runtime_diff = subprocess.check_output(["git", "diff", "--name-only", UPSTREAM, "--", "reproduction/runtime", "run.py", "cbf", "dynamics", "splat"], cwd=ROOT, text=True).strip().splitlines()
    merge_base = subprocess.check_output(["git", "merge-base", "HEAD", UPSTREAM], cwd=ROOT, text=True).strip()

    check("01 PR127 exact", input_lock["pr127"]["head"] == UPSTREAM and input_lock["pr127"]["base_sha"] == "c38a51310767669e51ef6c87307c831405221277" and merge_base == UPSTREAM)
    check("02 runtime diff zero", not runtime_diff, runtime_diff)
    check("03 TRACE-F02 preserved", trace_faults["faults"]["TRACE-F02"]["passed"] is False and trace_faults["faults"]["TRACE-F02"]["detail"]["plant_count"] == 1)
    check("04 TRACE-F03 preserved", trace_faults["faults"]["TRACE-F03"]["passed"] is False and trace_faults["faults"]["TRACE-F03"]["detail"]["session_status"] == "READY")
    check("05 current ordering reconstructed", current_order["actual_order"] == ["SupervisorDecision", "PlantCommitAdapter.commit", "BackupTokenStore.prepare_and_activate_OR_consume", "TraceWriter.append", "return_CommitReceipt"])
    check("06 finalize ordering reconstructed", "construct_and_publish_self._lock" in finalize_order["actual_order"] and finalize_order["session_finalized"] == "only after finalize returns")
    check("07 failure model complete", len(failures["failure_classes"]) >= 13 and {x["id"] for x in failures["failure_classes"]} >= {f"F{i}" for i in range(1,14)})
    check("08 A/B/C compared", {x["option"][0] for x in architectures} == {"A", "B", "C"})
    check("09 architecture mechanically selected", decision["selected"] == "OPTION_B_SOFTWARE_TRANSACTION_STATE_MACHINE" and decision["selection_method"]["mandatory"])
    check("10 no physical atomicity overclaim", decision["physical_atomicity_claim"] is False and "physical ACID" in (TASK / "NO_SILENT_UNTRACED_COMMIT_PROPERTY_V2R1.md").read_text())
    prop = (TASK / "TRACE_COMMIT_CONSISTENCY_PROPERTY_V2R1.md").read_text()
    check("11 no-silent-untraced property", "Confirmed plant commit" in prop and "COMMITTED_TRACE_INCOMPLETE" in prop)
    check("12 no fake rollback", "physical rollback" in (TASK / "NO_SILENT_UNTRACED_COMMIT_PROPERTY_V2R1.md").read_text())
    check("13 plant outcome unresolved", "PLANT_OUTCOME_UNRESOLVED" in prop and "automatic retry" in prop)
    check("14 typed transaction result", "CommitTransactionResult" in prop and "attempt identity" in prop)
    check("15 evidence status complete", all(x in prop for x in ["COMPLETE", "PLANT_NOT_COMMITTED", "COMMITTED_TOKEN_INCOMPLETE", "COMMITTED_TRACE_INCOMPLETE", "FINALIZATION_INCOMPLETE", "RECOVERY_REQUIRED"]))
    check("16 session non-ready semantics", any(x["session_status"] == "EVIDENCE_INCOMPLETE" for x in failures["failure_classes"]) and all(x["next_cycle"] == "NO" for x in faults if x["session_state"] != "READY"))
    check("17 token semantics", any(x["typed_result"] == "COMMITTED_TOKEN_INCOMPLETE" for x in failures["failure_classes"]))
    check("18 trace failure semantics", any(x["typed_result"] == "COMMITTED_TRACE_INCOMPLETE" for x in failures["failure_classes"]))
    check("19 boundary failure semantics", next(x for x in faults if x["fault_id"] == "F6")["plant_state"] == "NO")
    check("20 finalize failure semantics", any(x["session_status"] == "FINALIZATION_FAILED" for x in failures["failure_classes"]))
    check("21 retry policy", retry["selected_policy"] == "IDEMPOTENT_RETRY" and retry["automatic_retry"] is False and len(retry["allowed_only_if"]) >= 5)
    check("22 memory/durable split", decision["journal_decision"] == "JOURNAL_NOT_REQUIRED_FOR_CURRENT_CONTRACT" and failures["process_crash_in_current_guarantee"] is False)
    check("23 smoke durability decision", smoke["decision"] in {"SMOKE_REQUIRES_DURABLE", "SMOKE_ALLOWED_WITH_MEMORY_ONLY_FAIL_CLOSE"} and smoke["decision"] == "SMOKE_ALLOWED_WITH_MEMORY_ONLY_FAIL_CLOSE")
    check("24 journal decision justified", len(decision["journal_upgrade_triggers"]) >= 3)
    check("25 lock hazard resolved in design", hazard["confirmed"] is True and len(hazard["design_resolution_for_selected_architecture"]) >= 4)
    check("26 ownership", owners["owners"]["PlantCommitAdapter"] == "sole plant execution authority" and "selection" in owners["owners"]["Supervisor"])
    check("27 module shape", load("TRACE_COMMIT_IMPLEMENTATION_MODULE_DECISION_V2R1.json")["selected_shape"] == "SHAPE_2_NEW_COMMIT_TRANSACTION")
    check("28 BYPASS impact", bypass["BYPASS_REVALIDATION_REQUIRED"] is True and bypass["decision"] == "SHARED_TRACE_FINALIZATION_CHANGE")
    check("29 oracle impact", set(oracle["forbidden_labels_for_incomplete"]) == {"SAFE", "SUCCESS", "COLLISION_FREE", "NORMAL_FAIL"})
    check("30 fault matrix", len(faults) >= 13 and all(row["typed_result"] for row in faults))
    check("31 formal property", "exactly one typed class" in prop and "never transitions directly to `READY`" in prop)
    check("32 invariants", len(invariants["invariants"]) == 28 and invariants["invariants"][0]["id"] == "TCC-01" and invariants["invariants"][-1]["id"] == "TCC-28")
    check("33 future tests", tests["test_count"] >= 20 and len(tests["tests"]) == tests["test_count"])
    check("34 scenarios", len(scenarios) >= 32)
    check("35 model counterexamples zero", model["counterexample_count"] == 0)
    check("36 implementation manifest", len(changes) >= 9 and any(x["file"] == "commit_transaction.py" and x["change_required"] == "YES_NEW" for x in changes))
    check("37 real counts zero", all(v == 0 for v in input_lock["execution_counts"].values()))
    check("38 only next implementation task", "IMPLEMENT_ACTIVE_RUNTIME_TRACE_COMMIT_ATOMICITY_V2R1" in (TASK / "IMPLEMENTATION_PLAN.md").read_text())
    check("39 execution lock valid", all(digest(name) == expected for name, expected in execution_lock["locked_sha256"].items()))
    check("40 selected option sufficient not maximal", architectures[1]["frozen_requirement_fit"] == "SUFFICIENT" and architectures[2]["frozen_requirement_fit"] == "EXCEEDS_CURRENT_SCOPE")

    failed = [item for item in checks if not item["passed"]]
    result = {"schema": "TRACE_COMMIT_CONSISTENCY_DESIGN_V2R1_VALIDATION", "check_count": len(checks), "passed_count": len(checks)-len(failed), "failed_count": len(failed), "status": "PASS_TRACE_COMMIT_CONSISTENCY_DESIGN_V2R1_VALIDATION" if not failed else "BLOCKED_TRACE_COMMIT_CONSISTENCY_DESIGN_V2R1", "checks": checks}
    (TASK / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
