#!/usr/bin/env python3
"""CPU-only validator for protocol-freeze and evidence phases."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

EXPECTED = "50cadfe614da70ce0345c4b1789c787dc529287e"
TASK_REL = "reproduction/diagnostics/v3_hard_gate_near_zero_v1"

def sha(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def git(root: Path,*args: str)->str:
    return subprocess.run(["git","-C",str(root),*args],text=True,capture_output=True,check=True).stdout.strip()

def check(condition: bool, name: str, checks: dict[str,bool])->None:
    checks[name]=bool(condition)
    if not condition: raise RuntimeError("VALIDATION_FAILED:"+name)

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--checkout",type=Path,required=True); ap.add_argument("--phase",choices=("protocol","evidence"),required=True); ap.add_argument("--result-root",type=Path); a=ap.parse_args()
    root=a.checkout.resolve(strict=True); task=root/TASK_REL; p=json.loads((task/"DIAGNOSTIC_PROTOCOL.json").read_text())
    checks={}
    check(git(root,"merge-base",EXPECTED,"HEAD")==EXPECTED,"exact_start_is_ancestor",checks)
    check(p["violating_trial_ids"]==[22,28,57,59],"fixed_trial_set",checks)
    check(p["hard_radius_q"]==0.015 and p["historical_diagnostic_runtime_or_scientific_authority"] is False,"radius_authority",checks)
    check(p["dense_scan"]=={"point_count":1025,"parameter_denominator":1024,"endpoints_included":True},"dense_rule",checks)
    check(p["local_refinement"]["layers"]==4 and p["local_refinement"]["points_per_layer"]==65,"refinement_rule",checks)
    check(p["repeated_query"]["count"]==20 and p["representable_neighbor_audit"]["points"]==7,"precision_rules",checks)
    check(all(p["forbidden"].values()),"forbidden_operations",checks)
    check(p["execution_counts"]=={"gpu_diagnostic_runs":1,"active_scientific_trial_reruns":0,"controller_or_plant_executions":0,"frozen_analyzer_reruns":0,"reference_reruns":0,"official100_runs":0,"formal_new_outcomes":0},"execution_scope",checks)
    check(p["frozen_decision"]=="FAIL_V3_HARD_SAFETY_GATE","frozen_decision",checks)
    source={
      "frozen_analyzer":root/"reproduction/validation/active_runtime_paired_validation_v3_execution_r1/analyze_active_runtime_v3_paired_validation_r1.py",
      "frozen_runner":root/"reproduction/validation/active_runtime_paired_validation_v3_execution_r1/run_active_runtime_v3_paired_validation_r1.py",
      "gaussian_adapter":root/"reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/adapters/gaussian_barrier_adapter.py",
      "gsplat_query":root/"splat/gsplat_utils.py", "ellipsoid_distance":root/"splat/distances.py",
      "frozen_protocol":root/"reproduction/validation/active_runtime_paired_validation_v3/V3_PAIRED_VALIDATION_PROTOCOL.json",
    }
    check(all(sha(path)==p["input_sha256"][name] for name,path in source.items()),"frozen_source_hashes",checks)
    status_output=subprocess.run(["git","-C",str(root),"status","--porcelain","--untracked-files=all"],text=True,capture_output=True,check=True).stdout
    changed=[line[3:].replace("\\","/") for line in status_output.splitlines() if line]
    check(all(path.startswith(TASK_REL+"/") for path in changed),"only_task_local_worktree_changes",checks)
    protected=subprocess.run(["git","-C",str(root),"diff","--name-only",EXPECTED,"--","cbf","dynamics","splat","run.py","reproduction/runtime","reproduction/smoke","reproduction/pilot","reproduction/formal","reproduction/validation/active_runtime_paired_validation_v3","reproduction/validation/active_runtime_paired_validation_v3_execution","reproduction/validation/active_runtime_paired_validation_v3_execution_r1","reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1"],text=True,capture_output=True,check=True).stdout.splitlines()
    check(not protected,"protected_diff_zero",checks)
    if a.phase=="protocol":
        check(a.result_root is not None and not a.result_root.exists(),"fresh_result_root_absent",checks)
        status="PASS_V3_HARD_GATE_NEAR_ZERO_DIAGNOSTIC_PROTOCOL_VALIDATION"
    else:
        check(a.result_root is not None and a.result_root.is_dir(),"result_root_present",checks)
        summary=json.loads((a.result_root/"DIAGNOSTIC_SUMMARY.json").read_text())
        check(summary["status"]=="PASS_V3_HARD_GATE_NEAR_ZERO_DIAGNOSTIC_COMPLETE","diagnostic_complete",checks)
        check(summary["paired_result_root_mutation_count"]==0,"paired_root_preserved",checks)
        check([x["trial_id"] for x in summary["trials"]]==[22,28,57,59],"four_trial_results",checks)
        check(all(x["mapping"]["continuity_pass"] and x["mapping"]["committed_segment_count"]>0 for x in summary["trials"]),"segment_mapping_continuity",checks)
        check(all(x["frozen_witness_reproduction_delta"]==0 for x in summary["trials"]),"frozen_violation_reproduction",checks)
        check(all(x["depth_audit"]["dense_grid_point_count"]==1025 and len(x["depth_audit"]["refinement_layers"])==4 for x in summary["trials"]),"dense_refinement_complete",checks)
        check(all(x["repeated_query"]["witness"]["query_count"]==20 and x["ulp"]["witness_sign_counts"]["negative"]+x["ulp"]["witness_sign_counts"]["zero"]+x["ulp"]["witness_sign_counts"]["positive"]==7 for x in summary["trials"]),"repeat_ulp_complete",checks)
        check(summary["float64_equivalent_backend_status"] in {"IMPLEMENTED_AND_SANITY_VALIDATED","NOT_AVAILABLE_EQUIVALENCE_GATE_FAILED"},"float64_gate_typed",checks)
        lock=json.loads((a.result_root/"DIAGNOSTIC_RESULT_LOCK.json").read_text())
        check(all(sha(a.result_root/path)==meta["sha256"] for path,meta in lock["files"].items()),"result_lock_hashes",checks)
        check((task/"DIAGNOSTIC_EVIDENCE_LOCK.json").is_file() and (task/"DIAGNOSTIC_EVIDENCE_LOCK.sha256").is_file(),"repo_evidence_lock",checks)
        status="PASS_V3_HARD_GATE_NEAR_ZERO_DIAGNOSTIC_VALIDATION"
    print(json.dumps({"status":status,"checks":checks},sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())
