#!/usr/bin/env python3
"""CPU-only validator for retry1 base-config plumbing repair."""
from __future__ import annotations
import argparse, ast, hashlib, json, subprocess, sys
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
PROTOCOL = TASK_DIR / "SMOKE_REPAIR_V1_PROTOCOL.json"
ORIGINAL_LOCK = TASK_DIR / "SMOKE_REPAIR_V1_EXECUTION_LOCK.json"
RETRY_LOCK = TASK_DIR / "SMOKE_REPAIR_V1_EXECUTION_LOCK_RETRY1.json"
RUNNER = TASK_DIR / "run_cert_exec_identity_repair_smoke_v1.py"
VALIDATOR = TASK_DIR / "validate_cert_exec_identity_repair_smoke_v1.py"
LAUNCHER = TASK_DIR / "launch_cert_exec_identity_repair_smoke_v1.sh"
MONITOR = TASK_DIR / "monitor_cert_exec_identity_repair_smoke_v1.py"
BRANCH = "repair-cert-exec-identity-smoke-preflight-config-v1"
BASE = "ac12b04afab2c58b4573d8dc39c5226c9fdda9a1"
OLD_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_20260916")
RETRY_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_v1_retry1_20260916")
DIAGNOSTIC_ROOT = Path("/disk1/zlab/v3_repair_records/cert_exec_identity_repair_smoke_preflight_repair_v1_20260916")
PROTOCOL_SHA = "80b4c15413bdfa9b03b106a725af5cd97b17a51b9e81d03cfe79a7300a8077e7"
ORIGINAL_LOCK_SHA = "91de3e381cd9c3ddc9c5a7398ae9a170dd7867e08359611fc1c9595d8fd9342a"
HISTORICAL_SHA = "c1dc8b3f17850267f1cb3247795bc193a8944aa59349de5019efdf4ae72b1691"
OLD_LOG_SHA = "e6b627d62ce3a96cb5d975d5e0151fd0c54a93ee547ab34d90668771800f269f"

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()

def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, text=True, capture_output=True).stdout.strip()

def need(ok: bool, name: str, passed: list[str], failed: list[str]) -> None:
    (passed if ok else failed).append(name)

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--repo-root", type=Path, required=True); ap.add_argument("--pre-repair", action="store_true")
    args = ap.parse_args(); root = args.repo_root.resolve(strict=True); passed=[]; failed=[]
    protocol=json.loads(PROTOCOL.read_text()); original=json.loads(ORIGINAL_LOCK.read_text()); retry=json.loads(RETRY_LOCK.read_text())
    runner=RUNNER.read_text(); validator=VALIDATOR.read_text(); launcher=LAUNCHER.read_text(); monitor=MONITOR.read_text()
    historical_path=root/"reproduction/smoke/active_runtime_smoke_v3/SMOKE_V3_PROTOCOL.json"; historical=json.loads(historical_path.read_text())
    need(git(root,"branch","--show-current")==BRANCH,"EXACT_REPAIR_BRANCH",passed,failed)
    need(subprocess.run(["git","-C",str(root),"merge-base","--is-ancestor",BASE,"HEAD"]).returncode==0,"AC12B04_ANCESTRY",passed,failed)
    need(sha256(PROTOCOL)==PROTOCOL_SHA,"ORIGINAL_PROTOCOL_UNCHANGED",passed,failed)
    need(sha256(ORIGINAL_LOCK)==ORIGINAL_LOCK_SHA,"ORIGINAL_EXECUTION_LOCK_UNCHANGED",passed,failed)
    need(OLD_ROOT.is_dir() and (OLD_ROOT/"launcher.log").is_file() and sha256(OLD_ROOT/"launcher.log")==OLD_LOG_SHA,"OLD_FAILED_ROOT_READ_ONLY_EVIDENCE",passed,failed)
    diagnostic_ok = False
    diagnostic_result = DIAGNOSTIC_ROOT / "raw" / "gpu_preflight.json"
    if diagnostic_result.is_file():
        try:
            diagnostic = json.loads(diagnostic_result.read_text())
            diagnostic_ok = (diagnostic.get("status") == "PASS"
                             and int(diagnostic.get("runtime_cycles_executed", -1)) == 0
                             and int(diagnostic.get("plant_commit_count", -1)) == 0)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            diagnostic_ok = False
    need(not RETRY_ROOT.exists() and (diagnostic_ok or not DIAGNOSTIC_ROOT.exists()),"RETRY_ROOT_ABSENT_OR_VALID_GPU_PREFLIGHT",passed,failed)
    need(protocol["cohort"]["trial_ids"]==[15,45,75] and protocol["cohort"]["trial_order"]==[15,45,75],"REPAIR_COHORT_EXACT",passed,failed)
    need(protocol["cohort"]["maximum_completed_cycles_per_trial"]==500 and protocol["cohort"]["seed"]==0,"REPAIR_LIMITS_EXACT",passed,failed)
    need(protocol["geometry"]["hard_radius_q"]==0.015 and protocol["geometry"]["runtime_margin_q"]==0.0 and protocol["geometry"]["rho_seg_q"]==0.0 and protocol["geometry"]["historical_diagnostic_runtime_authority"] is False,"GEOMETRY_UNCHANGED",passed,failed)
    need(sha256(historical_path)==HISTORICAL_SHA,"HISTORICAL_V3_BASE_CONFIG_SHA",passed,failed)
    need(all(isinstance(historical.get(k),dict) for k in ("controller","certification","dynamics","deadline_profile")),"HISTORICAL_REQUIRED_MAPPINGS",passed,failed)
    need(historical["controller"]["controller_radius"]==0.015 and historical["certification"]["certification_margin"]==0.0 and historical["certification"]["rho_seg"]==0.0,"HISTORICAL_BASE_GEOMETRY",passed,failed)
    need("load_runtime_base_config" in runner and "runtime_base_config" in runner and "build_repaired_v3_stack(checkout_arg, output_dir, trial_id, runtime_base_config" in runner,"EXPLICIT_PROTOCOL_BASE_CONFIG_SEPARATION",passed,failed)
    need("HISTORICAL_V3_PROTOCOL_REL" in runner and "HISTORICAL_V3_PROTOCOL_SHA256" in runner,"HISTORICAL_CONFIG_EXPLICIT_PATH",passed,failed)
    need("TRIALS = (15, 45, 75)" in runner and "10, 50, 90" not in runner and "200" not in runner,"NO_OLD_COHORT_OR_200_LEAKAGE",passed,failed)
    need("project_v3_runtime_config(base)" in runner and "PROJECTED_V3_GEOMETRY_MISMATCH" in runner,"CPU_PROJECTED_GEOMETRY_CHECK",passed,failed)
    need("gpu_preflight_failure.json" in runner and "GPU_PREFLIGHT" in runner and "scientific_analysis_performed" in runner,"GPU_FAILURE_PERSISTENCE",passed,failed)
    need("OLD_FAILED_ROOT_MUST_REMAIN_READ_ONLY" in launcher and "RESULT_ROOT_ABSENT_CHECK_FAILED" in launcher,"RETRY_LAUNCH_REFUSAL_GATES",passed,failed)
    need("parent_failures" in runner and "EARLY_CHILD_FAILURE" in runner and "automatic_retry" in runner,"CHILD_AUTHORIZATION_AND_EARLY_FAILURE",passed,failed)
    need("TRACE_OBSERVATION_CARDINALITY_MISMATCH" in runner and "plant_commits\"] == 0" in runner,"TRACE_CARDINALITY_REGRESSION",passed,failed)
    need(retry["original_protocol_sha256"]==PROTOCOL_SHA and retry["original_execution_lock_sha256"]==ORIGINAL_LOCK_SHA,"RETRY_LOCK_PRESERVES_ORIGINAL_LOCKS",passed,failed)
    need(retry["historical_v3_base_config_sha256"]==HISTORICAL_SHA and retry["retry_result_root"]==str(RETRY_ROOT),"RETRY_LOCK_BASE_CONFIG_AND_ROOT",passed,failed)
    need(retry["trial_ids"]==[15,45,75] and retry["maximum_completed_cycles_per_trial"]==500 and retry["failure_classification"]=="PRE_TRIAL_GPU_PREFLIGHT_BASE_CONFIG_PLUMBING_FAILURE","RETRY_LOCK_CORE_FIELDS",passed,failed)
    need(retry["execution_counts_at_repair_freeze"]["smoke_trial_execution_count"]==0 and retry["execution_counts_at_repair_freeze"]["plant_commit_count"]==0,"ZERO_REPAIR_EXECUTION_COUNTS",passed,failed)
    if args.pre_repair: need(retry["harness_repair_commit"]=="PENDING_HARNESS_REPAIR_COMMIT","PENDING_REPAIR_LOCK_TEMPLATE",passed,failed)
    else:
        commit=retry["harness_repair_commit"]; need(isinstance(commit,str) and len(commit)==40 and subprocess.run(["git","-C",str(root),"merge-base","--is-ancestor",commit,"HEAD"]).returncode==0,"REPAIR_COMMIT_ANCESTOR",passed,failed)
        need(all(sha256(TASK_DIR/name)==digest for name,digest in retry["harness_sha256"].items()),"RETRY_HARNESS_HASHES",passed,failed)
    protected=git(root,"diff","--name-only",BASE,"--","cbf","dynamics","splat","run.py","reproduction/runtime","reproduction/smoke/active_runtime_smoke_v3","reproduction/design","reproduction/implementation","reproduction/validation/certification_execution_state_identity_repair_v1")
    need(not protected,"PROTECTED_DIFF_ZERO",passed,failed)
    ast.parse(runner); ast.parse(validator); ast.parse(monitor)
    need(all(x in runner for x in ("--cpu-static-preflight","--gpu-preflight","--one","--batch")),"RUNNER_MODES",passed,failed)
    need("--gpu-preflight" in launcher and "--batch" in launcher and "analyze_" not in launcher.lower(),"LAUNCHER_BOUNDARY",passed,failed)
    need("SMOKE_REPAIR_V1_COLLECTION_SUMMARY.json" in monitor,"MONITOR_RETRY_ROOT",passed,failed)
    need(protocol["scientific_boundaries"]["frozen_scientific_decision_remains"]=="FAIL_V3_HARD_SAFETY_GATE" and retry["no_scientific_efficacy_claim"] is True,"SCIENTIFIC_BOUNDARY",passed,failed)
    result={"schema":"CERT_EXEC_IDENTITY_SMOKE_PREFLIGHT_CONFIG_REPAIR_VALIDATION_V1","status":"PASS" if not failed else "FAIL","passed_checks":passed,"failed_checks":failed,"gpu_repair_preflight_attempts":0,"smoke_trial_execution_count":0,"PlantCommit_count":0}
    print(json.dumps(result,sort_keys=True))
    if failed: print("FAILED:"+",".join(failed),file=sys.stderr); return 2
    print("PASS_CERT_EXEC_IDENTITY_SMOKE_PREFLIGHT_CONFIG_REPAIR_V1"); return 0

if __name__ == "__main__": raise SystemExit(main())
