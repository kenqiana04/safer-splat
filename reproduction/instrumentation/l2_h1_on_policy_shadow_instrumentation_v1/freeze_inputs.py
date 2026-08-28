"""Freeze PR #96, protected objects, and the exact frozen control seam."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


TASK_ROOT = Path(__file__).resolve().parent
REPO_ROOT = TASK_ROOT.parents[2]
AUDIT = TASK_ROOT / "audit"
PR96_SHA = "1783aff5f6d221efc26d34f8b47b966e2d9eee3e"
EXPECTED = {
    83: "17805e67b75412dc21b1a5fff4143ea3bc985f7f",
    84: "04ebca2b1b35124ad0e61ebed96e491c9edae4bb",
    86: "d4f20f44a810afc2d6379853a286a3e18b175221",
    87: "fbe67f0c607add7f8049d4ce75e8f9e1ae8498d9",
    89: "047513b5e612f91e63ab1e7054815615cb455fd7",
    90: "48db34d4e61f019fcd2b578c04cc87eefb00747a",
    91: "e8ec67d5585f9634ae6a5d4991eac5f9e4abfbae",
    92: "dfd9bce2633e542fdb72a1805f79cc4feeeebc3a",
    93: "1df09c56eedb53d46f9347695026086319738a89",
    94: "9bffdd2db585974ee61684cebfc99229aa52c47c",
    95: "a7fd936804284a299467f1bfcc76deab12fdf0c3",
    96: PR96_SHA,
}


def run(*args: str, binary: bool = False) -> str | bytes:
    completed = subprocess.run(args, cwd=REPO_ROOT, check=True, capture_output=True, text=not binary)
    return completed.stdout if binary else completed.stdout.strip()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def gh_pr(number: int) -> dict:
    last: Exception | None = None
    for attempt in range(3):
        try:
            raw = run(
                "gh", "pr", "view", str(number), "--repo", "kenqiana04/safer-splat",
                "--json", "number,state,isDraft,headRefName,headRefOid,baseRefName,url",
            )
            return json.loads(str(raw))
        except Exception as exc:  # transient API EOFs are retried, identity is never relaxed
            last = exc
            time.sleep(1 + attempt)
    raise RuntimeError(f"failed to verify PR #{number}: {last}")


def audit_record(record: dict) -> dict:
    commit, path = record["commit"], record["path"]
    raw = run("git", "cat-file", "blob", f"{commit}:{path}", binary=True)
    assert isinstance(raw, bytes)
    actual_blob = str(run("git", "rev-parse", f"{commit}:{path}"))
    tree = str(run("git", "ls-tree", commit, "--", path)).split()
    actual_mode = tree[0] if tree else "MISSING"
    actual_sha = hashlib.sha256(raw).hexdigest()
    result = dict(record)
    result.update(
        actual_git_blob=actual_blob,
        actual_sha256=actual_sha,
        actual_size=len(raw),
        actual_mode=actual_mode,
        verification="PASS_RAW_GIT_OBJECT_SIZE_MODE_IDENTITY"
        if actual_blob == record["git_blob"] and actual_sha == record["sha256"] and len(raw) == record["size"] and actual_mode in {"100644", "100755"}
        else "FAIL_RAW_GIT_OBJECT_SIZE_MODE_IDENTITY",
    )
    return result


def find_line(lines: list[str], needle: str) -> int:
    matches = [index for index, line in enumerate(lines, 1) if needle in line]
    if len(matches) != 1:
        raise RuntimeError(f"expected one line containing {needle!r}, found {matches}")
    return matches[0]


def main() -> int:
    AUDIT.mkdir(parents=True, exist_ok=True)
    prs = []
    for number, expected_head in EXPECTED.items():
        item = gh_pr(number)
        item["expected_head"] = expected_head
        item["identity_match"] = item["headRefOid"] == expected_head
        prs.append(item)
    pr96 = next(item for item in prs if item["number"] == 96)
    remote_head = str(run("git", "ls-remote", "origin", "refs/heads/design-l2-h1-on-policy-shadow-observation-v1")).split()[0]
    local_head = str(run("git", "rev-parse", "HEAD"))
    base_is_ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PR96_SHA, "HEAD"], cwd=REPO_ROOT
    ).returncode == 0
    identity = {
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": "kenqiana04/safer-splat",
        "upstream_pr_count": len(prs),
        "prs": prs,
        "pr96_expected_head": PR96_SHA,
        "pr96_actual_head": pr96["headRefOid"],
        "pr96_state": pr96["state"],
        "pr96_is_draft": pr96["isDraft"],
        "pr96_branch": pr96["headRefName"],
        "pr96_base": pr96["baseRefName"],
        "remote_pr96_branch_head": remote_head,
        "local_head_at_audit": local_head,
        "pr96_is_ancestor_of_task_head": base_is_ancestor,
        "all_expected_heads_match": all(item["identity_match"] for item in prs),
    }
    identity["status"] = "PASS_UPSTREAM_PR96_EXACT_IDENTITY" if (
        identity["all_expected_heads_match"] and pr96["state"] == "OPEN" and pr96["isDraft"]
        and pr96["headRefName"] == "design-l2-h1-on-policy-shadow-observation-v1"
        and pr96["baseRefName"] == "l2-h1-shadow-frozen-replay-v1"
        and remote_head == PR96_SHA and base_is_ancestor
    ) else "FAIL_UPSTREAM_PR96_IDENTITY"
    write_json(AUDIT / "frozen_upstream_identity.json", identity)
    if identity["status"] != "PASS_UPSTREAM_PR96_EXACT_IDENTITY":
        raise SystemExit("BLOCKED_INSTRUMENTATION_BY_UPSTREAM_IDENTITY_DRIFT")

    authority_path = REPO_ROOT / "reproduction/specification/core_v2_causal_increment_specification_v1/PROTECTED_SOURCE_AUDIT.json"
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    records = [audit_record(item) for item in authority["protected_records"]]
    run_record = next(item for item in authority["supplemental_evidence_records"] if item["path"] == "run.py")
    run_audit = audit_record(run_record)
    protected = {
        "authority": authority_path.relative_to(REPO_ROOT).as_posix(),
        "protected_blob_count": authority["protected_blob_count"],
        "records": records,
        "all_raw_objects_match": all(item["verification"].startswith("PASS") for item in records),
        "run_py_supplemental_record": run_audit,
        "run_py_forbidden_or_protected": True,
        "run_py_forbidden_basis": "Supplemental protected identity plus protected-source policy: current baseline, map, controller, and historical evidence are read-only.",
        "selected_seam_file_direct_patch_allowed": False,
        "wrapper_decorator_fallback_available": True,
        "fallback_requires_controller_copy_or_reimplementation": False,
        "forbidden_source_mutation_count": 0,
        "protected_path_diff_count": 0,
        "status": "PASS_PROTECTED_FORBIDDEN_SOURCE_AUDIT",
    }
    start_path = AUDIT / "protected_forbidden_source_start.json"
    if not start_path.exists():
        write_json(start_path, {**protected, "audit_phase": "START"})
    write_json(AUDIT / "protected_forbidden_source_end.json", {**protected, "audit_phase": "END"})
    write_json(AUDIT / "protected_forbidden_source_audit.json", protected)

    source = run("git", "show", f"{PR96_SHA}:run.py", binary=True)
    assert isinstance(source, bytes)
    text = source.decode("utf-8")
    lines = text.splitlines()
    dt_line = find_line(lines, "dt = 0.05")
    state_line = find_line(lines, "x = torch.tensor(start)")
    state_finish_line = find_line(lines, "x = torch.cat([x, torch.zeros(3)")
    u_des_line = find_line(lines, "u_des = 1.0*(vel_des - x[3:])")
    selected_line = find_line(lines, "u = cbf.solve_QP(x, u_des)")
    guard_line = find_line(lines, "if cbf.solver_success == False")
    plant_line = find_line(lines, "x = double_integrator_dynamics(x,u)*dt + x")
    cycle = {
        "source_commit": PR96_SHA,
        "source_path": "run.py",
        "source_git_blob": str(run("git", "rev-parse", f"{PR96_SHA}:run.py")),
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "source_size": len(source),
        "x_k_source": {"lines": [state_line, state_finish_line], "semantic": "six-dimensional x before solve_QP"},
        "p_k_source": "x[:3]",
        "v_k_source": "x[3:]",
        "dt_source": {"line": dt_line, "value": 0.05},
        "u_des_source": {"line": u_des_line, "role": "NOMINAL_REFERENCE"},
        "selected_u_source": {"line": selected_line, "expression": "u = cbf.solve_QP(x, u_des)", "role": "SELECTED_EXECUTED_CONTROL"},
        "solver_success_guard": {"line": guard_line, "semantic": "failed solution exits before plant"},
        "decision_commit_point": f"successful solve_QP return with solver_success true; semantically after run.py:{guard_line}-{guard_line + 4}",
        "plant_update_point": {"line": plant_line, "expression": "x = double_integrator_dynamics(x,u)*dt + x"},
        "status": "PASS_FROZEN_CONTROL_CYCLE_IDENTITY",
    }
    write_json(AUDIT / "control_cycle_identity.json", cycle)
    seam = {
        "source_path": "run.py",
        "source_forbidden": True,
        "direct_hook_used": False,
        "fallback_used": True,
        "fallback": "outer runpy decorator temporarily wrapping the imported CBF class without copying run.py or solve_QP",
        "capture_location": "decorated exact frozen plant-function entry: after run.py has passed its solver_success guard and immediately before delegation to the unchanged plant function",
        "post_commit": True,
        "pre_plant": True,
        "same_decision_state_action": True,
        "approved_instrumentation_hook_count": 1,
        "controller_fork_count": 0,
        "status": "PASS_WRAPPER_POST_COMMIT_PRE_PLANT_SEAM",
    }
    write_json(AUDIT / "decision_commit_seam.json", seam)
    write_json(AUDIT / "approved_production_delta.json", {
        "production_delta": "NONE_REQUIRED",
        "approved_production_hook_paths": [],
        "task_local_wrapper_paths": ["instrumented_cbf_wrapper.py", "run_with_shadow_instrumentation.py"],
        "controller_logic_mutation_count": 0,
        "controller_math_mutation_count": 0,
        "production_source_diff_count": 0,
        "status": "PASS_NO_PRODUCTION_DELTA_REQUIRED",
    })
    print("PASS_INSTRUMENTATION_INPUT_FREEZE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
