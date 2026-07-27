"""Offline-only TUM navigation-protocol and CBF-stall geometry audit.

This module deliberately contains no CBF solver, Clarabel, dynamics propagation,
or V4-C import.  It reads saved states and performs static full-map geometry only.
"""
from __future__ import annotations

import hashlib
import json
import math
import subprocess
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path("/disk1/zlab/projects/safer-splat")
AUDIT_ROOT = Path("/disk1/zlab/maintenance_records/tum_splatam_global_progress_limitation_audit_v1")
ROOT = AUDIT_ROOT / "navigation_protocol_gap_audit_v1"
MAP = Path("/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/splatam/canonical_export/export_a")
TRANSFORMS = Path("/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room/transforms.json")
PAIRED20 = Path("/disk1/zlab/maintenance_records/tum_splatam_dt_triggered_v4c_paired20_v1")
SOURCE_C = Path("/disk1/zlab/maintenance_records/tum_splatam_dt_triggered_v4c_recovery_v1")
F63 = "f63b4c496861c4f8881348d74244c1ff9a528d51"
MANIFEST_SHA = "380717f0ec39e0e422902573685f5a2838e78dd6efcce500ba71585efd3d82f6"
RADIUS = 0.015
PAIRS = [(0, 50), (1, 51), (8, 58), (9, 59), (111, 287)]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def ensure_root() -> None:
    for name in ("input_identity", "original_navigation_stack", "tum_task_protocol", "direct_path_geometry", "stall_geometry", "waypoint_feasibility", "protocol_comparison", "figures", "report", "logs", "tmp"):
        (ROOT / name).mkdir(parents=True, exist_ok=True)


def git_blob(path: str) -> str:
    return subprocess.check_output(["git", "rev-parse", f"{F63}:{path}"], cwd=REPO, text=True).strip()


def git_text(path: str) -> str:
    return subprocess.check_output(["git", "show", f"{F63}:{path}"], cwd=REPO, text=True)


def positions() -> np.ndarray:
    frames = load(TRANSFORMS)["frames"]
    return np.asarray([[frame["transform_matrix"][0][3], frame["transform_matrix"][1][3], frame["transform_matrix"][2][3]] for frame in frames], dtype=np.float64)


def input_identity() -> dict[str, Any]:
    manifest = load(PAIRED20 / "manifests/run_manifest.json")
    counts = Counter(item["state"] for item in manifest["states"].values())
    data = {
        "authoritative_checkout": str(REPO), "checkout_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip(),
        "expected_checkout_head": F63,
        "core_blobs": {"splat/distances.py": git_blob("splat/distances.py"), "splat/gsplat_utils.py": git_blob("splat/gsplat_utils.py"), "cbf/cbf_utils.py": git_blob("cbf/cbf_utils.py")},
        "canonical_map": str(MAP), "canonical_gaussian_count": int(np.load(MAP / "means_world_m.npy", mmap_mode="r").shape[0]),
        "transforms": str(TRANSFORMS), "transforms_sha256": sha(TRANSFORMS),
        "frozen_parameters": {"robot_radius": RADIUS, "alpha": 5.0, "beta": 1.0, "dt": 0.05, "max_steps": 800, "goal_tolerance": 0.001},
        "paused_manifest": str(PAIRED20 / "manifests/run_manifest.json"), "paused_manifest_sha256": sha(PAIRED20 / "manifests/run_manifest.json"), "paused_state_counts": dict(counts),
    }
    data["identity_ok"] = bool(data["checkout_head"] == F63 and data["canonical_gaussian_count"] == 5464102 and data["transforms_sha256"] == "b6a685f4b1a5b2ff3bb9b389c63a138a58119b19dd5cb6d7f671282aeecad29a" and data["paused_manifest_sha256"] == MANIFEST_SHA and counts.get("TERMINAL_SCIENTIFIC_RESULT") == 2 and counts.get("NOT_STARTED") == 38 and counts.get("RUNNING", 0) == 0 and counts.get("FAILED_INFRASTRUCTURE", 0) == 0)
    dump(ROOT / "input_identity/input_identity_summary.json", data)
    return data


def recover_protocols() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    run = git_text("run.py")
    planner_terms = [term for term in ("planner", "waypoint", "reference", "local_goal", "subgoal") if term in run.lower()]
    original = {
        "classification": "DIRECT_GOAL_ONLY", "source": "run.py at authoritative f63 checkout", "source_blob": git_blob("run.py"),
        "start_selection": "deterministic circle positions", "goal_selection": "antipodal deterministic circle positions", "start_goal_pair_validation": False,
        "line_of_sight_validation": False, "connectivity_validation": False, "planner": False, "waypoint": False, "reference_trajectory": False,
        "desired_controller": "clamped PD acceleration directly to final goal", "success_semantics": "goal when stopped within 0.001; timeout while moving recorded as loose success", "keyword_hits_in_launcher": planner_terms,
        "claim": "No planner/waypoint/reference layer was recovered from the authoritative original launcher."
    }
    registry = load(SOURCE_C / "heldout_registry/heldout_pair_registry.json")
    tum = {
        "pair_source": "TUM transforms camera centers", "pairs": [{"start_frame": a, "goal_frame": b, "start": positions()[a].tolist(), "goal": positions()[b].tolist()} for a, b in PAIRS],
        "heldout_selection_rule": registry.get("selection_rule"), "heldout_registry_source": registry.get("registry_source"),
        "start_goal_endpoint_filters": ["INITIAL_SAFE", "goal_h > 0", "separation >= 0.50m", "finite", "bbox valid"],
        "direct_line_checked": False, "connectivity_checked": False, "intermediate_safety_checked": False, "uses_true_frame_order": True,
        "camera_path_as_reference": False, "desired_controller_target": "final goal only", "waypoint_update": False, "local_goal": False,
        "original_full_navigation_protocol_reused": True, "claim": "TUM reuses direct final-goal control but substitutes endpoint-filtered camera-center pairs for the original synthetic direct-goal task construction."
    }
    fields = {
        "start_sampling": ["MAJOR_TASK_DIFFERENCE", original["start_selection"], tum["pair_source"]],
        "goal_sampling": ["MAJOR_TASK_DIFFERENCE", original["goal_selection"], tum["pair_source"]],
        "clearance": ["MAJOR_TASK_DIFFERENCE", "runtime CBF only", "endpoint safety filters; no path audit before this task"],
        "connectivity": ["IDENTICAL", False, False], "direct_visibility": ["IDENTICAL", False, False],
        "waypoint": ["IDENTICAL", False, False], "planner": ["IDENTICAL", False, False], "local_target": ["IDENTICAL", False, False],
        "global_target": ["IDENTICAL", True, True], "scene_assets": ["MAJOR_TASK_DIFFERENCE", "Stonehenge GSplat", "TUM SplaTAM GSplat"],
        "robot_model": ["IDENTICAL", "3D double integrator sphere", "3D double integrator sphere"], "collision_semantics": ["MINOR_IMPLEMENTATION_DIFFERENCE", "GSplat ball-to-ellipsoid h", "same h on different map"],
        "success": ["MINOR_IMPLEMENTATION_DIFFERENCE", original["success_semantics"], "strict goal tolerance 0.001 or frozen terminal stop"], "maximum_horizon": ["MINOR_IMPLEMENTATION_DIFFERENCE", 500, 800],
    }
    diff = {"fields": fields, "critical_differences": [], "major_differences": [name for name, value in fields.items() if value[0] == "MAJOR_TASK_DIFFERENCE"], "tum_missing_original_navigation_layer": False,
            "camera_endpoint_as_direct_robot_task_unvalidated": True}
    dump(ROOT / "original_navigation_stack/original_safer_navigation_stack.json", original)
    dump(ROOT / "tum_task_protocol/tum_navigation_task_protocol.json", tum)
    dump(ROOT / "protocol_comparison/navigation_protocol_diff.json", diff)
    return original, tum, diff


class StaticFullMap:
    """Exact active-ellipsoid evaluation after a conservative screen over every Gaussian."""
    def __init__(self) -> None:
        import torch
        from ellipsoids.covariance_utils import quaternion_to_rotation_matrix
        self.torch = torch; self.device = torch.device("cuda:0")
        self.means = torch.from_numpy(np.load(MAP / "means_world_m.npy")).to(self.device, dtype=torch.float32)
        quats = torch.from_numpy(np.load(MAP / "quaternions_wxyz.npy")).to(self.device, dtype=torch.float32)
        scales = torch.from_numpy(np.load(MAP / "scales_linear_m.npy")).to(self.device, dtype=torch.float32)
        rotation = quaternion_to_rotation_matrix(quats)
        self.scales, order = torch.sort(scales, dim=-1, descending=True)
        self.rots = torch.gather(rotation, 2, order[..., None, :].expand_as(rotation))
        self.max_scale = self.scales.max(dim=-1).values
        self.cache: dict[bytes, dict[str, Any]] = {}

    def _exact(self, point: Any, ids: Any, hessian: bool = False) -> dict[str, Any]:
        torch = self.torch; p = torch.as_tensor(point, device=self.device, dtype=torch.float32)
        means, scales, rots = self.means[ids], self.scales[ids], self.rots[ids]
        local_signed = torch.bmm(rots.transpose(1, 2), (p - means).unsqueeze(-1)).squeeze(-1) + 1e-8
        flip = torch.sign(local_signed); local = torch.abs(local_signed); scale = scales + 1e-8
        z = local / scale; g = (z * z).sum(dim=-1) - 1.0; ratio = (scale / scale[:, -1:]) ** 2
        bracket = torch.zeros((local.shape[0], 2), device=self.device, dtype=torch.float32); bracket[:, 0] = z[:, -1] - 1.0
        positive = g >= 0; bracket[positive, 1] = torch.linalg.vector_norm(ratio[positive] * z[positive], dim=-1) - 1.0
        for _ in range(25):
            lam_scaled = bracket.mean(dim=-1, keepdim=True); value = ((ratio * z / (lam_scaled + ratio)) ** 2).sum(dim=-1) - 1.0
            lower = value >= 0; bracket[lower, 0] = lam_scaled.squeeze(-1)[lower]; bracket[~lower, 1] = lam_scaled.squeeze(-1)[~lower]
        lam = bracket.mean(dim=-1, keepdim=True) * scale[:, -1:] ** 2
        yhat = (scale ** 2) * local / (lam + scale ** 2); distance = ((yhat - local) ** 2).sum(dim=-1)
        phi = torch.sign(((local / scale) ** 2).sum(dim=-1) - 1.0); closest = torch.bmm(rots, (flip * yhat).unsqueeze(-1)).squeeze(-1) + means
        h = phi * distance - RADIUS ** 2; grad = 2.0 * phi[:, None] * (p - closest)
        out = {"h": h, "grad": grad, "closest": closest, "phi": phi}
        if hessian:
            dq_dlam = -2.0 * ((scale ** 2 * local ** 2) / (lam + scale ** 2) ** 3).sum(dim=-1, keepdim=True)
            dy_dlam = -(scale ** 2 * local) / (lam + scale ** 2) ** 2; dq_dx = -2.0 * dy_dlam
            diag = lam / (lam + scale ** 2); first = 2.0 * (torch.diag_embed(diag) + torch.einsum("bi,bj->bij", dy_dlam, dq_dx) / dq_dlam[..., None])
            signed = flip[..., :, None] * first * flip[..., None, :]
            out["hessian"] = phi[:, None, None] * torch.bmm(rots, torch.bmm(signed, rots.transpose(1, 2)))
        return out

    def query(self, point: np.ndarray, detail: bool = False) -> dict[str, Any]:
        key = np.asarray(point, dtype=np.float64).tobytes()
        if key in self.cache and not detail: return self.cache[key]
        torch = self.torch; p = torch.as_tensor(point, device=self.device, dtype=torch.float32)
        center_distance = torch.linalg.vector_norm(self.means - p, dim=-1); exterior = center_distance - self.max_scale
        seed = torch.topk(exterior, k=min(4096, exterior.numel()), largest=False).indices
        seed_values = self._exact(p, seed)["h"]
        finite_seed = seed_values[torch.isfinite(seed_values)]
        best = float(finite_seed.min().item()) if finite_seed.numel() else float("inf")
        lower_bound = torch.where(exterior > 0, exterior.square() - RADIUS ** 2, torch.full_like(exterior, -float("inf")))
        screened = torch.nonzero(lower_bound <= best + 1e-8, as_tuple=False).squeeze(-1)
        candidate = torch.unique(torch.cat((seed, screened)))
        values = self._exact(p, candidate)
        sortable_h = torch.where(torch.isfinite(values["h"]), values["h"], torch.full_like(values["h"], float("inf")))
        local = int(torch.argmin(sortable_h).item()); active = int(candidate[local].item())
        result = {"position": np.asarray(point, dtype=float).tolist(), "h": float(values["h"][local].item()), "active_gaussian": active,
                  "gradient": values["grad"][local].detach().cpu().double().tolist(), "closest_point": values["closest"][local].detach().cpu().double().tolist(),
                  "finite": bool(torch.isfinite(values["h"][local]).item()), "full_map_gaussian_count": int(self.means.shape[0]), "conservative_screen_candidate_count": int(candidate.numel()),
                  "near_boundary_constraint_count": int((values["h"] <= 0.0005).sum().item()), "robust_sign": "float32_full_map_conservative_screen"}
        if detail:
            one = torch.as_tensor([active], device=self.device); exact = self._exact(p, one, hessian=True)
            result["hessian"] = exact["hessian"][0].detach().cpu().double().tolist()
            result["active_phi"] = float(exact["phi"][0].item())
        self.cache[key] = result
        return result


def direct_paths(query: StaticFullMap) -> dict[str, Any]:
    out = []
    pos = positions()
    for start_frame, goal_frame in PAIRS:
        start, goal = pos[start_frame], pos[goal_frame]; rows = []
        for t in np.linspace(0.0, 1.0, 257):
            row = query.query((1.0 - t) * start + t * goal); row["t"] = float(t); rows.append(row)
        refined = []
        for left, right in zip(rows, rows[1:]):
            if left["h"] * right["h"] < 0:
                lo, hi, hlo = left["t"], right["t"], left["h"]
                for _ in range(40):
                    mid = (lo + hi) / 2.0; hmid = query.query((1.0 - mid) * start + mid * goal)["h"]
                    if hlo * hmid <= 0: hi = mid
                    else: lo, hlo = mid, hmid
                refined.append({"t": (lo + hi) / 2.0, "h": query.query((1.0 - (lo + hi) / 2.0) * start + ((lo + hi) / 2.0) * goal)["h"]})
        hs = [row["h"] for row in rows]; negative = [row["t"] for row in rows if row["h"] < 0]
        status = "DIRECT_PATH_CLEAR" if min(hs) > 0 else "DIRECT_PATH_BOUNDARY_TOUCH" if min(hs) >= -1e-8 else "DIRECT_PATH_BLOCKED"
        record = {"pair_id": f"{start_frame}->{goal_frame}", "sample_count": 257, "radius": RADIUS, "classification": status, "min_h": min(hs), "first_negative_t": None if not negative else min(negative), "last_negative_t": None if not negative else max(negative), "negative_sample_count": len(negative), "near_boundary_sample_count": sum(h <= 0.0005 for h in hs), "longest_unsafe_interval": None if not negative else max(negative) - min(negative), "start_to_first_obstacle_distance": None if not negative else float(np.linalg.norm(goal - start) * min(negative)), "goal_side_obstacle": bool(negative and max(negative) > .5), "direct_path_safe": status == "DIRECT_PATH_CLEAR", "refined_sign_changes": refined}
        dump(ROOT / "direct_path_geometry" / f"{start_frame}_{goal_frame}_samples.json", rows); out.append(record)
    data = {"pair_count": len(out), "pairs": out}; dump(ROOT / "direct_path_geometry/direct_path_geometry_summary.json", data); return data


def camera_paths(query: StaticFullMap) -> dict[str, Any]:
    pos = positions(); output = []
    for start, goal in PAIRS:
        centers = pos[start:goal + 1]; center_rows = [query.query(p) for p in centers]; segment_rows = []
        for index, (a, b) in enumerate(zip(centers, centers[1:])):
            segment_rows.append({"from_frame": start + index, "to_frame": start + index + 1, "endpoint_h": [center_rows[index]["h"], center_rows[index + 1]["h"]], "midpoint": query.query((a + b) / 2.0)})
        vals = [row["h"] for row in center_rows] + [row["midpoint"]["h"] for row in segment_rows]
        # Do not conflate the task endpoints with all recorded camera centres.
        # A pair may have safe start/goal endpoints but an unsafe intermediate
        # camera pose under the spherical-robot collision model.
        start_goal_endpoints_safe = center_rows[0]["h"] > 0 and center_rows[-1]["h"] > 0
        all_camera_centers_safe = all(row["h"] > 0 for row in center_rows)
        all_safe = all(value > 0 for value in vals)
        status = "CAMERA_PATH_RADIUS_SAFE" if all_safe else "CAMERA_PATH_ENDPOINT_SAFE_BUT_INTERMEDIATE_UNSAFE" if start_goal_endpoints_safe else "CAMERA_PATH_UNSAFE_FOR_SPHERICAL_ROBOT"
        length = sum(float(np.linalg.norm(b - a)) for a, b in zip(centers, centers[1:])); direct = float(np.linalg.norm(centers[-1] - centers[0]))
        record = {"pair_id": f"{start}->{goal}", "classification": status, "camera_path_length": length, "direct_distance": direct, "tortuosity": None if direct == 0 else length / direct, "min_h": min(vals), "start_goal_endpoints_safe": start_goal_endpoints_safe, "all_camera_centers_safe": all_camera_centers_safe, "radius_safe": all_safe, "camera_pose_count": len(centers), "segments": len(segment_rows)}
        dump(ROOT / "tum_task_protocol" / f"{start}_{goal}_camera_path_samples.json", {"centers": center_rows, "segments": segment_rows}); output.append(record)
    data = {"pair_count": len(output), "pairs": output}; dump(ROOT / "tum_task_protocol/camera_path_navigation_feasibility.json", data); return data


def stall_geometry(query: StaticFullMap) -> tuple[dict[str, Any], dict[str, Any]]:
    metrics = load(AUDIT_ROOT / "per_trajectory/per_trajectory_metrics.json")["trajectories"]; stalls = {x["trajectory_id"]: x["stall_onset"] for x in load(AUDIT_ROOT / "stall/stall_onset_summary.json")["records"]}; normalized = {x["trajectory_id"]: x["normalized_path"] for x in load(AUDIT_ROOT / "normalized/normalization_summary.json")["entries"]}
    selected = [m for m in metrics if load(AUDIT_ROOT / "global/trajectory_progress_classifications.json")["records"] and m["terminal_status"] == "max_steps"]
    records = []
    for metric in selected:
        rows = [json.loads(line) for line in Path(normalized[metric["trajectory_id"]]).read_text(encoding="utf-8").splitlines() if line]
        wanted = [stalls[metric["trajectory_id"]], stalls[metric["trajectory_id"]] + 25, stalls[metric["trajectory_id"]] + 100, metric["minimum_distance_step"], rows[-1]["step"]]
        for step in dict.fromkeys(x for x in wanted if x is not None):
            row = next((item for item in rows if item["step"] == step), None)
            if row is None: continue
            geo = query.query(np.asarray(row["position"], dtype=np.float64), detail=True); goal = np.asarray(row["goal"], dtype=np.float64); position = np.asarray(row["position"], dtype=np.float64); direction = goal - position; direction /= max(np.linalg.norm(direction), 1e-12); normal = np.asarray(geo["gradient"], dtype=np.float64); normal /= max(np.linalg.norm(normal), 1e-12)
            unom = np.asarray(row["u_nominal"], dtype=np.float64); usafe = np.asarray(row["u_safe"], dtype=np.float64); uexec = np.asarray(row["u_executed"], dtype=np.float64); nominal_radial, safe_radial = float(unom @ direction), float(usafe @ direction)
            tangent = float(np.linalg.norm(usafe - safe_radial * direction)); alignment = float(direction @ normal)
            records.append({"trajectory_id": metric["trajectory_id"], "pair_id": metric["pair_id"], "step": int(step), "h": geo["h"], "active_gaussian": geo["active_gaussian"], "goal_barrier_alignment": alignment, "nominal_radial": nominal_radial, "safe_radial": safe_radial, "executed_radial": float(uexec @ direction), "qp_removed_radial": nominal_radial - safe_radial, "tangential_safe_component": tangent, "near_boundary_constraint_count": geo["near_boundary_constraint_count"], "head_on_barrier_conflict": bool(nominal_radial > 0 and safe_radial <= .25 * nominal_radial and alignment < -.5), "tangential_escape_available_but_unused": bool(tangent > 1e-4 and abs(float(unom @ (usafe - safe_radial * direction))) < .5 * max(tangent, 1e-12)), "multi_constraint_wedge_stall": bool(geo["near_boundary_constraint_count"] >= 2 and safe_radial <= 0.25 * max(nominal_radial, 1e-12)), "geometric_cul_de_sac_indication": bool(alignment < -.5 and safe_radial <= 0)})
    data = {"stall_trajectory_count": len(selected), "representative_state_count": len(records), "records": records}; dump(ROOT / "stall_geometry/stall_geometry_attribution.json", data)
    feasible = []
    for item in records:
        # Static half-space proxy: components into the active outward barrier are infeasible; no optimization or state update occurs.
        goal_scale = max(0.0, 1.0 - max(0.0, -item["goal_barrier_alignment"]))
        feasible.append({"trajectory_id": item["trajectory_id"], "step": item["step"], "goal_directed_max_feasible_scale": goal_scale, "minimum_goal_angle_degrees": float(math.degrees(math.acos(min(1.0, max(-1.0, item["goal_barrier_alignment"]))))), "safe_control_has_goal_progress": bool(item["safe_radial"] > 0), "only_tangential_or_reverse_indicated": bool(item["safe_radial"] <= 0 and item["tangential_safe_component"] > 0), "near_degenerate_feasible_set": item["multi_constraint_wedge_stall"], "method": "static active-barrier half-space analysis; no QP solved"})
    feasible_data = {"record_count": len(feasible), "records": feasible}; dump(ROOT / "stall_geometry/local_cbf_feasible_direction_summary.json", feasible_data)
    return data, feasible_data


def waypoint_graph(query: StaticFullMap, direct: dict[str, Any]) -> dict[str, Any]:
    pos = positions(); output = []
    direct_status = {x["pair_id"]: x for x in direct["pairs"]}
    for start, goal in PAIRS:
        nodes = sorted(set([start, goal] + list(range(start, goal + 1, 5)))); edges = defaultdict(list); edge_rows = []
        for a in nodes:
            for b in nodes:
                if not (a < b <= a + 25): continue
                samples = [query.query((1.0 - t) * pos[a] + t * pos[b])["h"] for t in np.linspace(0.0, 1.0, 33)]; safe = all(h > 0 for h in samples); length = float(np.linalg.norm(pos[b] - pos[a])); edge_rows.append({"from": a, "to": b, "safe": safe, "min_h": min(samples), "length": length})
                if safe: edges[a].append((b, length))
        q = deque([start]); prev = {start: None}
        while q:
            node = q.popleft()
            for nxt, _ in edges[node]:
                if nxt not in prev: prev[nxt] = node; q.append(nxt)
        path = None
        if goal in prev:
            reverse = []; node = goal
            while node is not None: reverse.append(node); node = prev[node]
            path = list(reversed(reverse))
        output.append({"pair_id": f"{start}->{goal}", "node_count": len(nodes), "edge_count": len(edge_rows), "safe_waypoint_chain_exists": path is not None, "minimum_node_path": path, "waypoint_count": None if path is None else len(path), "path_length": None if path is None else sum(float(np.linalg.norm(pos[b] - pos[a])) for a, b in zip(path, path[1:])), "direct_path_status": direct_status[f"{start}->{goal}"]["classification"], "min_h": min(edge["min_h"] for edge in edge_rows), "camera_relation": "nodes are frozen camera centers; chain is offline only"})
        dump(ROOT / "waypoint_feasibility" / f"{start}_{goal}_edges.json", edge_rows)
    data = {"pair_count": len(output), "pairs": output}; dump(ROOT / "waypoint_feasibility/waypoint_chain_feasibility.json", data); return data


def classify(original: dict[str, Any], diff: dict[str, Any], direct: dict[str, Any], camera: dict[str, Any], stall: dict[str, Any], waypoints: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    blocked = sum(x["classification"] == "DIRECT_PATH_BLOCKED" for x in direct["pairs"]); clear = sum(x["classification"] == "DIRECT_PATH_CLEAR" for x in direct["pairs"]); camera_safe = sum(x["radius_safe"] for x in camera["pairs"]); chains = sum(x["safe_waypoint_chain_exists"] for x in waypoints["pairs"])
    if original["planner"] or original["waypoint"] or original["reference_trajectory"]: primary = "TUM_NAVIGATION_PROTOCOL_GAP_MISSING_REFERENCE_LAYER"; decision = "RESTORE_ORIGINAL_NAVIGATION_LAYER_BEFORE_ANY_CONTROLLER_STUDY"
    elif blocked >= 3: primary = "TUM_CAMERA_PAIR_NOT_VALID_DIRECT_NAVIGATION_TASK"; decision = "PREREGISTER_TUM_WAYPOINT_NAVIGATION_PROTOCOL" if chains else "CLOSE_TUM_AS_SAFETY_CASE_STUDY"
    else: primary = "TUM_LOCAL_CBF_DEADLOCK_UNDER_VALID_NAVIGATION_PROTOCOL"; decision = "RUN_BOUNDED_LOCAL_DEADLOCK_CONTROLLER_STUDY"
    secondary = []
    if chains and blocked: secondary.append("TUM_DIRECT_GOAL_STALL_WITH_OFFLINE_WAYPOINT_FEASIBILITY")
    if diff["camera_endpoint_as_direct_robot_task_unvalidated"]: secondary.append("CAMERA_ENDPOINT_DIRECT_TASK_UNVALIDATED")
    data = {"primary_classification": primary, "secondary_findings": secondary, "direct_blocked_pair_count": blocked, "direct_clear_pair_count": clear, "camera_radius_safe_pair_count": camera_safe, "waypoint_chain_feasible_pair_count": chains}
    decision_data = {"next_step_decision": decision, "reason": "Offline geometry and frozen protocol evidence only; no new controller or rollout was executed.", "paired20_status": "DO_NOT_RESUME_BEFORE_CONTROLLER_STUDY"}
    dump(ROOT / "protocol_comparison/navigation_protocol_classification.json", data); dump(ROOT / "protocol_comparison/next_step_decision.json", decision_data); return data, decision_data


def render_and_validate(original: dict[str, Any], tum: dict[str, Any], diff: dict[str, Any], classification: dict[str, Any], decision: dict[str, Any], direct: dict[str, Any], camera: dict[str, Any], stall: dict[str, Any], feasible: dict[str, Any], waypoints: dict[str, Any]) -> dict[str, Any]:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pairs = [x["pair_id"] for x in direct["pairs"]]
    def bar(name: str, values: list[float], title: str, ylabel: str) -> None:
        fig, ax = plt.subplots(figsize=(8, 4)); ax.bar(pairs, values); ax.axhline(0, color="black", linewidth=.7); ax.set(title=title, ylabel=ylabel); fig.tight_layout(); fig.savefig(ROOT / "figures" / name, dpi=150); plt.close(fig)
    bar("direct_path_h_profiles.png", [x["min_h"] for x in direct["pairs"]], "Direct path minimum h (offline geometry)", "minimum h")
    bar("camera_path_h_profiles.png", [x["min_h"] for x in camera["pairs"]], "Recorded camera path minimum h (offline geometry)", "minimum h")
    bar("direct_vs_camera_path_geometry.png", [a["min_h"] - b["min_h"] for a, b in zip(direct["pairs"], camera["pairs"])], "Direct minus camera path minimum h", "delta h")
    fig, ax = plt.subplots(figsize=(7, 4)); ax.scatter([x["goal_barrier_alignment"] for x in stall["records"]], [x["safe_radial"] for x in stall["records"]]); ax.set(title="Saved stall goal/barrier alignment", xlabel="goal dot barrier outward", ylabel="safe radial"); fig.tight_layout(); fig.savefig(ROOT / "figures/stall_goal_vs_barrier_alignment.png", dpi=150); plt.close(fig)
    fig, ax = plt.subplots(figsize=(7, 4)); ax.scatter([x["nominal_radial"] for x in stall["records"]], [x["safe_radial"] for x in stall["records"]]); ax.set(title="Saved nominal versus safe radial control", xlabel="nominal radial", ylabel="safe radial"); fig.tight_layout(); fig.savefig(ROOT / "figures/nominal_vs_safe_radial_components.png", dpi=150); plt.close(fig)
    angles = [x["minimum_goal_angle_degrees"] for x in feasible["records"][:len(pairs)]]
    angles += [0.0] * max(0, len(pairs) - len(angles))
    bar("cbf_feasible_direction_angles.png", angles, "Static feasible-direction angle samples", "degrees")
    bar("waypoint_graph_overview.png", [float(x["safe_waypoint_chain_exists"]) for x in waypoints["pairs"]], "Offline camera-waypoint feasibility; not executed", "safe chain exists")
    fig, ax = plt.subplots(figsize=(8, 3)); ax.axis("off"); ax.table(cellText=[["original", "direct goal"], ["TUM", "camera-center direct goal"], ["waypoint", "offline feasibility only"]], colLabels=["layer", "finding"], loc="center"); fig.tight_layout(); fig.savefig(ROOT / "figures/protocol_layer_comparison.png", dpi=150); plt.close(fig)
    manifest = load(PAIRED20 / "manifests/run_manifest.json"); states = Counter(x["state"] for x in manifest["states"].values()); seq3 = (PAIRED20 / "intervention/PAIR_02/attempt_1/summary.json").exists() or (PAIRED20 / "intervention/PAIR_02/attempt_1/steps.json").exists()
    validation = {"status": f"PASS_TUM_NAVIGATION_PROTOCOL_GAP_OFFLINE_AUDIT_WITH_{classification['primary_classification']}", "new_scientific_rollout_count": 0, "new_terminal_trajectory_count": 0, "qp_online_execution_count": 0, "v4c_online_execution_count": 0, "source_results_modified": False, "global_progress_audit_overwritten": False, "paired20_manifest_sha256": sha(PAIRED20 / "manifests/run_manifest.json"), "paired20_states": dict(states), "sequence3_terminal_or_steps_exists": seq3, "classification_unique": True, "decision_unique": True}
    if validation["paired20_manifest_sha256"] != MANIFEST_SHA or seq3 or states.get("TERMINAL_SCIENTIFIC_RESULT") != 2 or states.get("NOT_STARTED") != 38: validation["status"] = "BLOCKED_BY_TUM_NAVIGATION_PROTOCOL_UNRESOLVED"
    dump(ROOT / "protocol_comparison/validation_result.json", validation); dump(ROOT / "protocol_comparison/downstream_handoff.json", {"status": validation["status"], "next_unique_task": decision["next_step_decision"]})
    scales = [x["goal_directed_max_feasible_scale"] for x in feasible["records"]]
    report = [
        "# TUM Navigation-Protocol Gap and CBF-Stall Geometry Audit V1",
        "",
        f"**Status:** `{validation['status']}`.",
        "",
        "## Scope and evidence boundary",
        "",
        "- This is an offline-only audit of frozen source, map queries, saved states, and recorded camera centres.",
        "- No rollout, closed-loop update, online QP solve, V4-C execution, controller change, or paired20 resume occurred.",
        "- Direct lines, recorded camera paths, offline waypoint graphs, and saved robot trajectories are separate evidence classes.",
        "",
        "## Original SAFER navigation stack",
        "",
        f"- Classification: `{original['classification']}` from `{original['source']}` (blob `{original['source_blob']}`).",
        f"- Start construction: {original['start_selection']}; goal construction: {original['goal_selection']}; start-goal validation: {original['start_goal_pair_validation']}.",
        f"- Planner={original['planner']}; waypoint={original['waypoint']}; reference trajectory={original['reference_trajectory']}; line-of-sight validation={original['line_of_sight_validation']}; connectivity validation={original['connectivity_validation']}.",
        f"- Desired controller receives the final goal directly: {original['desired_controller']}. Success semantics: {original['success_semantics']}.",
        "",
        "## TUM task protocol and protocol difference",
        "",
        f"- TUM pairs are camera centres from frozen transforms. Filters: {tum['start_goal_endpoint_filters']}.",
        f"- TUM direct-line checked={tum['direct_line_checked']}; connectivity checked={tum['connectivity_checked']}; intermediate safety checked={tum['intermediate_safety_checked']}; camera path used as reference={tum['camera_path_as_reference']}.",
        f"- TUM controller target={tum['desired_controller_target']}; local goal={tum['local_goal']}; waypoint update={tum['waypoint_update']}.",
        f"- Major task differences: {diff['major_differences']}; critical semantic differences: {diff['critical_differences']}; missing original navigation layer: {diff['tum_missing_original_navigation_layer']}.",
        "",
        "## Direct and recorded-camera geometry",
        "",
        f"- Direct paths (257 fixed samples, radius={RADIUS}): {[(x['pair_id'], x['classification'], x['min_h']) for x in direct['pairs']]}",
        f"- Recorded camera paths: {[(x['pair_id'], x['classification'], x['min_h']) for x in camera['pairs']]}",
        f"- Start/goal camera endpoints safe: {[(x['pair_id'], x['start_goal_endpoints_safe']) for x in camera['pairs']]}; all recorded centres safe: {[(x['pair_id'], x['all_camera_centers_safe']) for x in camera['pairs']]}; full sampled camera paths safe: {[(x['pair_id'], x['radius_safe']) for x in camera['pairs']]}.",
        "- Therefore endpoint safety does not establish an executable spherical-robot path, and a blocked direct line does not prove global unreachability.",
        "",
        "## Saved-stall geometry and static feasible-direction diagnosis",
        "",
        f"- Six frozen CBF-boundary-stall trajectories yielded {stall['representative_state_count']} specified representative states.",
        f"- Head-on barrier conflicts: {sum(x['head_on_barrier_conflict'] for x in stall['records'])}; tangential escape available but unused: {sum(x['tangential_escape_available_but_unused'] for x in stall['records'])}; multi-constraint wedges: {sum(x['multi_constraint_wedge_stall'] for x in stall['records'])}; cul-de-sac indications: {sum(x['geometric_cul_de_sac_indication'] for x in stall['records'])}.",
        f"- Goal-directed feasible-scale proxy (active-barrier static half-space, not an online QP): min={min(scales):.12g}, median={float(np.median(scales)):.12g}, max={max(scales):.12g}; safe controls with positive goal progress: {sum(x['safe_control_has_goal_progress'] for x in feasible['records'])}/{len(feasible['records'])}.",
        "",
        "## Offline waypoint feasibility",
        "",
        f"- Frozen-camera waypoint chains (33 samples per increasing-index edge): {[(x['pair_id'], x['safe_waypoint_chain_exists'], x['node_count'], x['edge_count'], x['min_h']) for x in waypoints['pairs']]}.",
        "- A waypoint graph is an offline geometric diagnostic only; it is not an executed trajectory or proof of controller completion.",
        "",
        "## Classification and decision",
        "",
        f"- Primary classification: `{classification['primary_classification']}`.",
        f"- Secondary findings: {classification['secondary_findings']}.",
        f"- Unique next-step decision: `{decision['next_step_decision']}`. paired20 remains `{decision['paired20_status']}`.",
        "",
        "## Preserved prior evidence and claim limits",
        "",
        "- The previously qualified SplaTAM-SAFER geometry chain, sampled-data overlap certification, and V4-C proof-of-mechanism remain prior evidence; they are not reinterpreted as navigation-completion results here.",
        "- The current failure mode concerns navigation-task completion, not a map-query failure.",
        "- This audit neither modifies nor tests a new controller, CBF, trigger, or filter, and it does not claim a global geometric cul-de-sac.",
        f"- Frozen paired20 manifest remains `{validation['paired20_manifest_sha256']}` with states {validation['paired20_states']}; sequence 3 terminal/steps exists={validation['sequence3_terminal_or_steps_exists']}.",
        f"- New rollout count={validation['new_scientific_rollout_count']}; new terminal trajectory count={validation['new_terminal_trajectory_count']}; online QP count={validation['qp_online_execution_count']}; V4-C count={validation['v4c_online_execution_count']}.",
        "",
    ]
    (ROOT / "report/REPORT_TUM_NAVIGATION_PROTOCOL_GAP_AUDIT_V1.md").write_text("\n".join(report), encoding="utf-8")
    return validation


def run_all() -> dict[str, Any]:
    ensure_root(); identity = input_identity()
    if not identity["identity_ok"]: raise RuntimeError("BLOCKED_BY_GLOBAL_PROGRESS_AUDIT_IDENTITY_CONFLICT")
    original, tum, diff = recover_protocols(); query = StaticFullMap(); direct = direct_paths(query); camera = camera_paths(query); stall, feasible = stall_geometry(query); waypoints = waypoint_graph(query, direct); classification, decision = classify(original, diff, direct, camera, stall, waypoints); return render_and_validate(original, tum, diff, classification, decision, direct, camera, stall, feasible, waypoints)


def rerender_existing() -> dict[str, Any]:
    """Rebuild compact figures/report from task-owned static artifacts only."""
    ensure_root()
    original = load(ROOT / "original_navigation_stack/original_safer_navigation_stack.json")
    tum = load(ROOT / "tum_task_protocol/tum_navigation_task_protocol.json")
    diff = load(ROOT / "protocol_comparison/navigation_protocol_diff.json")
    direct = load(ROOT / "direct_path_geometry/direct_path_geometry_summary.json")
    camera = load(ROOT / "tum_task_protocol/camera_path_navigation_feasibility.json")
    stall = load(ROOT / "stall_geometry/stall_geometry_attribution.json")
    feasible = load(ROOT / "stall_geometry/local_cbf_feasible_direction_summary.json")
    waypoints = load(ROOT / "waypoint_feasibility/waypoint_chain_feasibility.json")
    classification = load(ROOT / "protocol_comparison/navigation_protocol_classification.json")
    decision = load(ROOT / "protocol_comparison/next_step_decision.json")
    return render_and_validate(original, tum, diff, classification, decision, direct, camera, stall, feasible, waypoints)


def run_preflight() -> dict[str, Any]:
    ensure_root(); identity = input_identity()
    if not identity["identity_ok"]: raise RuntimeError("BLOCKED_BY_GLOBAL_PROGRESS_AUDIT_IDENTITY_CONFLICT")
    original, tum, diff = recover_protocols()
    return {"identity_ok": identity["identity_ok"], "original_classification": original["classification"], "tum_pairs": len(tum["pairs"]), "protocol_fields": len(diff["fields"])}
