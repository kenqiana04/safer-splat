from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path


UPSTREAM_HEAD = "0b8e38e584c112eb778208e5c5933deb6adb23d0"
TASK_PREFIX = "reproduction/diagnosis/l0_shadow_certifier_semantics_v1/"
TASK_DIR = Path(__file__).resolve().parent
PR103_TASK = "reproduction/diagnosis/l2_h1_primary_reachability_v1"


def git_output(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def git_blob(repo: Path, revision_path: str) -> bytes:
    return subprocess.check_output(["git", "cat-file", "blob", revision_path], cwd=repo)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    repo = Path(git_output(TASK_DIR, "rev-parse", "--show-toplevel"))
    lock = read_json(TASK_DIR / "L0_DIAGNOSIS_INPUT_LOCK.json")
    upstream_lock = json.loads(git_blob(repo, f"{UPSTREAM_HEAD}:{PR103_TASK}/DIAGNOSIS_INPUT_LOCK.json"))
    observability = read_json(TASK_DIR / "l0_observability_inventory.json")
    outcome = read_json(TASK_DIR / "l0_outcome_summary.json")
    mapping = read_json(TASK_DIR / "l0_status_mapping_audit.json")
    semantics = read_json(TASK_DIR / "l0_semantics_summary.json")
    gating = read_json(TASK_DIR / "authority_observability_gating_audit.json")
    root = read_json(TASK_DIR / "root_cause_diagnosis.json")
    final = read_json(TASK_DIR / "FINAL_CASE_DECISION.json")
    scan = read_json(TASK_DIR / "L0_STREAMING_SCAN_LOCK.json")
    frozen_root = json.loads(git_blob(repo, f"{UPSTREAM_HEAD}:{PR103_TASK}/root_cause_diagnosis.json"))

    checks: dict[str, bool] = {}
    merge_base = git_output(repo, "merge-base", "HEAD", UPSTREAM_HEAD)
    checks["upstream_identity_exact"] = merge_base == UPSTREAM_HEAD and lock["pr103_head_sha"] == UPSTREAM_HEAD
    pr103_lock_blob = git_blob(repo, f"{UPSTREAM_HEAD}:{PR103_TASK}/DIAGNOSIS_INPUT_LOCK.json")
    checks["pr103_input_lock_exact"] = hashlib.sha256(pr103_lock_blob).hexdigest() == lock["pr103_input_lock_sha"] == "af42fc6551ef426b1e889a56a45fc3d3e20bf8572ea53e5898958a7c8b4730a5"
    checks["frozen_lock_fields_exact"] = (
        lock["protocol_sha"] == upstream_lock["protocol_sha"] == "e8ea8f3fda15ab81664829ea6f71fcb37f772ad613c13f61007856c16117791a"
        and lock["collection_lock_sha"] == upstream_lock["collection_lock_sha"] == "c30adc48099e8d7b90c980d84389cc1fa693cc1f87d3fc519089efb7cb81b756"
        and lock["analysis_execution_lock_sha"] == upstream_lock["analysis_execution_lock_sha"] == "08cecef117031f599167ca944ba1ac9ac78da94a908a314ecf750729073e6d59"
        and lock["post_reveal_evidence_lock_sha"] == upstream_lock["post_reveal_evidence_lock_sha"] == "a25172a98838d1e132ffc0f0a178029ead0f67dcf44b3ec634eb331c2113d1e4"
    )
    compact_base = f"{PR103_TASK}/"
    compact_hashes = {
        name: hashlib.sha256(git_blob(repo, f"{UPSTREAM_HEAD}:{compact_base}{name}")).hexdigest()
        for name in lock["compact_input_git_blob_sha256"]
    }
    checks["compact_inputs_exact"] = compact_hashes == lock["compact_input_git_blob_sha256"]
    checks["frozen_14122_l0_blocked_fact"] = (
        lock["formal_row_count"] == lock["frozen_L0_BLOCKED"] == 14122
        and frozen_root["data_evidence"]["l2_reachability_reason"] == {"L0_BLOCKED": 14122}
        and lock["frozen_L1_execution_count"] == 0
        and lock["frozen_L2_execution_count"] == 0
    )

    checks["l0_observability_evidence"] = (
        observability["formal_result_artifact_preserves_l0_fields"] is True
        and observability["canonical_analysis_table_preserves_l0_fields"] is False
        and observability["l0_status_logged"] is True
        and observability["l0_reason_logged"] is True
        and observability["one_formal_record_schema_inspection_count"] == 1
        and observability["raw_formal_rows_printed"] == 0
    )
    counts = outcome["counts"]
    checks["l0_status_accounting_exact"] = (
        outcome["observable"] is True
        and outcome["row_count"] == 14122
        and counts == {"FAIL": 14122, "OTHER": 0, "PASS": 0, "UNKNOWN": 0}
        and sum(counts.values()) == 14122
        and outcome["reason_counts"] == {"FROZEN_L0_CURRENT_MAP_QUERY": 14122}
    )
    with (TASK_DIR / "l0_status_distribution.csv").open("r", encoding="utf-8", newline="") as handle:
        status_csv = {row["l0_status"]: int(row["count"]) for row in csv.DictReader(handle)}
    checks["compact_csv_matches_summary"] = status_csv == counts

    adapter_source = git_blob(repo, f"{UPSTREAM_HEAD}:reproduction/equivalence/l2_h1_shadow_instrumentation_off_vs_on_v1/server_run_one.py").decode()
    frozen_adapter_source = git_blob(repo, f"{UPSTREAM_HEAD}:reproduction/instrumentation/l2_h1_on_policy_shadow_instrumentation_v1/frozen_certifier_adapter.py").decode()
    checks["status_mapping_has_source_basis"] = (
        'if status != "FINITE"' in adapter_source
        and '"PASS" if float(query.h) >= 0.0 else "FAIL"' in adapter_source
        and 'if l0["status"] != "PASS"' in frozen_adapter_source
        and '"l0_status": l0["status"]' in frozen_adapter_source
        and mapping["status_mapping_mismatch_detected"] is False
        and mapping["mapping_result"] == "PASS_MAPPING_CORRECT_NO_STATUS_MAPPING_DEFECT"
    )
    protocol_source = git_blob(repo, f"{UPSTREAM_HEAD}:reproduction/design/l2_h1_on_policy_shadow_observation_v1/ON_POLICY_SHADOW_OBSERVATION_PROTOCOL_V1.md").decode()
    checks["authority_gating_has_spec_basis"] = (
        "The shadow result has no consumer in the controller." in protocol_source
        and "L0/current-feasibility reached" in protocol_source
        and gating["controller_authority_gate"] == "NOT_REQUIRED"
        and gating["shadow_observation_gate"] == "REQUIRED"
        and gating["controller_and_shadow_gate_are_same_contract"] is False
        and gating["spec_conformance"] == "CONFORMANT"
    )
    checks["l0_semantics_source_bounded"] = (
        semantics["state_checked"].startswith("p_k")
        and semantics["immediate_segment_checked"] is False
        and semantics["candidate_dependent"] is False
        and semantics["repair_attempted"] is False
        and semantics["uses_map_current_state_query"] is True
    )
    checks["root_class_consistent"] = (
        root["root_class"] == final["root_class"] == "L0-S2_TRUE_L0_FAIL_SUPPORT"
        and root["only_next_task"] == final["only_next_task"] == "DIAGNOSE_L0_START_SAFE_FAILURE_SEMANTICS_V1"
        and root["mapping_defect"] is False
    )
    checks["single_streaming_scan"] = scan["streaming_scan_count"] == root["streaming_scan_count"] == 1 and scan["raw_rows_printed"] == 0

    changed = [line for line in git_output(repo, "diff", "--name-only", UPSTREAM_HEAD).splitlines() if line]
    status_paths = []
    for line in git_output(repo, "status", "--porcelain", "--untracked-files=all").splitlines():
        if line:
            status_paths.append(line[3:].replace("\\", "/"))
    checks["task_local_changes_only"] = all(path.startswith(TASK_PREFIX) for path in (*changed, *status_paths))
    checks["no_upstream_or_runtime_mutation"] = checks["task_local_changes_only"] and root["runtime_mutation_count"] == 0 and root["upstream_artifact_mutation_count"] == 0
    checks["no_new_experiment"] = root["new_experiment_count"] == 0
    checks["v1_scientific_result_not_reinterpreted"] = root["scientific_v1_reinterpretation"] is False
    checks["no_raw_logs_committed"] = not any(path.suffix.lower() in {".jsonl", ".log"} for path in TASK_DIR.rglob("*"))

    failed = [name for name, passed in checks.items() if not passed]
    result = {
        "checks": checks,
        "failed_checks": failed,
        "pass": not failed,
        "schema_version": "L0_SHADOW_CERTIFIER_SEMANTICS_DIAGNOSIS_VALIDATION_RESULT_V1",
        "validator": "PASS_L0_SHADOW_CERTIFIER_SEMANTICS_DIAGNOSIS_V1_VALIDATION" if not failed else "FAIL_L0_SHADOW_CERTIFIER_SEMANTICS_DIAGNOSIS_V1_VALIDATION",
    }
    with (TASK_DIR / "validation_result.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"failed_checks": failed, "validator": result["validator"]}, sort_keys=True))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
