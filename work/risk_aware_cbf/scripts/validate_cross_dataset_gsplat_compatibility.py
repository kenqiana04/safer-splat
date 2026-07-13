#!/usr/bin/env python3
"""Run read-only G1 GSplat compatibility gates for preregistered scenes."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import math
import time
from pathlib import Path


RESULT_DIR = Path("work/risk_aware_cbf/results/safer_baseline_cross_dataset_g0_g1")
MATRIX_FIELDS = [
    "candidate_id", "source_verified", "checkpoint_load_passed", "gaussian_fields_passed",
    "finite_tensor_passed", "covariance_passed", "query_h_passed", "query_grad_passed",
    "query_hess_passed", "scale_status", "navigation_volume_available",
    "geometry_collision_available", "gpu_memory_passed", "compatibility_status", "blocking_reason", "notes",
]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_adapter(adapter_dir: Path, candidate_id: str) -> dict[str, object] | None:
    path = adapter_dir / f"{candidate_id}.py"
    if not path.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"cross_dataset_adapter_{candidate_id}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load adapter module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    adapter = getattr(module, "SCENE_ADAPTER", None)
    if not isinstance(adapter, dict):
        raise RuntimeError(f"Adapter must export a dictionary named SCENE_ADAPTER: {path}")
    return adapter


def finite_tensor(torch, value) -> bool:
    return bool(torch.is_tensor(value) and value.numel() > 0 and torch.isfinite(value).all().item())


def classify(row: dict[str, object]) -> str:
    if not row["checkpoint_load_passed"] or not row["gaussian_fields_passed"] or not row["finite_tensor_passed"]:
        return "blocked_loader_incompatibility"
    if row["scale_status"] == "unknown":
        return "blocked_unknown_scale"
    if not row["navigation_volume_available"]:
        return "blocked_no_navigation_volume"
    if not row["gpu_memory_passed"]:
        return "blocked_resource_limit"
    if not row["query_h_passed"] or not row["query_grad_passed"] or not row["query_hess_passed"]:
        return "compatible_for_query_only"
    return "compatible_for_smoke"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--preregistration", type=Path, default=RESULT_DIR / "selected_scene_preregistration.csv")
    parser.add_argument("--output-dir", type=Path, default=RESULT_DIR)
    parser.add_argument("--adapter-dir", type=Path, default=Path("work/risk_aware_cbf/scripts/cross_dataset_scene_adapters"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    prereg = [row for row in read_csv(args.preregistration) if row.get("selected_for_g1", "").lower() == "true"]
    rows: list[dict[str, object]] = []
    gaussian_rows: list[dict[str, object]] = []
    query_rows: list[dict[str, object]] = []
    scale_rows: list[dict[str, object]] = []
    nav_rows: list[dict[str, object]] = []
    geometry_rows: list[dict[str, object]] = []
    if prereg:
        import torch
        from splat.gsplat_utils import GSplatLoader
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        for item in prereg:
            candidate_id = item["candidate_id"]
            adapter = load_adapter(args.adapter_dir, candidate_id)
            scale_status = "unknown"
            navigation_available = False
            geometry_available = False
            checkpoint_path = Path(item.get("checkpoint_path", ""))
            if adapter:
                scale = adapter.get("scale_transform", {})
                scale_status = str(scale.get("status", "unknown"))
                navigation_available = all(key in adapter for key in ("bounds", "start_region", "goal_region", "minimum_start_goal_separation"))
                geometry_available = adapter.get("geometry_checker") is not None
                checkpoint_path = Path(str(adapter.get("checkpoint_path", checkpoint_path)))
            record: dict[str, object] = {
                "candidate_id": candidate_id, "source_verified": "true", "checkpoint_load_passed": False,
                "gaussian_fields_passed": False, "finite_tensor_passed": False, "covariance_passed": False,
                "query_h_passed": False, "query_grad_passed": False, "query_hess_passed": False,
                "scale_status": scale_status, "navigation_volume_available": navigation_available,
                "geometry_collision_available": geometry_available, "gpu_memory_passed": True,
                "compatibility_status": "blocked_invalid_checkpoint", "blocking_reason": "", "notes": "",
            }
            try:
                if not checkpoint_path.exists():
                    raise FileNotFoundError(checkpoint_path)
                load_start = time.perf_counter()
                gsplat = GSplatLoader(checkpoint_path, device)
                load_seconds = time.perf_counter() - load_start
                record["checkpoint_load_passed"] = True
                fields = [getattr(gsplat, name, None) for name in ("means", "scales", "rots", "opacities")]
                record["gaussian_fields_passed"] = all(value is not None for value in fields)
                record["finite_tensor_passed"] = all(finite_tensor(torch, value) for value in fields)
                means = gsplat.means
                record["covariance_passed"] = bool(torch.isfinite(gsplat.scales).all().item() and torch.all(gsplat.scales > 0).item())
                state = torch.cat([means[0].to(device=device, dtype=torch.float32), torch.zeros(3, device=device)])
                query_start = time.perf_counter()
                h, grad, hess, _ = gsplat.query_distance(state, radius=0.03, distance_type="ball-to-ellipsoid")
                query_seconds = time.perf_counter() - query_start
                record["query_h_passed"] = finite_tensor(torch, h)
                record["query_grad_passed"] = finite_tensor(torch, grad)
                record["query_hess_passed"] = finite_tensor(torch, hess)
                gaussian_rows.append({"candidate_id": candidate_id, "gaussian_count": int(means.shape[0]), "load_seconds": load_seconds, "means_dtype": str(means.dtype), "scales_dtype": str(gsplat.scales.dtype)})
                query_rows.append({"candidate_id": candidate_id, "query_seconds": query_seconds, "h_finite": record["query_h_passed"], "grad_finite": record["query_grad_passed"], "hess_finite": record["query_hess_passed"]})
            except RuntimeError as exc:
                if "out of memory" in str(exc).lower():
                    record["gpu_memory_passed"] = False
                record["notes"] = f"{type(exc).__name__}: {exc}"[:500]
            except Exception as exc:  # Asset failures are audit results, not crashes.
                record["notes"] = f"{type(exc).__name__}: {exc}"[:500]
            record["compatibility_status"] = classify(record)
            record["blocking_reason"] = "" if record["compatibility_status"] == "compatible_for_smoke" else record["compatibility_status"]
            rows.append(record)
            scale_rows.append({"candidate_id": candidate_id, "scale_status": scale_status, "scale_source": adapter.get("scale_transform", {}).get("source", "") if adapter else "", "eligible_for_smoke": record["compatibility_status"] == "compatible_for_smoke"})
            nav_rows.append({"candidate_id": candidate_id, "navigation_volume_available": navigation_available, "notes": "Adapter declaration required; no inferred free space."})
            geometry_rows.append({"candidate_id": candidate_id, "geometry_type": "adapter_checker" if geometry_available else "none", "geometry_grounded_collision_available": geometry_available})
    write_csv(args.output_dir / "scene_compatibility_matrix.csv", MATRIX_FIELDS, rows)
    write_csv(args.output_dir / "gaussian_statistics.csv", ["candidate_id", "gaussian_count", "load_seconds", "means_dtype", "scales_dtype"], gaussian_rows)
    write_csv(args.output_dir / "query_sanity_summary.csv", ["candidate_id", "query_seconds", "h_finite", "grad_finite", "hess_finite"], query_rows)
    write_csv(args.output_dir / "scale_calibration_summary.csv", ["candidate_id", "scale_status", "scale_source", "eligible_for_smoke"], scale_rows)
    write_csv(args.output_dir / "navigation_volume_summary.csv", ["candidate_id", "navigation_volume_available", "notes"], nav_rows)
    write_csv(args.output_dir / "geometry_ground_truth_summary.csv", ["candidate_id", "geometry_type", "geometry_grounded_collision_available"], geometry_rows)
    print(f"preregistered_scene_count={len(prereg)}")
    print(f"compatible_for_smoke_count={sum(row['compatibility_status'] == 'compatible_for_smoke' for row in rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
