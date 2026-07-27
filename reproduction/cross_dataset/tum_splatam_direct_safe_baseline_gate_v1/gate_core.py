"""Deterministic, task-owned TUM direct-safe baseline qualification gate.

This module has two deliberately separate phases.  The geometry phase performs
only frozen-map queries and may authorize a registry.  The optional baseline
phase is invoked by a separate subprocess runner only after that registry is
frozen.  No recovery, V4-C, Start-Safe, Risk-Aware, or paired20 execution is
imported here.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path
from typing import Any

import numpy as np

GATE_ROOT = Path("/disk1/zlab/maintenance_records/tum_splatam_direct_safe_baseline_gate_v1_1")
REPO = Path("/disk1/zlab/projects/safer-splat")
MAP = Path("/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/splatam/canonical_export/export_a")
TRANSFORMS = Path("/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room/transforms.json")
PAIRED20 = Path("/disk1/zlab/maintenance_records/tum_splatam_dt_triggered_v4c_paired20_v1")
RADIUS = 0.015
ALPHA, BETA, DT, MAX_STEPS, GOAL_TOLERANCE = 5.0, 1.0, 0.05, 800, 0.001
F63 = "f63b4c496861c4f8881348d74244c1ff9a528d51"
MANIFEST_SHA = "380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6"
OLD_PAIRS = {(0, 50), (1, 51), (8, 58), (9, 59), (111, 287)}
SEED = "TUM_DIRECT_SAFE_V1_1"
BINS = (("B1", 0.50, 0.75), ("B2", 0.75, 1.00), ("B3", 1.00, 1.50), ("B4", 1.50, 3.00))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def compact_pair(row: dict[str, Any]) -> dict[str, Any]:
    """Keep full query samples server-side only; summaries/registry stay compact."""
    return {key: value for key, value in row.items() if key != "samples"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def ensure_root() -> None:
    for name in ("input_identity", "endpoint_inventory", "candidate_registry", "coarse_screen", "dense_qualification", "float64_certification", "frozen_rollout_registry", "baseline_rollouts", "baseline_certification", "decision", "logs", "manifests", "tmp"):
        (GATE_ROOT / name).mkdir(parents=True, exist_ok=True)


def camera_positions() -> np.ndarray:
    frames = load(TRANSFORMS)["frames"]
    return np.asarray([[f["transform_matrix"][0][3], f["transform_matrix"][1][3], f["transform_matrix"][2][3]] for f in frames], dtype=np.float64)


def position_sha(positions: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(positions, dtype=np.float64).tobytes()).hexdigest()


def git_blob(path: str) -> str:
    import subprocess
    return subprocess.check_output(["git", "rev-parse", f"{F63}:{path}"], cwd=REPO, text=True).strip()


def identity() -> dict[str, Any]:
    import subprocess
    positions = camera_positions()
    manifest = load(PAIRED20 / "manifests/run_manifest.json")
    states = Counter(entry["state"] for entry in manifest["states"].values())
    actual_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    data = {
        "status": "PASS" if actual_head == F63 else "BLOCKED_BY_TUM_DIRECT_SAFE_GATE_IDENTITY_MISMATCH",
        "authoritative_checkout": str(REPO), "checkout_head": actual_head, "expected_checkout_head": F63,
        "core_blobs": {p: git_blob(p) for p in ("splat/distances.py", "splat/gsplat_utils.py", "cbf/cbf_utils.py")},
        "expected_core_blobs": {"splat/distances.py": "d7f17b67df40e36e458c7a5ed77c4a04659c6f35", "splat/gsplat_utils.py": "782c38eca50e78c605085b481155ed61e4607336", "cbf/cbf_utils.py": "7c6e1300b125cc0a2a950ac2835a1fbe3d0de113"},
        "numerical_contract_v2_blob": "7a0d85b0b334c2e94ccc23b033d8453322d72fe1",
        "map": str(MAP), "canonical_gaussian_count": int(np.load(MAP / "means_world_m.npy", mmap_mode="r").shape[0]),
        "transforms": str(TRANSFORMS), "transforms_sha256": sha256(TRANSFORMS), "expected_camera_center_count": 300, "world_position_count": len(positions), "world_position_sha256": position_sha(positions), "camera_universe": "CANONICAL_TUM_MAP_ALIGNED_CAMERA_CENTER_UNIVERSE_V1", "synthetic_static_query_count_pr44": 908,
        "frozen_parameters": {"robot_radius": RADIUS, "alpha": ALPHA, "beta": BETA, "dt": DT, "integrator": "explicit Euler", "max_steps": MAX_STEPS, "goal_tolerance": GOAL_TOLERANCE, "qp_solver": "Clarabel"},
        "paired20_manifest": str(PAIRED20 / "manifests/run_manifest.json"), "paired20_manifest_sha256": sha256(PAIRED20 / "manifests/run_manifest.json"), "paired20_states": dict(states),
        "old_invalid_pairs": [list(pair) for pair in sorted(OLD_PAIRS)], "ordering_seed": SEED,
    }
    if data["core_blobs"] != data["expected_core_blobs"] or data["transforms_sha256"] != "b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a" or data["world_position_count"] != data["expected_camera_center_count"] or data["world_position_sha256"] != "bcee7929b9a7c595c669212972c60f5290e1eceb6834cec66f24a9193ae24d6c" or data["canonical_gaussian_count"] != 5464102 or data["paired20_manifest_sha256"] != MANIFEST_SHA or states != Counter({"TERMINAL_SCIENTIFIC_RESULT": 2, "NOT_STARTED": 38}):
        data["status"] = "BLOCKED_BY_TUM_DIRECT_SAFE_GATE_IDENTITY_MISMATCH"
    dump(GATE_ROOT / "input_identity/input_identity_summary_v1_1.json", data)
    return data


class FullMapQuery:
    """Full-map active-ellipsoid query with an exact lower-bound screen."""
    def __init__(self) -> None:
        import torch
        from ellipsoids.covariance_utils import quaternion_to_rotation_matrix
        self.torch = torch
        self.device = torch.device("cuda:0")
        self.means = torch.from_numpy(np.load(MAP / "means_world_m.npy")).to(self.device, dtype=torch.float32)
        quats = torch.from_numpy(np.load(MAP / "quaternions_wxyz.npy")).to(self.device, dtype=torch.float32)
        scales = torch.from_numpy(np.load(MAP / "scales_linear_m.npy")).to(self.device, dtype=torch.float32)
        rotation = quaternion_to_rotation_matrix(quats)
        self.scales, order = torch.sort(scales, dim=-1, descending=True)
        self.rots = torch.gather(rotation, 2, order[..., None, :].expand_as(rotation))
        self.max_scale = self.scales.max(dim=-1).values
        self.bbox_min = self.means.amin(dim=0)
        self.bbox_max = self.means.amax(dim=0)
        self.cache: dict[bytes, dict[str, Any]] = {}

    def _exact(self, point: np.ndarray, ids: Any, hessian: bool = False) -> dict[str, Any]:
        torch = self.torch
        p = torch.as_tensor(point, device=self.device, dtype=torch.float32)
        means, scales, rots = self.means[ids], self.scales[ids], self.rots[ids]
        signed = torch.bmm(rots.transpose(1, 2), (p - means).unsqueeze(-1)).squeeze(-1) + 1e-8
        flip, local, axes = torch.sign(signed), torch.abs(signed), scales + 1e-8
        z = local / axes
        g = (z * z).sum(dim=-1) - 1.0
        ratio = (axes / axes[:, -1:]) ** 2
        bracket = torch.zeros((local.shape[0], 2), device=self.device, dtype=torch.float32)
        bracket[:, 0] = z[:, -1] - 1.0
        exterior = g >= 0
        bracket[exterior, 1] = torch.linalg.vector_norm(ratio[exterior] * z[exterior], dim=-1) - 1.0
        for _ in range(32):
            lam_scaled = bracket.mean(dim=-1, keepdim=True)
            value = ((ratio * z / (lam_scaled + ratio)) ** 2).sum(dim=-1) - 1.0
            lower = value >= 0
            bracket[lower, 0] = lam_scaled.squeeze(-1)[lower]
            bracket[~lower, 1] = lam_scaled.squeeze(-1)[~lower]
        lam = bracket.mean(dim=-1, keepdim=True) * axes[:, -1:] ** 2
        yhat = (axes ** 2) * local / (lam + axes ** 2)
        distance = ((yhat - local) ** 2).sum(dim=-1)
        phi = torch.sign(((local / axes) ** 2).sum(dim=-1) - 1.0)
        closest = torch.bmm(rots, (flip * yhat).unsqueeze(-1)).squeeze(-1) + means
        h = phi * distance - RADIUS ** 2
        gradient = 2.0 * phi[:, None] * (p - closest)
        result = {"h": h, "gradient": gradient, "closest": closest, "phi": phi}
        if hessian:
            dq_dlam = -2.0 * ((axes ** 2 * local ** 2) / (lam + axes ** 2) ** 3).sum(dim=-1, keepdim=True)
            dy_dlam = -(axes ** 2 * local) / (lam + axes ** 2) ** 2
            dq_dx = -2.0 * dy_dlam
            diagonal = lam / (lam + axes ** 2)
            first = 2.0 * (torch.diag_embed(diagonal) + torch.einsum("bi,bj->bij", dy_dlam, dq_dx) / dq_dlam[..., None])
            signed_hessian = flip[..., :, None] * first * flip[..., None, :]
            result["hessian"] = phi[:, None, None] * torch.bmm(rots, torch.bmm(signed_hessian, rots.transpose(1, 2)))
        return result

    def query(self, point: np.ndarray, detail: bool = False) -> dict[str, Any]:
        key = np.asarray(point, dtype=np.float64).tobytes()
        if key in self.cache and not detail:
            return self.cache[key]
        torch = self.torch
        p = torch.as_tensor(point, device=self.device, dtype=torch.float32)
        exterior = torch.linalg.vector_norm(self.means - p, dim=-1) - self.max_scale
        seed = torch.topk(exterior, k=min(4096, exterior.numel()), largest=False).indices
        seed_h = self._exact(np.asarray(point), seed)["h"]
        finite_seed = seed_h[torch.isfinite(seed_h)]
        best = float(finite_seed.min().item()) if finite_seed.numel() else float("inf")
        lower_bound = torch.where(exterior > 0, exterior.square() - RADIUS ** 2, torch.full_like(exterior, -float("inf")))
        candidates = torch.unique(torch.cat((seed, torch.nonzero(lower_bound <= best + 1e-8, as_tuple=False).squeeze(-1))))
        exact = self._exact(np.asarray(point), candidates)
        sortable = torch.where(torch.isfinite(exact["h"]), exact["h"], torch.full_like(exact["h"], float("inf")))
        order = torch.argsort(sortable)[: min(16, sortable.numel())]
        local = int(order[0].item())
        active = int(candidates[local].item())
        result = {
            "position": np.asarray(point, dtype=float).tolist(), "h": float(exact["h"][local].item()), "active_gaussian": active,
            "gradient": exact["gradient"][local].detach().cpu().double().tolist(), "closest_point": exact["closest"][local].detach().cpu().double().tolist(),
            "finite": bool(torch.isfinite(exact["h"][local]).item() and torch.isfinite(exact["gradient"][local]).all().item()),
            "full_map_gaussian_count": int(self.means.shape[0]), "screen_candidate_count": int(candidates.numel()),
            "top_float32_candidates": [int(candidates[i].item()) for i in order], "query_source_identity": "full_map_lower_bound_screen_active_ellipsoid",
            "bbox_valid": bool(torch.isfinite(p).all().item() and torch.all(p >= self.bbox_min - 1e-6).item() and torch.all(p <= self.bbox_max + 1e-6).item()),
        }
        if detail:
            one = torch.as_tensor([active], device=self.device)
            active_exact = self._exact(np.asarray(point), one, hessian=True)
            result["hessian"] = active_exact["hessian"][0].detach().cpu().double().tolist()
            result["hessian_finite"] = bool(torch.isfinite(active_exact["hessian"]).all().item())
        self.cache[key] = result
        return result

    def query_many(self, points: list[np.ndarray], detail: bool = False) -> list[dict[str, Any]]:
        return [self.query(point, detail=detail) for point in points]


def inventory(query: FullMapQuery) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    existing_rows = GATE_ROOT / "endpoint_inventory/full_300_endpoint_inventory_v1_1.json"
    existing_summary = GATE_ROOT / "endpoint_inventory/endpoint_inventory_summary_v1_1.json"
    if existing_rows.exists() and existing_summary.exists():
        rows, summary = load(existing_rows), load(existing_summary)
        if len(rows) == 300 and summary.get("world_position_sha256") == position_sha(camera_positions()) and summary.get("radius") == RADIUS and summary.get("complete_map") and summary.get("no_filtering") and summary.get("no_downsampling"):
            summary = {**summary, "reused_within_same_gate_attempt": True}
            dump(existing_summary, summary)
            return rows, summary
        raise RuntimeError("BLOCKED_BY_TUM_DIRECT_SAFE_GATE_ENDPOINT_INVENTORY_REUSE_CONFLICT")
    positions = camera_positions()
    rows: list[dict[str, Any]] = []
    started = time.perf_counter()
    for frame, position in enumerate(positions):
        query_started = time.perf_counter()
        result = query.query(position, detail=True)
        finite = bool(np.isfinite(position).all() and result["finite"] and result["hessian_finite"])
        row = {"frame_index": frame, "world_position": position.tolist(), "finite": finite, "bbox_valid": result["bbox_valid"], "h_float32": result["h"], "active_gaussian": result["active_gaussian"], "gradient_finite": bool(np.isfinite(result["gradient"]).all()), "hessian_finite": result["hessian_finite"], "query_runtime_seconds": time.perf_counter() - query_started, "map_query_identity": result["query_source_identity"], "endpoint_classification": "ENDPOINT_FLOAT32_SAFE_CANDIDATE" if finite and result["bbox_valid"] and result["h"] > 0 else "ENDPOINT_REJECTED"}
        rows.append(row)
    dump(GATE_ROOT / "endpoint_inventory/full_300_endpoint_inventory_v1_1.json", rows)
    summary = {"status": "PASS", "endpoint_count": len(rows), "endpoint_float32_safe_candidate_count": sum(x["endpoint_classification"] == "ENDPOINT_FLOAT32_SAFE_CANDIDATE" for x in rows), "negative_or_boundary_count": sum(x["h_float32"] <= 0 for x in rows), "nonfinite_count": sum(not x["finite"] for x in rows), "world_position_sha256": position_sha(positions), "radius": RADIUS, "complete_map": True, "no_filtering": True, "no_downsampling": True, "runtime_seconds": time.perf_counter() - started, "query_source_identity": "full_map_lower_bound_screen_active_ellipsoid", "reuse_of_v1_pre_correction_results": False}
    dump(GATE_ROOT / "endpoint_inventory/endpoint_inventory_summary_v1_1.json", summary)
    return rows, summary


def separation_bin(distance: float) -> str | None:
    for name, lo, hi in BINS:
        if lo <= distance < hi or (name == "B4" and lo <= distance <= hi):
            return name
    return None


def candidate_inventory(rows: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    safe = [row for row in rows if row["endpoint_classification"] == "ENDPOINT_FLOAT32_SAFE_CANDIDATE"]
    positions = camera_positions()
    bins: dict[str, list[dict[str, Any]]] = {name: [] for name, _, _ in BINS}
    excluded = duplicates = 0
    for left, right in combinations(safe, 2):
        a, b = int(left["frame_index"]), int(right["frame_index"])
        pair = (min(a, b), max(a, b))
        if pair in OLD_PAIRS:
            excluded += 1
            continue
        distance = float(np.linalg.norm(positions[pair[1]] - positions[pair[0]]))
        which = separation_bin(distance)
        if which is None:
            continue
        key = hashlib.sha256(f"{SEED}:{pair[0]}:{pair[1]}".encode("utf-8")).hexdigest()
        bins[which].append({"pair_id": f"{pair[0]}->{pair[1]}", "start_frame": pair[0], "goal_frame": pair[1], "separation": distance, "bin": which, "hash_order": key})
    for values in bins.values():
        values.sort(key=lambda row: row["hash_order"])
    all_rows = [row for name, _, _ in BINS for row in bins[name]]
    dump(GATE_ROOT / "candidate_registry/all_pair_candidate_inventory.json", all_rows)
    summary = {"endpoint_safe_count": len(safe), "total_candidate_count": len(all_rows), "per_bin_candidate_count": {name: len(bins[name]) for name, _, _ in BINS}, "excluded_old_pair_count": excluded, "duplicate_count": duplicates, "ordering_seed": SEED, "candidate_identity": "unordered safe camera-center pairs; geometry/hash only; no rollout inputs"}
    dump(GATE_ROOT / "candidate_registry/all_pair_candidate_summary_v1_1.json", summary)
    return bins, summary


def pair_samples(pair: dict[str, Any], count: int) -> list[np.ndarray]:
    positions = camera_positions(); a, b = positions[pair["start_frame"]], positions[pair["goal_frame"]]
    return [(1.0 - t) * a + t * b for t in np.linspace(0.0, 1.0, count)]


def coarse_screen(query: FullMapQuery, bins: dict[str, list[dict[str, Any]]]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    stages = []
    started = time.perf_counter()
    for stage_name, budget, threshold in (("STAGE_1", 64, None), ("STAGE_2", 256, 12), ("STAGE_3", 512, 8)):
        if stage_name == "STAGE_2" and sum(row["classification"] == "COARSE_CLEAR" for row in results.values()) >= 12:
            stages.append({"stage": stage_name, "executed": False, "reason": "stage_1_clear_count_at_least_12"}); continue
        if stage_name == "STAGE_3" and sum(row["classification"] == "COARSE_CLEAR" for row in results.values()) >= 8:
            stages.append({"stage": stage_name, "executed": False, "reason": "stage_2_clear_count_at_least_8"}); continue
        before = len(results); query_count = 0; stage_started = time.perf_counter()
        for name, _, _ in BINS:
            for pair in bins[name][:budget]:
                if pair["pair_id"] in results:
                    continue
                samples = query.query_many(pair_samples(pair, 33))
                hs = [sample["h"] for sample in samples]
                finite = all(sample["finite"] for sample in samples)
                classification = "COARSE_CLEAR" if finite and all(h > 0 for h in hs) else "COARSE_NONFINITE" if not finite else "COARSE_BLOCKED"
                results[pair["pair_id"]] = {**pair, "classification": classification, "sample_count": 33, "min_float32_h": min(hs), "negative_sample_count": sum(h < 0 for h in hs), "nonfinite_sample_count": sum(not sample["finite"] for sample in samples), "minimum_sample_t": int(np.argmin(hs)) / 32.0, "active_gaussian_change_count": sum(a["active_gaussian"] != b["active_gaussian"] for a, b in zip(samples, samples[1:])), "samples": samples}
                query_count += 33
        stage_rows = list(results.values())
        stages.append({"stage": stage_name, "executed": True, "per_bin_budget": budget, "new_evaluated_pair_count": len(results) - before, "cumulative_evaluated_pair_count": len(results), "cumulative_clear_pair_count": sum(row["classification"] == "COARSE_CLEAR" for row in stage_rows), "cumulative_blocked_pair_count": sum(row["classification"] == "COARSE_BLOCKED" for row in stage_rows), "cumulative_nonfinite_pair_count": sum(row["classification"] == "COARSE_NONFINITE" for row in stage_rows), "new_query_count": query_count, "runtime_seconds": time.perf_counter() - stage_started, "per_bin_evaluated": {name: sum(row["bin"] == name for row in stage_rows) for name, _, _ in BINS}})
    compact_rows = [{key: value for key, value in row.items() if key != "samples"} for row in results.values()]
    dump(GATE_ROOT / "coarse_screen/full_coarse_pair_results.json", list(results.values()))
    summary = {"stages": stages, "total_search_budget_used": len(results), "total_query_count": sum(stage.get("new_query_count", 0) for stage in stages), "coarse_clear_count": sum(row["classification"] == "COARSE_CLEAR" for row in results.values()), "coarse_blocked_count": sum(row["classification"] == "COARSE_BLOCKED" for row in results.values()), "coarse_nonfinite_count": sum(row["classification"] == "COARSE_NONFINITE" for row in results.values()), "runtime_seconds": time.perf_counter() - started, "results": compact_rows}
    dump(GATE_ROOT / "coarse_screen/coarse_direct_path_screen_summary_v1_1.json", summary)
    return results, summary


def dense_candidates(coarse: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for name, _, _ in BINS:
        rows = [row for row in coarse.values() if row["bin"] == name and row["classification"] == "COARSE_CLEAR"]
        selected.extend(sorted(rows, key=lambda row: row["hash_order"])[:8])
    return selected


def dense_qualification(query: FullMapQuery, coarse: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected = dense_candidates(coarse)
    summaries: list[dict[str, Any]] = []
    started = time.perf_counter()
    for pair in selected:
        count = max(257, math.ceil(pair["separation"] / 0.005) + 1)
        positions = pair_samples(pair, count)
        base_rows = query.query_many(positions)
        rows = [{**sample, "t": float(index / (count - 1)), "source": "base"} for index, sample in enumerate(base_rows)]
        queue: list[tuple[dict[str, Any], dict[str, Any], int]] = []
        for left, right in zip(rows, rows[1:]):
            middle_position = (np.asarray(left["position"]) + np.asarray(right["position"])) * 0.5
            middle = {**query.query(middle_position), "t": (left["t"] + right["t"]) * 0.5, "source": "midpoint"}
            rows.append(middle)
            near = left["h"] <= 1e-5 or right["h"] <= 1e-5
            switch = left["active_gaussian"] != right["active_gaussian"] and min(left["h"], right["h"]) < 5e-5
            sign = left["h"] * right["h"] < 0
            lower_middle = middle["h"] < min(left["h"], right["h"])
            if near or switch or sign or lower_middle:
                queue.append((left, right, 1))
        refined: list[dict[str, Any]] = []
        while queue:
            left, right, depth = queue.pop()
            distance = float(np.linalg.norm(np.asarray(left["position"]) - np.asarray(right["position"])))
            if distance <= 0.001 or depth >= 20:
                continue
            middle_position = (np.asarray(left["position"]) + np.asarray(right["position"])) * 0.5
            middle = {**query.query(middle_position), "t": (left["t"] + right["t"]) * 0.5, "source": f"refinement_{depth}"}
            rows.append(middle); refined.append(middle)
            for a, b in ((left, middle), (middle, right)):
                near = a["h"] <= 1e-5 or b["h"] <= 1e-5
                switch = a["active_gaussian"] != b["active_gaussian"] and min(a["h"], b["h"]) < 5e-5
                sign = a["h"] * b["h"] < 0
                lower_mid = middle["h"] < min(a["h"], b["h"])
                if near or switch or sign or lower_mid:
                    queue.append((a, b, depth + 1))
        rows.sort(key=lambda row: row["t"])
        finite = all(row["finite"] and np.isfinite(row["gradient"]).all() for row in rows)
        minimum = min(rows, key=lambda row: row["h"])
        classification = "DENSE_SAMPLE_NONFINITE" if not finite else "DENSE_SAMPLE_BLOCKED" if any(row["h"] < 0 for row in rows) else "DENSE_SAMPLE_CLEAR_CANDIDATE"
        detailed = {"pair": pair, "sample_count_base": count, "sample_count_total": len(rows), "rows": rows, "refinement_sample_count": len(refined)}
        dump(GATE_ROOT / "dense_qualification" / f"{pair['start_frame']}_{pair['goal_frame']}_dense_samples.json", detailed)
        summaries.append({**compact_pair(pair), "classification": classification, "base_sample_count": count, "total_sample_count": len(rows), "refinement_sample_count": len(refined), "min_float32_h": minimum["h"], "minimum_t": minimum["t"], "active_gaussian": minimum["active_gaussian"], "nonfinite_count": sum(not row["finite"] for row in rows), "dense_samples_path": str(GATE_ROOT / "dense_qualification" / f"{pair['start_frame']}_{pair['goal_frame']}_dense_samples.json")})
    summary = {"selected_from_coarse_clear_count": len(selected), "dense_sample_clear_candidate_count": sum(row["classification"] == "DENSE_SAMPLE_CLEAR_CANDIDATE" for row in summaries), "dense_sample_blocked_count": sum(row["classification"] == "DENSE_SAMPLE_BLOCKED" for row in summaries), "dense_sample_nonfinite_count": sum(row["classification"] == "DENSE_SAMPLE_NONFINITE" for row in summaries), "runtime_seconds": time.perf_counter() - started, "pairs": summaries, "sampling_rule": "max(257, ceil(separation/0.005)+1), midpoint checks, deterministic refinement to <=0.001m or depth 20"}
    dump(GATE_ROOT / "dense_qualification/dense_direct_path_qualification_summary_v1_1.json", summary)
    return summaries, summary


def rotation(quaternion: np.ndarray) -> np.ndarray:
    w, x, y, z = np.asarray(quaternion, dtype=np.float64) / np.linalg.norm(quaternion)
    return np.asarray([[1 - 2*(y*y + z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]], dtype=np.float64)


def _reference_solve(axes: np.ndarray, local: np.ndarray, use_newton: bool) -> tuple[np.ndarray, float, float]:
    axes2 = axes * axes
    equation = lambda lam: float(np.sum((axes * local / (lam + axes2)) ** 2) - 1.0)
    inside = float(np.sum((local / axes) ** 2)) < 1.0
    lo, hi = (-(float(axes2.min())) * (1.0 - 1e-14), 0.0) if inside else (0.0, 1.0)
    while not inside and equation(hi) > 0.0:
        hi *= 2.0
    lam = (lo + hi) * 0.5
    for _ in range(180):
        value = equation(lam)
        if use_newton:
            derivative = -2.0 * float(np.sum((axes * local) ** 2 / (lam + axes2) ** 3))
            proposal = lam - value / derivative if derivative != 0.0 else math.nan
            if lo < proposal < hi and math.isfinite(proposal):
                lam = proposal
        if equation(lam) >= 0.0:
            lo = lam
        else:
            hi = lam
        lam = (lo + hi) * 0.5
    closest = axes2 * local / (lam + axes2)
    return closest, abs(equation(lam)), abs(float(np.sum((closest / axes) ** 2) - 1.0))


def float64_reference(point: np.ndarray, index: int, means: np.ndarray, scales: np.ndarray, quats: np.ndarray) -> dict[str, Any]:
    mean, axes, quat = means[index].astype(np.float64), scales[index].astype(np.float64), quats[index].astype(np.float64)
    local = rotation(quat).T @ (np.asarray(point, dtype=np.float64) - mean)
    phi = 1.0 if float(np.sum((local / axes) ** 2)) >= 1.0 else -1.0
    ya, residual_a, surface_a = _reference_solve(axes, local, False)
    yb, residual_b, surface_b = _reference_solve(axes, local, True)
    ha = phi * float(np.sum((ya-local) ** 2)) - RADIUS ** 2
    hb = phi * float(np.sum((yb-local) ** 2)) - RADIUS ** 2
    tau = max(1e-12, 10*abs(ha-hb), 10*max(residual_a, residual_b, surface_a, surface_b))
    classification = "ROBUST_SAFE" if ha > tau and hb > tau else "ROBUST_OVERLAP" if ha < -tau and hb < -tau else "NUMERICALLY_INDETERMINATE"
    return {"index": int(index), "h_ref_a": ha, "h_ref_b": hb, "kkt_residual_a": residual_a, "kkt_residual_b": residual_b, "surface_residual_a": surface_a, "surface_residual_b": surface_b, "tau_ref": tau, "classification": classification}


def float64_certification(dense: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    means = np.load(MAP / "means_world_m.npy", mmap_mode="r")
    scales = np.load(MAP / "scales_linear_m.npy", mmap_mode="r")
    quats = np.load(MAP / "quaternions_wxyz.npy", mmap_mode="r")
    summaries: list[dict[str, Any]] = []
    for pair in dense:
        if pair["classification"] != "DENSE_SAMPLE_CLEAR_CANDIDATE":
            summaries.append({**compact_pair(pair), "classification": "DIRECT_PATH_BLOCKED" if pair["classification"] == "DENSE_SAMPLE_BLOCKED" else "DIRECT_PATH_QUERY_NONFINITE", "float64_checked_sample_count": 0}); continue
        detailed = load(Path(pair["dense_samples_path"]))["rows"]
        ordered = sorted(detailed, key=lambda row: row["t"])
        minimum_index = min(range(len(ordered)), key=lambda index: ordered[index]["h"])
        chosen = {0, len(ordered)-1, minimum_index}
        chosen.update(range(max(0, minimum_index-2), min(len(ordered), minimum_index+3)))
        chosen.update(index for index, row in enumerate(ordered) if row["source"].startswith("refinement_"))
        refs = []
        for index in sorted(chosen):
            row = ordered[index]
            candidates = row["top_float32_candidates"]
            candidate_refs = [float64_reference(np.asarray(row["position"]), candidate, means, scales, quats) for candidate in candidates]
            worst = min(candidate_refs, key=lambda item: min(item["h_ref_a"], item["h_ref_b"]))
            refs.append({"t": row["t"], "position": row["position"], "float32_h": row["h"], "float32_active": row["active_gaussian"], "candidate_references": candidate_refs, "worst_reference": worst})
        statuses = [entry["worst_reference"]["classification"] for entry in refs]
        classification = "DIRECT_SAFE_PAIR_QUALIFIED" if statuses and all(status == "ROBUST_SAFE" for status in statuses) else "DIRECT_PATH_NUMERICALLY_INDETERMINATE" if "NUMERICALLY_INDETERMINATE" in statuses else "DIRECT_PATH_BLOCKED"
        details_path = GATE_ROOT / "float64_certification" / f"{pair['start_frame']}_{pair['goal_frame']}_float64.json"
        dump(details_path, {"pair": pair, "reference_a": "safeguarded KKT bisection", "reference_b": "safeguarded Newton plus bisection fallback", "references": refs})
        minima = [entry["worst_reference"] for entry in refs]
        summaries.append({**compact_pair(pair), "classification": classification, "float64_checked_sample_count": len(refs), "float64_min_h_ref_a": min(item["h_ref_a"] for item in minima), "float64_min_h_ref_b": min(item["h_ref_b"] for item in minima), "float64_max_tau_ref": max(item["tau_ref"] for item in minima), "float64_details_path": str(details_path)})
    summary = {"direct_safe_pair_qualified_count": sum(row["classification"] == "DIRECT_SAFE_PAIR_QUALIFIED" for row in summaries), "direct_path_blocked_count": sum(row["classification"] == "DIRECT_PATH_BLOCKED" for row in summaries), "numerically_indeterminate_count": sum(row["classification"] == "DIRECT_PATH_NUMERICALLY_INDETERMINATE" for row in summaries), "pairs": summaries}
    dump(GATE_ROOT / "float64_certification/float64_direct_pair_certification_summary_v1_1.json", summary)
    return summaries, summary


def select_registry(qualified: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    ordered = sorted([row for row in qualified if row["classification"] == "DIRECT_SAFE_PAIR_QUALIFIED"], key=lambda row: (next(index for index, (name, _, _) in enumerate(BINS) if name == row["bin"]), row["hash_order"]))
    valid: list[tuple[int, tuple[dict[str, Any], ...]]] = []
    for group in combinations(ordered, 4):
        endpoints = [endpoint for row in group for endpoint in (row["start_frame"], row["goal_frame"])]
        if len(set(endpoints)) != 8 or len({row["bin"] for row in group}) < 2 or not any(row["separation"] >= 1.0 for row in group):
            continue
        valid.append((-len({row["bin"] for row in group}), group))
    if not valid:
        return None
    _, group = min(valid, key=lambda value: (value[0], tuple(row["hash_order"] for row in value[1])))
    labels = ("DEVELOPMENT_PAIR", "HELDOUT_PAIR_1", "HELDOUT_PAIR_2", "HELDOUT_PAIR_3")
    return [{"label": label, **row} for label, row in zip(labels, group)]


def freeze_pool(certified: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    qualified = [row for row in certified if row["classification"] == "DIRECT_SAFE_PAIR_QUALIFIED"]
    selected = select_registry(certified) if len(qualified) >= 6 else None
    reasons = []
    if len(qualified) < 6: reasons.append("fewer_than_6_direct_safe_pair_qualified")
    if selected is None and len(qualified) >= 6: reasons.append("no_4_endpoint_disjoint_diverse_registry")
    gate = {"pair_pool_gate": "PASS" if selected else "FAIL", "direct_safe_pair_qualified_count": len(qualified), "selected_registry_count": 0 if selected is None else len(selected), "failure_reasons": reasons, "selection_rule": "bin then hash order; endpoint-disjoint; maximize bin diversity; no rollout inputs", "rollout_authorized": bool(selected)}
    positions = camera_positions()
    compact_selected = [] if selected is None else [{**compact_pair(row), "start_position": positions[row["start_frame"]].tolist(), "goal_position": positions[row["goal_frame"]].tolist()} for row in selected]
    registry = {"status": "FROZEN" if selected else "NOT_AUTHORIZED", "registry": compact_selected, "registry_sha256": None, "map_identity": F63, "transforms_sha256": sha256(TRANSFORMS), "selection_code_sha256": None if selected is None else sha256(Path(__file__)), "reason": None if selected else "PAIR_POOL_GATE_FAIL"}
    registry_bytes = json.dumps(registry, indent=2, sort_keys=True).encode("utf-8")
    registry["registry_sha256"] = hashlib.sha256(registry_bytes).hexdigest()
    dump(GATE_ROOT / "frozen_rollout_registry/pair_pool_gate_result_v1_1.json", gate)
    dump(GATE_ROOT / "frozen_rollout_registry/frozen_direct_safe_rollout_registry_v1_1.json", registry)
    manifest = {"schema": "TUM_DIRECT_SAFE_BASELINE_GATE_V1_1", "pair_pool_gate": gate["pair_pool_gate"], "states": {label: {"state": "NOT_STARTED" if selected else "NOT_AUTHORIZED", "pair": next((row for row in (selected or []) if row["label"] == label), None)} for label in ("DEVELOPMENT_PAIR", "HELDOUT_PAIR_1", "HELDOUT_PAIR_2", "HELDOUT_PAIR_3")}}
    dump(GATE_ROOT / "manifests/run_manifest.json", manifest)
    return gate, registry


def write_not_authorized_outputs(gate: dict[str, Any], registry: dict[str, Any]) -> None:
    if gate["pair_pool_gate"] == "PASS":
        return
    baseline = {"status": "NOT_AUTHORIZED", "scientific_rollout_count": 0, "reason": "PAIR_POOL_GATE_FAIL", "rollouts": []}
    cert = {"status": "NOT_AUTHORIZED", "certified_robust_overlap_count": 0, "proxy_only_stop_count": 0, "numerically_indeterminate_count": 0, "reason": "PAIR_POOL_GATE_FAIL"}
    viability = {"status": "TUM_DIRECT_SAFE_PAIR_POOL_INSUFFICIENT_WITHIN_PREREGISTERED_SEARCH_BUDGET", "final_tum_decision": "CLOSE_TUM_NAVIGATION_BENCHMARK_KEEP_SAFETY_CASE_STUDY", "scientific_rollout_authorized": False, "scientific_rollout_count": 0, "reason": gate["failure_reasons"]}
    dump(GATE_ROOT / "baseline_rollouts/baseline_rollout_summary_v1_1.json", baseline)
    dump(GATE_ROOT / "baseline_certification/baseline_float64_certification_summary_v1_1.json", cert)
    dump(GATE_ROOT / "decision/baseline_viability_result_v1_1.json", viability)


def run_geometry_gate() -> dict[str, Any]:
    ensure_root()
    identity_result = identity()
    if identity_result["status"] != "PASS":
        raise RuntimeError("BLOCKED_BY_TUM_DIRECT_SAFE_GATE_IDENTITY_MISMATCH")
    query = FullMapQuery()
    endpoints, endpoint_summary = inventory(query)
    bins, candidate_summary = candidate_inventory(endpoints)
    coarse, coarse_summary = coarse_screen(query, bins)
    dense, dense_summary = dense_qualification(query, coarse)
    certified, certification_summary = float64_certification(dense)
    gate, registry = freeze_pool(certified)
    write_not_authorized_outputs(gate, registry)
    return {"identity": identity_result, "endpoints": endpoint_summary, "candidates": candidate_summary, "coarse": coarse_summary, "dense": dense_summary, "certification": certification_summary, "gate": gate, "registry": registry}
