from __future__ import annotations
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def main() -> int:
    architecture = json.loads((ROOT / "MODULE_ARCHITECTURE_V2.json").read_text(encoding="utf-8"))
    scenarios = json.loads((ROOT / "ACTIVE_RUNTIME_DESIGN_SCENARIOS_V2.json").read_text(encoding="utf-8"))
    transitions = list(csv.DictReader((ROOT / "RUNTIME_TRANSITION_IMPLEMENTATION_MANIFEST_V2.csv").open(encoding="utf-8", newline="")))
    edges = {tuple(edge) for edge in architecture["edges"]}
    checks = {
        "every_commit_path_carries_certified_authority": all(r["commit_allowed"] != "true" or r["commit_authority"] in {"CERTIFIED_NAVIGATION", "CERTIFIED_TERMINAL", "RETAINED_BACKUP"} for r in transitions),
        "every_no_action_path_ends_boundary": all(r["runtime_destination"] != "ASSURANCE_BOUNDARY" or r["commit_allowed"] == "false" for r in transitions),
        "no_direct_proposal_to_plant_edge": ("primary_proposal_adapter.py", "plant_commit.py") not in edges,
        "no_l2_to_commit_edge": ("l2_runtime.py", "plant_commit.py") not in edges,
        "no_l3_to_plant_edge": ("l3_runtime.py", "plant_commit.py") not in edges,
        "no_alternative_provider_to_commit_edge": ("alternative_provider.py", "plant_commit.py") not in edges,
        "no_terminal_membership_to_commit_edge": ("terminal_runtime.py", "plant_commit.py") not in edges,
        "no_oracle_to_runtime_edge": not any("oracle" in a.lower() or "oracle" in b.lower() for a, b in edges),
        "transition_table_totality": len(transitions) == 43 and len({r["rule_id"] for r in transitions}) == 43 and all(r["mapping_cardinality"] == "EXACTLY_ONCE" for r in transitions),
        "scenario_totality": scenarios["scenario_count"] == 28 and all(s["resolved"] for s in scenarios["scenarios"]),
    }
    counterexamples = [{"property": name} for name, passed in checks.items() if not passed]
    result = {"status": "PASS_ACTIVE_RUNTIME_DESIGN_MODEL_CHECK" if not counterexamples else "FAIL_ACTIVE_RUNTIME_DESIGN_MODEL_CHECK", "abstract_only": True, "geometry_numeric_execution": False, "checks": checks, "check_count": len(checks), "counterexample_count": len(counterexamples), "transition_rule_count": len(transitions), "scenario_count": scenarios["scenario_count"]}
    (ROOT / "active_runtime_design_model_check.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (ROOT / "active_runtime_design_counterexamples.json").write_text(json.dumps({"counterexample_count": len(counterexamples), "counterexamples": counterexamples}, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    return 0 if not counterexamples else 1

if __name__ == "__main__": raise SystemExit(main())
