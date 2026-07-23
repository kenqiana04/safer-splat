#!/usr/bin/env python3
"""Independently certify full-map selected candidates in float64."""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path("/disk1/zlab/maintenance_records/tum_splatam_g1_boundary_dt_forensics_v1")
MAP = Path("/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/splatam/canonical_export/export_a")
RADIUS = 0.015


def rotation(q: np.ndarray) -> np.ndarray:
    w, x, y, z = q / np.linalg.norm(q)
    return np.array([[1-2*(y*y+z*z), 2*(x*y-z*w), 2*(x*z+y*w)], [2*(x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]], dtype=np.float64)


def solve(a: np.ndarray, z: np.ndarray, newton: bool) -> tuple[np.ndarray, float, float]:
    a2 = a * a
    f = lambda lam: float(np.sum((a*z/(lam+a2))**2) - 1.0)
    inside = float(np.sum((z/a)**2)) < 1.0
    lo, hi = ((-float(a2.min()) * (1.0-1e-14), 0.0) if inside else (0.0, 1.0))
    while not inside and f(hi) > 0.0:
        hi *= 2.0
    lam = (lo + hi) / 2.0
    for _ in range(160):
        if newton:
            val = f(lam)
            deriv = -2.0 * float(np.sum((a*z)**2 / (lam+a2)**3))
            candidate = lam - val / deriv
            if lo < candidate < hi:
                lam = candidate
        if f(lam) > 0.0:
            lo = lam
        else:
            hi = lam
        lam = (lo + hi) / 2.0
    closest = a2*z/(lam+a2)
    return closest, abs(f(lam)), abs(float(np.sum((closest/a)**2)-1.0))


def reference(point: np.ndarray, index: int, means: np.ndarray, scales: np.ndarray, quats: np.ndarray) -> dict[str, object]:
    mean, axes, q = means[index].astype(np.float64), scales[index].astype(np.float64), quats[index].astype(np.float64)
    z = rotation(q).T @ (point.astype(np.float64)-mean)
    phi = 1.0 if float(np.sum((z/axes)**2)) >= 1.0 else -1.0
    ya, ka, sa = solve(axes, z, False)
    yb, kb, sb = solve(axes, z, True)
    ha = phi*float(np.sum((ya-z)**2))-RADIUS**2
    hb = phi*float(np.sum((yb-z)**2))-RADIUS**2
    tau = max(1e-12, 10*abs(ha-hb), 10*max(ka, kb))
    return {"index": index, "h_ref_a": ha, "h_ref_b": hb, "kkt_residual_a": ka, "kkt_residual_b": kb, "surface_residual_a": sa, "surface_residual_b": sb, "tau_ref": tau, "classification": "ROBUST_OVERLAP" if ha < -tau else "ROBUST_SAFE" if ha > tau else "NUMERICALLY_INDETERMINATE", "closest_point_a": (rotation(q)@ya+mean).tolist(), "phi": phi}


def main() -> None:
    out = ROOT / "float64_reference"; out.mkdir(parents=True, exist_ok=True)
    states = np.fromfile(ROOT / "trajectory_recovery" / "trajectory_states.npy", dtype=np.float32).reshape(-1, 6)
    full = json.loads((ROOT / "fullmap_queries" / "event_window_fullmap.json").read_text(encoding="utf-8"))
    shadow = list(csv.DictReader((ROOT / "dt_h1_h2_h3" / "shadow_h1_h2_h3_per_step.csv").open(encoding="utf-8")))
    means = np.load(MAP / "means_world_m.npy", mmap_mode="r")
    scales = np.load(MAP / "scales_linear_m.npy", mmap_mode="r")
    quats = np.load(MAP / "quaternions_wxyz.npy", mmap_mode="r")
    event_rows: list[dict[str, object]] = []
    for row in full:
        candidates = set(row["top32_indices"]) | set(row["tie_indices_exact"]) | {row["active_index"]}
        refs = [reference(np.asarray(row["position"]), int(index), means, scales, quats) for index in sorted(candidates)]
        active_ref = next(item for item in refs if item["index"] == row["active_index"])
        event_rows.append({"step": row["step"], "state_label": row["state_label"], "active_index": row["active_index"], "official_float32_h": row["h"], "active_reference": active_ref, "candidate_references": refs})
    trajectory_rows: list[dict[str, object]] = []
    for row in shadow:
        k = int(row["step"])
        ref = reference(states[k, :3], int(row["current_active"]), means, scales, quats)
        trajectory_rows.append({"step": k, "active_index": int(row["current_active"]), "official_float32_h": float(row["current_h"]), "reference": ref})
    terminal = next(row for row in event_rows if row["step"] == 773 and row["state_label"] == "x_k")
    terminal_ref = terminal["active_reference"]
    # The shadow H script has controls through k=772, while the terminal x_773
    # was measured after the final transition and is supplied by the full-map
    # event replay rather than by a nonexistent control row.
    trajectory_rows.append({"step": 773, "active_index": terminal["active_index"], "official_float32_h": terminal["official_float32_h"], "reference": terminal_ref})
    first_overlap = next((row for row in trajectory_rows if row["reference"]["classification"] == "ROBUST_OVERLAP"), None)
    first_indeterminate = next((row for row in trajectory_rows if row["reference"]["classification"] == "NUMERICALLY_INDETERMINATE"), None)
    payload = {"reference_a": "float64 safeguarded KKT bisection", "reference_b": "float64 safeguarded Newton+bisection", "radius": RADIUS, "event_window": [740,773], "event_rows": event_rows, "terminal": terminal, "first_robust_overlap_step": None if first_overlap is None else first_overlap["step"], "first_indeterminate_step": None if first_indeterminate is None else first_indeterminate["step"], "trajectory_current_state_rows": trajectory_rows}
    (out / "float64_reference_full.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    summary = {"terminal_active_index": terminal["active_index"], "terminal_h_ref_a": terminal_ref["h_ref_a"], "terminal_h_ref_b": terminal_ref["h_ref_b"], "terminal_tau_ref": terminal_ref["tau_ref"], "terminal_classification": terminal_ref["classification"], "terminal_official_float32_h": terminal["official_float32_h"], "terminal_official_error": terminal["official_float32_h"]-terminal_ref["h_ref_a"], "terminal_kkt_residual_max": max(terminal_ref["kkt_residual_a"], terminal_ref["kkt_residual_b"]), "terminal_surface_residual_max": max(terminal_ref["surface_residual_a"], terminal_ref["surface_residual_b"]), "first_robust_overlap_step": None if first_overlap is None else first_overlap["step"], "first_indeterminate_step": None if first_indeterminate is None else first_indeterminate["step"]}
    (out / "float64_reference_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
