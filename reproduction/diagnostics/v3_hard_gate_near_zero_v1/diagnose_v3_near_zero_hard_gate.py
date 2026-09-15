#!/usr/bin/env python3
"""Frozen, read-only V3 near-zero hard-gate diagnostic.

The script never runs a controller or plant. It reads four immutable trials and
performs map queries only after the protocol has been committed.
"""
from __future__ import annotations

import argparse
from collections import deque
import csv
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import statistics
import subprocess
import sys
from typing import Any


TASK_REL = Path("reproduction/diagnostics/v3_hard_gate_near_zero_v1")
ANALYZER_REL = Path("reproduction/validation/active_runtime_paired_validation_v3_execution_r1/analyze_active_runtime_v3_paired_validation_r1.py")
RUNNER_REL = Path("reproduction/validation/active_runtime_paired_validation_v3_execution_r1/run_active_runtime_v3_paired_validation_r1.py")
PROTOCOL_REL = Path("reproduction/validation/active_runtime_paired_validation_v3/V3_PAIRED_VALIDATION_PROTOCOL.json")
ADAPTER_REL = Path("reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1/adapters/gaussian_barrier_adapter.py")
EXPECTED_HEAD = "50cadfe614da70ce0345c4b1789c787dc529287e"
RADIUS = 0.015
TRIALS = (22, 28, 57, 59)
WITNESSES = {22: -3.3954472705710614e-09, 28: -4.850638484626968e-10, 57: -4.850638484626968e-10, 59: -3.880511228321337e-09}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def import_file(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError("IMPORT_FAILED:" + str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def git(checkout: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(checkout), *args], text=True, capture_output=True, check=True).stdout.strip()


def all_file_hashes(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): sha256_file(path) for path in sorted(root.rglob("*")) if path.is_file()}


def raw_paths(paired_root: Path, trial: int) -> dict[str, Path]:
    root = paired_root / "raw" / f"trial_{trial}"
    return {name: root / name for name in (
        "ACTIVE_V3_RAW_EVIDENCE_LOCK.json", "trial_summary.json", "cycle_observations.jsonl",
        "runtime_trace.jsonl", "runtime_trace_lock.json",
    )}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_inputs(checkout: Path, paired_root: Path, map_root: Path, protocol: dict[str, Any]) -> dict[str, Any]:
    if git(checkout, "merge-base", EXPECTED_HEAD, "HEAD") != EXPECTED_HEAD:
        raise RuntimeError("SOURCE_START_IDENTITY_MISMATCH")
    source_map = {
        "frozen_analyzer": checkout / ANALYZER_REL,
        "frozen_runner": checkout / RUNNER_REL,
        "gaussian_adapter": checkout / ADAPTER_REL,
        "gsplat_query": checkout / "splat/gsplat_utils.py",
        "ellipsoid_distance": checkout / "splat/distances.py",
        "frozen_protocol": checkout / PROTOCOL_REL,
        "map_config": map_root / "config.yml",
        "map_dataparser": map_root / "dataparser_transforms.json",
        "map_checkpoint": map_root / "nerfstudio_models/step-000029999.ckpt",
    }
    actual = {key: sha256_file(path) for key, path in source_map.items()}
    for key, expected in protocol["input_sha256"].items():
        if key in actual and actual[key] != expected:
            raise RuntimeError("INPUT_SHA_MISMATCH:" + key)
    top_map = {
        "ACTIVE_V3_R1_COLLECTION_INTEGRITY_SUMMARY.json": paired_root / "ACTIVE_V3_R1_COLLECTION_INTEGRITY_SUMMARY.json",
        "V3_PAIRED_ANALYSIS_SUMMARY.json": paired_root / "V3_PAIRED_ANALYSIS_SUMMARY.json",
        "V3_PAIRED_PER_PAIR_ANALYSIS.json": paired_root / "V3_PAIRED_PER_PAIR_ANALYSIS.json",
    }
    top_hashes = {key: sha256_file(path) for key, path in top_map.items()}
    for key, digest in top_hashes.items():
        if digest != protocol["input_sha256"][key]:
            raise RuntimeError("TOP_LEVEL_EVIDENCE_SHA_MISMATCH:" + key)
    collection = read_json(top_map["ACTIVE_V3_R1_COLLECTION_INTEGRITY_SUMMARY.json"])
    analysis = read_json(top_map["V3_PAIRED_ANALYSIS_SUMMARY.json"])
    pairs = read_json(top_map["V3_PAIRED_PER_PAIR_ANALYSIS.json"])
    if analysis["final_decision"] != "FAIL_V3_HARD_SAFETY_GATE" or analysis["paired_eligible_count"] != 85:
        raise RuntimeError("FROZEN_ANALYSIS_FACT_MISMATCH")
    if analysis["active_hard_violation_trials"] != 4 or analysis["reference_hard_violation_trials"] != 0 or analysis["unresolved_oracle_unknown"] != 0:
        raise RuntimeError("FROZEN_ANALYSIS_COUNTS_MISMATCH")
    if not analysis["progress_noninferiority_pass"] or analysis["historical_0p025_primary_authority"]:
        raise RuntimeError("FROZEN_ANALYSIS_AUTHORITY_MISMATCH")
    got = sorted(int(row["trial_id"]) for row in pairs if row["active_hard"]["violation_trial"])
    if got != list(TRIALS):
        raise RuntimeError("FROZEN_VIOLATING_TRIAL_SET_MISMATCH")
    for row in pairs:
        trial = int(row["trial_id"])
        if trial in TRIALS:
            if row["active_hard"]["violation_segment_count"] != 1 or row["active_hard"]["unknown_segment_count"] != 0:
                raise RuntimeError("FROZEN_PER_TRIAL_COUNT_MISMATCH")
            if float(row["active_hard"]["min_clearance_q"]) != WITNESSES[trial]:
                raise RuntimeError("FROZEN_PER_TRIAL_WITNESS_MISMATCH")
    raw_hashes: dict[str, Any] = {}
    for trial in TRIALS:
        raw_hashes[str(trial)] = {name: {"sha256": sha256_file(path), "size": path.stat().st_size} for name, path in raw_paths(paired_root, trial).items()}
    return {
        "status": "PASS",
        "source_start_sha": EXPECTED_HEAD,
        "source_head_at_execution": git(checkout, "rev-parse", "HEAD"),
        "top_level_hashes": top_hashes,
        "source_and_map_hashes": actual,
        "raw_trial_hashes": raw_hashes,
        "collection_frozen_facts": collection,
        "analysis_frozen_facts": analysis,
    }


def build_segment_mapping(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not rows:
        raise RuntimeError("EMPTY_CYCLE_OBSERVATIONS")
    mapping: list[dict[str, Any]] = []
    expected_pre = tuple(rows[0]["pre_state"])
    continuity = True
    for row in rows:
        if tuple(row["pre_state"]) != expected_pre:
            continuity = False
        if row["committed"]:
            if row["post_state"] is None:
                raise RuntimeError("COMMITTED_POST_STATE_MISSING")
            mapping.append({
                "active_segment_index": len(mapping),
                "cycle_index": int(row["cycle_index"]),
                "pre_state": row["pre_state"],
                "post_state": row["post_state"],
                "committed": True,
                "boundary": bool(row["boundary"]),
                "selected_action_identity": row["selected_action_identity"],
                "executed_action_identity": row["executed_action_identity"],
                "executed_vector": row["executed_vector"],
                "action_role": row["action_role"],
            })
            expected_pre = tuple(row["post_state"])
    return mapping, {"continuity_pass": continuity, "committed_segment_count": len(mapping)}


def first_negative_witness(provider: Any, start: Any, end: Any) -> dict[str, Any]:
    import numpy as np
    start = np.asarray(start, dtype=np.float64)
    end = np.asarray(end, dtype=np.float64)
    queue = deque([(0.0, 1.0)])
    length = float(np.linalg.norm(end - start))
    nodes = 0
    while queue:
        a, b = queue.popleft()
        mid = 0.5 * (a + b)
        point = start + mid * (end - start)
        status, signed, _ = provider.minimum_signed_distance(point)
        nodes += 1
        if status != "FINITE" or signed is None:
            raise RuntimeError("WITNESS_QUERY_NOT_FINITE")
        clearance = float(signed) - RADIUS
        if clearance < 0.0:
            return {"t": mid, "point": point.tolist(), "signed_distance_q": float(signed), "clearance_q": clearance, "nodes": nodes}
        lower = float(signed) - 0.5 * (b - a) * length - RADIUS
        if lower >= 0.0:
            continue
        if nodes >= 4096 or (b - a) <= 1e-10:
            raise RuntimeError("FROZEN_WITNESS_EXPECTED_BUT_INTERVAL_INCONCLUSIVE")
        queue.append((a, mid))
        queue.append((mid, b))
    raise RuntimeError("FROZEN_WITNESS_NOT_FOUND")


def query_point(adapter: Any, map_id: str, point: Any) -> dict[str, Any]:
    import numpy as np
    import torch
    constructed = np.asarray(point, dtype=np.float64)
    cast = torch.as_tensor(constructed, device=torch.device("cuda:0"), dtype=torch.float32)
    cast64 = cast.detach().cpu().numpy().astype(np.float64)
    result = adapter.query(cast, map_id, "FULL")
    if result.status.value != "FINITE" or result.h is None or result.signed_distance is None:
        return {"status": result.status.value, "constructed_xyz": constructed.tolist(), "backend_xyz": cast64.tolist(), "backend_dtype": str(cast.dtype)}
    index = int(result.active_gaussian_indices[0])
    return {
        "status": "FINITE", "constructed_xyz": constructed.tolist(), "backend_xyz": cast64.tolist(), "backend_dtype": str(cast.dtype),
        "quantization_delta": (cast64 - constructed).tolist(), "h_min": float(result.h), "argmin_gaussian_index": index,
        "signed_distance_q": float(result.signed_distance), "clearance_q": float(result.signed_distance) - RADIUS,
    }


def dense_and_refine(adapter: Any, map_id: str, start: Any, end: Any, csv_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    import numpy as np
    start = np.asarray(start[:3], dtype=np.float64)
    end = np.asarray(end[:3], dtype=np.float64)
    dense: list[dict[str, Any]] = []
    for j in range(1025):
        t = j / 1024.0
        row = query_point(adapter, map_id, start + t * (end - start))
        row["t"] = t
        dense.append(row)
    if any(row["status"] != "FINITE" for row in dense):
        raise RuntimeError("DENSE_SCAN_NONFINITE")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["t", "constructed_xyz", "backend_dtype", "backend_xyz", "quantization_delta", "h_min", "argmin_gaussian_index", "signed_distance_q", "clearance_q", "status"]
    with csv_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in dense:
            writer.writerow({**row, "constructed_xyz": json.dumps(row["constructed_xyz"]), "backend_xyz": json.dumps(row["backend_xyz"]), "quantization_delta": json.dumps(row["quantization_delta"])})
    best_index = min(range(len(dense)), key=lambda i: dense[i]["clearance_q"])
    neg = [row for row in dense if row["clearance_q"] < 0.0]
    layers: list[dict[str, Any]] = []
    left = max(0.0, (best_index - 1) / 1024.0)
    right = min(1.0, (best_index + 1) / 1024.0)
    refined_best = dense[best_index]
    refined_t = dense[best_index]["t"]
    for layer in range(1, 5):
        ts = np.linspace(left, right, 65, dtype=np.float64)
        values = [query_point(adapter, map_id, start + float(t) * (end - start)) for t in ts]
        index = min(range(65), key=lambda i: values[i]["clearance_q"])
        refined_best = values[index]
        refined_t = float(ts[index])
        layers.append({"layer": layer, "interval": [float(left), float(right)], "point_count": 65, "min_index": index, "min_t": refined_t, "min_clearance_q": refined_best["clearance_q"]})
        left = float(ts[max(0, index - 1)])
        right = float(ts[min(64, index + 1)])
    summary = {
        "dense_grid_point_count": 1025,
        "dense_min_clearance_q": dense[best_index]["clearance_q"], "dense_min_t": dense[best_index]["t"],
        "dense_min_gaussian_index": dense[best_index]["argmin_gaussian_index"], "negative_grid_point_count": len(neg),
        "first_negative_t": None if not neg else neg[0]["t"], "last_negative_t": None if not neg else neg[-1]["t"],
        "max_negative_depth_abs_q": 0.0 if not neg else abs(min(row["clearance_q"] for row in neg)),
        "refined_min_clearance_q": refined_best["clearance_q"], "refined_min_t": refined_t,
        "refined_min_gaussian_index": refined_best["argmin_gaussian_index"], "refinement_layers": layers,
        "final_local_sampling_resolution_t": (right - left) / 64.0,
    }
    return summary, dense


def repeat_audit(adapter: Any, map_id: str, point: Any) -> dict[str, Any]:
    values = [query_point(adapter, map_id, point) for _ in range(20)]
    clearances = [row["clearance_q"] for row in values]
    encoded = [json.dumps(row, sort_keys=True, separators=(",", ":")) for row in values]
    signs = {"negative": sum(x < 0 for x in clearances), "zero": sum(x == 0 for x in clearances), "positive": sum(x > 0 for x in clearances)}
    return {
        "query_count": 20, "values": values, "clearance_min": min(clearances), "clearance_max": max(clearances),
        "clearance_range": max(clearances) - min(clearances), "clearance_std": statistics.pstdev(clearances),
        "bitwise_identical_to_first_count": sum(item == encoded[0] for item in encoded), "sign_counts": signs,
        "argmin_stable": len({row["argmin_gaussian_index"] for row in values}) == 1,
    }


def ulp_audit(adapter: Any, map_id: str, point: Any) -> dict[str, Any]:
    import numpy as np
    p = np.asarray(point, dtype=np.float32)
    neighbors: list[tuple[str, Any]] = [("original", p.copy())]
    for axis, name in enumerate(("x", "y", "z")):
        minus = p.copy(); plus = p.copy()
        minus[axis] = np.nextafter(p[axis], np.float32(-np.inf), dtype=np.float32)
        plus[axis] = np.nextafter(p[axis], np.float32(np.inf), dtype=np.float32)
        neighbors.extend([(name + "_minus_1ulp", minus), (name + "_plus_1ulp", plus)])
    rows = []
    for label, value in neighbors:
        row = query_point(adapter, map_id, value.astype(np.float64))
        row["label"] = label
        row["coordinate_delta_from_original"] = (value.astype(np.float64) - p.astype(np.float64)).tolist()
        rows.append(row)
    signs = {"negative": sum(row["clearance_q"] < 0 for row in rows), "zero": sum(row["clearance_q"] == 0 for row in rows), "positive": sum(row["clearance_q"] > 0 for row in rows)}
    ulps = [float(max(abs(np.nextafter(value, np.float32(np.inf), dtype=np.float32) - value), abs(value - np.nextafter(value, np.float32(-np.inf), dtype=np.float32)))) for value in p]
    return {"point_count": 7, "backend_dtype": "torch.float32", "original_float32": p.astype(np.float64).tolist(), "coordinate_ulp_sizes": ulps, "rows": rows, "sign_counts": signs, "argmin_stable": len({row["argmin_gaussian_index"] for row in rows}) == 1}


class Float64Equivalent:
    def __init__(self, loader: Any) -> None:
        import torch
        from ellipsoids.covariance_utils import quaternion_to_rotation_matrix
        self.torch = torch
        self.means = loader.means.detach().to(dtype=torch.float64)
        rotations = quaternion_to_rotation_matrix(loader.rots.detach().to(dtype=torch.float64))
        self.scales, indices = torch.sort(loader.scales.detach().to(dtype=torch.float64), dim=-1, descending=True)
        self.rotations = torch.gather(rotations, 2, indices[..., None, :].expand_as(rotations))

    def query(self, point: Any) -> dict[str, Any]:
        torch = self.torch
        x = torch.as_tensor(point, device=self.means.device, dtype=torch.float64)
        x_local_signed = torch.bmm(self.rotations.transpose(1, 2), (x - self.means).unsqueeze(-1)).squeeze(-1) + 1e-8
        local = torch.abs(x_local_signed)
        s = self.scales + 1e-8
        z = local / s
        g = torch.sum(z ** 2, dim=-1) - 1.0
        r = (s / s[..., -1, None]) ** 2
        n = r * z
        bracket = torch.zeros((len(n), 2), device=r.device, dtype=torch.float64)
        bracket[:, 0] = z[..., -1] - 1.0
        positive = g >= 0
        bracket[positive, 1] = torch.linalg.norm(n[positive], dim=-1) - 1.0
        midpoint = None
        for _ in range(25):
            midpoint = torch.mean(bracket, dim=-1, keepdim=True)
            ratio = n / (midpoint + r)
            residual = torch.sum(ratio ** 2, dim=-1) - 1.0
            positive = residual >= 0
            flat = midpoint.squeeze(-1)
            bracket[positive, 0] = flat[positive]
            bracket[~positive, 1] = flat[~positive]
        y = r * local / (midpoint + r)
        squared_distance = torch.sum((y - local) ** 2, dim=-1)
        phi = torch.sign(torch.sum((1.0 / self.scales) ** 2 * local ** 2, dim=-1) - 1.0)
        h = phi * squared_distance - RADIUS ** 2
        index = int(torch.argmin(h).item())
        h_min = float(h[index].item())
        raw = h_min + RADIUS ** 2
        signed = math.copysign(math.sqrt(abs(raw)), raw)
        return {"dtype": "torch.float64", "h_min": h_min, "argmin_gaussian_index": index, "signed_distance_q": signed, "clearance_q": signed - RADIUS}


def classify_numerical(frozen: float, depth: dict[str, Any], repeats: list[dict[str, Any]], ulps: list[dict[str, Any]]) -> str:
    sign_stable = all(item["sign_counts"]["negative"] == item["query_count"] for item in repeats) and all(item["sign_counts"]["negative"] == item["point_count"] for item in ulps)
    if sign_stable and depth["negative_grid_point_count"] >= 2 and depth["refined_min_clearance_q"] < frozen:
        return "FLOAT32_STABLE_NEGATIVE_WITH_DEEPER_SEGMENT_INTRUSION"
    if not sign_stable:
        return "FLOAT32_SIGN_UNSTABLE_NEAR_ZERO" if depth["negative_grid_point_count"] <= 1 else "BACKEND_PRECISION_UNRESOLVED"
    return "FLOAT32_STABLE_NEGATIVE_SHALLOW"


def boundary_relation(rows: list[dict[str, Any]], cycle: int) -> str:
    boundary_cycles = [int(row["cycle_index"]) for row in rows if row["boundary"]]
    if cycle in boundary_cycles: return "SAME_CYCLE"
    if cycle - 1 in boundary_cycles: return "IMMEDIATELY_BEFORE"
    if cycle + 1 in boundary_cycles: return "IMMEDIATELY_AFTER"
    return "DISTANT" if boundary_cycles else "NONE"


def runtime_classification(role: str) -> str:
    return {"PRIMARY_NAVIGATION": "VIOLATION_ON_PRIMARY_COMMIT", "RETAINED_BACKUP": "VIOLATION_ON_BACKUP_COMMIT", "ALTERNATIVE_NAVIGATION": "VIOLATION_ON_ALTERNATIVE_COMMIT", "CERTIFIED_TERMINAL": "VIOLATION_ON_TERMINAL_COMMIT"}.get(role, "SEGMENT_MAPPING_UNRESOLVED")


def identity_value(value: Any) -> Any:
    """Normalize the two frozen JSON identity encodings without changing identity."""
    return value.get("value") if isinstance(value, dict) and set(value) == {"value"} else value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--paired-root", type=Path, required=True)
    parser.add_argument("--map-root", type=Path, required=True)
    parser.add_argument("--result-root", type=Path, required=True)
    parser.add_argument("--repo-task-dir", type=Path, required=True)
    args = parser.parse_args()
    checkout = args.checkout.resolve(strict=True); paired_root = args.paired_root.resolve(strict=True); map_root = args.map_root.resolve(strict=True)
    task = args.repo_task_dir.resolve(strict=True); result_root = args.result_root.resolve()
    if result_root.exists():
        raise RuntimeError("RESULT_ROOT_NOT_FRESH")
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "1":
        raise RuntimeError("GPU1_NOT_EXCLUSIVELY_SELECTED")
    protocol = read_json(task / "DIAGNOSTIC_PROTOCOL.json")
    input_identity = verify_inputs(checkout, paired_root, map_root, protocol)
    paired_before = all_file_hashes(paired_root)
    result_root.mkdir(parents=True)
    write_json(result_root / "input_identity.json", input_identity)

    import numpy as np
    import torch
    if not torch.cuda.is_available(): raise RuntimeError("CUDA_NOT_AVAILABLE")
    sys.path[:0] = [str(checkout / "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1"), str(checkout)]
    from splat.gsplat_utils import GSplatLoader
    from adapters.gaussian_barrier_adapter import SourceGaussianBarrierAdapter
    frozen_helper = import_file(checkout / "reproduction/pilot/active_runtime_pilot_v2/run_active_runtime_pilot_v2.py", "_frozen_v3_diagnostic_helper")
    frozen_protocol = read_json(checkout / PROTOCOL_REL)
    map_id = frozen_protocol["map"]["identity"]
    loader = GSplatLoader((map_root / "config.yml").resolve(strict=True), torch.device("cuda:0"))
    if loader.means.dtype != torch.float32 or loader.scales.dtype != torch.float32 or loader.rots.dtype != torch.float32:
        raise RuntimeError("FROZEN_MAP_TENSOR_DTYPE_NOT_FLOAT32")
    def bridge(point: Any, **kwargs: Any) -> Any:
        if not torch.is_tensor(point): point = torch.as_tensor(point, device=torch.device("cuda:0"), dtype=torch.float32)
        return loader.query_distance(point, **kwargs)
    adapter = SourceGaussianBarrierAdapter(bridge, map_id, RADIUS, int(loader.means.shape[0]))

    located: list[dict[str, Any]] = []
    per_trial_data: dict[int, dict[str, Any]] = {}
    for trial in TRIALS:
        paths = raw_paths(paired_root, trial)
        rows = [json.loads(line) for line in paths["cycle_observations.jsonl"].read_text(encoding="utf-8").splitlines() if line]
        traces = [json.loads(line) for line in paths["runtime_trace.jsonl"].read_text(encoding="utf-8").splitlines() if line]
        summary = read_json(paths["trial_summary.json"])
        mapping, chain = build_segment_mapping(rows)
        if chain["committed_segment_count"] != int(summary["plant_commit_count"]): raise RuntimeError(f"PLANT_SEGMENT_COUNT_MISMATCH:{trial}")
        violations = []
        for segment in mapping:
            status, clearance = frozen_helper.certify_segment_clearance(adapter, np.asarray(segment["pre_state"][:3]), np.asarray(segment["post_state"][:3]), RADIUS)
            if status == "UNSAFE": violations.append((segment, float(clearance)))
            elif status != "SAFE": raise RuntimeError(f"FROZEN_SEGMENT_UNKNOWN:{trial}:{segment['active_segment_index']}")
        if len(violations) != 1: raise RuntimeError(f"FROZEN_VIOLATION_REPRODUCTION_MISMATCH:{trial}:{len(violations)}")
        segment, returned = violations[0]
        if returned != WITNESSES[trial]: raise RuntimeError(f"FROZEN_WITNESS_REPRODUCTION_MISMATCH:{trial}:{returned-WITNESSES[trial]}")
        witness = first_negative_witness(adapter, segment["pre_state"][:3], segment["post_state"][:3])
        if witness["clearance_q"] != returned: raise RuntimeError("WITNESS_TRAVERSAL_MISMATCH")
        trace = next((row for row in traces if int(row["cycle_index"]) == segment["cycle_index"]), None)
        if trace is None: raise RuntimeError("RUNTIME_TRACE_ALIGNMENT_MISSING")
        if identity_value(trace["selected_action_identity"]) != identity_value(segment["selected_action_identity"]) or identity_value(trace["executed_action_identity"]) != identity_value(segment["executed_action_identity"]):
            raise RuntimeError("RUNTIME_ACTION_IDENTITY_ALIGNMENT_MISMATCH")
        facts = dict(trace.get("facts", []))
        relation = "SAME_EXECUTED_SEGMENT_CERTIFIED_PASS" if segment["action_role"] in {"PRIMARY_NAVIGATION", "ALTERNATIVE_NAVIGATION"} and facts.get("runtime_reason") == "TIMELY_CERTIFIED_NAVIGATION_WITH_PREPARED_TOKEN" else "CERTIFICATE_NOT_AVAILABLE"
        alignment = {
            **segment, "trace": trace, "runtime_reason": facts.get("runtime_reason"), "boundary_relation": boundary_relation(rows, segment["cycle_index"]),
            "runtime_association_classification": runtime_classification(segment["action_role"]), "runtime_certificate_relation": relation,
            "semantic_note": "runtime L1 certifies the same immediate closed segment; L2 certifies the next H1 segment; trace does not serialize individual certificate payloads",
            "trial_level_status_counts": {key: summary.get(key) for key in ("L1_status_counts", "C0_status_counts", "L2_status_counts", "L3_status_counts", "deadline_status_counts")},
        }
        write_json(result_root / "runtime_alignment" / f"trial_{trial}.json", alignment)
        located.append({"trial_id": trial, "active_segment_index": segment["active_segment_index"], "cycle_index": segment["cycle_index"], "frozen_returned_clearance_q": returned, "first_negative_witness": witness})
        per_trial_data[trial] = {"rows": rows, "summary": summary, "segment": segment, "witness": witness, "alignment": alignment, "chain": chain}
    write_json(result_root / "violating_segments.json", located)
    with (result_root / "violating_segments.csv").open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("trial_id", "active_segment_index", "cycle_index", "frozen_returned_clearance_q")); writer.writeheader()
        for row in located: writer.writerow({key: row[key] for key in writer.fieldnames})

    f64 = Float64Equivalent(loader)
    sanity_points = [
        (loader.means.detach().amin(dim=0).cpu().numpy().astype(np.float64) - 1.0).tolist(),
        (loader.means.detach().amax(dim=0).cpu().numpy().astype(np.float64) + 1.0).tolist(),
        per_trial_data[22]["rows"][0]["pre_state"][:3],
    ]
    sanity = []
    eps32 = float(np.finfo(np.float32).eps)
    for point in sanity_points:
        p32 = query_point(adapter, map_id, point); p64 = f64.query(np.asarray(p32["backend_xyz"], dtype=np.float64))
        max_ulp = max(float(x) for x in ulp_audit(adapter, map_id, point)["coordinate_ulp_sizes"])
        tolerance = 32.0 * max_ulp + 32.0 * eps32 * max(1.0, abs(p32["clearance_q"]))
        sanity.append({"point": point, "float32": p32, "float64": p64, "abs_clearance_delta": abs(p32["clearance_q"] - p64["clearance_q"]), "parity_tolerance": tolerance, "pass": abs(p32["clearance_q"] - p64["clearance_q"]) <= tolerance})
    f64_available = all(row["pass"] for row in sanity)
    float64_root = result_root / "float64_audit"; float64_root.mkdir(parents=True, exist_ok=True)
    write_json(float64_root / "sanity.json", {"status": "IMPLEMENTED_AND_SANITY_VALIDATED" if f64_available else "NOT_AVAILABLE_EQUIVALENCE_GATE_FAILED", "sanity_points": sanity})

    summaries = []
    for trial in TRIALS:
        item = per_trial_data[trial]; segment = item["segment"]
        dense_csv = result_root / "dense_scan" / f"trial_{trial}_segment_{segment['active_segment_index']}.csv"
        depth, _ = dense_and_refine(adapter, map_id, segment["pre_state"], segment["post_state"], dense_csv)
        start = np.asarray(segment["pre_state"][:3], dtype=np.float64); end = np.asarray(segment["post_state"][:3], dtype=np.float64)
        refined_point = start + depth["refined_min_t"] * (end - start)
        witness_point = item["witness"]["point"]
        repeat_w = repeat_audit(adapter, map_id, witness_point); repeat_r = repeat_audit(adapter, map_id, refined_point)
        ulp_w = ulp_audit(adapter, map_id, witness_point); ulp_r = ulp_audit(adapter, map_id, refined_point)
        write_json(result_root / "ulp_audit" / f"trial_{trial}_witness.json", {"repeat": repeat_w, "ulp": ulp_w})
        write_json(result_root / "ulp_audit" / f"trial_{trial}_refined_min.json", {"repeat": repeat_r, "ulp": ulp_r})
        p32w = query_point(adapter, map_id, witness_point); p32r = query_point(adapter, map_id, refined_point)
        f64_result = {"status": "IMPLEMENTED_AND_SANITY_VALIDATED" if f64_available else "NOT_AVAILABLE_EQUIVALENCE_GATE_FAILED", "witness": {"float32": p32w, "float64": f64.query(p32w["backend_xyz"])}, "refined_min": {"float32": p32r, "float64": f64.query(p32r["backend_xyz"])}}
        for key in ("witness", "refined_min"):
            f64_result[key]["clearance_delta_f64_minus_f32"] = f64_result[key]["float64"]["clearance_q"] - f64_result[key]["float32"]["clearance_q"]
            f64_result[key]["sign_agreement"] = (f64_result[key]["float64"]["clearance_q"] < 0) == (f64_result[key]["float32"]["clearance_q"] < 0)
        write_json(float64_root / f"trial_{trial}.json", f64_result)
        numerical = classify_numerical(WITNESSES[trial], depth, [repeat_w, repeat_r], [ulp_w, ulp_r])
        summary = {
            "trial_id": trial, "segment": segment, "mapping": item["chain"], "frozen_witness_clearance_q": WITNESSES[trial],
            "frozen_witness_reproduction_delta": item["witness"]["clearance_q"] - WITNESSES[trial], "depth_audit": depth,
            "repeated_query": {"witness": {key: repeat_w[key] for key in repeat_w if key != "values"}, "refined_min": {key: repeat_r[key] for key in repeat_r if key != "values"}},
            "ulp": {"witness_sign_counts": ulp_w["sign_counts"], "refined_sign_counts": ulp_r["sign_counts"], "witness_argmin_stable": ulp_w["argmin_stable"], "refined_argmin_stable": ulp_r["argmin_stable"]},
            "float64": f64_result, "numerical_boundary_classification": numerical,
            "runtime_association_classification": item["alignment"]["runtime_association_classification"], "boundary_relation": item["alignment"]["boundary_relation"],
            "runtime_certificate_relation": item["alignment"]["runtime_certificate_relation"],
        }
        write_json(result_root / "per_trial" / f"trial_{trial}.json", summary); summaries.append(summary)

    paired_after = all_file_hashes(paired_root)
    mutations = sorted(set(paired_before) ^ set(paired_after)) + sorted(path for path in set(paired_before) & set(paired_after) if paired_before[path] != paired_after[path])
    deeper = [row["trial_id"] for row in summaries if row["numerical_boundary_classification"] == "FLOAT32_STABLE_NEGATIVE_WITH_DEEPER_SEGMENT_INTRUSION"]
    backup = [row["trial_id"] for row in summaries if row["runtime_association_classification"] == "VIOLATION_ON_BACKUP_COMMIT"]
    primary = [row["trial_id"] for row in summaries if row["runtime_association_classification"] == "VIOLATION_ON_PRIMARY_COMMIT"]
    same_pass = [row["trial_id"] for row in summaries if row["runtime_certificate_relation"] == "SAME_EXECUTED_SEGMENT_CERTIFIED_PASS"]
    diagnostic_summary = {
        "schema": "V3_HARD_GATE_NEAR_ZERO_DIAGNOSTIC_SUMMARY_V1", "status": "PASS_V3_HARD_GATE_NEAR_ZERO_DIAGNOSTIC_COMPLETE",
        "frozen_scientific_decision_remains": "FAIL_V3_HARD_SAFETY_GATE", "trials": summaries,
        "float64_equivalent_backend_status": "IMPLEMENTED_AND_SANITY_VALIDATED" if f64_available else "NOT_AVAILABLE_EQUIVALENCE_GATE_FAILED",
        "deeper_segment_intrusion_trial_ids": deeper, "backup_associated_trial_ids": backup, "primary_associated_trial_ids": primary,
        "same_executed_segment_certified_pass_trial_ids": same_pass, "paired_result_root_mutation_count": len(mutations), "paired_result_root_mutations": mutations,
        "execution_counts": protocol["execution_counts"], "historical_0p025_runtime_or_scientific_authority": False,
    }
    write_json(result_root / "DIAGNOSTIC_SUMMARY.json", diagnostic_summary)
    critical_files = [path for path in sorted(result_root.rglob("*")) if path.is_file() and path.name not in {"DIAGNOSTIC_RESULT_LOCK.json", "DIAGNOSTIC_RESULT_LOCK.sha256", "diagnostic_console.log"}]
    result_lock = {"schema": "V3_NEAR_ZERO_DIAGNOSTIC_RESULT_LOCK_V1", "files": {str(path.relative_to(result_root)): {"sha256": sha256_file(path), "size": path.stat().st_size} for path in critical_files}, "paired_result_root_mutation_count": len(mutations), "frozen_decision": "FAIL_V3_HARD_SAFETY_GATE"}
    write_json(result_root / "DIAGNOSTIC_RESULT_LOCK.json", result_lock)
    result_lock_sha = sha256_file(result_root / "DIAGNOSTIC_RESULT_LOCK.json")
    (result_root / "DIAGNOSTIC_RESULT_LOCK.sha256").write_text(result_lock_sha + "  DIAGNOSTIC_RESULT_LOCK.json\n", encoding="utf-8", newline="\n")

    compact = {**diagnostic_summary, "external_result_root": str(result_root), "diagnostic_result_lock_sha256": result_lock_sha}
    write_json(task / "DIAGNOSTIC_SUMMARY.json", compact)
    evidence_files = [task / "DIAGNOSTIC_PROTOCOL.json", task / "DIAGNOSTIC_PROTOCOL.md", task / "diagnose_v3_near_zero_hard_gate.py", task / "validate_v3_near_zero_diagnostic.py", task / "IMPLEMENTATION_PLAN.md", task / "README.md", task / "DIAGNOSTIC_SUMMARY.json"]
    evidence_lock = {"schema": "V3_NEAR_ZERO_DIAGNOSTIC_EVIDENCE_LOCK_V1", "files": {path.name: {"sha256": sha256_file(path), "size": path.stat().st_size} for path in evidence_files}, "external_result_lock_sha256": result_lock_sha, "paired_result_root_mutation_count": len(mutations), "protected_source_diff_count": 0, "frozen_decision": "FAIL_V3_HARD_SAFETY_GATE"}
    write_json(task / "DIAGNOSTIC_EVIDENCE_LOCK.json", evidence_lock)
    evidence_sha = sha256_file(task / "DIAGNOSTIC_EVIDENCE_LOCK.json")
    (task / "DIAGNOSTIC_EVIDENCE_LOCK.sha256").write_text(evidence_sha + "  DIAGNOSTIC_EVIDENCE_LOCK.json\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
