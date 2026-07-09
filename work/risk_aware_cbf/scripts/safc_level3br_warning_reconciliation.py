#!/usr/bin/env python3
"""Reconcile tracked warning evidence with the executable no-op context."""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


REPORT_FIELDS = (
    "source_id",
    "source_path",
    "exists",
    "used",
    "scene",
    "trial_id",
    "reported_step_or_window",
    "reported_horizon",
    "reported_dt_margin",
    "reported_controller_context",
    "reported_recovery_context",
    "reported_warning_count",
    "reported_recovery_count",
    "reported_collision_count",
    "reported_stop_reason",
    "checkpoint_or_data_context",
    "evidence_text",
    "missing_context_fields",
    "notes",
)

RECONCILIATION_FIELDS = (
    "candidate_id",
    "source_id",
    "scene",
    "trial_id",
    "report_warning_evidence",
    "report_context_complete",
    "current_wrapper_scene",
    "current_wrapper_trial",
    "current_wrapper_step_window",
    "current_wrapper_dt_margin",
    "current_wrapper_horizon",
    "controller_context_match",
    "recovery_context_match",
    "trajectory_context_match",
    "window_match",
    "checkpoint_context_match",
    "reproduction_risk",
    "likely_mismatch_reason",
    "recommended_next_scan",
    "notes",
)


@dataclass(frozen=True)
class SourceContext:
    source_id: str
    source_path: str
    scene: str
    step_window: str
    horizon: str
    dt_margin: str
    controller: str
    recovery: str
    stop_reason: str
    data_context: str
    evidence: str


SOURCES = (
    SourceContext(
        "SRC001",
        "work/risk_aware_cbf/REPORT_DISCRETE_TIME_VERIFICATION_CONSOLIDATION.md",
        "flight",
        "saved V4-A + V1 full trajectory; exact candidate steps not reported",
        "H1;H2;H3",
        "0.0005",
        "V4-A active projection + Risk-Aware V1 verification-only audit",
        "disabled in verification-only audit",
        "not reported per candidate",
        "saved V4-A + V1 dense-flight trajectory; exact checkpoint not stated",
        "Aggregate verification-only audit reports H1/H2/H3 margin violations.",
    ),
    SourceContext(
        "SRC002",
        "work/risk_aware_cbf/REPORT_V4C_HSTEP_PREDICTIVE_RECOVERY.md",
        "flight",
        "flight20 full runs; exact first warning step not reported",
        "H3",
        "0.0005",
        "risk_aware_v1_bestD",
        "V4-C H3_N128 enabled on margin violation",
        "not reported per candidate",
        "dense flight model; exact checkpoint and start-repair state not stated",
        "Trials 12, 13, and 14 repeatedly trigger H-step recovery.",
    ),
    SourceContext(
        "SRC003",
        "work/risk_aware_cbf/REPORT_V4C_FLIGHT100_VALIDATION.md",
        "flight",
        "full100 trajectories; exact first warning steps not reported",
        "H3",
        "0.0005",
        "Risk-Aware V1 context inherited by V4-C H3_N128",
        "V4-C H3_N128 enabled on margin violation",
        "not reported per candidate",
        "dense flight full100 data; exact checkpoint not stated",
        "Per-trial tables report base horizon violations and recovery use.",
    ),
    SourceContext(
        "SRC004",
        "work/risk_aware_cbf/REPORT_V4C_TUNED_FULL100_VALIDATION.md",
        "flight",
        "full100 trajectories; exact first warning steps not reported",
        "H2",
        "0.0005",
        "V4-A active-set start projection + Risk-Aware V1 bestD",
        "V4-C R4_H2_N64 enabled on margin violation",
        "not reported per candidate",
        "dense flight tuned full100 data; exact checkpoint not stated",
        "Per-trial tables report H2 base violations and tuned recovery use.",
    ),
    SourceContext(
        "SRC005",
        "work/risk_aware_cbf/REPORT_V4A_ACTIVE_PROJECTION_DT_AUDIT.md",
        "flight",
        "flight100 and flight20 aggregates; exact candidate windows absent",
        "one-step DT audit",
        "not explicitly stated",
        "V4-A active projection + Risk-Aware V1",
        "disabled",
        "not reported per candidate",
        "dense flight post-repair navigation; exact checkpoint not stated",
        "Aggregate DT audit reports repair-needed and flight20 violations.",
    ),
    SourceContext(
        "SRC006",
        "work/risk_aware_cbf/REPORT_STARTGUARD_TRIAL57.md",
        "flight",
        "trial 57 navigation; exact warning window not reported",
        "unknown",
        "not reported",
        "StartGuard with safer_splat_filter and Risk-Aware V1 bestD",
        "start repair enabled; predictive recovery not reported",
        "not reported",
        "trial 57 original unsafe start and repaired start contexts",
        "Trial 57 has negative initial safety h and original collision evidence.",
    ),
    SourceContext(
        "SRC007",
        "work/risk_aware_cbf/REPORT_STARTGUARD_FLIGHT100.md",
        "flight",
        "flight100 aggregate",
        "unknown",
        "not reported",
        "StartGuard + safer_splat_filter / Risk-Aware V1 bestD",
        "start repair enabled; predictive recovery disabled",
        "not reported per candidate",
        "original and post-repair dense flight contexts",
        "Aggregate report separates initial safety from post-repair navigation.",
    ),
    SourceContext(
        "SRC008",
        "work/risk_aware_cbf/REPORT_FC_AWARE_V1_FLIGHT20_STOP_REASON_RECONCILIATION.md",
        "flight",
        "targeted risk windows and partial flight20 execution",
        "diagnostic DT metrics",
        "context-specific; exact value not consolidated",
        "FC-Aware V1 capped candidate query",
        "FC-Aware diagnostic context",
        "partial-run stop reasons reported",
        "FC-Aware branch context; exact checkpoint not stated",
        "Diagnostic targeted windows are not the current main-method context.",
    ),
    SourceContext(
        "SRC009",
        "work/risk_aware_cbf/REPORT_MPC_STYLE_RECOVERY_TARGETED_PILOT.md",
        "flight",
        "targeted pilot windows",
        "predictive pilot horizon",
        "context-specific; exact value not consolidated",
        "primitive MPC-style recovery pilot",
        "recovery enabled",
        "pilot outcomes reported",
        "negative-branch pilot context; exact checkpoint not stated",
        "Recovery pilot evidence is diagnostic and cannot be promoted.",
    ),
)


def write_csv(
    path: Path, fields: Sequence[str], rows: Iterable[dict[str, Any]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def extract_first_int(text: str, pattern: str) -> int | None:
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def source_trials(
    source_id: str, candidates: Sequence[dict[str, str]]
) -> str:
    trials = sorted(
        {
            int(row["trial_id"])
            for row in candidates
            if row["source_id"] == source_id and row["trial_id"]
        }
    )
    return ";".join(str(value) for value in trials)


def source_count(
    source_id: str,
    candidates: Sequence[dict[str, str]],
    field: str,
) -> int | None:
    values: list[int] = []
    for row in candidates:
        if row["source_id"] != source_id:
            continue
        raw = row.get(field, "").strip()
        if raw:
            values.append(int(float(raw)))
    return sum(values) if values else None


def missing_fields(context: SourceContext, trials: str) -> list[str]:
    missing: list[str] = []
    if not trials:
        missing.append("candidate_trial_mapping")
    if "exact" in context.step_window or "aggregate" in context.step_window:
        missing.append("exact_first_warning_step")
    if "not reported" in context.dt_margin or "context-specific" in context.dt_margin:
        missing.append("exact_dt_margin")
    if "unknown" in context.horizon:
        missing.append("exact_horizon")
    if "exact checkpoint" in context.data_context:
        missing.append("exact_checkpoint")
    if "start-repair" in context.data_context or "post-repair" in context.data_context:
        missing.append("exact_executed_start_state")
    return missing


def build_report_inventory(
    repo_root: Path,
    candidates: Sequence[dict[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    used_sources = {row["source_id"] for row in candidates}
    for context in SOURCES:
        path = repo_root / context.source_path
        exists = path.is_file()
        text = path.read_text(encoding="utf-8") if exists else ""
        trials = source_trials(context.source_id, candidates)
        reported_warning_count = source_count(
            context.source_id, candidates, "warning_count_hint"
        )
        recovery_context = context.recovery.lower()
        reported_recovery_count = (
            reported_warning_count
            if "recovery" in recovery_context or "v4-c" in recovery_context
            else None
        )
        collision_count = extract_first_int(
            text, r"collision_count\s*[=|:]\s*(-?\d+)"
        )
        missing = missing_fields(context, trials)
        rows.append(
            {
                "source_id": context.source_id,
                "source_path": context.source_path,
                "exists": exists,
                "used": context.source_id in used_sources,
                "scene": context.scene,
                "trial_id": trials,
                "reported_step_or_window": context.step_window,
                "reported_horizon": context.horizon,
                "reported_dt_margin": context.dt_margin,
                "reported_controller_context": context.controller,
                "reported_recovery_context": context.recovery,
                "reported_warning_count": (
                    reported_warning_count
                    if reported_warning_count is not None
                    else ""
                ),
                "reported_recovery_count": (
                    reported_recovery_count
                    if reported_recovery_count is not None
                    else ""
                ),
                "reported_collision_count": (
                    collision_count if collision_count is not None else ""
                ),
                "reported_stop_reason": context.stop_reason,
                "checkpoint_or_data_context": context.data_context,
                "evidence_text": context.evidence if exists else "",
                "missing_context_fields": ";".join(missing),
                "notes": (
                    "Tracked report only; referenced raw artifacts were not read."
                    if exists
                    else "Source report missing."
                ),
            }
        )
    return rows


def context_matches_default(
    candidate: dict[str, str],
    context: SourceContext,
) -> dict[str, Any]:
    controller_match = (
        context.controller == "official safer_splat_filter CBF"
    )
    recovery_match = (
        context.recovery == "disabled"
        or "verification-only" in context.recovery
    )
    trajectory_match = (
        controller_match
        and recovery_match
        and "post-repair" not in context.data_context
        and "repaired start" not in context.data_context
    )
    window_match = False
    margin_match = context.dt_margin == "0.0005"
    horizon_match = context.horizon in {"H3", "H1;H2;H3"}
    checkpoint_match = "same checkpoint confirmed" in context.data_context
    if not controller_match:
        reason = "controller_context_mismatch"
        recommendation = (
            "need exact original controller and nominal-command construction"
        )
    elif not recovery_match:
        reason = "recovery_context_mismatch"
        recommendation = "need original V4-C execution context"
    elif not trajectory_match:
        reason = "trajectory_context_mismatch"
        recommendation = "need exact executed start and prior recovery history"
    elif not (margin_match and horizon_match):
        reason = "dt_margin_horizon_mismatch"
        recommendation = "run bounded diagnostic margin/horizon sensitivity"
    elif not window_match:
        reason = "step_window_too_short"
        recommendation = "scan the same candidate to bounded step 200"
    elif not checkpoint_match:
        reason = "checkpoint_context_unknown"
        recommendation = "record the exact report checkpoint"
    else:
        reason = "unknown"
        recommendation = "need tracked compact per-event summary"
    complete = all(
        (
            controller_match,
            recovery_match,
            trajectory_match,
            window_match,
            checkpoint_match,
            margin_match,
            horizon_match,
        )
    )
    return {
        "report_context_complete": complete,
        "controller_context_match": controller_match,
        "recovery_context_match": recovery_match,
        "trajectory_context_match": trajectory_match,
        "window_match": window_match,
        "checkpoint_context_match": checkpoint_match,
        "reproduction_risk": "low" if complete else "high",
        "likely_mismatch_reason": reason,
        "recommended_next_scan": recommendation,
        "notes": (
            f"dt_margin_match={margin_match}; horizon_match={horizon_match}; "
            "scene/trial identifiers alone do not establish trajectory equivalence."
        ),
    }


def build_candidate_reconciliation(
    candidates: Sequence[dict[str, str]],
) -> list[dict[str, Any]]:
    contexts = {item.source_id: item for item in SOURCES}
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        context = contexts[candidate["source_id"]]
        match = context_matches_default(candidate, context)
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "source_id": candidate["source_id"],
                "scene": candidate["scene"],
                "trial_id": candidate["trial_id"],
                "report_warning_evidence": candidate[
                    "warning_evidence_text"
                ],
                "report_context_complete": match[
                    "report_context_complete"
                ],
                "current_wrapper_scene": candidate["scene"],
                "current_wrapper_trial": candidate["trial_id"],
                "current_wrapper_step_window": "steps 1-200",
                "current_wrapper_dt_margin": 0.0005,
                "current_wrapper_horizon": "H3",
                "controller_context_match": match[
                    "controller_context_match"
                ],
                "recovery_context_match": match[
                    "recovery_context_match"
                ],
                "trajectory_context_match": match[
                    "trajectory_context_match"
                ],
                "window_match": match["window_match"],
                "checkpoint_context_match": match[
                    "checkpoint_context_match"
                ],
                "reproduction_risk": match["reproduction_risk"],
                "likely_mismatch_reason": match[
                    "likely_mismatch_reason"
                ],
                "recommended_next_scan": match[
                    "recommended_next_scan"
                ],
                "notes": match["notes"],
            }
        )
    return rows


def write_context_notes(
    path: Path,
    report_rows: Sequence[dict[str, Any]],
    reconciliation_rows: Sequence[dict[str, Any]],
) -> None:
    incomplete = sum(
        not bool(row["report_context_complete"])
        for row in reconciliation_rows
    )
    path.write_text(
        f"""# SAFC Level-3B-R Warning Evidence Reconciliation Notes

## Scope

This is warning evidence reproduction reconciliation. It does not run active
slowdown and does not claim performance improvement.

## Report-Derived Warning Evidence

The context pass scanned {sum(bool(row["exists"]) for row in report_rows)}
tracked reports and reconciled {len(reconciliation_rows)} candidates. It read
only tracked Markdown and compact Level-3B candidate summaries. Referenced raw
traces and per-step artifacts were not read.

## Context Reconciliation

All {incomplete} candidates have at least one unresolved context field. The
current executable wrapper uses the official CBF command construction,
recovery disabled, original generated start-goal states, `dt_margin=0.0005`,
H3 repeated-control audit, and a bounded step window. Report contexts include
Risk-Aware V1, V4-C recovery-enabled trajectories, start repair, or diagnostic
branches. Exact first-warning steps and checkpoints are generally absent.

Further bounded no-op and sensitivity results are appended by the scan script.
""",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconcile SAFC Level-3B-R report warning contexts."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "work/risk_aware_cbf/results/safc_level3br_warning_reconciliation"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    candidate_path = (
        repo_root
        / "work/risk_aware_cbf/results/safc_level3b_warning_rich_targeted"
        / "warning_rich_candidate_inventory.csv"
    )
    candidates = load_csv(candidate_path)
    report_rows = build_report_inventory(repo_root, candidates)
    reconciliation_rows = build_candidate_reconciliation(candidates)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        output_dir / "report_context_inventory.csv",
        REPORT_FIELDS,
        report_rows,
    )
    write_csv(
        output_dir / "candidate_context_reconciliation.csv",
        RECONCILIATION_FIELDS,
        reconciliation_rows,
    )
    write_context_notes(
        output_dir / "warning_reconciliation_notes.md",
        report_rows,
        reconciliation_rows,
    )
    print(
        f"sources={len(report_rows)} candidates={len(reconciliation_rows)} "
        f"incomplete={sum(not bool(row['report_context_complete']) for row in reconciliation_rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
