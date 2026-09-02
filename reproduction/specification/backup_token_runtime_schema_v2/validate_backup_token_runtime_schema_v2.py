#!/usr/bin/env python3
"""Static schema and lifecycle evidence validator; no production import."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
EXPECTED_BASE = "a658c858995d76a4baa1ad119701e2706df075be"
SUCCESS = "PASS_BACKUP_TOKEN_RUNTIME_SCHEMA_V2_VALIDATION"


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=REPO)


def load(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    lock = load("BACKUP_TOKEN_SCHEMA_INPUT_LOCK.json")
    if lock["upstream"]["pr_111"]["head"] != EXPECTED_BASE:
        fail("PR111 exact identity mismatch")
    for item in lock["frozen_blobs"]:
        blob = git("rev-parse", f"{EXPECTED_BASE}:{item['path']}").decode().strip()
        raw = git("cat-file", "blob", blob)
        if blob != item["git_blob"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
            fail(f"upstream contract drift: {item['path']}")
    bundle = load("IMMUTABLE_BACKUP_CERTIFICATE_BUNDLE_SCHEMA_V2.json")
    token = load("RETAINED_BACKUP_TOKEN_SCHEMA_V2.json")
    runtime = load("BACKUP_TOKEN_RUNTIME_STATE_V2.json")
    numeric = load("BACKUP_TOKEN_NUMERIC_IDENTITY_V2.json")
    events = load("BACKUP_TOKEN_EVENT_SCHEMA_V2.json")
    predicate = load("BACKUP_TOKEN_VALIDITY_PREDICATE_V2.json")
    invariants = load("BACKUP_TOKEN_INVARIANTS_V2.json")
    properties = load("BACKUP_TOKEN_PROPERTIES_V2.json")
    scenarios = load("BACKUP_TOKEN_ADVERSARIAL_SCENARIOS_V2.json")
    result = load("backup_token_model_check_result.json")
    counterexamples = load("backup_token_counterexamples.json")
    if bundle.get("mutable_after_creation") is not False or bundle.get("partial_witness_allowed") is not False or token.get("prepared_is_executable") is not False:
        fail("immutable bundle / mutable handle split invalid")
    if runtime.get("single_active_token_invariant") is not True or token.get("single_active_token_invariant") is not True:
        fail("single active token invariant missing")
    if predicate.get("requirement_count") != 19 or len(predicate.get("requirements", [])) != 19:
        fail("validity predicate incomplete")
    if numeric.get("tolerance_allowed") is not False or numeric.get("unspecified_decimal_rounding_allowed") is not False:
        fail("invented tolerance or rounding")
    if runtime["activation"]["active_cycle_rule"] != "source_commit_cycle_plus_1" or runtime["activation"]["prepared_before_commit_executable"] is not False:
        fail("prepared or activation timing invalid")
    if events.get("append_only") is not True or set(events["properties"]["event_type"]["enum"]) != {"PREPARE", "ACTIVATE", "CONSUME", "ADVANCE", "INVALIDATE", "EXHAUST", "SUPERSEDE", "ABORT_PREPARED"}:
        fail("event chain incomplete")
    invariant_ids = [item["id"] for item in invariants["invariants"]]
    if invariant_ids != [f"BT-{i:02d}" for i in range(1, 25)]:
        fail("BT-01 through BT-24 incomplete")
    property_ids = [item["id"] for item in properties["properties"]]
    if property_ids != [f"PBT-{i:02d}" for i in range(1, 21)]:
        fail("PBT-01 through PBT-20 incomplete")
    if len(scenarios["scenarios"]) != 20:
        fail("adversarial scenario set incomplete")
    if result.get("status") != "PASS_BACKUP_TOKEN_LIFECYCLE_MODEL_CHECK_V2" or result.get("property_pass_count") != 20 or result.get("scenario_pass_count") != 20:
        fail("lifecycle checker did not pass all properties/scenarios")
    if counterexamples.get("counterexample_count") != 0:
        fail("lifecycle counterexample present")
    deadline_text = (ROOT / "DEADLINE_BACKUP_TOKEN_COMPATIBILITY_AUDIT_V2.md").read_text(encoding="utf-8")
    if "COMPATIBLE_WITHOUT_LOGIC_CHANGE" not in deadline_text:
        fail("deadline compatibility not established")
    terminal_text = (ROOT / "TERMINAL_REFERENCE_BOUNDARY_V2.md").read_text(encoding="utf-8")
    if "BACKUP_TOKEN_EXHAUSTED != TERMINAL_ACTION_AUTHORIZED" not in terminal_text:
        fail("terminal boundary not preserved")
    alternative_text = (ROOT / "ALTERNATIVE_BACKUP_ROLE_SEPARATION_V2.md").read_text(encoding="utf-8")
    if "not an alternative source" not in alternative_text:
        fail("alternative/backup separation missing")
    if lock.get("runtime_mutation_authority") is not False or lock.get("physical_tracking_model_available") is not False:
        fail("scope or physical assumption crossed")
    prefix = "reproduction/specification/backup_token_runtime_schema_v2/"
    changed = git("diff", "--name-only", EXPECTED_BASE).decode().splitlines()
    if any(not path.startswith(prefix) for path in changed):
        fail("protected or production source changed")
    print(SUCCESS)


if __name__ == "__main__":
    main()
