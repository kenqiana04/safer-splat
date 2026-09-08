from __future__ import annotations

import csv
import json
from pathlib import Path


TASK = Path(__file__).resolve().parent


def main() -> int:
    faults = list(csv.DictReader((TASK / "TRACE_COMMIT_FAULT_MATRIX_V2R1.csv").open(encoding="utf-8")))
    decision = json.loads((TASK / "TRACE_COMMIT_ARCHITECTURE_DECISION_V2R1.json").read_text(encoding="utf-8"))
    counterexamples: list[dict[str, object]] = []

    for row in faults:
        fault = row["fault_id"]
        session = row["session_state"]
        plant = row["plant_state"]
        trace = row["trace_state"]
        typed = row["typed_result"]
        retry = row["retry"]
        oracle = row["oracle_eligible"]
        next_cycle = row["next_cycle"]

        if plant == "YES" and "INCOMPLETE" in trace and session == "READY":
            counterexamples.append({"fault": fault, "property": "no committed+READY+trace_incomplete"})
        if "UNRESOLVED" in typed and session == "READY":
            counterexamples.append({"fault": fault, "property": "no unresolved+READY"})
        if "FINALIZATION_INCOMPLETE" == typed and session == "READY":
            counterexamples.append({"fault": fault, "property": "no finalize_failed+READY"})
        if plant == "NO" and typed.startswith("COMMITTED"):
            counterexamples.append({"fault": fault, "property": "no false executed claim before plant"})
        if retry == "YES":
            counterexamples.append({"fault": fault, "property": "no automatic/ordinary retry"})
        if fault == "F6" and plant != "NO":
            counterexamples.append({"fault": fault, "property": "no boundary plant"})
        if "INCOMPLETE" in typed and oracle != "NO":
            counterexamples.append({"fault": fault, "property": "no oracle-ready incomplete trace"})
        if session != "READY" and next_cycle != "NO":
            counterexamples.append({"fault": fault, "property": "non-ready blocks next cycle"})
        if not typed:
            counterexamples.append({"fault": fault, "property": "all faults terminate in typed class"})

    required_states = {"PREPARED", "COMMITTED", "TOKEN_APPLIED", "TRACE_RECORDED", "COMPLETE", "RECOVERY_REQUIRED"}
    actual_states = set(decision["transaction_states"])
    if not required_states <= actual_states:
        counterexamples.append({"property": "architecture-specific states", "missing": sorted(required_states - actual_states)})
    if decision["selected"] != "OPTION_B_SOFTWARE_TRANSACTION_STATE_MACHINE":
        counterexamples.append({"property": "mechanical architecture selection"})
    if decision["physical_atomicity_claim"]:
        counterexamples.append({"property": "no physical ACID claim"})

    result = {
        "schema": "TRACE_COMMIT_DESIGN_MODEL_CHECK_V2R1",
        "architecture": decision["selected"],
        "fault_state_count": len(faults),
        "properties_checked": 10,
        "counterexample_count": len(counterexamples),
        "status": "PASS_TRACE_COMMIT_CONSISTENCY_DESIGN_V2R1_MODEL_CHECK" if not counterexamples else "BLOCKED_TRACE_COMMIT_DESIGN_BY_MODEL_COUNTEREXAMPLE",
    }
    (TASK / "TRACE_COMMIT_DESIGN_MODEL_CHECK_V2R1.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (TASK / "TRACE_COMMIT_DESIGN_COUNTEREXAMPLES_V2R1.json").write_text(json.dumps({"schema": "TRACE_COMMIT_DESIGN_COUNTEREXAMPLES_V2R1", "counterexamples": counterexamples}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    return 0 if not counterexamples else 1


if __name__ == "__main__":
    raise SystemExit(main())
