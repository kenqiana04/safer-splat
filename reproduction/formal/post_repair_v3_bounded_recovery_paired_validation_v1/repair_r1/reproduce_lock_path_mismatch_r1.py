#!/usr/bin/env python3
"""CPU-only deterministic reproduction of the pre-repair basename mismatch."""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path

TASK=Path(__file__).resolve().parents[1]
RUNNER=TASK/"run_post_repair_v3_bounded_recovery_trial_v1.py"
CANONICAL="POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_EXECUTION_LOCK.json"
WRONG="POST_REPAIR_V3_BOUNDED_RECOVERY_PAIRED_VALIDATION_EXECUTION_LOCK.json"
OUT=Path(__file__).resolve().parent/"PRE_REPAIR_LOCK_PATH_REPRODUCTION.json"

def assigned_basename(source:str)->str:
    tree=ast.parse(source)
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id=="LOCK" for x in node.targets):
            if isinstance(node.value,ast.BinOp) and isinstance(node.value.op,ast.Div) and isinstance(node.value.right,ast.Constant): return node.value.right.value
    raise RuntimeError("RUNNER_LOCK_ASSIGNMENT_NOT_FOUND")

def main()->int:
    declared=assigned_basename(RUNNER.read_text(encoding="utf-8")); missing=TASK/declared; raised=False; message=""
    try: hashlib.sha256(missing.read_bytes()).hexdigest()
    except FileNotFoundError as error: raised=True; message=str(error)
    checks={"canonical_existing_lock":(TASK/CANONICAL).is_file(),"runner_declared_wrong_lock":declared==WRONG,"wrong_lock_absent":not missing.exists(),"names_differ":declared!=CANONICAL,"sha_raises_file_not_found":raised,"attempt0_missing_basename_matches":WRONG in message}
    result={"schema":"PRE_REPAIR_LOCK_PATH_REPRODUCTION_R1","status":"PASS_REPRODUCE_FORMAL85_LOCK_PATH_MISMATCH_R1" if all(checks.values()) else "FAIL_REPRODUCE_FORMAL85_LOCK_PATH_MISMATCH_R1","checks":checks,"canonical_basename":CANONICAL,"runner_declared_basename":declared,"exception_type":"FileNotFoundError" if raised else None,"exception":message,"gpu_run_count":0,"trial_run_count":0}
    OUT.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8"); print(json.dumps(result,sort_keys=True)); return 0 if all(checks.values()) else 2
if __name__=="__main__": raise SystemExit(main())
