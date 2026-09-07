#!/usr/bin/env python3
"""Source-locked Stonehenge control/plant slice for REFERENCE and BYPASS QA."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import struct
import subprocess
import sys
from typing import Any

import numpy as np
import torch


ARMS = {"REFERENCE_CONTROL_PLANT", "ACTIVE_HARNESS_BYPASS"}
TRIAL_IDS = {10, 30, 50, 70, 90}
N = 100
N_STEPS = 500
DT = 0.05
ALPHA = 5.0
BETA = 1.0
RADIUS = 0.015
DISTANCE_METHOD = "ball-to-ellipsoid"
MAP_RELATIVE = Path("outputs/stonehenge/splatfacto/2024-09-11_100724")
MAP_FILES = (
    "config.yml",
    "dataparser_transforms.json",
    "nerfstudio_models/step-000029999.ckpt",
)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(normalize(value), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(normalize(row), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")


def normalize(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return normalize(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(key): normalize(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [normalize(item) for item in value]
    if hasattr(value, "value") and isinstance(value.value, str):
        return value.value
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def semantic_sha256(value: Any) -> str:
    payload = json.dumps(normalize(value), sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def values(tensor: torch.Tensor) -> list[float]:
    return [float(item) for item in tensor.detach().to(torch.float32).cpu().tolist()]


def bits_f32(items: list[float] | tuple[float, ...]) -> list[str]:
    return [struct.pack(">f", float(item)).hex() for item in items]


def trial_geometry(trial_id: int) -> tuple[np.ndarray, np.ndarray]:
    t = np.linspace(0, 2 * np.pi, N)
    t_z = 10 * np.linspace(0, 2 * np.pi, N)
    radius_z = 0.01
    radius_config = 0.784 / 2
    mean_config = np.array([-0.08, -0.03, 0.05])
    x0 = np.stack([radius_config * np.cos(t), radius_config * np.sin(t), radius_z * np.sin(t_z)], axis=-1) + mean_config
    xf = np.stack([radius_config * np.cos(t + np.pi), radius_config * np.sin(t + np.pi), radius_z * np.sin(t_z + np.pi)], axis=-1) + mean_config
    return x0[trial_id], xf[trial_id]


def map_identity(checkout: Path) -> tuple[str, list[dict[str, Any]]]:
    root = (checkout / MAP_RELATIVE).resolve(strict=True)
    records = []
    for relative in MAP_FILES:
        path = root / relative
        records.append({"relative_path": relative, "size": path.stat().st_size, "sha256": sha256_file(path)})
    return semantic_sha256({"scene": "stonehenge", "artifacts": records}), records


def git_head(checkout: Path) -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=checkout, check=True, text=True, capture_output=True).stdout.strip()


def run_trial(arm: str, trial_id: int, checkout: Path, output_dir: Path, seed: int = 0) -> dict[str, Any]:
    if arm not in ARMS:
        raise ValueError("ARM_NOT_FROZEN")
    if trial_id not in TRIAL_IDS:
        raise ValueError("TRIAL_ID_NOT_FROZEN")
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "1":
        raise RuntimeError("CUDA_VISIBLE_DEVICES_MUST_EQUAL_1")
    if output_dir.exists():
        raise FileExistsError(output_dir)
    output_dir.mkdir(parents=True)
    checkout = checkout.resolve(strict=True)
    sys.path.insert(0, str(checkout))

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    device = torch.device("cuda:0")
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
        raise RuntimeError("FROZEN_SINGLE_VISIBLE_GPU_REQUIRED")

    from cbf.cbf_utils import CBF
    from dynamics.systems import DoubleIntegrator, double_integrator_dynamics
    from splat.gsplat_utils import GSplatLoader

    map_id, map_records = map_identity(checkout)
    config = (checkout / MAP_RELATIVE / "config.yml").resolve(strict=True)
    loader = GSplatLoader(config, device)
    dynamics = DoubleIntegrator(device=device, ndim=3)
    cbf = CBF(loader, dynamics, ALPHA, BETA, RADIUS, distance_type=DISTANCE_METHOD)
    start, goal_position = trial_geometry(trial_id)
    x = torch.cat((torch.tensor(start, device=device, dtype=torch.float32), torch.zeros(3, device=device, dtype=torch.float32)))
    goal = torch.cat((torch.tensor(goal_position, device=device, dtype=torch.float32), torch.zeros(3, device=device, dtype=torch.float32)))

    runner = writer = token_store = plant = None
    if arm == "ACTIVE_HARNESS_BYPASS":
        from reproduction.runtime.active_runtime_assurance_v2.active_runner import ActiveRunner
        from reproduction.runtime.active_runtime_assurance_v2.authority_registry import AuthorityRegistry
        from reproduction.runtime.active_runtime_assurance_v2.backup_token_store import BackupTokenStore
        from reproduction.runtime.active_runtime_assurance_v2.plant_commit import PlantCommitAdapter
        from reproduction.runtime.active_runtime_assurance_v2.runtime_types import RuntimeMode
        from reproduction.runtime.active_runtime_assurance_v2.supervisor import Supervisor
        from reproduction.runtime.active_runtime_assurance_v2.trace_writer import TraceWriter

        registry = AuthorityRegistry.frozen(map_id, "RUN_PY_DT_0P05")
        supervisor = Supervisor(registry)
        token_store = BackupTokenStore()
        writer = TraceWriter(f"stonehenge-trial-{trial_id}")

        def gpu_transition(state_tuple, control_tuple, dt_value):
            state_tensor = torch.tensor(state_tuple, device=device, dtype=torch.float32)
            control_tensor = torch.tensor(control_tuple, device=device, dtype=torch.float32)
            post = double_integrator_dynamics(state_tensor, control_tensor) * float(dt_value) + state_tensor
            return tuple(float(item) for item in post.tolist())

        plant = PlantCommitAdapter(registry, gpu_transition)
        runner = ActiveRunner(RuntimeMode.ACTIVE_HARNESS_BYPASS, registry, supervisor, plant, token_store, writer)
        runner.startup()

    rows: list[dict[str, Any]] = []
    termination_reason = "UNRESOLVED"
    solver_failure_step = None
    intervention_counters = {"l0": 0, "l1": 0, "c0": 0, "l2": 0, "l3": 0, "alternative": 0, "backup": 0, "terminal": 0, "deadline": 0}
    initial_state = values(x)
    goal_values = values(goal)

    for cycle in range(N_STEPS):
        pre = x.clone()
        vel_des = 5.0 * (goal[:3] - x[:3])
        vel_des = torch.clamp(vel_des, -0.1, 0.1)
        vel_des = vel_des + 1.0 * (goal[3:] - x[3:])
        u_des = 1.0 * (vel_des - x[3:])
        u_des = torch.clamp(u_des, -0.1, 0.1)
        torch.cuda.synchronize()
        u = cbf.solve_QP(x, u_des)
        torch.cuda.synchronize()
        solver_success = bool(cbf.solver_success)
        row: dict[str, Any] = {
            "trial_id": trial_id,
            "cycle_index": cycle,
            "committed": False,
            "pre_state": values(pre),
            "pre_state_bits": bits_f32(values(pre)),
            "goal": goal_values,
            "goal_bits": bits_f32(goal_values),
            "u_des": values(u_des),
            "u_des_bits": bits_f32(values(u_des)),
            "solver_success": solver_success,
            "reference_action": values(u),
            "reference_action_bits": bits_f32(values(u)),
            "native_termination_reason": null_if_none(None),
        }
        if not solver_success:
            solver_failure_step = cycle
            termination_reason = "SOLVER_FAILURE"
            row["native_termination_reason"] = termination_reason
            rows.append(row)
            break

        if arm == "REFERENCE_CONTROL_PLANT":
            x = double_integrator_dynamics(x, u) * DT + x
            row.update({
                "supplied_action": values(u),
                "supplied_action_bits": bits_f32(values(u)),
                "selected_action": values(u),
                "selected_action_bits": bits_f32(values(u)),
                "executed_action": values(u),
                "executed_action_bits": bits_f32(values(u)),
                "supplied_action_id": None,
                "selected_action_id": None,
                "executed_action_id": None,
                "action_role": "REFERENCE_NAVIGATION",
                "bypass_supervisor_reason": None,
                "decision_allows_commit": True,
                "commit_status": "REFERENCE_COMMITTED",
                "commit_reason": "REFERENCE_COMMITTED",
                "trace_step_identity": None,
                "token_mutation_count": 0,
                "active_intervention_counters": intervention_counters,
            })
        else:
            from reproduction.runtime.active_runtime_assurance_v2.runtime_types import ActionRole, RuntimeStateSnapshot, canonical_sha256, make_action

            snapshot = RuntimeStateSnapshot.create(f"stonehenge-{trial_id}", cycle, values(pre), goal_values, map_id, DT)
            action = make_action(values(u), ActionRole.PRIMARY_NAVIGATION, f"reference-cbf-qp:{trial_id}:{cycle}")
            token_before = token_store.current()
            receipt = runner.commit_bypass(snapshot, action)
            token_after = token_store.current()
            if not receipt.committed or receipt.post_state is None:
                termination_reason = "BYPASS_COMMIT_REJECTED"
                row["native_termination_reason"] = termination_reason
                row.update({
                    "supplied_action": values(u), "supplied_action_bits": bits_f32(values(u)),
                    "supplied_action_id": action.identity.value, "decision_allows_commit": False,
                    "commit_status": "REJECTED", "commit_reason": receipt.reason,
                    "token_mutation_count": int(token_before != token_after),
                    "active_intervention_counters": intervention_counters,
                })
                rows.append(row)
                break
            x = torch.tensor(receipt.post_state.state, device=device, dtype=torch.float32)
            trace_record = writer._records[-1]
            row.update({
                "supplied_action": values(u),
                "supplied_action_bits": bits_f32(values(u)),
                "selected_action": list(receipt.exact_vector),
                "selected_action_bits": bits_f32(receipt.exact_vector),
                "executed_action": list(receipt.exact_vector),
                "executed_action_bits": bits_f32(receipt.exact_vector),
                "supplied_action_id": action.identity.value,
                "selected_action_id": receipt.selected_action_identity.value,
                "executed_action_id": receipt.executed_action_identity.value,
                "action_role": receipt.action_role.value,
                "bypass_supervisor_reason": "BYPASS_REFERENCE_ACTION_UNCHANGED",
                "decision_allows_commit": True,
                "commit_status": "COMMITTED",
                "commit_reason": receipt.reason,
                "trace_step_identity": canonical_sha256(trace_record),
                "token_mutation_count": int(token_before != token_after),
                "active_intervention_counters": intervention_counters,
            })

        row["committed"] = True
        row["post_state"] = values(x)
        row["post_state_bits"] = bits_f32(values(x))
        if torch.norm(x - pre) < 0.001:
            termination_reason = "REACHED_GOAL" if torch.norm(pre - goal) < 0.001 else "NOT_MOVING"
            row["native_termination_reason"] = termination_reason
            rows.append(row)
            break
        if cycle >= N_STEPS - 1:
            termination_reason = "MAX_STEPS_MOVING"
            row["native_termination_reason"] = termination_reason
        rows.append(row)

    trace_lock = None
    if arm == "ACTIVE_HARNESS_BYPASS":
        trace_lock = normalize(runner.finalize_trace())
        write_json(output_dir / f"trial_{trial_id}_trace_lock.json", trace_lock)

    write_jsonl(output_dir / f"trial_{trial_id}.jsonl", rows)
    summary = {
        "schema": "BYPASS_QA_TRIAL_SUMMARY_V2",
        "arm": arm,
        "trial_id": trial_id,
        "initial_state": initial_state,
        "initial_state_bits": bits_f32(initial_state),
        "goal": goal_values,
        "goal_bits": bits_f32(goal_values),
        "attempted_step_count": len(rows),
        "committed_step_count": sum(bool(row["committed"]) for row in rows),
        "solver_failure_step": solver_failure_step,
        "termination_reason": termination_reason,
        "termination_step": rows[-1]["cycle_index"] if rows else None,
        "final_state": values(x),
        "final_state_bits": bits_f32(values(x)),
        "plant_commit_count": sum(bool(row["committed"]) for row in rows) if plant is None else plant.commit_count,
        "active_intervention_call_count": sum(intervention_counters.values()),
        "token_mutation_count": sum(int(row.get("token_mutation_count", 0)) for row in rows),
        "trace_lock": trace_lock,
    }
    write_json(output_dir / f"trial_{trial_id}_summary.json", summary)
    environment = {
        "schema": "BYPASS_QA_ARM_ENVIRONMENT_V2",
        "arm": arm,
        "trial_id": trial_id,
        "repo_head": git_head(checkout),
        "python": platform.python_version(),
        "executable": sys.executable,
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "numpy": np.__version__,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "visible_device_count": torch.cuda.device_count(),
        "device_name": torch.cuda.get_device_name(0),
        "dtype": "torch.float32",
        "dt": DT,
        "alpha": ALPHA,
        "beta": BETA,
        "radius": RADIUS,
        "distance_method": DISTANCE_METHOD,
        "n_steps": N_STEPS,
        "seed": seed,
        "map_identity": map_id,
        "map_artifacts": map_records,
    }
    environment["pairing_identity"] = semantic_sha256({key: value for key, value in environment.items() if key not in {"arm", "trial_id"}})
    write_json(output_dir / "environment_identity.json", environment)
    print(json.dumps({"status": "TRIAL_COMPLETE", "arm": arm, "trial_id": trial_id, "committed_steps": summary["committed_step_count"], "termination": termination_reason}, sort_keys=True), flush=True)
    return summary


def null_if_none(value):
    return value


def cli(expected_arm: str) -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--trial-id", required=True, type=int)
    parser.add_argument("--checkout", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()
    run_trial(expected_arm, args.trial_id, args.checkout, args.output_dir, args.seed)
    return 0
