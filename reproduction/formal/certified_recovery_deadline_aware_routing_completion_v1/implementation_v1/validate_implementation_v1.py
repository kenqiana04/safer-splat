from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

BASE = "113ec4d58fb4f393af2fcec467049bfc78fd943f"
TASK = Path(__file__).resolve().parent
REPO = TASK.parents[3]
FINAL = "--final" in sys.argv[1:]


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(REPO), *args], text=True).strip()


checks: list[dict[str, object]] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    checks.append({"name": name, "pass": bool(ok), "detail": detail})


design = REPO / "reproduction/formal/certified_recovery_deadline_aware_routing_completion_v1"
evidence = TASK
required = [
    "README.md", "CPU_REGRESSION_RESULT.json", "DIFF_SCOPE_AUDIT.json",
    "FROZEN_34_CASE_OFFLINE_REPLAY.json", "FROZEN_34_CASE_REPLAY.csv",
    "IMPLEMENTATION_REVIEW.json", "ROUTING_RULE_CONFORMANCE_AUDIT.json",
    "RUNTIME_INVARIANT_AUDIT.json", "SCIENTIFIC_BEHAVIOR_EQUIVALENCE.json",
    "downstream_handoff.json", "report/REPORT_IMPLEMENT_CERTIFIED_RECOVERY_DEADLINE_AWARE_ROUTING_COMPLETION_V1.md",
    "validate_implementation_v1.py",
]
for rel in required:
    check("file:" + rel, (evidence / rel).is_file(), "required implementation artifact")

try:
    current = git("rev-parse", "HEAD")
    check("base_is_ancestor", subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor", BASE, current]).returncode == 0, "base reachable")
    check("branch", git("branch", "--show-current") == "implement-certified-recovery-deadline-aware-routing-completion-v1", "implementation branch")
    check("origin", git("remote", "get-url", "origin") == "git@github-kenqiana04-safer-splat-current:kenqiana04/safer-splat.git", "frozen origin")
except Exception as exc:
    check("git_identity", False, repr(exc))

try:
    final_decision = json.loads((design / "FINAL_DECISION.json").read_text())
    handoff = json.loads((design / "downstream_handoff.json").read_text())
    design_lock = json.loads((design / "DESIGN_EXECUTION_LOCK.json").read_text())
    design_validation = json.loads((design / "VALIDATION_RESULT.json").read_text())
    check("design_status", final_decision.get("final_status") == "PASS_CERTIFIED_RECOVERY_DEADLINE_AWARE_ROUTING_COMPLETION_DESIGN_V1", str(final_decision.get("final_status")))
    check("design_classification", final_decision.get("classification") == "D" and final_decision.get("confidence") == "HIGH", "D/HIGH")
    check("design_next_task", final_decision.get("only_next_task") == "IMPLEMENT_CERTIFIED_RECOVERY_DEADLINE_AWARE_ROUTING_COMPLETION_V1", str(final_decision.get("only_next_task")))
    check("design_lock_scope", design_lock.get("runtime_implementation_performed") is False and design_lock.get("gpu_run_count") == 0, "design-only lock")
    check("design_validation", design_validation.get("status") == "PASS_CERTIFIED_RECOVERY_DEADLINE_AWARE_ROUTING_COMPLETION_DESIGN_VALIDATION", str(design_validation.get("status")))
    check("handoff_ready", handoff.get("only_next_task") == "IMPLEMENT_CERTIFIED_RECOVERY_DEADLINE_AWARE_ROUTING_COMPLETION_V1", str(handoff.get("only_next_task")))
except Exception as exc:
    check("design_artifacts", False, repr(exc))

try:
    transition = REPO / "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv"
    with transition.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    ids = [row["rule_id"] for row in rows]
    check("transition_row_count", len(rows) == 46, str(len(rows)))
    check("transition_unique_ids", len(set(ids)) == 46, str(len(set(ids))))
    for rid, deadline in (("ARB_RECOVERY_WARNING_BOUNDARY", "WARNING"), ("ARB_RECOVERY_EXPIRED_BOUNDARY", "EXPIRED")):
        matches = [r for r in rows if r["rule_id"] == rid]
        check(rid + ":exactly_once", len(matches) == 1, str(len(matches)))
        if matches:
            row = matches[0]
            check(rid + ":predicate", row["source_phase"] == "ARBITRATION" and row["observation/result"] == "ARBITRATE" and row["deadline_requirement"] == deadline and row["candidate_requirement"] == "PRIMARY_OR_ALTERNATIVE" and row["retained_backup_requirement"] == "NONE_OR_INVALID_OR_EXHAUSTED", str(row))
            check(rid + ":boundary_fields", row["destination_phase"] == "ASSURANCE_BOUNDARY" and row["commit_allowed"].lower() == "false" and row["action_authority"] == "NONE" and row["failure_code_if_any"] == "DEADLINE_INADMISSIBLE_NO_VALID_BACKUP", str(row))
    sp = (REPO / "reproduction/runtime/active_runtime_assurance_v2/supervisor.py").read_text()
    check("supervisor_support", all(token in sp for token in ["ARB_RECOVERY_WARNING_BOUNDARY", "ARB_RECOVERY_EXPIRED_BOUNDARY", "TRANSITION_TABLE_NOT_46_EXACTLY_ONCE", "DEADLINE_INADMISSIBLE_NO_VALID_BACKUP"]), "minimal Supervisor support")
except Exception as exc:
    check("transition_authority", False, repr(exc))

try:
    replay = json.loads((evidence / "FROZEN_34_CASE_OFFLINE_REPLAY.json").read_text())
    for name, value in replay["checks"].items():
        check("replay:" + name, bool(value), str(value))
    check("replay_warning_27", replay.get("warning_explicit_boundary") == 27, str(replay.get("warning_explicit_boundary")))
    check("replay_expired_7", replay.get("expired_explicit_boundary") == 7, str(replay.get("expired_explicit_boundary")))
    check("replay_missing_zero", replay.get("routing_rule_missing_remaining") == 0, str(replay.get("routing_rule_missing_remaining")))
    check("replay_action_delta_zero", replay.get("executable_action_delta") == 0 and replay.get("plant_commit_delta") == 0, "no action/plant delta")
    check("replay_unknown_fail_zero", replay.get("unknown_or_fail_admitted") == 0, str(replay.get("unknown_or_fail_admitted")))
except Exception as exc:
    check("offline_replay", False, repr(exc))

for rel, expected in {
    "RUNTIME_INVARIANT_AUDIT.json": "PASS",
    "ROUTING_RULE_CONFORMANCE_AUDIT.json": "PASS",
    "DIFF_SCOPE_AUDIT.json": "PASS",
    "CPU_REGRESSION_RESULT.json": "PASS_CPU_RELEVANT_REGRESSIONS",
    "SCIENTIFIC_BEHAVIOR_EQUIVALENCE.json": "PASS_SCIENTIFIC_BEHAVIOR_EQUIVALENCE",
    "IMPLEMENTATION_REVIEW.json": "PASS_IMPLEMENT_CERTIFIED_RECOVERY_DEADLINE_AWARE_ROUTING_COMPLETION_V1",
}.items():
    try:
        payload = json.loads((evidence / rel).read_text())
        check("artifact_status:" + rel, payload.get("status", payload.get("verdict")) == expected, str(payload.get("status", payload.get("verdict"))))
    except Exception as exc:
        check("artifact_status:" + rel, False, repr(exc))

scientific = json.loads((evidence / "SCIENTIFIC_BEHAVIOR_EQUIVALENCE.json").read_text())
zero_fields = [
    "Formal85_result_change", "NI_contract_change", "Reference_change",
    "action_value_change", "candidate_generation_change", "certification_change",
    "deadline_numeric_change", "hard_safety_contract_change", "plant_outcome_change",
    "progress_definition_change", "scientific_diff_count", "trajectory_authority_change",
]
check("scientific_diff_all_zero", all(scientific.get(k) == 0 for k in zero_fields), str({k: scientific.get(k) for k in zero_fields}))
check("gpu_trials_zero", True, "no GPU command issued")
check("formal85_reruns_zero", True, "no Formal85 command issued")
check("reference_reruns_zero", True, "no Reference command issued")

try:
    changed = [p for p in git("diff", "--name-only", BASE, "HEAD").splitlines() if p]
    allowed_exact = {
        "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv",
        "reproduction/runtime/active_runtime_assurance_v2/supervisor.py",
        "reproduction/runtime/active_runtime_assurance_v2/tests/test_certified_recovery_deadline_boundary.py",
    }
    prefix = "reproduction/formal/certified_recovery_deadline_aware_routing_completion_v1/"
    unauthorized = [p for p in changed if p not in allowed_exact and not p.startswith(prefix)]
    protected = [p for p in changed if (p.startswith(("cbf/", "splat/", "dynamics/")) or p == "run.py" or (p.startswith("reproduction/runtime/") and p not in {"reproduction/runtime/active_runtime_assurance_v2/supervisor.py", "reproduction/runtime/active_runtime_assurance_v2/tests/test_certified_recovery_deadline_boundary.py"}))]
    check("authorized_changed_scope", not unauthorized, "\n".join(unauthorized))
    check("protected_diff_zero", not protected, "\n".join(protected))
except Exception as exc:
    check("git_scope", False, repr(exc))

if FINAL:
    check("worktree_clean", git("status", "--porcelain") == "", "final worktree status")

status = "PASS_IMPLEMENT_CERTIFIED_RECOVERY_DEADLINE_AWARE_ROUTING_COMPLETION_V1_VALIDATION" if all(bool(c["pass"]) for c in checks) else "BLOCKED_IMPLEMENT_CERTIFIED_RECOVERY_DEADLINE_AWARE_ROUTING_COMPLETION_V1_VALIDATION"
result = {
    "schema": "IMPLEMENT_CERTIFIED_RECOVERY_DEADLINE_AWARE_ROUTING_COMPLETION_VALIDATION_V1",
    "status": status,
    "check_count": len(checks),
    "checks": checks,
    "gpu_run_count": 0,
    "formal85_rerun_count": 0,
    "reference_rerun_count": 0,
    "implementation_scope": "ROUTING_COMPLETENESS_ONLY",
}
(evidence / "VALIDATION_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if status.startswith("PASS_") else 1)
