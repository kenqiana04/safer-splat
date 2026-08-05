"""Fail-closed static and evidence validator for the bounded V1 task."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

from certifier.result_types import AUTHORIZED_STATUS_VALUES
from task_config import *


REPO=TASK_ROOT.parents[2]
PROTECTED=json.loads((TASK_ROOT/"input_freeze"/"protected_source_hashes.json").read_text(encoding="utf-8"))["files"]


def load(path): return json.loads(Path(path).read_text(encoding="utf-8"))


def main()->None:
    pr=load(TASK_ROOT/"input_freeze"/"pr83_identity.json"); model=load(TASK_ROOT/"proof_artifacts"/"execution_model_audit.json")
    prop=load(TASK_ROOT/"proof_artifacts"/"property_test_summary.json"); smoke=load(TASK_ROOT/"map_smoke"/"replica_smoke_records.json")
    manifest=load(TASK_ROOT/"report"/"run_manifest.json"); handoff=load(TASK_ROOT/"report"/"downstream_handoff.json")
    tests=load(TASK_ROOT/"report"/"test_execution.json"); system=load(TASK_ROOT/"report"/"system_final_state.json")
    report=(TASK_ROOT/"report"/"REPORT_IMPLEMENT_ACTUATOR_BOUNDED_SWEPT_SEGMENT_TERMINAL_BACKUP_CERTIFIER_V1.md").read_text(encoding="utf-8")
    diff_check=subprocess.run(["git","diff","--check"],cwd=REPO,capture_output=True,text=True)
    protected_clean=all(subprocess.run(["git","diff","--quiet",UPSTREAM_HEAD,"--",path],cwd=REPO).returncode==0 for path in PROTECTED)
    required=["certifier/result_types.py","certifier/actuator_certificate.py","certifier/current_feasibility_certificate.py","certifier/segment_certificate.py","certifier/terminal_set.py","certifier/terminal_certificate.py","certifier/braking_backup_policy.py","certifier/backup_witness.py","certifier/backup_certifier.py","certifier/candidate_library.py","certifier/executable_safety_certifier.py","certifier/state_machine.py","certifier/segment_backends/base.py","certifier/segment_backends/analytic_primitive.py","certifier/segment_backends/conservative_interval.py","certifier/segment_backends/sampled_diagnostic.py","adapters/normative_dynamics_adapter.py","adapters/gaussian_barrier_adapter.py","adapters/current_cbf_adapter.py","proof_artifacts/proof_status_registry.json","map_smoke/replica_smoke_records.json","report/downstream_handoff.json","report/DRAFT_PR_BODY.md"]
    files=[p for p in TASK_ROOT.rglob("*") if p.is_file()]
    forbidden_suffix={".npy",".npz",".ply",".pt",".pth",".ckpt",".tar",".zip",".7z"}
    checks={
      "pr83_identity":all(pr["checks"].values()) and pr["pr"]["headRefOid"]==UPSTREAM_HEAD,
      "protected_sources_unchanged":protected_clean,
      "zero_map_training_mutation_dataset_switch":manifest["counters"]["map_training_count"]==manifest["counters"]["map_mutation_count"]==manifest["counters"]["dataset_switch_count"]==0,
      "normative_model_unique":manifest["counters"]["normative_model_count"]==1 and model["optimizer_verifier_backup_consistent"],
      "unknown_not_free":(TASK_ROOT/"tests"/"test_unknown_is_not_free.py").exists(),
      "reference_online_reads_zero":manifest["counters"]["reference_online_read_count"]==smoke["reference_online_read_count"]==0,
      "no_endpoint_only_fallback":load(TASK_ROOT/"proof_artifacts"/"swept_segment_assumptions.json")["endpoint_only_fallback"] is False,
      "synthetic_false_safe_zero":prop["false_safe_count"]==0,
      "all_typed_states_terminal":len(AUTHORIZED_STATUS_VALUES)==13 and "CERTIFIED_UNRECOVERABLE" not in AUTHORIZED_STATUS_VALUES,
      "terminal_returns_next_cycle":"NEXT_CYCLE_DIAGNOSIS" in report,
      "candidate_exhaustion_not_unrecoverable":"FAIL_CLOSED_BACKUP_WITNESS_NOT_FOUND_IN_FROZEN_LIBRARY" in report,
      "map_snapshot_mismatch_tested":(TASK_ROOT/"tests"/"test_segment_map_snapshot_mismatch.py").exists() and (TASK_ROOT/"tests"/"test_backup_snapshot_change.py").exists(),
      "report_json_status_consistent":manifest["final_status"]==handoff["status"]==FINAL_STATUS_PASS and FINAL_STATUS_PASS in report,
      "required_files_present":all((TASK_ROOT/path).exists() for path in required),
      "no_forbidden_files":not any(p.suffix.lower() in forbidden_suffix for p in files),
      "no_large_files":not any(p.stat().st_size>1_000_000 for p in files),
      "no_repository_pycache":not any(p.name=="__pycache__" or p.suffix==".pyc" for p in files),
      "python_syntax_compile":tests["syntax_compile"]["exit_code"]==0 and tests["syntax_compile"]["source_count"]>0,
      "pytest":tests["pytest"]["exit_code"]==0 and tests["pytest"]["passed_count"]>=33,
      "git_diff_check":diff_check.returncode==0,
      "replica_map_smoke":smoke["status"]=="PASS_REPLICA_GT_FINE_PLANT_FREE_MAP_SMOKE" and smoke["formal_navigation_rollout_count"]==0,
      "gpu_clean":system["gpu1_compute_process_count"]==0 and system["task_owned_remote_process_count"]==0,
      "watchdog_ssh_preserved":system["watchdog_preserved"] and system["remote_proxy_listener_127_0_0_1_17898"],
      "protected_scope_only":all(str(p.relative_to(REPO)).replace("\\","/").startswith("reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/") for p in files),
    }
    status="PASS_UNIFIED_EXECUTABLE_SAFETY_CERTIFIER_VALIDATION" if all(checks.values()) else "BLOCKED_UNIFIED_EXECUTABLE_SAFETY_CERTIFIER_VALIDATION"
    result={"status":status,"checks":checks,"failed_checks":[k for k,v in checks.items() if not v],"file_count":len(files),"figure_count":len(list((TASK_ROOT/"figures").glob("*.png"))),"pytest_passed":tests["pytest"]["passed_count"],"false_safe_count":prop["false_safe_count"],"final_status":manifest["final_status"]}
    path=TASK_ROOT/"report"/"validation_result.json"
    with path.open("w",encoding="utf-8",newline="\n") as handle: handle.write(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(status)
    if not all(checks.values()): raise SystemExit(json.dumps(result,sort_keys=True))


if __name__=="__main__": main()
