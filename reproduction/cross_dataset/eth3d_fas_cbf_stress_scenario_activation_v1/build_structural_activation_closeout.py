#!/usr/bin/env python3
"""Fail-closed Case-D closeout if the 200k shadow search cannot reach a stage."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from task_config_v2 import (  # noqa: F401
    BASE_BRANCH,
    BASE_HEAD,
    BRANCH,
    CANDIDATE_STATE_LIMIT,
    EXPECTED,
    MAP_PLY,
    TASK_NAME,
    TASK_ROOT,
    atomic_json,
    sha256_file,
)


FINAL_STATUS = "NO_ETH3D_FROZEN_STATE_SET_SUFFICIENTLY_ACTIVATES_FAS_CBF_STAGE_H3_DISCRETE_TIME"
FINAL_DECISION = "FREEZE_STRUCTURAL_ACTIVATION_LIMIT_AND_USE_EXISTING_CERTIFIED_MODULE_CASES"
ONLY_NEXT_TASK = "ASSEMBLE_FAS_CBF_MODULE_EVIDENCE_FROM_ETH3D_AND_EXISTING_FROZEN_CASES_V1"


def main() -> int:
    candidate = json.loads(
        (TASK_ROOT / "candidate_pool/candidate_pool_summary.json").read_text(
            encoding="utf-8"
        )
    )
    if candidate["status"] != "CANDIDATE_POOL_EXHAUSTED_WITH_STAGE_DEFICIT":
        raise RuntimeError("Case-D closeout requires an exhausted candidate pool")
    if candidate["candidate_state_count"] != CANDIDATE_STATE_LIMIT:
        raise RuntimeError("Case-D closeout requires the frozen 200000-tuple ceiling")
    freeze = json.loads(
        (TASK_ROOT / "input_freeze/pr80_frozen_input_identity.json").read_text(
            encoding="utf-8"
        )
    )
    v1 = json.loads(
        (TASK_ROOT / "v1_semantic_audit/v1_terminal_semantics.json").read_text(
            encoding="utf-8"
        )
    )
    activation = json.loads(
        (TASK_ROOT / "v1_semantic_audit/v1_activation_semantics.json").read_text(
            encoding="utf-8"
        )
    )
    diagnostic_path = (
        TASK_ROOT / "shadow_predicates/projected_entry_frame_diagnostic.json"
    )
    diagnostic = (
        json.loads(diagnostic_path.read_text(encoding="utf-8"))
        if diagnostic_path.exists()
        else None
    )
    actions_path = TASK_ROOT / "operational_autonomy_actions.json"
    actions = (
        json.loads(actions_path.read_text(encoding="utf-8")).get("actions", [])
        if actions_path.exists()
        else []
    )
    system = json.loads(
        (TASK_ROOT / "report/system_final_state.json").read_text(encoding="utf-8")
    )
    compact = json.loads(
        (TASK_ROOT / "report/compact_structural_evidence_validation.json").read_text(
            encoding="utf-8"
        )
    )
    omissions = json.loads(
        (TASK_ROOT / "report/formal_dependent_artifact_omissions.json").read_text(
            encoding="utf-8"
        )
    )
    counts = candidate["qualified_pool_counts"]
    final = {
        "FINAL_STATUS": FINAL_STATUS,
        "FINAL_DECISION": FINAL_DECISION,
        "ONLY_NEXT_TASK": ONLY_NEXT_TASK,
        "structural_stage": "H3_DISCRETE_TIME_ENDPOINT_UNSAFE_STRATUM",
        "candidate_state_count": candidate["candidate_state_count"],
        "qualified_pool_counts": counts,
    }
    atomic_json(TASK_ROOT / "report/final_decision.json", final)
    handoff = {
        "status": FINAL_STATUS,
        "decision": FINAL_DECISION,
        "only_next_task": ONLY_NEXT_TASK,
        "system_final_status": system["status"],
        "unresolved_evidence": [
            "The frozen ETH3D map, double-integrator, Start-Safe threshold, and bounded velocity did not yield the required endpoint-unsafe/QP-feasible stratum within the preregistered 200000 plant-free tuple ceiling.",
            "No V2 registry, smoke, or formal controller matrix was authorized after the activation gate failed.",
        ],
    }
    atomic_json(TASK_ROOT / "report/downstream_handoff.json", handoff)
    counters = {
        "map_training_count": 0,
        "map_mutation_count": 0,
        "dataset_count": 1,
        "scene_count": 1,
        "formal_map_count": 1,
        "candidate_state_count": candidate["candidate_state_count"],
        "shadow_probe_count": candidate["shadow_probe_count"],
        "v2_scenario_count": 0,
        "v2_registry_generation_count": 0,
        "controller_smoke_run_count": 0,
        "controller_formal_run_count": 0,
        "per_method_runs": {},
        "reference_reads_during_controller_decision": 0,
        "scenario_deletion_after_formal": 0,
        "method_tuning": 0,
        "control_parameter_changes": 0,
        "logger_only_fixes": 1,
        "shadow_predicate_fixes": 0,
        "operational_autonomy_actions": len(actions),
        "task_owned_process_cleanup": sum(
            int(action.get("termination_signal") not in {None, "NONE_NATURAL_EXIT"})
            * max(1, len(action.get("affected_pids", [])))
            for action in actions
        ),
    }
    atomic_json(TASK_ROOT / "report/execution_counters.json", counters)
    manifest = {
        "task": TASK_NAME,
        "state": "COMPLETED_STRUCTURAL_ACTIVATION_LIMIT",
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "phase_status": {
            "input_freeze": freeze["status"],
            "v1_audit": v1["status"],
            "candidate_search": candidate["status"],
            "registry": "NOT_RUN_FAIL_CLOSED",
            "smoke": "NOT_RUN_FAIL_CLOSED",
            "formal": "NOT_RUN_FAIL_CLOSED",
        },
        "counters": counters,
        "final": final,
    }
    atomic_json(TASK_ROOT / "run_manifest.json", manifest)
    gates = {
        "candidate_ceiling_reached": candidate["candidate_state_count"]
        == CANDIDATE_STATE_LIMIT,
        "formal_rollout_results_not_read_for_selection": candidate[
            "formal_rollout_result_read_count"
        ]
        == 0,
        "plant_not_executed_during_search": candidate["plant_execution_count"] == 0,
        "map_identity_unchanged": sha256_file(MAP_PLY)
        == EXPECTED["map_ply_sha256"],
        "v1_preserved": freeze["pr80_preserved"],
        "endpoint_unsafe_deficit_real": counts.get("G3_ENDPOINT_UNSAFE", 0) < 1,
        "no_registry": not (TASK_ROOT / "scenario_registry_v2/scenario_registry.json").exists(),
        "no_smoke": not any((TASK_ROOT / "smoke/results").glob("*.json"))
        if (TASK_ROOT / "smoke/results").exists()
        else True,
        "no_formal": not any((TASK_ROOT / "formal/results").glob("*.json"))
        if (TASK_ROOT / "formal/results").exists()
        else True,
        "final_system_boundary": system["status"] == "PASS_FINAL_SYSTEM_BOUNDARY",
        "compact_structural_evidence": compact["status"]
        == "PASS_COMPACT_STRUCTURAL_EVIDENCE"
        and compact["structural_figure_count"] == 6
        and compact["stage_summary_rows"] == 10,
        "formal_dependent_artifacts_explicitly_omitted": omissions["status"]
        == "FORMAL_DEPENDENT_ARTIFACTS_NOT_GENERATED_FAIL_CLOSED",
    }
    validation = {
        "status": "PASS_CASE_D_STRUCTURAL_ACTIVATION_LIMIT_VALIDATION"
        if all(gates.values())
        else "CASE_D_STRUCTURAL_ACTIVATION_LIMIT_VALIDATION_FAILED",
        "gates": gates,
        "final": final,
    }
    atomic_json(TASK_ROOT / "report/validation_result.json", validation)
    if not all(gates.values()):
        raise RuntimeError(validation)

    diagnostic_text = (
        f"The independent projected-entry-frame diagnostic evaluated {diagnostic['tuple_count']} additional plant-free engineering tuples: "
        f"QP-feasible endpoint-unsafe count={diagnostic['endpoint_unsafe_count']}."
        if diagnostic
        else "No auxiliary projected-entry-frame diagnostic was required."
    )
    lines = [
        f"# {TASK_NAME}",
        "",
        f"**{FINAL_STATUS}**",
        "",
        "## Outcome",
        "",
        "The preregistered activation gate failed closed on the same frozen ETH3D Delivery Area map. No V2 registry was locked and no smoke or formal controller rollout was started.",
        "",
        "## Frozen lineage",
        "",
        f"- Branch/base/head: `{BRANCH}` / `{BASE_BRANCH}` / `{BASE_HEAD}`",
        f"- Map PLY SHA-256: `{EXPECTED['map_ply_sha256']}`",
        f"- Canonical tree SHA-256: `{EXPECTED['canonical_tree_sha256']}`",
        f"- Reference mesh SHA-256: `{EXPECTED['reference_mesh_sha256']}`",
        f"- Method code SHA-256: `{freeze['identities']['method_code_sha256']}`",
        f"- Baseline core SHA-256: `{freeze['identities']['baseline_core_sha256']}`",
        "",
        "## V1 semantic audit",
        "",
        v1["explanations"]["twenty_completions"],
        v1["explanations"]["m0_qp_infeasible_80"],
        v1["explanations"]["m1_m4_60_qp_plus_20_rejected"],
        f"The corrected audit records `{activation['defect']['code']}` without changing PR #80.",
        "",
        "## Bounded shadow search",
        "",
        f"- Candidate tuples: {candidate['candidate_state_count']} / {CANDIDATE_STATE_LIMIT}",
        f"- Qualified strata: `{json.dumps(counts, sort_keys=True)}`",
        f"- Formal rollout results read: {candidate['formal_rollout_result_read_count']}",
        f"- Plant executions: {candidate['plant_execution_count']}",
        f"- {diagnostic_text}",
        "",
        "The pool contains sufficient G0, G1, G2, G3 margin/endpoint-safe-segment-unsafe, and G4 cases, but no required endpoint-unsafe/QP-feasible H3 case. The task therefore does not relabel margin violations as endpoint collisions and does not relax the activation definition.",
        "Six structural evidence figures and a ten-row stage summary were generated. Eighteen formal-dependent figures and all registry/formal paired artifacts are explicitly recorded as NOT_GENERATED_FAIL_CLOSED rather than populated with placeholder data.",
        "",
        "## Boundary",
        "",
        "Map training/mutation, dataset switching, method tuning, control-parameter changes, reference-to-controller reads, registry generation, smoke runs, and formal runs are all zero.",
        f"GPU final: `{json.dumps(system['gpu_final'], sort_keys=True)}`",
        f"Watchdog/SSH final: `{json.dumps(system['watchdog_ssh_final'], sort_keys=True)}`",
        "",
        "## Decision",
        "",
        f"- FINAL_STATUS: `{FINAL_STATUS}`",
        f"- FINAL_DECISION: `{FINAL_DECISION}`",
        f"- Only next task: `{ONLY_NEXT_TASK}`",
        "",
    ]
    report = (
        TASK_ROOT
        / "report/REPORT_REFINE_FAS_CBF_STRESS_SCENARIO_ACTIVATION_ON_FROZEN_ETH3D_MAP_V1.md"
    )
    report.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    pr_body = f"""## Scope

PR #80 and its Case-B result are preserved. This continuation performed the preregistered plant-free activation search on the same frozen ETH3D map and failed closed before registry lock.

## Evidence

- candidate tuples: `{candidate['candidate_state_count']}`
- qualified strata: `{json.dumps(counts, sort_keys=True)}`
- V1 semantic defect recorded without history rewrite
- H2 global constraint reduction reconciled against zero designated-G2 entry
- no map retraining, dataset switch, method tuning, smoke, or formal rollout

## Decision

- FINAL_STATUS: `{FINAL_STATUS}`
- FINAL_DECISION: `{FINAL_DECISION}`
- Only next task: `{ONLY_NEXT_TASK}`
"""
    (TASK_ROOT / "report/DRAFT_PR_BODY.md").write_text(
        pr_body, encoding="utf-8", newline="\n"
    )
    print(json.dumps(validation, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
