from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TASK = Path(__file__).resolve().parent


def load(name: str):
    return json.loads((TASK / name).read_text(encoding="utf-8"))


def main() -> int:
    checks = []

    def check(name: str, passed: bool, evidence):
        checks.append({"name": name, "passed": bool(passed), "evidence": evidence})

    lock = load("ACTIVE_CONFORMANCE_INPUT_LOCK.json")
    check("01_pr119_exact", lock["direct_upstream"]["head"] == "b4ff579cf6a2bcffd0661cd39eb925aa4f3a5d27" and lock["direct_upstream"]["base_sha"] == "a537ff653ac896aa1ab567b5197136efa1a937b4", lock["direct_upstream"])
    check("02_bypass_pass_frozen", lock["bypass_evidence"]["verdict"] == "PASS_REFROZEN_BYPASS_EQUIVALENCE_V2R1" and lock["bypass_evidence"]["pairs"] == 5 and lock["bypass_evidence"]["compared_steps"] == 732 and lock["bypass_evidence"]["all_mismatch_counts_zero"], lock["bypass_evidence"])
    source_diff = subprocess.run(["git", "diff", "--name-only", "b4ff579cf6a2bcffd0661cd39eb925aa4f3a5d27", "--", "run.py", "cbf", "dynamics", "splat", "reproduction/runtime/active_runtime_assurance_v2"], cwd=ROOT, text=True, capture_output=True, check=True).stdout.strip().splitlines()
    check("03_protected_source_diff_zero", not source_diff, source_diff)
    check("04_input_lock_present", len(lock["runtime_modules_17"]) == 17 and lock["runtime_correction_quota"] == 0, len(lock["runtime_modules_17"]))
    audit = (TASK / "ACTIVE_RUNTIME_PUBLIC_INTEGRATION_AUDIT_V2.md").read_text(encoding="utf-8")
    check("05_integration_audit", "no public" in audit.lower() and "INTEGRATION_ORCHESTRATION_GAP" in audit, "public cycle absent")
    ownership = load("ACTIVE_AUTHORITY_OWNERSHIP_AUDIT_V2.json")
    check("06_selection_owner", ownership["selection_owner"]["expected"] == "Supervisor.arbitrate", ownership["selection_owner"])
    check("07_plant_owner", ownership["plant_owner"]["expected"] == "PlantCommitAdapter.commit", ownership["plant_owner"])
    check("08_call_order_artifact", load("ACTIVE_CALL_ORDER_CONFORMANCE_V2.json")["required_order"] == ["L1", "P0", "C0", "L2", "L3"], "required order present")
    matrix = list(csv.DictReader((TASK / "ACTIVE_TRANSITION_CONFORMANCE_MATRIX_V2.csv").open(encoding="utf-8", newline="")))
    critical = [row for row in matrix if row["critical"] == "true"]
    check("09_transition_43", len(matrix) == 43 and len({row["rule_id"] for row in matrix}) == 43, len(matrix))
    check("10_critical_dynamic_declared", all(row["mode"] == "DYNAMIC_PUBLIC_PATH" for row in critical), len(critical))
    c0_source = (ROOT / "reproduction/runtime/active_runtime_assurance_v2/c0_admission.py").read_text(encoding="utf-8")
    plant_source = (ROOT / "reproduction/runtime/active_runtime_assurance_v2/plant_commit.py").read_text(encoding="utf-8")
    check("11_c0_no_clip", ".clip(" not in c0_source and "clamp(" not in c0_source and ".clip(" not in plant_source and "clamp(" not in plant_source, "source scan")
    check("12_l2_geometry", load("ACTIVE_CONFORMANCE_INPUT_LOCK.json")["frozen_contracts"][1]["authority"] == "PR108_GEOMETRY", "PR108 locked")
    check("13_l3_semantics", any("L3" in row["rule_id"] for row in matrix), "L3 rows")
    check("14_no_synthetic", ownership["forbidden_direct_edges"]["alternative_to_plant"], "no direct alternative plant edge")
    check("15_deadline_fixture", load("CONFORMANCE_TEST_FIXTURE_BOUNDARY_V2.json")["deadline_profile"] == "TEST_FIXTURE_ONLY_NOT_RUNTIME_AUTHORITY", "fixture boundary")
    check("16_token_artifact", load("ACTIVE_CONFORMANCE_INPUT_LOCK.json")["frozen_contracts"][5]["authority"] == "PR112_BACKUP_TOKEN", "PR112 locked")
    check("17_terminal_artifact", load("ACTIVE_CONFORMANCE_INPUT_LOCK.json")["frozen_contracts"][6]["authority"] == "PR113_TERMINAL", "PR113 locked")
    check("18_boundary_no_plant", load("ACTIVE_TRACE_CONFORMANCE_V2.json")["boundary_trace_role"] == "PASS", "boundary role")
    check("19_unknown_separation", load("UNKNOWN_ROUTING_CONFORMANCE_V2.json")["module_level_typed_unknown"] is True and load("UNKNOWN_ROUTING_CONFORMANCE_V2.json")["silent_pass"] is False, "typed UNKNOWN")
    check("20_trace_oracle", load("ACTIVE_TRACE_CONFORMANCE_V2.json")["oracle_import_or_feedback"] == "NONE_OBSERVED", "oracle isolated")
    check("21_scenario_manifest", load("scenario_manifest.json")["scenario_count"] >= 76, load("scenario_manifest.json")["scenario_count"])
    results = load("scenario_results.json")["results"]
    check("22_mandatory_scenarios", len(results) == load("scenario_manifest.json")["scenario_count"], len(results))
    check("23_e2e_6_not_faked", load("scenario_results.json")["e2e_genuine_count"] == 0, "blocked, not fabricated")
    model = load("active_contract_model_check_result.json")
    check("24_model_counterexample_preserved", model["counterexample_count"] == 1 and model["checks"][0]["passed"] is False, model["counterexample_count"])
    check("25_real_active_zero", lock["real_active_rollout_count"] == 0, lock["real_active_rollout_count"])
    check("26_gpu_zero", lock["gpu_execution_count"] == 0, lock["gpu_execution_count"])
    check("27_oracle_zero", lock["scientific_oracle_count"] == 0, lock["scientific_oracle_count"])
    check("28_official100_zero", lock["official100_count"] == 0, lock["official100_count"])
    check("29_protocol_deviation_zero", lock["runtime_correction_quota"] == 0, lock["runtime_correction_quota"])
    check("30_blocker_preserved", load("FINAL_DECISION.json")["FINAL_STATUS"] == "BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP", load("FINAL_DECISION.json")["FINAL_STATUS"])
    failures = [item for item in checks if not item["passed"]]
    final_status = load("FINAL_DECISION.json")["FINAL_STATUS"]
    verdict = "PASS_ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2_VALIDATION" if not failures and final_status.startswith("PASS_") else "BLOCKED_ACTIVE_CONFORMANCE_BY_INTEGRATION_ORCHESTRATION_GAP"
    result = {"schema": "ACTIVE_RUNTIME_CONTRACT_CONFORMANCE_V2_VALIDATION", "check_count": len(checks), "passed_count": len(checks) - len(failures), "failed_count": len(failures), "checks": checks, "verdict": verdict, "real_active_rollout_count": 0, "gpu_execution_count": 0, "scientific_oracle_count": 0, "official100_count": 0}
    (TASK / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["verdict"])
    print(f"checks={len(checks)} failed={len(failures)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
