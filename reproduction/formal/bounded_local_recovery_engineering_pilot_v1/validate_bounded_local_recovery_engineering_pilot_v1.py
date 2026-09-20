#!/usr/bin/env python3
"""CPU-only freeze, prelaunch, and future post-run validator for the pilot."""
from __future__ import annotations

import argparse, csv, hashlib, json, subprocess
from pathlib import Path

TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
PROTOCOL = TASK / "BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_PROTOCOL.json"
LOCK = TASK / "BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_EXECUTION_LOCK.json"
BASE = "abea482dc5bf49ed09cc224dedb7019acba67515"
REPAIR = "2102c8401b61ca8fe74123ab51e8fc9c27ed0895"
IMPL = "8184b0ecec20b6e84b1745518903b87bbb5cde8f"
GATE0 = "18ba8ed8aa3b4acc326426e05808bd5abe67561c"
BRANCH = "freeze-bounded-local-recovery-engineering-pilot-v1"
ORIGIN = "git@github-kenqiana04-safer-splat-current:kenqiana04/safer-splat.git"
TOKEN = "EXECUTE_BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_V1"
RESULT_ROOT = Path("/disk1/zlab/v3_repair_records/bounded_local_recovery_engineering_pilot_v1_20260919")
SESSION = "bounded_local_recovery_engineering_pilot_v1"
TASK_PREFIX = "reproduction/formal/bounded_local_recovery_engineering_pilot_v1/"
FORMAL_PROTOCOL_PATH = "reproduction/formal/post_repair_v3_paired_validation_v1/POST_REPAIR_V3_PAIRED_PROTOCOL.json"
FINAL_TRIALS = [66, 12, 88, 24, 2, 14, 63, 36, 58, 68, 62, 77]
FORMAL85_ORDER = [66,74,9,12,73,26,79,31,54,18,19,88,38,8,28,29,0,24,37,98,27,91,2,78,76,80,82,99,56,21,33,44,14,16,61,23,6,96,43,47,51,69,59,63,42,13,4,93,39,49,97,60,83,36,67,86,3,81,87,71,20,53,7,58,40,89,94,68,48,92,34,72,17,32,62,41,52,64,22,84,11,57,1,46,77]
HARNESS = (
    "run_bounded_local_recovery_engineering_pilot_trial_v1.py",
    "launch_bounded_local_recovery_engineering_pilot_v1.py",
    "validate_bounded_local_recovery_engineering_pilot_v1.py",
    "monitor_bounded_local_recovery_engineering_pilot_v1.py",
    "analyze_bounded_local_recovery_engineering_pilot_v1.py",
    "freeze_bounded_local_recovery_engineering_pilot_v1.py",
)

def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def git(*args: str, check: bool = True, binary: bool = False):
    result = subprocess.run(["git", "-C", str(REPO), *args], check=check,
                            capture_output=True, text=not binary)
    return result.stdout if binary else result.stdout.strip()

def ancestor(commit: str) -> bool:
    return subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor", commit, "HEAD"],
                          capture_output=True).returncode == 0

def semantic_hash(value) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def tmux_active() -> bool:
    return subprocess.run(["tmux", "has-session", "-t", SESSION], capture_output=True).returncode == 0

def compute_controls(order: list[int], requested_anchors: list[int]) -> dict:
    present = [value for value in requested_anchors if value in order]
    missing = [value for value in requested_anchors if value not in order]
    remaining = [value for value in order if value not in present]
    count = 12 - len(present)
    indices = []
    for i in range(count):
        raw = 0 if count == 1 else i * (len(remaining) - 1) / (count - 1)
        index = int(raw + 0.5)
        while index in indices and index + 1 < len(remaining):
            index += 1
        while index in indices and index > 0:
            index -= 1
        indices.append(index)
    controls = [remaining[index] for index in indices]
    final = [value for value in order if value in set(present + controls)]
    return {"present": present, "missing": missing, "remaining": remaining,
            "indices": indices, "controls": controls, "final": final}

def validate_freeze(*, require_lock: bool, require_absent_root: bool) -> dict:
    protocol = read(PROTOCOL)
    checks: dict[str, str] = {}
    def need(name: str, condition: bool) -> None:
        checks[name] = "PASS" if condition else "FAIL"
        if not condition:
            raise RuntimeError("PILOT_FREEZE_PRELAUNCH_" + name.upper() + "_FAIL")

    need("schema", protocol["schema"] == "BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_PROTOCOL_V1")
    need("branch", git("branch", "--show-current") == BRANCH)
    need("origin", git("remote", "get-url", "origin") == ORIGIN)
    need("base_head", protocol["base_head"] == BASE and ancestor(BASE))
    need("authority_heads", protocol["implementation_head"] == REPAIR and
         protocol["original_bounded_recovery_implementation_head"] == IMPL and
         protocol["gate0_head"] == GATE0 and protocol["retry2_freeze_head"] == BASE)
    need("authority_ancestry", all(ancestor(commit) for commit in (REPAIR, IMPL, GATE0)))

    frozen_bytes = git("show", f"{BASE}:{FORMAL_PROTOCOL_PATH}", binary=True)
    frozen = json.loads(frozen_bytes.decode("utf-8"))
    cohort = protocol["cohort"]
    need("formal85_source", cohort["source_path"] == FORMAL_PROTOCOL_PATH and
         cohort["source_sha256"] == hashlib.sha256(frozen_bytes).hexdigest() ==
         "19d17e585aacfc18481878543cd7848bf351a5d89362a305fb60de4fcae917c3")
    need("formal85_order", frozen["cohort"]["trial_order"] == FORMAL85_ORDER and
         cohort["source_trial_order_sha256"] == semantic_hash(FORMAL85_ORDER))
    selection = compute_controls(FORMAL85_ORDER, [12, 15, 24, 45, 68, 75])
    need("anchor_accounting", selection["present"] == cohort["present_anchors"] == [12,24,68] and
         selection["missing"] == cohort["missing_anchors"] == [15,45,75])
    need("outcome_blind_controls", not cohort["outcome_data_consulted_for_controls"] and
         cohort["selected_control_indices_in_remaining_order"] == selection["indices"] and
         cohort["deterministic_controls"] == selection["controls"])
    need("pilot_cohort", cohort["trial_ids"] == cohort["trial_order"] == selection["final"] == FINAL_TRIALS and
         len(set(FINAL_TRIALS)) == 12)
    need("execution_shape", cohort["seed"] == 0 and cohort["maximum_completed_cycles_per_trial"] == 500 and
         cohort["serial_execution"] is True and cohort["separate_process_per_trial"] is True and
         cohort["automatic_retry"] is False)

    env = protocol["environment"]
    need("environment", env["conda_environment"] == "/disk1/zlab/conda_envs/safer_splat_official" and
         env["python"] == "/disk1/zlab/conda_envs/safer_splat_official/bin/python" and Path(env["python"]).is_file() and
         env["physical_gpu"] == 1 and env["CUDA_VISIBLE_DEVICES"] == "1" and env["process_visible_device"] == "cuda:0" and
         env["PYTHONHASHSEED"] == "0" and env["PYTHONNOUSERSITE"] == "1" and
         env["PYTHONDONTWRITEBYTECODE"] == "1" and
         env["CUBLAS_WORKSPACE_CONFIG"] == ":4096:8")
    need("future_identity", Path(protocol["future_result_root"]) == RESULT_ROOT and
         protocol["future_tmux_session"] == SESSION and protocol["execution_authorization_token"] == TOKEN)
    need("result_root_state", (not RESULT_ROOT.exists()) if require_absent_root else RESULT_ROOT.is_dir())
    if require_absent_root:
        need("tmux_absent", not tmux_active())

    bindings = protocol["local_infrastructure_bindings"]
    outputs_source, data_source = Path(bindings["outputs_source"]), Path(bindings["data_source"])
    outputs_binding, data_binding = REPO / "outputs/stonehenge", REPO / "data/stonehenge"
    need("binding_authority", bindings["authority"] == "EXECUTION_HARNESS_ONLY_NO_SCIENTIFIC_AUTHORITY" and
         not bindings["git_commit_authority"] and not bindings["runtime_method_authority"] and
         not bindings["scientific_parameter_authority"])
    need("outputs_binding", outputs_source.is_dir() and outputs_binding.is_symlink() and
         outputs_binding.readlink() == outputs_source and outputs_binding.resolve() == outputs_source.resolve())
    need("data_binding", data_source.is_dir() and data_binding.is_symlink() and
         data_binding.readlink() == data_source and data_binding.resolve() == data_source.resolve())
    need("bindings_ignored", all(subprocess.run(["git", "-C", str(REPO), "check-ignore", "-q", item],
         capture_output=True).returncode == 0 for item in ("outputs/stonehenge", "data/stonehenge")))

    map_contract = protocol["map"]
    need("map_identity", map_contract["identity"] == "c9eade9ca89b741768a0ca33b3a755b2656402864f121aefdceaed4b0174f7c8")
    for row in map_contract["artifacts"]:
        path = Path(map_contract["root"]) / row["relative_path"]
        need("map_" + row["relative_path"].replace("/", "_"),
             path.is_file() and path.stat().st_size == row["size"] and sha(path) == row["sha256"])
    g = protocol["geometry"]
    need("geometry", (g["unit"],g["hard_radius_q"],g["runtime_margin_q"],g["effective_radius_q"],g["rho_seg_q"],
         g["epsilon"],g["historical_diagnostic_radius_q"],g["historical_diagnostic_runtime_authority"]) ==
         ("q",0.015,0.0,0.015,0.0,None,0.025,False))
    need("dynamics", protocol["dynamics"] == {"identity":"POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1",
         "dt":0.05,"causality":["d_p_k1_d_u_k=0","d_p_k2_d_u_k=dt^2_I"]})
    r = protocol["recovery"]
    need("recovery", r["source"] == "SOURCE_BOUNDED_LOCAL_RECOVERY_V1" and r["generator"] == "AXIS_EXTREMA_F32_V1" and
         r["candidate_family"] == "F1_AXIS_EXTREMA_ONLY" and r["maximum_candidates"] == 6 and
         r["candidate_order"] == ["+x","-x","+y","-y","+z","-z"])

    retry2 = protocol["retry2_authority"]
    retry2_root = Path(retry2["root"])
    for name, authority in retry2["artifacts"].items():
        path = retry2_root / name
        need("retry2_" + name.lower().replace(".", "_"), path.is_file() and
             path.stat().st_size == authority["size"] and sha(path) == authority["sha256"])
    summary = read(retry2_root / "SMOKE_SUMMARY.json")
    need("retry2_status", summary["status"] == retry2["status"] == "PASS_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_V1")
    need("retry2_counts", summary["counts"]["public_cycle_count"] == 1500 and summary["counts"]["PlantCommit_count"] == 1500 and
         summary["counts"]["recovery_selected_count"] == 26 and summary["counts"]["recovery_PlantCommit_count"] == 26 and
         not any(summary["hard_zero_counts"].values()))
    need("retry2_read_only", retry2["source_mutation_authority"] is False)

    comparator = protocol["historical_comparator"]
    comparator_root = Path(comparator["root"])
    for name, authority in comparator["artifacts"].items():
        path = comparator_root / name
        need("comparator_" + name.lower().replace(".", "_"), path.is_file() and
             path.stat().st_size == authority["size"] and sha(path) == authority["sha256"])
    with (comparator_root / "POST_REPAIR_V3_PAIRED_TRIAL_RESULTS.csv").open(encoding="utf-8", newline="") as stream:
        baseline = {int(row["trial_id"]): row for row in csv.DictReader(stream)}
    need("comparator_same_trial", comparator["same_trial_availability"] == FINAL_TRIALS and all(t in baseline for t in FINAL_TRIALS))
    need("comparator_role", comparator["role"] == "DIAGNOSTIC_HISTORICAL_SAME_TRIAL_NO_NI_NO_FORMAL_CAUSAL_CLAIM" and
         comparator["source_mutation_authority"] is False)

    gates = set(protocol["hard_zero_integrity_gates"])
    need("hard_zero_gates", len(gates) == 22 and {"canonical_l2_evidence_rewrite_exception_count",
         "candidate_scoped_l2_evidence_missing_count","candidate_scoped_l2_scope_conflict_count",
         "legacy_primary_l2_flat_evidence_corruption_count","represented_map_hard_violation_count",
         "hard_safety_unknown_count"}.issubset(gates))
    need("pilot_acceptance", protocol["acceptance"]["required_completed_trials"] == 12 and
         protocol["acceptance"]["maximum_planned_cycles"] == 6000 and
         protocol["acceptance"]["recovery_selected_min"] == protocol["acceptance"]["recovery_plantcommit_min"] == 1 and
         not protocol["acceptance"]["progress_improvement_is_hard_gate"])
    need("engineering_signal", protocol["engineering_decision_signal"]["ready"] == "READY_FOR_FORMAL_PAIRED_VALIDATION" and
         "0.10*baseline_progress" in protocol["engineering_decision_signal"]["catastrophic_progress_regression"]["relative_collapse_rule"])
    s = protocol["science"]
    need("scientific_boundary", s["engineering_only"] and not s["noninferiority_analysis"] and not s["reference_arm_enabled"] and
         not s["efficacy_claim_authorized"] and s["formal_scientific_verdict"] == "FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE" and
         s["retry2_status"] == "PASS_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_V1" and not s["scientific_state_changed"])

    need("harness_present", all((TASK / name).is_file() for name in HARNESS))
    monitor = (TASK / "monitor_bounded_local_recovery_engineering_pilot_v1.py").read_text(encoding="utf-8")
    need("percent_monitor", all(token in monitor for token in ("OVERALL","CURRENT","RUNNING","PENDING","DONE",
         "BATCH COMPLETE","BATCH STOP","--json","BAR_WIDTH = 30")))
    analyzer = (TASK / "analyze_bounded_local_recovery_engineering_pilot_v1.py").read_text(encoding="utf-8")
    need("analyzer_contract", all(token in analyzer for token in ("PILOT_PROGRESS_DIAGNOSTIC.json",
         "PILOT_ROUTING_DIAGNOSTIC.json","NO_NI_NO_FORMAL_EFFICACY_CLAIM","READY_FOR_FORMAL_PAIRED_VALIDATION",
         "NEEDS_ENGINEERING_DIAGNOSIS_BEFORE_FORMAL","canonical_l2_evidence_rewrite_exception_count",
         "PASS_BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_V1")))
    launcher = (TASK / "launch_bounded_local_recovery_engineering_pilot_v1.py").read_text(encoding="utf-8")
    need("launcher_token", f'choices=("{TOKEN}",)' in launcher and f'args.authorize_execution != "{TOKEN}"' in launcher)
    need("launcher_cwd", "cwd=str(REPO)" in launcher)

    protected = ("cbf","splat","dynamics","run.py","reproduction/runtime",
                 "reproduction/formal/bounded_local_recovery_smoke_v1",
                 "reproduction/formal/bounded_local_recovery_smoke_retry2_v1",
                 "reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1")
    need("protected_diff_zero", not git("diff","--name-only",BASE,"--",*protected))
    changed = [line for line in git("diff","--name-only",BASE).splitlines() if line]
    need("task_scope_only", all(line.startswith(TASK_PREFIX) for line in changed))

    if require_lock:
        lock = read(LOCK)
        need("lock_schema", lock["schema"] == "BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_EXECUTION_LOCK_V1")
        need("lock_protocol", lock["protocol_sha256"] == sha(PROTOCOL) and lock["semantic_protocol_sha256"] == semantic_hash(protocol))
        need("lock_harness", lock["harness_sha256"] == {name: sha(TASK/name) for name in HARNESS})
        need("lock_order", lock["trial_order"] == FINAL_TRIALS and lock["trial_order_sha256"] == semantic_hash(FINAL_TRIALS))
        need("lock_authorities", lock["base_head"] == BASE and lock["repair_implementation_head"] == REPAIR and
             lock["original_bounded_recovery_implementation_head"] == IMPL and lock["gate0_head"] == GATE0 and
             lock["retry2_freeze_head"] == BASE)
        need("lock_external_hashes", lock["retry2_result_artifact_sha256"] == {n:v["sha256"] for n,v in retry2["artifacts"].items()} and
             lock["formal85_source_sha256"] == cohort["source_sha256"] and
             lock["historical_comparator_artifact_sha256"] == {n:v["sha256"] for n,v in comparator["artifacts"].items()})
        need("lock_future", lock["future_result_root"] == str(RESULT_ROOT) and lock["future_tmux_session"] == SESSION and
             lock["execution_authorization_token"] == TOKEN)
        need("lock_zero", (lock["freeze_gpu_run_count"],lock["freeze_tmux_created_count"],
             lock["freeze_real_trial_count"],lock["freeze_real_plantcommit_count"]) == (0,0,0,0))
        need("protocol_commit_ancestor", ancestor(lock["protocol_commit"]))
        committed = git("show",f'{lock["protocol_commit"]}:{TASK_PREFIX}BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_PROTOCOL.json',binary=True)
        need("protocol_pre_outcome", hashlib.sha256(committed).hexdigest() == sha(PROTOCOL))

    return {"schema":"BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_FREEZE_VALIDATION_V1",
            "status":"PASS_FREEZE_BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_V1_VALIDATION",
            "checks":checks,"check_count":len(checks),"gpu_run_count":0,"tmux_created_count":0,
            "real_trial_run_count":0,"plantcommit_real_count":0}

def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode",required=True,choices=("freeze","prelaunch","postrun"))
    args=parser.parse_args()
    if args.mode == "postrun":
        from analyze_bounded_local_recovery_engineering_pilot_v1 import analyze
        result=analyze(write_outputs=False)
        print(json.dumps(result,sort_keys=True))
        return 0 if result["status"] == "PASS_BOUNDED_LOCAL_RECOVERY_ENGINEERING_PILOT_V1" else 2
    result=validate_freeze(require_lock=args.mode == "prelaunch",require_absent_root=True)
    print(json.dumps(result,sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
