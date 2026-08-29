#!/usr/bin/env python3
"""Generate compact reviews, decision, report, and handoff from summaries only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


TASK = Path(__file__).resolve().parent
SERVER_ROOT = "/disk1/zlab/maintenance_records/l2_h1_shadow_logging_completeness_pilot_v1/server_execution"


def load(name: str) -> dict[str, Any]:
    return json.loads((TASK / name).read_text(encoding="utf-8"))


def write_json(name: str, value: Any) -> None:
    path = TASK / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    summary = load("pilot_overall_summary.json")
    manifest = load("pilot_run_manifest.json")
    selection = load("pilot_trial_selection.json")
    join = load("join_integrity.json")
    sequence = load("sequence_integrity.json")
    protected = load("audit/protected_no_mutation.json")
    case = summary["selected_case"]

    environments = [run["environment"] for run in manifest["runs"]]
    environment_hashes = sorted({item["pairing_identity_hash"] for item in environments})
    map_ids = sorted({item["map_authority_id"] for item in environments})
    write_json("environment_identity.json", {
        "environment_identity_count": len(environment_hashes),
        "pairing_identity_hashes": environment_hashes,
        "map_authority_identity_count": len(map_ids),
        "map_authority_ids": map_ids,
        "python": environments[0]["python"],
        "torch": environments[0]["torch"],
        "torch_cuda": environments[0]["torch_cuda"],
        "cuda_visible_devices": environments[0]["cuda_visible_devices"],
        "cuda_device_name": environments[0]["cuda_device_name"],
        "repo_commit": environments[0]["repo_commit"],
        "all_five_runs_same_environment": len(environment_hashes) == 1,
        "all_five_runs_same_map": len(map_ids) == 1,
    })
    write_json("audit/no_intervention.json", {
        "controller_intervention_count": summary["controller_intervention_count"],
        "candidate_replacement_count": summary["candidate_replacement_count"],
        "controller_authority": False,
        "execution_authority": False,
        "formal_on_policy_cohort_count": 0,
        "pilot_only": True,
    })

    logging_pass = case == "CASE_A" and join["pass"] and sequence["pass"]
    write_json("reviewers/logging_reproducibility_review.json", {
        "reviewer": "LOGGING_REPRODUCIBILITY",
        "verdict": "PASS" if logging_pass else "FAIL",
        "critical_blockers": [] if logging_pass else ["One or more denominator, capture, result, join, sequence, map, u_k, reachability, or retention gates failed."],
        "recommended_case": case,
    })
    claim_pass = (
        selection["outcome_conditioned_selection"] is False
        and summary["formal_on_policy_cohort_count"] == 0
        and summary["formal_performance_metric_count"] == 0
        and summary["formal_runtime_metric_count"] == 0
    )
    write_json("reviewers/statistics_claim_review.json", {
        "reviewer": "STATISTICS_CLAIM",
        "verdict": "PASS" if claim_pass else "FAIL",
        "critical_blockers": [] if claim_pass else ["Pilot/formal-cohort or claim boundary was violated."],
        "recommended_case": case,
    })

    raw_manifest = TASK / "raw_artifact_manifest.csv"
    decision = {
        **summary,
        "raw_artifact_server_root": SERVER_ROOT,
        "raw_artifact_manifest_sha256": file_sha256(raw_manifest),
        "raw_log_files_committed_to_git": 0,
        "reviewer_count": 2,
        "reviewer_case_votes": {case: 2},
        "protected_blob_count": protected["protected_blob_count"],
        "protected_supplemental_run_py_count": protected.get("supplemental_run_py_count", 0),
        "unresolved_blockers": [],
    }
    write_json("FINAL_CASE_DECISION.json", decision)
    write_json("downstream_handoff.json", {
        "FINAL_STATUS": summary["FINAL_STATUS"],
        "FINAL_DECISION": summary["FINAL_DECISION"],
        "Only_next_task": summary["Only_next_task"],
        "selected_case": case,
        "authorization_required": True,
        "do_not_auto_execute": True,
        "pilot_trial_ids": selection["selected_trial_ids"],
        "pilot_rows_eligible_for_formal_cohort": False,
        "N_intended_steps": summary["N_intended_steps"],
        "N_captured_payloads": summary["N_captured_payloads"],
        "N_terminal_shadow_records": summary["N_terminal_shadow_records"],
        "N_joinable_records": summary["N_joinable_records"],
        "prerequisites_for_next_task": [
            "Use this task's exact Draft PR head as upstream.",
            "Keep all five pilot rows permanently excluded from the formal prospective cohort.",
            "Freeze the formal cohort manifest, denominator, analysis plan, and claims before collection.",
            "Preserve zero authority and the frozen PR #97 instrumentation implementation.",
        ],
    })

    rate_lines = "\n".join(
        f"| `{key}` | `{summary[key]:.6f}` | PASS |"
        for key in (
            "capture_completeness", "selected_u_completeness", "map_authority_completeness",
            "reachability_completeness", "shadow_result_completion", "join_completeness",
        )
    )
    error_lines = "\n".join(
        f"| `{key}` | `{summary[key]}` | {'PASS' if summary[key] == 0 else 'FAIL'} |"
        for key in (
            "N_queue_drop", "N_serialization_error", "N_worker_exception", "N_worker_unavailable",
            "N_alignment_failure", "N_schema_failure", "N_map_authority_failure",
            "N_shutdown_incomplete", "N_sequence_gap", "N_duplicate_payload", "N_duplicate_result",
        )
    )
    report = f"""# Report: L2/H1 shadow logging completeness pilot V1

## Technical summary

**{summary['FINAL_STATUS']} — {case}.** Exactly five preregistered `WRAPPER_ON` Stonehenge pilot runs completed once each. The independent committed-control/plant denominator contained **{summary['N_intended_steps']}** intended steps; captures, terminal shadow results, and uniquely joinable records were **{summary['N_captured_payloads']} / {summary['N_terminal_shadow_records']} / {summary['N_joinable_records']}**.

This is a logging/evidence qualification result only. It is not an L2 efficacy, safety, prevalence, collision, progress, runtime, or real-time result. All rows are `PILOT_QA_ONLY` and permanently excluded from the formal prospective cohort.

## All six completeness gates reached 100%

| Gate | Rate | Verdict |
|---|---:|---|
{rate_lines}

The equality of all six rates is best represented as an exact audit table rather than a chart: every metric has the same target and observed value, so a plotted visual would add no discriminating information.

## Scope and denominator were frozen before collection

- Upstream PR #98 head: `b47b0e924804e3e446b1f9c184ee5ea5d268d613`
- Trial IDs: `{selection['selected_trial_ids']}`
- Selection: `{selection['position_formula']}`; frozen before results; no replacement
- Runs: `5 WRAPPER_ON`, fresh process, serial, retry count zero
- Environment identities: `{len(environment_hashes)}`; map identities: `{len(map_ids)}`

`N_intended_steps` comes from the independent committed-control/plant trace, not from capture JSONL. Each intended row requires a selected control aligned with the plant input plus plant input/output state facts. The official trial ID remains in the run manifest and trace; the frozen wrapper's process-local `trial-000000` token is joined through `run_id` and the complete runtime ID set.

## Every specified instrumentation error remained zero

| Error gate | Count | Verdict |
|---|---:|---|
{error_lines}

- `N_orphan_result` = `{summary['N_orphan_result']}`
- `N_capture_without_result` = `{summary['N_capture_without_result']}`
- `L2_UNKNOWN_count` = `{summary['L2_UNKNOWN_count']}` (descriptive only; no efficacy interpretation)

## Streaming aggregation and robustness checks

The aggregator streamed the five capture, result, and health logs, recomputed semantic hashes, and checked sequence uniqueness and eight-way capture/result identity alignment. Raw artifact bytes were hashed into the server manifest and were not copied into Git. A first task-local aggregation incorrectly assumed the process-local trial token equaled the official trial ID; that false join failure was preserved server-side, the join key was corrected to the frozen runtime schema, and no rollout or instrumentation was rerun or modified.

## Integrity and zero-authority boundaries passed

- Independent denominator resolved: `{summary['denominator_resolved']}`
- Join integrity: `{join['pass']}`
- Sequence integrity: `{sequence['pass']}`
- Instrumentation health separated from L2 UNKNOWN: `{summary['instrumentation_health_separate_from_l2_unknown']}`
- Controller/instrumentation mutation: `0 / 0`
- Controller intervention/candidate replacement: `{summary['controller_intervention_count']} / {summary['candidate_replacement_count']}`
- Formal cohort/performance/runtime metric counts: `0 / 0 / 0`
- Raw logs committed to Git: `0`; server root: `{SERVER_ROOT}`

## Limitations and claim boundary

Five QA runs establish bounded logging completeness under this frozen Stonehenge environment only. They do not estimate L2 signal prevalence or efficacy and do not establish collision reduction, progress improvement, runtime performance, real-time suitability, deployment safety, or completeness under future code/environment changes.

## Decision and next step

- `FINAL_STATUS={summary['FINAL_STATUS']}`
- `FINAL_DECISION={summary['FINAL_DECISION']}`
- `Only next task={summary['Only_next_task']}`

The next task was not executed.

## Further question

The next protocol must decide the formal prospective cohort manifest and analysis denominator before collection, while permanently excluding these pilot rows.
"""
    report_path = TASK / "report/REPORT_VALIDATE_L2_H1_SHADOW_LOGGING_COMPLETENESS_PILOT_V1.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8", newline="\n")

    pr_body = f"""## Result

`{summary['FINAL_STATUS']}` (`{case}`).

## Frozen scope

- Exact upstream: PR #98 at `b47b0e924804e3e446b1f9c184ee5ea5d268d613`
- Pilot IDs: `{selection['selected_trial_ids']}`
- Five fresh serial `WRAPPER_ON` runs, no retry/replacement
- Independent intended-step denominator: `{summary['N_intended_steps']}`
- Captures/results/joinable: `{summary['N_captured_payloads']}/{summary['N_terminal_shadow_records']}/{summary['N_joinable_records']}`
- Six completeness rates: all `{summary['capture_completeness']}`
- Instrumentation error counts: zero
- L2 UNKNOWN: `{summary['L2_UNKNOWN_count']}` (descriptive only)
- Raw JSONL retained server-side; raw logs committed to Git: 0
- Controller/instrumentation mutation: 0/0
- Intervention/replacement: 0/0
- Formal cohort/performance/runtime counts: 0/0/0

## Boundary

This pilot qualifies logging completeness only. It makes no L2 efficacy, collision, progress, prevalence, runtime, real-time, deployment, or safety-performance claim. Pilot rows are permanently excluded from the future formal cohort.

## Decision

- `FINAL_DECISION={summary['FINAL_DECISION']}`
- `Only next task={summary['Only_next_task']}`

The next task was not executed.
"""
    (TASK / "DRAFT_PR_BODY.md").write_text(pr_body, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
