#!/usr/bin/env python3
"""Freeze and re-query the bounded L0 sentinel set without replaying trials."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from statistics import median
from typing import Any


TRIAL_IDS = (0, 24, 49, 74, 99)
EFFECTIVE_RADIUS_M = 0.11
ROBOT_RADIUS_M = 0.10
SAFETY_MARGIN_M = 0.01
MAP_RELATIVE = Path("outputs/stonehenge/splatfacto/2024-09-11_100724")
CAPTURE_RELATIVE = Path("run/instrumentation/step_capture_log.jsonl")


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_capture(formal_root: Path, trial_id: int) -> list[dict[str, Any]]:
    path = formal_root / f"trial-{trial_id:03d}" / "attempt-0" / CAPTURE_RELATIVE
    with path.open("r", encoding="utf-8") as stream:
        rows = [json.loads(line) for line in stream if line.strip()]
    if not rows:
        raise RuntimeError(f"empty capture log: {path}")
    return rows


def sentinel_indices(n: int) -> tuple[int, int, int]:
    if n < 3:
        raise ValueError("sentinel selection requires at least three committed steps")
    return 0, (n - 1) // 2, n - 1


def build_lock(server_root: Path, checkout: Path, output: Path) -> None:
    formal_root = server_root / "formal-v1"
    samples: list[dict[str, Any]] = []
    map_ids: set[str] = set()
    for trial_id in TRIAL_IDS:
        rows = load_capture(formal_root, trial_id)
        for role, index in zip(("first", "middle", "last"), sentinel_indices(len(rows))):
            row = rows[index]
            p_k = row["p_k"]
            map_ids.add(row["map_authority_id"])
            samples.append({
                "trial_id": trial_id,
                "step_id": int(row["step_id"]),
                "selection_role": role,
                "committed_step_count_in_trial": len(rows),
                "p_k_sha256": canonical_sha256(p_k),
                "decision_commit_id": row["decision_commit_id"],
                "map_authority_id": row["map_authority_id"],
            })
    if len(samples) != 15 or len(map_ids) != 1:
        raise RuntimeError(f"invalid sentinel lock cardinality: samples={len(samples)} maps={len(map_ids)}")

    source_paths = (
        Path("splat/gsplat_utils.py"),
        Path("splat/distances.py"),
        Path("reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/adapters/gaussian_barrier_adapter.py"),
    )
    source_identity = {str(p).replace("\\", "/"): file_sha256(checkout / p) for p in source_paths}
    query_hash = canonical_sha256(source_identity)
    config = checkout / MAP_RELATIVE / "config.yml"
    lock = {
        "schema_version": "L0_SENTINEL_SAMPLE_LOCK_V1",
        "selection_rule": "trials=[0,24,49,74,99]; per trial first, floor((N-1)/2), last committed step",
        "selection_rule_fixed_before_h_read": True,
        "trial_ids": list(TRIAL_IDS),
        "sample_count": len(samples),
        "samples": samples,
        "map_authority_id": next(iter(map_ids)),
        "map_config_relative_path": str(MAP_RELATIVE / "config.yml").replace("\\", "/"),
        "map_config_sha256": file_sha256(config),
        "query_source_sha256": source_identity,
        "query_implementation_hash": query_hash,
        "robot_radius_m": ROBOT_RADIUS_M,
        "safety_margin_m": SAFETY_MARGIN_M,
        "effective_radius_m": EFFECTIVE_RADIUS_M,
        "raw_h_read_count_at_lock_creation": 0,
        "rollout_count": 0,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(lock, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def requery(server_root: Path, checkout: Path, lock_path: Path, csv_path: Path, summary_path: Path) -> None:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    if not lock.get("selection_rule_fixed_before_h_read") or lock.get("sample_count") != 15:
        raise RuntimeError("sentinel lock is not frozen at exactly 15 samples")
    config = checkout / lock["map_config_relative_path"]
    if file_sha256(config) != lock["map_config_sha256"]:
        raise RuntimeError("map config identity drift")
    for relative, expected in lock["query_source_sha256"].items():
        if file_sha256(checkout / relative) != expected:
            raise RuntimeError(f"query source identity drift: {relative}")

    formal_root = server_root / "formal-v1"
    selected: list[tuple[dict[str, Any], list[float]]] = []
    capture_cache: dict[int, dict[int, dict[str, Any]]] = {}
    for sample in lock["samples"]:
        trial_id = int(sample["trial_id"])
        if trial_id not in capture_cache:
            capture_cache[trial_id] = {int(r["step_id"]): r for r in load_capture(formal_root, trial_id)}
        row = capture_cache[trial_id][int(sample["step_id"])]
        p_k = [float(x) for x in row["p_k"]]
        if canonical_sha256(p_k) != sample["p_k_sha256"]:
            raise RuntimeError(f"p_k identity mismatch: trial={trial_id} step={sample['step_id']}")
        if row["map_authority_id"] != lock["map_authority_id"]:
            raise RuntimeError("map authority drift")
        selected.append((sample, p_k))

    sys.path.insert(0, str(checkout))
    os.chdir(checkout)
    import torch
    from splat.gsplat_utils import GSplatLoader

    if not torch.cuda.is_available():
        raise RuntimeError("frozen query backend requires CUDA")
    device = torch.device("cuda:0")
    loader = GSplatLoader(config, device)
    records: list[dict[str, Any]] = []
    inflation = EFFECTIVE_RADIUS_M ** 2
    with torch.no_grad():
        for sample, p_k in selected:
            point = torch.tensor(p_k, dtype=torch.float32, device=device)
            h_all, _grad, _hess, _info = loader.query_distance(
                point, radius=EFFECTIVE_RADIUS_M, distance_type="ball-to-ellipsoid"
            )
            flat = h_all.reshape(-1)
            active_index = int(torch.argmin(flat).item())
            h_value = float(flat[active_index].item())
            status = "UNKNOWN" if not math.isfinite(h_value) else ("PASS" if h_value >= 0.0 else "FAIL")
            records.append({
                "trial_id": sample["trial_id"],
                "step_id": sample["step_id"],
                "h": h_value,
                "status_from_h": status,
                "nearest_or_active_gaussian_id": active_index,
                "raw_clearance_component": h_value + inflation,
                "inflation_component": inflation,
            })

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(records[0])
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
    values = [r["h"] for r in records]
    summary = {
        "schema_version": "L0_SENTINEL_H_SUMMARY_V1",
        "n": len(values),
        "min": min(values),
        "median": median(values),
        "max": max(values),
        "all_negative": all(v < 0.0 for v in values),
        "sign_consistent_with_logged_FAIL": all(r["status_from_h"] == "FAIL" for r in records),
        "absolute_magnitude_order": sorted(abs(v) for v in values),
        "near_zero_classification": "NOT_ESTABLISHED_NO_POST_HOC_THRESHOLD",
        "interpretation_boundary": "Diagnostic sentinel only; not a cohort sample and no prevalence or quantile claim.",
        "rollout_count": 0,
        "query_count": len(values),
    }
    summary_path.write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare-lock", "requery"))
    parser.add_argument("--server-root", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--summary", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare-lock":
        build_lock(args.server_root, args.checkout, args.lock)
    else:
        if args.csv is None or args.summary is None:
            parser.error("requery requires --csv and --summary")
        requery(args.server_root, args.checkout, args.lock, args.csv, args.summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
