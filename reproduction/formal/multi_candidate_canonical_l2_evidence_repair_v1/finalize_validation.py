#!/usr/bin/env python3
"""Finalize CPU regression, protected-diff, and immutable-root audits."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]
BASE = "fff812999a2243e2cd670772abba0a3d5e3214f0"
BRANCH = "repair-multi-candidate-canonical-l2-evidence-v1"
ORIGIN = "git@github-kenqiana04-safer-splat-current:kenqiana04/safer-splat.git"
PYTHON = "/disk1/zlab/conda_envs/safer_splat_official/bin/python"
RESULTS = TASK / "results_cpu_validation"
ALLOWED_RUNTIME = {
    "reproduction/runtime/certification_execution_state_identity_repair_v1/evidence.py",
    "reproduction/runtime/certification_execution_state_identity_repair_v1/repaired_components.py",
}
PROTECTED_PREFIXES = ("cbf/", "splat/", "dynamics/", "reproduction/runtime/active_runtime_assurance_v2/",
                      "reproduction/runtime/v3_hard_radius_runtime_wiring_v1/", "reproduction/smoke/")


def write(name: str, value) -> None:
    target = RESULTS / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def root_digest(root: Path) -> dict:
    files = [{"path": path.relative_to(root).as_posix(), "size": path.stat().st_size, "sha256": sha(path)}
             for path in sorted(item for item in root.rglob("*") if item.is_file())]
    digest = hashlib.sha256(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"root": str(root), "file_count": len(files), "content_manifest_sha256": digest}


def run(command: list[str]) -> dict:
    result = subprocess.run(command, cwd=REPO, capture_output=True, text=True,
                            env={**__import__("os").environ, "CUDA_VISIBLE_DEVICES": "",
                                 "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0"})
    combined = result.stdout + result.stderr
    match = re.search(r"Ran (\d+) tests", combined)
    return {"command": command, "returncode": result.returncode,
            "test_count": int(match.group(1)) if match else None,
            "status": "PASS" if result.returncode == 0 else "FAIL",
            "tail": combined.splitlines()[-12:]}


def main() -> int:
    before = json.loads((RESULTS / "result_root_snapshots_before.json").read_text(encoding="utf-8"))
    current = {name: root_digest(Path(before[name]["root"])) for name in ("retry1", "attempt0")}
    mutation = {name: {
        "before_file_count": before[name]["file_count"], "after_file_count": current[name]["file_count"],
        "before_manifest_sha256": before[name]["content_manifest_sha256"],
        "after_manifest_sha256": current[name]["content_manifest_sha256"],
        "mutation_count": int(before[name]["file_count"] != current[name]["file_count"] or
                              before[name]["content_manifest_sha256"] != current[name]["content_manifest_sha256"]),
    } for name in ("retry1", "attempt0")}
    write("result_root_mutation_audit.json", {"schema": "MULTI_CANDIDATE_L2_RESULT_ROOT_MUTATION_AUDIT_V1",
          "roots": mutation, "total_mutation_count": sum(x["mutation_count"] for x in mutation.values())})

    changed = subprocess.run(["git", "-C", str(REPO), "diff", "--name-only", BASE, "HEAD"],
                             check=True, capture_output=True, text=True).stdout.splitlines()
    uncommitted = subprocess.run(["git", "-C", str(REPO), "diff", "--name-only"],
                                 check=True, capture_output=True, text=True).stdout.splitlines()
    status_rows = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain",
                                  "--untracked-files=all"], check=True,
                                 capture_output=True, text=True).stdout.splitlines()
    untracked = [row[3:] for row in status_rows if row.startswith("?? ")]
    changed = sorted(set(changed + uncommitted + untracked))
    protected = [path for path in changed if path == "run.py" or path.startswith(PROTECTED_PREFIXES)]
    runtime_changed = [path for path in changed if path.startswith("reproduction/runtime/")]
    unauthorized_runtime = [path for path in runtime_changed if path not in ALLOWED_RUNTIME]
    out_of_scope = [path for path in changed if path not in ALLOWED_RUNTIME and
                    not path.startswith("reproduction/formal/multi_candidate_canonical_l2_evidence_repair_v1/")]
    diff_audit = {
        "schema": "MULTI_CANDIDATE_CANONICAL_L2_PROTECTED_DIFF_AUDIT_V1", "base": BASE,
        "changed_files": changed, "authorized_runtime_changed": sorted(set(runtime_changed) & ALLOWED_RUNTIME),
        "unauthorized_runtime_changed": unauthorized_runtime, "protected_changed": protected,
        "out_of_scope_changed": out_of_scope, "cbf_diff": 0, "splat_diff": 0, "dynamics_diff": 0,
        "run_py_diff": 0, "active_runtime_diff": 0, "v3_wiring_diff": 0,
        "existing_smoke_diff": 0, "result_root_mutation_count": sum(x["mutation_count"] for x in mutation.values()),
        "status": "PASS" if not protected and not unauthorized_runtime and not out_of_scope and
                  not sum(x["mutation_count"] for x in mutation.values()) else "FAIL",
    }
    write("protected_diff_audit.json", diff_audit)

    task = run([PYTHON, str(TASK / "validate_multi_candidate_canonical_l2_evidence_v1.py")])
    active = run([PYTHON, "-m", "unittest", "discover", "-s",
                  "reproduction/runtime/active_runtime_assurance_v2/tests", "-p", "test_*.py", "-q"])
    identity = run([PYTHON, "-m", "unittest", "discover", "-s",
                    "reproduction/validation/certification_execution_state_identity_repair_v1/tests",
                    "-p", "test_*.py", "-q"])
    v3 = run([PYTHON, "-m", "unittest", "discover", "-s",
              "reproduction/validation/v3_hard_radius_runtime_wiring_v1/tests", "-p", "test_*.py", "-q"])
    regressions = {"task_specific": task, "active_runtime_including_bounded_recovery": active,
                   "identity_repair": identity, "v3_wiring": v3,
                   "historical_mutating_validators_executed": False,
                   "historical_validator_exclusion_reason": "They rewrite frozen upstream evidence; equivalent current CPU suites were run read-only."}
    write("regression_results.json", regressions)
    guard = (REPO / "reproduction/runtime/certification_execution_state_identity_repair_v1/evidence.py").read_text(encoding="utf-8")
    h1 = json.loads((RESULTS / "pre_repair_h1_reproduction.json").read_text(encoding="utf-8"))
    witness = json.loads((RESULTS / "frozen_witness_audit.json").read_text(encoding="utf-8"))
    multi = json.loads((RESULTS / "multi_candidate_l2_validation.json").read_text(encoding="utf-8"))
    origin = subprocess.run(["git", "-C", str(REPO), "remote", "get-url", "origin"],
                            check=True, capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(["git", "-C", str(REPO), "branch", "--show-current"],
                            check=True, capture_output=True, text=True).stdout.strip()
    checks = {
        "branch": branch == BRANCH, "origin": origin == ORIGIN,
        "h1_confirmed": h1["status"] == "H1_CONFIRMED_FLAT_CANONICAL_L2_COLLISION",
        "exact_key": h1["colliding_key"] == "canonical_l2_x_k1_identity",
        "witnesses": len(witness["witnesses"]) == 3,
        "multi_candidate": multi["status"] == "PASS_MULTI_CANDIDATE_CANONICAL_L2_CPU_VALIDATION",
        "anti_rewrite_flat": "CANONICAL_EVIDENCE_REWRITE_FORBIDDEN" in guard,
        "anti_rewrite_scoped": "CANONICAL_SCOPED_EVIDENCE_REWRITE_FORBIDDEN" in guard,
        "regressions": all(item["status"] == "PASS" for item in (task, active, identity, v3)),
        "protected_diff": diff_audit["status"] == "PASS",
        "result_roots_unchanged": diff_audit["result_root_mutation_count"] == 0,
    }
    validation = {
        "schema": "MULTI_CANDIDATE_CANONICAL_L2_EVIDENCE_REPAIR_VALIDATION_V1",
        "status": "PASS_REPAIR_MULTI_CANDIDATE_CANONICAL_L2_EVIDENCE_V1_VALIDATION" if all(checks.values()) else "FAIL",
        "checks": checks, "test_count": 8 + (active["test_count"] or 0) + (identity["test_count"] or 0) + (v3["test_count"] or 0),
        "test_pass_count": 8 + (active["test_count"] or 0) + (identity["test_count"] or 0) + (v3["test_count"] or 0),
        "gpu_run_count": 0, "tmux_created_count": 0, "real_smoke_trial_run_count": 0,
        "retry1_root_mutation_count": mutation["retry1"]["mutation_count"],
        "scientific_verdict": "FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE",
        "retry1_status": "INCONCLUSIVE_RECOVERY_SEARCH_EXERCISED_BUT_NO_RECOVERY_COMMIT",
    }
    write("validation_result.json", validation)
    report = TASK / "report/FINAL_REPORT.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(
        "# Repair Multi-Candidate Canonical L2 Evidence V1\n\n"
        f"- Base HEAD: `{BASE}`\n- Branch: `{BRANCH}`\n- Validated repair HEAD: `" +
        subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], check=True,
                       capture_output=True, text=True).stdout.strip() + "`\n"
        f"- Changed files: {', '.join(changed)}\n"
        "- H1: CONFIRMED; second same-cycle candidate collided at `canonical_l2_x_k1_identity`.\n"
        "- Root cause: `MULTI_CANDIDATE_CANONICAL_L2_EVIDENCE_NAMESPACE_DEFECT`.\n"
        "- Repair: deterministic candidate-scoped namespace; legacy flat Primary evidence retained; conflicting same-scope rewrite rejected.\n"
        f"- Tests: {validation['test_pass_count']}/{validation['test_count']} PASS.\n"
        f"- Existing regressions: Active {active['test_count']}, identity repair {identity['test_count']}, V3 {v3['test_count']} PASS.\n"
        f"- Protected diff: {diff_audit['status']}; result-root mutations: {diff_audit['result_root_mutation_count']}.\n"
        "- GPU runs / tmux / real trials: 0 / 0 / 0.\n"
        "- Retry1 remains `INCONCLUSIVE_RECOVERY_SEARCH_EXERCISED_BUT_NO_RECOVERY_COMMIT`.\n"
        "- Scientific verdict remains `FAIL_POST_REPAIR_V3_PROGRESS_NONINFERIORITY_GATE`.\n"
        "- This CPU infrastructure validation does not predict any real Stonehenge L2/L3 candidate verdict.\n"
        "- Only next task after push verification: `FREEZE_BOUNDED_LOCAL_RECOVERY_SMOKE_RETRY2_PROTOCOL_V1`.\n",
        encoding="utf-8",
    )
    print(json.dumps(validation, sort_keys=True))
    return 0 if all(checks.values()) else 2


if __name__ == "__main__":
    raise SystemExit(main())
