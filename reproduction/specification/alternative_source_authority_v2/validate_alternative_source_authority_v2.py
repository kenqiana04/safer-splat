#!/usr/bin/env python3
"""Fail-closed static validator; imports no controller or runtime module."""

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
EXPECTED_BASE = "52467acd2ab82c300a8f6c3ce712ab0d59d4f4cf"
SUCCESS = "PASS_ALTERNATIVE_SOURCE_AUTHORITY_V2_VALIDATION"


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=REPO)


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    lock = json.loads((ROOT / "ALTERNATIVE_SOURCE_AUTHORITY_INPUT_LOCK.json").read_text(encoding="utf-8"))
    contract = json.loads((ROOT / "ALTERNATIVE_SOURCE_AUTHORITY_V2.json").read_text(encoding="utf-8"))
    taxonomy = json.loads((ROOT / "ALTERNATIVE_SOURCE_TAXONOMY_V2.json").read_text(encoding="utf-8"))
    chain = json.loads((ROOT / "ALTERNATIVE_RECERTIFICATION_CHAIN_V2.json").read_text(encoding="utf-8"))
    identity = json.loads((ROOT / "CANDIDATE_IDENTITY_CONTRACT_V2.json").read_text(encoding="utf-8"))
    failures = json.loads((ROOT / "ALTERNATIVE_FAILURE_TAXONOMY_V2.json").read_text(encoding="utf-8"))
    invariants = json.loads((ROOT / "ALTERNATIVE_AUTHORITY_INVARIANTS_V2.json").read_text(encoding="utf-8"))
    if lock["upstream"]["pr_110"]["head"] != EXPECTED_BASE:
        fail("PR110 identity mismatch")
    for item in lock["frozen_blobs"]:
        blob = git("rev-parse", f"{EXPECTED_BASE}:{item['path']}").decode().strip()
        raw = git("cat-file", "blob", blob)
        if blob != item["git_blob"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
            fail(f"frozen blob mismatch: {item['path']}")
    sys.path.insert(0, str(ROOT))
    from contract_rules import validate_contract
    errors = validate_contract(contract, taxonomy, chain)
    if errors:
        fail(",".join(errors))
    if identity["required_fields"] != contract["candidate_identity_fields"] or len(identity["required_fields"]) != 7:
        fail("candidate provenance contract incomplete")
    if len(invariants["invariants"]) < 10:
        fail("insufficient authority invariants")
    expected_failures = {"NO_ALTERNATIVE_AVAILABLE", "SOURCE_INVALID", "PROVENANCE_MISSING", "ALTERNATIVE_CERTIFICATION_FAILED", "ALTERNATIVE_SEARCH_BLOCKED_BY_DEADLINE", "UNKNOWN_SOURCE", "failure_does_not_imply"}
    if set(failures) != expected_failures or failures["UNKNOWN_SOURCE"].get("convert_to_pass") is not False:
        fail("failure or unknown taxonomy incomplete")
    rows = list(csv.DictReader((ROOT / "CROSS_LAYER_ALTERNATIVE_CONSISTENCY_V2.csv").open(encoding="utf-8", newline="")))
    owners = [row["layer"] for row in rows if row["alternative_search_owner"] == "YES"]
    if owners != ["SUPERVISOR"] or any(row["may_create_alternative"] != "NO" for row in rows):
        fail("authority duplication or hidden generation")
    if any(value != 0 for value in contract["runtime_counts"].values()):
        fail("forbidden runtime/scientific action count is nonzero")
    required = ["BACKUP_ALTERNATIVE_COMPATIBILITY_V2.md", "NO_UNSAFE_GENERATION_POLICY.md", "NONCLAIMS.md"]
    if any(not (ROOT / name).is_file() for name in required):
        fail("required contract artifact missing")
    prefix = "reproduction/specification/alternative_source_authority_v2/"
    changed = git("diff", "--name-only", EXPECTED_BASE).decode().splitlines()
    if any(not path.startswith(prefix) for path in changed):
        fail("protected or production source changed")
    print(SUCCESS)


if __name__ == "__main__":
    main()
