#!/usr/bin/env python3
"""Validate the frozen protocol without invoking Nerfstudio training."""
from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[2]
BASE="8199c9c4c5ce76e65f389e963376a8a02d784247"
POLICY="becbc4af"

def load(name): return json.loads((ROOT/name).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def git(*args): return subprocess.run(["git",*args],cwd=REPO,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def cache(path): return path.endswith(".pyc") or "/__pycache__/" in path

def main():
    dataset,env,frozen,cmd,out,bundle=map(load,["dataset_lock.json","environment_lock.json","frozen_training_config.json","exact_training_command.json","output_directory_contract.json","protocol_bundle_sha256.json"])
    base_caches=sorted(x for x in git("ls-tree","-r","--name-only",BASE).stdout.splitlines() if cache(x))
    current_caches=sorted(x for x in git("ls-files").stdout.splitlines() if cache(x))
    audit="reproduction/cross_dataset/tum_splatfacto_training_protocol_v1"
    untracked=[x for x in git("ls-files","--others","--exclude-standard","--",audit).stdout.splitlines() if cache(x)]
    tracked=[x for x in git("ls-files","--",audit).stdout.splitlines() if cache(x)]
    checks=[
      ("base_commit",git("merge-base","--is-ancestor",BASE,"HEAD").returncode==0),
      ("policy_commit",git("merge-base","--is-ancestor",POLICY,"HEAD").returncode==0),
      ("dataset_lock",dataset["transforms_sha256"]=="b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a" and (dataset["source_frame_count"],dataset["train_frame_count"],dataset["eval_frame_count"])==(300,240,60)),
      ("metric_parser",dataset["depth_unit_scale_factor_meters"]==0.0002 and dataset["orientation_method"]=="none" and dataset["center_method"]=="none" and dataset["auto_scale_poses"] is False and dataset["dataparser_scale"]==1.0),
      ("environment",env["hostname"]=="zlab-Super-Server" and env["nerfstudio_version"]=="1.1.5" and env["visible_gpu_name"]=="NVIDIA GeForce RTX 4090"),
      ("references",load("reference_config_inventory.json")["stonehenge"]["exists"] and frozen["reference"]["primary"]=="stonehenge"),
      ("parameter_provenance",(ROOT/"parameter_provenance.csv").is_file()),
      ("method_seed",frozen["method"]=="splatfacto" and frozen["seed"]==20260716 and frozen["formal_run_count"]==1),
      ("command",cmd["status"]=="NOT_EXECUTED" and sha(ROOT/"exact_training_command.sh")==cmd["command_sha256"]),
      ("no_execution",cmd["training_iterations_executed"]==0 and cmd["checkpoint_created"] is False and cmd["run_directory_created"] is False),
      ("output_contract",out["must_not_exist_before_training"] and not out["source_data_overlap"] and not out["overwrite_allowed"] and not out["resume_allowed"]),
      ("checkpoint_policy",load("checkpoint_selection_policy.json")["selection_by_metric"] is False),
      ("handoff",load("training_execution_handoff.json")["training_authorized_by_this_task"] is False and load("training_execution_handoff.json")["G1_allowed"] is False),
      ("freeze_zero_diff",git("diff","--exit-code",BASE,"--","reproduction/experiment_protocol_freeze_v1").returncode==0),
      ("g0_zero_diff",git("diff","--exit-code",BASE,"--","reproduction/cross_dataset/tum_g0_checkpoint_entry_audit_v1").returncode==0),
      ("core_zero_diff",git("diff","--exit-code",BASE,"--","cbf","dynamics","ellipsoids","ns_utils","splat","run.py").returncode==0),
      ("cache_baseline_unchanged",base_caches==current_caches and not [x for x in git("diff","--name-status",BASE,"--").stdout.splitlines() if cache(x.split("\t")[-1])]),
      ("audit_cache_absent",not tracked and not untracked),
      ("bundle",all((ROOT/k).is_file() and sha(ROOT/k)==v for k,v in bundle["files"].items())),
    ]
    status="PASS_READY_FOR_FORMAL_TRAINING_EXECUTION" if all(ok for _,ok in checks) else "FAIL"
    result={"status":status,"checks":[{"check":n,"passed":ok} for n,ok in checks],"training_iterations_executed":0,"run_directory_created":False,"checkpoint_created":False,"safer_executed":False,"G1_allowed":False,"unresolved_critical_fields":[],"unresolved_noncritical_fields":["actual run directory timestamp must be recorded at execution"]}
    (ROOT/"validation_result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(status)
    if status=="FAIL": raise SystemExit("failed: "+", ".join(n for n,ok in checks if not ok))
if __name__=="__main__": main()
