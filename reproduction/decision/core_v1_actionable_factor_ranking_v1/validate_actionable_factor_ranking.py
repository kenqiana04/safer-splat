"""Fail-closed validator for the Core V1 actionable-factor ranking package."""

from __future__ import annotations

import csv
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from task_config import EXPECTED_PRS, FIGURES, FATAL_GATES, TASK_ROOT


def fail(message: str) -> None:
    raise AssertionError(message)


def read_json(relative: str) -> object:
    return json.loads((TASK_ROOT / relative).read_text(encoding="utf-8"))


def read_csv(relative: str) -> list[dict[str, str]]:
    with (TASK_ROOT / relative).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    required = [
        "RANK_CORE_V1_ACTIONABLE_FACTORS_AND_SELECT_ONE_BOUNDED_NEXT_STEP_V1.md", "IMPLEMENTATION_PLAN.md", "task_config.py", "freeze_upstream_inputs.py",
        "input_freeze/protected_source_hashes.json", "input_freeze/source_evidence_index.json", "actions/action_package_registry.json",
        "dependencies/dependency_graph.json", "dependencies/dependency_matrix.csv", "dependencies/fatal_dependency_audit.csv",
        "scoring/scoring_contract.json", "scoring/positive_scores.csv", "scoring/risk_scores.csv", "scoring/net_scores.csv", "scoring/fatal_gate_audit.csv",
        "feasibility/effort_estimates.csv", "feasibility/five_day_decision_paths.csv", "feasibility/asset_dependencies.csv", "feasibility/data_dependencies.csv",
        "checks/a1_math_prerequisite.md", "checks/a2_asset_availability.csv", "checks/a3_eligible_state_inventory.csv", "checks/a4_regime_legitimacy.md",
        "reviews/reviewer_score_matrix.csv", "reviews/disagreement_analysis.md", "decision/final_action_selection.json", "decision/selection_rationale.md",
        "decision/rejected_actions.md", "decision/anti_drift_contract.md", "decision/next_task_contract.md", "report/REPORT_RANK_CORE_V1_ACTIONABLE_FACTORS_AND_SELECT_ONE_BOUNDED_NEXT_STEP_V1.md",
        "report/DRAFT_PR_BODY.md", "report/downstream_handoff.json", "report/operational_state.json", "capture_operational_state.py", "validate_actionable_factor_ranking.py",
    ]
    required.extend([f"input_freeze/pr{n}_identity.json" for n in EXPECTED_PRS])
    required.extend([f"actions/action_cards/A{i}.md" for i in range(1, 6)])
    required.extend([f"reviews/{d}/{d}_review.md" for d in ("control_theory", "robotics_system", "evaluation_statistics", "novelty_publication")])
    required.extend([f"figures/{name}" for name in FIGURES])
    missing = [p for p in required if not (TASK_ROOT / p).is_file()]
    if missing: fail(f"missing required outputs: {missing}")

    for number, (branch, oid) in EXPECTED_PRS.items():
        payload = read_json(f"input_freeze/pr{number}_identity.json")
        if payload["headRefName"] != branch or payload["headRefOid"] != oid: fail(f"PR {number} identity mismatch")
        if payload["state"] != "OPEN" or payload["isDraft"] is not True or payload["mergedAt"] is not None: fail(f"PR {number} no longer preserved")

    protected = read_json("input_freeze/protected_source_hashes.json")
    if protected["status"] != "PASS_PROTECTED_SOURCE_BYTES_PRESERVED" or protected["record_count"] != 16: fail("protected-source audit failed")
    if any(row["verification"] != "PASS_RAW_GIT_OBJECT_MATCH" for row in protected["records"]): fail("protected bytes not verified")

    registry = read_json("actions/action_package_registry.json")
    if registry["status"] != "PRE_FROZEN_BEFORE_SCORING" or [p["id"] for p in registry["packages"]] != ["A1", "A2", "A3", "A4", "A5"]: fail("action packages not pre-frozen")
    contract = read_json("scoring/scoring_contract.json")
    if contract["formula"] != "net_score=positive_score-0.75*risk_penalty" or contract["sunk_cost_in_positive_score"]: fail("scoring contract drift")

    pos = {r["action"]: int(r["positive_score"]) for r in read_csv("scoring/positive_scores.csv")}
    risk = {r["action"]: int(r["risk_penalty"]) for r in read_csv("scoring/risk_scores.csv")}
    net = {r["action"]: float(r["net_score"]) for r in read_csv("scoring/net_scores.csv")}
    for action in ("A1", "A2", "A3", "A4", "A5"):
        if abs(net[action] - (pos[action] - .75 * risk[action])) > 1e-9: fail(f"net arithmetic failed for {action}")
    if max(net, key=net.get) != "A1": fail("A1 is not score leader")

    gates = read_csv("scoring/fatal_gate_audit.csv")
    if len(gates) != 60 or {r["gate"] for r in gates} != set(FATAL_GATES): fail("fatal gate audit incomplete")
    a1 = [r for r in gates if r["action"] == "A1"]
    if any(r["status"] != "PASS" for r in a1): fail("A1 fatal gate failure")
    for blocked in ("A2", "A3", "A4"):
        if not any(r["action"] == blocked and r["gate"] == "G10" and r["status"] == "FAIL" for r in gates): fail(f"{blocked} dependency gate missing")

    graph = read_json("dependencies/dependency_graph.json")
    edges = {(e["from"], e["to"]): e["status"] for e in graph["edges"]}
    for target in ("A2", "A3", "A4"):
        if edges.get(("A1", target)) != "REQUIRED": fail(f"A1 dependency missing for {target}")
    if "A1_REQUIRED_COMMON_PREREQUISITE=TRUE" not in (TASK_ROOT / "checks/a1_math_prerequisite.md").read_text(encoding="utf-8"): fail("A1 math prerequisite not answered")
    eligible = read_csv("checks/a3_eligible_state_inventory.csv")
    if eligible[-1]["eligible_states"] != "0": fail("A3 inventory must remain read-only with zero eligible states")
    if any(r["status"] != "ABSENT" for r in read_csv("checks/a2_asset_availability.csv")[:4]): fail("A2 availability unexpectedly changed")
    if "VALID_REGIME_ANALYSIS=NOT_YET_SUPPORTED" not in (TASK_ROOT / "checks/a4_regime_legitimacy.md").read_text(encoding="utf-8"): fail("A4 legitimacy check incomplete")

    reviews = read_csv("reviews/reviewer_score_matrix.csv")
    if len(reviews) != 4 or sum(r["top1"] == "A1" for r in reviews) != 3: fail("reviewer panel does not support A1 3/4")
    decision = read_json("decision/final_action_selection.json")
    if decision["selected_case"] != "CASE_A1" or decision["selected_action_package"] != "A1": fail("wrong final case")
    if decision["Only_next_task"] != "WRITE_CORE_CAUSAL_ARCHITECTURE_SPECIFICATION_V1": fail("not exactly one next task")
    report = (TASK_ROOT / "report/REPORT_RANK_CORE_V1_ACTIONABLE_FACTORS_AND_SELECT_ONE_BOUNDED_NEXT_STEP_V1.md").read_text(encoding="utf-8")
    if "NO PERFORMANCE CLAIM" not in (TASK_ROOT / "figures/figure_manifest.json").read_text(encoding="utf-8") or "Only next task" not in report: fail("report/figures consistency failure")

    operational = read_json("report/operational_state.json")
    if operational["status"] != "PASS_READ_ONLY_OPERATIONAL_PRESERVATION" or operational["task_owned_compute_process_count"] != 0: fail("GPU/process or operational preservation failure")
    if operational["formal_method_run_count"] != 0 or operational["forbidden_actions_executed"]: fail("no-execution boundary failed")

    repo = TASK_ROOT.parents[2]
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True, encoding="utf-8")
    allowed = "reproduction/decision/core_v1_actionable_factor_ranking_v1/"
    changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=repo, text=True, encoding="utf-8").splitlines()
    untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=repo, text=True, encoding="utf-8").splitlines()
    if any(path.replace("\\", "/") and not path.replace("\\", "/").startswith(allowed) for path in [*changed, *untracked]): fail("mutation outside task directory")
    whitespace = subprocess.run(["git", "diff", "--check"], cwd=repo, text=True, capture_output=True, encoding="utf-8", check=False)
    if whitespace.returncode != 0 or whitespace.stdout.strip(): fail("git diff --check failed")
    with tempfile.TemporaryDirectory() as bytecode_root:
        compile_env = {**os.environ, "PYTHONPYCACHEPREFIX": bytecode_root}
        compile_result = subprocess.run([sys.executable, "-B", "-m", "compileall", "-q", str(TASK_ROOT)], text=True, capture_output=True, check=False, env=compile_env)
        if compile_result.returncode != 0: fail("compileall failed")
    for path in TASK_ROOT.rglob("*"):
        if path.is_file() and path.stat().st_size > 2_000_000: fail(f"large asset prohibited: {path}")
        if path.is_file() and re.search(r"(?:hf_|ghp_|github_pat_)[A-Za-z0-9_-]{10,}", path.read_text(encoding="utf-8", errors="ignore")): fail(f"credential-like content: {path}")

    result = {"status": "PASS_CORE_V1_ACTIONABLE_FACTOR_RANKING_VALIDATION", "checks": 24, "selected_case": "CASE_A1", "Only_next_task": decision["Only_next_task"], "formal_method_runs": 0, "pytest_available": importlib.util.find_spec("pytest") is not None, "pytest_check": "available" if importlib.util.find_spec("pytest") is not None else "unavailable; stdlib unittest fallback required"}
    (TASK_ROOT / "report" / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["status"])


if __name__ == "__main__":
    main()
