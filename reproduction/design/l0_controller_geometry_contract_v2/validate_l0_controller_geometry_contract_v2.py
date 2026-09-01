#!/usr/bin/env python3
"""Validate the design-only L0/controller geometry contract V2 artifacts."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any


EXPECTED_UPSTREAM = "3c2ad6122d61436c845cb449c41fae0cd2c1608f"
EXPECTED_PARENT = "14c844adeda8a0e8eb418abcdbaac62c701e2910"
TASK_RELATIVE = Path("reproduction/design/l0_controller_geometry_contract_v2")
PASS_STATUS = "PASS_L0_CONTROLLER_GEOMETRY_CONTRACT_V2_DESIGN_VALIDATION"


def validate_contract_dict(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    source = contract.get("controller_radius_source", {})
    if contract.get("controller_geometry_authority") != "CONTROLLER_GEOMETRY_AUTHORITY":
        errors.append("BASE_RADIUS_AUTHORITY_NOT_CONTROLLER")
    if not source.get("resolved") or not source.get("unique"):
        errors.append("CONTROLLER_RADIUS_AUTHORITY_UNRESOLVED")
    if contract.get("independent_l0_base_radius_m") is not None:
        errors.append("DUPLICATE_BASE_RADIUS")
    if contract.get("margin_application_count") != 1:
        errors.append("MARGIN_APPLICATION_COUNT_NOT_ONE")
    expected = float(contract.get("controller_radius_m", math.nan)) + float(contract.get("certification_margin_m", math.nan))
    if not math.isclose(float(contract.get("effective_l0_radius_m", math.nan)), expected, rel_tol=0.0, abs_tol=1e-15):
        errors.append("EFFECTIVE_RADIUS_COMPOSITION_MISMATCH")
    if contract.get("composition_rule") != "r_L0_eff = r_controller + m_cert":
        errors.append("COMPOSITION_RULE_MISMATCH")
    if contract.get("parameter_selection", {}).get("sentinel_driven") is not False:
        errors.append("SENTINEL_DRIVEN_PARAMETER_SELECTION")
    if contract.get("V1_reinterpretation_allowed") is not False:
        errors.append("V1_REINTERPRETATION_ALLOWED")
    return errors


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def git_output(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True, encoding="utf-8").strip()


def git_blob_bytes(repo: Path, commit: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=repo)


def task_local(path: str) -> bool:
    return path.replace("\\", "/").startswith(str(TASK_RELATIVE).replace("\\", "/") + "/")


def validate(repo: Path) -> list[str]:
    failures: list[str] = []
    task = repo / TASK_RELATIVE
    required = [
        "README.md", "DESIGN_INPUT_LOCK.json", "L0_CONTROLLER_GEOMETRY_CONTRACT_V2.json",
        "GEOMETRY_CONTRACT_V2_INVARIANTS.json", "GEOMETRY_CONTRACT_V2_DECISION.md",
        "geometry_authority_trace.md", "margin_semantics_audit.json", "V1_V2_GEOMETRY_DELTA.json",
        "V2_GEOMETRY_CONTRACT_VERIFICATION_PLAN.json", "geometry_contract_v2_review.json",
        "validation_result.json", "FINAL_DECISION.json", "downstream_handoff.json", "DRAFT_PR_BODY.md",
        "tests/test_geometry_contract_v2.py",
    ]
    for relative in required:
        if not (task / relative).is_file():
            failures.append(f"MISSING_ARTIFACT:{relative}")

    lock = json.loads((task / "DESIGN_INPUT_LOCK.json").read_text(encoding="utf-8"))
    if lock["upstream"]["head_sha"] != EXPECTED_UPSTREAM or lock["upstream"]["base_head_sha"] != EXPECTED_PARENT:
        failures.append("UPSTREAM_IDENTITY_LOCK_MISMATCH")
    if git_output(repo, "rev-parse", EXPECTED_UPSTREAM + "^") != EXPECTED_PARENT:
        failures.append("UPSTREAM_PARENT_MISMATCH")
    remote_ref = git_output(repo, "rev-parse", "refs/remotes/origin/diagnose-l0-start-safe-failure-semantics-v1")
    if remote_ref != EXPECTED_UPSTREAM:
        failures.append("PR105_REMOTE_TRACKING_IDENTITY_MISMATCH")
    for path, identity in lock["input_identities"].items():
        raw = git_blob_bytes(repo, EXPECTED_UPSTREAM, path)
        if hashlib.sha256(raw).hexdigest() != identity["sha256"]:
            failures.append(f"INPUT_SHA256_MISMATCH:{path}")
        if git_output(repo, "rev-parse", f"{EXPECTED_UPSTREAM}:{path}") != identity["git_blob"]:
            failures.append(f"INPUT_GIT_BLOB_MISMATCH:{path}")

    facts = lock["frozen_v1_facts"]
    if (facts["formal_rows"], facts["l0_pass"], facts["l0_fail"], facts["l0_unknown"]) != (14122, 0, 14122, 0):
        failures.append("V1_FROZEN_FACT_DRIFT")
    if facts["root_class"] != "SS-F5":
        failures.append("ROOT_CLASS_DRIFT")

    contract_path = task / "L0_CONTROLLER_GEOMETRY_CONTRACT_V2.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    failures.extend(validate_contract_dict(contract))
    if contract_path.read_bytes() != canonical_json_bytes(contract):
        failures.append("CONTRACT_JSON_NOT_CANONICAL")
    if contract["controller_radius_m"] != 0.015:
        failures.append("CONTROLLER_RADIUS_NOT_RESOLVED_AUTHORITY_VALUE")
    if contract["certification_margin_policy"] != "PRESERVE_PREEXISTING_CERTIFICATION_MARGIN":
        failures.append("MARGIN_POLICY_NOT_EVIDENCE_BACKED")
    if contract["certification_margin_m"] != 0.01:
        failures.append("CERTIFICATION_MARGIN_DRIFT")
    if contract["effective_l0_radius_m"] != 0.025:
        failures.append("EFFECTIVE_L0_RADIUS_DRIFT")
    if contract["units"] != "meters":
        failures.append("UNITS_NOT_METERS")

    unchanged = set(contract["unchanged_from_v1"])
    required_unchanged = {
        "query_state_robot_position_state_0_3", "frame_convention", "axis_order", "scale_convention",
        "gaussian_log_scale_exponentiation_count_1", "map_checkpoint_identity_semantics",
        "gaussian_query_set_FULL", "opacity_filter_behavior", "point_to_ellipsoid_math",
        "min_over_gaussians_aggregation", "status_semantics", "no_candidate_dependence_in_L0",
        "L1_formula", "L2_formula", "shadow_gating",
    }
    if unchanged != required_unchanged:
        failures.append("UNCHANGED_GEOMETRY_SEMANTICS_INCOMPLETE")

    margin = json.loads((task / "margin_semantics_audit.json").read_text(encoding="utf-8"))
    if margin["verdict"] != "PRESERVE_PREEXISTING_CERTIFICATION_MARGIN" or margin["outcome_or_sentinel_driven"]:
        failures.append("MARGIN_SEMANTICS_UNRESOLVED_OR_OUTCOME_DRIVEN")

    plan = json.loads((task / "V2_GEOMETRY_CONTRACT_VERIFICATION_PLAN.json").read_text(encoding="utf-8"))
    stages = {stage["id"]: stage for stage in plan["stages"]}
    if set(stages) != {"V2-A", "V2-B", "V2-C", "V2-D", "V2-E"}:
        failures.append("VERIFICATION_STAGES_INCOMPLETE")
    if stages.get("V2-D", {}).get("mode") != "SUPPORT_ONLY" or stages.get("V2-D", {}).get("l2_distribution_visible") is not False:
        failures.append("SUPPORT_ONLY_PILOT_NOT_FROZEN")

    decision = json.loads((task / "FINAL_DECISION.json").read_text(encoding="utf-8"))
    if decision["FINAL_STATUS"] != "PASS_L0_CONTROLLER_GEOMETRY_CONTRACT_V2_DESIGN":
        failures.append("FINAL_STATUS_MISMATCH")
    if decision["only_next_task"] != "IMPLEMENT_L0_CONTROLLER_GEOMETRY_CONTRACT_V2":
        failures.append("DOWNSTREAM_TASK_MISMATCH")

    status_paths = [line[3:] for line in git_output(repo, "status", "--porcelain").splitlines() if line]
    if not all(task_local(path) for path in status_paths):
        failures.append("NON_TASK_LOCAL_MUTATION")
    return failures


def main() -> int:
    repo = Path(__file__).resolve().parents[3]
    failures = validate(repo)
    if failures:
        print("FAIL_L0_CONTROLLER_GEOMETRY_CONTRACT_V2_DESIGN_VALIDATION")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(PASS_STATUS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
