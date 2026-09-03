from __future__ import annotations
import csv, hashlib, json, subprocess
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[2]
UPSTREAM = "c924a959b1aa18b446a1d3c85afbe4f897604a84"
PREFIX = "reproduction/design/active_runtime_assurance_implementation_v2/"

def load(name): return json.loads((TASK / name).read_text(encoding="utf-8"))
def git(*args): return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
def rows(name):
    with (TASK / name).open(encoding="utf-8", newline="") as h: return list(csv.DictReader(h))

def main():
    inp = load("ACTIVE_RUNTIME_DESIGN_INPUT_LOCK.json")
    lock = load("ACTIVE_RUNTIME_DESIGN_EXECUTION_LOCK.json")
    arch = load("MODULE_ARCHITECTURE_V2.json")
    feasibility = load("ADDITIVE_DRIVER_FEASIBILITY_V2.json")
    modes = load("RUNTIME_MODE_CONTRACT_V2.json")
    gates = load("ACTIVE_RUNTIME_PARAMETERIZATION_GATES_V2.json")
    deadline = load("DEADLINE_RUNTIME_PARAMETERIZATION_GATE_V2.json")
    invariants = load("ACTIVE_RUNTIME_DESIGN_INVARIANTS_V2.json")
    scenarios = load("ACTIVE_RUNTIME_DESIGN_SCENARIOS_V2.json")
    model = load("active_runtime_design_model_check.json")
    counter = load("active_runtime_design_counterexamples.json")
    transitions = rows("RUNTIME_TRANSITION_IMPLEMENTATION_MANIFEST_V2.csv")
    implementation = rows("ACTIVE_RUNTIME_IMPLEMENTATION_FILE_MANIFEST_V2.csv")
    changes = rows("IMPLEMENTATION_CHANGE_AUTHORIZATION_MATRIX_V2.csv")
    alternatives = rows("NATIVE_ALTERNATIVE_SOURCE_INVENTORY_V2.csv")
    source = rows("../../specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv")
    commit1 = lock["commit1"]
    frozen_ok = True
    for item in lock["frozen_artifacts"].values():
        full = PREFIX + item["path"]
        raw = subprocess.check_output(["git", "show", f"{commit1}:{full}"], cwd=ROOT)
        frozen_ok &= git("rev-parse", f"{commit1}:{full}") == item["git_blob_sha1"] and hashlib.sha256(raw).hexdigest() == item["sha256"]
    source_by_id = {r["rule_id"]: r for r in source}
    transition_exact = len(transitions) == len(source) == 43 and len({r["rule_id"] for r in transitions}) == 43
    for row in transitions:
        original = source_by_id.get(row["rule_id"], {})
        transition_exact &= all(row.get(k) == v for k, v in original.items()) and row["mapping_cardinality"] == "EXACTLY_ONCE"
    checks = {
        "01_PR114_exact_identity": inp["direct_upstream"]["head"] == UPSTREAM and inp["direct_upstream"]["state"] == "OPEN" and inp["direct_upstream"]["draft"] is True and git("merge-base", commit1, UPSTREAM) == UPSTREAM,
        "02_zero_preimplementation_blockers": inp["preimplementation_contract_blocker_count"] == 0,
        "03_PR107_PR114_authorities_referenced": [x["pr"] for x in inp["upstream_prs"]] == list(range(107,115)),
        "04_additive_strategy_resolved": feasibility["verdict"] == "PASS_ADDITIVE_DRIVER_FEASIBLE" and feasibility["production_edit_required"] is False,
        "05_module_graph_acyclic": arch["acyclic_dependency_graph"] is True,
        "06_single_supervisor_selection": sum(1 for m in arch["modules"] if m["owns_selection"]) == 1 and arch["selection_owner"] == "Supervisor.arbitrate",
        "07_single_plant_commit": sum(1 for m in arch["modules"] if m["writes_plant"]) == 1 and arch["plant_commit_owner"] == "PlantCommitAdapter.commit",
        "08_no_oracle_feedback_edge": arch["oracle_runtime_edges"] == [] and not any("oracle" in e[0].lower() for e in arch["edges"]),
        "09_no_V1_geometry_loader_future_import": all("load_frozen_robot_margin_contract" not in r["allowed_imports"] and "0.11" not in r["allowed_imports"] for r in implementation),
        "10_transition_table_total_mapping": transition_exact,
        "11_runtime_modes_frozen": set(modes["modes"]) == {"REFERENCE_BASELINE", "ACTIVE_HARNESS_BYPASS", "ACTIVE_RUNTIME_ON"},
        "12_first_cycle_semantics": "first runtime cycle" in (TASK / "FIRST_CYCLE_AND_START_ADMISSION_V2.md").read_text(encoding="utf-8").lower(),
        "13_deadline_activation_gate": deadline["active_startup_missing_profile_result"] == "DEADLINE_PROFILE_REQUIRED" and deadline["numeric_values_frozen_by_this_task"] is False,
        "14_alternative_inventory_policy": len(alternatives) == 1 and alternatives[0]["candidate_count"] == "0" and alternatives[0]["result"] == "NO_ALTERNATIVE_AVAILABLE",
        "15_token_lifecycle_interface": all(x in (TASK / "PLANT_COMMIT_BOUNDARY_V2.md").read_text(encoding="utf-8") + (TASK / "CANDIDATE_CERTIFICATION_PIPELINE_V2.md").read_text(encoding="utf-8") for x in ["prepared", "active", "cursor"]),
        "16_terminal_policy_preserved": gates["goal_hold_runtime_authority"]["status"] == "DISABLED" and "CERTIFIED_TERMINAL" in (TASK / "PLANT_COMMIT_BOUNDARY_V2.md").read_text(encoding="utf-8"),
        "17_trace_oracle_boundary": "Only after that lock exists" in (TASK / "RUNTIME_TRACE_TO_ORACLE_BOUNDARY_V2.md").read_text(encoding="utf-8"),
        "18_legacy_semantics_quarantined": all(x in (TASK / "LEGACY_RUNNER_REUSE_AND_QUARANTINE_V2.md").read_text(encoding="utf-8") for x in ["endpoint-only", "timeout", "physical safe stop"]),
        "19_ARI_01_30_complete": invariants["invariant_count"] == 30 and [x["id"] for x in invariants["invariants"]] == [f"ARI-{i:02d}" for i in range(1,31)],
        "20_all_design_scenarios_resolved": scenarios["scenario_count"] == 28 and all(x["resolved"] for x in scenarios["scenarios"]),
        "21_implementation_file_manifest_complete": len(implementation) == 17 and all(r["target_path"].startswith("reproduction/runtime/active_runtime_assurance_v2/") for r in implementation),
        "22_production_source_read_only": all(next(r for r in changes if r["path_or_surface"] == p)["authorization"] == "READ_ONLY" for p in ["run.py", "cbf/cbf_utils.py", "dynamics/systems.py", "splat/*"]),
        "23_execution_lock_exact": frozen_ok,
        "24_model_check_pass": model["status"] == "PASS_ACTIVE_RUNTIME_DESIGN_MODEL_CHECK" and counter["counterexample_count"] == 0,
        "25_design_scope_zero_execution": inp["scientific_execution_count"] == 0 and inp["gpu_authority"] is False and inp["rollout_authority"] is False,
    }
    status = "PASS_ACTIVE_RUNTIME_ASSURANCE_IMPLEMENTATION_V2_DESIGN_VALIDATION" if all(checks.values()) else "FAIL_ACTIVE_RUNTIME_ASSURANCE_IMPLEMENTATION_V2_DESIGN_VALIDATION"
    result = {"status": status, "checks": checks, "check_count": len(checks), "passed_count": sum(checks.values()), "transition_rule_count": len(transitions), "production_source_mutation_count": 0, "runtime_implementation_count": 0, "gpu_execution_count": 0, "rollout_count": 0, "formal_collection_count": 0}
    (TASK / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(status)
    return 0 if all(checks.values()) else 1

if __name__ == "__main__": raise SystemExit(main())
