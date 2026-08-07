"""Freeze live PR identities and raw Git bytes used by the architecture spec."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from task_config import EXPECTED_PRS, TASK_ROOT


SOURCES = [
    ("17805e67b75412dc21b1a5fff4143ea3bc985f7f", "reproduction/cross_dataset/fas_cbf_core_v1_conceptual_closure/module_mapping/CURRENT_TO_CORE_V1_MODULE_MAPPING.md", "PR83 role mapping"),
    ("17805e67b75412dc21b1a5fff4143ea3bc985f7f", "reproduction/cross_dataset/fas_cbf_core_v1_conceptual_closure/state_machine/transition_table.csv", "PR83 state machine"),
    ("04ebca2b1b35124ad0e61ebed96e491c9edae4bb", "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/adapters/normative_dynamics_adapter.py", "PR84 frozen dynamics"),
    ("04ebca2b1b35124ad0e61ebed96e491c9edae4bb", "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/certifier/state_machine.py", "PR84 executable states"),
    ("04ebca2b1b35124ad0e61ebed96e491c9edae4bb", "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/proof_artifacts/braking_policy_derivation.md", "PR84 braking witness"),
    ("d4f20f44a810afc2d6379853a286a3e18b175221", "reproduction/cross_dataset/replica_gt_executable_safety_method_matrix_v1/alternative_library/directional_library.py", "PR86 finite directional library"),
    ("fbe67f0c607add7f8049d4ce75e8f9e1ae8498d9", "reproduction/cross_dataset/resume_replica_gt_executable_safety_activated_benchmark_v1/benchmark/one_step_records.csv", "PR87 activated and representative records"),
    ("047513b5e612f91e63ab1e7054815615cb455fd7", "reproduction/cross_dataset/core_v1_cross_environment_activation_portability_audit_v1/report/REPORT_AUDIT_CORE_V1_CROSS_ENVIRONMENT_ACTIVATION_PORTABILITY_V1.md", "PR89 portability report"),
    ("48db34d4e61f019fcd2b578c04cc87eefb00747a", "reproduction/causal_audit/core_v1_representative_shortfall_causal_decomposition_v1/report/REPORT_AUDIT_CORE_V1_REPRESENTATIVE_SHORTFALL_CAUSAL_DECOMPOSITION_V1.md", "PR90 causal report"),
    ("48db34d4e61f019fcd2b578c04cc87eefb00747a", "reproduction/causal_audit/core_v1_representative_shortfall_causal_decomposition_v1/decision/final_causal_decomposition_decision.json", "PR90 final decision"),
    ("e8ec67d5585f9634ae6a5d4991eac5f9e4abfbae", "reproduction/decision/core_v1_actionable_factor_ranking_v1/report/REPORT_RANK_CORE_V1_ACTIONABLE_FACTORS_AND_SELECT_ONE_BOUNDED_NEXT_STEP_V1.md", "PR91 ranking report"),
    ("e8ec67d5585f9634ae6a5d4991eac5f9e4abfbae", "reproduction/decision/core_v1_actionable_factor_ranking_v1/actions/action_cards/A1.md", "PR91 selected action card"),
    (None, "reproduction/experiment_protocol_freeze_v1/frozen_configs/certified_start_safe.json", "frozen Start-Safe evidence"),
    (None, "reproduction/experiment_protocol_freeze_v1/frozen_configs/dt_verification_h1.json", "frozen DT H1"),
    (None, "reproduction/experiment_protocol_freeze_v1/frozen_configs/dt_verification_h2.json", "frozen DT H2"),
    (None, "reproduction/experiment_protocol_freeze_v1/frozen_configs/dt_verification_h3.json", "frozen DT H3"),
    (None, "reproduction/experiment_protocol_freeze_v1/frozen_configs/v4c_hce_v0.json", "frozen HCE recovery"),
]


def run(*args: str) -> str:
    return subprocess.check_output(args, text=True, encoding="utf-8").strip()


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def freeze_prs() -> None:
    for number, (branch, oid) in EXPECTED_PRS.items():
        payload = json.loads(run("gh", "pr", "view", str(number), "--repo", "kenqiana04/safer-splat", "--json", "number,state,isDraft,mergedAt,mergeable,baseRefName,baseRefOid,headRefName,headRefOid,url"))
        assert payload["number"] == number and payload["state"] == "OPEN" and payload["isDraft"] is True
        assert payload["mergedAt"] is None and payload["mergeable"] == "MERGEABLE"
        assert payload["headRefName"] == branch and payload["headRefOid"] == oid
        payload["freeze_status"] = "PASS_LIVE_PR_IDENTITY_MATCH"
        write_json(TASK_ROOT / "input_freeze" / f"pr{number}_identity.json", payload)


def freeze_sources() -> None:
    records = []
    for commit, path, role in SOURCES:
        resolved = commit or run("git", "rev-list", "-1", "HEAD", "--", path)
        raw = subprocess.check_output(["git", "show", f"{resolved}:{path}"])
        blob = run("git", "rev-parse", f"{resolved}:{path}")
        records.append({"commit": resolved, "path": path, "role": role, "git_blob": blob, "sha256": hashlib.sha256(raw).hexdigest(), "size": len(raw), "verification": "PASS_RAW_GIT_OBJECT_MATCH"})
    write_json(TASK_ROOT / "input_freeze" / "protected_source_hashes.json", {"status": "PASS_CORE_CAUSAL_PROTECTED_SOURCE_FREEZE", "record_count": len(records), "records": records, "scope": "read-only raw Git object verification"})


def main() -> None:
    freeze_prs(); freeze_sources()
    print("PASS_CORE_CAUSAL_UPSTREAM_FREEZE")


if __name__ == "__main__":
    main()
