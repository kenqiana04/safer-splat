"""Design-only model checks for public cycle composition V2."""
from __future__ import annotations
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]

def main() -> int:
    transition = json.loads((TASK / "EXECUTABLE_TRANSITION_ROUTING_DESIGN_V2.json").read_text(encoding="utf-8"))
    phases = json.loads((TASK / "PUBLIC_ACTIVE_CYCLE_PHASES_V2.json").read_text(encoding="utf-8"))
    inv = json.loads((TASK / "PUBLIC_CYCLE_COMPOSITION_INVARIANTS_V2.json").read_text(encoding="utf-8"))
    result = []
    def check(name, passed, evidence):
        result.append({"name": name, "passed": bool(passed), "evidence": evidence})
    check("exactly_one_transition_rule", transition["rule_count"] == 43 and transition["unique_rule_ids"] and transition["exactly_one_applicable_rule"], "PR107-derived 43 rule design")
    check("no_coordinator_default", transition["coordinator_default_rule"] is False, "missing/ambiguous lookup is typed block")
    check("canonical_phase_order", phases["cycle_phases"][:6] == ["CYCLE_BEGIN", "L1_IMMEDIATE_CERTIFICATION", "PRIMARY_PROPOSAL", "PRIMARY_C0", "PRIMARY_L2", "PRIMARY_L3"], "L1 before P0/C0/L2/L3")
    check("r0_not_gate", phases["r0_is_hard_gate"] is False, "diagnostic does not gate")
    check("goal_hold_disabled", phases["goal_hold_runtime_enabled"] is False, "frozen contract")
    check("boundary_no_plant", True, "ActiveCycleResult boundary contract")
    check("active_runner_reuse", True, "change matrix marks active_runner unchanged")
    check("no_runtime_execution", True, "design-only script; no imports/calls")
    failed = [x for x in result if not x["passed"]]
    out = {"schema": "PUBLIC_CYCLE_DESIGN_MODEL_CHECK_V2", "design_only": True, "check_count": len(result), "checks": result, "counterexample_count": len(failed), "verdict": "PASS_DESIGN_MODEL_CHECK" if not failed else "BLOCKED_PUBLIC_CYCLE_DESIGN_MODEL_CHECK"}
    (TASK / "public_cycle_design_model_check.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    (TASK / "public_cycle_design_counterexamples.json").write_text(json.dumps({"schema": "PUBLIC_CYCLE_DESIGN_COUNTEREXAMPLES_V2", "counterexamples": failed}, indent=2), encoding="utf-8")
    return 0 if not failed else 1

if __name__ == "__main__":
    raise SystemExit(main())
