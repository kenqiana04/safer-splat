#!/usr/bin/env python3
"""CPU-only freeze, prelaunch, and future post-run validator for Retry2."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
PROTOCOL = TASK / "BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_PROTOCOL.json"
LOCK = TASK / "BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_EXECUTION_LOCK.json"
REPAIR = "2102c8401b61ca8fe74123ab51e8fc9c27ed0895"
IMPL = "8184b0ecec20b6e84b1745518903b87bbb5cde8f"
GATE0 = "18ba8ed8aa3b4acc326426e05808bd5abe67561c"
BRANCH = "freeze-bounded-local-recovery-smoke-retry2-protocol-v1"
ORIGIN = "git@github-kenqiana04-safer-splat-current:kenqiana04/safer-splat.git"
TOKEN = "EXECUTE_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_V1"
RESULT_ROOT = Path("/disk1/zlab/v3_repair_records/bounded_local_recovery_smoke_retry2_v1_20260919")
SESSION = "bounded_local_recovery_smoke_retry2_v1"
TASK_PREFIX = "reproduction/formal/bounded_local_recovery_smoke_retry2_v1/"
HARNESS = (
    "run_bounded_local_recovery_smoke_retry2_trial_v1.py",
    "launch_bounded_local_recovery_smoke_retry2_v1.py",
    "validate_bounded_local_recovery_smoke_retry2_v1.py",
    "monitor_bounded_local_recovery_smoke_retry2_v1.py",
    "analyze_bounded_local_recovery_smoke_retry2_v1.py",
    "freeze_bounded_local_recovery_smoke_retry2_v1.py",
)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def git(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["git", "-C", str(REPO), *args], check=check, capture_output=True, text=True
    )
    return result.stdout.strip()


def ancestor(commit: str) -> bool:
    return subprocess.run(
        ["git", "-C", str(REPO), "merge-base", "--is-ancestor", commit, "HEAD"],
        capture_output=True,
    ).returncode == 0


def semantic_hash(value) -> str:
    canonical = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def tmux_active() -> bool:
    return subprocess.run(
        ["tmux", "has-session", "-t", SESSION], capture_output=True
    ).returncode == 0


def validate_freeze(*, require_lock: bool, require_absent_root: bool) -> dict:
    protocol = read(PROTOCOL)
    checks: dict[str, str] = {}

    def need(name: str, condition: bool) -> None:
        checks[name] = "PASS" if condition else "FAIL"
        if not condition:
            raise RuntimeError("RETRY2_FREEZE_PRELAUNCH_" + name.upper() + "_FAIL")

    cohort = protocol["cohort"]
    environment = protocol["environment"]
    map_contract = protocol["map"]
    geometry = protocol["geometry"]
    dynamics = protocol["dynamics"]
    recovery = protocol["recovery"]
    lineage = protocol["retry1_lineage"]
    evidence = protocol["multi_candidate_l2_evidence"]

    need("schema", protocol["schema"] == "BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_PROTOCOL_V1")
    need("branch", git("branch", "--show-current") == BRANCH)
    need("origin", git("remote", "get-url", "origin") == ORIGIN)
    need("authority_heads", protocol["implementation_head"] == REPAIR and
         protocol["original_bounded_recovery_implementation_head"] == IMPL and
         protocol["gate0_head"] == GATE0)
    need("authority_ancestry", all(ancestor(commit) for commit in (REPAIR, IMPL, GATE0)))
    need("cohort", cohort == {
        "trial_ids": [15, 45, 75], "trial_order": [15, 45, 75],
        "source": "RETRY1_NATURAL_RECOVERY_WITNESS_COHORT", "seed": 0,
        "maximum_completed_cycles_per_trial": 500, "serial_execution": True,
        "separate_process_per_trial": True, "automatic_retry": False,
    })
    need("environment", environment["conda_environment"] == "/disk1/zlab/conda_envs/safer_splat_official" and
         environment["python"] == "/disk1/zlab/conda_envs/safer_splat_official/bin/python" and
         Path(environment["python"]).is_file() and environment["physical_gpu"] == 1 and
         environment["CUDA_VISIBLE_DEVICES"] == "1" and environment["process_visible_device"] == "cuda:0" and
         environment["PYTHONHASHSEED"] == "0" and environment["PYTHONNOUSERSITE"] == "1" and
         environment["PYTHONDONTWRITEBYTECODE"] == "1" and
         environment["CUBLAS_WORKSPACE_CONFIG"] == ":4096:8")
    need("result_root_identity", Path(protocol["future_result_root"]) == RESULT_ROOT)
    need("result_root_state", (not RESULT_ROOT.exists()) if require_absent_root else RESULT_ROOT.is_dir())
    need("tmux_identity", protocol["future_tmux_session"] == SESSION)
    if require_absent_root:
        need("tmux_absent", not tmux_active())
    need("authorization_token", protocol["execution_authorization_token"] == TOKEN)

    bindings = protocol["local_infrastructure_bindings"]
    outputs_source = Path("/disk1/zlab/projects/safer-splat/outputs/stonehenge")
    data_source = Path("/disk1/zlab/projects/safer-splat/data/stonehenge")
    outputs_binding = REPO / "outputs/stonehenge"
    data_binding = REPO / "data/stonehenge"
    need("binding_authority", bindings["authority"] == "EXECUTION_HARNESS_ONLY_NO_SCIENTIFIC_AUTHORITY" and
         not bindings["git_commit_authority"] and not bindings["runtime_method_authority"] and
         not bindings["scientific_parameter_authority"])
    need("outputs_binding", outputs_source.is_dir() and outputs_binding.is_symlink() and
         outputs_binding.readlink() == outputs_source and outputs_binding.resolve() == outputs_source.resolve())
    need("data_binding", data_source.is_dir() and data_binding.is_symlink() and
         data_binding.readlink() == data_source and data_binding.resolve() == data_source.resolve())
    need("bindings_git_ignored", all(subprocess.run(
        ["git", "-C", str(REPO), "check-ignore", "-q", relative], capture_output=True
    ).returncode == 0 for relative in ("outputs/stonehenge", "data/stonehenge")))

    need("map_identity", map_contract["identity"] ==
         "c9eade9ca89b741768a0ca33b3a755b2656402864f121aefdceaed4b0174f7c8")
    for row in map_contract["artifacts"]:
        path = Path(map_contract["root"]) / row["relative_path"]
        need("map_" + row["relative_path"].replace("/", "_"),
             path.is_file() and path.stat().st_size == row["size"] and sha(path) == row["sha256"])
    need("map_composite", semantic_hash({"scene": "stonehenge", "artifacts": map_contract["artifacts"]}) ==
         map_contract["identity"])

    need("geometry", (geometry["unit"], geometry["hard_radius_q"], geometry["runtime_margin_q"],
         geometry["effective_radius_q"], geometry["rho_seg_q"], geometry["epsilon"],
         geometry["historical_diagnostic_radius_q"], geometry["historical_diagnostic_runtime_authority"]) ==
         ("q", 0.015, 0.0, 0.015, 0.0, None, 0.025, False))
    need("dynamics", dynamics == {"identity": "POSITION_FIRST_FORWARD_EULER_DOUBLE_INTEGRATOR_V1",
         "dt": 0.05, "causality": ["d_p_k1_d_u_k=0", "d_p_k2_d_u_k=dt^2_I"]})
    expected_vectors = {
        "+x": [0.1, 0.0, 0.0], "-x": [-0.1, 0.0, 0.0],
        "+y": [0.0, 0.1, 0.0], "-y": [0.0, -0.1, 0.0],
        "+z": [0.0, 0.0, 0.1], "-z": [0.0, 0.0, -0.1],
    }
    need("recovery_f1", recovery["source"] == "SOURCE_BOUNDED_LOCAL_RECOVERY_V1" and
         recovery["generator"] == "AXIS_EXTREMA_F32_V1" and
         recovery["candidate_family"] == "F1_AXIS_EXTREMA_ONLY" and
         recovery["maximum_candidates"] == 6 and
         recovery["candidate_order"] == ["+x", "-x", "+y", "-y", "+z", "-z"] and
         recovery["candidate_vectors"] == expected_vectors)
    bounded_source = REPO / "reproduction/runtime/active_runtime_assurance_v2/bounded_recovery.py"
    need("recovery_source_contract", all(token in bounded_source.read_text(encoding="utf-8") for token in
         ("SOURCE_BOUNDED_LOCAL_RECOVERY_V1", "AXIS_EXTREMA_F32_V1", "+x", "-x", "+y", "-y", "+z", "-z")))

    need("retry1_lineage", lineage["retry1_status"] ==
         "INCONCLUSIVE_RECOVERY_SEARCH_EXERCISED_BUT_NO_RECOVERY_COMMIT" and
         lineage["blocker"] == "MULTI_CANDIDATE_CANONICAL_L2_EVIDENCE_NAMESPACE_DEFECT" and
         lineage["repair_status"] == "PASS_REPAIR_MULTI_CANDIDATE_CANONICAL_L2_EVIDENCE_V1" and
         lineage["repair_head"] == REPAIR and lineage["natural_witnesses"] == [
             {"trial_id": 15, "cycle_index": 202}, {"trial_id": 45, "cycle_index": 168},
             {"trial_id": 75, "cycle_index": 281}])
    need("historical_roots_present", Path(lineage["attempt0_root"]).is_dir() and Path(lineage["retry1_root"]).is_dir() and
         lineage["historical_roots_mutation_authority"] is False)

    evidence_source = REPO / "reproduction/runtime/certification_execution_state_identity_repair_v1/evidence.py"
    repaired_source = REPO / "reproduction/runtime/certification_execution_state_identity_repair_v1/repaired_components.py"
    need("repair_source_exact", not git("diff", "--name-only", REPAIR, "--", str(evidence_source.relative_to(REPO)),
         str(repaired_source.relative_to(REPO))))
    need("repair_contract_present", "record_scoped" in evidence_source.read_text(encoding="utf-8") and
         "CANONICAL_SCOPED_EVIDENCE_REWRITE_FORBIDDEN" in evidence_source.read_text(encoding="utf-8") and
         "canonical_l2_candidate_evidence" in repaired_source.read_text(encoding="utf-8") and
         "CandidateRole.PRIMARY" in repaired_source.read_text(encoding="utf-8"))
    need("evidence_contract", evidence["legacy_primary_flat_required"] is True and
         evidence["candidate_scoped_namespace"] == "canonical_l2_candidate_evidence" and
         evidence["candidate_scoped_required_for_each_l2_evaluation"] is True and
         evidence["canonical_l2_evidence_rewrite_exception_count_max"] == 0)
    need("hard_zero_extensions", all(name in protocol["hard_zero_integrity_gates"] for name in (
         "canonical_l2_evidence_rewrite_exception_count", "candidate_scoped_l2_evidence_missing_count",
         "candidate_scoped_l2_scope_conflict_count", "legacy_primary_l2_flat_evidence_corruption_count")))
    need("recovery_l2_counters", protocol["recovery_l2_counters"] == [
         "recovery_l2_enter_count", "recovery_l2_result_count", "recovery_l2_pass_count",
         "recovery_l2_fail_count", "recovery_l2_unknown_count", "recovery_l2_exception_count"])
    analyzer = (TASK / "analyze_bounded_local_recovery_smoke_retry2_v1.py").read_text(encoding="utf-8")
    monitor = (TASK / "monitor_bounded_local_recovery_smoke_retry2_v1.py").read_text(encoding="utf-8")
    need("analyzer_evidence_gates", all(token in analyzer for token in (
         "canonical_l2_candidate_evidence", "canonical_l2_evidence_rewrite_exception_count",
         "candidate_scoped_l2_evidence_missing_count", "candidate_scoped_l2_scope_conflict_count",
         "legacy_primary_l2_flat_evidence_corruption_count", "FAIL_MULTI_CANDIDATE_L2_EVIDENCE_REGRESSION",
         "FAIL_RECOVERY_L2_RUNTIME_INFRASTRUCTURE", "PASS_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_V1")))
    need("monitor_recovery_l2_fields", all(token in monitor for token in (
         "recovery_l2_enter", "recovery_l2_result", "recovery_l2_pass", "recovery_l2_fail",
         "recovery_l2_unknown", "recovery_l2_exception", "canonical_l2_rewrite_exceptions")))
    need("scientific_boundary", protocol["progress_role"] == "DIAGNOSTIC_ONLY_NO_NI_NO_REFERENCE_PAIRING" and
         protocol["science"] == {"post_repair_progress_ni": "FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE",
         "scientific_oracle_enabled": False, "reference_arm_enabled": False,
         "formal85_enabled": False, "parameter_selection_enabled": False})

    protected = git("diff", "--name-only", REPAIR, "--", "cbf", "splat", "dynamics", "run.py",
                    "reproduction/runtime", "reproduction/formal/bounded_local_recovery_smoke_v1",
                    "reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1")
    need("protected_diff_zero", not protected)
    changed = [line for line in git("diff", "--name-only", REPAIR).splitlines() if line]
    need("task_scope_only", all(line.startswith(TASK_PREFIX) for line in changed))
    need("harness_present", all((TASK / name).is_file() for name in HARNESS))

    if require_lock:
        lock = read(LOCK)
        need("lock_schema", lock["schema"] == "BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_EXECUTION_LOCK_V1")
        need("lock_protocol_hash", lock["protocol_sha256"] == sha(PROTOCOL))
        need("lock_semantic_hash", lock["semantic_protocol_sha256"] == semantic_hash(protocol))
        need("lock_harness_hashes", lock["harness_sha256"] == {name: sha(TASK / name) for name in HARNESS})
        need("lock_trial_order", lock["trial_order"] == [15, 45, 75] and
             lock["trial_order_sha256"] == semantic_hash([15, 45, 75]))
        need("lock_authority", lock["repair_implementation_head"] == REPAIR and
             lock["original_bounded_recovery_implementation_head"] == IMPL and lock["gate0_head"] == GATE0)
        need("lock_future_identity", lock["future_result_root"] == str(RESULT_ROOT) and
             lock["future_tmux_session"] == SESSION and lock["execution_authorization_token"] == TOKEN)
        need("lock_freeze_zero", (lock["freeze_gpu_run_count"], lock["freeze_tmux_created_count"],
             lock["freeze_smoke_trial_run_count"], lock["freeze_real_plantcommit_count"]) == (0, 0, 0, 0))
        need("protocol_commit_ancestor", ancestor(lock["protocol_commit"]))
        committed_protocol = subprocess.run(
            ["git", "-C", str(REPO), "show", f'{lock["protocol_commit"]}:{TASK_PREFIX}BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_PROTOCOL.json'],
            check=True, capture_output=True,
        ).stdout
        need("protocol_pre_outcome_freeze", hashlib.sha256(committed_protocol).hexdigest() == sha(PROTOCOL))
        launcher = (TASK / "launch_bounded_local_recovery_smoke_retry2_v1.py").read_text(encoding="utf-8")
        need("launcher_token_choices", f'choices=("{TOKEN}",)' in launcher)
        need("launcher_token_guard", f'args.authorize_execution != "{TOKEN}"' in launcher)
        need("runner_worktree_cwd", 'cwd=str(REPO)' in launcher)

    return {
        "schema": "BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_FREEZE_VALIDATION_V1",
        "status": "PASS_FREEZE_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_PROTOCOL_V1_VALIDATION",
        "checks": checks,
        "check_count": len(checks),
        "gpu_run_count": 0,
        "tmux_created_count": 0,
        "smoke_trial_run_count": 0,
        "plantcommit_real_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("freeze", "prelaunch", "postrun"))
    args = parser.parse_args()
    if args.mode == "postrun":
        from analyze_bounded_local_recovery_smoke_retry2_v1 import analyze
        result = analyze(write_outputs=False)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "PASS_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_V1" else 2
    result = validate_freeze(require_lock=args.mode == "prelaunch", require_absent_root=True)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
