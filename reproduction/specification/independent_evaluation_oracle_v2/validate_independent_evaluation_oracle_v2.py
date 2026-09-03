#!/usr/bin/env python3
"""Validate the V2 design freeze without running an evaluator or experiment."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
BASE = "5595e56b756291881fb9f6f17ba3d7551263574f"
PREFIX = "reproduction/specification/independent_evaluation_oracle_v2/"


def load(name: str):
    return json.loads((TASK / name).read_text(encoding="utf-8"))


def git(*args: str, binary: bool = False):
    return subprocess.check_output(["git", *args], cwd=REPO, text=not binary)


def main() -> int:
    inp = load("INDEPENDENT_EVALUATION_ORACLE_INPUT_LOCK.json")
    lock = load("INDEPENDENT_EVALUATION_ORACLE_EXECUTION_LOCK.json")
    auth = load("EVALUATION_ORACLE_AUTHORITY_V2.json")
    tiers = load("EVALUATION_CLAIM_TIERS_V2.json")
    trace = load("EVALUATION_TRACE_SCHEMA_V2.json")
    goal = load("GOAL_COMPLETION_ORACLE_V2.json")
    progress = load("PROGRESS_ORACLE_V2.json")
    unknown = load("EVALUATION_UNKNOWN_POLICY_V2.json")
    inv = load("INDEPENDENT_EVALUATION_ORACLE_INVARIANTS_V2.json")
    hierarchy = load("PRE_REGISTERED_OUTCOME_HIERARCHY_V2.json")
    anti = load("evaluation_oracle_independence_check.json")
    scenarios = load("ORACLE_SYNTHETIC_SCENARIOS_V2.json")
    gt = load("EXTERNAL_GROUND_TRUTH_ORACLE_AUDIT_V2.json")
    action = load("ACTION_ROLE_OUTCOME_ORACLE_V2.json")
    metrics = load("EVALUATION_METRIC_REGISTRY_V2.json")
    commit1 = lock["commit1"]

    frozen_blobs_ok = True
    for item in lock["frozen_artifacts"].values():
        full = PREFIX + item["path"]
        blob = git("rev-parse", f"{commit1}:{full}").strip()
        raw = git("cat-file", "blob", blob, binary=True)
        frozen_blobs_ok &= blob == item["git_blob_sha1"] and hashlib.sha256(raw).hexdigest() == item["sha256"]

    input_blobs_ok = True
    for item in inp["frozen_inputs"]:
        blob = git("rev-parse", f"{BASE}:{item['path']}").strip()
        raw = git("cat-file", "blob", blob, binary=True)
        input_blobs_ok &= blob == item["git_blob_sha1"] and hashlib.sha256(raw).hexdigest() == item["sha256"] and len(raw) == item["size"]

    diff_names = sorted(set(
        [x for x in git("diff", "--name-only", BASE, "HEAD").splitlines() if x]
        + [x for x in git("diff", "--name-only").splitlines() if x]
        + [x for x in git("diff", "--cached", "--name-only").splitlines() if x]
        + [x for x in git("ls-files", "--others", "--exclude-standard").splitlines() if x]
    ))
    production_diff_zero = all(x.startswith(PREFIX) for x in diff_names)
    required_step = set(trace["properties"]["steps"]["items"]["required"])
    checks = {
        "01_PR113_exact_upstream": inp["direct_upstream"]["head"] == BASE and git("merge-base", "--is-ancestor", BASE, "HEAD") == "" and input_blobs_ok,
        "02_execution_lock_raw_blobs": frozen_blobs_ok,
        "03_PR108_radii_separated": "0.015 m" in (TASK / "COLLISION_VS_MARGIN_ORACLE_V2.md").read_text(encoding="utf-8") and "0.025 m" in (TASK / "COLLISION_VS_MARGIN_ORACLE_V2.md").read_text(encoding="utf-8"),
        "04_PR109_execution_identity_compatible": "selected_action_vector" in required_step and "executed_action_vector" in required_step,
        "05_PR110_timing_nonclaims": "not a real-time guarantee" in (TASK / "RUNTIME_TIMING_EVALUATION_ORACLE_V2.md").read_text(encoding="utf-8"),
        "06_PR112_backup_separate": action["backup_and_alternative_counts_separate"] is True,
        "07_PR113_failclose_boundary": "SOFTWARE_FAIL_CLOSE != PHYSICAL_SAFE_STOP" in (TASK / "SAFE_STOP_EVALUATION_BOUNDARY_V2.md").read_text(encoding="utf-8"),
        "08_owner_unique_readonly_posthoc": auth["unique_owner"] == "POSTHOC_EVALUATION_ORACLE" and auth["read_only"] and not auth["ORACLE_FEEDBACK_AUTHORITY"],
        "09_legacy_runpy_audited": "LEGACY_RUN_PY_NOT_AUTHORIZED_AS_FINAL_V2_EVALUATION_ORACLE" in (TASK / "LEGACY_EVALUATION_SEMANTICS_AUDIT_V2.md").read_text(encoding="utf-8"),
        "10_collision_margin_separate": metrics["safety_liveness_separated"] and metrics["composite_score"] is None,
        "11_swept_segment_frozen": "swept-segment" in (TASK / "COLLISION_VS_MARGIN_ORACLE_V2.md").read_text(encoding="utf-8"),
        "12_goal_authority_resolved": goal["authority"] == "PRE_EXISTING_RUN_PY_EXPLICIT_GOAL_PREDICATE" and goal["tolerance"] == 0.001,
        "13_timeout_success_banned": goal["timeout_alone_is_success"] is False,
        "14_progress_preregistered": progress["outcome_adaptation"] is False and progress["clipping"] == "NONE",
        "15_action_roles_explicit": len(action["roles"]) == 6 and action["zero_vector_heuristic_forbidden"],
        "16_unknown_typed": unknown["EVAL_UNKNOWN_IS_SAFE"] is False and unknown["unknown_trials_retained_in_accounting"],
        "17_external_GT_tier_explicit": not gt["physical_collision_claim_authorized"] and tiers["tiers"]["TIER_B_INDEPENDENT_REPRESENTED_MAP_OUTCOME"]["scope_label"] == "REPRESENTED_MAP_RELATIVE",
        "18_no_composite_score": metrics["composite_score"] is None,
        "19_trial_primary_unit": "trial is the primary independent statistical unit" in (TASK / "STATISTICAL_AGGREGATION_CONTRACT_V2.md").read_text(encoding="utf-8"),
        "20_paired_comparability": "trial/start/goal identities" in (TASK / "VARIANT_COMPARABILITY_CONTRACT_V2.md").read_text(encoding="utf-8"),
        "21_primary_hierarchy": hierarchy["primary"]["safety"]["tier"] == "TIER_B" and not hierarchy["internal_L2_PASS_rate_is_primary_safety_efficacy"],
        "22_EO_01_through_26": [x["id"] for x in inv["invariants"]] == [f"EO-{i:02d}" for i in range(1, 27)],
        "23_anti_circularity_PASS": anti["status"] == "PASS_EVALUATION_ORACLE_ANTI_CIRCULARITY_CHECK" and not anti["forbidden_edge_hits"],
        "24_synthetic_scenarios_PASS": scenarios["count"] >= 20 and len({x["id"] for x in scenarios["scenarios"]}) == scenarios["count"],
        "25_production_runtime_diff_zero": production_diff_zero,
        "26_no_experiment_execution": all(inp[k] == 0 for k in ["outcome_data_read_count", "trial_execution_count", "gpu_execution_count", "runtime_implementation_count"]),
    }
    result = {
        "status": "PASS_INDEPENDENT_EVALUATION_ORACLE_V2_VALIDATION" if all(checks.values()) else "FAIL_INDEPENDENT_EVALUATION_ORACLE_V2_VALIDATION",
        "checks": checks,
        "pass_count": sum(checks.values()),
        "check_count": len(checks),
        "production_runtime_diff_count": 0 if production_diff_zero else len([x for x in diff_names if not x.startswith(PREFIX)]),
        "scientific_execution_counts": {"outcome_data_read": 0, "trial": 0, "gpu": 0, "runtime_implementation": 0},
    }
    (TASK / "validation_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(result["status"])
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
