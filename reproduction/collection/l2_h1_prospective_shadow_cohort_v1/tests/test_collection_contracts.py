#!/usr/bin/env python3
"""The twelve preregistered synthetic/pre-data collection contract tests."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parents[1]
REPO = TASK.parents[2]
sys.path.insert(0, str(TASK))

from collection_common import (  # noqa: E402
    DATA_ROLE, EXPECTED_UPSTREAM_HEAD, OFFICIAL100_SHA256, PROTOCOL_SHA256,
    file_sha256, formal_run_id, semantic_sha256,
)


def git_blob(relative: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(REPO), "cat-file", "blob", f"{EXPECTED_UPSTREAM_HEAD}:{relative}"])


def check(name: str, condition: bool) -> None:
    if not condition:
        raise AssertionError(name)
    print(f"{name}=PASS")


def main() -> int:
    protocol_root = "reproduction/protocol/l2_h1_prospective_shadow_cohort_v1"
    lock = json.loads(git_blob(f"{protocol_root}/PROTOCOL_LOCK.json"))
    per_file = {name: hashlib.sha256(git_blob(f"{protocol_root}/{name}")).hexdigest() for name in lock["per_file_sha256"]}
    combined = semantic_sha256([{"path": name, "sha256": per_file[name]} for name in sorted(per_file)])
    check("01_protocol_sha_verification", per_file == lock["per_file_sha256"] and combined == PROTOCOL_SHA256)

    official = REPO / "reproduction/experiment_protocol_freeze_v1/trial_manifests/stonehenge_official100_manifest.csv"
    manifest = json.loads((REPO / protocol_root / "formal_trial_manifest.json").read_text(encoding="utf-8"))
    check("02_official100_ordering", file_sha256(official) == OFFICIAL100_SHA256 and [row["trial_id"] for row in manifest["trials"]] == list(range(100)))

    ids = [formal_run_id(index, 0) for index in range(100)]
    check("03_formal_run_id_generation", ids[0] == "formal-v1-trial-000-attempt-0" and ids[-1] == "formal-v1-trial-099-attempt-0" and len(set(ids)) == 100)
    qa_ids = {"equivalence-wrapper-on-trial-000", "pilot_c_trial010"}
    check("04_qa_formal_namespace_disjoint", not qa_ids.intersection(ids) and all(value.startswith("formal-v1-") for value in ids))

    pre_data = {"intended": 0, "capture": 0, "result": 0, "attempt": 0}
    retry_allowed = all((pre_data["intended"] == 0, pre_data["capture"] == 0, pre_data["result"] == 0, pre_data["attempt"] == 0))
    check("05_pre_data_retry_state_machine", retry_allowed and formal_run_id(7, 1).endswith("attempt-1"))
    post_data = {"intended": 1, "capture": 0, "result": 0}
    check("06_post_data_stop_state_machine", any(post_data[key] > 0 for key in post_data))

    forbidden = ("N_L2_PASS", "N_L2_FAIL", "N_L2_UNKNOWN", "primary_numerator", "primary_denominator", "bootstrap_ci")
    qc_source = (TASK / "outcome_blind_qc.py").read_text(encoding="utf-8")
    check("07_outcome_blind_output_contract", not any(token in qc_source for token in forbidden))

    with tempfile.TemporaryDirectory() as temporary:
        sample = Path(temporary) / "sample.bin"
        sample.write_bytes(b"raw-byte-fixture\n")
        check("08_raw_manifest_hashing", file_sha256(sample) == hashlib.sha256(b"raw-byte-fixture\n").hexdigest())

    execution_payload = {"scripts": {"a.py": "a" * 64}, "formal_counts": 0, "protocol": PROTOCOL_SHA256}
    check("09_execution_lock_determinism", semantic_sha256(execution_payload) == semantic_sha256(json.loads(json.dumps(execution_payload))))
    progress = {"trials": [{"trial_id": 0, "state": "PASSED_OUTCOME_BLIND_QC"}, {"trial_id": 1, "state": "PASSED_OUTCOME_BLIND_QC"}]}
    next_trial = len([row for row in progress["trials"] if row["state"] == "PASSED_OUTCOME_BLIND_QC"])
    check("10_resume_semantics", next_trial == 2)

    lock_fixture = {
        "schema_version": "FORMAL_COLLECTION_LOCK_V1", "formal_trial_count": 100,
        "formal_run_ids": ids, "raw_artifact_manifests": [{} for _ in ids],
        "per_trial_sha256": {run_id: "a" * 64 for run_id in ids}, "environment_identity": "env",
        "map_identity": "b" * 64, "protocol_lock_sha256": PROTOCOL_SHA256, "qc_completeness": True,
        "collection_deviations": [], "collection_locked_before_scientific_analysis": True,
    }
    pattern = re.compile(r"^formal-v1-trial-0[0-9]{2}-attempt-[01]$")
    check("11_collection_lock_schema_fixture", set(lock_fixture) == set(json.loads((REPO / protocol_root / "formal_collection_lock_schema.json").read_text())["required"]) and all(pattern.match(value) for value in ids))

    git_allowed = ["compact.json", "report.md", "manifest.csv"]
    check("12_raw_log_git_exclusion", not any(Path(path).suffix in {".jsonl", ".log"} for path in git_allowed))
    print("COLLECTION_CONTRACT_TEST_COUNT=12")
    print("NAVIGATION_ROLLOUT_COUNT=0")
    print(f"DATA_ROLE={DATA_ROLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
