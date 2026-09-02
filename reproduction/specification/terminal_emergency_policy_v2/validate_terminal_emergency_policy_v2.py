#!/usr/bin/env python3
"""Static task-local validator. It imports no production/runtime modules."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
EXPECTED_BASE = "8b47c5c9af05bbb022af4a964a6c8989231bc1bc"
PREFIX = "reproduction/specification/terminal_emergency_policy_v2/"
SUCCESS = "PASS_TERMINAL_EMERGENCY_POLICY_V2_VALIDATION"


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=REPO)


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def validate_input_lock() -> dict:
    lock = load("TERMINAL_EMERGENCY_POLICY_INPUT_LOCK.json")
    if lock["upstream"]["pr_112"]["head"] != EXPECTED_BASE:
        fail("PR112 exact identity mismatch")
    for item in lock["frozen_blobs"]:
        tree_line = git("ls-tree", EXPECTED_BASE, "--", item["path"]).decode().strip()
        if not tree_line:
            fail(f"missing frozen input: {item['path']}")
        left, _ = tree_line.split("\t", 1)
        mode, object_type, blob = left.split()
        raw = git("cat-file", "blob", blob)
        if object_type != "blob" or mode != item["mode"] or blob != item["git_blob"] or len(raw) != item["size"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
            fail(f"frozen input drift: {item['path']}")
    return lock


def validate_execution_lock() -> None:
    lock = load("TERMINAL_EMERGENCY_POLICY_EXECUTION_LOCK.json")
    commit = lock["design_commit"]
    for item in lock["artifacts"]:
        blob = git("rev-parse", f"{commit}:{item['path']}").decode().strip()
        raw = git("cat-file", "blob", blob)
        if blob != item["git_blob"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
            fail(f"execution-lock artifact drift: {item['path']}")


def main() -> None:
    input_lock = validate_input_lock()
    validate_execution_lock()
    action = load("TERMINAL_ACTION_IDENTITY_V2.json")
    certificate = load("TERMINAL_CERTIFICATE_CONTRACT_V2.json")
    policy = load("TERMINAL_EMERGENCY_POLICY_CONTRACT_V2.json")
    contexts = load("TERMINAL_ELIGIBILITY_CONTEXTS_V2.json")
    lifecycle = load("TERMINAL_ACTION_LIFECYCLE_V2.json")
    terminology = load("FAIL_CLOSE_TERMINOLOGY_V2.json")
    legacy = load("LEGACY_TERMINAL_REUSE_POLICY_V2.json")
    invariants = load("TERMINAL_EMERGENCY_POLICY_INVARIANTS_V2.json")
    properties = load("TERMINAL_EMERGENCY_POLICY_PROPERTIES_V2.json")
    scenarios = load("TERMINAL_EMERGENCY_ADVERSARIAL_SCENARIOS_V2.json")
    result = load("terminal_policy_model_check_result.json")
    counterexamples = load("terminal_policy_counterexamples.json")
    if action["canonical_action"]["action_name"] != "TERMINAL_ZERO_HOLD" or action["canonical_action"]["vector"] != [0.0, 0.0, 0.0]:
        fail("canonical terminal action identity missing")
    if action.get("post_certification_transform_allowed") is not False or action.get("selected_executed_identity_required") is not True:
        fail("selected/executed terminal identity contract incomplete")
    if len(certificate.get("required_fields", [])) != 14 or certificate.get("partial_certificate_ready") is not False or any(certificate["authority"].values()):
        fail("terminal certificate semantics incomplete")
    if policy.get("arbitration_priority") != ["TIMELY_CERTIFIED_NAVIGATION_WITH_PREPARED_TOKEN", "STILL_VALID_RETAINED_BACKUP", "ELIGIBLE_CURRENT_CERTIFIED_TERMINAL_ACTION", "ASSURANCE_BOUNDARY_NO_CERTIFIED_ACTION"]:
        fail("machine-readable arbitration priority drift")
    if policy.get("external_emergency_authority") != "UNRESOLVED_OUTSIDE_METHOD" or any(policy.get(key) for key in ("runtime_implementation_count", "controller_mutation_count", "terminal_controller_implementation_count", "external_emergency_controller_implementation_count", "gpu_execution_count", "rollout_count", "benchmark_count")):
        fail("external authority invented or runtime scope crossed")
    if contexts.get("terminal_certificate_ready_equals_eligible") is not False or contexts.get("membership_alone_eligible") is not False:
        fail("membership/certificate/eligibility separation incomplete")
    goal = next(item for item in contexts["contexts"] if item["id"] == "TCTX_GOAL_HOLD")
    if goal["runtime_authority_status"] != "DEFINED_BUT_RUNTIME_AUTHORITY_UNRESOLVED":
        fail("goal authority was invented")
    priority = (ROOT / "TERMINAL_ARBITRATION_PRIORITY_V2.md").read_text(encoding="utf-8")
    if "NAVIGATION > TERMINAL" not in priority or "VALID_BACKUP > TERMINAL" not in priority:
        fail("PR107 priority not preserved")
    deadline = (ROOT / "DEADLINE_TERMINAL_COMPATIBILITY_AUDIT_V2.md").read_text(encoding="utf-8")
    if "COMPATIBLE_WITHOUT_LOGIC_CHANGE" not in deadline:
        fail("deadline compatibility not established")
    backup_boundary = (ROOT / "BACKUP_TERMINAL_REFERENCE_CONSUMPTION_V2.md").read_text(encoding="utf-8")
    if "BACKUP_TOKEN_EXHAUSTED != TERMINAL_ACTION_AUTHORIZED" not in backup_boundary:
        fail("PR112 EXHAUSTED boundary not preserved")
    external = (ROOT / "EXTERNAL_EMERGENCY_ASSURANCE_BOUNDARY_V2.md").read_text(encoding="utf-8")
    if "UNRESOLVED_OUTSIDE_METHOD" not in external or "ASSURANCE_BOUNDARY_NO_CERTIFIED_ACTION" not in external:
        fail("external emergency boundary incomplete")
    if "SOFTWARE_FAIL_CLOSE != PHYSICAL_SAFE_STOP" not in terminology["inequalities"]:
        fail("false physical safe-stop claim not banned")
    if lifecycle.get("invalidated_executable") is not False or lifecycle.get("unknown_executable") is not False:
        fail("terminal lifecycle UNKNOWN/INVALID semantics invalid")
    if legacy.get("promotion_to_v2_policy_authority") is not False:
        fail("legacy V1 terminal authority promoted")
    if [x["id"] for x in invariants["invariants"]] != [f"TP-{i:02d}" for i in range(1, 25)]:
        fail("TP-01 through TP-24 incomplete")
    if [x["id"] for x in properties["properties"]] != [f"PTP-{i:02d}" for i in range(1, 21)]:
        fail("PTP-01 through PTP-20 incomplete")
    if len(scenarios["scenarios"]) < 20:
        fail("adversarial scenarios incomplete")
    if result.get("status") != "PASS_TERMINAL_EMERGENCY_POLICY_MODEL_CHECK_V2" or result.get("property_pass_count") != 20 or result.get("scenario_pass_count") != len(scenarios["scenarios"]):
        fail("model checker did not pass all properties and scenarios")
    if counterexamples.get("counterexample_count") != 0:
        fail("policy counterexample exists")
    if input_lock.get("runtime_mutation_authority") is not False or input_lock.get("physical_emergency_authority_available") is not False:
        fail("task scope or physical emergency boundary crossed")
    changed = git("diff", "--name-only", EXPECTED_BASE, "HEAD").decode().splitlines()
    working = [line[3:] for line in git("status", "--porcelain").decode().splitlines() if len(line) > 3]
    if any(not path.replace("\\", "/").startswith(PREFIX) for path in changed + working):
        fail("protected or production source changed")
    print(SUCCESS)


if __name__ == "__main__":
    main()
