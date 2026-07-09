#!/usr/bin/env python3
"""Discover targeted warning-rich candidates from tracked compact reports."""

from __future__ import annotations

import argparse
import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence


SOURCE_PATHS = (
    "work/risk_aware_cbf/REPORT_DISCRETE_TIME_VERIFICATION_CONSOLIDATION.md",
    "work/risk_aware_cbf/REPORT_V4C_HSTEP_PREDICTIVE_RECOVERY.md",
    "work/risk_aware_cbf/REPORT_V4C_FLIGHT100_VALIDATION.md",
    "work/risk_aware_cbf/REPORT_V4C_TUNED_FULL100_VALIDATION.md",
    "work/risk_aware_cbf/REPORT_V4A_ACTIVE_PROJECTION_DT_AUDIT.md",
    "work/risk_aware_cbf/REPORT_STARTGUARD_TRIAL57.md",
    "work/risk_aware_cbf/REPORT_STARTGUARD_FLIGHT100.md",
    "work/risk_aware_cbf/REPORT_FC_AWARE_V1_FLIGHT20_STOP_REASON_RECONCILIATION.md",
    "work/risk_aware_cbf/REPORT_MPC_STYLE_RECOVERY_TARGETED_PILOT.md",
)

SOURCE_FIELDS = (
    "source_id",
    "source_path",
    "exists",
    "used",
    "evidence_type",
    "warning_terms_found",
    "recovery_terms_found",
    "collision_terms_found",
    "candidate_terms_found",
    "notes",
)

CANDIDATE_FIELDS = (
    "candidate_id",
    "source_id",
    "source_path",
    "scene",
    "trial_id",
    "case_name",
    "candidate_type",
    "warning_evidence_text",
    "warning_horizon",
    "warning_count_hint",
    "recovery_evidence_text",
    "collision_evidence_text",
    "entrypoint_feasible",
    "expected_natural_warning",
    "priority",
    "claim_scope",
    "notes",
)


@dataclass
class Candidate:
    source_id: str
    source_path: str
    scene: str
    trial_id: int
    case_name: str
    candidate_type: str
    warning_evidence_text: str
    warning_horizon: str
    warning_count_hint: int | None
    recovery_evidence_text: str
    collision_evidence_text: str
    entrypoint_feasible: bool
    expected_natural_warning: bool
    priority: str
    claim_scope: str = "targeted_candidate_only"
    notes: str = ""


def write_csv(
    path: Path, fieldnames: Sequence[str], rows: Iterable[dict[str, Any]]
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def count_terms(text: str, pattern: str) -> int:
    return len(re.findall(pattern, text, flags=re.IGNORECASE))


def parse_markdown_tables(text: str) -> list[tuple[list[str], list[list[str]]]]:
    lines = text.splitlines()
    tables: list[tuple[list[str], list[list[str]]]] = []
    index = 0
    while index + 1 < len(lines):
        header_line = lines[index].strip()
        separator_line = lines[index + 1].strip()
        if (
            header_line.startswith("|")
            and separator_line.startswith("|")
            and re.fullmatch(r"[|:\-\s]+", separator_line)
        ):
            headers = [cell.strip() for cell in header_line.strip("|").split("|")]
            rows: list[list[str]] = []
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                cells = [
                    cell.strip()
                    for cell in lines[index].strip().strip("|").split("|")
                ]
                if len(cells) == len(headers):
                    rows.append(cells)
                index += 1
            tables.append((headers, rows))
            continue
        index += 1
    return tables


def parse_int(value: str) -> int | None:
    match = re.search(r"-?\d+", value)
    return int(match.group(0)) if match else None


def infer_horizon(path: str, text: str) -> str:
    if "TUNED_FULL100" in path or "R4_H2" in text:
        return "H2"
    if "HSTEP" in path or "V4C_FLIGHT100" in path or "H3_N128" in text:
        return "H3"
    if re.search(r"\bH[123]\b", text):
        values = re.findall(r"\bH[123]\b", text)
        return ";".join(sorted(set(values)))
    return "unknown"


def add_or_enrich(
    candidates: list[Candidate],
    candidate: Candidate,
) -> None:
    for existing in candidates:
        if (
            existing.scene == candidate.scene
            and existing.trial_id == candidate.trial_id
        ):
            if (
                candidate.warning_count_hint is not None
                and (
                    existing.warning_count_hint is None
                    or candidate.warning_count_hint > existing.warning_count_hint
                )
            ):
                existing.warning_count_hint = candidate.warning_count_hint
            for attr in (
                "warning_evidence_text",
                "recovery_evidence_text",
                "collision_evidence_text",
            ):
                new_value = getattr(candidate, attr)
                old_value = getattr(existing, attr)
                if new_value and new_value not in old_value:
                    setattr(
                        existing,
                        attr,
                        "; ".join(item for item in (old_value, new_value) if item),
                    )
            existing.expected_natural_warning = (
                existing.expected_natural_warning
                or candidate.expected_natural_warning
            )
            if candidate.priority == "high":
                existing.priority = "high"
            return
    candidates.append(candidate)


def narrative_candidates(
    source_id: str, source_path: str, text: str
) -> list[Candidate]:
    rows: list[Candidate] = []
    if "REPORT_V4C_HSTEP_PREDICTIVE_RECOVERY.md" in source_path:
        match = re.search(
            r"trials\s+12,\s*13,\s*and\s*14.*?trigger H-step recovery repeatedly",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if match:
            evidence = (
                "Tracked report states that flight trials 12, 13, and 14 "
                "trigger H-step recovery repeatedly."
            )
            for trial_id in (12, 13, 14):
                rows.append(
                    Candidate(
                        source_id=source_id,
                        source_path=source_path,
                        scene="flight",
                        trial_id=trial_id,
                        case_name=f"flight_trial{trial_id}_reported_h3_recovery",
                        candidate_type="v4c_recovery_reported",
                        warning_evidence_text=evidence,
                        warning_horizon="H3",
                        warning_count_hint=None,
                        recovery_evidence_text=evidence,
                        collision_evidence_text="",
                        entrypoint_feasible=True,
                        expected_natural_warning=True,
                        priority="high",
                        notes="Narrative report evidence; requires bounded no-op confirmation.",
                    )
                )
    if "REPORT_STARTGUARD_TRIAL57.md" in source_path:
        rows.append(
            Candidate(
                source_id=source_id,
                source_path=source_path,
                scene="flight",
                trial_id=57,
                case_name="flight_trial57_initial_unsafe_diagnostic",
                candidate_type="diagnostic_collision_case",
                warning_evidence_text="",
                warning_horizon="unknown",
                warning_count_hint=None,
                recovery_evidence_text="StartGuard report documents start repair.",
                collision_evidence_text=(
                    "Tracked report records original trial 57 collision_count=1 "
                    "and negative initial safety h."
                ),
                entrypoint_feasible=True,
                expected_natural_warning=False,
                priority="medium",
                notes="Collision evidence is diagnostic, not direct warning evidence.",
            )
        )
    return rows


def table_candidates(
    source_id: str, source_path: str, text: str
) -> list[Candidate]:
    candidates: list[Candidate] = []
    horizon = infer_horizon(source_path, text)
    for headers, rows in parse_markdown_tables(text):
        normalized = [re.sub(r"\s+", "_", header.strip().lower()) for header in headers]
        if "trial" not in normalized:
            continue
        trial_index = normalized.index("trial")
        warning_indexes = [
            index
            for index, name in enumerate(normalized)
            if "margin_violation_count" in name
            and ("base" in name or "horizon" in name)
        ]
        recovery_indexes = [
            index
            for index, name in enumerate(normalized)
            if name == "predictive_recovery_used_count"
        ]
        collision_indexes = [
            index for index, name in enumerate(normalized) if name == "collision_count"
        ]
        if not warning_indexes and not recovery_indexes and not collision_indexes:
            continue
        for row in rows:
            trial_id = parse_int(row[trial_index])
            if trial_id is None or not 0 <= trial_id < 100:
                continue
            warning_counts = [
                parse_int(row[index]) or 0 for index in warning_indexes
            ]
            recovery_counts = [
                parse_int(row[index]) or 0 for index in recovery_indexes
            ]
            collision_counts = [
                parse_int(row[index]) or 0 for index in collision_indexes
            ]
            warning_count = max(warning_counts, default=0)
            recovery_count = max(recovery_counts, default=0)
            collision_count = max(collision_counts, default=0)
            if warning_count <= 0 and recovery_count <= 0 and collision_count <= 0:
                continue
            warning_evidence = (
                f"Table row reports base horizon margin violations={warning_count}."
                if warning_count > 0
                else ""
            )
            recovery_evidence = (
                f"Table row reports predictive recovery used={recovery_count}."
                if recovery_count > 0
                else ""
            )
            collision_evidence = (
                f"Table row reports collision_count={collision_count}."
                if collision_count > 0
                else ""
            )
            candidate_type = (
                "dt_warning_reported"
                if warning_count > 0
                else (
                    "v4c_recovery_reported"
                    if recovery_count > 0
                    else "diagnostic_collision_case"
                )
            )
            expected_warning = warning_count > 0 or recovery_count > 0
            candidates.append(
                Candidate(
                    source_id=source_id,
                    source_path=source_path,
                    scene="flight",
                    trial_id=trial_id,
                    case_name=f"flight_trial{trial_id}_{horizon.lower()}_table",
                    candidate_type=candidate_type,
                    warning_evidence_text=warning_evidence,
                    warning_horizon=horizon,
                    warning_count_hint=max(warning_count, recovery_count) or None,
                    recovery_evidence_text=recovery_evidence,
                    collision_evidence_text=collision_evidence,
                    entrypoint_feasible=True,
                    expected_natural_warning=expected_warning,
                    priority="high" if expected_warning else "medium",
                    notes="Tracked compact report table; requires bounded no-op confirmation.",
                )
            )
    return candidates


def discover(
    repo_root: Path,
    output_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_rows: list[dict[str, Any]] = []
    candidates: list[Candidate] = []
    source_candidate_counts: dict[str, int] = {}
    evidence_sources: set[str] = set()
    for index, relative_path in enumerate(SOURCE_PATHS, start=1):
        source_id = f"SRC{index:03d}"
        path = repo_root / relative_path
        exists = path.is_file()
        text = path.read_text(encoding="utf-8") if exists else ""
        if exists:
            found_candidates = narrative_candidates(
                source_id, relative_path, text
            ) + table_candidates(source_id, relative_path, text)
            for candidate in found_candidates:
                add_or_enrich(candidates, candidate)
            if found_candidates:
                evidence_sources.add(source_id)
            source_candidate_counts[source_id] = len(found_candidates)
        else:
            source_candidate_counts[source_id] = 0
        source_rows.append(
            {
                "source_id": source_id,
                "source_path": relative_path,
                "exists": exists,
                "used": False,
                "evidence_type": "tracked_report" if exists else "missing",
                "warning_terms_found": count_terms(
                    text,
                    r"\bwarning\b|margin violation|horizon margin violation|DT warning",
                ),
                "recovery_terms_found": count_terms(
                    text, r"\brecovery\b|recovery_used|predictive_recovery"
                ),
                "collision_terms_found": count_terms(text, r"\bcollision\b"),
                "candidate_terms_found": count_terms(
                    text, r"\btrial[-_ ]?\d+\b|\|\s*\d+\s*\|"
                ),
                "notes": (
                    "Tracked report scanned; raw referenced artifacts were not read."
                    if exists
                    else "Required source report is missing."
                ),
            }
        )

    priority_order = {"high": 0, "medium": 1, "low": 2}
    candidates.sort(
        key=lambda item: (
            priority_order[item.priority],
            0 if item.source_path.endswith("REPORT_V4C_HSTEP_PREDICTIVE_RECOVERY.md") else 1,
            -1 if item.warning_count_hint is None else -item.warning_count_hint,
            item.trial_id,
        )
    )
    candidate_rows: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates, start=1):
        row = candidate.__dict__.copy()
        row["candidate_id"] = f"C{index:03d}"
        candidate_rows.append(row)
    for source_row in source_rows:
        source_row["used"] = source_row["source_id"] in evidence_sources
        if source_candidate_counts[source_row["source_id"]] > 0:
            source_row["notes"] += (
                f" Added {source_candidate_counts[source_row['source_id']]} "
                "unique candidate(s) before cross-source enrichment."
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(
        output_dir / "candidate_source_inventory.csv",
        SOURCE_FIELDS,
        source_rows,
    )
    write_csv(
        output_dir / "warning_rich_candidate_inventory.csv",
        CANDIDATE_FIELDS,
        candidate_rows,
    )
    return source_rows, candidate_rows


def write_discovery_notes(
    path: Path,
    source_rows: Sequence[dict[str, Any]],
    candidate_rows: Sequence[dict[str, Any]],
) -> None:
    existing = sum(bool(row["exists"]) for row in source_rows)
    high = sum(row["priority"] == "high" for row in candidate_rows)
    path.write_text(
        f"""# SAFC Level-3B Warning-Rich Discovery Notes

The discovery pass scanned {existing}/{len(source_rows)} tracked report
sources and produced {len(candidate_rows)} unique targeted candidates,
including {high} high-priority candidates.

Only tracked Markdown reports were read. Referenced raw traces, full
`trials.csv`, per-step files, active-constraint files, trajectory samples, and
JSONL files were not read.

Candidates are evidence-backed hypotheses until the bounded Stage-A no-op scan
confirms a natural H1/H2/H3 warning in the current wrapper.
""",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Discover SAFC Level-3B warning-rich targeted candidates."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "work/risk_aware_cbf/results/safc_level3b_warning_rich_targeted"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    source_rows, candidate_rows = discover(repo_root, output_dir)
    write_discovery_notes(
        output_dir / "warning_rich_notes.md", source_rows, candidate_rows
    )
    print(
        f"sources={len(source_rows)} candidates={len(candidate_rows)} "
        f"high_priority={sum(row['priority'] == 'high' for row in candidate_rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
