#!/usr/bin/env python3
"""Fail-closed static validator. No runtime controller or rollout is imported."""

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[2]
EXPECTED_HEAD = "729b3c78a81f2f3ca8948916b64dcb6e2c50fc66"
SUCCESS = "PASS_RUNTIME_ASSURANCE_DEADLINE_AUTHORITY_V2_VALIDATION"


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=REPO)


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    lock = json.loads((ROOT / "DEADLINE_AUTHORITY_INPUT_LOCK.json").read_text(encoding="utf-8"))
    contract = json.loads((ROOT / "RUNTIME_ASSURANCE_DEADLINE_AUTHORITY_V2.json").read_text(encoding="utf-8"))
    invariants = json.loads((ROOT / "DEADLINE_AUTHORITY_INVARIANTS_V2.json").read_text(encoding="utf-8"))
    timeline = json.loads((ROOT / "RUNTIME_DECISION_TIMELINE_V2.json").read_text(encoding="utf-8"))
    if lock["upstream"]["pr_109"]["head"] != EXPECTED_HEAD:
        fail("PR109 identity mismatch in input lock")
    for item in lock["frozen_blobs"]:
        blob = git("rev-parse", f"{EXPECTED_HEAD}:{item['path']}").decode().strip()
        raw = git("cat-file", "blob", blob)
        if blob != item["git_blob"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
            fail(f"frozen blob mismatch: {item['path']}")
    sys.path.insert(0, str(ROOT))
    from contract_rules import validate_contract
    errors = validate_contract(contract)
    if errors:
        fail(",".join(errors))
    if len(invariants["invariants"]) < 8:
        fail("fewer than eight invariants")
    stages = timeline["stages"]
    if len(stages) != 9 or any(not all(key in stage for key in ("start", "end", "budget")) for stage in stages):
        fail("timeline incomplete")
    rows = list(csv.DictReader((ROOT / "DEADLINE_STATE_TRANSITION_TABLE_V2.csv").open(encoding="utf-8", newline="")))
    expired = [row for row in rows if row["from_state"] == "DEADLINE_EXPIRED"]
    if len(expired) != 1 or expired[0]["to_state"] != "DEADLINE_EXPIRED" or expired[0]["new_high_cost_search"] != "NO":
        fail("expired state is not complete and absorbing")
    consistency = list(csv.DictReader((ROOT / "CROSS_LAYER_DEADLINE_CONSISTENCY_V2.csv").open(encoding="utf-8", newline="")))
    owners = [row["layer"] for row in consistency if row["deadline_owner"] == "YES"]
    if owners != ["SUPERVISOR"]:
        fail("deadline owner duplication")
    if any(value != 0 for value in contract["runtime_counts"].values()):
        fail("runtime action count is nonzero")
    required = ["BACKUP_TEMPORAL_VALIDITY_CONTRACT_V2.md", "TERMINAL_DEADLINE_INTERACTION_V2.md", "DEADLINE_UNKNOWN_TAXONOMY_V2.json", "NO_SEARCH_AFTER_EXPIRY_POLICY.md", "NONCLAIMS.md"]
    if any(not (ROOT / name).is_file() for name in required):
        fail("required artifact missing")
    changed = git("diff", "--name-only", EXPECTED_HEAD).decode().splitlines()
    prefix = "reproduction/specification/runtime_assurance_deadline_authority_v2/"
    if any(not path.startswith(prefix) for path in changed):
        fail("protected or production source changed")
    print(SUCCESS)


if __name__ == "__main__":
    main()
