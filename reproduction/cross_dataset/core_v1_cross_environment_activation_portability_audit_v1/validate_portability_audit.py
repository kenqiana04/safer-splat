"""Fail-closed validator for the frozen Core V1 portability audit."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
BASE_HEAD = "9287617cce74561aa434d1aca7eb684f79551188"
EXPECTED_HEADS = {
    84: "04ebca2b1b35124ad0e61ebed96e491c9edae4bb",
    85: "7afef38392bec36d9d9811e5a22c816da5faf1ff",
    86: "d4f20f44a810afc2d6379853a286a3e18b175221",
    87: "fbe67f0c607add7f8049d4ce75e8f9e1ae8498d9",
    88: BASE_HEAD,
}
METHODS = [
    "B0_CURRENT_CBF_ONLY",
    "B1_PLUS_SWEPT_SEGMENT",
    "B2_PLUS_TERMINAL_BACKUP",
    "B3_FULL_UNIFIED_WITH_DIRECTIONAL_ALTERNATIVES",
]
ENVIRONMENTS = [
    "E1_REPLICA_GT_FINE", "E2_ETH3D_LEARNED_GAUSSIAN", "E3_TUM_SPLATAM",
    "E4_TUM_GAUSSIAN_SLAM", "E5_STONEHENGE_SAFER", "E6_FLIGHT_SAFER",
    "E7_TUM_SPLATFACTO_NEGATIVE_CONTROL",
]
REQUIRED_FIELDS = {
    "environment", "reference_tier", "registry_sha256", "shared_input_hash", "method",
    "current_gate", "segment_gate", "backup_gate", "directional_availability",
    "selected_candidate", "committed", "typed_status", "fail_closed_reason",
    "segment_lower_bound", "backup_horizon", "active_primitive_count", "candidate_count",
    "component_timing", "total_runtime_s", "deadline_miss", "semantic_status",
    "offline_reference_sweep", "map_reference_disagreement", "unknown", "nonfinite",
    "infrastructure_failure",
}
FINAL_STATUS = "NO_CORE_V1_REPRESENTATIVE_PORTABILITY_SIGNAL"
FINAL_DECISION = "UPHOLD_PR88_CASE_D_AND_STOP_CORE_V1_METHOD_EXPANSION"
PASS = "PASS_CORE_V1_CROSS_ENVIRONMENT_ACTIVATION_PORTABILITY_AUDIT_VALIDATION"


def read_json(relative: str) -> Any:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def rows(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], *, env: dict[str, str] | None = None) -> dict[str, Any]:
    result = subprocess.run(command, cwd=REPO, capture_output=True, text=True, env=env)
    return {
        "command": command,
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-2000:],
        "stderr_tail": result.stderr[-2000:],
    }


def main() -> None:
    checks: list[dict[str, Any]] = []

    def check(name: str, condition: bool, detail: Any = None) -> None:
        checks.append({"name": name, "pass": bool(condition), "detail": detail})

    for number, expected in EXPECTED_HEADS.items():
        identity = read_json(f"input_freeze/pr{number}_identity.json")
        check(f"pr{number}_identity", identity["head_sha"] == expected and identity["state"] == "OPEN" and identity["draft"] is True and identity.get("merged", False) is False and identity["mergeable"] in {True, "MERGEABLE"}, identity)
    pr88 = read_json("input_freeze/pr88_identity.json")
    check("pr88_lineage", pr88["base"] == "resume-replica-gt-executable-safety-activated-benchmark-v1" and pr88["base_sha"] == "fbe67f0c607add7f8049d4ce75e8f9e1ae8498d9")

    protected = read_json("input_freeze/protected_source_hashes.json")
    check("protected_record_count", protected["record_count"] == 14)
    protected_ok = True
    protected_detail = []
    for item in protected["records"]:
        blob = subprocess.run(["git", "cat-file", "blob", f"{item['commit']}:{item['path']}"], cwd=REPO, capture_output=True).stdout
        observed = hashlib.sha256(blob).hexdigest()
        good = observed == item["sha256"] and len(blob) == item["size"]
        protected_ok &= good
        protected_detail.append({"path": item["path"], "match": good})
    check("protected_raw_git_blobs", protected_ok, protected_detail)
    check("protected_source_mutation_zero", read_json("audits/protected_source_audit.json")["protected_source_mutation_count"] == 0)

    method = read_json("methods/method_registry.json")
    check("exact_frozen_method_contract", method["normative_model"] == "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1" and method["dt_s"] == 0.05 and method["u_bound_inf"] == method["v_bound_inf"] == 0.1 and method["robot_radius_m"] == 0.1 and method["effective_radius_m"] == 0.11 and method["terminal_tolerance_m_per_s"] == 1e-12 and method["h_stop_max"] == 20 and method["methods"] == METHODS and method["six_slot_library_sha256"] == "3d491876234161d4e881ec1227c505cb07c0af00d5e881c5289fdf1f1577c6fe")
    fairness = read_json("methods/fairness_audit.json")
    check("method_fairness", fairness["same_state_goal_map_controller_bounds"] and fairness["method_mutation_count"] == fairness["parameter_tuning_count"] == 0 and fairness["slot_count"] == 6)

    env = read_json("environments/environment_registry.json")
    check("seven_environment_preregistration_no_e8", env["environment_count"] == 7 and [item["environment"] for item in env["environments"]] == ENVIRONMENTS and env["no_e8"] is True)
    readiness = {row["environment"]: row for row in rows("environments/environment_readiness_matrix.csv")}
    check("environment_readiness_and_unknown_policy", set(readiness) == set(ENVIRONMENTS) and all(row["unknown_not_free"] == "True" and row["hidden_clipping"] == "False" for row in readiness.values()))
    tiers = {row["environment"]: row for row in rows("environments/reference_tier_matrix.csv")}
    check("reference_tiers_and_no_pooling", set(tiers) == set(ENVIRONMENTS) and all(row["pooled_across_tiers"] == "False" for row in tiers.values()))

    combined = read_json("registry/combined_registry_manifest.json")
    counts = {row["environment"]: row["state_count"] for row in combined["environments"]}
    check("registry_counts", counts == {ENVIRONMENTS[0]: 160, ENVIRONMENTS[1]: 0, ENVIRONMENTS[2]: 0, ENVIRONMENTS[3]: 0, ENVIRONMENTS[4]: 100, ENVIRONMENTS[5]: 100, ENVIRONMENTS[6]: 0}, counts)
    replica = next(row for row in combined["environments"] if row["environment"] == ENVIRONMENTS[0])
    check("replica_registry_exact_reuse", replica["registry_sha256"] == "eaa0f9f63cbcae433741b959441cf244648e30bf184b62309334602b76659a1a")
    rebuild = read_json("audits/registry_rebuild_audit.json")
    check("three_process_registry_rebuild", rebuild["registry_rebuild_count_each"] == 3 and all(row["fresh_process_count"] == 3 and row["match"] and len(set(row["sha256_values"])) == 1 for row in rebuild["environments"].values()))
    leakage = read_json("audits/selection_leakage_audit.json")
    check("selection_no_leakage", leakage["prelock_method_run_count"] == leakage["prelock_future_reference_read_count"] == leakage["prelock_activation_read_count"] == leakage["prelock_progress_read_count"] == leakage["prelock_runtime_read_count"] == leakage["postlock_replacement_count"] == 0 and leakage["outcome_columns_consumed_by_selection"] == [])

    formal = read_json("benchmark/formal_attempt.json")
    records = rows("benchmark/one_step_records.csv")
    check("single_formal_attempt", formal["status"] == "FORMAL_ATTEMPT_COMPLETED" and formal["formal_attempt_count"] == 1 and formal["infrastructure_failure_count"] == 0 and formal["same_manifest_resume_count"] == 0)
    check("formal_output_identity", sha256(ROOT / "benchmark/one_step_records.csv") == formal["normalized_output_sha256"] == formal["output_sha256"] and formal["raw_output_sha256"] == "9d13a540edff5e79706d0ae6a905ea6c58ed56020d9a9a8a0e43617b70dc65af" and formal["normalization_semantics_changed"] is False)
    check("one_step_required_fields", len(records) == 1440 and REQUIRED_FIELDS <= set(records[0]), sorted(REQUIRED_FIELDS - set(records[0])))
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in records:
        grouped[(row["environment"], row["state_id"])].append(row)
    pairing_ok = len(grouped) == 360 and Counter(environment for environment, _ in grouped) == {ENVIRONMENTS[0]: 160, ENVIRONMENTS[4]: 100, ENVIRONMENTS[5]: 100}
    pairing_ok &= all({row["method"] for row in values} == set(METHODS) and len({row["shared_input_hash"] for row in values}) == 1 for values in grouped.values())
    check("paired_shared_input_contract", pairing_ok)
    check("no_unknown_nonfinite_infrastructure", all(row["unknown"] == row["nonfinite"] == row["infrastructure_failure"] == "False" for row in records))
    check("zero_incremental_events", all(row["segment_incremental_activation"] == row["backup_incremental_activation"] == row["directional_incremental_rescue"] == row["any_incremental_activation"] == "False" for row in records))
    replica_records = [row for row in records if row["environment"] == ENVIRONMENTS[0]]
    check("replica_reference_separation", all(row["offline_reference_sweep"] == "False" and row["map_reference_disagreement"] == "False" and row["represented_false_safe"] == "False" for row in replica_records))
    external_records = [row for row in records if row["environment"] in {ENVIRONMENTS[4], ENVIRONMENTS[5]}]
    check("behavior_only_reference_not_evaluable", all(row["offline_reference_sweep"] == row["map_reference_disagreement"] == row["represented_false_safe"] == "NOT_EVALUABLE" for row in external_records))
    check("fail_closed_not_safe_stop", all(not (row["committed"] == "False" and "SAFE_STOP" in row["semantic_status"]) for row in records))

    natural = rows("benchmark/natural_event_rollout_records.csv")
    check("natural_event_only_no_synthetic_replacement", natural == [] and formal["natural_incremental_event_count"] == formal["natural_rollout_episode_count"] == formal["logical_rollout_step_count"] == 0)
    gate = read_json("statistics/portability_gate_audit.json")
    check("frozen_portability_gates", gate["gates"] == {"P1": False, "P2": False, "P3": False, "P4": False, "P5": True, "P6": True, "P7": True, "P8": True, "P9": True, "P10": True} and gate["qualified_count"] == 0 and gate["e7_in_pass_fail"] is False and gate["cross_tier_pooling"] is False)
    decision = read_json("decision/final_portability_decision.json")
    check("strict_case_c_decision", decision["case"] == "CASE_C" and decision["final_status"] == FINAL_STATUS and decision["final_decision"] == FINAL_DECISION and decision["only_next_task"] == "WRITE_FROZEN_PAPER_CONTRIBUTION_AND_EXPERIMENT_PLAN_V1")

    figures = sorted((ROOT / "figures").glob("*.png"))
    check("thirty_nonempty_figures", len(figures) == 30 and all(path.stat().st_size > 10_000 for path in figures), {path.name: path.stat().st_size for path in figures})
    source = (ROOT / "build_audit_artifacts.py").read_text(encoding="utf-8")
    labels = ["REPRESENTATIVE COHORT", "ACTIVATED RESULT REUSED ONLY AS MECHANISM CONTROL", "REFERENCE-COMPLETE", "OBSERVABLE-REFERENCE ONLY", "REPRESENTED-MAP BEHAVIOR ONLY", "DIAGNOSTIC NEGATIVE CONTROL", "CONFIGURATION FROZEN", "NO PARAMETER TUNING", "NOT A COLLISION-SUPERIORITY CLAIM", "NOT A REAL-TIME CLAIM", "NOT A CROSS-MAP SAFETY CERTIFICATE"]
    check("required_figure_labels", all(label in source for label in labels))
    report = (ROOT / "report/REPORT_AUDIT_CORE_V1_CROSS_ENVIRONMENT_ACTIVATION_PORTABILITY_V1.md").read_text(encoding="utf-8")
    check("report_61_fields_and_historical_deadline", all(re.search(rf"(?m)^{number}\. ", report) for number in range(1, 62)) and "116/260" in report and FINAL_STATUS in report and FINAL_DECISION in report)

    final_system = read_json("audits/final_system_state.json")
    check("gpu_and_task_process_clean", final_system["status"] == "PASS_FINAL_SERVER_GPU_PROCESS_AUDIT" and final_system["gpu_compute_process_count"] == final_system["task_owned_process_count"] == 0)
    check("watchdog_ssh_preserved", final_system["watchdog_preserved_no_action"] and final_system["ssh_preserved_no_action"] and final_system["ssh_kill_count"] == final_system["sshd_restart_count"] == final_system["network_restart_count"] == final_system["firewall_or_route_change_count"] == 0)

    status = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True, text=True, check=True).stdout.splitlines()
    outside = [line for line in status if str(ROOT.relative_to(REPO)).replace("\\", "/") not in line.replace("\\", "/")]
    check("git_scope_only_task_directory", not outside, outside)
    text_suffixes = {".py", ".json", ".csv", ".md", ".sh"}
    bad_text: list[str] = []
    large: list[str] = []
    secret_hits: list[str] = []
    secret_pattern = re.compile(r"(?i)(hf_[a-z0-9]{20,}|github_pat_[a-z0-9_]{20,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----)")
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.stat().st_size > 5 * 1024 * 1024:
            large.append(str(path.relative_to(ROOT)))
        if path.suffix in text_suffixes:
            raw = path.read_bytes()
            if raw.startswith(b"\xef\xbb\xbf") or b"\r\n" in raw or not raw.endswith(b"\n"):
                bad_text.append(str(path.relative_to(ROOT)))
            if secret_pattern.search(raw.decode("utf-8", errors="ignore")):
                secret_hits.append(str(path.relative_to(ROOT)))
    check("utf8_lf_no_bom", not bad_text, bad_text)
    check("no_large_assets", not large, large)
    check("no_credentials", not secret_hits, secret_hits)

    env_vars = dict(os.environ)
    env_vars["PYTHONDONTWRITEBYTECODE"] = "1"
    compile_result = run([sys.executable, "-m", "compileall", "-q", str(ROOT)], env=env_vars)
    for cache in ROOT.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    pytest_runtime = Path.home() / "Documents/Codex/github-clean-work/safer-splat-direction-audit-v1/reproduction/research_direction/safer_splat_direction_audit_v1/.cache/pytest_runtime"
    pytest_env = dict(env_vars)
    pytest_env["PYTHONPATH"] = str(pytest_runtime) + (os.pathsep + pytest_env["PYTHONPATH"] if pytest_env.get("PYTHONPATH") else "")
    pytest_result = run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(ROOT / "tests")], env=pytest_env)
    diff_result = run(["git", "diff", "--check"])
    cached_diff_result = run(["git", "diff", "--cached", "--check"])
    check("compileall", compile_result["returncode"] == 0, compile_result)
    check("pytest", pytest_result["returncode"] == 0, pytest_result)
    check("git_diff_check", diff_result["returncode"] == 0 and cached_diff_result["returncode"] == 0, {"unstaged": diff_result, "cached": cached_diff_result})

    failures = [item for item in checks if not item["pass"]]
    payload = {
        "status": PASS if not failures else "FAIL_CORE_V1_CROSS_ENVIRONMENT_ACTIVATION_PORTABILITY_AUDIT_VALIDATION",
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "final_status": FINAL_STATUS,
        "final_decision": FINAL_DECISION,
    }
    output = ROOT / "report/validation_result.json"
    output.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    if failures:
        print(payload["status"])
        for failure in failures:
            print("FAIL", failure["name"], failure["detail"])
        raise SystemExit(1)
    print(PASS)


if __name__ == "__main__":
    main()
