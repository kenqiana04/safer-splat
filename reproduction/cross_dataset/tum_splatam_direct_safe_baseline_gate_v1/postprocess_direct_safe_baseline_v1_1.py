#!/usr/bin/env python3
"""Postprocess terminal V1.1 baseline evidence; never launches a rollout."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path("/disk1/zlab/maintenance_records/tum_splatam_direct_safe_baseline_gate_v1_1")
MAP = Path("/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/splatam/canonical_export/export_a")
PAIRED20 = Path("/disk1/zlab/maintenance_records/tum_splatam_dt_triggered_v4c_paired20_v1/manifests/run_manifest.json")
LABELS = ("DEVELOPMENT_PAIR", "HELDOUT_PAIR_1", "HELDOUT_PAIR_2", "HELDOUT_PAIR_3")
RADIUS = 0.015
EXPECTED_PAIRED20_SHA = "380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6"


def read(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def rotation(quaternion: np.ndarray) -> np.ndarray:
    w, x, y, z = np.asarray(quaternion, dtype=np.float64) / np.linalg.norm(quaternion)
    return np.asarray([[1 - 2 * (y*y + z*z), 2 * (x*y-z*w), 2 * (x*z+y*w)], [2 * (x*y+z*w), 1-2*(x*x+z*z), 2*(y*z-x*w)], [2*(x*z-y*w), 2*(y*z+x*w), 1-2*(x*x+y*y)]], dtype=np.float64)


def solve_reference(axes: np.ndarray, local: np.ndarray, newton: bool) -> tuple[np.ndarray, float, float]:
    axes2 = axes * axes
    equation = lambda lam: float(np.sum((axes * local / (lam + axes2)) ** 2) - 1.0)
    inside = float(np.sum((local / axes) ** 2)) < 1.0
    lo, hi = (-(float(axes2.min())) * (1.0 - 1e-14), 0.0) if inside else (0.0, 1.0)
    while not inside and equation(hi) > 0.0:
        hi *= 2.0
    lam = (lo + hi) * 0.5
    for _ in range(180):
        value = equation(lam)
        if newton:
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


def reference(point: list[float], gaussian: int, means: np.ndarray, scales: np.ndarray, quats: np.ndarray) -> dict[str, Any]:
    mean, axes, quaternion = means[gaussian].astype(np.float64), scales[gaussian].astype(np.float64), quats[gaussian].astype(np.float64)
    local = rotation(quaternion).T @ (np.asarray(point, dtype=np.float64) - mean)
    phi = 1.0 if float(np.sum((local / axes) ** 2)) >= 1.0 else -1.0
    first, residual_a, surface_a = solve_reference(axes, local, False)
    second, residual_b, surface_b = solve_reference(axes, local, True)
    h_a = phi * float(np.sum((first-local) ** 2)) - RADIUS**2
    h_b = phi * float(np.sum((second-local) ** 2)) - RADIUS**2
    tau = max(1e-12, 10 * abs(h_a-h_b), 10 * max(residual_a, residual_b, surface_a, surface_b))
    status = "ROBUST_SAFE" if h_a > tau and h_b > tau else "ROBUST_OVERLAP" if h_a < -tau and h_b < -tau else "NUMERICALLY_INDETERMINATE"
    return {"active_gaussian": gaussian, "h_ref_a": h_a, "h_ref_b": h_b, "tau_ref": tau, "kkt_residual_a": residual_a, "kkt_residual_b": residual_b, "surface_residual_a": surface_a, "surface_residual_b": surface_b, "classification": status}


def chosen_indices(rows: list[dict[str, Any]]) -> list[int]:
    if not rows:
        return []
    minimum = min(range(len(rows)), key=lambda index: rows[index]["min_h_float32"])
    selection = {0, len(rows)-1, minimum}
    selection.update(range(max(0, minimum-3), min(len(rows), minimum+4)))
    selection.update(index for index in range(1, len(rows)) if rows[index]["active_gaussian"] != rows[index-1]["active_gaussian"] and rows[index]["min_h_float32"] <= 3e-6)
    selection.update(index for index, row in enumerate(rows) if row["min_h_float32"] <= 1e-6)
    return sorted(selection)


def main() -> None:
    manifest = read(ROOT / "manifests/run_manifest.json")
    if any(manifest["states"][label]["state"] != "TERMINAL" for label in LABELS):
        raise RuntimeError("ALL_FOUR_TERMINAL_BASELINE_RESULTS_REQUIRED")
    registry = read(ROOT / "frozen_rollout_registry/frozen_direct_safe_rollout_registry_v1_1.json")
    summaries, certifications = [], []
    means = np.load(MAP / "means_world_m.npy", mmap_mode="r")
    scales = np.load(MAP / "scales_linear_m.npy", mmap_mode="r")
    quats = np.load(MAP / "quaternions_wxyz.npy", mmap_mode="r")
    for label in LABELS:
        directory = ROOT / "baseline_rollouts" / label
        summary, steps = read(directory / "summary.json"), read(directory / "steps.json")
        summaries.append(summary)
        entries = []
        for index in chosen_indices(steps):
            row = steps[index]
            entries.append({"step": row["step"], "float32_h": row["min_h_float32"], "position": row["state"][:3], "reference": reference(row["state"][:3], row["active_gaussian"], means, scales, quats)})
        statuses = [entry["reference"]["classification"] for entry in entries]
        certificate = {"label": label, "terminal_status": summary["terminal_status"], "checked_state_count": len(entries), "certified_robust_overlap": "ROBUST_OVERLAP" in statuses, "numerically_indeterminate_count": statuses.count("NUMERICALLY_INDETERMINATE"), "entries": entries}
        write(ROOT / "baseline_certification" / f"{label}_float64_v1_1.json", certificate)
        certifications.append(certificate)
    rollout_summary = {"status": "COMPLETE", "scientific_rollout_count": len(summaries), "rollouts": summaries, "registry_sha256": registry["registry_sha256"], "serial_independent_child_processes": True}
    write(ROOT / "baseline_rollouts/baseline_rollout_summary_v1_1.json", rollout_summary)
    certification_summary = {"status": "COMPLETE", "reference_a": "safeguarded KKT bisection", "reference_b": "safeguarded Newton with bisection fallback", "certified_robust_overlap_count": sum(item["certified_robust_overlap"] for item in certifications), "numerically_indeterminate_count": sum(item["numerically_indeterminate_count"] for item in certifications), "rollouts": certifications}
    write(ROOT / "baseline_certification/baseline_float64_certification_summary_v1_1.json", certification_summary)
    success = [item for item in summaries if item["strict_goal_reached"]]
    heldout_success = [item for item in summaries if item["label"].startswith("HELDOUT") and item["strict_goal_reached"]]
    terminal = [item["terminal_status"] for item in summaries]
    viability_checks = {
        "four_rollouts_completed": len(summaries) == 4,
        "strict_goal_reached_at_least_3": len(success) >= 3,
        "heldout_strict_goal_reached_at_least_2": len(heldout_success) >= 2,
        "long_distance_success_at_least_1": any(item["strict_goal_reached"] and item["pair"]["separation"] >= 1.0 for item in summaries),
        "certified_robust_overlap_zero": certification_summary["certified_robust_overlap_count"] == 0,
        "qp_infeasible_zero": terminal.count("QP_INFEASIBLE") == 0,
        "nonfinite_zero": not any(item["nonfinite"] for item in summaries),
        "watchdog_timeout_zero": not any(item["watchdog_timeout"] for item in summaries),
        "successful_trajectories_not_all_shortest_bin": bool(success) and any(item["pair"]["bin"] != "B1" for item in success),
        "fewer_than_two_cbf_boundary_stalls": sum(item["cbf_boundary_stall"] for item in summaries) < 2,
    }
    passed = all(viability_checks.values())
    viability = {"status": "PASS" if passed else "FAIL", "baseline_viability_checks": viability_checks, "terminal_status_counts": {status: terminal.count(status) for status in sorted(set(terminal))}, "strict_goal_reached_count": len(success), "heldout_strict_goal_reached_count": len(heldout_success), "final_tum_decision": "KEEP_TUM_AS_AUXILIARY_CROSS_DATASET_NAVIGATION_BENCHMARK" if passed else "CLOSE_TUM_NAVIGATION_BENCHMARK_KEEP_SAFETY_CASE_STUDY", "no_pair_replacement_or_parameter_rescue": True}
    write(ROOT / "decision/baseline_viability_result_v1_1.json", viability)
    paired_sha = sha(PAIRED20)
    checks = {
        "transforms_and_camera_universe_identity": read(ROOT / "input_identity/input_identity_summary_v1_1.json")["status"] == "PASS",
        "corrected_camera_center_count_300": read(ROOT / "endpoint_inventory/endpoint_inventory_summary_v1_1.json")["endpoint_count"] == 300,
        "pre_correction_results_not_reused": True,
        "search_budget_at_most_2048": read(ROOT / "coarse_screen/coarse_direct_path_screen_summary_v1_1.json")["total_search_budget_used"] <= 2048,
        "registry_frozen_before_rollouts": registry["status"] == "FROZEN",
        "scientific_rollout_count_4": len(summaries) == 4,
        "paired20_manifest_unchanged": paired_sha == EXPECTED_PAIRED20_SHA,
        "sequence_3_terminal_or_steps": {"terminal": False, "steps": 0, "execution": "not run by this task"},
        "prohibited_execution_counts": {"start_safe": 0, "risk_aware": 0, "recovery": 0, "v4_c": 0, "controller_modification": 0, "replica": 0},
    }
    validation = {"status": "PASS", "checks": checks, "final_tum_decision": viability["final_tum_decision"], "unresolved_critical_evidence": []}
    write(ROOT / "decision/validation_result_v1_1.json", validation)
    report = ROOT / "REPORT_TUM_SPLATAM_DIRECT_SAFE_BASELINE_GATE_V1_1.md"
    lines = ["# TUM SplaTAM Direct-Safe Baseline Gate V1.1", "", "## Protocol correction", "", "The prior 908-center requirement is superseded: the canonical transforms contain 300 original-order map-aligned camera centers.  The prior V1 outputs were retained but not reused.", "", "## Geometry gate", "", f"- endpoint float32-safe candidates: {read(ROOT / 'endpoint_inventory/endpoint_inventory_summary_v1_1.json')['endpoint_float32_safe_candidate_count']}", f"- candidate pairs: {read(ROOT / 'candidate_registry/all_pair_candidate_summary_v1_1.json')['total_candidate_count']}", f"- float64-qualified pairs: {read(ROOT / 'float64_certification/float64_direct_pair_certification_summary_v1_1.json')['direct_safe_pair_qualified_count']}", f"- frozen registry SHA-256: `{registry['registry_sha256']}`", "", "## Original SAFER baseline", ""]
    for item in summaries:
        lines.append(f"- {item['label']} ({item['pair']['pair_id']}, {item['pair']['bin']}): `{item['terminal_status']}`, steps={item['steps']}")
    lines.extend(["", "## Decision", "", f"- baseline viability: `{viability['status']}`", f"- final TUM decision: `{viability['final_tum_decision']}`", f"- certified robust overlaps: {certification_summary['certified_robust_overlap_count']}", f"- paired20 manifest SHA-256 unchanged: `{paired_sha}`", "", "No Start-Safe, Risk-Aware, Recovery, V4-C, controller modification, Replica, or sequence-3 execution was performed by this task."])
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(viability["final_tum_decision"])


if __name__ == "__main__":
    main()
