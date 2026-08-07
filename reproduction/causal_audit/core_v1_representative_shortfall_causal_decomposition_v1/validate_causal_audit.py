"""Fail-closed validator for the Core V1 causal-decomposition package."""
from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

from common import sha256_file, write_json
from task_config import BASE_HEAD, BRANCH, FORMAL_ENVIRONMENTS, TASK_ROOT


def require(condition: bool, token: str, failures: list[str]) -> None:
    if not condition:
        failures.append(token)


def rows(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(encoding="utf-8", newline="")))


def main() -> None:
    failures: list[str] = []
    branch = subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
    require(branch == BRANCH, "BRANCH_MISMATCH", failures)
    changed = set(subprocess.check_output(["git", "diff", "--name-only", BASE_HEAD], text=True).splitlines())
    changed.update(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], text=True).splitlines())
    allowed_prefix = "reproduction/causal_audit/core_v1_representative_shortfall_causal_decomposition_v1/"
    require(all(path.startswith(allowed_prefix) for path in changed), "OUT_OF_SCOPE_GIT_CHANGE", failures)
    formal = rows(TASK_ROOT.parents[1] / "cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/benchmark/one_step_records.csv")
    require(len(formal) == 1440, "FORMAL_RECORD_COUNT_MISMATCH", failures)
    phase0 = json.loads((TASK_ROOT / "phase_manifests/phase0.json").read_text(encoding="utf-8"))
    require(phase0["status"] == "PASS_PHASE0_FROZEN" and not phase0["new_diagnostic_result_read_before_freeze"], "PHASE0_FREEZE_VIOLATION", failures)
    factors = json.loads((TASK_ROOT / "causes/causal_factor_registry.json").read_text(encoding="utf-8"))
    require(len(factors["factors"]) == 11, "FACTOR_COUNT_MISMATCH", failures)
    selection = json.loads((TASK_ROOT / "diagnostic_design/bounded_state_selection.json").read_text(encoding="utf-8"))
    require(selection["status"] == "PASS_C0_C1_SELECTION_FROZEN", "SELECTION_NOT_FROZEN", failures)
    for environment in FORMAL_ENVIRONMENTS:
        require(selection["environments"][environment]["c0_count"] <= 16, f"C0_LIMIT_{environment}", failures)
        require(selection["environments"][environment]["c1_count"] <= 16, f"C1_LIMIT_{environment}", failures)
    replay = rows(TASK_ROOT / "server_diagnostics/f11_deterministic_replay.csv")
    require(len(replay) == 768, "REPLAY_CALL_COUNT_MISMATCH", failures)
    require(all(row["match_formal"] == "True" for row in replay), "FORMAL_REPLAY_SEMANTIC_MISMATCH", failures)
    require(all(row.get("repeat_deterministic", "") == "True" for row in replay if row["repeat"] == "2"), "REPLAY_NONDETERMINISM", failures)
    formulas = rows(TASK_ROOT / "server_diagnostics/f04_position_first_formula.csv")
    require(len(formulas) == 96, "F04_FORMULA_ROW_COUNT", failures)
    for field in ("p_next_formula_max_abs_error", "v_next_formula_max_abs_error", "p_tau_control_independence_max_abs_error", "dp_tau_du_max_abs"):
        require(max(float(row[field]) for row in formulas) <= 1e-12, "F04_FORMULA_MISMATCH_" + field, failures)
    coverage = rows(TASK_ROOT / "server_diagnostics/f06_bounded_coverage.csv")
    require(len(coverage) == 80, "F06_COVERAGE_ROW_COUNT", failures)
    require(sum(row["outcome"] == "B2_PRIMARY_COMMITTED_NO_B3_SEARCH_REQUIRED" for row in coverage) == 22, "F06_B2_OUTCOME_MISMATCH", failures)
    require(sum(row["outcome"] == "PRECLUDED_BY_CANDIDATE_INDEPENDENT_NEGATIVE_CURRENT_MAP_H" for row in coverage) == 58, "F06_PRECLUSION_OUTCOME_MISMATCH", failures)
    manifest = json.loads((TASK_ROOT / "server_diagnostics/server_diagnostic_manifest.json").read_text(encoding="utf-8"))
    require(manifest["status"] == "PASS_SERVER_READONLY_DIAGNOSTICS", "SERVER_DIAGNOSTIC_STATUS", failures)
    require(manifest["replay_mismatch_count"] == 0, "SERVER_REPLAY_MISMATCH", failures)
    require(manifest["no_training"] and manifest["no_rollout"] and manifest["no_controller_loop"], "EXECUTION_BOUNDARY_VIOLATION", failures)
    figures = sorted((TASK_ROOT / "figures").glob("*.png"))
    require(len(figures) == 28, "FIGURE_COUNT_MISMATCH", failures)
    decision = json.loads((TASK_ROOT / "decision/final_causal_decision.json").read_text(encoding="utf-8"))
    require(decision["status"] == "PASS_MULTIFACTOR_CORE_V1_SHORTFALL_DECOMPOSITION", "FINAL_STATUS_MISMATCH", failures)
    require(decision["case"] == "D", "FINAL_CASE_MISMATCH", failures)
    require(decision["next_authorized_task"] == "RANK_CORE_V1_ACTIONABLE_FACTORS_AND_SELECT_ONE_BOUNDED_NEXT_STEP_V1", "NEXT_TASK_MISMATCH", failures)
    require((TASK_ROOT / "report/REPORT_AUDIT_CORE_V1_REPRESENTATIVE_SHORTFALL_CAUSAL_DECOMPOSITION_V1.md").is_file(), "REPORT_MISSING", failures)
    output = {
        "status": "PASS_CORE_V1_REPRESENTATIVE_SHORTFALL_CAUSAL_DECOMPOSITION_VALIDATION" if not failures else "FAIL_CORE_V1_REPRESENTATIVE_SHORTFALL_CAUSAL_DECOMPOSITION_VALIDATION",
        "failures": failures, "branch": branch, "base_head": BASE_HEAD,
        "task_tree_sha256": sha256_file(TASK_ROOT / "decision/final_causal_decision.json"),
        "formal_training_or_rollout_started": False,
    }
    write_json(TASK_ROOT / "report/validation_result.json", output)
    print(output["status"], len(failures))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
