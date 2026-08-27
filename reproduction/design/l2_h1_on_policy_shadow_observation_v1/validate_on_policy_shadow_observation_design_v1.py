#!/usr/bin/env python3
"""Static validator for the L2/H1 on-policy shadow observation design.

The validator reads task-local documentation, schemas, mock fixtures, Git
metadata, and frozen identity audits. It never imports or runs production code.
"""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
UPSTREAM = "a7fd936804284a299467f1bfcc76deab12fdf0c3"
PASS = "PASS_L2_H1_ON_POLICY_SHADOW_OBSERVATION_DESIGN_VALIDATION"
TASK_PREFIX = "reproduction/design/l2_h1_on_policy_shadow_observation_v1/"

REQUIRED = [
    "README.md", "ON_POLICY_SHADOW_OBSERVATION_PROTOCOL_V1.md",
    "CONTROL_FLOW_OBSERVATION_SEAM_AUDIT.md", "control_flow_observation_seams.json",
    "observation_architecture_comparison.csv", "SELECTED_OBSERVATION_ARCHITECTURE.md",
    "ZERO_AUTHORITY_CONTRACT.md", "STATE_ACTION_ALIGNMENT_CONTRACT.md",
    "prospective_step_schema.json", "native_candidate_schema.json",
    "map_authority_manifest_schema.json", "observer_health_schema.json",
    "reachability_reason_schema.json", "PROSPECTIVE_DENOMINATOR_CONTRACT.md",
    "prospective_analysis_plan.md", "sample_size_and_stopping_rule.md",
    "future_trial_manifest_policy.md", "future_equivalence_gate_spec.md",
    "future_logging_completeness_gate.md", "future_validation_plan.md",
    "kill_gates.json", "claims_contract.md", "frozen_replay_to_prospective_gap_mapping.csv",
    "reviewer/control_theory_review.json", "reviewer/robotics_systems_review.json",
    "reviewer/statistics_evaluation_review.json", "reviewer/software_architecture_review.json",
    "FINAL_CASE_DECISION.json", "run_manifest.json", "validation_result.json",
    "downstream_handoff.json", "DRAFT_PR_BODY.md",
    "validate_on_policy_shadow_observation_design_v1.py",
    "report/REPORT_DESIGN_L2_H1_ON_POLICY_SHADOW_OBSERVATION_V1.md",
]


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def require(condition: bool, message: str, checks: list[str]) -> None:
    if not condition:
        raise AssertionError(message)
    checks.append(message)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, text=True).stdout


def main() -> int:
    checks: list[str] = []

    for relative in REQUIRED:
        require((ROOT / relative).is_file(), f"required artifact exists: {relative}", checks)

    upstream = load_json("audit/upstream_pr_identity.json")
    require(upstream["upstream_pr_count"] == 11, "upstream PR count is 11", checks)
    require(upstream["pr95_expected_head"] == UPSTREAM, "PR95 expected head frozen", checks)
    require(upstream["pr95_actual_head"] == UPSTREAM, "PR95 actual head exact", checks)
    require(upstream["pr95_state"] == "OPEN" and upstream["pr95_is_draft"] is True, "PR95 remains Open Draft", checks)
    require(all(item["identity_match"] for item in upstream["prs"]), "all upstream PR identities preserved", checks)

    start = load_json("audit/protected_source_start.json")
    end = load_json("audit/protected_source_end.json")
    require(start["protected_blob_count"] == 17 == end["protected_blob_count"], "protected blob count is 17", checks)
    require(start["records"] == end["records"], "protected raw blob/size/mode audit stable", checks)
    require(start["protected_path_diff_count"] == 0 == end["protected_path_diff_count"], "protected path diff count is zero", checks)

    status_lines = [line[3:].replace("\\", "/") for line in git("status", "--porcelain=v1", "--untracked-files=all").splitlines()]
    require(all(path.startswith(TASK_PREFIX) for path in status_lines), "all worktree mutations are task-local", checks)

    manifest = load_json("run_manifest.json")
    counts = manifest["counts"]
    zero_counts = [
        "on_policy_collection_count", "navigation_rollout_count", "new_state_collection_count",
        "new_candidate_generation_count", "new_map_generation_count", "controller_mutation_count",
        "production_instrumentation_mutation_count", "shadow_certifier_mutation_count",
        "dynamics_mutation_count", "map_mutation_count", "formal_performance_metric_count",
        "formal_runtime_metric_count",
    ]
    require(all(counts[key] == 0 for key in zero_counts), "all collection/runtime/production mutation counts are zero", checks)
    require(counts["selected_observation_architecture_count"] == 1, "exactly one observation architecture selected", checks)
    require(counts["reviewer_count"] == 4, "four reviewer passes present", checks)
    require(counts["future_kill_gate_count"] >= 8, "at least eight kill gates designed", checks)

    seams = load_json("control_flow_observation_seams.json")
    source = seams["source_audit"]
    for key in ("state", "nominal_candidate", "selected_candidate", "dt", "plant_update", "map", "trial_step", "l0", "l1", "native_multi_candidate"):
        require(key in source, f"seam source identified: {key}", checks)
    require(seams["selected_seam"] == "S1_AFTER_ACCEPT_BEFORE_PROPAGATE", "post-commit/pre-propagation seam selected", checks)
    require(seams["candidate_synthesis_count"] == 0, "candidate synthesis count zero", checks)

    with (ROOT / "observation_architecture_comparison.csv").open(encoding="utf-8", newline="") as handle:
        architectures = list(csv.DictReader(handle))
    require(len(architectures) >= 3, "at least three observation architectures compared", checks)
    require(sum(row["decision"] == "SELECTED" for row in architectures) == 1, "architecture comparison has one selection", checks)
    require(sum(row["decision"] == "FALLBACK" for row in architectures) == 1, "architecture comparison has one fallback", checks)

    step_schema = load_json("prospective_step_schema.json")
    valid = load_json("fixtures/valid_step.json")
    invalid = load_json("fixtures/invalid_missing_u_k.json")
    jsonschema.Draft202012Validator.check_schema(step_schema)
    jsonschema.validate(valid, step_schema)
    invalid_rejected = False
    try:
        jsonschema.validate(invalid, step_schema)
    except jsonschema.ValidationError:
        invalid_rejected = True
    require(invalid_rejected, "missing u_k fixture fails closed", checks)
    require("u_k" in step_schema["properties"]["selected_candidate"]["required"], "u_k is mandatory", checks)
    require("l2" in step_schema["required"] and "map_authority" in step_schema["required"], "L2 and map authority mandatory", checks)
    authority_props = step_schema["properties"]["authority"]["properties"]
    require(all(spec.get("const") is False for spec in authority_props.values()), "all shadow authority fields are false", checks)
    require(step_schema["properties"]["l2"]["properties"]["shadow_only"]["const"] is True, "L2 result shadow-only", checks)
    require("UNKNOWN" in step_schema["$defs"]["triState"]["enum"], "L2 tri-state includes UNKNOWN", checks)
    require("OBSERVATION_INCOMPLETE" in step_schema["properties"]["instrumentation"]["properties"]["observation_completeness"]["enum"], "observation incomplete is separate", checks)

    for schema_file in ("native_candidate_schema.json", "map_authority_manifest_schema.json", "observer_health_schema.json", "reachability_reason_schema.json"):
        jsonschema.Draft202012Validator.check_schema(load_json(schema_file))
        checks.append(f"valid JSON schema: {schema_file}")
    native = load_json("native_candidate_schema.json")
    require(native["properties"]["candidate_synthesis_count"]["const"] == 0, "native schema prohibits synthesis", checks)
    require(native["properties"]["candidates"]["items"]["properties"]["existed_before_shadow_observation"]["const"] is True, "candidate provenance mandatory", checks)

    denominator = (ROOT / "PROSPECTIVE_DENOMINATOR_CONTRACT.md").read_text(encoding="utf-8")
    for token in ("N_control_steps_all", "N_L2_selected_evaluated", "primary_future_fail_signal_rate", "logging_completeness", "N_observation_dropped"):
        require(token in denominator, f"denominator token defined: {token}", checks)

    analysis = (ROOT / "prospective_analysis_plan.md").read_text(encoding="utf-8")
    require("selected/executed" in analysis and "trial-cluster bootstrap" in analysis, "executed primary and cluster-aware analysis defined", checks)
    require("No result-dependent" in analysis, "outcome-conditioned sampling prohibited", checks)
    stopping = (ROOT / "sample_size_and_stopping_rule.md").read_text(encoding="utf-8")
    require("Plan A" in stopping and "Plan B" in stopping and "never" in stopping.lower(), "two stopping plans avoid FAIL-count stopping", checks)
    phases = (ROOT / "future_validation_plan.md").read_text(encoding="utf-8")
    require(all(f"Phase {index}" in phases for index in range(5)), "future phases 0-4 separated", checks)

    zero_authority = (ROOT / "ZERO_AUTHORITY_CONTRACT.md").read_text(encoding="utf-8")
    require("no result-return interface" in zero_authority.lower(), "zero-feedback return path absent", checks)
    require("continues the frozen path" in zero_authority.lower(), "observer failure preserves controller path", checks)
    equivalence = (ROOT / "future_equivalence_gate_spec.md").read_text(encoding="utf-8")
    for token in ("control_trace_equivalence", "selected_candidate_hash_equivalence", "trial_seed_equivalence", "map_identity_equivalence", "controller_return_value_equivalence"):
        require(token in equivalence, f"equivalence metric defined: {token}", checks)

    kill_gates = load_json("kill_gates.json")
    gate_ids = {gate["id"] for gate in kill_gates["gates"]}
    required_gates = {"G1_CONTROL_TRACE_EQUIVALENCE", "G2_U_K_COMPLETENESS", "G3_REACHABILITY_COMPLETENESS", "G4_MAP_AUTHORITY_COMPLETENESS", "G5_ZERO_FEEDBACK", "G6_QUEUE_NONBLOCKING", "G7_CANDIDATE_PROVENANCE", "G8_PROTOCOL_FREEZE"}
    require(required_gates <= gate_ids, "required future kill gates defined", checks)
    require(kill_gates["executed_in_this_task"] is False, "future kill gates not executed in design task", checks)

    reviewers = [load_json(path) for path in (
        "reviewer/control_theory_review.json", "reviewer/robotics_systems_review.json",
        "reviewer/statistics_evaluation_review.json", "reviewer/software_architecture_review.json",
    )]
    require(all(review["verdict"] == "PASS_DESIGN_ONLY" for review in reviewers), "all reviewers pass design-only", checks)
    require(all(review["critical_blockers"] == [] for review in reviewers), "reviewers have no critical blockers", checks)
    require(all(review["recommended_case"] == "CASE_A" for review in reviewers), "reviewer case vote is 4/4 Case A", checks)

    decision = load_json("FINAL_CASE_DECISION.json")
    require(decision["selected_case"] == "CASE_A", "Case A selected", checks)
    require(decision["final_status"] == "PASS_L2_H1_ON_POLICY_SHADOW_OBSERVATION_DESIGN_V1", "final design status exact", checks)
    require(decision["only_next_task"] == "IMPLEMENT_L2_H1_ON_POLICY_SHADOW_INSTRUMENTATION_V1", "only next task exact", checks)
    require(decision["unresolved_blockers"] == [], "no unresolved design blockers", checks)

    claims = load_json("claims_contract.md.json")
    for prohibited in ("collision reduction", "controller efficacy", "recursive feasibility", "deployment guarantee", "real-time guarantee"):
        require(prohibited in claims["prohibited"], f"prohibited claim explicit: {prohibited}", checks)
    require(claims["shadow_signal_is_control_efficacy"] is False, "shadow signal is not control efficacy", checks)

    report = (ROOT / "report/REPORT_DESIGN_L2_H1_ON_POLICY_SHADOW_OBSERVATION_V1.md").read_text(encoding="utf-8")
    require(all(f"**Q{index}." in report for index in range(1, 21)), "report starts with all 20 required questions", checks)
    require("Any synthetic candidates?** NO" in report, "report answers no synthetic candidates", checks)
    require("Did this task collect any on-policy data?** NO" in report, "report answers no on-policy data", checks)

    handoff = load_json("downstream_handoff.json")
    require(handoff["formal_collection_allowed"] is False and handoff["authority_granted_for_next_task"] is False, "handoff grants no collection or next-task authority", checks)

    result = {
        "validator": Path(__file__).name,
        "status": PASS,
        "check_count": len(checks),
        "checks": checks,
        "upstream_pr_count": upstream["upstream_pr_count"],
        "protected_blob_count": start["protected_blob_count"],
        "design_scope": "DESIGN_ONLY",
        "runtime_collection_executed": False,
        "production_mutation_executed": False,
        "selected_case": decision["selected_case"],
        "final_status": decision["final_status"],
    }
    (ROOT / "validation_result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(PASS)
    print("CHECK_COUNT", len(checks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
