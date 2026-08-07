"""Reanalyse frozen PR87/PR89 records without executing a controller."""
from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from scipy.stats import beta

from common import sha256_file, write_csv, write_json
from task_config import FORMAL_ENVIRONMENTS, METHODS, TASK_ROOT, UPSTREAM_ROOT


def boolean(value: str) -> bool:
    return value.strip().lower() == "true"


def exact_upper_zero(n: int, confidence: float) -> float:
    """Exact one-sided binomial upper bound for zero observed events."""
    return float(1.0 - (1.0 - confidence) ** (1.0 / n)) if n else float("nan")


def clopper_upper(k: int, n: int, confidence: float) -> float:
    if not n:
        return float("nan")
    if k == n:
        return 1.0
    return float(beta.ppf(confidence, k + 1, n - k))


def parse_json_cell(cell: str) -> object:
    try:
        return json.loads(cell)
    except (TypeError, ValueError):
        return cell


def main() -> None:
    csv_path = UPSTREAM_ROOT / "benchmark/one_step_records.csv"
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8", newline="")))
    if len(rows) != 1440:
        raise RuntimeError(f"FORMAL_RECORD_COUNT_MISMATCH:{len(rows)}")
    by_environment: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_environment[row["environment"]].append(row)
    if tuple(sorted(by_environment)) != tuple(sorted(FORMAL_ENVIRONMENTS)):
        raise RuntimeError("FORMAL_ENVIRONMENT_SET_MISMATCH")

    formal_funnel = []
    environment_rows = []
    f03 = {"factor_id": "F03", "evidence_class": "E1_REANALYSIS_OF_FROZEN_RECORDS", "environments": {}}
    f08 = {"factor_id": "F08", "evidence_class": "E1_REANALYSIS_OF_FROZEN_RECORDS", "metrics": {}}
    f10_rows = []
    for environment in FORMAL_ENVIRONMENTS:
        env_rows = by_environment[environment]
        states = sorted({row["state_id"] for row in env_rows})
        state_count = len(states)
        per_method = {method: [row for row in env_rows if row["method"] == method] for method in METHODS}
        if any(len(method_rows) != state_count for method_rows in per_method.values()):
            raise RuntimeError(f"NESTED_METHOD_MATRIX_MISMATCH:{environment}")
        first = per_method[METHODS[0]]
        exposure = {
            "environment": environment,
            "state_count": state_count,
            "reference_tiers": dict(Counter(row["reference_tier"] for row in env_rows)),
            "current_h_min": min(float(row["current_h"]) for row in env_rows),
            "current_h_max": max(float(row["current_h"]) for row in env_rows),
            "current_gate_fail_states": sum(row["current_gate"] == "FAIL" for row in first),
            "deadline_miss_records": sum(boolean(row["deadline_miss"]) for row in env_rows),
            "physical_reference_available": environment == "E1_REPLICA_GT_FINE",
            "interpretation_limit": (
                "Reference-complete represented-map behavior only; no on-policy/deployment evidence."
                if environment == "E1_REPLICA_GT_FINE"
                else "Behavior-only source-map evidence; physical reference is NOT_EVALUABLE."
            ),
        }
        environment_rows.append(exposure)
        f03["environments"][environment] = {
            "state_count": state_count,
            "b0_current_pass": sum(row["current_gate"] == "PASS" for row in first),
            "b0_current_fail": sum(row["current_gate"] == "FAIL" for row in first),
            "b1_reached": sum(row["segment_gate"] != "NOT_REACHED_CURRENT_GATE_FAILED" for row in per_method[METHODS[1]]),
            "b2_reached": sum(row["backup_gate"] != "NOT_REACHED_CURRENT_GATE_FAILED" for row in per_method[METHODS[2]]),
            "b3_reached": sum(row["backup_gate"] != "NOT_REACHED_CURRENT_GATE_FAILED" for row in per_method[METHODS[3]]),
            "conclusion": "Current-gate left truncation is structural where B0 fails; it does not establish a candidate rescue."
        }
        for method, method_rows in per_method.items():
            activated = {
                "segment": sum(boolean(row["segment_incremental_activation"]) for row in method_rows),
                "backup": sum(boolean(row["backup_incremental_activation"]) for row in method_rows),
                "directional": sum(boolean(row["directional_incremental_rescue"]) for row in method_rows),
                "any": sum(boolean(row["any_incremental_activation"]) for row in method_rows),
            }
            certified = sum(boolean(row["committed"]) for row in method_rows)
            formal_funnel.append({
                "environment": environment, "method": method, "records": len(method_rows),
                "committed": certified, "current_pass": sum(row["current_gate"] == "PASS" for row in method_rows),
                "segment_pass": sum(row["segment_gate"] == "PASS" for row in method_rows),
                "backup_pass": sum(row["backup_gate"] == "PASS" for row in method_rows),
                "terminal_already_safe": sum(boolean(row["terminal_already_safe"]) for row in method_rows),
                "segment_increment": activated["segment"], "backup_increment": activated["backup"],
                "directional_increment": activated["directional"], "any_increment": activated["any"],
                "typed_status_counts": json.dumps(dict(sorted(Counter(row["typed_status"] for row in method_rows).items())), sort_keys=True),
            })
        b0, b1, b2, b3 = (per_method[method] for method in METHODS)
        f08["metrics"][environment] = {
            "M1_decision_gain_b3_vs_b0": sum(
                boolean(x["committed"]) != boolean(y["committed"])
                for x, y in zip(b0, b3)
            ),
            "M2_certificate_gain_b3_vs_b0": sum(
                (x["typed_status"], x["selected_candidate"]) != (y["typed_status"], y["selected_candidate"])
                for x, y in zip(b0, b3)
            ),
            "M3_availability_gain_directional_slots": sum(
                x["directional_availability"] != y["directional_availability"] for x, y in zip(b0, b3)
            ),
            "M4_leadtime_incremental_segment_or_backup": sum(
                boolean(row["segment_incremental_activation"]) or boolean(row["backup_incremental_activation"])
                for row in b3
            ),
            "M5_backup_margin_observable": sum(row["backup_horizon"] != "" for row in b3),
            "M6_cost_runtime_difference_defined": True,
            "claim_boundary": "M2 certificate gain is not behavioral gain; M3 availability is not a rescue."
        }
        # Population rate calculations explicitly remain environment-specific.
        for rate_percent in (0.1, 0.5, 1, 2, 3, 5):
            p = rate_percent / 100.0
            for required_events in (1, 3, 5):
                required_n = math.ceil(required_events / p)
                f10_rows.append({
                    "environment": environment, "event_rate_percent": rate_percent,
                    "required_events": required_events, "nominal_required_n": required_n,
                    "observed_state_n": state_count,
                    "conditional_sample_definition": (
                        "all representative states" if environment == "E1_REPLICA_GT_FINE"
                        else "states reaching the specified downstream gate; not the nominal 100"
                    ),
                    "cluster_adjustment_status": "DATA_BLOCKED_NO_FROZEN_CLUSTER_OR_ICC_MODEL",
                })
        for metric in ("segment_increment", "backup_increment", "directional_increment", "any_increment"):
            f10_rows.append({
                "environment": environment, "event_rate_percent": "zero_event_upper_bound",
                "required_events": metric, "nominal_required_n": state_count,
                "observed_state_n": state_count,
                "conditional_sample_definition": "one-sided exact upper at 80/95 percent is stored in power_summary",
                "cluster_adjustment_status": "DATA_BLOCKED_NO_FROZEN_CLUSTER_OR_ICC_MODEL",
            })

    power_summary = {"factor_id": "F10", "evidence_class": "E1_REANALYSIS_OF_FROZEN_RECORDS", "environments": {}}
    for environment in FORMAL_ENVIRONMENTS:
        n = len({row["state_id"] for row in by_environment[environment]})
        b3 = [row for row in by_environment[environment] if row["method"] == METHODS[-1]]
        outcomes = {metric: sum(boolean(row[field]) for row in b3) for metric, field in {
            "segment_increment": "segment_incremental_activation", "backup_increment": "backup_incremental_activation",
            "directional_increment": "directional_incremental_rescue", "any_increment": "any_incremental_activation",
        }.items()}
        power_summary["environments"][environment] = {
            "state_n": n,
            "observed": outcomes,
            "zero_event_one_sided_upper_80": exact_upper_zero(n, .80),
            "zero_event_one_sided_upper_95": exact_upper_zero(n, .95),
            "conditional_downstream_n": {
                "B1": sum(row["segment_gate"] != "NOT_REACHED_CURRENT_GATE_FAILED" for row in b3),
                "B2": sum(row["backup_gate"] != "NOT_REACHED_CURRENT_GATE_FAILED" for row in b3),
            },
            "cluster_ess": "DATA_BLOCKED_NO_FROZEN_CLUSTER_OR_ICC_MODEL",
        }

    f11 = {
        "factor_id": "F11", "evidence_class": "E0_FROZEN_FORMAL_EVIDENCE",
        "formal_csv_sha256": sha256_file(csv_path), "row_count": len(rows),
        "environment_method_rows": {env: {method: sum(row["environment"] == env and row["method"] == method for row in rows) for method in METHODS} for env in FORMAL_ENVIRONMENTS},
        "shared_input_hash_mismatches_within_state": 0,
        "frozen_record_parse_errors": 0,
        "replay_required": "Two deterministic replays per formal environment on >=32 states are evaluated separately; any mismatch routes Case G.",
    }
    for environment in FORMAL_ENVIRONMENTS:
        grouped: dict[str, set[str]] = defaultdict(set)
        for row in by_environment[environment]:
            grouped[row["state_id"]].add(row["shared_input_hash"])
        f11["shared_input_hash_mismatches_within_state"] += sum(len(hashes) != 1 for hashes in grouped.values())

    write_csv(TASK_ROOT / "evidence/formal_funnel.csv", formal_funnel)
    write_json(TASK_ROOT / "evidence/f01_environment_exposure.json", {"factor_id": "F01", "evidence_class": "E1_REANALYSIS_OF_FROZEN_RECORDS", "environments": environment_rows})
    write_json(TASK_ROOT / "evidence/f03_gate_funnel.json", f03)
    write_json(TASK_ROOT / "evidence/f08_metric_sensitivity.json", f08)
    write_csv(TASK_ROOT / "evidence/f10_power_grid.csv", f10_rows)
    write_json(TASK_ROOT / "evidence/f10_power_summary.json", power_summary)
    write_json(TASK_ROOT / "evidence/f11_frozen_record_integrity.json", f11)
    write_json(TASK_ROOT / "phase_manifests/phase1.json", {
        "status": "PASS_FROZEN_RECORD_REANALYSIS", "formal_csv_sha256": sha256_file(csv_path),
        "record_count": len(rows), "new_controller_or_map_execution": False,
    })
    print("PASS_FROZEN_REANALYSIS", len(rows))


if __name__ == "__main__":
    main()
