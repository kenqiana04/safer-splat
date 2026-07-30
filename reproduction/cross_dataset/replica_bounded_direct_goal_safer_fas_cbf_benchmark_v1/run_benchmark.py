#!/usr/bin/env python3
"""Phase runner and atomic-resume scheduler for the frozen Replica benchmark."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

from benchmark_core import METHODS, FineSphereMap, ReplicaMeshOracle, atomic_json, environment_identity, parse_oracle_distance, project_start_safe, sha256_file, sha256_json

SCRIPT_DIR = Path(__file__).resolve().parent
EXPECTED = {
    "canonical_tree_sha256": "3b318a98a454ec5c36410b3c41dfb3dd4a25b7b5a1899f1f2c939fbf24ad0e55",
    "means_world_m.npy": "e2ca0533767590c0b5ca657ec7f73fd4626a5fbaf07beb2ce76c2c67d1dc4152",
    "scales_linear_m.npy": "d81393a0ede4126a18b49fc9e12cca7476ca665c55fce05242b02766589c59e3",
    "quaternions_wxyz.npy": "a646a65b6665b4f09e7b295172045236eb40934202d5ef19481e963d591d56e1",
    "opacities_probability.npy": "953ed306a6860660568a0e649d1db0dc53fcf33ddbd2d003876682566572f492",
    "colors_rgb.npy": "1e8c6d97d066a269261d620c87841dabe42f2301ed5626449e0c24a237b9554e",
    "voxel_indices_int64.npy": "8e452be734959793f15b2dc9da796ff2f6d702cb03a88d76eb97566ca9b077f0",
    "route_registry_sha256": "ffe0dadd2dcf4de7e0011a9e3ff6bb1170a385957486ffca33832fc90cc355a6",
    "start_safe_registry_sha256": "e58cd9de67928ddc22f493f1eaf182044ac7e009656f092dacea42b6aaceb499",
    "robot_contract_sha256": "681e3112fb4ba7214dc27f2175f81ba6f910064fc14d5c21e5aa2555534f7337",
    "qp_contract_sha256": "2fe08f34912a13d535200054e3e20287e3726ff54ae1a5d8f05c4780afe176de",
    "mesh_oracle_validation_sha256": "d0d1452bdc6ca5d6df32f6b4c20a3d0a0a512804de9f0553cd6cded6317c1fd6",
}
PRIOR = Path("/disk1/zlab/maintenance_records/replica_bounded_direct_goal_gt_gaussian_benchmark_v1")
MAP_DIR = Path("/disk1/zlab/cross_dataset_assets/qualified_replica_gaussian_safety_maps_v1/bounded_direct_goal_v1")
MESH_PATH = Path("/disk1/zlab/cross_dataset_assets/raw/replica/replica_v1/apartment_0/mesh.ply")


def fail(reason: str) -> None:
    raise RuntimeError(reason)


def verify_hash(path: Path, expected: str, label: str) -> str:
    actual = sha256_file(path)
    if actual != expected:
        fail(f"BLOCKED_BY_REPLICA_BENCHMARK_FROZEN_IDENTITY_MISMATCH:{label}:{actual}")
    return actual


def code_hashes() -> dict[str, str]:
    return {path.name: sha256_file(path) for path in sorted(SCRIPT_DIR.glob("*.py"))}


def route_order(route_id: str) -> list[str]:
    digest = hashlib.sha256(f"REPLICA_BENCHMARK_METHOD_ORDER_V1:{route_id}".encode("utf-8")).digest()
    offset = int.from_bytes(digest[:8], "big") % len(METHODS)
    return list(METHODS[offset:] + METHODS[:offset])


def load_config(root: Path) -> dict[str, Any]:
    return json.loads((root / "frozen_inputs.json").read_text(encoding="utf-8"))


def write_manifest(root: Path, **fields: Any) -> None:
    path = root / "run_manifest.json"
    current: dict[str, Any] = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    current.update(fields)
    current["updated_unix_s"] = time.time()
    atomic_json(path, current)


def preflight(root: Path) -> dict[str, Any]:
    map_identity = json.loads((MAP_DIR / "asset_identity.json").read_text(encoding="utf-8"))
    if map_identity.get("canonical_tree_sha256") != EXPECTED["canonical_tree_sha256"]:
        fail("BLOCKED_BY_REPLICA_BENCHMARK_FROZEN_IDENTITY_MISMATCH:canonical_tree")
    arrays = {name: verify_hash(MAP_DIR / name, digest, name) for name, digest in EXPECTED.items() if name.endswith(".npy")}
    route_path = PRIOR / "route_registry/replica_bounded_direct_goal_route_registry.json"
    start_path = PRIOR / "start_state_registry/replica_start_safe_diagnostic_registry.json"
    robot_path = PRIOR / "contract/replica_bounded_robot_contract.json"
    qp_path = PRIOR / "selection/bounded_qp_adapter_contract.json"
    oracle_validation = PRIOR / "mesh_oracle/replica_mesh_collision_oracle_validation.json"
    for path, digest, label in ((route_path, EXPECTED["route_registry_sha256"], "routes"),
                                (start_path, EXPECTED["start_safe_registry_sha256"], "start_states"),
                                (robot_path, EXPECTED["robot_contract_sha256"], "robot"),
                                (qp_path, EXPECTED["qp_contract_sha256"], "qp"),
                                (oracle_validation, EXPECTED["mesh_oracle_validation_sha256"], "oracle")):
        verify_hash(path, digest, label)
    if not MESH_PATH.is_file():
        fail("BLOCKED_BY_FAS_MODULE_PREFLIGHT_VALIDATION:official_mesh_missing")
    routes = json.loads(route_path.read_text(encoding="utf-8"))["routes"]
    starts = json.loads(start_path.read_text(encoding="utf-8"))["states"]
    if len(routes) != 100 or len(starts) != 30:
        fail("BLOCKED_BY_REPLICA_BENCHMARK_FROZEN_IDENTITY_MISMATCH:registry_count")
    if set(METHODS) != {"M0_BOUNDED_SAFER", "M1_BOUNDED_RISK_AWARE_V1", "M2_FAS_START_SAFE", "M3_FAS_START_SAFE_DISCRETE", "M4_FAS_START_SAFE_DISCRETE_RECOVERY"}:
        fail("BLOCKED_BY_FAS_MODULE_PREFLIGHT_VALIDATION:method_matrix")
    frozen_qp = SCRIPT_DIR / "frozen_bounded_qp_adapter.py"
    prior_qp = PRIOR / "selection/bounded_cbf_qp_adapter.py"
    # PR #64 froze the JSON QP contract, not a line-ending-sensitive source
    # blob.  The server handoff contains the same implementation with a
    # packaging-only source hash; bind both hashes for provenance while using
    # the checked-out PR #64 source that this branch inherits.
    if sha256_file(frozen_qp) != "8f77f1f7ebba6c8870fb1cf6f1c7749695bce98bf55c63874ef1516d9c6094e1":
        fail("BLOCKED_BY_REPLICA_BENCHMARK_FROZEN_IDENTITY_MISMATCH:bounded_qp_checkedout_source")
    map_geometry = FineSphereMap(MAP_DIR)
    applicability = []
    for index, route in enumerate(routes):
        ok, clearance = map_geometry.map_applicable(np.asarray(route["start_m"]), np.asarray(route["goal_m"]))
        applicability.append({"route_index": index, "route_id": route["route_id"], "map_applicable": ok,
                              "direct_segment_cg_m": clearance})
    if sum(bool(row["map_applicable"]) for row in applicability) != 99:
        fail("BLOCKED_BY_REPLICA_BENCHMARK_FROZEN_IDENTITY_MISMATCH:map_applicability_not_99")
    root.mkdir(parents=True, exist_ok=True)
    identity = {
        "status": "PASS", "expected": EXPECTED, "arrays": arrays, "map_dir": str(MAP_DIR),
        "route_registry_path": str(route_path), "start_state_registry_path": str(start_path),
        "robot_contract_path": str(robot_path), "qp_contract_path": str(qp_path),
        "mesh_oracle_validation_path": str(oracle_validation), "mesh_backend": str(PRIOR / "tmp/replica_mesh_oracle_backend"),
        "mesh_path": str(MESH_PATH), "map_applicability": applicability, "map_admissible_route_count": 99,
        "map_blocked_route_count": 1, "code_hashes": code_hashes(), "environment": environment_identity(),
        "risk_aware_binding_sha256": sha256_file(SCRIPT_DIR / "risk_aware_v1_binding.json"),
        "bounded_qp_checkedout_source_sha256": sha256_file(frozen_qp),
        "bounded_qp_server_handoff_source_sha256": sha256_file(prior_qp),
        "source_risk_code_sha256": "330f05942800e1bea2639ba21a9e1cd64e0d13c4a784f6adf031fc513dc8a1dc",
    }
    identity["identity_sha256"] = sha256_json(identity)
    atomic_json(root / "frozen_inputs.json", identity)
    atomic_json(root / "preflight" / "frozen_identity.json", identity)
    # Smoke has an independent results root so the locked full schedule remains exactly 500 records.
    smoke = root / "smoke_workspace"; smoke.mkdir(parents=True, exist_ok=True); atomic_json(smoke / "frozen_inputs.json", identity)
    write_manifest(root, status="PREFLIGHT_PASS", identity_sha256=identity["identity_sha256"],
                   completed_records=0, expected_records=500, phase="S0")
    return identity


def static_start_safe(root: Path) -> dict[str, Any]:
    config = load_config(root); states = json.loads(Path(config["start_state_registry_path"]).read_text(encoding="utf-8"))["states"]
    map_geometry = FineSphereMap(Path(config["map_dir"])); projections = []
    points = []
    for index, state in enumerate(states):
        source = np.asarray(state["position_m"], dtype=np.float64); projected = project_start_safe(map_geometry, source)
        projections.append({"index": index, "registry_gt_label": state["classification"], "source_position_m": source.tolist(),
                            "map_initial_cg_m": projected["initial_cg"], "map_label": projected["classification"],
                            "projection_accepted": projected["accepted"], "projection_position_m": np.asarray(projected["position"]).tolist(),
                            "projection_displacement_m": projected["displacement"], "projection_iterations": projected["iterations"],
                            "projected_map_cg_m": projected["final_cg"]})
        points.append(source); points.append(np.asarray(projected["position"], dtype=np.float64))
    oracle = ReplicaMeshOracle(Path(config["mesh_backend"]), Path(config["mesh_path"]), root / "preflight" / "start_safe_oracle")
    rows = oracle.query_points(points, "start_safe_static")
    for index, row in enumerate(projections):
        row["source_gt_clearance_m_evaluation_only"] = parse_oracle_distance(rows[2*index]) - 0.10
        row["projected_gt_clearance_m_evaluation_only"] = parse_oracle_distance(rows[2*index+1]) - 0.10
    confusion = Counter((x["registry_gt_label"], x["map_label"], str(x["projection_accepted"])) for x in projections)
    result = {"state_count": len(projections), "mesh_oracle_controller_input_count": 0, "rows": projections,
              "status": "PASS", "three_way_counts": {"|".join(key): value for key, value in sorted(confusion.items())}}
    atomic_json(root / "preflight" / "start_safe_static_evaluation.json", result)
    return result


def verifier_twice(root: Path) -> dict[str, Any]:
    outputs = []
    for tag in ("fresh_A", "fresh_B"):
        command = [sys.executable, "-B", str(SCRIPT_DIR / "verify_segment_verifier.py"), "--root", str(root), "--tag", tag]
        subprocess.run(command, check=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        outputs.append(json.loads((root / "preflight" / f"segment_verifier_{tag}.json").read_text(encoding="utf-8")))
    comparable = [{key: value for key, value in row.items() if key not in {"tag", "result_sha256"}} for row in outputs]
    status = "PASS" if all(row["status"] == "PASS" for row in outputs) and comparable[0] == comparable[1] else "FAIL"
    result = {"status": status, "fresh_process_repeats": 2, "segment_count_each": 256,
              "max_abs_error_m": max(row["max_abs_error_m"] for row in outputs), "result_sha256_A": outputs[0]["result_sha256"],
              "result_sha256_B": outputs[1]["result_sha256"]}
    atomic_json(root / "preflight" / "segment_verifier_double_validation.json", result)
    if status != "PASS":
        fail("BLOCKED_BY_FAS_MODULE_PREFLIGHT_VALIDATION:segment_verifier")
    return result


def output_trial_id(root: Path, index: int, method: str) -> str:
    config = load_config(root); route = json.loads(Path(config["route_registry_path"]).read_text(encoding="utf-8"))["routes"][index]
    return f"{index:03d}_{method}_{str(route['route_id'])[:12]}"


def is_complete(root: Path, index: int, method: str) -> bool:
    trial_id = output_trial_id(root, index, method); result = root / "results" / f"{trial_id}.json"; marker = root / "results" / f"{trial_id}.complete.json"
    if not result.exists() and not marker.exists(): return False
    if not result.exists() or not marker.exists():
        quarantine = root / "quarantine" / f"{trial_id}_{int(time.time())}"; quarantine.parent.mkdir(parents=True, exist_ok=True)
        if result.exists(): shutil.move(str(result), str(quarantine.with_suffix(".json")))
        if marker.exists(): shutil.move(str(marker), str(quarantine.with_suffix(".marker.json")))
        return False
    record = json.loads(result.read_text(encoding="utf-8")); marker_row = json.loads(marker.read_text(encoding="utf-8")); config = load_config(root)
    if record.get("identity_sha256") != config["identity_sha256"] or marker_row.get("sha256") != sha256_json(record):
        fail("BLOCKED_BY_REPLICA_BENCHMARK_FROZEN_IDENTITY_MISMATCH:resume_record")
    return True


def run_trial(root: Path, index: int, method: str, *, smoke: bool = False) -> None:
    workspace = root / "smoke_workspace" if smoke else root
    if not smoke and is_complete(root, index, method): return
    command = [sys.executable, "-B", str(SCRIPT_DIR / "run_trial.py"), "--root", str(workspace), "--route-index", str(index), "--method", method]
    log = root / "logs" / ("smoke" if smoke else "trials") / f"{index:03d}_{method}.log"; log.parent.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, 4):
        with log.open("a", encoding="utf-8") as handle:
            handle.write(f"attempt={attempt} command={command}\n"); handle.flush()
            completed = subprocess.run(command, stdout=handle, stderr=subprocess.STDOUT,
                                       env={**os.environ, "CUDA_VISIBLE_DEVICES": "1", "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
        if completed.returncode == 0: break
        if attempt == 3: fail("BLOCKED_BY_REPLICA_BENCHMARK_INFRASTRUCTURE:trial_process_retry_exhausted")
    if not smoke:
        record_path = root / "results" / f"{output_trial_id(root,index,method)}.json"
        record = json.loads(record_path.read_text(encoding="utf-8"))
        if record.get("status") == "NUMERICAL_FAILURE":
            fail("BLOCKED_BY_REPLICA_BENCHMARK_NONDETERMINISM_OR_NUMERICAL_FAILURE")
    write_manifest(root, phase="S3_S4", last_trial={"route_index": index, "method": method},
                   completed_records=sum(1 for _ in (root / "results").glob("*.complete.json")))


def smoke(root: Path) -> None:
    config = load_config(root); routes = json.loads(Path(config["route_registry_path"]).read_text(encoding="utf-8"))["routes"]
    selected = []
    for stratum in ("TIGHT", "MODERATE", "OPEN"):
        selected.append(next(index for index, route in enumerate(routes[:20]) if route["clearance_stratum"] == stratum))
    for index in selected:
        for method in METHODS:
            run_trial(root, index, method, smoke=True)
    rows = list((root / "smoke_workspace" / "results").glob("*.json"))
    records = [json.loads(path.read_text(encoding="utf-8")) for path in rows if not path.name.endswith(".complete.json")]
    if len(records) != 15 or any(row.get("status") == "NUMERICAL_FAILURE" for row in records):
        fail("BLOCKED_BY_REPLICA_BENCHMARK_SMOKE")
    result = {"status": "PASS", "route_indices": selected, "records": len(records),
              "terminal_statuses": dict(Counter(row["status"] for row in records))}
    atomic_json(root / "smoke_validation.json", result)
    write_manifest(root, phase="S1", smoke_status="PASS", smoke_records=15)


def execution_lock(root: Path) -> dict[str, Any]:
    config = load_config(root)
    lock = {"status": "LOCKED", "identity_sha256": config["identity_sha256"], "code_hashes": code_hashes(),
            "method_order_rule": "SHA256(REPLICA_BENCHMARK_METHOD_ORDER_V1:{route_id}) balanced cyclic", "trial_seed_rule": "SHA256(REPLICA_BOUNDED_TRIAL_V1:{method_id}:{route_id})",
            "bootstrap_seed": 20260730, "methods": METHODS, "environment": environment_identity(),
            "post_lock_code_change_requires": "BLOCKED_BY_POST_LOCK_IMPLEMENTATION_CHANGE_REQUIRED"}
    lock["lock_sha256"] = sha256_json(lock); atomic_json(root / "benchmark_execution_lock.json", lock)
    write_manifest(root, phase="S2", execution_lock_sha256=lock["lock_sha256"])
    return lock


def check_lock(root: Path) -> None:
    lock = json.loads((root / "benchmark_execution_lock.json").read_text(encoding="utf-8"))
    if lock["code_hashes"] != code_hashes(): fail("BLOCKED_BY_POST_LOCK_IMPLEMENTATION_CHANGE_REQUIRED")
    if lock["identity_sha256"] != load_config(root)["identity_sha256"]: fail("BLOCKED_BY_REPLICA_BENCHMARK_FROZEN_IDENTITY_MISMATCH:post_lock")


def run_schedule(root: Path) -> None:
    check_lock(root); config = load_config(root); routes = json.loads(Path(config["route_registry_path"]).read_text(encoding="utf-8"))["routes"]
    for index, route in enumerate(routes):
        for method in route_order(str(route["route_id"])):
            run_trial(root, index, method)
    records = [json.loads(path.read_text(encoding="utf-8")) for path in (root / "results").glob("*.json") if not path.name.endswith(".complete.json")]
    if len(records) != 500:
        fail("BLOCKED_BY_REPLICA_BENCHMARK_INFRASTRUCTURE:record_count")
    counts = Counter(row["status"] for row in records)
    blocked = sum(1 for row in records if row["status"] == "MAP_GEOMETRY_BLOCKED")
    if blocked != 5:
        fail("BLOCKED_BY_REPLICA_BENCHMARK_INFRASTRUCTURE:map_blocked_accounting")
    write_manifest(root, phase="S5", completed_records=500, terminal_status_counts=dict(counts), status="EXECUTION_COMPLETE")


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, required=True); parser.add_argument("--phase", choices=("preflight", "smoke", "run"), default="run")
    args = parser.parse_args(); root = args.root.resolve()
    if args.phase == "preflight":
        preflight(root); static_start_safe(root); verifier_twice(root)
        write_manifest(root, phase="S0", status="PREFLIGHT_PASS")
    elif args.phase == "smoke":
        if not (root / "frozen_inputs.json").exists(): preflight(root)
        smoke(root); execution_lock(root)
    else:
        if not (root / "benchmark_execution_lock.json").exists():
            if not (root / "frozen_inputs.json").exists(): preflight(root)
            smoke(root); execution_lock(root)
        run_schedule(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
