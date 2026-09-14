#!/usr/bin/env python3
"""CPU-only validator for the repaired, pre-outcome R1 execution harness."""
from __future__ import annotations
import argparse, ast, hashlib, json, subprocess, sys
from pathlib import Path

REPAIRED_HEAD = "604981dca96cf924679aaf718b78776d858b55b1"
REPAIRED_PARENT = "bf0a0792932c02e243236f1b316a41037c95fc69"
BRANCH = "refreeze-active-runtime-v3-paired-execution-harness-after-trace-repair-v1"
PROTOCOL_REL = "reproduction/validation/active_runtime_paired_validation_v3"
TASK_REL = "reproduction/validation/active_runtime_paired_validation_v3_execution_r1"
OLD_TASK_REL = "reproduction/validation/active_runtime_paired_validation_v3_execution"
REPAIR_EVIDENCE_REL = "reproduction/validation/active_runtime_v3_trace_cardinality_repair_v1"
PROTOCOL_SHA = "2de32310c84db49f0b8982e2bb63f15d234732250a5c3ddf859fdb75386439c5"
RESULT_ROOT = Path("/disk1/zlab/v3_execution_records/active_runtime_paired_validation_v3_r1_20260914")
MAP_ROOT = Path("/disk1/zlab/projects/safer-splat/outputs/stonehenge/splatfacto/2024-09-11_100724")
CHECKPOINT_SHA = "ac14f5ced354c93f26cf92404540712eff65bd02554d9e9ed0332508e290382d"
PRIMARY = [0,1,2,3,4,6,7,8,9,11,12,13,14,16,17,18,19,20,21,22,23,24,26,27,28,29,31,32,33,34,36,37,38,39,40,41,42,43,44,46,47,48,49,51,52,53,54,56,57,58,59,60,61,62,63,64,66,67,68,69,71,72,73,74,76,77,78,79,80,81,82,83,84,86,87,88,89,91,92,93,94,96,97,98,99]
ORDER = [66,74,9,12,73,26,79,31,54,18,19,88,38,8,28,29,0,24,37,98,27,91,2,78,76,80,82,99,56,21,33,44,14,16,61,23,6,96,43,47,51,69,59,63,42,13,4,93,39,49,97,60,83,36,67,86,3,81,87,71,20,53,7,58,40,89,94,68,48,92,34,72,17,32,62,41,52,64,22,84,11,57,1,46,77]
DEV15 = [5,10,15,25,30,35,45,50,55,65,70,75,85,90,95]

def sha(path: Path) -> str:
    h = hashlib.sha256(); h.update(path.read_bytes()); return h.hexdigest()
def need(ok: bool, name: str, failures: list[str]) -> None:
    if not ok: failures.append(name)
def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True).stdout.strip()
def json_load(path: Path): return json.loads(path.read_text(encoding="utf-8"))

def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--repo-root", type=Path, default=Path.cwd()); args = ap.parse_args()
    repo = args.repo_root.resolve(); task = repo / TASK_REL; failures: list[str] = []
    lock = json_load(task / "V3_PAIRED_EXECUTION_R1_LOCK.json")
    need(git(repo, "branch", "--show-current") == BRANCH, "BRANCH", failures)
    need(subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", REPAIRED_HEAD, "HEAD"]).returncode == 0, "REPAIRED_HEAD_ANCESTOR", failures)
    need(git(repo, "rev-parse", f"{REPAIRED_HEAD}^") == REPAIRED_PARENT, "REPAIRED_PARENT", failures)
    need(lock.get("repaired_runtime_head") == REPAIRED_HEAD and lock.get("repaired_runtime_parent") == REPAIRED_PARENT and lock.get("repair_pr") == 146, "REPAIR_IDENTITY", failures)
    protocol = repo / PROTOCOL_REL; protocol_json = json_load(protocol / "V3_PAIRED_VALIDATION_PROTOCOL.json")
    need(sha(protocol / "V3_PAIRED_VALIDATION_PROTOCOL.json") == PROTOCOL_SHA, "PROTOCOL_SHA", failures)
    old_lock = json_load(protocol / "V3_INPUT_LOCK.json")
    for name, expected in old_lock["task_artifact_sha256"].items(): need(sha(protocol / name) == expected, "FROZEN:" + name, failures)
    need(lock.get("protocol_freeze_commit") == "b614ff3e985376b5b52f62709ce1a9332170af99", "PROTOCOL_COMMIT", failures)
    need(lock.get("trial_ids") == PRIMARY, "EXACT_85", failures)
    need(lock.get("execution_order") == ORDER, "EXACT_ORDER", failures)
    need(lock.get("development_exposed_excluded_trial_ids") == DEV15 and set(PRIMARY).isdisjoint(DEV15), "DEV15_EXCLUSION", failures)
    execution = lock.get("execution", {})
    need(execution.get("seed") == 0 and execution.get("maximum_completed_cycles_per_trial") == 500 and execution.get("serial") is True and execution.get("separate_process_per_trial") is True and execution.get("future_gpu_id") == 1, "EXECUTION_FREEZE", failures)
    env = lock.get("environment", {})
    need(env.get("python") == "/disk1/zlab/conda_envs/safer_splat_official/bin/python" and env.get("CUDA_VISIBLE_DEVICES") == "1" and env.get("PYTHONHASHSEED") == "0" and env.get("CUBLAS_WORKSPACE_CONFIG") == ":4096:8", "ENVIRONMENT", failures)
    geom = lock.get("v3_hard_geometry", {}); hist = lock.get("historical_diagnostic_shell", {})
    need(geom == {"r_body_q":0.015,"m_hard_q":0.0,"r_hard_q":0.015,"rho_seg_q":0.0,"coordinate_unit":"q"}, "V3_GEOMETRY", failures)
    need(hist.get("radius_q") == 0.025 and all(hist.get(k) is False for k in ("runtime_authority","primary_gate_authority","selection_authority","rejection_authority","fallback_authority","arbitration_authority","ranking_authority","backup_veto_authority","terminal_veto_authority")), "HISTORICAL_DIAGNOSTIC_ONLY", failures)
    need(lock.get("map", {}).get("identity") == "c9eade9ca89b741768a0ca33b3a755b2656402864f121aefdceaed4b0174f7c8", "MAP_IDENTITY", failures)
    need((MAP_ROOT / "config.yml").is_file() and (MAP_ROOT / "dataparser_transforms.json").is_file() and (MAP_ROOT / "nerfstudio_models/step-000029999.ckpt").is_file() and sha(MAP_ROOT / "nerfstudio_models/step-000029999.ckpt") == CHECKPOINT_SHA, "MAP_CHECKPOINT", failures)
    reference = lock.get("reference_reuse", {}); need(reference.get("required_count") == 85 and reference.get("immutable_complete_identity_compatible") is True and reference.get("rerun_authorized") is False and reference.get("rerun_count") == 0, "REFERENCE_REUSE", failures)
    need(not RESULT_ROOT.exists(), "FRESH_RESULT_ROOT_ABSENT", failures)
    for rel in ("active_cycle.py", "supervisor.py"):
        full = repo / "reproduction/runtime/active_runtime_assurance_v2" / rel
        key = "reproduction/runtime/active_runtime_assurance_v2/" + rel
        need(sha(full) == lock["repaired_runtime_source_sha256"][key], "REPAIRED_SOURCE:" + rel, failures)
    changed = git(repo, "diff", "--name-only", REPAIRED_HEAD, "HEAD").splitlines()
    need(all(p.startswith(TASK_REL + "/") for p in changed), "PROTECTED_DIFF", failures)
    need(not git(repo, "diff", "--name-only", REPAIRED_HEAD, "HEAD", "--", OLD_TASK_REL), "OLD_HARNESS_UNCHANGED", failures)
    need(not git(repo, "diff", "--name-only", REPAIRED_HEAD, "HEAD", "--", REPAIR_EVIDENCE_REL), "REPAIR_EVIDENCE_UNCHANGED", failures)
    counts = lock.get("execution_counts_at_harness_freeze", {}); need(all(counts.get(k) == 0 for k in ("active_v3","reference_rerun","scientific_oracle","official100","formal_new_outcome")), "ZERO_EXECUTION_COUNTS", failures)
    required = ["run_active_runtime_v3_paired_validation_r1.py","analyze_active_runtime_v3_paired_validation_r1.py","validate_v3_paired_execution_harness_r1.py","start_v3_paired_validation_r1_tmux.sh","monitor_v3_paired_validation_r1.sh","execution_evidence_schema.json","EXECUTION_HARNESS_R1_REPORT.md","DRAFT_PR_BODY.md","downstream_handoff.json","test_first_launch_preflight_order_r1.py"]
    for name in required: need((task / name).is_file(), "MISSING:" + name, failures)
    for name, expected in lock.get("harness_file_sha256", {}).items(): need(sha(task / name) == expected, "HARNESS_HASH:" + name, failures)
    runner = (task / "run_active_runtime_v3_paired_validation_r1.py").read_text(); analyzer = (task / "analyze_active_runtime_v3_paired_validation_r1.py").read_text(); launcher = (task / "start_v3_paired_validation_r1_tmux.sh").read_text(); monitor = (task / "monitor_v3_paired_validation_r1.sh").read_text()
    need(all(flag in runner for flag in ("--static-preflight","--gpu-preflight","--one","--batch","--summarize-integrity","--resume")), "RUNNER_MODES", failures)
    need("ACTIVE_V3_R1_COLLECTION_INTEGRITY_SUMMARY" in runner and "complete_evidence" in runner, "INTEGRITY_SUMMARY", failures)
    need("10000" in analyzer and "20260911" in analyzer and "NI_MARGIN=-0.02" in analyzer and "--post-collection-authorized" in analyzer, "ANALYZER_PROTOCOL", failures)
    static_i = launcher.find("--static-preflight")
    validator_i = launcher.find('"$VALIDATOR" --repo-root')
    mkdir_i = launcher.find('mkdir -p "$RESULT_ROOT"')
    gpu_i = launcher.find("--gpu-preflight")
    batch_i = launcher.find("--batch")
    need(static_i >= 0 and validator_i >= 0 and mkdir_i >= 0 and gpu_i >= 0 and batch_i >= 0 and static_i < validator_i < mkdir_i < gpu_i < batch_i, "FIRST_LAUNCH_ORDER", failures)
    need("--gpu-preflight" in launcher and "--batch" in launcher and "analyze_active_runtime" not in launcher and "FIRST_LAUNCH_RESULT_ROOT_ALREADY_EXISTS" in launcher, "LAUNCHER_BOUNDARY", failures)
    need('"$PYTHON" "$RUNNER" --static-preflight' in launcher and '"$PYTHON" "$VALIDATOR" --repo-root' in launcher, "CPU_PRECHECK_OUTSIDE_TMUX", failures)
    need("ACTIVE_V3_R1_COLLECTION_INTEGRITY_SUMMARY" in monitor and "raw/*/ACTIVE_V3_RAW_EVIDENCE_LOCK" not in monitor, "MONITOR_AUTHORITY", failures)
    need(lock.get("execution_counts_at_harness_freeze") == {"active_v3":0,"reference_rerun":0,"scientific_oracle":0,"official100":0,"formal_new_outcome":0}, "LOCK_ZERO_COUNTS", failures)
    if failures:
        print("BLOCK_ACTIVE_RUNTIME_V3_PAIRED_EXECUTION_HARNESS_R1"); [print("FAIL=" + f) for f in failures]; return 1
    print("PASS_ACTIVE_RUNTIME_V3_PAIRED_EXECUTION_HARNESS_R1_VALIDATION")
    print("ACTIVE_R1_EXECUTION_COUNT=0\nREFERENCE_RERUN_COUNT=0\nGPU_PREFLIGHT_COUNT=0\nORACLE_EXECUTION_COUNT=0\nOFFICIAL100_EXECUTION_COUNT=0\nFORMAL_NEW_OUTCOME_COUNT=0\nSCIENTIFIC_ANALYZER_EXECUTION_COUNT=0")
    return 0
if __name__ == "__main__": raise SystemExit(main())
