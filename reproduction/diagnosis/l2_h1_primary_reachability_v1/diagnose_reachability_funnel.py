#!/usr/bin/env python3
"""One-pass, compact diagnosis of the frozen primary eligibility funnel."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


DATA_ROLE = "FORMAL_PROSPECTIVE_SHADOW_COHORT_V1"
TYPED_L2 = {"PASS", "FAIL", "UNKNOWN"}

GATES = [
    ("G1", "data_role", "data_role=FORMAL_PROSPECTIVE_SHADOW_COHORT_V1", lambda row: row.get("data_role") == DATA_ROLE),
    ("G2", "logging_qc_complete", "logging_qc_complete=true", lambda row: row.get("logging_qc_complete") is True),
    ("G3", "selected_candidate_role", "selected_candidate_role=SELECTED_EXECUTED_CONTROL", lambda row: row.get("selected_candidate_role") == "SELECTED_EXECUTED_CONTROL"),
    ("G4", "selected_candidate_committed", "selected_candidate_committed=true", lambda row: row.get("selected_candidate_committed") is True),
    ("G5", "l1_observation_source", "l1_observation_source=SHADOW_RECOMPUTED_FROZEN_CERTIFIER", lambda row: row.get("l1_observation_source") == "SHADOW_RECOMPUTED_FROZEN_CERTIFIER"),
    ("G6", "l1_status", "l1_status=PASS", lambda row: row.get("l1_status") == "PASS"),
    ("G7", "l2_reached", "l2_reached=true", lambda row: row.get("l2_reached") is True),
    ("G8", "l2_status", "l2_status in {PASS,FAIL,UNKNOWN}", lambda row: row.get("l2_status") in TYPED_L2),
    ("G9", "map_authority_valid", "map_authority_valid=true", lambda row: row.get("map_authority_valid") is True),
    ("G10", "payload_join_identity_valid", "payload_join_identity_valid=true", lambda row: row.get("payload_join_identity_valid") is True),
]

L1_REASON_CANDIDATES = ("l1_reason", "l1_status_reason")
L2_REASON_CANDIDATES = ("l2_reachability_reason", "l2_reached_reason", "reachability_reason")


class DiagnosisContradictionError(RuntimeError):
    pass


def value_label(row: dict[str, Any], field: str) -> str:
    if field not in row:
        return "__MISSING__"
    value = row[field]
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def l2_reach_label(row: dict[str, Any]) -> str:
    value = row.get("l2_reached")
    if value is True:
        return "true"
    if value is False:
        return "false"
    return "missing_or_invalid"


def diagnose_rows(rows: Iterable[dict[str, Any]], expected: dict[str, int] | None = None) -> dict[str, Any]:
    overlapping = Counter({gate_id: 0 for gate_id, *_ in GATES})
    first_failures = Counter({gate_id: 0 for gate_id, *_ in GATES})
    cumulative_support = Counter({gate_id: 0 for gate_id, *_ in GATES})
    l1_status = Counter()
    l1_source = Counter()
    l2_reach = Counter({"true": 0, "false": 0, "missing_or_invalid": 0})
    l2_status = Counter()
    field_presence = Counter()
    field_types: dict[str, set[str]] = defaultdict(set)
    reason_distributions: dict[str, Counter[str]] = defaultdict(Counter)
    dependencies: dict[str, Counter[tuple[str, str]]] = {
        "l1_status_x_l2_reached": Counter(),
        "l1_observation_source_x_l1_status": Counter(),
        "l2_reached_x_l2_status_typed": Counter(),
    }
    row_count = 0
    n_primary = 0
    n_l2_typed = 0
    n_l1_pass_l2_typed = 0
    trial_ids: set[str] = set()

    for row in rows:
        row_count += 1
        if "trial_id" in row:
            trial_ids.add(str(row["trial_id"]))
        for field, value in row.items():
            field_presence[field] += 1
            field_types[field].add(type(value).__name__)

        l1_label = value_label(row, "l1_status")
        source_label = value_label(row, "l1_observation_source")
        reach_label = l2_reach_label(row)
        status_label = value_label(row, "l2_status")
        typed_label = "typed" if row.get("l2_status") in TYPED_L2 else "not_typed"
        l1_status[l1_label] += 1
        l1_source[source_label] += 1
        l2_reach[reach_label] += 1
        l2_status[status_label] += 1
        n_l2_typed += int(typed_label == "typed")
        n_l1_pass_l2_typed += int(l1_label == "PASS" and typed_label == "typed")
        dependencies["l1_status_x_l2_reached"][(l1_label, reach_label)] += 1
        dependencies["l1_observation_source_x_l1_status"][(source_label, l1_label)] += 1
        dependencies["l2_reached_x_l2_status_typed"][(reach_label, typed_label)] += 1

        for field in (*L1_REASON_CANDIDATES, *L2_REASON_CANDIDATES):
            if field in row:
                reason_distributions[field][value_label(row, field)] += 1
                if field in L2_REASON_CANDIDATES:
                    dependencies.setdefault("l1_status_x_reachability_reason", Counter())[(l1_label, value_label(row, field))] += 1

        gate_results = [(gate_id, predicate(row)) for gate_id, _, _, predicate in GATES]
        for gate_id, passed in gate_results:
            if not passed:
                overlapping[gate_id] += 1
        first_failed = next((gate_id for gate_id, passed in gate_results if not passed), None)
        if first_failed is None:
            n_primary += 1
        else:
            first_failures[first_failed] += 1
        prefix_pass = True
        for gate_id, passed in gate_results:
            prefix_pass = prefix_pass and passed
            cumulative_support[gate_id] += int(prefix_pass)

    earliest = next((gate_id for gate_id, *_ in GATES if cumulative_support[gate_id] == 0), "NOT_UNIQUELY_IDENTIFIED")
    earliest_count = first_failures.get(earliest, 0) if earliest != "NOT_UNIQUELY_IDENTIFIED" else 0
    algebra = sum(first_failures.values()) + n_primary
    if algebra != row_count:
        raise DiagnosisContradictionError(f"first-failure algebra mismatch: {algebra} != {row_count}")

    if expected:
        actuals = {
            "row_count": row_count,
            "N_primary": n_primary,
            "N_l2_reached_true": l2_reach["true"],
        }
        mismatches = {key: (actuals[key], value) for key, value in expected.items() if actuals.get(key) != value}
        if mismatches:
            raise DiagnosisContradictionError(f"frozen compact contradiction: {mismatches}")

    l1_pass = l1_status["PASS"]
    l1_pass_l2_true = dependencies["l1_status_x_l2_reached"][("PASS", "true")]
    l1_pass_l2_false = dependencies["l1_status_x_l2_reached"][("PASS", "false")]
    l1_pass_l2_invalid = dependencies["l1_status_x_l2_reached"][("PASS", "missing_or_invalid")]
    data_only = {
        "downstream_zero_support_consequence": f"support after {earliest} is zero, so G7-G10 and N_primary have zero support" if earliest != "NOT_UNIQUELY_IDENTIFIED" else "NOT_UNIQUELY_IDENTIFIED",
        "earliest_universal_blocking_gate": earliest,
        "earliest_universal_blocking_gate_count": earliest_count,
        "whether_L1_PASS_exists": l1_pass > 0,
        "whether_L2_reached_exists": l2_reach["true"] > 0,
        "whether_typed_L2_exists": n_l2_typed > 0,
        "data_only_root_statement": f"{row_count} -> {earliest} -> downstream L2 support = 0 -> N_primary={n_primary}" if earliest != "NOT_UNIQUELY_IDENTIFIED" else "NOT_UNIQUELY_IDENTIFIED",
    }
    if l1_pass == 0:
        data_only["conditional_L2_after_L1_PASS"] = "L2_CONDITIONAL_REACHABILITY_AFTER_L1_PASS_NOT_OBSERVABLE"

    inventory = {
        "fields": {
            field: {"presence_count": field_presence[field], "python_types": sorted(field_types[field])}
            for field in sorted(field_presence)
        },
        "l1_reason_fields": [field for field in L1_REASON_CANDIDATES if field_presence[field] > 0],
        "reachability_reason_fields": [field for field in L2_REASON_CANDIDATES if field_presence[field] > 0],
        "reason_distributions": {field: dict(sorted(counts.items())) for field, counts in sorted(reason_distributions.items())},
    }
    return {
        "N_formal_result_records": row_count,
        "N_l2_status_typed": n_l2_typed,
        "N_primary": n_primary,
        "data_only": data_only,
        "dependencies": dependencies,
        "field_inventory": inventory,
        "first_failures": dict(first_failures),
        "first_failure_algebra": algebra,
        "formal_trial_count": len(trial_ids),
        "l1_observation_source": dict(l1_source),
        "l1_pass_conditional": {
            "L1_PASS": l1_pass,
            "l2_reached_false": l1_pass_l2_false,
            "l2_reached_missing_or_invalid": l1_pass_l2_invalid,
            "l2_reached_true": l1_pass_l2_true,
            "l2_status_typed": n_l1_pass_l2_typed,
        },
        "l1_status": dict(l1_status),
        "l2_reach": dict(l2_reach),
        "l2_status": dict(l2_status),
        "overlapping_unmet": dict(overlapping),
        "row_count": row_count,
        "cumulative_support": dict(cumulative_support),
    }


def stream_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if line.strip():
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise DiagnosisContradictionError(f"row {line_number} is not an object")
                yield row


def write_json(path: Path, value: Any) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_counter_csv(path: Path, rows: Iterable[list[Any]], header: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def emit_outputs(result: dict[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    gate_rows = []
    for gate_id, field, condition, _ in GATES:
        gate_rows.append(
            [
                gate_id,
                field,
                condition,
                result["overlapping_unmet"][gate_id],
                result["first_failures"][gate_id],
                result["cumulative_support"][gate_id],
            ]
        )
    write_counter_csv(
        output_dir / "gate_failure_counts.csv",
        gate_rows,
        ["gate_id", "field", "frozen_condition", "overlapping_unmet_count", "first_failing_count", "cumulative_support_after_gate"],
    )
    row_count = result["row_count"]
    write_counter_csv(
        output_dir / "l1_status_distribution.csv",
        [[value, count, count / row_count if row_count else None] for value, count in sorted(result["l1_status"].items())],
        ["value", "count", "share"],
    )
    write_counter_csv(
        output_dir / "l2_reachability_distribution.csv",
        [[value, result["l2_reach"][value], result["l2_reach"][value] / row_count if row_count else None] for value in ("true", "false", "missing_or_invalid")],
        ["value", "count", "share"],
    )
    dependency_rows: list[list[Any]] = []
    for relation, counter in result["dependencies"].items():
        for (left, right), count in sorted(counter.items()):
            dependency_rows.append([relation, left, right, count])
    write_counter_csv(output_dir / "gate_dependency_table.csv", dependency_rows, ["relation", "left_value", "right_value", "count"])

    funnel = {key: value for key, value in result.items() if key not in {"dependencies", "field_inventory", "data_only"}}
    funnel["formal_result_record_semantics"] = "one canonical joined row exists for each frozen formal result record"
    funnel["result_record_is_not_equivalent_to_l2_evaluation"] = True
    write_json(output_dir / "reachability_funnel.json", funnel)
    write_json(output_dir / "diagnostic_field_inventory.json", result["field_inventory"])
    write_json(output_dir / "DATA_ONLY_DIAGNOSIS.json", result["data_only"])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-row-count", type=int, default=14122)
    parser.add_argument("--expected-primary", type=int, default=0)
    parser.add_argument("--expected-l2-reached", type=int, default=0)
    args = parser.parse_args()
    result = diagnose_rows(
        stream_jsonl(args.input),
        expected={
            "row_count": args.expected_row_count,
            "N_primary": args.expected_primary,
            "N_l2_reached_true": args.expected_l2_reached,
        },
    )
    emit_outputs(result, args.output_dir)
    print(
        json.dumps(
            {
                "N_l2_status_typed": result["N_l2_status_typed"],
                "N_primary": result["N_primary"],
                "earliest_universal_blocking_gate": result["data_only"]["earliest_universal_blocking_gate"],
                "formal_trial_count": result["formal_trial_count"],
                "row_count": result["row_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
