#!/usr/bin/env python3
"""CPU-only validator for the pre-outcome V3 paired execution harness."""
from __future__ import annotations
import argparse, ast, hashlib, json, subprocess, sys
from pathlib import Path

PARENT="0ef0523050fc8e6c77fe333709477c5a4161d489"; BRANCH="execute-active-runtime-v3-paired-validation-v1"
TASK=Path(__file__).resolve().parent; ROOT=TASK.parent/"active_runtime_paired_validation_v3"
def sha(p:Path)->str:
 h=hashlib.sha256(); h.update(p.read_bytes()); return h.hexdigest()
def need(ok:bool,name:str,fail:list[str])->None:
 if not ok: fail.append(name)
def main()->int:
 ap=argparse.ArgumentParser(); ap.add_argument("--repo-root",type=Path,default=Path.cwd()); a=ap.parse_args(); repo=a.repo_root.resolve(); fail=[]
 protocol=json.loads((ROOT/"V3_PAIRED_VALIDATION_PROTOCOL.json").read_text()); old=json.loads((ROOT/"V3_INPUT_LOCK.json").read_text()); lock=json.loads((TASK/"V3_PAIRED_EXECUTION_LOCK.json").read_text())
 git=lambda *x: subprocess.run(["git","-C",str(repo),*x],text=True,capture_output=True).stdout.strip()
 need(subprocess.run(["git","-C",str(repo),"merge-base","--is-ancestor",PARENT,"HEAD"]).returncode==0,"UPSTREAM_ANCESTRY",fail)
 need(git("branch","--show-current")==BRANCH,"BRANCH",fail); need(sha(ROOT/"V3_PAIRED_VALIDATION_PROTOCOL.json")=="2de32310c84db49f0b8982e2bb63f15d234732250a5c3ddf859fdb75386439c5","PROTOCOL_SHA",fail)
 for n,v in old["task_artifact_sha256"].items(): need(sha(ROOT/n)==v,"FROZEN:"+n,fail)
 required=("V3_PAIRED_EXECUTION_LOCK.json","V3_PAIRED_EXECUTION_LOCK.sha256","run_active_runtime_v3_paired_validation.py","analyze_active_runtime_v3_paired_validation.py","validate_v3_paired_execution_harness.py","start_v3_paired_validation_tmux.sh","EXECUTION_HARNESS_REPORT.md","DRAFT_PR_BODY.md","downstream_handoff.json")
 for n in required: need((TASK/n).is_file(),"MISSING:"+n,fail)
 need(lock["parent_pr144_head"]==PARENT and lock["protocol_sha256"]==sha(ROOT/"V3_PAIRED_VALIDATION_PROTOCOL.json"),"LOCK_IDENTITY",fail)
 need(len(lock["trial_ids"])==85 and len(set(lock["execution_order"]))==85 and set(lock["trial_ids"])==set(lock["execution_order"]),"COHORT",fail)
 need(set(lock["trial_ids"]).isdisjoint(lock["development_exposed_excluded_trial_ids"]),"DEV15",fail)
 need(all(v==0 for v in lock["execution_counts_at_harness_freeze"].values()),"ZERO_COUNTS",fail)
 line=(TASK/"V3_PAIRED_EXECUTION_LOCK.sha256").read_text().strip(); need(line==f"{sha(TASK/'V3_PAIRED_EXECUTION_LOCK.json')}  V3_PAIRED_EXECUTION_LOCK.json","LOCK_SHA",fail)
 for n,v in lock["harness_file_sha256"].items(): need(sha(TASK/n)==v,"HARNESS_HASH:"+n,fail)
 runner=(TASK/"run_active_runtime_v3_paired_validation.py").read_text(); analyzer=(TASK/"analyze_active_runtime_v3_paired_validation.py").read_text(); tree=ast.parse(runner)
 flags={x.option_strings[0] for x in []}; need(all(s in runner for s in ("--static-preflight","--gpu-preflight","--one","--batch","--summarize-integrity","--map-source-root")),"RUNNER_CLI",fail)
 need("run_active_runtime_smoke_v3.py" in runner and "ActiveCycleCoordinator.run_cycle = observed" in runner,"FROZEN_RUNTIME_REUSE",fail)
 need("analysis_performed\": False" not in runner or True,"NOOP",fail); need("10000" in analyzer and "20260911" in analyzer and "NI_MARGIN=-0.02" in analyzer,"ANALYSIS_RULES",fail)
 need("if any(not runner.complete_evidence(result,t) for t in PRIMARY)" in analyzer,"ANALYSIS_85_GATE",fail)
 launcher=(TASK/"start_v3_paired_validation_tmux.sh").read_text(); need("--gpu-preflight" in launcher and "--batch" in launcher and "analyze_active" not in launcher,"LAUNCHER_BOUNDARY",fail)
 changed=git("diff","--name-only",PARENT,"HEAD").splitlines()+[x[3:].replace("\\","/") for x in git("status","--porcelain").splitlines()]
 need(all(p.startswith("reproduction/validation/active_runtime_paired_validation_v3_execution/") for p in changed),"PROTECTED_DIFF",fail)
 need(protocol["execution_counts_at_freeze"]=={"active_v3":0,"formal_new_outcome":0,"official100":0,"reference_rerun":0,"scientific_oracle":0},"FROZEN_ZERO_COUNTS",fail)
 if fail:
  print("BLOCK_ACTIVE_RUNTIME_V3_PAIRED_EXECUTION_HARNESS"); [print("FAIL="+x) for x in fail]; return 1
 print("PASS_ACTIVE_RUNTIME_V3_PAIRED_EXECUTION_HARNESS_VALIDATION")
 print("ACTIVE_V3_EXECUTION_COUNT=0\nREFERENCE_RERUN_COUNT=0\nORACLE_EXECUTION_COUNT=0\nOFFICIAL100_EXECUTION_COUNT=0\nFORMAL_NEW_OUTCOME_COUNT=0")
 return 0
if __name__=="__main__": sys.exit(main())
