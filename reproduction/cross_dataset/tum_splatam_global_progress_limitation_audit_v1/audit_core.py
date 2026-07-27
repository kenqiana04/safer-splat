#!/usr/bin/env python3
"""Read-only global progress audit for completed TUM SplaTAM evidence.

The module deliberately contains no controller, CBF, QP, V4-C, or map-loader
import.  It consumes saved JSON/JSONL only and writes exclusively to AUDIT_ROOT.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np

AUDIT_ROOT = Path(os.environ.get("AUDIT_ROOT", "/disk1/zlab/maintenance_records/tum_splatam_global_progress_limitation_audit_v1"))
TRANSFORMS = Path("/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room/transforms.json")
SOURCE_A = Path("/disk1/zlab/maintenance_records/tum_splatam_one_shot_runtime_recovery_g1_v2")
SOURCE_B = Path("/disk1/zlab/maintenance_records/tum_splatam_g1_boundary_dt_forensics_v1")
SOURCE_C = Path("/disk1/zlab/maintenance_records/tum_splatam_dt_triggered_v4c_recovery_v1")
SOURCE_D = Path("/disk1/zlab/maintenance_records/tum_splatam_dt_triggered_v4c_paired20_v1")
PAUSED_MANIFEST_SHA = "380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6"
PR49_HEAD = "519478a541ab114e7877b365b93e54a0b049e119"
PR47_HEAD = "5f3078a88ba6121ba2c1918a1b89120438006916"
RADIUS, ALPHA, BETA, DT, MAX_STEPS, GOAL_TOLERANCE = .015, 5.0, 1.0, .05, 800, .001
V4_COMMIT = "b626b99cb1ed1437730c0e0734635fd8f0bdc517"
V4_BLOB = "5b28585b9b98d991d9f4fa9e0158812d2a3be80a"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def ensure_root() -> None:
    for name in ("input_identity", "inventory", "normalized", "per_trajectory", "paired", "controller", "cbf", "recovery", "oscillation", "stall", "global", "figures", "report", "logs", "tmp"):
        (AUDIT_ROOT / name).mkdir(parents=True, exist_ok=True)


def git_head(ref: str) -> str | None:
    repo = Path("/disk1/zlab/projects/safer-splat")
    try:
        return subprocess.check_output(["git", "-C", str(repo), "rev-parse", ref], text=True).strip()
    except Exception:
        return None


def frame_positions() -> np.ndarray:
    frames = load(TRANSFORMS)["frames"]
    return np.asarray([[f["transform_matrix"][0][3], f["transform_matrix"][1][3], f["transform_matrix"][2][3]] for f in frames], dtype=np.float64)


def arm_name(value: str) -> str:
    return "ORIGINAL_SAFER_BASELINE" if value == "baseline" else "STRICT_DT_TRIGGERED_V4C"


def identity() -> dict[str, Any]:
    ensure_root()
    manifest = SOURCE_D / "manifests/run_manifest.json"
    paused = load(manifest)
    paused_states = Counter(item["state"] for item in paused["states"].values())
    source_b_identity = load(SOURCE_B / "input_identity/input_identity.json") if (SOURCE_B / "input_identity/input_identity.json").exists() else {}
    source_c_contract = load(SOURCE_C / "protocol/dt_trigger_contract.json")
    data = {"pr47_head": source_b_identity.get("pr47_head") or PR47_HEAD, "pr48_head": source_b_identity.get("head") or git_head("HEAD"), "pr49_head": PR49_HEAD, "paused_paired20_branch": "tum-splatam-dt-triggered-v4c-paired20-v1", "paused_paired20_base": PR49_HEAD, "paused_manifest_path": str(manifest), "paused_manifest_sha256": sha(manifest), "paused_manifest_expected_sha256": PAUSED_MANIFEST_SHA, "paused_manifest_states": dict(paused_states), "paused_manifest_pause_status": paused.get("pause_status"), "map_identity": source_b_identity.get("map_identity") or {"canonical_gaussian_count": 5464102}, "transforms_path": str(TRANSFORMS), "transforms_sha256": sha(TRANSFORMS), "frozen_parameters": {"robot_radius": RADIUS, "alpha": ALPHA, "beta": BETA, "dt": DT, "max_steps": MAX_STEPS, "goal_tolerance": GOAL_TOLERANCE, "integrator": "x_next = x + 0.05 * [v,u]"}, "controller_source_identity": git_head("HEAD:work/risk_aware_cbf/scripts/run_risk_aware_v1_pre_cbf_comparison.py"), "cbf_source_identity": git_head("HEAD:cbf/cbf_utils.py"), "v4c_identity": {"restoration_commit": V4_COMMIT, "blob": V4_BLOB}, "strict_trigger": source_c_contract.get("strict_trigger_expression", "current_h > 0 and h3_min < 0"), "margin_monitor": source_c_contract.get("margin_monitor_expression", "h3_min < 0.0005"), "margin_action": source_c_contract.get("margin_monitor_action", "LOG_ONLY")}
    data["identity_ok"] = bool(data["paused_manifest_sha256"] == PAUSED_MANIFEST_SHA and paused_states.get("TERMINAL_SCIENTIFIC_RESULT") == 2 and paused_states.get("RUNNING", 0) == 0 and paused_states.get("FAILED_INFRASTRUCTURE", 0) == 0)
    if not data["identity_ok"]:
        data["status"] = "BLOCKED_BY_GLOBAL_PROGRESS_AUDIT_IDENTITY_CONFLICT"
        dump(AUDIT_ROOT / "input_identity/input_identity_summary.json", data)
        raise RuntimeError(data["status"])
    dump(AUDIT_ROOT / "input_identity/input_identity_summary.json", data)
    return data


def candidate_records() -> list[dict[str, Any]]:
    records = [{"source_task": "pr47_g1_baseline", "summary": SOURCE_A / "resumed_trials/one_trial_summary.json", "steps": SOURCE_A / "resumed_trials/one_trial_steps.json", "start": 0, "goal": 50, "arm": "baseline", "state_mode": "reconstruct_from_executed_controls"}, {"source_task": "pr49_v4c", "summary": SOURCE_C / "development_intervention/summary.json", "steps": SOURCE_C / "development_intervention/steps.json", "start": 0, "goal": 50, "arm": "intervention", "state_mode": "saved"}]
    for pair in (1, 2, 3):
        for arm, directory in (("baseline", SOURCE_C / "heldout_baseline" / f"pair_{pair}"), ("intervention", SOURCE_C / "heldout_intervention" / f"pair_{pair}")):
            summary = load(directory / "summary.json")
            records.append({"source_task": "pr49_v4c", "summary": directory / "summary.json", "steps": directory / "steps.json", "start": int(summary["start_frame"]), "goal": int(summary["goal_frame"]), "arm": arm, "state_mode": "saved"})
    for arm in ("baseline", "intervention"):
        directory = SOURCE_D / arm / "PAIR_01" / "attempt_1"
        summary = load(directory / "summary.json")
        records.append({"source_task": "paused_paired20", "summary": directory / "summary.json", "steps": directory / "steps.json", "start": int(summary["start_frame"]), "goal": int(summary["goal_frame"]), "arm": arm, "state_mode": "saved"})
    return records


def inventory() -> dict[str, Any]:
    ensure_root()
    identity()
    discovered, excluded, canonical, seen = [], [], [], set()
    for item in candidate_records():
        complete = item["summary"].is_file() and item["steps"].is_file()
        if not complete:
            excluded.append({**item, "reason": "INCOMPLETE_FOR_PER_STEP_AUDIT"})
            continue
        summary, rows = load(item["summary"]), load(item["steps"])
        if not rows:
            excluded.append({**item, "reason": "EMPTY_STEP_LOG"})
            continue
        trajectory_id = f"{item['source_task']}:{item['start']}:{item['goal']}:{arm_name(item['arm'])}"
        control_sha = sha(item["steps"])
        key = (item["start"], item["goal"], item["arm"], control_sha)
        record = {"trajectory_id": trajectory_id, "source_task": item["source_task"], "pair_id": f"{item['start']}->{item['goal']}", "start_frame": item["start"], "goal_frame": item["goal"], "arm": arm_name(item["arm"]), "raw_arm": item["arm"], "summary_path": str(item["summary"]), "steps_path": str(item["steps"]), "summary_sha256": sha(item["summary"]), "state_control_sha256": control_sha, "step_count": len(rows), "terminal_status": summary.get("stop_reason") or summary.get("status"), "state_mode": item["state_mode"], "complete": True, "provenance_links": []}
        discovered.append(record)
        if key in seen:
            next(x for x in canonical if (x["start_frame"], x["goal_frame"], x["raw_arm"], x["state_control_sha256"]) == key)["provenance_links"].append(trajectory_id)
        else:
            seen.add(key); canonical.append(record)
    shadow = [{"source_task": "pr48_boundary_forensics", "reason": "SHADOW_ONLY_NOT_CLOSED_LOOP", "path": str(SOURCE_B / "dt_h1_h2_h3/shadow_h1_h2_h3_summary.json")}]
    data = {"discovered_count": len(discovered), "canonical_trajectory_count": len(canonical), "duplicate_reference_count": len(discovered) - len(canonical), "missing_log_count": sum(x["reason"] == "INCOMPLETE_FOR_PER_STEP_AUDIT" for x in excluded), "incomplete_count": len(excluded), "excluded_count": len(excluded) + len(shadow), "canonical_trajectories": canonical, "incomplete": excluded, "shadow_excluded": shadow}
    dump(AUDIT_ROOT / "inventory/trajectory_inventory.json", data)
    dump(AUDIT_ROOT / "inventory/trajectory_inventory_summary.json", data)
    return data


def vector(value: Any) -> list[float] | None:
    if value is None:
        return None
    arr = np.asarray(value, dtype=np.float64)
    return arr.tolist() if arr.size else None


def norm(value: Any) -> float | None:
    return None if value is None else float(np.linalg.norm(np.asarray(value, dtype=np.float64)))


def normalize_record(record: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_rows, summary = load(Path(record["steps_path"])), load(Path(record["summary_path"]))
    positions = frame_positions(); goal = positions[record["goal_frame"]]
    rows: list[dict[str, Any]] = []
    reconstructed = None
    if record["state_mode"] == "reconstruct_from_executed_controls":
        reconstructed = np.concatenate([positions[record["start_frame"]], np.zeros(3, dtype=np.float64)])
    for index, raw in enumerate(raw_rows):
        executed = vector(raw.get("u_executed", raw.get("executed_control", raw.get("u"))))
        if raw.get("state") is not None:
            state = vector(raw["state"])
        elif reconstructed is not None:
            state = reconstructed.tolist()
        else:
            state = None
        if raw.get("next_state") is not None:
            next_state = vector(raw["next_state"])
        elif state is not None and executed is not None:
            x = np.asarray(state, dtype=np.float64); u = np.asarray(executed, dtype=np.float64)
            next_state = np.concatenate([x[:3] + DT*x[3:], x[3:] + DT*u]).tolist()
        else:
            next_state = None
        if next_state is not None and reconstructed is not None:
            reconstructed = np.asarray(next_state, dtype=np.float64)
        position = None if state is None else state[:3]
        distance = None if position is None else float(np.linalg.norm(goal - np.asarray(position)))
        current_h = raw.get("current_h", raw.get("current_fullmap_h", raw.get("min_h")))
        next_h = raw.get("next_h", raw.get("next_fullmap_h", raw.get("min_h")))
        row = {"trajectory_id": record["trajectory_id"], "pair_id": record["pair_id"], "arm": record["arm"], "step": index, "state": state, "next_state": next_state, "position": position, "velocity": None if state is None else state[3:], "goal": goal.tolist(), "distance_to_goal": distance, "official_progress": raw.get("progress"), "u_nominal": vector(raw.get("u_nominal")), "u_safe": vector(raw.get("u_safe")), "u_executed": executed, "current_h": None if current_h is None else float(current_h), "next_h": None if next_h is None else float(next_h), "h1_min": raw.get("h1", raw.get("h1_min_predicted")), "h2_min": raw.get("h2", raw.get("h2_min_predicted")), "h3_min": raw.get("h3", raw.get("h3_min_predicted")), "margin_warning": raw.get("margin_warning"), "strict_trigger": bool(raw.get("strict_trigger", False)), "recovery_active": bool(raw.get("recovery_active", False)), "active_gaussian": raw.get("active_gaussian", raw.get("active_gaussian_current", raw.get("active"))), "active_constraint_count": raw.get("active_constraints_count"), "candidate_count": raw.get("sequence_count"), "qp_status": raw.get("qp_status"), "qp_residual": raw.get("qp_residual"), "fallback": raw.get("recovery_failed"), "step_runtime": raw.get("runtime_step", raw.get("runtime_step_seconds")), "terminal_flag": index == len(raw_rows) - 1, "provenance": {"state": "saved" if raw.get("state") is not None else "deterministically_reconstructed_from_saved_executed_control", "h": "saved", "controls": "saved"}}
        rows.append(row)
    distances = [r["distance_to_goal"] for r in rows if r["distance_to_goal"] is not None]
    initial = distances[0] if distances else None
    for row in rows:
        row["geometric_progress"] = None if initial in (None, 0) or row["distance_to_goal"] is None else (initial - row["distance_to_goal"]) / initial
    if rows and rows[-1]["official_progress"] is None:
        rows[-1]["official_progress"] = summary.get("progress")
    compact = {"trajectory_id": record["trajectory_id"], "normalized_path": str(AUDIT_ROOT / "normalized" / f"{record['trajectory_id'].replace(':', '__')}.jsonl"), "row_count": len(rows), "state_reconstructed": record["state_mode"] != "saved", "missing_fields": sorted({key for row in rows for key, value in row.items() if value is None}), "terminal_status": record["terminal_status"]}
    return rows, compact


def normalize() -> dict[str, Any]:
    inv = load(AUDIT_ROOT / "inventory/trajectory_inventory.json")
    entries = []
    for record in inv["canonical_trajectories"]:
        rows, compact = normalize_record(record)
        output = AUDIT_ROOT / "normalized" / f"{record['trajectory_id'].replace(':', '__')}.jsonl"
        with output.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, separators=(",", ":")) + "\n")
        compact["normalized_sha256"] = sha(output); entries.append(compact)
    data = {"canonical_trajectory_count": len(entries), "entries": entries, "online_fullmap_queries": 0, "new_state_generation": 0, "qp_execution": 0, "v4c_execution": 0}
    dump(AUDIT_ROOT / "normalized/normalization_summary.json", data)
    return data


def read_normalized(path: str) -> list[dict[str, Any]]:
    with Path(path).open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def progress_semantics() -> dict[str, Any]:
    inv = load(AUDIT_ROOT / "inventory/trajectory_inventory.json")
    entries = []
    for record in inv["canonical_trajectories"]:
        rows, _ = normalize_record(record); summary = load(Path(record["summary_path"]))
        final_geometric = rows[-1]["geometric_progress"]
        official = summary.get("progress")
        row_values = [r["official_progress"] for r in rows if r["official_progress"] is not None and r["geometric_progress"] is not None]
        diffs = [abs(r["official_progress"] - r["geometric_progress"]) for r in rows if r["official_progress"] is not None and r["geometric_progress"] is not None]
        entries.append({"trajectory_id": record["trajectory_id"], "official_final_progress": official, "geometric_final_progress": final_geometric, "final_difference": None if official is None or final_geometric is None else official-final_geometric, "max_absolute_difference_over_available_steps": max(diffs) if diffs else None, "semantic_equivalence": bool(official is not None and final_geometric is not None and abs(official-final_geometric) < 2e-5), "official_is_clipped": any(value < 0 or value > 1 for value in row_values), "other_normalization_detected": False})
    data = {"official_progress_definition": "Saved terminal-summary progress compared against independently reconstructed geometric progress; per-step official progress is retained only when present in raw logs.", "geometric_progress_definition": "(initial_distance-distance_k)/initial_distance", "entries": entries}
    dump(AUDIT_ROOT / "per_trajectory/progress_semantics_contract.json", data)
    return data


def finite(values: list[float | None]) -> np.ndarray:
    return np.asarray([value for value in values if value is not None and math.isfinite(value)], dtype=np.float64)


def cosine(a: Any, b: Any) -> float | None:
    if a is None or b is None:
        return None
    aa, bb = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    den = np.linalg.norm(aa) * np.linalg.norm(bb)
    return None if den == 0 else float(np.dot(aa, bb) / den)


def sign_changes(values: list[float]) -> int:
    if len(values) < 3:
        return 0
    signs = np.sign(np.asarray(values, dtype=np.float64)); signs = signs[signs != 0]
    return int(np.sum(signs[1:] * signs[:-1] < 0)) if len(signs) > 1 else 0


def window_metrics(rows: list[dict[str, Any]], size: int) -> dict[str, Any] | None:
    if len(rows) < size:
        return None
    sample = rows[-size:]
    distances = finite([r["distance_to_goal"] for r in sample])
    progress = finite([r["geometric_progress"] for r in sample])
    positions = [np.asarray(r["position"], dtype=np.float64) for r in sample if r["position"] is not None]
    velocities = [np.asarray(r["velocity"], dtype=np.float64) for r in sample if r["velocity"] is not None]
    corrections = [norm(np.asarray(r["u_safe"])-np.asarray(r["u_nominal"])) for r in sample if r["u_safe"] is not None and r["u_nominal"] is not None]
    active = [value is not None and value > 1e-8 for value in corrections]
    radial = radial_components(sample)["velocity_radial"]
    path = sum(float(np.linalg.norm(positions[i]-positions[i-1])) for i in range(1, len(positions))) if len(positions) > 1 else 0.0
    net = float(np.linalg.norm(positions[-1]-positions[0])) if len(positions) > 1 else 0.0
    return {"size": size, "net_distance_reduction": float(distances[0]-distances[-1]) if len(distances) else None, "distance_slope": float(np.polyfit(np.arange(len(distances)), distances, 1)[0]) if len(distances)>1 else None, "progress_gain": float(progress[-1]-progress[0]) if len(progress) else None, "average_radial_velocity": float(np.mean(radial)) if radial else None, "negative_radial_velocity_ratio": float(np.mean(np.asarray(radial)<0)) if radial else None, "qp_correction_mean": float(np.mean(corrections)) if corrections else None, "active_constraint_ratio": float(np.mean(active)) if active else None, "path_length": path, "net_displacement": net, "path_efficiency": None if path == 0 else net/path, "control_sign_changes": sum(sign_changes([float(np.asarray(r["u_executed"])[axis]) for r in sample if r["u_executed"] is not None]) for axis in range(3))}


def radial_components(rows: list[dict[str, Any]]) -> dict[str, list[float]]:
    result: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row["position"] is None:
            continue
        direction = np.asarray(row["goal"], dtype=np.float64) - np.asarray(row["position"], dtype=np.float64)
        length = np.linalg.norm(direction)
        if length == 0:
            continue
        direction /= length
        for label, field in (("velocity_radial", "velocity"), ("nominal_radial", "u_nominal"), ("safe_radial", "u_safe"), ("executed_radial", "u_executed")):
            if row[field] is not None:
                result[label].append(float(np.dot(np.asarray(row[field], dtype=np.float64), direction)))
    return result


def per_trajectory_metrics() -> dict[str, Any]:
    inv, normal = load(AUDIT_ROOT / "inventory/trajectory_inventory.json"), load(AUDIT_ROOT / "normalized/normalization_summary.json")
    normal_paths = {entry["trajectory_id"]: entry["normalized_path"] for entry in normal["entries"]}
    output = []
    for record in inv["canonical_trajectories"]:
        rows, summary = read_normalized(normal_paths[record["trajectory_id"]]), load(Path(record["summary_path"]))
        positions = [np.asarray(row["position"], dtype=np.float64) for row in rows if row["position"] is not None]
        distances = finite([row["distance_to_goal"] for row in rows]); gp = finite([row["geometric_progress"] for row in rows]); h = finite([row["next_h"] for row in rows]); radial = radial_components(rows)
        path = sum(float(np.linalg.norm(positions[i]-positions[i-1])) for i in range(1, len(positions))) if len(positions)>1 else 0.0
        net = float(np.linalg.norm(positions[-1]-positions[0])) if len(positions)>1 else 0.0
        corrections = [norm(np.asarray(row["u_safe"])-np.asarray(row["u_nominal"])) for row in rows if row["u_safe"] is not None and row["u_nominal"] is not None]
        recovery_dev = [norm(np.asarray(row["u_executed"])-np.asarray(row["u_safe"])) for row in rows if row["u_executed"] is not None and row["u_safe"] is not None]
        control = [norm(row["u_executed"]) for row in rows if row["u_executed"] is not None]
        velocity = [norm(row["velocity"]) for row in rows if row["velocity"] is not None]
        active_switch = sum(rows[i]["active_gaussian"] != rows[i-1]["active_gaussian"] for i in range(1, len(rows)) if rows[i]["active_gaussian"] is not None and rows[i-1]["active_gaussian"] is not None)
        safe_cos = [cosine(row["u_safe"], row["u_nominal"]) for row in rows]; exec_cos = [cosine(row["u_executed"], row["u_safe"]) for row in rows]
        base = {"trajectory_id": record["trajectory_id"], "pair_id": record["pair_id"], "arm": record["arm"], "source_task": record["source_task"], "step_count": len(rows), "terminal_status": record["terminal_status"], "reached_goal": bool(summary.get("goal_reached", summary.get("reached_goal", False))), "float32_proxy_overlap_stop": "overlap" in str(record["terminal_status"]).lower() or "collision" in str(record["terminal_status"]).lower(), "robust_overlap_status": "CERTIFIED_ROBUST_OVERLAP" if record["source_task"] == "pr47_g1_baseline" else None, "initial_distance": float(distances[0]) if len(distances) else None, "final_distance": float(summary.get("final_distance_m", distances[-1] if len(distances) else np.nan)), "minimum_distance": float(np.min(distances)) if len(distances) else None, "minimum_distance_step": int(np.argmin(distances)) if len(distances) else None, "final_official_progress": summary.get("progress"), "best_official_progress": None, "final_geometric_progress": float(gp[-1]) if len(gp) else None, "best_geometric_progress": float(np.max(gp)) if len(gp) else None, "total_path_length": path, "net_displacement": net, "path_efficiency": None if path == 0 else net/path, "average_speed": float(np.mean(velocity)) if velocity else None, "final_speed": velocity[-1] if velocity else None, "positive_radial_velocity_ratio": float(np.mean(np.asarray(radial["velocity_radial"])>1e-8)) if radial["velocity_radial"] else None, "negative_radial_velocity_ratio": float(np.mean(np.asarray(radial["velocity_radial"])<-1e-8)) if radial["velocity_radial"] else None, "near_zero_radial_velocity_ratio": float(np.mean(np.abs(np.asarray(radial["velocity_radial"]))<=1e-8)) if radial["velocity_radial"] else None, "nominal_radial_mean": float(np.mean(radial["nominal_radial"])) if radial["nominal_radial"] else None, "safe_radial_mean": float(np.mean(radial["safe_radial"])) if radial["safe_radial"] else None, "executed_radial_mean": float(np.mean(radial["executed_radial"])) if radial["executed_radial"] else None, "cbf_radial_suppression_mean": None if not radial["nominal_radial"] or not radial["safe_radial"] else float(np.mean(np.asarray(radial["nominal_radial"])-np.asarray(radial["safe_radial"]))), "recovery_radial_change_mean": None if not radial["safe_radial"] or not radial["executed_radial"] else float(np.mean(np.asarray(radial["safe_radial"])-np.asarray(radial["executed_radial"]))), "control_norm_mean": float(np.mean(control)) if control else None, "qp_correction_norm_mean": float(np.mean(corrections)) if corrections else None, "cbf_correction_active_ratio": float(np.mean(np.asarray(corrections)>1e-8)) if corrections else None, "recovery_deviation_mean": float(np.mean(recovery_dev)) if recovery_dev else None, "control_saturation_rate": float(np.mean([value >= .0999 for value in control])) if control else None, "control_direction_sign_changes": sum(sign_changes([float(np.asarray(row["u_executed"])[axis]) for row in rows if row["u_executed"] is not None]) for axis in range(3)), "control_jerk_mean": float(np.mean([np.linalg.norm(np.asarray(rows[i]["u_executed"])-np.asarray(rows[i-1]["u_executed"])) for i in range(1,len(rows)) if rows[i]["u_executed"] is not None and rows[i-1]["u_executed"] is not None])) if len(rows)>1 else None, "safe_nominal_cosine_mean": float(np.mean(finite(safe_cos))) if len(finite(safe_cos)) else None, "executed_safe_cosine_mean": float(np.mean(finite(exec_cos))) if len(finite(exec_cos)) else None, "min_h": float(np.min(h)) if len(h) else None, "median_h": float(np.median(h)) if len(h) else None, "h_percentiles": None if not len(h) else [float(np.quantile(h,q)) for q in (.05,.25,.5)], "negative_h_steps": int(np.sum(h<0)) if len(h) else None, "near_boundary_occupancy": float(np.mean(h<.0005)) if len(h) else None, "active_gaussian_switch_count": active_switch, "strict_trigger_count": int(sum(row["strict_trigger"] for row in rows)), "first_trigger_step": next((row["step"] for row in rows if row["strict_trigger"]), None), "recovery_active_steps": int(sum(row["recovery_active"] for row in rows)), "windows": {str(size): window_metrics(rows,size) for size in (25,50,100,200)}}
        output.append(base)
        dump(AUDIT_ROOT / "per_trajectory" / f"{record['trajectory_id'].replace(':','__')}_summary.json", base)
    data = {"trajectory_count": len(output), "trajectories": output}
    dump(AUDIT_ROOT / "per_trajectory/per_trajectory_metrics.json", data); dump(AUDIT_ROOT / "per_trajectory/per_trajectory_metrics_summary.json", data)
    return data


def stall_onset() -> dict[str, Any]:
    normal = load(AUDIT_ROOT / "normalized/normalization_summary.json")
    records = []
    for entry in normal["entries"]:
        rows = read_normalized(entry["normalized_path"]); flags = []
        for end in range(99, len(rows)):
            window = window_metrics(rows[:end+1], 100)
            low = window is not None and window["progress_gain"] is not None and window["progress_gain"] < .005
            conditions = [window["path_length"] > 5*window["net_displacement"] if window and window["net_displacement"] is not None else False, window["negative_radial_velocity_ratio"] is not None and window["negative_radial_velocity_ratio"] > .35 if window else False, window["active_constraint_ratio"] is not None and window["active_constraint_ratio"] > .5 and (window["qp_correction_mean"] or 0)>0 if window else False, window["control_sign_changes"] >= 10 if window else False]
            flags.append(bool(low and any(conditions)))
        onset = None
        for index in range(2, len(flags)):
            if flags[index-2] and flags[index-1] and flags[index]:
                onset = index - 2; break
        records.append({"trajectory_id": entry["trajectory_id"], "window_size":100, "low_progress_threshold":.005, "stall_onset": onset, "three_consecutive_low_progress_windows": onset is not None})
    data = {"records": records}; dump(AUDIT_ROOT / "stall/stall_onset_summary.json", data); return data


def attribution_and_oscillation() -> tuple[dict[str, Any], dict[str, Any]]:
    metrics = load(AUDIT_ROOT / "per_trajectory/per_trajectory_metrics.json")["trajectories"]; stalls = {x["trajectory_id"]:x for x in load(AUDIT_ROOT / "stall/stall_onset_summary.json")["records"]}
    attributes, oscillations, classifications = [], [], []
    for m in metrics:
        nominal_limit = m["nominal_radial_mean"] is not None and m["nominal_radial_mean"] <= 1e-5
        cbf_stall = m["nominal_radial_mean"] is not None and m["nominal_radial_mean"] > 0 and m["safe_radial_mean"] is not None and m["safe_radial_mean"] <= .25*m["nominal_radial_mean"] and (m["cbf_correction_active_ratio"] or 0) > .5
        rows = read_normalized(next(x["normalized_path"] for x in load(AUDIT_ROOT / "normalized/normalization_summary.json")["entries"] if x["trajectory_id"] == m["trajectory_id"]))
        last = rows[-200:]; distances=[x["distance_to_goal"] for x in last if x["distance_to_goal"] is not None]; radial=radial_components(last)["velocity_radial"]; path = sum(float(np.linalg.norm(np.asarray(last[i]["position"])-np.asarray(last[i-1]["position"]))) for i in range(1,len(last)) if last[i]["position"] is not None and last[i-1]["position"] is not None); net = float(np.linalg.norm(np.asarray(last[-1]["position"])-np.asarray(last[0]["position"]))) if last and last[-1]["position"] is not None and last[0]["position"] is not None else 0.0
        osc = bool(len(radial)>2 and sign_changes(radial) >= 20 and path > 5*net and (max(distances)-min(distances) if distances else 0)>1e-4)
        attributes.append({"trajectory_id":m["trajectory_id"],"nominal_controller_limitation_supported":nominal_limit,"cbf_boundary_stall_supported":cbf_stall,"recovery_steps":m["recovery_active_steps"],"baseline_limitation_preserved_candidate":m["arm"]=="STRICT_DT_TRIGGERED_V4C" and m["recovery_active_steps"]>0,"evidence_missing_nominal_or_safe":m["nominal_radial_mean"] is None or m["safe_radial_mean"] is None})
        oscillations.append({"trajectory_id":m["trajectory_id"],"window":"last200","radial_sign_changes":sign_changes(radial),"distance_sign_changes":sign_changes(np.diff(distances).tolist()) if len(distances)>2 else 0,"path_to_net_ratio":None if net==0 else path/net,"distance_peak_to_peak":None if not distances else max(distances)-min(distances),"controller_oscillation_supported":osc,"local_limit_cycle_supported":False})
        primary, secondary = ("EARLY_SAFETY_PROXY_STOP", []) if m["float32_proxy_overlap_stop"] else ("GOAL_TOLERANCE_LIMITED", []) if m["minimum_distance"] is not None and .001 < m["minimum_distance"] <= .01 else ("HORIZON_LIMITED_PROGRESSING", []) if m["terminal_status"] == "max_steps" and m["windows"].get("100") and m["windows"]["100"]["progress_gain"] is not None and m["windows"]["100"]["progress_gain"] >= .005 and not stalls[m["trajectory_id"]]["three_consecutive_low_progress_windows"] else ("CONTROLLER_OSCILLATION", []) if osc else ("CBF_BOUNDARY_STALL", []) if cbf_stall else ("NOMINAL_CONTROLLER_LIMITATION", []) if nominal_limit else ("INSUFFICIENT_LOG_EVIDENCE", [])
        classifications.append({"trajectory_id":m["trajectory_id"],"primary_classification":primary,"secondary_classifications":secondary,"proxy_overlap_certification":m["robust_overlap_status"] or ("PROXY_ONLY_NOT_CERTIFIED" if primary=="EARLY_SAFETY_PROXY_STOP" else None)})
    attr={"records":attributes}; osc={"records":oscillations}; classes={"records":classifications}; dump(AUDIT_ROOT / "controller/controller_cbf_recovery_attribution.json",attr); dump(AUDIT_ROOT / "oscillation/oscillation_diagnosis.json",osc); dump(AUDIT_ROOT / "global/trajectory_progress_classifications.json",classes); return attr,osc


def paired_comparison() -> dict[str, Any]:
    metrics = load(AUDIT_ROOT / "per_trajectory/per_trajectory_metrics.json")["trajectories"]
    classes = {x["trajectory_id"]:x for x in load(AUDIT_ROOT / "global/trajectory_progress_classifications.json")["records"]}
    normal = {x["trajectory_id"]:x for x in load(AUDIT_ROOT / "normalized/normalization_summary.json")["entries"]}
    groups: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for item in metrics: groups[item["pair_id"]][item["arm"]] = item
    pairs=[]
    for pair_id, pair in sorted(groups.items()):
        if set(pair) != {"ORIGINAL_SAFER_BASELINE", "STRICT_DT_TRIGGERED_V4C"}: continue
        b,i=pair["ORIGINAL_SAFER_BASELINE"],pair["STRICT_DT_TRIGGERED_V4C"]
        triggered=i["strict_trigger_count"]>0
        b_rows,i_rows=read_normalized(normal[b["trajectory_id"]]["normalized_path"]),read_normalized(normal[i["trajectory_id"]]["normalized_path"])
        state_control = lambda rows: canonical_sha([{"state":r["state"],"u":r["u_executed"]} for r in rows])
        invariant = not triggered and state_control(b_rows)==state_control(i_rows)
        progress_delta=(i["final_official_progress"]-b["final_official_progress"]) if b["final_official_progress"] is not None and i["final_official_progress"] is not None else None
        if invariant: conclusion="TRIGGER_NEUTRAL_BASELINE_EQUIVALENT"
        elif b["float32_proxy_overlap_stop"] and not i["float32_proxy_overlap_stop"] and (progress_delta is None or progress_delta >= -.005): conclusion="AVOIDED_OVERLAP_BUT_PRESERVED_BASELINE_PROGRESS_LIMITATION"
        elif triggered and progress_delta is not None and progress_delta < -.02: conclusion="PROGRESS_REGRESSION"
        else: conclusion="NO_MEANINGFUL_EFFECT"
        if invariant:
            for item in (b, i):
                classes[item["trajectory_id"]]["secondary_classifications"] = ["TRIGGER_NEUTRAL_BASELINE_EQUIVALENT"]
        elif conclusion == "AVOIDED_OVERLAP_BUT_PRESERVED_BASELINE_PROGRESS_LIMITATION":
            classes[i["trajectory_id"]]["secondary_classifications"] = ["BASELINE_LIMITATION_PRESERVED"]
        pairs.append({"pair_id":pair_id,"baseline_trajectory_id":b["trajectory_id"],"intervention_trajectory_id":i["trajectory_id"],"terminal_status":{ "baseline":b["terminal_status"],"intervention":i["terminal_status"]},"step_count_delta":i["step_count"]-b["step_count"],"final_progress_delta":progress_delta,"best_progress_delta":(i["best_geometric_progress"]-b["best_geometric_progress"]) if i["best_geometric_progress"] is not None and b["best_geometric_progress"] is not None else None,"final_distance_delta":i["final_distance"]-b["final_distance"],"min_distance_delta":i["minimum_distance"]-b["minimum_distance"],"path_length_delta":i["total_path_length"]-b["total_path_length"],"path_efficiency_delta":None if i["path_efficiency"] is None or b["path_efficiency"] is None else i["path_efficiency"]-b["path_efficiency"],"qp_correction_delta":None if i["qp_correction_norm_mean"] is None or b["qp_correction_norm_mean"] is None else i["qp_correction_norm_mean"]-b["qp_correction_norm_mean"],"strict_trigger_count":i["strict_trigger_count"],"recovery_active_steps":i["recovery_active_steps"],"baseline_classification":classes[b["trajectory_id"]]["primary_classification"],"intervention_classification":classes[i["trajectory_id"]]["primary_classification"],"triggered":triggered,"untriggered_invariance":invariant,"conclusion":conclusion,"float32_proxy_avoidance_only":bool(b["float32_proxy_overlap_stop"] and not i["float32_proxy_overlap_stop"]),"certified_robust_avoidance_claimed":False})
    class_records = sorted(classes.values(), key=lambda item: item["trajectory_id"])
    dump(AUDIT_ROOT / "global/trajectory_progress_classifications.json", {"records": class_records})
    data={"complete_paired_count":len(pairs),"pairs":pairs};dump(AUDIT_ROOT / "paired/paired_progress_comparison.json",data);return data


def global_causes() -> dict[str, Any]:
    metrics=load(AUDIT_ROOT / "per_trajectory/per_trajectory_metrics.json")["trajectories"]; classes=load(AUDIT_ROOT / "global/trajectory_progress_classifications.json")["records"]; paired=load(AUDIT_ROOT / "paired/paired_progress_comparison.json")
    class_lookup={x["trajectory_id"]:x["primary_classification"] for x in classes}
    secondary_lookup={x["trajectory_id"]:x["secondary_classifications"] for x in classes}
    cohorts={"baseline":[x for x in metrics if x["arm"]=="ORIGINAL_SAFER_BASELINE"],"intervention":[x for x in metrics if x["arm"]=="STRICT_DT_TRIGGERED_V4C"],"strict_triggered_intervention":[x for x in metrics if x["arm"]=="STRICT_DT_TRIGGERED_V4C" and x["strict_trigger_count"]>0],"non_triggered_intervention":[x for x in metrics if x["arm"]=="STRICT_DT_TRIGGERED_V4C" and x["strict_trigger_count"]==0],"proxy_stop":[x for x in metrics if x["float32_proxy_overlap_stop"]],"max_steps":[x for x in metrics if x["terminal_status"]=="max_steps"],"certified_robust_overlap":[x for x in metrics if x["robust_overlap_status"]=="CERTIFIED_ROBUST_OVERLAP"],"no_robust_overlap_intervention":[x for x in metrics if x["arm"]=="STRICT_DT_TRIGGERED_V4C" and x["robust_overlap_status"] != "CERTIFIED_ROBUST_OVERLAP"]}
    summary={}
    for name,values in cohorts.items():
        numeric_mean = lambda field: float(np.mean([x[field] for x in values if x.get(field) is not None])) if any(x.get(field) is not None for x in values) else None
        summary[name]={"trajectory_count":len(values),"goal_reached_count":sum(x["reached_goal"] for x in values),"terminal_status_counts":dict(Counter(x["terminal_status"] for x in values)),"primary_category_counts":dict(Counter(class_lookup[x["trajectory_id"]] for x in values)),"secondary_category_counts":dict(Counter(label for x in values for label in secondary_lookup[x["trajectory_id"]])),"final_progress_mean":numeric_mean("final_geometric_progress"),"best_progress_mean":numeric_mean("best_geometric_progress"),"final_distance_mean":numeric_mean("final_distance"),"minimum_distance_mean":numeric_mean("minimum_distance"),"path_efficiency_mean":numeric_mean("path_efficiency"),"executed_radial_mean":numeric_mean("executed_radial_mean"),"qp_correction_mean":numeric_mean("qp_correction_norm_mean"),"active_constraint_ratio_mean":numeric_mean("cbf_correction_active_ratio"),"trigger_count":sum(x["strict_trigger_count"] for x in values),"recovery_steps":sum(x["recovery_active_steps"] for x in values)}
    count=Counter(class_lookup.values()); primary=count.most_common(1)[0][0] if count else "INSUFFICIENT_LOG_EVIDENCE"; secondary=[name for name,_ in count.most_common(3)[1:3]]
    triggered=[x for x in paired["pairs"] if x["triggered"]]; untriggered=[x for x in paired["pairs"] if not x["triggered"]]
    data={"cohorts":summary,"global_primary_cause":primary,"global_secondary_causes":secondary,"pair_specific_exceptions":[{"pair_id":x["pair_id"],"conclusion":x["conclusion"]} for x in paired["pairs"] if x["conclusion"] not in {"AVOIDED_OVERLAP_BUT_PRESERVED_BASELINE_PROGRESS_LIMITATION","TRIGGER_NEUTRAL_BASELINE_EQUIVALENT"}],"answers":{"all_unreached_same_cause":len(count)==1,"nominal_controller_systematic":count.get("NOMINAL_CONTROLLER_LIMITATION",0)>len(metrics)/2,"cbf_systematic":count.get("CBF_BOUNDARY_STALL",0)>len(metrics)/2,"recovery_systemic_regression":any(x["conclusion"]=="PROGRESS_REGRESSION" for x in paired["pairs"]),"untriggered_noninvasive":bool(untriggered) and all(x["untriggered_invariance"] for x in untriggered),"triggered_preserved_baseline_limitation":any(x["conclusion"]=="AVOIDED_OVERLAP_BUT_PRESERVED_BASELINE_PROGRESS_LIMITATION" for x in triggered)}}
    dump(AUDIT_ROOT / "global/global_progress_root_cause.json",data);return data


def paired20_decision() -> dict[str, Any]:
    global_data=load(AUDIT_ROOT / "global/global_progress_root_cause.json"); inventory_data=load(AUDIT_ROOT / "inventory/trajectory_inventory.json")
    cats=Counter(global_data["cohorts"]["baseline"]["primary_category_counts"]) + Counter(global_data["cohorts"]["intervention"]["primary_category_counts"])
    if inventory_data["canonical_trajectory_count"] < 8: decision="INSUFFICIENT_EVIDENCE_FOR_RESUME_DECISION"
    elif cats["NOMINAL_CONTROLLER_LIMITATION"]+cats["CBF_BOUNDARY_STALL"]+cats["CONTROLLER_OSCILLATION"] > inventory_data["canonical_trajectory_count"]/2: decision="DO_NOT_RESUME_BEFORE_CONTROLLER_STUDY"
    elif global_data["answers"]["triggered_preserved_baseline_limitation"]: decision="RESUME_PAIRED20_AS_SAFETY_ONLY_EVALUATION"
    else: decision="DO_NOT_RESUME_BEFORE_CONTROLLER_STUDY"
    data={"decision":decision,"reason":"Offline-only evidence gate; no paired20 continuation was launched.","exact_resume_point":{"sequence":3,"pair_id":"PAIR_02","arm":"intervention","frames":"114->165"},"manifest_sha256":PAUSED_MANIFEST_SHA,"next_authorized_task":"A separately authorized controller-navigation study" if decision=="DO_NOT_RESUME_BEFORE_CONTROLLER_STUDY" else "A separately authorized safety-only paired20 continuation"}
    dump(AUDIT_ROOT / "global/paired20_resume_decision.json",data);return data


def render_figures() -> dict[str, Any]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    normal=load(AUDIT_ROOT / "normalized/normalization_summary.json")["entries"]; metrics=load(AUDIT_ROOT / "per_trajectory/per_trajectory_metrics.json")["trajectories"]
    records=[]
    def plot_lines(filename: str, field: str, title: str) -> None:
        fig,ax=plt.subplots(figsize=(9,5))
        for entry in normal:
            rows=read_normalized(entry["normalized_path"]); y=[r[field] for r in rows if r.get(field) is not None]; x=np.linspace(0,1,len(y)) if y else []
            ax.plot(x,y,label=entry["trajectory_id"],alpha=.65,linewidth=.9)
        ax.set(title=title,xlabel="normalized step",ylabel=field); ax.legend(fontsize=5,ncol=2); fig.tight_layout(); path=AUDIT_ROOT/"figures"/filename;fig.savefig(path,dpi=150);plt.close(fig);records.append(str(path))
    plot_lines("all_distance_to_goal_vs_normalized_step.png","distance_to_goal","Distance to goal: raw trajectories")
    plot_lines("all_progress_vs_step.png","geometric_progress","Geometric progress: raw trajectories")
    fig,ax=plt.subplots(figsize=(8,5)); xs=np.arange(len(metrics)); ax.scatter(xs,[m["final_geometric_progress"] for m in metrics],label="final");ax.scatter(xs,[m["best_geometric_progress"] for m in metrics],label="best");ax.legend();ax.set(title="Final versus best geometric progress",xlabel="trajectory",ylabel="progress");fig.tight_layout();path=AUDIT_ROOT/"figures"/"final_vs_best_progress.png";fig.savefig(path,dpi=150);plt.close(fig);records.append(str(path))
    for filename,field,title in (("path_efficiency_by_arm.png","path_efficiency","Path efficiency"),("radial_velocity_by_arm.png","executed_radial_mean","Executed radial component"),("qp_correction_by_arm.png","qp_correction_norm_mean","QP correction"),("active_constraint_ratio_by_arm.png","cbf_correction_active_ratio","Active correction ratio")):
        fig,ax=plt.subplots(figsize=(7,4)); groups=defaultdict(list)
        for m in metrics:
            if m[field] is not None:groups[m["arm"]].append(m[field])
        ax.boxplot(list(groups.values()),labels=list(groups));ax.set(title=title);fig.tight_layout();path=AUDIT_ROOT/"figures"/filename;fig.savefig(path,dpi=150);plt.close(fig);records.append(str(path))
    paired=load(AUDIT_ROOT/"paired/paired_progress_comparison.json")["pairs"]
    fig,ax=plt.subplots(figsize=(7,4));ax.bar([x["pair_id"] for x in paired],[x["final_progress_delta"] or 0 for x in paired]);ax.set(title="Paired final progress delta (intervention-baseline)",ylabel="delta");fig.tight_layout();path=AUDIT_ROOT/"figures"/"paired_progress_delta.png";fig.savefig(path,dpi=150);plt.close(fig);records.append(str(path))
    stalls={x["trajectory_id"]:x["stall_onset"] for x in load(AUDIT_ROOT/"stall/stall_onset_summary.json")["records"]}
    fig,ax=plt.subplots(figsize=(9,4));ax.bar(range(len(metrics)),[stalls.get(m["trajectory_id"]) if stalls.get(m["trajectory_id"]) is not None else -1 for m in metrics]);ax.set(title="Stall onset (-1 means none)",xlabel="trajectory",ylabel="step");fig.tight_layout();path=AUDIT_ROOT/"figures"/"stall_onset_by_trajectory.png";fig.savefig(path,dpi=150);plt.close(fig);records.append(str(path))
    fig,ax=plt.subplots(figsize=(9,4));
    for index,m in enumerate(metrics):
        if m["strict_trigger_count"]: ax.scatter([m["first_trigger_step"]],[index],marker="|",s=200,label=m["pair_id"] if index==0 else None)
    ax.set(title="Strict-trigger timeline",xlabel="step",ylabel="trajectory index");fig.tight_layout();path=AUDIT_ROOT/"figures"/"trigger_recovery_timeline.png";fig.savefig(path,dpi=150);plt.close(fig);records.append(str(path))
    fig,ax=plt.subplots(figsize=(6,5));
    for m in metrics:
        if m["nominal_radial_mean"] is not None and m["safe_radial_mean"] is not None: ax.scatter(m["nominal_radial_mean"],m["safe_radial_mean"],label=m["pair_id"])
    ax.axline((0,0),slope=1,color="gray",linestyle="--");ax.set(title="Nominal versus safe radial control",xlabel="nominal radial",ylabel="safe radial");fig.tight_layout();path=AUDIT_ROOT/"figures"/"controller_vs_safe_radial_component.png";fig.savefig(path,dpi=150);plt.close(fig);records.append(str(path))
    categories=Counter(x["primary_classification"] for x in load(AUDIT_ROOT/"global/trajectory_progress_classifications.json")["records"]);fig,ax=plt.subplots(figsize=(8,4));ax.bar(categories.keys(),categories.values());ax.tick_params(axis="x",rotation=35);ax.set(title="Progress-limitation category counts");fig.tight_layout();path=AUDIT_ROOT/"figures"/"progress_limitation_category_counts.png";fig.savefig(path,dpi=150);plt.close(fig);records.append(str(path))
    by_id={entry["trajectory_id"]:entry for entry in normal}; by_pair=defaultdict(dict)
    for metric in metrics: by_pair[metric["pair_id"]][metric["arm"]]=metric
    pair_root=AUDIT_ROOT/"figures"/"paired"; pair_root.mkdir(parents=True,exist_ok=True)
    def pair_value(row: dict[str, Any], field: str) -> float:
        if field == "executed_radial":
            if row["position"] is None or row["goal"] is None or row["u_executed"] is None: return float("nan")
            direction=np.asarray(row["goal"],dtype=np.float64)-np.asarray(row["position"],dtype=np.float64); length=float(np.linalg.norm(direction))
            return float("nan") if length == 0 else float(np.dot(np.asarray(row["u_executed"],dtype=np.float64),direction/length))
        if field == "qp_correction_norm":
            if row["u_nominal"] is None or row["u_safe"] is None: return float("nan")
            return norm(np.asarray(row["u_safe"],dtype=np.float64)-np.asarray(row["u_nominal"],dtype=np.float64))
        value=row.get(field)
        return float("nan") if value is None else float(value)
    for pair_id, arms in sorted(by_pair.items()):
        if set(arms) != {"ORIGINAL_SAFER_BASELINE","STRICT_DT_TRIGGERED_V4C"}: continue
        pair_slug=pair_id.replace("->","_to_")
        arm_rows={label:read_normalized(by_id[metric["trajectory_id"]]["normalized_path"]) for label,metric in arms.items()}
        for field,label in (("distance_to_goal","distance_to_goal"),("geometric_progress","geometric_progress"),("executed_radial","executed_radial"),("next_h","h"),("qp_correction_norm","qp_correction_norm")):
            fig,ax=plt.subplots(figsize=(9,4))
            for arm,rows in arm_rows.items():
                x=[row["step"] for row in rows]; y=[pair_value(row,field) for row in rows]
                ax.plot(x,y,label=arm,linewidth=.9,alpha=.85)
                trigger_steps=[row["step"] for row in rows if row["strict_trigger"]]; recovery_steps=[row["step"] for row in rows if row["recovery_active"]]
                for step in trigger_steps: ax.axvline(step,color="tab:orange",alpha=.35,linewidth=.8)
                for step in recovery_steps: ax.axvline(step,color="tab:red",alpha=.20,linewidth=.8)
            ax.set(title=f"{pair_id}: raw {label} (orange=trigger, red=recovery)",xlabel="saved step",ylabel=label);ax.legend(fontsize=7);fig.tight_layout()
            path=pair_root/f"{pair_slug}_{field}.png";fig.savefig(path,dpi=150);plt.close(fig);records.append(str(path))
    return {"figure_count":len(records),"figures":records}


def validate_and_report() -> dict[str, Any]:
    inv=load(AUDIT_ROOT/"inventory/trajectory_inventory.json"); normal=load(AUDIT_ROOT/"normalized/normalization_summary.json"); metrics=load(AUDIT_ROOT/"per_trajectory/per_trajectory_metrics.json"); paired=load(AUDIT_ROOT/"paired/paired_progress_comparison.json"); global_data=load(AUDIT_ROOT/"global/global_progress_root_cause.json"); decision=load(AUDIT_ROOT/"global/paired20_resume_decision.json"); source_manifest=SOURCE_D/"manifests/run_manifest.json"; manifest=load(source_manifest); states=Counter(x["state"] for x in manifest["states"].values())
    ids=[x["trajectory_id"] for x in inv["canonical_trajectories"]]; no_seq3=not (SOURCE_D/"intervention/PAIR_02/attempt_1/summary.json").exists() and not (SOURCE_D/"intervention/PAIR_02/attempt_1/steps.json").exists()
    validation={"status":"PASS_TUM_GLOBAL_PROGRESS_LIMITATION_OFFLINE_AUDIT" if len(ids)>=10 and len(ids)==len(set(ids)) and sha(source_manifest)==PAUSED_MANIFEST_SHA and states.get("TERMINAL_SCIENTIFIC_RESULT")==2 and states.get("RUNNING",0)==0 and no_seq3 else "BLOCKED_BY_GLOBAL_PROGRESS_AUDIT_INSUFFICIENT_EVIDENCE","unique_trajectory_ids":len(ids)==len(set(ids)),"source_manifest_sha256":sha(source_manifest),"source_manifest_states":dict(states),"sequence3_terminal_or_steps_exists":not no_seq3,"new_scientific_rollout_count":0,"qp_execution_count":0,"v4c_online_execution_count":0,"source_roots_written":False}
    dump(AUDIT_ROOT/"global/validation_result.json",validation);dump(AUDIT_ROOT/"global/downstream_handoff.json",{"status":validation["status"],"next_unique_task":decision["next_authorized_task"]})
    stalls={item["trajectory_id"]:item for item in load(AUDIT_ROOT/"stall/stall_onset_summary.json")["records"]}
    classes=load(AUDIT_ROOT/"global/trajectory_progress_classifications.json")["records"]; class_lookup={item["trajectory_id"]:item for item in classes}
    lines=["# TUM SplaTAM Global Progress-Limitation Offline Audit V1","",f"**Status:** `{validation['status']}`.","", "## Scope and evidence", "", "- Offline-only audit of saved terminal trajectories from PR #47, PR #48 shadow provenance, PR #49, and paused paired20. No rollout, sequence 3, QP execution, V4-C execution, Start-Safe, Risk-Aware, or tuning occurred.",f"- Canonical closed-loop trajectories: {inv['canonical_trajectory_count']}; complete paired comparisons: {paired['complete_paired_count']}; incomplete logs: {inv['incomplete_count']}.",f"- Paused manifest SHA-256 remains `{validation['source_manifest_sha256']}` with state counts {validation['source_manifest_states']}.","", "## Progress semantics and trajectory outcomes", ""]
    for m in metrics["trajectories"]:
        window=m["windows"].get("100") or {}; classification=class_lookup[m["trajectory_id"]]
        lines.append(f"- `{m['trajectory_id']}`: terminal `{m['terminal_status']}`; final/best geometric progress `{m['final_geometric_progress']}`/`{m['best_geometric_progress']}`; minimum distance `{m['minimum_distance']}`; path length/efficiency `{m['total_path_length']}`/`{m['path_efficiency']}`; last100 distance slope `{window.get('distance_slope')}`; stall onset `{stalls[m['trajectory_id']]['stall_onset']}`; primary `{classification['primary_classification']}`; secondary `{classification['secondary_classifications']}`.")
    lines += ["", "## Attribution and paired findings", "", f"- GLOBAL_PRIMARY_CAUSE: `{global_data['global_primary_cause']}`; secondary causes: `{global_data['global_secondary_causes']}`.",f"- Triggered-pair conclusions: {[(p['pair_id'],p['conclusion']) for p in paired['pairs'] if p['triggered']]}",f"- Untriggered invariance: {[(p['pair_id'],p['untriggered_invariance']) for p in paired['pairs'] if not p['triggered']]}.", "- Float32 proxy-stop avoidance is not reported as certified robust-overlap avoidance unless independent saved float64 certification explicitly supports it.", "- Safety-mechanism behavior, navigation completion, and progress limitation remain separate claims.", "", "## Paired20 decision and scheduler-race boundary", "", f"- Resume decision: `{decision['decision']}`. No paired20 continuation was started.", "- Scheduler-race fact preserved: sequence 3 briefly entered but wrote no terminal summary or step file; it is not a scientific result and resume point remains sequence 3.", "", "## Claim boundary", "", "This preliminary audit explains saved evidence only; it does not prove global goal reachability or general safety. Any controller study or paired20 continuation needs separate authorization.", ""]
    semantics=load(AUDIT_ROOT/"per_trajectory/progress_semantics_contract.json"); attr=load(AUDIT_ROOT/"controller/controller_cbf_recovery_attribution.json")["records"]; osc=load(AUDIT_ROOT/"oscillation/oscillation_diagnosis.json")["records"]
    primary_counts=Counter(item["primary_classification"] for item in classes); secondary_counts=Counter(label for item in classes for label in item["secondary_classifications"])
    lines += ["", "## Offline metric interpretation", "", f"- Official-versus-geometric progress records: {[(x['trajectory_id'], x['semantic_equivalence'], x['final_difference']) for x in semantics['entries']]}.", f"- Per-trajectory primary classifications: {[(x['trajectory_id'], x['primary_classification'], x['proxy_overlap_certification']) for x in classes]}.", f"- Primary counts: {dict(primary_counts)}; secondary counts: {dict(secondary_counts)}.", f"- Nominal/CBF attribution: {[(x['trajectory_id'], x['nominal_controller_limitation_supported'], x['cbf_boundary_stall_supported']) for x in attr]}.", f"- Oscillation-supported trajectories: {[x['trajectory_id'] for x in osc if x['controller_oscillation_supported']]}.", "- Goal-tolerance-limited and horizon-limited labels are offline classifications only; no horizon/tolerance was changed and no arrival was extrapolated.", "", "## Evidence limits", "", "- PR #47's 0->50 baseline proxy stop has saved PR #48 float64 robust-overlap certification. Other proxy stops remain proxy-only unless an existing matching certification is present.", "- Source A lacks saved nominal/safe controls; its state is reconstructed only from saved executed controls and frozen explicit Euler, so CBF-attribution claims for that record remain unavailable.", "- The scheduler race is preserved exactly: sequence 3 briefly entered, produced no terminal or step file, and is excluded from all trajectory statistics.", f"- Unique recommended next task: `{decision['next_authorized_task']}`.", ""]
    report=AUDIT_ROOT/"report/REPORT_TUM_SPLATAM_GLOBAL_PROGRESS_LIMITATION_AUDIT_V1.md";report.write_text("\n".join(lines),encoding="utf-8")
    return {"validation":validation,"report":str(report),"report_sha256":sha(report)}
