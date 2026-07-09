#!/usr/bin/env python3
"""Reconstruct SAFC aggregate events from existing compact evidence."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


REPORT_SPECS = (
    (
        "REPORT_SYNTHETIC_INITIAL_UNSAFE_STRESS_TEST.md",
        "start_safe",
        "Synthetic initial-unsafe repair and post-repair aggregate evidence.",
    ),
    (
        "REPORT_STARTGUARD_FLIGHT100.md",
        "start_safe",
        "Flight100 start certification, repair, and navigation aggregate evidence.",
    ),
    (
        "REPORT_STARTGUARD_TRIAL57.md",
        "start_safe",
        "Trial57 start repair and post-repair navigation evidence.",
    ),
    (
        "REPORT_DISCRETE_TIME_VERIFICATION_CONSOLIDATION.md",
        "dt_verification",
        "H1/H2/H3 verification-only and recovery comparison evidence.",
    ),
    (
        "REPORT_V4A_ACTIVE_PROJECTION_DT_AUDIT.md",
        "dt_verification",
        "Verified projection, navigation, and one-step DT audit evidence.",
    ),
    (
        "REPORT_V4C_HSTEP_PREDICTIVE_RECOVERY.md",
        "recovery",
        "Named V4-C H-step recovery aggregate evidence.",
    ),
    (
        "REPORT_V4C_FLIGHT100_VALIDATION.md",
        "recovery",
        "Named V4-C H3_N128 flight100 aggregate evidence.",
    ),
    (
        "REPORT_V4C_TUNED_FULL100_VALIDATION.md",
        "recovery",
        "Named V4-C R4_H2_N64 tuned full100 aggregate evidence.",
    ),
    (
        "REPORT_FC_AWARE_V1_FLIGHT20_STOP_REASON_RECONCILIATION.md",
        "diagnostic_negative",
        "Recovery-disabled FC-Aware stop/collision reconciliation evidence.",
    ),
    (
        "REPORT_MPC_STYLE_RECOVERY_TARGETED_PILOT.md",
        "diagnostic_negative",
        "Primitive MPC-style offline diagnostic evidence.",
    ),
    (
        "REPORT_SAFER_BASELINE_NAVIGATION_STACK_AUDIT.md",
        "navigation_stack_audit",
        "Textual source audit of baseline, DT, and recovery interfaces.",
    ),
)

SOURCE_FIELDS = (
    "source_id",
    "source_path",
    "source_type",
    "exists",
    "tracked_assumed",
    "used",
    "missing_reason",
    "evidence_scope",
    "notes",
)

EVENT_FIELDS = (
    "event_id",
    "source_id",
    "source_path",
    "event_type",
    "evidence_text",
    "parsed_value",
    "parsed_unit",
    "safc_from_state",
    "safc_to_state",
    "feedback_action",
    "claim_scope",
    "confidence",
    "notes",
)

TRANSITION_FIELDS = (
    "from_state",
    "to_state",
    "event_type",
    "count",
    "sources",
    "feedback_actions",
    "claim_scopes",
    "confidence_min",
    "notes",
)

ACTION_FIELDS = (
    "feedback_action",
    "count",
    "source_count",
    "dominant_event_types",
    "claim_scopes",
    "implemented_supported_count",
    "interface_level_count",
    "diagnostic_only_count",
    "notes",
)

S0 = "S0_PreExecutionCertification"
S1 = "S1_NominalFiltering"
S2 = "S2_VerifiedExecution"
S3 = "S3_WarningAwareExecution"
S4 = "S4_RecoveryMode"
S5 = "S5_ReplanRequested"
S6 = "S6_SafeHaltAbort"
NA = "NA"

CONFIDENCE_RANK = {"low": 0, "medium": 1, "high": 2}
ALLOWED_EVENT_TYPES = {
    "start_certified",
    "start_repaired",
    "start_repair_failed",
    "qp_success",
    "qp_infeasible",
    "dt_warning_H1",
    "dt_warning_H2",
    "dt_warning_H3",
    "dt_warning_any",
    "collision",
    "collision_free",
    "recovery_used",
    "recovery_success",
    "recovery_failed",
    "recovery_disabled",
    "stop_reason",
    "replan_candidate",
    "safe_halt_candidate",
    "diagnostic_negative",
    "unsupported_or_missing",
}
ALLOWED_STATES = {S0, S1, S2, S3, S4, S5, S6, NA}
ALLOWED_ACTIONS = {
    "admit_task",
    "command_slowdown_candidate",
    "activate_recovery",
    "replan_request_candidate",
    "risk_cost_update_candidate",
    "waypoint_rejection_candidate",
    "safe_halt_candidate",
    "no_feedback",
    "diagnostic_only",
    NA,
}
ALLOWED_CLAIM_SCOPES = {
    "implemented_supported",
    "offline_reconstruction_only",
    "interface_level",
    "diagnostic_only",
    "future_work",
    "unsupported",
}
PROHIBITED_PARTS = (
    "trace",
    "trials.csv",
    "per_step",
    "active_constraints",
    "trajectory_samples",
)
MAX_LOCAL_FILE_BYTES = 5 * 1024 * 1024


@dataclass
class SourceRecord:
    source_id: str
    source_path: str
    source_type: str
    exists: bool
    tracked_assumed: bool
    used: bool
    missing_reason: str
    evidence_scope: str
    notes: str


@dataclass
class Event:
    event_id: str
    source_id: str
    source_path: str
    event_type: str
    evidence_text: str
    parsed_value: str
    parsed_unit: str
    safc_from_state: str
    safc_to_state: str
    feedback_action: str
    claim_scope: str
    confidence: str
    notes: str


@dataclass
class MarkdownTable:
    line_number: int
    headers: list[str]
    rows: list[dict[str, str]]


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"expected true/false, got {value!r}")


def normalize_header(value: str) -> str:
    value = value.strip().strip("`").lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_separator_row(line: str) -> bool:
    cells = split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def parse_markdown_tables(text: str) -> list[MarkdownTable]:
    lines = text.splitlines()
    tables: list[MarkdownTable] = []
    index = 0
    while index + 1 < len(lines):
        if not lines[index].lstrip().startswith("|") or not is_separator_row(
            lines[index + 1]
        ):
            index += 1
            continue
        raw_headers = split_table_row(lines[index])
        headers = [normalize_header(header) for header in raw_headers]
        rows: list[dict[str, str]] = []
        row_index = index + 2
        while row_index < len(lines) and lines[row_index].lstrip().startswith("|"):
            cells = split_table_row(lines[row_index])
            if len(cells) == len(headers):
                rows.append(dict(zip(headers, cells)))
            row_index += 1
        tables.append(MarkdownTable(index + 1, headers, rows))
        index = row_index
    return tables


def parse_scalar(value: Any) -> float | None:
    if value is None:
        return None
    text = str(value).strip().strip("`").replace(",", "")
    if not text or text.lower() in {"na", "n/a", "none", "true", "false"}:
        return None
    match = re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?", text, re.I)
    if not match:
        return None
    return float(text)


def parse_key_values(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"^\s*([A-Za-z][A-Za-z0-9_ /-]*):\s*(.+?)\s*$", line)
        if match:
            values[normalize_header(match.group(1))] = match.group(2).strip()
    for table in parse_markdown_tables(text):
        if table.headers == ["metric", "value"]:
            for row in table.rows:
                values[normalize_header(row["metric"])] = row["value"]
    return values


def find_tables(
    tables: Sequence[MarkdownTable],
    required: Iterable[str],
    excluded: Iterable[str] = (),
) -> list[MarkdownTable]:
    required_set = set(required)
    excluded_set = set(excluded)
    return [
        table
        for table in tables
        if required_set.issubset(table.headers)
        and not excluded_set.intersection(table.headers)
    ]


def evidence_from_row(table: MarkdownTable, row: dict[str, str]) -> str:
    parts = [f"{header}={row.get(header, '')}" for header in table.headers]
    return f"line {table.line_number}: " + "; ".join(parts)


class EventBuilder:
    def __init__(self, source: SourceRecord) -> None:
        self.source = source
        self.events: list[Event] = []
        self._dedupe: set[tuple[str, str, str, str, str]] = set()

    def add(
        self,
        event_type: str,
        evidence_text: str,
        parsed_value: Any,
        parsed_unit: str,
        from_state: str,
        to_state: str,
        feedback_action: str,
        claim_scope: str,
        confidence: str,
        notes: str,
    ) -> None:
        parsed = "" if parsed_value is None else str(parsed_value)
        key = (event_type, evidence_text, from_state, to_state, feedback_action)
        if key in self._dedupe:
            return
        self._dedupe.add(key)
        self.events.append(
            Event(
                event_id="",
                source_id=self.source.source_id,
                source_path=self.source.source_path,
                event_type=event_type,
                evidence_text=evidence_text,
                parsed_value=parsed,
                parsed_unit=parsed_unit,
                safc_from_state=from_state,
                safc_to_state=to_state,
                feedback_action=feedback_action,
                claim_scope=claim_scope,
                confidence=confidence,
                notes=notes,
            )
        )


def add_navigation_row_events(
    builder: EventBuilder,
    table: MarkdownTable,
    row: dict[str, str],
    scope: str = "offline_reconstruction_only",
) -> None:
    evidence = evidence_from_row(table, row)
    qp_value = parse_scalar(row.get("qp_infeasible_count"))
    if qp_value is not None:
        if qp_value == 0:
            builder.add(
                "qp_success",
                evidence,
                qp_value,
                "count",
                S1,
                S2,
                "no_feedback",
                scope,
                "high",
                "Aggregate report row records zero QP infeasibility.",
            )
        else:
            builder.add(
                "qp_infeasible",
                evidence,
                qp_value,
                "count",
                S1,
                S6,
                "safe_halt_candidate",
                "offline_reconstruction_only",
                "medium",
                "Recovery availability is not established by this aggregate row.",
            )
    collision_value = parse_scalar(row.get("collision_count"))
    if collision_value is not None:
        if collision_value > 0:
            builder.add(
                "collision",
                evidence,
                collision_value,
                "count",
                S2,
                S6,
                "safe_halt_candidate",
                "diagnostic_only",
                "high",
                "Collision is reconstructed separately from warning and infeasibility.",
            )
        else:
            builder.add(
                "collision_free",
                evidence,
                collision_value,
                "count",
                S2,
                S2,
                "no_feedback",
                scope,
                "high",
                "Aggregate report row records zero collisions.",
            )


def add_dt_recovery_row_events(
    builder: EventBuilder,
    table: MarkdownTable,
    row: dict[str, str],
    recovery_scope: str,
) -> None:
    evidence = evidence_from_row(table, row)
    horizon = row.get("horizon", "")
    recovery_used = parse_scalar(
        row.get("predictive_recovery_used_count", row.get("recovery_used"))
    )
    recovery_success = parse_scalar(
        row.get("predictive_recovery_success_count", row.get("recovery_success"))
    )
    recovery_failed = parse_scalar(
        row.get("recovery_failed_count", row.get("recovery_failed"))
    )
    base_key = (
        "margin_violation_count"
        if "margin_violation_count" in row
        else "base_horizon_margin_violation_count"
    )
    base_value = parse_scalar(row.get(base_key))
    if base_value is not None and base_value > 0:
        event_type = (
            f"dt_warning_H{int(float(horizon))}"
            if parse_scalar(horizon) in {1.0, 2.0, 3.0}
            else "dt_warning_any"
        )
        builder.add(
            event_type,
            evidence,
            base_value,
            "count",
            S2,
            S3,
            "activate_recovery"
            if recovery_used is not None and recovery_used > 0
            else "command_slowdown_candidate",
            "offline_reconstruction_only",
            "high",
            "Finite-horizon margin warning; this is not collision.",
        )

    if recovery_used is not None and recovery_used > 0:
        builder.add(
            "recovery_used",
            evidence,
            recovery_used,
            "count",
            S3,
            S4,
            "activate_recovery",
            recovery_scope,
            "high",
            "Named recovery activation reconstructed from aggregate evidence.",
        )
    if recovery_success is not None and recovery_success > 0:
        builder.add(
            "recovery_success",
            evidence,
            recovery_success,
            "count",
            S4,
            S2,
            "activate_recovery",
            recovery_scope,
            "high",
            "Recovery success is configuration-specific and followed by verification.",
        )
    if recovery_failed is not None and recovery_failed > 0:
        builder.add(
            "recovery_failed",
            evidence,
            recovery_failed,
            "count",
            S4,
            S6,
            "safe_halt_candidate",
            "offline_reconstruction_only",
            "high",
            "Failed recovery maps to a conservative halt candidate.",
        )


def extract_synthetic(
    builder: EventBuilder, text: str, tables: Sequence[MarkdownTable]
) -> None:
    for table in find_tables(
        tables,
        {"method", "num_cases", "repair_success_count", "full_query_verified_count"},
        {"synthetic_category"},
    )[:1]:
        for row in table.rows:
            success = parse_scalar(row.get("repair_success_count"))
            if success is not None and success > 0:
                method = row.get("method", "").strip().strip("`").lower()
                if method == "no_repair":
                    builder.add(
                        "start_certified",
                        evidence_from_row(table, row),
                        success,
                        "count",
                        S0,
                        S1,
                        "admit_task",
                        "offline_reconstruction_only",
                        "medium",
                        "No-repair full-query-valid cases are reconstructed as already admissible, not repaired.",
                    )
                    continue
                builder.add(
                    "start_repaired",
                    evidence_from_row(table, row),
                    success,
                    "count",
                    S0,
                    S1,
                    "admit_task",
                    "implemented_supported",
                    "high",
                    "Repair outcome includes aggregate full-query validation evidence.",
                )
    for table in find_tables(
        tables,
        {
            "method",
            "collision_count",
            "qp_infeasible_count",
            "base_horizon_margin_violation_count",
            "predictive_recovery_used_count",
        },
    )[:1]:
        for row in table.rows:
            add_navigation_row_events(builder, table, row)
            add_dt_recovery_row_events(
                builder, table, row, "implemented_supported"
            )


def extract_startguard_flight(
    builder: EventBuilder, text: str, tables: Sequence[MarkdownTable]
) -> None:
    values = parse_key_values(text)
    success = parse_scalar(values.get("repair_success_count"))
    if success is not None and success > 0:
        builder.add(
            "start_repaired",
            f"repair_success_count: {values['repair_success_count']}",
            success,
            "count",
            S0,
            S1,
            "admit_task",
            "implemented_supported",
            "high",
            "StartGuard report records successful repairs.",
        )
    failure = parse_scalar(values.get("repair_failure_count"))
    if failure is not None and failure > 0:
        builder.add(
            "start_repair_failed",
            f"repair_failure_count: {values['repair_failure_count']}",
            failure,
            "count",
            S0,
            S6,
            "safe_halt_candidate",
            "offline_reconstruction_only",
            "high",
            "Unresolved repair maps to conservative halt.",
        )
    for table in find_tables(
        tables, {"method", "collision_count", "qp_infeasible_count"}
    )[:1]:
        for row in table.rows:
            add_navigation_row_events(builder, table, row)


def extract_startguard_trial(
    builder: EventBuilder, text: str, tables: Sequence[MarkdownTable]
) -> None:
    values = parse_key_values(text)
    if values.get("repair_success", "").strip().lower() == "true":
        builder.add(
            "start_repaired",
            "repair_success: True",
            True,
            "boolean",
            S0,
            S1,
            "admit_task",
            "implemented_supported",
            "high",
            "Trial57 report explicitly records repair success.",
        )
    for table in find_tables(
        tables, {"method", "collision_count", "qp_infeasible_count"}
    )[:1]:
        for row in table.rows:
            add_navigation_row_events(builder, table, row)


def extract_dt_consolidation(
    builder: EventBuilder, text: str, tables: Sequence[MarkdownTable]
) -> None:
    selected = find_tables(
        tables,
        {
            "horizon",
            "margin_violation_count",
            "collision_count",
            "qp_infeasible_count",
        },
    )[:1]
    total_warnings = 0.0
    for table in selected:
        for row in table.rows:
            add_navigation_row_events(builder, table, row)
            add_dt_recovery_row_events(
                builder, table, row, "offline_reconstruction_only"
            )
            total_warnings += parse_scalar(row.get("margin_violation_count")) or 0.0
    if total_warnings > 0:
        builder.add(
            "replan_candidate",
            f"verification-only aggregate warnings={int(total_warnings)}",
            int(total_warnings),
            "count",
            S3,
            S5,
            "replan_request_candidate",
            "interface_level",
            "medium",
            "Persistent warnings without recovery are reconstructed only as a planner-interface candidate.",
        )


def extract_v4a(
    builder: EventBuilder, text: str, tables: Sequence[MarkdownTable]
) -> None:
    for table in find_tables(
        tables, {"method", "repair_success_count", "full_query_verified_count"}
    )[:1]:
        for row in table.rows:
            success = parse_scalar(row.get("repair_success_count"))
            if success is not None and success > 0:
                builder.add(
                    "start_repaired",
                    evidence_from_row(table, row),
                    success,
                    "count",
                    S0,
                    S1,
                    "admit_task",
                    "implemented_supported",
                    "high",
                    "Full-query verified projection evidence.",
                )
    for table in find_tables(
        tables, {"section", "collision_count", "qp_infeasible_count"}
    )[:1]:
        for row in table.rows:
            add_navigation_row_events(builder, table, row)
    for table in find_tables(
        tables, {"section", "predicted_next_violation_count"}
    )[:1]:
        for row in table.rows:
            count = parse_scalar(row.get("predicted_next_violation_count"))
            if count is not None and count > 0:
                evidence = evidence_from_row(table, row)
                builder.add(
                    "dt_warning_any",
                    evidence,
                    count,
                    "count",
                    S2,
                    S3,
                    "command_slowdown_candidate",
                    "offline_reconstruction_only",
                    "high",
                    "One-step DT violation is reconstructed as warning, not collision.",
                )
                builder.add(
                    "replan_candidate",
                    evidence,
                    count,
                    "count",
                    S3,
                    S5,
                    "replan_request_candidate",
                    "interface_level",
                    "medium",
                    "Repeated warning evidence supports only an interface-level replan candidate.",
                )


def extract_v4c_table_report(
    builder: EventBuilder, text: str, tables: Sequence[MarkdownTable]
) -> None:
    for table in find_tables(
        tables,
        {
            "collision_count",
            "qp_infeasible_count",
            "base_horizon_margin_violation_count",
        },
        {"trial"},
    )[:1]:
        for row in table.rows:
            add_navigation_row_events(
                builder, table, row, "implemented_supported"
            )
            add_dt_recovery_row_events(
                builder, table, row, "implemented_supported"
            )


def extract_v4c_vertical(
    builder: EventBuilder, text: str, tables: Sequence[MarkdownTable]
) -> None:
    values = parse_key_values(text)
    row = {
        "collision_count": values.get("collision_count", ""),
        "qp_infeasible_count": values.get("qp_infeasible_count", ""),
        "base_horizon_margin_violation_count": values.get(
            "base_horizon_margin_violation_count", ""
        ),
        "exec_horizon_margin_violation_count": values.get(
            "exec_horizon_margin_violation_count", ""
        ),
        "predictive_recovery_used_count": values.get(
            "predictive_recovery_used_count", ""
        ),
        "predictive_recovery_success_count": values.get(
            "predictive_recovery_success_count", ""
        ),
        "recovery_failed_count": values.get("recovery_failed_count", ""),
    }
    table = MarkdownTable(26, list(row), [row])
    add_navigation_row_events(builder, table, row, "implemented_supported")
    add_dt_recovery_row_events(builder, table, row, "implemented_supported")


def extract_v4c_tuned(
    builder: EventBuilder, text: str, tables: Sequence[MarkdownTable]
) -> None:
    for table in find_tables(
        tables,
        {
            "rows",
            "collision_count",
            "qp_infeasible_count",
            "base_horizon_margin_violation_count",
            "predictive_recovery_used_count",
        },
        {"run", "trial"},
    )[:1]:
        for row in table.rows:
            add_navigation_row_events(
                builder, table, row, "implemented_supported"
            )
            add_dt_recovery_row_events(
                builder, table, row, "implemented_supported"
            )


def extract_fc_aware(
    builder: EventBuilder, text: str, tables: Sequence[MarkdownTable]
) -> None:
    selected = find_tables(
        tables,
        {"profile", "collision_count", "qp_infeasible_count", "dt_warning"},
    )[:1]
    for table in selected:
        for row in table.rows:
            evidence = evidence_from_row(table, row)
            add_navigation_row_events(builder, table, row, "diagnostic_only")
            warning = parse_scalar(row.get("dt_warning"))
            if warning is not None and warning > 0:
                builder.add(
                    "dt_warning_any",
                    evidence,
                    warning,
                    "count",
                    S2,
                    S3,
                    "command_slowdown_candidate",
                    "diagnostic_only",
                    "high",
                    "Recovery-disabled diagnostic warning; warning is not collision.",
                )
    builder.add(
        "recovery_disabled",
        "fixed and capped recovery-disabled trial0 evaluation",
        True,
        "boolean",
        S3,
        S5,
        "replan_request_candidate",
        "interface_level",
        "medium",
        "Recovery-disabled collision supports only a candidate replan escalation.",
    )
    builder.add(
        "diagnostic_negative",
        "collision occurred in both fixed and capped configurations",
        2,
        "configurations",
        NA,
        NA,
        "diagnostic_only",
        "diagnostic_only",
        "high",
        "Do not attribute collision causality to the FC-Aware cap.",
    )


def extract_mpc_diagnostic(
    builder: EventBuilder, text: str, tables: Sequence[MarkdownTable]
) -> None:
    for table in find_tables(
        tables,
        {"profile", "triggers", "success", "base_violations", "selected_violations"},
    )[:1]:
        for row in table.rows:
            evidence = evidence_from_row(table, row)
            base = parse_scalar(row.get("base_violations"))
            selected = parse_scalar(row.get("selected_violations"))
            triggers = parse_scalar(row.get("triggers"))
            success = parse_scalar(row.get("success"))
            if base is not None and base > 0:
                builder.add(
                    "dt_warning_any",
                    evidence,
                    base,
                    "count",
                    S2,
                    S3,
                    "command_slowdown_candidate",
                    "diagnostic_only",
                    "high",
                    "Offline diagnostic margin violations; not closed-loop evidence.",
                )
            if triggers is not None and triggers > 0:
                builder.add(
                    "recovery_used",
                    evidence,
                    triggers,
                    "count",
                    S3,
                    S4,
                    "diagnostic_only",
                    "diagnostic_only",
                    "high",
                    "Primitive offline evaluator activation, not supported V4-C recovery.",
                )
            if success is not None and success > 0:
                builder.add(
                    "recovery_success",
                    evidence,
                    success,
                    "count",
                    S4,
                    S2,
                    "diagnostic_only",
                    "diagnostic_only",
                    "medium",
                    "Offline evaluator success is diagnostic and not closed-loop validation.",
                )
            if selected is not None and selected > 0:
                builder.add(
                    "diagnostic_negative",
                    evidence,
                    selected,
                    "count",
                    S4,
                    S5,
                    "replan_request_candidate",
                    "diagnostic_only",
                    "high",
                    "Unresolved selected violations support a diagnostic replan candidate only.",
                )


def extract_navigation_audit(
    builder: EventBuilder, text: str, tables: Sequence[MarkdownTable]
) -> None:
    builder.add(
        "unsupported_or_missing",
        "Static navigation-stack audit documents solver, DT, and recovery interfaces.",
        None,
        "textual",
        NA,
        NA,
        "diagnostic_only",
        "diagnostic_only",
        "high",
        "Textual evidence only; no aggregate event count is inferred.",
    )


EXTRACTORS = {
    "REPORT_SYNTHETIC_INITIAL_UNSAFE_STRESS_TEST.md": extract_synthetic,
    "REPORT_STARTGUARD_FLIGHT100.md": extract_startguard_flight,
    "REPORT_STARTGUARD_TRIAL57.md": extract_startguard_trial,
    "REPORT_DISCRETE_TIME_VERIFICATION_CONSOLIDATION.md": extract_dt_consolidation,
    "REPORT_V4A_ACTIVE_PROJECTION_DT_AUDIT.md": extract_v4a,
    "REPORT_V4C_HSTEP_PREDICTIVE_RECOVERY.md": extract_v4c_table_report,
    "REPORT_V4C_FLIGHT100_VALIDATION.md": extract_v4c_vertical,
    "REPORT_V4C_TUNED_FULL100_VALIDATION.md": extract_v4c_tuned,
    "REPORT_FC_AWARE_V1_FLIGHT20_STOP_REASON_RECONCILIATION.md": extract_fc_aware,
    "REPORT_MPC_STYLE_RECOVERY_TARGETED_PILOT.md": extract_mpc_diagnostic,
    "REPORT_SAFER_BASELINE_NAVIGATION_STACK_AUDIT.md": extract_navigation_audit,
}


def prohibited_path(path: Path) -> bool:
    lower = path.as_posix().lower()
    return (
        path.suffix.lower() == ".jsonl"
        or any(part in lower for part in PROHIBITED_PARTS)
    )


def discover_compact_local_sources(
    repo_root: Path, reports_dir: Path, output_dir: Path
) -> list[Path]:
    candidates: set[Path] = set()
    results_root = reports_dir / "results"
    if not results_root.exists():
        return []
    for pattern in ("*summary*.csv", "*metrics*.json", "*inventory*.csv"):
        candidates.update(results_root.rglob(pattern))
    allowed: list[Path] = []
    for path in sorted(candidates):
        resolved = path.resolve()
        if output_dir == resolved or output_dir in resolved.parents:
            continue
        if prohibited_path(resolved) or not resolved.is_file():
            continue
        if resolved.stat().st_size > MAX_LOCAL_FILE_BYTES:
            continue
        allowed.append(resolved)
    return allowed


def flatten_json(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    items: list[tuple[str, Any]] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_prefix = f"{prefix}.{key}" if prefix else str(key)
            items.extend(flatten_json(child, child_prefix))
    elif isinstance(value, list):
        for index, child in enumerate(value[:1000]):
            items.extend(flatten_json(child, f"{prefix}[{index}]"))
    else:
        items.append((prefix, value))
    return items


def extract_compact_source(builder: EventBuilder, path: Path) -> None:
    pairs: list[tuple[str, Any]] = []
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        pairs = flatten_json(data)
    elif path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row_index, row in enumerate(reader):
                if row_index >= 1000:
                    break
                pairs.extend((f"row{row_index}.{key}", value) for key, value in row.items())

    for key, raw_value in pairs:
        metric = normalize_header(key.split(".")[-1])
        value = parse_scalar(raw_value)
        evidence = f"{key}={raw_value}"
        if value is None:
            continue
        if metric == "qp_infeasible_count":
            add_navigation_row_events(
                builder,
                MarkdownTable(0, [metric], [{metric: str(raw_value)}]),
                {metric: str(raw_value)},
            )
        elif metric in {
            "base_horizon_margin_violation_count",
            "margin_violation_count",
        } and value > 0:
            row = {metric: str(raw_value)}
            add_dt_recovery_row_events(
                builder,
                MarkdownTable(0, [metric], [row]),
                row,
                "offline_reconstruction_only",
            )
        elif metric in {
            "predictive_recovery_used_count",
            "predictive_recovery_success_count",
            "recovery_failed_count",
        }:
            row = {metric: str(raw_value)}
            add_dt_recovery_row_events(
                builder,
                MarkdownTable(0, [metric], [row]),
                row,
                "offline_reconstruction_only",
            )
        elif metric == "collision_count":
            add_navigation_row_events(
                builder,
                MarkdownTable(0, [metric], [{metric: str(raw_value)}]),
                {metric: str(raw_value)},
            )
        else:
            continue
        if builder.events:
            builder.events[-1].evidence_text = evidence
            builder.events[-1].confidence = "medium"
            builder.events[-1].notes += " Optional compact local source."


def write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def summarize_transitions(events: Sequence[Event]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str, str], list[Event]] = defaultdict(list)
    for event in events:
        if event.safc_from_state == NA or event.safc_to_state == NA:
            continue
        groups[(event.safc_from_state, event.safc_to_state, event.event_type)].append(
            event
        )
    rows: list[dict[str, Any]] = []
    for (from_state, to_state, event_type), group in sorted(groups.items()):
        rows.append(
            {
                "from_state": from_state,
                "to_state": to_state,
                "event_type": event_type,
                "count": len(group),
                "sources": ";".join(sorted({event.source_id for event in group})),
                "feedback_actions": ";".join(
                    sorted({event.feedback_action for event in group})
                ),
                "claim_scopes": ";".join(
                    sorted({event.claim_scope for event in group})
                ),
                "confidence_min": min(
                    (event.confidence for event in group),
                    key=lambda item: CONFIDENCE_RANK[item],
                ),
                "notes": "Grouped report-level aggregate event mappings.",
            }
        )
    return rows


def summarize_actions(events: Sequence[Event]) -> list[dict[str, Any]]:
    groups: dict[str, list[Event]] = defaultdict(list)
    for event in events:
        if event.feedback_action != NA:
            groups[event.feedback_action].append(event)
    rows: list[dict[str, Any]] = []
    for action, group in sorted(groups.items()):
        event_counts = Counter(event.event_type for event in group)
        dominant = ",".join(
            event_type
            for event_type, _ in sorted(
                event_counts.items(), key=lambda item: (-item[1], item[0])
            )[:3]
        )
        claim_scopes = sorted({event.claim_scope for event in group})
        rows.append(
            {
                "feedback_action": action,
                "count": len(group),
                "source_count": len({event.source_id for event in group}),
                "dominant_event_types": dominant,
                "claim_scopes": ";".join(claim_scopes),
                "implemented_supported_count": sum(
                    event.claim_scope == "implemented_supported" for event in group
                ),
                "interface_level_count": sum(
                    event.claim_scope == "interface_level" for event in group
                ),
                "diagnostic_only_count": sum(
                    event.claim_scope == "diagnostic_only" for event in group
                ),
                "notes": "Counts are reconstructed event rows, not performance gains.",
            }
        )
    return rows


def write_notes(path: Path) -> None:
    path.write_text(
        """# SAFC Level-1 Reconstruction Notes

## Scope

This is Level-1 offline reconstruction. It validates whether existing reports
can be consistently mapped into the SAFC state machine. It does not run new
experiments, does not modify control, and does not claim SAFC performance
improvement.

## Source Policy

The default run reads only the designated `REPORT*.md` files. Optional local
inputs are limited to compact `summary`, `metrics`, or `inventory` CSV/JSON
files smaller than 5 MiB. The reconstruction does not read raw traces,
`trials.csv`, per-step dumps, active-constraint dumps, trajectory samples, or
JSONL files.

## Mapping Rules

1. **Start-Safe / repair:** explicit certification, successful repair, or
   full-query verification maps S0 Pre-Execution Certification to S1 Nominal
   Filtering with `admit_task`. Unresolved repair maps to a halt or replan
   candidate only when directly supported.
2. **CBF-QP:** zero aggregate infeasibility maps S1 to S2 with `no_feedback`.
   Positive infeasibility maps to S4 only when recovery availability is
   explicit; otherwise it maps conservatively to an S6 halt candidate.
3. **DT Verification:** positive H1/H2/H3 or aggregate horizon-margin counts map
   S2 to S3. The feedback is a slowdown candidate unless the same named
   evidence explicitly activates recovery.
4. **Triggered Recovery:** named V4-C use maps S3 to S4; named success with
   post-recovery margin resolution maps S4 to S2. Recovery failure maps S4 to
   an S6 halt candidate.
5. **Collision / stop:** positive collision evidence maps the active execution
   context to an S6 halt candidate. FC-Aware fixed/capped collision evidence is
   diagnostic and does not assign causality to the cap.
6. **Replan candidate:** repeated warning, unresolved recovery, recovery-disabled
   collision, or repeated DT risk may map S3/S4 to S5 with
   `replan_request_candidate`. This is an interface-level reconstruction, not
   an implemented planner.

## Claim Boundaries

- DT warning is not collision.
- QP infeasibility is not collision.
- Recovery success is configuration-specific.
- Replan request is interface-level.
- Risk-cost update is future planner integration unless separately implemented.
- Safe halt is a conservative fallback, not global safety proof.

## Limitations

- Report-level aggregate evidence only.
- Not per-step state reconstruction unless compact per-event summaries exist.
- Missing scripts/results remain release gaps.
- No new controller behavior.
- No performance improvement claim.
- No planner validation.
- No real-robot validation.
- Event counts reflect reconstructed evidence rows, not independent trials or
  causal effects.
""",
        encoding="utf-8",
    )


def validate_records(sources: Sequence[SourceRecord], events: Sequence[Event]) -> None:
    source_ids = {source.source_id for source in sources}
    if len(source_ids) != len(sources):
        raise ValueError("duplicate source_id detected")
    for event in events:
        if event.source_id not in source_ids:
            raise ValueError(f"unknown source_id in {event.event_id}: {event.source_id}")
        if event.event_type not in ALLOWED_EVENT_TYPES:
            raise ValueError(
                f"unknown event_type in {event.event_id}: {event.event_type}"
            )
        if event.safc_from_state not in ALLOWED_STATES:
            raise ValueError(
                f"unknown from state in {event.event_id}: {event.safc_from_state}"
            )
        if event.safc_to_state not in ALLOWED_STATES:
            raise ValueError(
                f"unknown to state in {event.event_id}: {event.safc_to_state}"
            )
        if event.feedback_action not in ALLOWED_ACTIONS:
            raise ValueError(
                f"unknown feedback action in {event.event_id}: {event.feedback_action}"
            )
        if event.claim_scope not in ALLOWED_CLAIM_SCOPES:
            raise ValueError(
                f"unknown claim scope in {event.event_id}: {event.claim_scope}"
            )
        if event.confidence not in CONFIDENCE_RANK:
            raise ValueError(
                f"unknown confidence in {event.event_id}: {event.confidence}"
            )
        if not event.evidence_text.strip():
            raise ValueError(f"empty evidence text in {event.event_id}")


def build_metrics(
    sources: Sequence[SourceRecord],
    events: Sequence[Event],
    transition_rows: Sequence[dict[str, Any]],
    action_rows: Sequence[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "task": "SAFC Level-1 Offline Event Reconstruction",
        "new_experiments_run": False,
        "controller_modified": False,
        "official_core_source_modified": False,
        "raw_traces_used": False,
        "sources_scanned": len(sources),
        "sources_used": sum(source.used for source in sources),
        "sources_missing": sum(not source.exists for source in sources),
        "events_reconstructed": len(events),
        "state_transitions_reconstructed": sum(
            event.safc_from_state != NA and event.safc_to_state != NA
            for event in events
        ),
        "state_transition_groups": len(transition_rows),
        "feedback_actions_reconstructed": sum(
            event.feedback_action != NA for event in events
        ),
        "feedback_action_groups": len(action_rows),
        "implemented_supported_events": sum(
            event.claim_scope == "implemented_supported" for event in events
        ),
        "interface_level_events": sum(
            event.claim_scope == "interface_level" for event in events
        ),
        "diagnostic_only_events": sum(
            event.claim_scope == "diagnostic_only" for event in events
        ),
        "future_work_events": sum(
            event.claim_scope == "future_work" for event in events
        ),
        "collision_events_reconstructed": sum(
            event.event_type == "collision" for event in events
        ),
        "dt_warning_events_reconstructed": sum(
            event.event_type.startswith("dt_warning") for event in events
        ),
        "recovery_events_reconstructed": sum(
            event.event_type
            in {"recovery_used", "recovery_success", "recovery_failed"}
            for event in events
        ),
        "safe_halt_candidates": sum(
            event.feedback_action == "safe_halt_candidate" for event in events
        ),
        "replan_request_candidates": sum(
            event.feedback_action == "replan_request_candidate" for event in events
        ),
        "limitations": [
            "offline reconstruction only",
            "aggregate report-level evidence, not per-step replay unless compact summaries are available",
            "does not modify controller",
            "does not claim performance improvement",
            "does not validate planner integration",
            "does not validate real-robot deployment",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reconstruct SAFC report-level events without running simulation."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "work/risk_aware_cbf/results/safc_level1_offline_reconstruction"
        ),
    )
    parser.add_argument(
        "--reports-dir", type=Path, default=Path("work/risk_aware_cbf")
    )
    parser.add_argument(
        "--include-local-results", type=parse_bool, default=False
    )
    return parser.parse_args()


def resolve_under(root: Path, value: Path) -> Path:
    resolved = value.resolve() if value.is_absolute() else (root / value).resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError(f"path escapes repository root: {value}")
    return resolved


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    reports_dir = resolve_under(repo_root, args.reports_dir)
    output_dir = resolve_under(repo_root, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    sources: list[SourceRecord] = []
    all_events: list[Event] = []
    for index, (name, scope, notes) in enumerate(REPORT_SPECS, start=1):
        path = reports_dir / name
        relative = path.relative_to(repo_root).as_posix()
        exists = path.is_file()
        source = SourceRecord(
            source_id=f"SRC{index:03d}",
            source_path=relative,
            source_type="report_markdown" if exists else "missing",
            exists=exists,
            tracked_assumed=exists,
            used=False,
            missing_reason="" if exists else "file not found",
            evidence_scope=scope if exists else "unknown",
            notes=notes if exists else "missing_source",
        )
        sources.append(source)
        if not exists:
            continue
        text = path.read_text(encoding="utf-8")
        tables = parse_markdown_tables(text)
        builder = EventBuilder(source)
        EXTRACTORS[name](builder, text, tables)
        source.used = True
        if not builder.events:
            source.notes += " Textual evidence only."
        all_events.extend(builder.events)

    if args.include_local_results:
        local_paths = discover_compact_local_sources(
            repo_root, reports_dir, output_dir
        )
        for path in local_paths:
            source = SourceRecord(
                source_id=f"SRC{len(sources) + 1:03d}",
                source_path=path.relative_to(repo_root).as_posix(),
                source_type=(
                    "local_untracked_summary"
                    if "results" in path.parts
                    else "compact_summary_csv"
                ),
                exists=True,
                tracked_assumed=False,
                used=False,
                missing_reason="",
                evidence_scope="unknown",
                notes="Optional compact local summary/metrics source.",
            )
            builder = EventBuilder(source)
            extract_compact_source(builder, path)
            source.used = bool(builder.events)
            if not builder.events:
                source.notes += " No recognized SAFC aggregate metrics."
            sources.append(source)
            all_events.extend(builder.events)

    for index, event in enumerate(all_events, start=1):
        event.event_id = f"EVT{index:04d}"

    validate_records(sources, all_events)
    transition_rows = summarize_transitions(all_events)
    action_rows = summarize_actions(all_events)
    metrics = build_metrics(sources, all_events, transition_rows, action_rows)

    write_csv(
        output_dir / "source_inventory.csv",
        SOURCE_FIELDS,
        (asdict(source) for source in sources),
    )
    write_csv(
        output_dir / "event_inventory.csv",
        EVENT_FIELDS,
        (asdict(event) for event in all_events),
    )
    write_csv(
        output_dir / "state_transition_summary.csv",
        TRANSITION_FIELDS,
        transition_rows,
    )
    write_csv(
        output_dir / "feedback_action_summary.csv",
        ACTION_FIELDS,
        action_rows,
    )
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    write_notes(output_dir / "reconstruction_notes.md")

    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
