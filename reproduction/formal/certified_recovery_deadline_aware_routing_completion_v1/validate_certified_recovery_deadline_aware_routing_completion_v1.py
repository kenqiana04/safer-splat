from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


BASE_HEAD = "e61798341f956f9960b5e5607ba6fdccc5547c36"
TASK = Path(__file__).resolve().parent
REPO = TASK.parents[2]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(REPO), *args], text=True).strip()


checks: list[dict[str, object]] = []


def check(name: str, ok: bool, detail: str) -> None:
    checks.append({"name": name, "pass": bool(ok), "detail": detail})


required = [
    "README.md", "DESIGN_INPUT_LOCK.json", "SOURCE_SEMANTICS_AUDIT.json",
    "DEADLINE_ROUTING_SEMANTICS_CLASSIFICATION.json", "ROUTING_COMPLETION_TRUTH_TABLE.md",
    "CERTIFIED_RECOVERY_DEADLINE_AWARE_ROUTING_COMPLETION_V1_SPEC.md",
    "ROUTING_COMPLETION_IMPLEMENTATION_PLAN.md", "ROUTING_COMPLETION_COUNTERFACTUAL_AUDIT.json",
    "ROUTING_COMPLETION_PROOF_OBLIGATIONS.md", "DESIGN_EXECUTION_LOCK.json",
    "FINAL_DECISION.json", "downstream_handoff.json", "DRAFT_PR_BODY.md",
    "report/REPORT_DESIGN_CERTIFIED_RECOVERY_DEADLINE_AWARE_ROUTING_COMPLETION_V1.md",
    "validate_certified_recovery_deadline_aware_routing_completion_v1.py",
]
for rel in required:
    check("file:" + rel, (TASK / rel).is_file(), "required task-local artifact")

try:
    head = git("rev-parse", "HEAD")
    check("base_is_ancestor", subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor", BASE_HEAD, head]).returncode == 0, "base reachable")
    check("branch", git("branch", "--show-current") == "design-certified-recovery-deadline-aware-routing-completion-v1", git("branch", "--show-current"))
    origin = git("remote", "get-url", "origin")
    check("origin", origin == "git@github-kenqiana04-safer-splat-current:kenqiana04/safer-splat.git", origin)
except Exception as exc:
    check("git_identity", False, repr(exc))

try:
    classification = json.loads((TASK / "DEADLINE_ROUTING_SEMANTICS_CLASSIFICATION.json").read_text())
    counter = json.loads((TASK / "ROUTING_COMPLETION_COUNTERFACTUAL_AUDIT.json").read_text())
    source_audit = json.loads((TASK / "SOURCE_SEMANTICS_AUDIT.json").read_text())
    lock = json.loads((TASK / "DESIGN_INPUT_LOCK.json").read_text())
    execution = json.loads((TASK / "DESIGN_EXECUTION_LOCK.json").read_text())
    check("classification_case", classification.get("overall_case") == "D", str(classification.get("overall_case")))
    check("classification_confidence", classification.get("confidence") == "HIGH", str(classification.get("confidence")))
    check("warning_count", classification["warning"]["observed"].startswith("27 "), classification["warning"]["observed"])
    check("expired_count", classification["expired"]["observed"].startswith("7 "), classification["expired"]["observed"])
    check("source_status", source_audit.get("status") == "PASS_SOURCE_SEMANTICS_SUFFICIENT", str(source_audit.get("status")))
    check("counter_warning", counter.get("warning_boundary_rows") == 27, str(counter.get("warning_boundary_rows")))
    check("counter_expired", counter.get("expired_boundary_rows") == 7, str(counter.get("expired_boundary_rows")))
    check("counter_no_recovery_action", counter.get("recovery_action_reroutes") == 0, str(counter.get("recovery_action_reroutes")))
    check("counter_no_plant_change", counter.get("plant_outcome_changes") == 0, str(counter.get("plant_outcome_changes")))
    check("counter_no_unknown_fail", counter.get("unknown_or_fail_admitted") == 0, str(counter.get("unknown_or_fail_admitted")))
    check("counter_no_ambiguity", counter.get("rule_ambiguity") == 0, str(counter.get("rule_ambiguity")))
    check("input_base", lock.get("base_head") == BASE_HEAD, str(lock.get("base_head")))
    check("execution_scope", execution.get("runtime_implementation_performed") is False, str(execution.get("runtime_implementation_performed")))
except Exception as exc:
    check("artifact_json", False, repr(exc))

for rel, expected in json.loads((TASK / "DESIGN_INPUT_LOCK.json").read_text()).get("source_artifact_hashes", {}).items():
    if rel == "boundary_truth_table":
        path = Path("/disk1/zlab/tmp/formal85_retry3_routing_completion_diagnosis_v1/BOUNDARY_FINAL_CYCLE_TRUTH_TABLE.json")
    else:
        path = REPO / {"deadline_runtime": "reproduction/runtime/active_runtime_assurance_v2/deadline_runtime.py", "supervisor": "reproduction/runtime/active_runtime_assurance_v2/supervisor.py", "transition_table": "reproduction/specification/method_logic_closure_v2/STATE_TRANSITION_TABLE_V2.csv", "deadline_test": "reproduction/runtime/active_runtime_assurance_v2/tests/test_public_cycle_deadline.py", "deadline_backup_test": "reproduction/runtime/active_runtime_assurance_v2/tests/test_deadline_aware_backup_arbitration_row.py"}[rel]
    check("source_hash:" + rel, path.is_file() and sha256(path) == expected, str(path))

try:
    changed = [p for p in git("diff", "--name-only", BASE_HEAD, "HEAD").splitlines() if p]
    allowed_prefix = "reproduction/formal/certified_recovery_deadline_aware_routing_completion_v1/"
    check("changed_paths_task_local", all(p.startswith(allowed_prefix) for p in changed), "\n".join(changed))
    protected = [p for p in changed if p.startswith(("reproduction/runtime/", "cbf/", "splat/", "dynamics/")) or p == "run.py"]
    check("protected_diff_zero", not protected, "\n".join(protected))
except Exception as exc:
    check("git_diff", False, repr(exc))

for rel in ["README.md", "CERTIFIED_RECOVERY_DEADLINE_AWARE_ROUTING_COMPLETION_V1_SPEC.md", "ROUTING_COMPLETION_PROOF_OBLIGATIONS.md"]:
    text = (TASK / rel).read_text() if (TASK / rel).is_file() else ""
    check("scope_tokens:" + rel, all(token in text for token in ["DESIGN ONLY", "NO IMPLEMENTATION", "NO GPU"]), "scope markers")

check("gpu_runs_zero", execution.get("gpu_run_count") == 0, str(execution.get("gpu_run_count")))
check("formal85_reruns_zero", execution.get("formal85_rerun_count") == 0, str(execution.get("formal85_rerun_count")))
check("scientific_mutation_false", execution.get("scientific_result_mutation") is False, str(execution.get("scientific_result_mutation")))

status = "PASS_CERTIFIED_RECOVERY_DEADLINE_AWARE_ROUTING_COMPLETION_DESIGN_VALIDATION" if all(bool(item["pass"]) for item in checks) else "BLOCKED_CERTIFIED_RECOVERY_DEADLINE_AWARE_ROUTING_COMPLETION_DESIGN_VALIDATION"
result = {"schema": "CERTIFIED_RECOVERY_DEADLINE_AWARE_ROUTING_COMPLETION_VALIDATION_V1", "status": status, "check_count": len(checks), "checks": checks}
(TASK / "VALIDATION_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2, sort_keys=True))
raise SystemExit(0 if status.startswith("PASS_") else 1)
