#!/usr/bin/env python3
"""Run or aggregate frozen actual-SAFER static G0 queries."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import types

import numpy as np
import torch


OFFICIAL_FOUR_SCENE_SLOWEST_S = 22.893853902816772


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_dummy(source: Path):
    sys.path.insert(0, str(source))
    parent = types.ModuleType("ns_utils"); child = types.ModuleType("ns_utils.nerfstudio_utils")
    child.GaussianSplat = object; child.SH2RGB = lambda value: value
    sys.modules.setdefault("ns_utils", parent); sys.modules.setdefault("ns_utils.nerfstudio_utils", child)
    from splat.gsplat_utils import DummyGSplatLoader
    return DummyGSplatLoader


def execute(args) -> None:
    Dummy = import_dummy(args.safer_source)
    means = np.load(args.map_dir / "means_world_m.npy").astype(np.float32)
    scales = np.load(args.map_dir / "scales_linear_m.npy").astype(np.float32)
    quats = np.load(args.map_dir / "quaternions_wxyz.npy").astype(np.float32)
    registry = np.load(args.registry); points = registry["points_m"].astype(np.float32)
    before = {name: sha(args.map_dir / f"{name}.npy") for name in ("means_world_m", "scales_linear_m", "quaternions_wxyz", "opacities_probability", "colors_rgb")}
    loader = Dummy(torch.device("cuda:0")); loader.initialize_attributes(torch.from_numpy(means), torch.from_numpy(quats), torch.from_numpy(scales))
    torch.cuda.reset_peak_memory_stats(); rows = []; started = time.perf_counter()
    for index, point in enumerate(points):
        h, grad, hess, _ = loader.query_distance(torch.as_tensor(point, device="cuda:0"), distance_type="ball-to-ellipsoid", radius=0.10, epsilon=0.01)
        active = int(torch.argmin(h).item())
        rows.append({"index": index, "h": float(h[active].item()), "grad": grad[active].detach().cpu().tolist(), "hessian": hess[active].detach().cpu().tolist(), "active_index": active})
    torch.cuda.synchronize(); elapsed = time.perf_counter() - started; peak = int(torch.cuda.max_memory_allocated())
    after = {name: sha(args.map_dir / f"{name}.npy") for name in before}
    h_values = np.array([row["h"] for row in rows]); gradients = np.array([row["grad"] for row in rows]); hessians = np.array([row["hessian"] for row in rows]); active = np.array([row["active_index"] for row in rows], dtype=np.int64)
    symmetry = float(np.max(np.abs(hessians - np.swapaxes(hessians, 1, 2)) / np.maximum(1.0, np.abs(hessians))))
    gates = {"query_count_256": len(rows) == 256, "h_finite": bool(np.isfinite(h_values).all()), "gradient_finite": bool(np.isfinite(gradients).all()),
             "hessian_finite": bool(np.isfinite(hessians).all()), "hessian_symmetric": symmetry <= 1e-5, "map_unmodified": before == after, "peak_gpu_under_20gib": peak <= 20 * 1024**3}
    result = {"status": "PASS_FRESH_STATIC_G0_RUN" if all(gates.values()) else "FAIL_FRESH_STATIC_G0_RUN", "pass": all(gates.values()), "run_id": args.run_id,
              "gates": gates, "radius_m": .10, "epsilon_base_m": .01, "distance_type": "ball-to-ellipsoid", "query_count": len(rows), "runtime_s": elapsed,
              "peak_gpu_bytes": peak, "hessian_symmetry_relative_max": symmetry, "active_index_sha256": hashlib.sha256(active.tobytes()).hexdigest(),
              "h_sha256": hashlib.sha256(h_values.tobytes()).hexdigest(), "grad_sha256": hashlib.sha256(gradients.tobytes()).hexdigest(),
              "hessian_sha256": hashlib.sha256(hessians.tobytes()).hexdigest(), "map_sha256_before": before, "map_sha256_after": after, "rows": rows}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    if not result["pass"]: raise SystemExit(2)


def aggregate(args) -> None:
    runs = [json.loads(path.read_text(encoding="utf-8")) for path in args.inputs]
    identities = [(row["active_index_sha256"], row["h_sha256"], row["grad_sha256"], row["hessian_sha256"]) for row in runs]
    runtime_limit = 2.0 * OFFICIAL_FOUR_SCENE_SLOWEST_S
    gates = {"three_fresh_processes": len(runs) == 3, "all_pass": all(row["pass"] for row in runs), "exact_repeatability": len(set(identities)) == 1,
             "map_unmodified": all(row["gates"]["map_unmodified"] for row in runs), "peak_gpu_under_20gib": max(row["peak_gpu_bytes"] for row in runs) <= 20 * 1024**3,
             "runtime_comparable": max(row["runtime_s"] for row in runs) <= runtime_limit}
    result = {"status": "PASS_ARKITSCENES_M1_SAFER_STATIC_G0" if all(gates.values()) else "NO_ARKITSCENES_M1_LEARNED_GAUSSIAN_MAP_QUALIFIED_UNDER_FROZEN_CONTRACT",
              "pass": all(gates.values()), "gates": gates, "run_count": len(runs), "query_count_per_run": 256, "active_index_sha256": identities[0][0] if identities else None,
              "runtime_s": [row["runtime_s"] for row in runs], "peak_gpu_bytes": [row["peak_gpu_bytes"] for row in runs], "official_four_scene_slowest_runtime_s": OFFICIAL_FOUR_SCENE_SLOWEST_S,
              "runtime_limit_2x_s": runtime_limit, "controller_count": 0, "navigation_count": 0, "map_mutation_count": 0}
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["status"])
    if not result["pass"]: raise SystemExit(3)


def main() -> None:
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="mode", required=True)
    one = sub.add_parser("run"); one.add_argument("--map-dir", type=Path, required=True); one.add_argument("--registry", type=Path, required=True); one.add_argument("--safer-source", type=Path, required=True); one.add_argument("--run-id", required=True); one.add_argument("--output", type=Path, required=True)
    agg = sub.add_parser("aggregate"); agg.add_argument("--inputs", nargs=3, type=Path, required=True); agg.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(); execute(args) if args.mode == "run" else aggregate(args)


if __name__ == "__main__":
    main()

