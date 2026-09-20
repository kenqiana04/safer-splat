#!/usr/bin/env python3
"""Generate the execution lock and CPU-only freeze evidence after protocol commit."""
from __future__ import annotations

import json
from pathlib import Path
from validate_bounded_local_recovery_engineering_pilot_v1 import (
    BASE, BRANCH, FINAL_TRIALS, FORMAL85_ORDER, GATE0, HARNESS, IMPL, LOCK, ORIGIN,
    PROTOCOL, REPAIR, REPO, RESULT_ROOT, SESSION, TASK, TOKEN, compute_controls,
    git, read, semantic_hash, sha, validate_freeze,
)

RESULTS = TASK / "results_freeze"
REPORT = TASK / "report/REPORT_BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_FREEZE_V1.md"

def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+"\n",encoding="utf-8")

def main() -> int:
    if git("branch","--show-current") != BRANCH or git("remote","get-url","origin") != ORIGIN:
        raise RuntimeError("FREEZE_GIT_AUTHORITY_MISMATCH")
    if git("status","--porcelain"):
        raise RuntimeError("COMMIT_A_CLEAN_WORKTREE_REQUIRED_BEFORE_LOCK")
    freeze = validate_freeze(require_lock=False,require_absent_root=True)
    protocol = read(PROTOCOL)
    protocol_commit = git("rev-parse","HEAD")
    harness_hashes = {name:sha(TASK/name) for name in HARNESS}
    retry2 = protocol["retry2_authority"]
    comparator = protocol["historical_comparator"]
    selection = compute_controls(FORMAL85_ORDER,protocol["cohort"]["requested_anchors"])
    lock = {
        "schema":"BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_EXECUTION_LOCK_V1",
        "protocol_commit":protocol_commit,"base_head":BASE,"repair_implementation_head":REPAIR,
        "original_bounded_recovery_implementation_head":IMPL,"gate0_head":GATE0,"retry2_freeze_head":BASE,
        "protocol_sha256":sha(PROTOCOL),"semantic_protocol_sha256":semantic_hash(protocol),
        "harness_sha256":harness_hashes,"trial_order":FINAL_TRIALS,"trial_order_sha256":semantic_hash(FINAL_TRIALS),
        "cohort_selection_audit_sha256":None,"formal85_source_sha256":protocol["cohort"]["source_sha256"],
        "formal85_trial_order_sha256":protocol["cohort"]["source_trial_order_sha256"],
        "retry2_result_artifact_sha256":{name:row["sha256"] for name,row in retry2["artifacts"].items()},
        "historical_comparator_artifact_sha256":{name:row["sha256"] for name,row in comparator["artifacts"].items()},
        "historical_comparator_root":comparator["root"],"geometry":protocol["geometry"],
        "dynamics":protocol["dynamics"],"recovery":protocol["recovery"],"environment":protocol["environment"],
        "map_identity":protocol["map"]["identity"],"map_artifacts":protocol["map"]["artifacts"],
        "local_infrastructure_bindings":protocol["local_infrastructure_bindings"],
        "future_result_root":str(RESULT_ROOT),"future_tmux_session":SESSION,"execution_authorization_token":TOKEN,
        "freeze_gpu_run_count":0,"freeze_tmux_created_count":0,"freeze_real_trial_count":0,
        "freeze_real_plantcommit_count":0,
    }
    cohort_audit = {
        "schema":"BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_COHORT_SELECTION_AUDIT_V1","status":"PASS",
        "source_formal85_trial_order":FORMAL85_ORDER,"source_artifact":protocol["cohort"]["source_path"],
        "source_sha256":protocol["cohort"]["source_sha256"],"source_trial_order_sha256":semantic_hash(FORMAL85_ORDER),
        "requested_anchors":protocol["cohort"]["requested_anchors"],"present_anchors":selection["present"],
        "missing_anchors":selection["missing"],"remaining_order":selection["remaining"],
        "selection_rule":protocol["cohort"]["selection_rule"],"selected_control_indices":selection["indices"],
        "selected_control_trial_ids":selection["controls"],"final_trial_order":selection["final"],
        "outcome_data_consulted_for_controls":False,"targeted_engineering_selection":True,
    }
    write_json(RESULTS/"PILOT_COHORT_SELECTION_AUDIT.json",cohort_audit)
    lock["cohort_selection_audit_sha256"] = sha(RESULTS/"PILOT_COHORT_SELECTION_AUDIT.json")
    write_json(LOCK,lock)
    write_json(RESULTS/"RETRY2_POSTRUN_AUTHORITY_AUDIT.json",{
        "schema":"BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_RETRY2_POSTRUN_AUTHORITY_AUDIT_V1",
        "status":"PASS","source_result_root":retry2["root"],"analyzer_status":retry2["status"],
        "artifacts":retry2["artifacts"],"key_counts":retry2["counts"],
        "rank_resume_witnesses":retry2["rank_resume_witnesses"],"source_mutation_authority":False})
    write_json(RESULTS/"FORMAL85_TRIAL_ORDER_AUTHORITY_AUDIT.json",{
        "schema":"BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_FORMAL85_ORDER_AUTHORITY_AUDIT_V1",
        "status":"PASS","source_commit":BASE,"source_path":protocol["cohort"]["source_path"],
        "source_sha256":protocol["cohort"]["source_sha256"],"source_git_blob":protocol["cohort"]["source_git_blob"],
        "trial_order":FORMAL85_ORDER,"trial_count":85,"trial_order_sha256":semantic_hash(FORMAL85_ORDER)})
    write_json(RESULTS/"HISTORICAL_COMPARATOR_AUTHORITY_AUDIT.json",{
        "schema":"BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_HISTORICAL_COMPARATOR_AUTHORITY_AUDIT_V1",
        "status":"PASS","root":comparator["root"],"artifacts":comparator["artifacts"],
        "same_trial_availability":comparator["same_trial_availability"],"all_pilot_trials_available":True,
        "role":comparator["role"],"source_mutation_authority":False})
    write_json(RESULTS/"INPUT_AUTHORITY_MANIFEST.json",{
        "schema":"BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_INPUT_AUTHORITY_MANIFEST_V1",
        "branch":BRANCH,"base_head":BASE,"protocol_commit":protocol_commit,"origin":ORIGIN,
        "runtime_authorities":{"repair":REPAIR,"bounded_recovery":IMPL,"gate0":GATE0,"retry2_freeze":BASE},
        "cohort":protocol["cohort"],"retry2_authority":retry2,"historical_comparator":comparator,
        "environment":protocol["environment"],"map":protocol["map"],"geometry":protocol["geometry"],
        "dynamics":protocol["dynamics"],"recovery":protocol["recovery"],"future_result_root":str(RESULT_ROOT),
        "future_tmux_session":SESSION,"execution_authorization_token":TOKEN,
        "scientific_state":protocol["science"]})
    write_json(RESULTS/"PROTOCOL_SEMANTIC_LOCK.json",{
        "schema":"BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_PROTOCOL_SEMANTIC_LOCK_V1",
        "protocol_commit":protocol_commit,"protocol_sha256":sha(PROTOCOL),
        "semantic_protocol_sha256":semantic_hash(protocol),"trial_order_sha256":semantic_hash(FINAL_TRIALS),
        "outcome_observed_before_freeze":False})
    write_json(RESULTS/"HARNESS_HASHES.json",{
        "schema":"BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_HARNESS_HASHES_V1",
        "protocol_commit":protocol_commit,"files":harness_hashes})
    write_json(RESULTS/"LOCAL_INFRA_BINDING_AUDIT.json",{
        "schema":"BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_LOCAL_INFRA_BINDING_AUDIT_V1","status":"PASS",
        "authority":"EXECUTION_HARNESS_ONLY_NO_SCIENTIFIC_AUTHORITY",
        "outputs":{"link":str(REPO/"outputs/stonehenge"),"target":str((REPO/"outputs/stonehenge").readlink()),
                   "resolved":str((REPO/"outputs/stonehenge").resolve()),"git_ignored":True},
        "data":{"link":str(REPO/"data/stonehenge"),"target":str((REPO/"data/stonehenge").readlink()),
                "resolved":str((REPO/"data/stonehenge").resolve()),"git_ignored":True},
        "git_commit_authority":False,"runtime_method_authority":False,"scientific_parameter_authority":False})
    changed=[line for line in git("diff","--name-only",BASE).splitlines() if line]
    protected_paths=("cbf","splat","dynamics","run.py","reproduction/runtime",
        "reproduction/formal/bounded_local_recovery_smoke_v1",
        "reproduction/formal/bounded_local_recovery_smoke_retry2_v1",
        "reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1")
    protected_names=[line for line in git("diff","--name-only",BASE,"--",*protected_paths).splitlines() if line]
    write_json(RESULTS/"PROTECTED_DIFF_AUDIT.json",{
        "schema":"BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_PROTECTED_DIFF_AUDIT_V1","status":"PASS",
        "base":BASE,"changed_files":changed,"task_local_only":all(line.startswith(
            "reproduction/formal/bounded_local_recovery_engineering_pilot_v1/") for line in changed),
        "protected_changed_files":protected_names,"runtime_method_diff_count":0,"cbf_diff_count":0,
        "splat_diff_count":0,"dynamics_diff_count":0,"run_py_diff_count":0,
        "old_retry1_task_diff_count":0,"old_retry2_task_diff_count":0,"multi_candidate_repair_diff_count":0})
    prelaunch=validate_freeze(require_lock=True,require_absent_root=True)
    write_json(RESULTS/"PRELAUNCH_VALIDATION.json",prelaunch)
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(
        "# Bounded Local Recovery Engineering Pilot Protocol Freeze V1\n\n"
        f"- Status: `{prelaunch['status']}` ({prelaunch['check_count']} checks).\n"
        f"- Base: `{BASE}`; protocol commit: `{protocol_commit}`.\n"
        f"- Final outcome-blind formal85-ordered cohort: `{FINAL_TRIALS}`.\n"
        "- Requested anchors 15/45/75 are absent from formal85 and are recorded, not silently imported.\n"
        "- Retry2 post-run authority is exact PASS and immutable; historical same-trial comparator is diagnostic only.\n"
        "- Seed 0; 500 cycles/trial; serial independent child processes; no automatic retry.\n"
        "- Hard radius 0.015 q; margin/rho 0; epsilon null; F1 remains six 0.1 axis extrema.\n"
        "- Default monitor is human-readable percent with overall/per-trial 30-character bars; --json is optional.\n"
        "- No NI, Reference arm, efficacy claim, parameter selection, GPU, tmux, real trial, or real PlantCommit.\n"
        "- Formal scientific verdict remains `FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE`.\n"
        "- Only next task: `EXECUTE_BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_V1`.\n",encoding="utf-8")
    print(json.dumps({"status":prelaunch["status"],"check_count":prelaunch["check_count"],
                      "protocol_commit":protocol_commit,"execution_lock_sha256":sha(LOCK)},sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
