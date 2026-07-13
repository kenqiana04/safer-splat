#!/usr/bin/env python3
"""Bounded original-SAFER smoke wrapper with non-intervening DT diagnostics."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import numpy as np


RESULT_DIR = Path("work/risk_aware_cbf/results/safer_baseline_cross_dataset_g0_g1")
PAIR_FIELDS = [
    "candidate_id", "dataset_family", "pair_id", "goal_reached", "stop_reason", "steps",
    "progress_ratio", "final_goal_distance", "min_safety_h", "internal_h_collision_count",
    "geometry_grounded_collision_count", "qp_infeasible_count", "H1_margin_violation_count",
    "H2_margin_violation_count", "H3_margin_violation_count", "runtime_mean", "runtime_p95",
    "active_constraints_mean", "active_constraints_p95", "query_runtime_mean", "notes",
]
PARITY_FIELDS = [
    "reference_scene", "trial", "parity_passed", "max_abs_u_nom_delta", "max_abs_u_safe_delta",
    "max_abs_u_exec_delta", "max_abs_state_delta", "max_abs_h_delta", "official_stop_reason",
    "wrapper_stop_reason", "notes",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def percentile(values: list[float], q: float) -> float | None:
    return float(np.percentile(np.asarray(values, dtype=float), q)) if values else None


def parse_xyz(text: str) -> np.ndarray:
    return np.asarray([float(item) for item in text.split(";")], dtype=float)


def nominal_control(torch, state, goal):
    # This is intentionally identical to reproduction/scripts/run_official_runpy_smoke.py.
    vel_des = 5.0 * (goal[:3] - state[:3])
    vel_des = torch.clamp(vel_des, -0.1, 0.1)
    vel_des = vel_des + 1.0 * (goal[3:] - state[3:])
    return torch.clamp(1.0 * (vel_des - state[3:]), -0.1, 0.1)


def hstep_warning(torch, gsplat, dynamics_fn, state, control, radius: float, horizon: int, dt_margin: float) -> bool:
    shadow = state.clone()
    for _ in range(horizon):
        shadow = dynamics_fn(shadow, control) * 0.05 + shadow
        h, _, _, _ = gsplat.query_distance(shadow, radius=radius, distance_type="ball-to-ellipsoid")
        if not bool(torch.isfinite(h).all().item()) or float(torch.min(h).item()) < dt_margin:
            return True
    return False


def run_trajectory(torch, wrapper, gsplat, dynamics, dynamics_fn, start: np.ndarray, goal_xyz: np.ndarray, radius: float, max_steps: int, dt_margin: float) -> tuple[dict[str, object], list[dict[str, float]]]:
    device = gsplat.means.device
    state = torch.tensor(np.r_[start, np.zeros(3)], device=device, dtype=torch.float32)
    goal = torch.tensor(np.r_[goal_xyz, np.zeros(3)], device=device, dtype=torch.float32)
    cbf = wrapper.InstrumentedCBF(gsplat, dynamics, 5.0, 1.0, radius, distance_type="ball-to-ellipsoid")
    rows: list[dict[str, float]] = []
    step_times: list[float] = []
    query_times: list[float] = []
    h_values: list[float] = []
    warnings = {1: 0, 2: 0, 3: 0}
    stop_reason = "max_steps"
    goal_reached = False
    for step in range(max_steps):
        previous = state.clone()
        u_nom = nominal_control(torch, state, goal)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        started = time.perf_counter()
        u_safe = cbf.solve_QP(state, u_nom)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        step_times.append(time.perf_counter() - started)
        if not bool(cbf.solver_success):
            stop_reason = "qp_infeasible"
            break
        if not bool(torch.isfinite(u_safe).all().item()):
            stop_reason = "nonfinite_control"
            break
        state = dynamics_fn(state, u_safe) * 0.05 + state
        if not bool(torch.isfinite(state).all().item()):
            stop_reason = "nonfinite_state"
            break
        query_started = time.perf_counter()
        h, _, _, _ = gsplat.query_distance(state, radius=radius, distance_type="ball-to-ellipsoid")
        query_times.append(time.perf_counter() - query_started)
        if not bool(torch.isfinite(h).all().item()):
            stop_reason = "query_failure"
            break
        min_h = float(torch.min(h).item())
        h_values.append(min_h)
        for horizon in warnings:
            warnings[horizon] += int(hstep_warning(torch, gsplat, dynamics_fn, previous, u_safe, radius, horizon, dt_margin))
        state_np = state.detach().cpu().numpy()
        u_nom_np = u_nom.detach().cpu().numpy()
        u_safe_np = u_safe.detach().cpu().numpy()
        rows.append({
            "x": state_np[0], "y": state_np[1], "z": state_np[2], "vx": state_np[3], "vy": state_np[4], "vz": state_np[5],
            "u_nom_x": u_nom_np[0], "u_nom_y": u_nom_np[1], "u_nom_z": u_nom_np[2],
            "u_safe_x": u_safe_np[0], "u_safe_y": u_safe_np[1], "u_safe_z": u_safe_np[2], "h": min_h,
        })
        if torch.norm(state - previous) < 0.001:
            goal_reached = bool(torch.norm(previous - goal) < 0.001)
            stop_reason = "goal_reached" if goal_reached else "stalled"
            break
    initial_distance = float(np.linalg.norm(start - goal_xyz))
    final_distance = float(torch.norm(state[:3] - goal[:3]).item())
    result = {
        "goal_reached": goal_reached, "stop_reason": stop_reason, "steps": len(rows),
        "progress_ratio": 1.0 - final_distance / initial_distance if initial_distance > 0 else 0.0,
        "final_goal_distance": final_distance, "min_safety_h": min(h_values) if h_values else None,
        "internal_h_collision_count": int(any(value < 0 for value in h_values)),
        "geometry_grounded_collision_count": None, "qp_infeasible_count": int(cbf.qp_infeasible_count),
        "H1_margin_violation_count": warnings[1], "H2_margin_violation_count": warnings[2], "H3_margin_violation_count": warnings[3],
        "runtime_mean": float(np.mean(step_times)) if step_times else None, "runtime_p95": percentile(step_times, 95),
        "active_constraints_mean": float(np.mean(cbf.n_constraints)) if cbf.n_constraints else None,
        "active_constraints_p95": percentile([float(value) for value in cbf.n_constraints], 95),
        "query_runtime_mean": float(np.mean(query_times)) if query_times else None,
    }
    return result, rows


def max_abs_delta(left: list[list[float]], right: list[list[float]]) -> float:
    if len(left) != len(right) or not left:
        return float("inf")
    return float(np.max(np.abs(np.asarray(left, dtype=float) - np.asarray(right, dtype=float))))


def run_reference_parity(repo_root: Path, output_dir: Path, dt_margin: float) -> list[dict[str, object]]:
    import torch
    from dynamics.systems import DoubleIntegrator, double_integrator_dynamics
    wrapper_path = repo_root / "reproduction/scripts/run_official_runpy_smoke.py"
    wrapper = load_module(wrapper_path, "official_runpy_smoke_for_parity")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    cfg = wrapper.SCENES["stonehenge"]
    records: list[dict[str, object]] = []
    for trial in (0, 1, 2):
        record = {"reference_scene": "stonehenge", "trial": trial, "parity_passed": False, "max_abs_u_nom_delta": None, "max_abs_u_safe_delta": None, "max_abs_u_exec_delta": None, "max_abs_state_delta": None, "max_abs_h_delta": None, "official_stop_reason": "", "wrapper_stop_reason": "", "notes": ""}
        try:
            with tempfile.TemporaryDirectory(prefix="safer_cross_dataset_parity_") as temp:
                temp_dir = Path(temp)
                completed = subprocess.run([sys.executable, str(wrapper_path), "--scene", "stonehenge", "--trial", str(trial), "--n-steps", "50", "--output-dir", str(temp_dir)], cwd=repo_root, text=True, capture_output=True, check=False)
                if completed.returncode != 0:
                    raise RuntimeError(completed.stderr[-500:] or completed.stdout[-500:])
                official_rows = read_csv(temp_dir / "official_smoke_trajectory.csv")
                official_summary = read_csv(temp_dir / "official_smoke_summary.csv")[0]
                t = np.linspace(0, 2 * np.pi, 100)
                t_z = 10 * np.linspace(0, 2 * np.pi, 100)
                starts = np.stack([cfg["radius_config"] * np.cos(t), cfg["radius_config"] * np.sin(t), cfg["radius_z"] * np.sin(t_z)], axis=-1) + cfg["mean_config"]
                goals = np.stack([cfg["radius_config"] * np.cos(t + np.pi), cfg["radius_config"] * np.sin(t + np.pi), cfg["radius_z"] * np.sin(t_z + np.pi)], axis=-1) + cfg["mean_config"]
                gsplat = wrapper.GSplatLoader(cfg["path_to_gsplat"], device)
                ours, our_rows = run_trajectory(torch, wrapper, gsplat, DoubleIntegrator(device=device, ndim=3), double_integrator_dynamics, starts[trial], goals[trial], cfg["radius"], 50, dt_margin)
                record["max_abs_u_nom_delta"] = max_abs_delta([[row["u_des_x"], row["u_des_y"], row["u_des_z"]] for row in official_rows], [[row["u_nom_x"], row["u_nom_y"], row["u_nom_z"]] for row in our_rows])
                record["max_abs_u_safe_delta"] = max_abs_delta([[row["ux"], row["uy"], row["uz"]] for row in official_rows], [[row["u_safe_x"], row["u_safe_y"], row["u_safe_z"]] for row in our_rows])
                record["max_abs_u_exec_delta"] = record["max_abs_u_safe_delta"]
                record["max_abs_state_delta"] = max_abs_delta([[row[key] for key in ("x", "y", "z", "vx", "vy", "vz")] for row in official_rows], [[row[key] for key in ("x", "y", "z", "vx", "vy", "vz")] for row in our_rows])
                record["max_abs_h_delta"] = max_abs_delta([[row["safety_h"]] for row in official_rows], [[row["h"]] for row in our_rows])
                record["official_stop_reason"] = official_summary.get("stop_reason", "")
                record["wrapper_stop_reason"] = str(ours["stop_reason"])
                record["parity_passed"] = all(float(record[field]) == 0.0 for field in ("max_abs_u_nom_delta", "max_abs_u_safe_delta", "max_abs_u_exec_delta")) and float(record["max_abs_state_delta"]) <= 1e-6
        except Exception as exc:
            record["notes"] = f"{type(exc).__name__}: {exc}"[:500]
        records.append(record)
    write_csv(output_dir / "reference_parity_summary.csv", PARITY_FIELDS, records)
    return records


def load_scene_adapter(adapter_dir: Path, candidate_id: str) -> dict[str, object]:
    module = load_module(adapter_dir / f"{candidate_id}.py", f"cross_dataset_adapter_{candidate_id}")
    adapter = getattr(module, "SCENE_ADAPTER", None)
    if not isinstance(adapter, dict):
        raise RuntimeError(f"Adapter must export SCENE_ADAPTER: {candidate_id}")
    return adapter


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--preregistration", type=Path, default=RESULT_DIR / "selected_scene_preregistration.csv")
    parser.add_argument("--pairs", type=Path, default=RESULT_DIR / "start_goal_candidate_pairs.csv")
    parser.add_argument("--output-dir", type=Path, default=RESULT_DIR)
    parser.add_argument("--adapter-dir", type=Path, default=Path("work/risk_aware_cbf/scripts/cross_dataset_scene_adapters"))
    parser.add_argument("--pairs-per-scene", type=int, default=3)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--dt-horizons", default="1,2,3")
    parser.add_argument("--dt-margin", type=float, default=0.0005)
    parser.add_argument("--recovery", default="disabled")
    parser.add_argument("--start-repair", default="disabled")
    parser.add_argument("--risk-aware", default="disabled")
    parser.add_argument("--safc", default="disabled")
    parser.add_argument("--mode", default="baseline-smoke")
    parser.add_argument("--run-reference-parity", action="store_true")
    args = parser.parse_args()
    if (args.pairs_per_scene, args.max_steps, args.dt_horizons, args.mode) != (3, 200, "1,2,3", "baseline-smoke"):
        raise ValueError("The G0-G1 smoke contract fixes pairs-per-scene=3, max-steps=200, dt-horizons=1,2,3, and mode=baseline-smoke.")
    if any(value != "disabled" for value in (args.recovery, args.start_repair, args.risk_aware, args.safc)):
        raise ValueError("Recovery, Start-Safe repair, Risk-Aware, and SAFC must remain disabled.")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    parity = run_reference_parity(args.repo_root.resolve(), args.output_dir, args.dt_margin) if args.run_reference_parity else []
    parity_passed = bool(parity) and all(bool(row["parity_passed"]) for row in parity)
    pair_rows: list[dict[str, object]] = []
    scene_rows: list[dict[str, object]] = []
    if parity_passed:
        import torch
        from dynamics.systems import DoubleIntegrator, double_integrator_dynamics
        from splat.gsplat_utils import GSplatLoader
        wrapper = load_module(args.repo_root.resolve() / "reproduction/scripts/run_official_runpy_smoke.py", "official_runpy_smoke_for_g1")
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        prereg_by_id = {row["candidate_id"]: row for row in read_csv(args.preregistration)}
        admitted = [row for row in read_csv(args.pairs) if row.get("initially_admissible", "").lower() == "true"]
        by_scene: dict[str, list[dict[str, str]]] = {}
        for row in admitted:
            candidate_id = row["candidate_id"]
            if prereg_by_id.get(candidate_id, {}).get("tier") == "Tier-R":
                continue
            by_scene.setdefault(candidate_id, []).append(row)
        for candidate_id in sorted(by_scene)[:3]:
            selected_pairs = sorted(by_scene[candidate_id], key=lambda row: int(row["pair_id"]))[:3]
            if len(selected_pairs) < 3:
                scene_rows.append({"candidate_id": candidate_id, "completed_run_count": 0, "notes": "insufficient_admissible_pairs"})
                continue
            scene = prereg_by_id[candidate_id]
            completed = 0
            try:
                adapter = load_scene_adapter(args.adapter_dir, candidate_id)
                gsplat = GSplatLoader(Path(str(adapter["checkpoint_path"])), device)
                dynamics = DoubleIntegrator(device=device, ndim=3)
                # The transfer contract freezes this radius for every independent scene.
                radius = 0.03
                for pair in selected_pairs:
                    try:
                        result, _ = run_trajectory(torch, wrapper, gsplat, dynamics, double_integrator_dynamics, parse_xyz(pair["start_xyz"]), parse_xyz(pair["goal_xyz"]), radius, args.max_steps, args.dt_margin)
                        pair_rows.append({"candidate_id": candidate_id, "dataset_family": scene["dataset_family"], "pair_id": pair["pair_id"], **result, "notes": "Original loader, CBF-QP, nominal controller, and dynamics; H warnings are diagnostic only."})
                        completed += 1
                    except RuntimeError as exc:
                        pair_rows.append({"candidate_id": candidate_id, "dataset_family": scene["dataset_family"], "pair_id": pair["pair_id"], "goal_reached": False, "stop_reason": "resource_failure" if "out of memory" in str(exc).lower() else "exception", "steps": 0, "notes": f"{type(exc).__name__}: {exc}"[:500]})
            except Exception as exc:
                scene_rows.append({"candidate_id": candidate_id, "completed_run_count": completed, "notes": f"{type(exc).__name__}: {exc}"[:500]})
                continue
            scene_rows.append({"candidate_id": candidate_id, "completed_run_count": completed, "notes": ""})
    write_csv(args.output_dir / "pair_smoke_summary.csv", PAIR_FIELDS, pair_rows)
    write_csv(args.output_dir / "scene_smoke_summary.csv", ["candidate_id", "completed_run_count", "notes"], scene_rows)
    (args.output_dir / "smoke_runner_status.json").write_text(json.dumps({"baseline_smoke_run": bool(pair_rows), "reference_parity_run": bool(parity), "reference_parity_passed": parity_passed, "reason": "No cross-dataset run occurred." if not pair_rows else "Completed bounded original-baseline smoke."}, indent=2), encoding="utf-8")
    print(f"reference_parity_run={bool(parity)}")
    print("baseline_smoke_run=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
