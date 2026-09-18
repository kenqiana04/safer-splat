#!/usr/bin/env python3
"""CPU-only freeze/prelaunch and future post-run acceptance validator."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess

TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
PROTOCOL = TASK / "BOUNDED_LOCAL_RECOVERY_SMOKE_PROTOCOL.json"
LOCK = TASK / "BOUNDED_LOCAL_RECOVERY_SMOKE_EXECUTION_LOCK.json"
IMPL = "8184b0ecec20b6e84b1745518903b87bbb5cde8f"
GATE0 = "18ba8ed8aa3b4acc326426e05808bd5abe67561c"
BRANCH = "repair-bounded-local-recovery-smoke-local-infra-binding-r1"
ORIGIN = "git@github-kenqiana04-safer-splat-current:kenqiana04/safer-splat.git"
HARNESS = ("run_bounded_local_recovery_smoke_trial_v1.py",
           "launch_bounded_local_recovery_smoke_v1.py",
           "validate_bounded_local_recovery_smoke_v1.py",
           "monitor_bounded_local_recovery_smoke_v1.py",
           "analyze_bounded_local_recovery_smoke_v1.py")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def git(*args: str, check: bool = True) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args], check=check,
                          capture_output=True, text=True).stdout.strip()


def semantic_hash(value) -> str:
    # All current protocol fields are semantic. No field is omitted.
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_freeze(*, require_lock: bool, require_absent_root: bool) -> dict:
    p = read(PROTOCOL)
    c, e, m, g, r = (p[k] for k in ("cohort", "environment", "map", "geometry", "recovery"))
    checks = {}

    def need(name: str, condition: bool):
        checks[name] = "PASS" if condition else "FAIL"
        if not condition:
            raise RuntimeError("FREEZE_PRELAUNCH_" + name.upper() + "_FAIL")

    need("schema", p["schema"] == "BOUNDED_LOCAL_RECOVERY_SMOKE_PROTOCOL_V1")
    need("upstream_identifiers", p["implementation_head"] == IMPL and p["gate0_head"] == GATE0)
    need("source_ancestry", git("merge-base", "--is-ancestor", IMPL, "HEAD", check=False) == "" and
         subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor", IMPL, "HEAD"]).returncode == 0 and
         subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor", GATE0, "HEAD"]).returncode == 0)
    need("branch", git("branch", "--show-current") == BRANCH)
    need("origin_unchanged", git("remote", "get-url", "origin") == ORIGIN)
    need("cohort", c["trial_ids"] == c["trial_order"] == [15, 45, 75] and
         len(set(c["trial_ids"])) == 3 and c["seed"] == 0 and
         c["maximum_completed_cycles_per_trial"] == 500 and
         c["serial_execution"] is True and c["separate_process_per_trial"] is True and
         c["automatic_retry"] is False)
    need("environment", e["physical_gpu"] == 1 and e["CUDA_VISIBLE_DEVICES"] == "1" and
         e["process_visible_device"] == "cuda:0" and
         e["conda_environment"] == "/disk1/zlab/conda_envs/safer_splat_official" and
         Path(e["python"]).is_file())
    need("result_root_fixed", p["future_result_root"] ==
         "/disk1/zlab/v3_repair_records/bounded_local_recovery_smoke_v1_retry1_20260918")
    root = Path(p["future_result_root"])
    need("result_root_state", (not root.exists()) if require_absent_root else root.is_dir())

    local_bindings = p.get("local_infrastructure_bindings", {})
    outputs_binding = REPO / "outputs/stonehenge"
    data_binding = REPO / "data/stonehenge"
    outputs_source = Path("/disk1/zlab/projects/safer-splat/outputs/stonehenge")
    data_source = Path("/disk1/zlab/projects/safer-splat/data/stonehenge")

    need("local_infra_outputs_binding",
         local_bindings.get("outputs", {}).get("worktree_relative_path") == "outputs/stonehenge" and
         local_bindings.get("outputs", {}).get("source") == "/disk1/zlab/projects/safer-splat/outputs/stonehenge" and
         outputs_source.is_dir() and outputs_binding.is_symlink() and
         outputs_binding.resolve() == outputs_source.resolve())

    need("local_infra_data_binding",
         local_bindings.get("data", {}).get("worktree_relative_path") == "data/stonehenge" and
         local_bindings.get("data", {}).get("source") == "/disk1/zlab/projects/safer-splat/data/stonehenge" and
         data_source.is_dir() and data_binding.is_symlink() and
         data_binding.resolve() == data_source.resolve())

    need("map_identity", m["identity"] ==
         "c9eade9ca89b741768a0ca33b3a755b2656402864f121aefdceaed4b0174f7c8")
    actual = []
    for row in m["artifacts"]:
        file = Path(m["root"]) / row["relative_path"]
        need("map_" + row["relative_path"].replace("/", "_"),
             file.is_file() and file.stat().st_size == row["size"] and sha(file) == row["sha256"])
        actual.append(row)
    need("map_composite", semantic_hash({"scene": "stonehenge", "artifacts": actual}) == m["identity"])
    need("geometry", (g["hard_radius_q"], g["runtime_margin_q"], g["effective_radius_q"],
                      g["rho_seg_q"], g["epsilon"], g["historical_diagnostic_radius_q"],
                      g["historical_diagnostic_runtime_authority"]) ==
         (0.015, 0.0, 0.015, 0.0, None, 0.025, False))
    need("recovery", r["source"] == "SOURCE_BOUNDED_LOCAL_RECOVERY_V1" and
         r["generator"] == "AXIS_EXTREMA_F32_V1" and
         r["candidate_family"] == "F1_AXIS_EXTREMA_ONLY" and
         r["maximum_candidates"] == 6 and r["candidate_order"] == ["+x", "-x", "+y", "-y", "+z", "-z"])
    need("trigger", r["trigger"] == ["SAME_CYCLE_L1_PASS", "PRIMARY_C0_PASS", "PRIMARY_L2_PASS",
         "PRIMARY_L3_TYPED_CANDIDATE_LOCAL_FAIL", "NO_VALID_RETAINED_BACKUP",
         "TERMINAL_CURRENT_STATE_PRECERT_PASS", "DEADLINE_OPEN", "EXACT_IDENTITIES",
         "SOURCE_AUTHORIZED", "EXHAUSTION_KEY_ELIGIBLE"])
    need("priority", r["priority"] == ["CERTIFIED_PRIMARY", "VALID_RETAINED_BACKUP",
         "BOUNDED_LOCAL_RECOVERY", "CERTIFIED_TERMINAL", "ASSURANCE_BOUNDARY"])
    need("source_code_contract", all(token in (REPO /
         "reproduction/runtime/active_runtime_assurance_v2/bounded_recovery.py").read_text(encoding="utf-8")
         for token in ("SOURCE_BOUNDED_LOCAL_RECOVERY_V1", "AXIS_EXTREMA_F32_V1", "+x", "-x", "+y", "-y", "+z", "-z")))
    changed = git("diff", "--name-only", IMPL, "--", "cbf", "dynamics", "splat", "run.py",
                  "reproduction/runtime", "reproduction/smoke", "reproduction/pilot")
    need("protected_diff_zero", not changed)
    formal_changed = [line for line in git("diff", "--name-only", IMPL, "--", "reproduction/formal").splitlines()
                      if not line.startswith("reproduction/formal/bounded_local_recovery_smoke_v1/")]
    need("other_formal_diff_zero", not formal_changed)
    need("science_unchanged", p["science"]["post_repair_progress_ni"] ==
         "FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE" and
         p["science"]["old_v3_hard_safety"] == "FAIL_V3_HARD_SAFETY_GATE" and
         p["science"]["scientific_oracle_enabled"] is False)
    need("harness_present", all((TASK / name).is_file() for name in HARNESS))
    if require_lock:
        lock = read(LOCK)
        need("lock_protocol_hash", lock["protocol_sha256"] == sha(PROTOCOL))
        need("lock_semantic_hash", lock["semantic_protocol_sha256"] == semantic_hash(p))
        need("lock_harness_hashes", all(lock["harness_sha256"][name] == sha(TASK / name) for name in HARNESS))
        need("lock_trial_order", lock["trial_order_sha256"] ==
             semantic_hash(c["trial_order"]))
        need("lock_commit_ancestry", subprocess.run(["git", "-C", str(REPO), "merge-base",
             "--is-ancestor", lock["protocol_commit"], "HEAD"]).returncode == 0)
        need("lock_source", lock["implementation_head"] == IMPL and
             lock["future_result_root"] == str(root))
        launcher_text = (TASK / "launch_bounded_local_recovery_smoke_v1.py").read_text(encoding="utf-8")
        need("lock_execution_authorization",
             lock.get("execution_authorization_token") == "EXECUTE_BOUNDED_LOCAL_RECOVERY_SMOKE_V1_R1" and
             'choices=("EXECUTE_BOUNDED_LOCAL_RECOVERY_SMOKE_V1_R1",)' in launcher_text and
             'args.authorize_execution != "EXECUTE_BOUNDED_LOCAL_RECOVERY_SMOKE_V1_R1"' in launcher_text)
    return {"status": "PASS_FREEZE_PRELAUNCH_CPU_VALIDATION_V1", "checks": checks,
            "check_count": len(checks), "gpu_run_count": 0, "tmux_created_count": 0,
            "smoke_trial_run_count": 0, "plantcommit_real_count": 0,
            "cuda_probe_definition": "Future execution task only: assert torch.cuda.is_available and one visible cuda:0 under CUDA_VISIBLE_DEVICES=1"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("freeze", "prelaunch", "postrun"))
    args = parser.parse_args()
    if args.mode == "postrun":
        from analyze_bounded_local_recovery_smoke_v1 import analyze
        result = analyze(write_outputs=False)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "PASS_BOUNDED_LOCAL_RECOVERY_SMOKE_V1" else 2
    result = validate_freeze(require_lock=args.mode == "prelaunch", require_absent_root=True)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
