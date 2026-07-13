#!/usr/bin/env python3
"""Generate preregistered, seeded start-goal admissions without repair."""

from __future__ import annotations

import argparse
import csv
import importlib.util
from pathlib import Path

import numpy as np


RESULT_DIR = Path("work/risk_aware_cbf/results/safer_baseline_cross_dataset_g0_g1")
PAIR_FIELDS = ["candidate_id", "pair_id", "start_xyz", "goal_xyz", "start_goal_distance", "start_h", "goal_h", "start_finite", "goal_finite", "initially_admissible", "rejection_reason"]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def load_adapter(adapter_dir: Path, candidate_id: str) -> dict[str, object]:
    path = adapter_dir / f"{candidate_id}.py"
    spec = importlib.util.spec_from_file_location(f"cross_dataset_adapter_{candidate_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Adapter not found: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    adapter = getattr(module, "SCENE_ADAPTER", None)
    if not isinstance(adapter, dict):
        raise RuntimeError(f"Adapter must export SCENE_ADAPTER: {path}")
    return adapter


def sample_region(rng: np.random.Generator, region: dict[str, object]) -> np.ndarray:
    return rng.uniform(np.asarray(region["min_xyz"], dtype=float), np.asarray(region["max_xyz"], dtype=float))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--compatibility", type=Path, default=RESULT_DIR / "scene_compatibility_matrix.csv")
    parser.add_argument("--preregistration", type=Path, default=RESULT_DIR / "selected_scene_preregistration.csv")
    parser.add_argument("--output-dir", type=Path, default=RESULT_DIR)
    parser.add_argument("--adapter-dir", type=Path, default=Path("work/risk_aware_cbf/scripts/cross_dataset_scene_adapters"))
    parser.add_argument("--seed", type=int, default=20260713)
    parser.add_argument("--candidate-pairs", type=int, default=20)
    args = parser.parse_args()
    if args.candidate_pairs != 20:
        raise ValueError("The G0-G1 contract requires exactly 20 candidate pairs per scene.")
    compatible = {row["candidate_id"] for row in read_csv(args.compatibility) if row.get("compatibility_status") == "compatible_for_smoke"}
    prereg = [row for row in read_csv(args.preregistration) if row.get("candidate_id") in compatible]
    rows: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    if prereg:
        import torch
        from splat.gsplat_utils import GSplatLoader
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        for scene_index, scene in enumerate(sorted(prereg, key=lambda item: item["candidate_id"])):
            adapter = load_adapter(args.adapter_dir, scene["candidate_id"])
            rng = np.random.default_rng(args.seed + scene_index)
            gsplat = GSplatLoader(Path(str(adapter["checkpoint_path"])), device)
            admitted = 0
            for pair_id in range(args.candidate_pairs):
                start = sample_region(rng, adapter["start_region"])
                goal = sample_region(rng, adapter["goal_region"])
                separation = float(np.linalg.norm(goal - start))
                start_state = torch.tensor(np.r_[start, np.zeros(3)], device=device, dtype=torch.float32)
                goal_state = torch.tensor(np.r_[goal, np.zeros(3)], device=device, dtype=torch.float32)
                start_h, _, _, _ = gsplat.query_distance(start_state, radius=0.03, distance_type="ball-to-ellipsoid")
                goal_h, _, _, _ = gsplat.query_distance(goal_state, radius=0.03, distance_type="ball-to-ellipsoid")
                min_start_h, min_goal_h = float(torch.min(start_h).item()), float(torch.min(goal_h).item())
                start_finite, goal_finite = bool(torch.isfinite(start_h).all().item()), bool(torch.isfinite(goal_h).all().item())
                reasons = []
                if separation < float(adapter["minimum_start_goal_separation"]):
                    reasons.append("minimum_separation")
                if not start_finite or not goal_finite:
                    reasons.append("nonfinite_query")
                if min_start_h <= 0 or min_goal_h <= 0:
                    reasons.append("initial_unsafe")
                admissible = not reasons
                admitted += int(admissible)
                rows.append({"candidate_id": scene["candidate_id"], "pair_id": pair_id, "start_xyz": ";".join(f"{value:.9g}" for value in start), "goal_xyz": ";".join(f"{value:.9g}" for value in goal), "start_goal_distance": separation, "start_h": min_start_h, "goal_h": min_goal_h, "start_finite": start_finite, "goal_finite": goal_finite, "initially_admissible": admissible, "rejection_reason": ";".join(reasons)})
            summaries.append({"candidate_id": scene["candidate_id"], "candidate_pair_count": args.candidate_pairs, "admissible_pair_count": admitted, "initial_admission_rate": admitted / args.candidate_pairs, "smoke_eligible": admitted >= 3, "notes": "No repair and no navigation-result-based selection."})
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "start_goal_candidate_pairs.csv", PAIR_FIELDS, rows)
    write_csv(args.output_dir / "initial_admission_summary.csv", ["candidate_id", "candidate_pair_count", "admissible_pair_count", "initial_admission_rate", "smoke_eligible", "notes"], summaries)
    print(f"generated_pair_count={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
