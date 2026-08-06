"""Fail-closed validator for the SAFER-Splat direction audit V1."""

from __future__ import annotations

import csv
import json
import os
import py_compile
import re
import subprocess
import sys
from pathlib import Path

from task_config import (
    DIRECTIONS,
    EXECUTION_COUNTS,
    FATAL_GATES,
    METHOD_THRESHOLDS,
    POSITIVE_WEIGHTS,
    RISK_WEIGHTS,
    UPSTREAM,
)

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
PASS_STATUS = "PASS_SAFER_SPLAT_RESEARCH_DIRECTION_DUE_DILIGENCE_VALIDATION"


def load_json(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def csv_rows(relative: str):
    with (ROOT / relative).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def run(command: list[str], *, env=None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=REPO, text=True, encoding="utf-8", capture_output=True, env=env)


def check(condition: bool, name: str, detail: str = "") -> dict[str, object]:
    return {"check": name, "passed": bool(condition), "detail": detail}


def main() -> int:
    checks: list[dict[str, object]] = []
    required = [
        "AUDIT_SAFER_SPLAT_RESEARCH_DIRECTION_NOVELTY_DATA_AND_WINNABILITY_V1.md",
        "IMPLEMENTATION_PLAN.md", "task_config.py", "freeze_upstream_inputs.py",
        "history/workstream_ledger.csv", "history/evidence_asset_inventory.csv", "history/falsified_hypotheses.csv",
        "history/reusable_artifact_manifest.json", "history/claim_boundary_registry.csv", "history/timeline.md",
        "literature/search_protocol.md", "literature/search_queries.csv", "literature/screening_log.csv",
        "literature/included_papers.csv", "literature/excluded_papers.csv", "literature/snowballing_log.csv",
        "literature/source_archive_manifest.json", "literature/fulltext_evidence_matrix.csv",
        "literature/baseline_availability.csv", "literature/claim_to_source_map.json",
        "data/map_readiness_matrix.csv", "data/reference_authority_matrix.csv", "data/query_event_rate_contract.md",
        "data/query_event_rate_records.csv", "data/event_rate_summary.csv", "data/split_feasibility.csv", "data/data_blockers.json",
        "candidates/candidate_direction_registry.json", "feasibility/asset_dependency_graph.json",
        "feasibility/effort_estimates.csv", "feasibility/eight_week_critical_path.csv", "feasibility/external_dependency_risks.csv",
        "scoring/scoring_contract.json", "scoring/positive_scores.csv", "scoring/risk_scores.csv", "scoring/net_scores.csv",
        "scoring/fatal_gate_audit.csv", "reviews/reviewer_score_matrix.csv", "reviews/disagreement_analysis.md",
        "decision/venue_fit_matrix.csv", "decision/submission_timeline.md", "decision/anti_drift_contract.md",
        "decision/final_direction_decision.json", "decision/frozen_problem_statement.md", "decision/frozen_eight_week_plan.md",
        "decision/two_week_falsifiability_gate.md", "audits/selection_bias_audit.json",
        "audits/literature_completeness_audit.json", "audits/data_leakage_audit.json", "audits/claim_evidence_audit.json",
        "audits/operational_autonomy_actions.json", "audits/system_state.json", "report/downstream_handoff.json",
        "report/REPORT_AUDIT_SAFER_SPLAT_RESEARCH_DIRECTION_NOVELTY_DATA_AND_WINNABILITY_V1.md", "report/DRAFT_PR_BODY.md",
    ]
    missing = [p for p in required if not (ROOT / p).is_file()]
    checks.append(check(not missing, "required_files", ",".join(missing)))

    live = load_json("input_freeze/github_pr_state_verification.json")
    expected = {84: "04ebca2b1b35124ad0e61ebed96e491c9edae4bb", 85: "7afef38392bec36d9d9811e5a22c816da5faf1ff", 86: "d4f20f44a810afc2d6379853a286a3e18b175221", 87: "fbe67f0c607add7f8049d4ce75e8f9e1ae8498d9"}
    pr_ok = live["status"].startswith("PASS") and all(x["state"] == "OPEN" and x["is_draft"] and x["mergeable"] == "MERGEABLE" and x["head_sha"] == expected[x["number"]] for x in live["pull_requests"])
    checks.append(check(pr_ok, "pr_84_87_identities_and_state"))
    objects_ok = all(run(["git", "cat-file", "-e", f"{sha}^{{commit}}"]).__dict__["returncode"] == 0 for sha in UPSTREAM.values())
    checks.append(check(objects_ok, "upstream_objects_preserved"))

    changed = run(["git", "diff", "--name-only", UPSTREAM[87], "--"]).stdout.splitlines()
    out_of_scope = [p for p in changed if p and not p.replace("\\", "/").startswith("reproduction/research_direction/safer_splat_direction_audit_v1/")]
    checks.append(check(not out_of_scope, "no_protected_source_mutation", ",".join(out_of_scope)))
    checks.append(check(all(value == 0 for value in EXECUTION_COUNTS.values()), "zero_training_map_controller_method_navigation_mutations"))

    queries = csv_rows("literature/search_queries.csv")
    clusters = {r["query_id"] for r in queries if r["round"] == "A"}
    checks.append(check(len(queries) == 36 and clusters == {f"L{i}" for i in range(1, 25)} and {r["round"] for r in queries} == {"A", "B"}, "literature_queries_rounds_dates"))
    checks.append(check(all(r["search_date"] == "2026-08-06" and r["exact_query"] and r["source"] and r["result_count"] for r in queries), "literature_query_fields_complete"))
    screened = csv_rows("literature/screening_log.csv")
    included = csv_rows("literature/included_papers.csv")
    excluded = csv_rows("literature/excluded_papers.csv")
    evidence = csv_rows("literature/fulltext_evidence_matrix.csv")
    checks.append(check(len(screened) == len(included) + len(excluded), "included_excluded_reconcile"))
    full_ids = {r["dedup_key"] for r in evidence}
    card_ids = {p.stem for p in (ROOT / "literature/competitor_cards").glob("*.md")}
    checks.append(check(len(evidence) == 15 and full_ids == card_ids and all(r["source_pointer"] for r in evidence), "fulltext_evidence_and_cards"))
    sources = load_json("literature/source_archive_manifest.json")
    checks.append(check(sources["source_count"] == 15 and all(s["sha256"] and s["pages"] > 0 and s["committed"] is False for s in sources["sources"]), "primary_source_archive_manifest"))
    claim_map = load_json("literature/claim_to_source_map.json")["claims"]
    included_ids = {r["dedup_key"] for r in included}
    checks.append(check(all(set(ids) <= included_ids for ids in claim_map.values()), "claim_to_source_consistency"))

    candidates = load_json("candidates/candidate_direction_registry.json")
    checks.append(check(candidates["candidate_count"] == 9 and [x["id"] for x in candidates["candidates"]] == list(DIRECTIONS), "candidate_set_prefrozen"))
    contract = load_json("scoring/scoring_contract.json")
    checks.append(check(sum(POSITIVE_WEIGHTS.values()) == 100 and sum(RISK_WEIGHTS.values()) == 100 and contract["positive_weights"] == POSITIVE_WEIGHTS and contract["risk_weights"] == RISK_WEIGHTS and contract["thresholds"] == METHOD_THRESHOLDS, "scoring_contract_weights_unchanged"))
    gate_rows = csv_rows("scoring/fatal_gate_audit.csv")
    gate_ok = all(len([r for r in gate_rows if r["direction"] == d]) == 10 and any(r["result"] == "FAIL" for r in gate_rows if r["direction"] == d) for d in list(DIRECTIONS)[1:])
    checks.append(check(gate_ok and {r["gate"] for r in gate_rows} == set(FATAL_GATES), "fatal_gates_not_lowered"))

    event = csv_rows("data/query_event_rate_records.csv")
    event_ok = len(event) == 320 and {r["cohort"] for r in event} == {"REPRESENTATIVE_HOLDOUT"} and sum(r["query_type"] == "point" for r in event) == 160 and sum(r["query_type"] == "short_segment" for r in event) == 160
    checks.append(check(event_ok, "event_sampling_contract_and_counts"))
    checks.append(check(load_json("audits/selection_bias_audit.json")["activated_cohort_excluded"] is True, "no_selection_leakage"))
    refs = csv_rows("data/reference_authority_matrix.csv")
    checks.append(check(len(refs) == 9 and all(r["authority_tier"] in {"A", "A/B", "B", "C", "D"} for r in refs), "reference_authority_layered"))
    splits = csv_rows("data/split_feasibility.csv")
    checks.append(check(len(splits) == 8 and all(r["status"] == "FAIL" for r in splits), "cross_map_split_honestly_blocked"))

    reviews = csv_rows("reviews/reviewer_score_matrix.csv")
    review_files = list((ROOT / "reviews").glob("D*/*_review.md"))
    reviews_independent = len(reviews) == 12 and len(review_files) == 12 and all("withheld from the review prompt" in p.read_text(encoding="utf-8") for p in review_files)
    checks.append(check(reviews_independent, "independent_role_reviews"))
    decision = load_json("decision/final_direction_decision.json")
    decision_ok = decision["case"] == "D" and decision["selected_direction"] == "D0" and decision["selected_direction_count"] == 1 and decision["directions_passing_all_new_method_gates"] == [] and decision["no_threshold_relaxation"] is True
    checks.append(check(decision_ok, "case_d_decision_rule"))
    checks.append(check((ROOT / "decision/anti_drift_contract.md").is_file() and (ROOT / "decision/frozen_eight_week_plan.md").is_file(), "eight_week_plan_and_anti_drift"))
    checks.append(check(len(list((ROOT / "figures").glob("*.png"))) == 24, "required_figures"))

    report = (ROOT / "report/REPORT_AUDIT_SAFER_SPLAT_RESEARCH_DIRECTION_NOVELTY_DATA_AND_WINNABILITY_V1.md").read_text(encoding="utf-8")
    checks.append(check(all(f"| {n} |" in report for n in range(1, 64)), "report_63_fields"))
    checks.append(check(decision["final_status"] in report and decision["final_decision"] in report and decision["only_next_task"] in report, "report_decision_consistency"))

    secret_pattern = re.compile(r"(?:hf_[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|BEGIN (?:RSA|OPENSSH) PRIVATE KEY|Authorization:\s*Bearer\s+[A-Za-z0-9._-]{12,})")
    secret_hits = []
    large_nonfigure = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".cache" in path.parts or "__pycache__" in path.parts:
            continue
        if path.suffix.lower() != ".png" and path.stat().st_size > 2_000_000:
            large_nonfigure.append(str(path.relative_to(ROOT)))
        if path.suffix.lower() in {".md", ".csv", ".json", ".py", ".txt"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            if secret_pattern.search(text):
                secret_hits.append(str(path.relative_to(ROOT)))
    checks.append(check(not secret_hits, "no_credentials", ",".join(secret_hits)))
    committed_candidate_pdfs = [p for p in ROOT.glob("**/*.pdf") if ".cache" not in p.parts]
    checks.append(check(not large_nonfigure and not committed_candidate_pdfs, "no_large_pdfs_or_datasets_committed", ",".join(large_nonfigure)))
    system = load_json("audits/system_state.json")
    system_ok = system["gpu_1"]["compute_process_count"] == 0 and system["task_owned_remote_compute_process_count"] == 0 and system["local_watchdog"]["unchanged_by_task"] and system["remote_proxy_listener"]["unchanged_by_task"]
    checks.append(check(system_ok, "gpu_process_watchdog_ssh_clean"))

    compile_errors = []
    for path in ROOT.rglob("*.py"):
        if ".cache" in path.parts:
            continue
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            compile_errors.append(str(exc))
    checks.append(check(not compile_errors, "compileall_equivalent", " | ".join(compile_errors)))

    pytest_root = ROOT / ".cache" / "pytest_runtime"
    env = os.environ.copy()
    if pytest_root.is_dir():
        env["PYTHONPATH"] = str(pytest_root) + os.pathsep + env.get("PYTHONPATH", "")
    pytest_run = run([sys.executable, "-m", "pytest", "-q", str(ROOT / "tests")], env=env)
    checks.append(check(pytest_run.returncode == 0, "pytest", (pytest_run.stdout + pytest_run.stderr).strip()[-2000:]))
    diff_check = run(["git", "diff", "--check"])
    cached_diff_check = run(["git", "diff", "--cached", "--check"])
    checks.append(check(diff_check.returncode == 0 and cached_diff_check.returncode == 0, "git_diff_check", diff_check.stdout + diff_check.stderr + cached_diff_check.stdout + cached_diff_check.stderr))

    failures = [c for c in checks if not c["passed"]]
    result = {
        "status": PASS_STATUS if not failures else "FAIL_SAFER_SPLAT_RESEARCH_DIRECTION_DUE_DILIGENCE_VALIDATION",
        "check_count": len(checks),
        "failure_count": len(failures),
        "checks": checks,
        "execution_counts": EXECUTION_COUNTS,
        "scientific_decision": decision,
    }
    target = ROOT / "report" / "validation_result.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    if failures:
        for failure in failures:
            print(f"FAIL {failure['check']}: {failure['detail']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
