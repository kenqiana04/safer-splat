"""Freeze C0/C1 state selections from existing registries before shadow execution."""
from __future__ import annotations

import csv
from collections import defaultdict

from common import sha256_file, write_csv, write_json
from task_config import FORMAL_ENVIRONMENTS, METHODS, TASK_ROOT, UPSTREAM_ROOT

MAX_PER_ENVIRONMENT = 16


def allocate(groups: dict[str, list[dict[str, str]]], limit: int) -> list[dict[str, str]]:
    total = sum(len(rows) for rows in groups.values())
    quotas = {name: max(1, round(limit * len(rows) / total)) for name, rows in groups.items()}
    while sum(quotas.values()) > limit:
        name = max(quotas, key=lambda key: (quotas[key], len(groups[key]), key))
        if quotas[name] == 1:
            break
        quotas[name] -= 1
    while sum(quotas.values()) < min(limit, total):
        name = max(groups, key=lambda key: (len(groups[key]) / quotas[key], len(groups[key]), key))
        if quotas[name] < len(groups[name]):
            quotas[name] += 1
        else:
            break
    selected: list[dict[str, str]] = []
    for name in sorted(groups):
        rows = sorted(groups[name], key=lambda row: row["state_id"])
        count = min(quotas[name], len(rows))
        selected.extend(rows[(index * len(rows)) // count] for index in range(count))
    return sorted(selected, key=lambda row: row["state_id"])


def main() -> None:
    formal = list(csv.DictReader((UPSTREAM_ROOT / "benchmark/one_step_records.csv").open(encoding="utf-8", newline="")))
    output: list[dict[str, str]] = []
    summary = {"status": "PASS_C0_C1_SELECTION_FROZEN", "selection_rule": {}, "environments": {}}
    for environment in FORMAL_ENVIRONMENTS:
        registry_path = UPSTREAM_ROOT / "registry" / environment / "representative_registry.csv"
        registry = list(csv.DictReader(registry_path.open(encoding="utf-8", newline="")))
        c0_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in registry:
            c0_groups[row["source_type"]].append(row)
        c0 = allocate(c0_groups, MAX_PER_ENVIRONMENT)
        b0 = {row["state_id"]: row for row in formal if row["environment"] == environment and row["method"] == METHODS[0]}
        b2 = {row["state_id"]: row for row in formal if row["environment"] == environment and row["method"] == METHODS[2]}
        c1_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in registry:
            state_id = row["state_id"]
            b0_row, b2_row = b0[state_id], b2[state_id]
            if b0_row["current_gate"] == "FAIL" or b2_row["committed"].lower() != "true":
                label = f"B0:{b0_row['typed_status']}|B2:{b2_row['typed_status']}"
                enriched = dict(row); enriched["failure_stratum"] = label
                c1_groups[label].append(enriched)
        c1 = allocate(c1_groups, MAX_PER_ENVIRONMENT) if c1_groups else []
        summary["selection_rule"][environment] = {
            "c0": "source_type stratified then canonical state_id spaced selection",
            "c1": "B0 current failure or B2 noncommit; typed status stratified then canonical state_id spaced selection",
        }
        summary["environments"][environment] = {
            "registry_sha256": sha256_file(registry_path), "c0_count": len(c0), "c1_count": len(c1),
            "c1_eligible_count": sum(len(rows) for rows in c1_groups.values()),
            "c0_strata": {name: len(rows) for name, rows in sorted(c0_groups.items())},
            "c1_strata": {name: len(rows) for name, rows in sorted(c1_groups.items())},
        }
        for cohort, rows in (("C0_METHOD_INDEPENDENT", c0), ("C1_FAILURE_DIAGNOSTIC", c1)):
            for ordinal, row in enumerate(rows, 1):
                output.append({
                    "environment": environment, "cohort": cohort, "ordinal": str(ordinal),
                    "state_id": row["state_id"], "position_m": row["position_m"],
                    "velocity_m_per_s": row["velocity_m_per_s"], "goal_m": row["goal_m"],
                    "source_type": row["source_type"], "failure_stratum": row.get("failure_stratum", ""),
                })
    write_csv(TASK_ROOT / "diagnostic_design/bounded_state_selection.csv", output)
    write_json(TASK_ROOT / "diagnostic_design/bounded_state_selection.json", summary)
    write_json(TASK_ROOT / "phase_manifests/phase2_design.json", {
        "status": "PASS_BOUNDED_DIAGNOSTIC_SELECTION_FROZEN", "selection_rows": len(output),
        "selection_csv_sha256": sha256_file(TASK_ROOT / "diagnostic_design/bounded_state_selection.csv"),
        "no_new_runtime_result_read_before_selection": True,
    })
    print("PASS_C0_C1_SELECTION", len(output))


if __name__ == "__main__":
    main()
