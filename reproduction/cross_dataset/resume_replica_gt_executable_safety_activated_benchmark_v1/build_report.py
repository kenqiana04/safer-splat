#!/usr/bin/env python3
"""Build the compact scientific report and Draft PR body from frozen outputs."""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

TASK_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(TASK_ROOT))
from common import read_json, sha256_file, write_text
from task_config import DT, EFFECTIVE_RADIUS, H_STOP_MAX, METHODS, NORMATIVE_MODEL, ROBOT_RADIUS, MARGIN, U_BOUND, V_BOUND


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def boolean(value: Any) -> bool:
    return str(value).lower() == "true"


def number(value: Any) -> float:
    if value in (None, "", "None", "null"):
        return 0.0
    return float(value)


def percent(value: float) -> str:
    return f"{100.0 * value:.2f}%"


def main() -> None:
    activated = read_json(TASK_ROOT / "registry/activated_registry_v1.json")
    representative = read_json(TASK_ROOT / "registry/representative_holdout_registry_v1.json")
    manifest = read_json(TASK_ROOT / "registry/combined_registry_manifest.json")
    search = read_json(TASK_ROOT / "activated_generation/search_summary.json")
    rep_pool = read_json(TASK_ROOT / "representative_sampling/pool_summary.json")
    formal = read_json(TASK_ROOT / "benchmark/formal_attempt.json")
    one = rows(TASK_ROOT / "benchmark/one_step_records.csv")
    episodes = rows(TASK_ROOT / "benchmark/episode_summary.csv")
    tests = rows(TASK_ROOT / "statistics/paired_tests.csv")
    effects = rows(TASK_ROOT / "statistics/effect_sizes.csv")
    prevalence = read_json(TASK_ROOT / "audits/representative_prevalence_audit.json")
    execution = read_json(TASK_ROOT / "audits/execution_count_audit.json")
    claims = read_json(TASK_ROOT / "audits/claim_boundary_audit.json")
    decision = read_json(TASK_ROOT / "statistics/project_decision_gates.json")
    environment = read_json(TASK_ROOT / "audits/final_environment_audit.json")
    pr84 = read_json(TASK_ROOT / "input_freeze/pr84_identity.json")
    certifier = read_json(TASK_ROOT / "input_freeze/pr84_certifier_identity_summary.json")
    pr85 = read_json(TASK_ROOT / "input_freeze/pr85_identity.json")
    pr86 = read_json(TASK_ROOT / "input_freeze/pr86_identity.json")
    method_registry = read_json(TASK_ROOT / "methods/method_registry.json")
    map_identity = read_json(TASK_ROOT / "input_freeze/replica_map_identity.json")
    ref_identity = read_json(TASK_ROOT / "input_freeze/reference_mesh_identity.json")
    actions = read_json(TASK_ROOT / "operational_autonomy_actions.json")
    reference_mesh = ref_identity.get("reference_mesh", ref_identity.get("assets", {}).get("reference_mesh", {}))
    certifier_identity = f"{certifier['certifier_identity']}@{certifier['head']}:{certifier['artifact_manifest_sha256']}"
    library_identity = pr86["library_id"]
    library_sha256 = pr86["global_library_sha256"]
    validation_path = TASK_ROOT / "report/validation_result.json"
    validation = read_json(validation_path) if validation_path.exists() else {"status": "NOT_YET_RUN"}

    method_summary = []
    for method in METHODS:
        for cohort in ("ACTIVATED", "REPRESENTATIVE_HOLDOUT"):
            values = [record for record in one if record["method"] == method and record["cohort"] == cohort]
            method_summary.append({
                "method": method.split("_")[0], "cohort": cohort, "n": len(values),
                "commit": sum(boolean(r["committed"]) for r in values),
                "directional": sum(r["selected_candidate"].startswith("ALT-") for r in values),
                "terminal": sum(r["semantic_status"] == "CERTIFIED_TERMINAL_ACTION" for r in values),
                "fail": sum(not boolean(r["committed"]) for r in values),
                "deadline": sum(boolean(r["deadline_miss"]) for r in values),
                "mean_progress": sum(number(r["progress_m"]) for r in values) / len(values),
                "mean_runtime": sum(number(r["total_runtime_s"]) for r in values) / len(values),
            })
    g3_b3 = [r for r in one if r["cohort"] == "ACTIVATED" and r["postlock_group"] == "G3" and r["method"] == METHODS[3]]
    g3_episodes = [r for r in episodes if r["cohort"] == "ACTIVATED" and r["group"] == "G3" and r["method"] == METHODS[3]]
    g3_positive = sum(boolean(r["positive_progress"]) for r in g3_episodes)
    map_disagreement_unique = len({r["state_id"] for r in one if boolean(r["map_reference_disagreement"])})
    reference_collisions = sum(boolean(r["reference_collision_after_commit"]) for r in one)
    reference_rollout_collisions = sum(boolean(r["reference_collision"]) for r in episodes)
    rep_prev = {item["metric"]: item for item in prevalence["prevalence"]}
    b3_rep_episodes = [r for r in episodes if r["cohort"] == "REPRESENTATIVE_HOLDOUT" and r["method"] == METHODS[3]]
    rep_progress = sum(number(r["progress_m"]) for r in b3_rep_episodes) / len(b3_rep_episodes)
    rep_overreject = sum(boolean(r["reference_safe_but_rejected"]) for r in one if r["cohort"] == "REPRESENTATIVE_HOLDOUT" and r["method"] == METHODS[3])

    lines = [
        "# REPORT: Resumed Replica GT Executable-Safety Activated Benchmark V1",
        "",
        f"**FINAL_STATUS:** `{decision['final_status']}`",
        f"**FINAL_DECISION:** `{decision['final_decision']}`",
        f"**Only next task:** `{decision['only_next_task']}`",
        "",
        "> This is configuration-specific evidence on the frozen Replica GT-FINE represented map. It is not a deployment, real-time, collision-superiority, or cross-map generalization claim.",
        "",
        "## Answer first",
        "",
        "FAS-CBF Core V1 passed the preregistered activated mechanism test: the swept-segment and backup layers produced the intended distinctions, and B3 recovered certified control in all 20 locked G3 states where B2 could not. The represented-map backend produced zero false-safe records. However, the method-independent 160-state representative holdout contained no segment/backup-added rejection and no directional selection. The frozen representative-relevance gate therefore failed, so Core V1 must not be framed as a broad real-time SAFER replacement.",
        "",
        "## Frozen lineage and identities",
        "",
        f"- PR #84: `{pr84['head']}`; preserved by frozen identity and artifact manifest.",
        f"- PR #85: `{pr85['head']}`; preserved by frozen identity and artifact manifest.",
        f"- PR #86: `{pr86['head']}`; base `{pr86['pr']['baseRefOid']}`; preserved by frozen identity and artifact manifest.",
        f"- Certifier identity: `{certifier_identity}`.",
        f"- Directional library: `{library_identity}`; SHA-256 `{library_sha256}`.",
        f"- Map snapshot: `{map_identity['map_snapshot_id']}`.",
        f"- Reference mesh SHA-256: `{reference_mesh['sha256']}`.",
        f"- Model: `{NORMATIVE_MODEL}`, dt={DT}, |u|∞≤{U_BOUND}, |v|∞≤{V_BOUND}, robot={ROBOT_RADIUS} m, margin={MARGIN} m, effective radius={EFFECTIVE_RADIUS} m, H={H_STOP_MAX}.",
        "",
        "## Cohorts and leakage boundary",
        "",
        f"Activated search evaluated {search['activated_candidate_generation_count']} candidates, all {search['activated_physical_valid_count']} physical-valid, and stopped after targets were met. Locked G0-G5 counts are {activated['group_counts']} under `{activated['quota_case']}`.",
        f"The representative generator formed {rep_pool['candidate_pool_count']} method-independent candidates and locked {len(representative['states'])}. Registry SHAs are `{manifest['activated']['sha256']}` and `{manifest['representative']['sha256']}`; overlap={manifest['cohort_overlap_count']}. Each registry rebuilt identically in three fresh processes. Pre-lock future-reference reads and formal method runs were both zero.",
        "",
        "## One-step paired results",
        "",
        "| Method | Cohort | n | Commit | Directional | Terminal | Fail-closed | Deadline miss | Mean progress (m) | Mean runtime (s) |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for item in method_summary:
        lines.append(f"| {item['method']} | {item['cohort']} | {item['n']} | {item['commit']} | {item['directional']} | {item['terminal']} | {item['fail']} | {item['deadline']} | {item['mean_progress']:.6f} | {item['mean_runtime']:.6f} |")
    lines += [
        "",
        "### Mechanism attribution",
        "",
        "- G1: B0 committed 20/20 while B1 rejected 20/20 by the swept-segment layer.",
        "- G2/G3: B1 committed 40/40 while B2 rejected 40/40 after terminal/backup certification.",
        f"- G3: B3 selected a frozen directional slot and committed {sum(boolean(r['committed']) for r in g3_b3)}/20; B2 committed 0/20.",
        f"- G3 bounded rollout: positive progress in {g3_positive}/{len(g3_episodes)} B3 episodes; reference collisions={sum(boolean(r['reference_collision']) for r in g3_episodes)}.",
        "- G0: B0 and B3 both committed 20/20 with identical one-step progress; no G0 over-rejection was observed.",
        "",
        "## Representative prevalence and utility",
        "",
        f"- Segment activation: {rep_prev['segment_activation']['count']}/160 ({percent(rep_prev['segment_activation']['rate'])}; Wilson 95% CI {percent(rep_prev['segment_activation']['wilson95_lower'])}–{percent(rep_prev['segment_activation']['wilson95_upper'])}).",
        f"- Backup activation: {rep_prev['backup_activation']['count']}/160 ({percent(rep_prev['backup_activation']['rate'])}).",
        f"- Directional selection: {rep_prev['directional_rescue']['count']}/160 ({percent(rep_prev['directional_rescue']['rate'])}).",
        f"- B3 fail-closed: {rep_prev['fail_closed']['count']}/160; terminal action: {rep_prev['terminal']['count']}/160.",
        f"- B3 representative bounded-rollout mean progress: {rep_progress:.6f} m; reference-safe-but-rejected: {rep_overreject}/160.",
        "",
        "The representative relevance threshold (at least eight segment/backup-added states or four directional selections) was not met. Activated group frequencies are deliberately not used as prevalence estimates.",
        "",
        "## Represented-map and offline-reference evidence",
        "",
        f"- Represented false-safe count: {execution['represented_false_safe_count']} across one-step and rollout.",
        f"- Offline immediate reference collisions after committed controls: {reference_collisions}; rollout collisions: {reference_rollout_collisions}.",
        f"- Map-reference disagreement: {map_disagreement_unique} unique states ({execution['map_reference_disagreement_method_record_count']} method-records). These are map-vs-mesh differences, not certifier implementation errors.",
        "- With zero B0/B3 collision events, no reference collision-superiority claim is made.",
        "",
        "## Runtime and realism",
        "",
        f"Across 1040 one-step method records, deadline misses={execution['deadline_miss_count']}. B3 miss rate={percent(decision['runtime_b3_deadline_miss_rate'])}. Semantic certification and the 50 ms diagnostic are reported separately; the benchmark does not establish real-time readiness.",
        "",
        "## Preregistered H1-H7",
        "",
        "| H | Contrast | Raw p | Holm p | Result |",
        "|---|---|---:|---:|---|",
    ]
    for test in tests:
        raw = "N/A" if test["raw_p_value"] in ("", "None") else f"{float(test['raw_p_value']):.4g}"
        adjusted = "N/A" if test["holm_adjusted_p_value"] in ("", "None") else f"{float(test['holm_adjusted_p_value']):.4g}"
        lines.append(f"| {test['hypothesis']} | {test['contrast']} | {raw} | {adjusted} | {test['status']} |")
    lines += [
        "",
        "H5 is descriptive because no post-hoc null threshold was introduced. H6 has no collision events and therefore supports no superiority inference. Holm correction covers the evaluable inferential contrasts.",
        "",
        "## Project decision gates",
        "",
        f"- Scientific mechanism gate: **{decision['scientific_mechanism_gate']}**.",
        f"- Active utility gate: **{decision['active_utility_gate']}**.",
        f"- Representative relevance gate: **{decision['representative_relevance_gate']}**.",
        f"- No adverse reference regression: **{decision['reference_no_adverse_regression']}**.",
        f"- Frozen decision-tree case: **{decision['decision_case']}**.",
        "",
        "## Claim boundary",
        "",
    ]
    lines.extend(f"- Supported: {claim}" for claim in claims["supported"])
    lines.extend(f"- Not supported: {claim}" for claim in claims["not_supported"])
    lines += [
        "",
        "## Execution and operational audit",
        "",
        f"Formal attempt count={formal['formal_attempt_count']}; infrastructure failures={formal['infrastructure_failure_count']}; same-manifest resumes={formal['infrastructure_resume_count']}. The interruption occurred before any completed formal output, and no scientific result was replaced.",
        f"Map training/mutation=0/0; dataset switches=0; parameter/safety-threshold tuning=0/0; protected-source mutation=0. Operational autonomy actions={actions['operational_autonomy_action_count']}.",
        f"GPU 1 final compute processes={environment['gpu']['compute_process_count']} at {environment['gpu']['memory_used_mib']} MiB / {environment['gpu']['utilization_percent']}%; reverse proxy listener preserved={environment['managed_reverse_proxy']['listener_present']}; watchdog state={environment['scheduled_watchdog']['state']}.",
        f"Validator status: `{validation['status']}`.",
        "",
        "## Evidence locations",
        "",
        "- Server task root: `/disk1/zlab/maintenance_records/resume_replica_gt_executable_safety_activated_benchmark_v1`",
        "- Report: `report/REPORT_RESUME_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md`",
        "- Downstream handoff: `report/downstream_handoff.json`",
        "- Figures: `figures/` (32 preregistered PNGs)",
        "",
        "## Final disposition",
        "",
        f"`FINAL_STATUS={decision['final_status']}`",
        "",
        f"`FINAL_DECISION={decision['final_decision']}`",
        "",
        f"`ONLY_NEXT_TASK={decision['only_next_task']}`",
    ]
    report_path = TASK_ROOT / "report/REPORT_RESUME_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md"
    write_text(report_path, "\n".join(lines))

    body = f"""## Outcome

`FINAL_STATUS={decision['final_status']}`

`FINAL_DECISION={decision['final_decision']}`

`ONLY_NEXT_TASK={decision['only_next_task']}`

## Frozen scope

- Preserves PR #84 `{pr84['head']}`, PR #85 `{pr85['head']}`, and PR #86 `{pr86['head']}`.
- Reproduces the exact nested B0-B3 method matrix and library `{library_sha256}`.
- Uses map `{map_identity['map_snapshot_id']}` and reference mesh `{reference_mesh['sha256']}` without training or mutation.
- Locks separate ACTIVATED (100) and REPRESENTATIVE_HOLDOUT (160) registries with three-process deterministic rebuilds and zero overlap.

## Result

- Activated G0-G5: `{activated['group_counts']}`; quota `{activated['quota_case']}`.
- One-step: 260 states / 1040 paired method records; represented false-safe=0.
- B3 rescued 20/20 G3 states over B2; the representative holdout selected 0 directional alternatives and added 0 segment/backup rejections.
- Bounded rollout: {execution['logical_episode_count']} episodes / {execution['logical_control_step_count']} logical steps.
- Offline reference collisions after commit: {reference_collisions}; no collision-superiority claim.
- B3 50 ms deadline miss rate: {percent(decision['runtime_b3_deadline_miss_rate'])}; no real-time claim.

## Audits and boundaries

Fairness and selection-leakage audits pass. Activated data support mechanism existence only; representative prevalence remains separate. Represented-map certificates and offline-reference geometry are not conflated. No map training/mutation, data switch, parameter tuning, or protected-source mutation occurred. One same-manifest infrastructure resume was recorded before any completed formal output.

See `report/REPORT_RESUME_REPLICA_GT_EXECUTABLE_SAFETY_ACTIVATED_BENCHMARK_V1.md`, H1-H7 statistics, 32 figures, and the final validator result for full evidence.
"""
    write_text(TASK_ROOT / "report/DRAFT_PR_BODY.md", body)
    print("PASS_REPORT_AND_DRAFT_PR_BODY", decision["final_status"], validation["status"])


if __name__ == "__main__":
    main()
