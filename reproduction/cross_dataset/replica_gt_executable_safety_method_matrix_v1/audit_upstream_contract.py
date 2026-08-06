"""Reproduce PR #85's candidate-library fairness blocker from PR #84 raw blobs."""
from __future__ import annotations

import csv
import subprocess

from common import write_json
from task_config import PR84_HEAD, PR85_HEAD, REPO_ROOT, TASK_ROOT

PREFIX = "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/"


def blob(relative: str) -> str:
    return subprocess.run(["git", "show", f"{PR84_HEAD}:{PREFIX}{relative}"], cwd=REPO_ROOT, check=True, capture_output=True, text=True).stdout


def main() -> None:
    candidate = blob("candidate_library.py")
    certifier = blob("executable_safety_certifier.py")
    required = {
        "order_function_exists": "def frozen_candidate_order" in candidate,
        "caller_supplied_alternatives_ordered": "alternatives:tuple[Control,...]" in candidate,
        "certify_requires_external_alternatives": "alternative_controls:tuple[Control,...]" in certifier,
        "certifier_passes_external_alternatives_to_order": "frozen_candidate_order(state,nominal_control,alternative_controls" in certifier,
        "no_module_level_concrete_controls": "Control(" not in candidate,
        "no_fixed_slot_ids": "ALT-01-OUTWARD" not in candidate,
        "no_fixed_library_size": "template_slot_count" not in candidate,
        "braking_added_inside_order": "braking_policy.control_for_state" in candidate,
    }
    reproduction = {
        "status": "PASS_PR85_BLOCKER_REPRODUCED" if all(required.values()) else "BLOCKED_BY_UPSTREAM_METHOD_GAP_REPRODUCTION_MISMATCH",
        "pr84_head": PR84_HEAD, "pr85_head": PR85_HEAD, "checks": required,
        "gap": "Ordering is frozen, while concrete task-local alternative values, IDs, count, availability semantics, and canonical identity are absent from PR #84.",
    }
    write_json(TASK_ROOT / "audits/pr84_candidate_contract_gap.json", reproduction)
    write_json(TASK_ROOT / "audits/pr85_fairness_blocker_reproduction.json", reproduction)
    trace = [
        ("candidate_library.py", "frozen_candidate_order", "orders caller-supplied alternatives", required["caller_supplied_alternatives_ordered"]),
        ("executable_safety_certifier.py", "ExecutableSafetyCertifier.certify", "requires alternative_controls argument", required["certify_requires_external_alternatives"]),
        ("candidate_library.py", "module scope", "contains no concrete Control constructor", required["no_module_level_concrete_controls"]),
        ("candidate_library.py", "braking", "appended by frozen policy", required["braking_added_inside_order"]),
    ]
    path = TASK_ROOT / "audits/source_semantics_trace.csv"; path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        writer = csv.writer(handle, lineterminator="\n"); writer.writerow(("source", "symbol", "semantics", "verified")); writer.writerows(trace)
    if not all(required.values()):
        raise SystemExit(reproduction["status"])
    print(reproduction["status"])


if __name__ == "__main__":
    main()
