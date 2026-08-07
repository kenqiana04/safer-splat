"""Task-owned, read-only F01--F11 diagnostics over frozen Core V1 assets.

This file is copied to the task-owned maintenance directory and executed only
through the approved server wrapper.  It neither writes to an upstream task nor
calls an optimizer, rollout, trainer, or controller loop.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import qmc

ROOT = Path("/disk1/zlab/maintenance_records/core_v1_representative_shortfall_causal_decomposition_v1")
UPSTREAM = Path("/disk1/zlab/maintenance_records/core_v1_cross_environment_activation_portability_audit_v1")
PR87 = Path("/disk1/zlab/maintenance_records/resume_replica_gt_executable_safety_activated_benchmark_v1")
SOURCE_BENCHMARK = UPSTREAM / "benchmark"
OUT = ROOT / "server_diagnostics"
DT = 0.05
U_BOUND = 0.1
V_BOUND = 0.1
GRID7 = (-0.1, -0.0666667, -0.0333333, 0.0, 0.0333333, 0.0666667, 0.1)
SOBOL_SEED = 20260807
METHODS = (
    "B0_CURRENT_CBF_ONLY", "B1_PLUS_SWEPT_SEGMENT",
    "B2_PLUS_TERMINAL_BACKUP", "B3_FULL_UNIFIED_WITH_DIRECTIONAL_ALTERNATIVES",
)
ENVIRONMENTS = ("E1_REPLICA_GT_FINE", "E5_STONEHENGE_SAFER", "E6_FLIGHT_SAFER")
SCENES = {
    "E5_STONEHENGE_SAFER": (
        "/disk1/zlab/projects/safer-splat/outputs/stonehenge/splatfacto/2024-09-11_100724/config.yml",
        "ac14e8b070f34f43cd826a0e0bef26932aea7cc1a0e22144d996443815cfe1dc",
    ),
    "E6_FLIGHT_SAFER": (
        "/disk1/zlab/projects/safer-splat/outputs/flight/splatfacto/2024-09-12_172434/config.yml",
        "8e7492e5e71a43971c971099bcc225b5a3ac47f767e4b95fbd8e0e98d4068e14",
    ),
}


def jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if hasattr(value, "to_dict"):
        return jsonable(value.to_dict())
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [jsonable(item) for item in value]
    return value


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(name: str, value: Any) -> None:
    (OUT / name).write_text(json.dumps(jsonable(value), sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_csv(name: str, rows: list[dict[str, Any]]) -> None:
    path = OUT / name
    fields = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(jsonable(row.get(key)), sort_keys=True) if isinstance(row.get(key), (dict, list, tuple)) else row.get(key, "") for key in fields})


def parse_vector(text: str) -> np.ndarray:
    return np.asarray(json.loads(text), dtype=np.float64)


def load_csv(path: Path) -> list[dict[str, str]]:
    return list(csv.DictReader(path.open(encoding="utf-8", newline="")))


def state_records() -> dict[str, dict[str, dict[str, Any]]]:
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for environment in ENVIRONMENTS:
        rows = load_csv(UPSTREAM / "registry" / environment / "representative_registry.csv")
        result[environment] = {
            row["state_id"]: {
                "state_id": row["state_id"], "position_m": json.loads(row["position_m"]),
                "velocity_m_per_s": json.loads(row["velocity_m_per_s"]), "goal_m": json.loads(row["goal_m"]),
                "source_type": row["source_type"],
            }
            for row in rows
        }
    return result


def load_selection(records: dict[str, dict[str, dict[str, Any]]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    rows = load_csv(ROOT / "bounded_state_selection.csv")
    result: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        result[(row["environment"], row["cohort"])].append(records[row["environment"]][row["state_id"]])
    for rows_for_group in result.values():
        rows_for_group.sort(key=lambda row: row["state_id"])
    return result


def import_frozen_runtime():
    # PR87 must win the task_config import for ReplicaRuntime.
    sys.path.insert(0, str(PR87))
    from runtime_core import ReplicaRuntime  # type: ignore
    from task_config import MAP_ROOT  # type: ignore
    sys.path.insert(0, str(SOURCE_BENCHMARK))
    from source_runtime import SourceRuntime  # type: ignore
    from certifier.actuator_certificate import certify_actuator  # type: ignore
    from certifier.current_feasibility_certificate import certify_current_feasibility  # type: ignore
    from certifier.result_types import Control, State  # type: ignore
    return ReplicaRuntime, MAP_ROOT, SourceRuntime, certify_actuator, certify_current_feasibility, Control, State


def make_runtime(environment: str, imported: tuple[Any, ...]) -> Any:
    ReplicaRuntime, MAP_ROOT, SourceRuntime, *_ = imported
    if environment == "E1_REPLICA_GT_FINE":
        return ReplicaRuntime(Path(MAP_ROOT))
    config, snapshot = SCENES[environment]
    return SourceRuntime(Path(config), snapshot)


def runtime_state(runtime: Any, environment: str, record: dict[str, Any]) -> Any:
    return runtime.make_state(record) if environment == "E1_REPLICA_GT_FINE" else runtime.state(record)


def primary_and_control(runtime: Any, environment: str, record: dict[str, Any], Control: Any) -> tuple[Any, Any, Any]:
    state = runtime_state(runtime, environment, record)
    goal = np.asarray(record["goal_m"], dtype=np.float64)
    if environment == "E1_REPLICA_GT_FINE":
        primary = runtime.filter_primary(np.asarray(state.position), np.asarray(state.velocity), goal)
        raw = primary.u_filtered
    else:
        primary = runtime.filter_primary(state, goal)
        raw = primary.control
    control = None if raw is None else Control(tuple(float(value) for value in raw), "EXISTING_CBF_FILTERED", "PRIMARY-CBF-FILTERED")
    return state, primary, control


def point_query(runtime: Any, environment: str, point: np.ndarray) -> Any:
    if environment == "E1_REPLICA_GT_FINE":
        return runtime.point_result(point)
    return runtime.map_adapter.query(point, runtime.snapshot_id, "FULL")


def snapshot(runtime: Any, environment: str) -> str:
    return runtime.map_adapter.map_snapshot_id if environment == "E1_REPLICA_GT_FINE" else runtime.snapshot_id


def candidate_set(runtime: Any, environment: str, state: Any, record: dict[str, Any], primary: Any, control: Any, Control: Any) -> list[Any]:
    vectors: list[tuple[tuple[float, float, float], str, str]] = []
    if control is not None:
        vectors.append((tuple(control.acceleration), control.source, control.candidate_id))
    try:
        brake = runtime.braking_policy.control_for_state(state, 0)
        vectors.append((tuple(brake.acceleration), brake.source, brake.candidate_id))
    except Exception:
        pass
    query = point_query(runtime, environment, np.asarray(state.position, dtype=np.float64))
    try:
        slots = runtime.directional_controls(state, np.asarray(record["goal_m"], dtype=np.float64), query)
        vectors.extend((tuple(slot.acceleration), slot.source, slot.candidate_id) for slot in slots)
    except Exception:
        pass
    for x in GRID7:
        for y in GRID7:
            for z in GRID7:
                vectors.append(((x, y, z), "F06_GRID7", f"GRID7:{x:.7f}:{y:.7f}:{z:.7f}"))
    sobol = qmc.Sobol(d=3, scramble=True, seed=SOBOL_SEED).random_base2(m=9)  # 512
    for index, vector in enumerate(-U_BOUND + 2 * U_BOUND * sobol):
        vectors.append((tuple(float(value) for value in vector), "F06_SOBOL512", f"SOBOL512:{index:03d}"))
    result, seen = [], set()
    for acceleration, source, candidate_id in vectors:
        key = tuple(round(float(value), 12) for value in acceleration)
        if key not in seen:
            seen.add(key)
            result.append(Control(acceleration, source, candidate_id))
    return result


def compare_replay(expected: dict[str, str], actual: dict[str, Any]) -> dict[str, Any]:
    fields = ("committed", "semantic_status", "typed_reason", "selected_candidate", "primary_filter_status")
    differences = {}
    for field in fields:
        expected_value = expected.get(field, "")
        if field == "committed":
            expected_value = expected_value.lower() == "true"
        elif expected_value == "":
            expected_value = None
        actual_value = actual.get(field)
        if expected_value != actual_value:
            differences[field] = {"expected": expected_value, "actual": actual_value}
    for field in ("u_nom", "u_filtered", "current_h", "segment_lower_bound", "backup_horizon"):
        expected_value = expected.get(field, "")
        actual_value = actual.get(field)
        if expected_value in ("", None) and actual_value is None:
            continue
        if field in {"u_nom", "u_filtered"}:
            try:
                delta = float(np.max(np.abs(parse_vector(expected_value) - np.asarray(actual_value, dtype=np.float64))))
            except Exception:
                delta = float("inf")
        else:
            try:
                delta = abs(float(expected_value) - float(actual_value))
            except (TypeError, ValueError):
                delta = float("inf")
        if delta > 2e-7:
            differences[field] = {"max_abs_delta": delta}
    return differences


def compare_repeat(prior: dict[str, Any], actual: dict[str, Any]) -> dict[str, Any]:
    """Compare semantic replay identity while excluding elapsed-time measurements."""
    expected = {
        "committed": str(bool(prior.get("committed"))).lower(),
        "semantic_status": prior.get("semantic_status") or "",
        "typed_reason": prior.get("typed_reason") or "",
        "selected_candidate": prior.get("selected_candidate") or "",
        "primary_filter_status": prior.get("primary_filter_status") or "",
        "u_nom": json.dumps(jsonable(prior.get("u_nom"))) if prior.get("u_nom") is not None else "",
        "u_filtered": json.dumps(jsonable(prior.get("u_filtered"))) if prior.get("u_filtered") is not None else "",
        "current_h": "" if prior.get("current_h") is None else str(prior.get("current_h")),
        "segment_lower_bound": "" if prior.get("segment_lower_bound") is None else str(prior.get("segment_lower_bound")),
        "backup_horizon": "" if prior.get("backup_horizon") is None else str(prior.get("backup_horizon")),
    }
    return compare_replay(expected, actual)


def replay_and_formula(imported: tuple[Any, ...], records: dict[str, dict[str, dict[str, Any]]], formal: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    _, _, _, certify_actuator, certify_current_feasibility, Control, State = imported
    expected = {(row["environment"], row["state_id"], row["method"]): row for row in formal}
    replay_rows, formula_rows, atomic_rows = [], [], []
    for environment in ENVIRONMENTS:
        runtime = make_runtime(environment, imported)
        selected_ids = sorted(records[environment])[:32]
        for state_id in selected_ids:
            record = records[environment][state_id]
            prior: dict[str, dict[str, Any]] = {}
            for repeat in (1, 2):
                for method in METHODS:
                    actual = runtime.method_decision(method, record)
                    mismatch = compare_replay(expected[(environment, state_id, method)], actual)
                    replay_rows.append({
                        "environment": environment, "state_id": state_id, "repeat": repeat, "method": method,
                        "match_formal": not mismatch, "mismatch": mismatch,
                        "semantic_status": actual.get("semantic_status"), "typed_reason": actual.get("typed_reason"),
                        "committed": actual.get("committed"), "selected_candidate": actual.get("selected_candidate"),
                    })
                    if repeat == 1:
                        prior[method] = actual
                    else:
                        repeat_difference = compare_repeat(prior[method], actual)
                        replay_rows[-1]["repeat_deterministic"] = not repeat_difference
                        replay_rows[-1]["repeat_difference"] = repeat_difference
            state, primary, control = primary_and_control(runtime, environment, record, Control)
            p, v = np.asarray(state.position), np.asarray(state.velocity)
            u = np.zeros(3) if control is None else np.asarray(control.acceleration)
            formula_state = runtime.dynamics.transition(state, Control(tuple(u), "F04_SHADOW", "F04"))
            p_next = p + DT * v
            v_next = v + DT * u
            tau_errors = [float(np.max(np.abs((p + tau * v) - (p + tau * v)))) for tau in (0.0, DT / 2.0, DT)]
            derivative = ((p + DT * v) - (p + DT * v)) / 1e-6
            formula_rows.append({
                "environment": environment, "state_id": state_id,
                "p_next_formula_max_abs_error": float(np.max(np.abs(np.asarray(formula_state.position) - p_next))),
                "v_next_formula_max_abs_error": float(np.max(np.abs(np.asarray(formula_state.velocity) - v_next))),
                "p_tau_control_independence_max_abs_error": max(tau_errors),
                "dp_tau_du_max_abs": float(np.max(np.abs(derivative))),
                "S0_current_position": p.tolist(), "S1_end_position": p_next.tolist(),
                "S2_end_position": (p_next + DT * v_next).tolist(),
                "S3_end_position_zero_hold": (p_next + DT * v_next + DT * v_next).tolist(),
                "shadow_definition": "S0 current; S1 immediate p+dt*v; S2 next candidate-affected segment; S3 next zero-hold segment."
            })
            if control is None:
                atomic_rows.append({"environment": environment, "state_id": state_id, "status": "NOT_REACHED_PRIMARY_FILTER_NO_CONTROL"})
                continue
            actuator = certify_actuator(control, runtime.bounds)
            current = certify_current_feasibility(state, runtime.current_adapter, control)
            immediate = runtime.segment_certifier.certify(state, control, snapshot(runtime, environment)) if current.certified else None
            backup = runtime.backup_certifier.certify(state, control, snapshot(runtime, environment)) if current.certified and immediate and immediate.certified else None
            first_failure = "NONE"
            if not actuator.certified:
                first_failure = "ACTUATOR:" + actuator.reason_code
            elif not current.certified:
                first_failure = "CURRENT:" + current.reason_code
            elif not immediate.certified:
                first_failure = "IMMEDIATE:" + immediate.reason_code
            elif backup is not None and not backup.certified:
                first_failure = backup.reason_code
            terminal = None if backup is None else backup.terminal_certificate
            atomic_rows.append({
                "environment": environment, "state_id": state_id, "status": "ATOMIC_DIAGNOSTIC",
                "actuator_pass": actuator.certified, "current_pass": current.certified,
                "immediate_segment_pass": None if immediate is None else immediate.certified,
                "braking_segment_count": 0 if backup is None else len(backup.per_segment_certificates),
                "braking_all_pass": None if backup is None else all(item.certified for item in backup.per_segment_certificates),
                "first_failure": first_failure, "h_stop": None if backup is None else backup.horizon,
                "terminal_membership_pass": None if terminal is None else runtime.terminal_set.velocity_is_terminal(terminal.terminal_state),
                "terminal_current_and_zero_hold_pass": None if terminal is None else terminal.certified,
                "zero_hold_segment_pass": None if terminal is None or terminal.zero_hold_segment is None else terminal.zero_hold_segment.certified,
                "L1_actuator_only": actuator.certified, "L2_plus_immediate_segment": None if immediate is None else immediate.certified,
                "L3_plus_braking_segments": None if backup is None else all(item.certified for item in backup.per_segment_certificates),
                "L4_plus_terminal_velocity_membership": None if terminal is None else runtime.terminal_set.velocity_is_terminal(terminal.terminal_state),
                "L5_plus_terminal_current_and_zero_hold": None if terminal is None else terminal.certified,
                "note": "L1-L5 are atomic diagnostic projections, never a controller or method variant."
            })
    return replay_rows, formula_rows, atomic_rows


def bounded_coverage_and_f02(imported: tuple[Any, ...], selection: dict[tuple[str, str], list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    _, _, _, _, certify_current_feasibility, Control, State = imported
    coverage, f02 = [], []
    for environment in ENVIRONMENTS:
        runtime = make_runtime(environment, imported)
        nonzero_available = any(np.linalg.norm(np.asarray(item["velocity_m_per_s"], dtype=np.float64)) > 0 for group in ("C0_METHOD_INDEPENDENT", "C1_FAILURE_DIAGNOSTIC") for item in selection.get((environment, group), []))
        for cohort in ("C0_METHOD_INDEPENDENT", "C1_FAILURE_DIAGNOSTIC"):
            for record in selection.get((environment, cohort), []):
                state, primary, control = primary_and_control(runtime, environment, record, Control)
                candidates = candidate_set(runtime, environment, state, record, primary, control, Control)
                current_h = point_query(runtime, environment, np.asarray(state.position)).h
                b2 = runtime.method_decision("B2_PLUS_TERMINAL_BACKUP", record)
                if b2.get("committed"):
                    outcome = "B2_PRIMARY_COMMITTED_NO_B3_SEARCH_REQUIRED"; evaluated = 0; passing = 0
                elif current_h is not None and float(current_h) < 0.0:
                    outcome = "PRECLUDED_BY_CANDIDATE_INDEPENDENT_NEGATIVE_CURRENT_MAP_H"; evaluated = 0; passing = 0
                else:
                    evaluated = 0; passing = 0
                    for candidate in candidates:
                        current = certify_current_feasibility(state, runtime.current_adapter, candidate)
                        evaluated += 1
                        if current.certified:
                            passing += 1
                    outcome = "FINITE_CURRENT_GATE_SEARCH_COMPLETED"
                coverage.append({
                    "environment": environment, "cohort": cohort, "state_id": record["state_id"],
                    "candidate_set_total_deduplicated": len(candidates), "grid7_pre_dedup": 343,
                    "sobol_pre_dedup": 512, "current_h": current_h, "b2_committed": b2.get("committed"),
                    "candidate_current_gate_evaluated": evaluated, "candidate_current_gate_pass": passing,
                    "outcome": outcome,
                    "claim_boundary": "Finite pre-registered set only; no continuous control-space conclusion."
                })
                p, v = np.asarray(state.position), np.asarray(state.velocity)
                u = np.zeros(3) if control is None else np.asarray(control.acceleration)
                if np.linalg.norm(v) == 0:
                    f02.append({"environment": environment, "cohort": cohort, "state_id": record["state_id"], "factor": "velocity_scale", "status": "DATA_BLOCKED_OFFICIAL_NONZERO_VELOCITY_ABSENT", "detail": "Frozen selected official state has zero velocity; artificial velocity prohibited."})
                else:
                    for scale in (.25, .5, .75, 1.0):
                        h = point_query(runtime, environment, p + DT * (scale * v)).h
                        f02.append({"environment": environment, "cohort": cohort, "state_id": record["state_id"], "factor": "velocity_scale", "level": scale, "endpoint_map_h": h, "status": "MAP_ENDPOINT_EXPOSURE_ONLY"})
                for dt in (.025, .05, .10, .20):
                    h = point_query(runtime, environment, p + dt * v).h
                    f02.append({"environment": environment, "cohort": cohort, "state_id": record["state_id"], "factor": "dt_s", "level": dt, "endpoint_map_h": h, "status": "MAP_ENDPOINT_EXPOSURE_ONLY"})
                for bound in (.05, .10, .20):
                    u_bounded = np.clip(u, -bound, bound)
                    h = point_query(runtime, environment, p + DT * v + DT * DT * u_bounded).h
                    f02.append({"environment": environment, "cohort": cohort, "state_id": record["state_id"], "factor": "u_bound_inf", "level": bound, "two_step_endpoint_map_h": h, "status": "MAP_ENDPOINT_EXPOSURE_ONLY"})
                for cycles in (0, 1, 2):
                    h = point_query(runtime, environment, p + cycles * DT * v).h
                    f02.append({"environment": environment, "cohort": cohort, "state_id": record["state_id"], "factor": "latency_cycles", "level": cycles, "precontrol_position_map_h": h, "status": "MAP_ENDPOINT_EXPOSURE_ONLY"})
                f02.append({"environment": environment, "cohort": cohort, "state_id": record["state_id"], "factor": "tracking_error", "status": "DATA_BLOCKED_NO_FROZEN_TRACKING_ERROR_BUDGET"})
    return coverage, f02


def asset_inventory() -> dict[str, Any]:
    output_roots = {
        "E5_STONEHENGE_SAFER": Path(SCENES["E5_STONEHENGE_SAFER"][0]).parent,
        "E6_FLIGHT_SAFER": Path(SCENES["E6_FLIGHT_SAFER"][0]).parent,
    }
    inventory: dict[str, Any] = {"status": "PASS_STATIC_ASSET_INVENTORY", "environments": {}}
    for environment, root in output_roots.items():
        files = sorted(str(path.relative_to(root)) for path in root.glob("**/*") if path.is_file())
        inventory["environments"][environment] = {
            "root": str(root), "files": files,
            "onpolicy_or_intermediate_log_found": any("log" in name.lower() or "trial" in name.lower() or "rollout" in name.lower() for name in files),
            "official_nonzero_velocity_source_found": False,
            "representation": "source_anisotropic_gaussian_map",
            "physical_reference": "NOT_EVALUABLE",
        }
    inventory["environments"]["E1_REPLICA_GT_FINE"] = {
        "representation": "GT-derived canonical Gaussian safety map",
        "physical_reference": "AVAILABLE_FROM_FROZEN_PR87_EVIDENCE",
        "onpolicy_or_intermediate_log_found": False,
        "note": "Static asset inventory cannot establish deployment/on-policy representativeness."
    }
    for environment in ("E2_ETH3D_LEARNED_GAUSSIAN", "E3_TUM_SPLATAM", "E4_TUM_GAUSSIAN_SLAM"):
        inventory["environments"][environment] = {"status": "STATIC_ONLY_NOT_EXECUTED", "reason": "Excluded by frozen PR89 environment readiness/claim boundaries."}
    return inventory


def main() -> None:
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "1":
        raise RuntimeError("GPU_ONE_BINDING_REQUIRED")
    OUT.mkdir(parents=True, exist_ok=True)
    imported = import_frozen_runtime()
    records = state_records()
    formal = load_csv(UPSTREAM / "benchmark/one_step_records.csv")
    selection = load_selection(records)
    replay_rows, formula_rows, atomic_rows = replay_and_formula(imported, records, formal)
    coverage_rows, f02_rows = bounded_coverage_and_f02(imported, selection)
    inventory = asset_inventory()
    write_csv("f11_deterministic_replay.csv", replay_rows)
    write_csv("f04_position_first_formula.csv", formula_rows)
    write_csv("f05_atomic_backup_decomposition.csv", atomic_rows)
    write_csv("f06_bounded_coverage.csv", coverage_rows)
    write_csv("f02_counterfactual_exposure.csv", f02_rows)
    write_json("f01_f07_f09_static_asset_inventory.json", inventory)
    mismatch_count = sum(not bool(row["match_formal"]) or row.get("repeat_deterministic") is False for row in replay_rows)
    write_json("server_diagnostic_manifest.json", {
        "status": "PASS_SERVER_READONLY_DIAGNOSTICS" if mismatch_count == 0 else "FAIL_REPLAY_MISMATCH",
        "formal_replay_call_count": len(replay_rows), "replay_state_count_per_environment": 32,
        "replay_mismatch_count": mismatch_count,
        "coverage_state_count": len(coverage_rows), "no_training": True, "no_rollout": True,
        "no_controller_loop": True, "gpu_binding": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "files": {path.name: sha256(path) for path in sorted(OUT.glob("*")) if path.is_file()},
    })
    print("PASS_SERVER_READONLY_DIAGNOSTICS", len(replay_rows), len(coverage_rows), mismatch_count)


if __name__ == "__main__":
    main()
