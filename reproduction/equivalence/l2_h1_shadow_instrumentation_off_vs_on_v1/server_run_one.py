#!/usr/bin/env python3
"""Execute one preregistered Stonehenge trial in one fresh A/B/C process."""

from __future__ import annotations

import argparse
import builtins
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import inspect
import json
import os
from pathlib import Path
import platform
import random
import runpy
import sys
import threading
from typing import Any

import numpy as np
import torch

from canonical_trace_hash import file_sha256, semantic_sha256
from trace_capture import FrozenRunTraceCapture


ARMS = {"A": "NATIVE_OFF", "B": "WRAPPER_OFF", "C": "WRAPPER_ON"}
PR97_HEAD = "7d48bf6c3b8932aa65d851c3cd70404404453cb3"
MAP_RELATIVE = Path("outputs/stonehenge/splatfacto/2024-09-11_100724")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


@contextmanager
def select_exact_official_trial(run_path: Path, trial_id: int):
    """Intercept only run.py:98 zip(x0, xf); delegate every other zip."""
    original_zip = builtins.zip
    evidence = {"selection_hit_count": 0, "delegated_zip_call_count": 0, "target_trial_id": int(trial_id)}
    resolved = str(run_path.resolve())

    def selective_zip(*iterables):
        caller = inspect.currentframe().f_back
        if (
            caller is not None
            and str(Path(caller.f_code.co_filename).resolve()) == resolved
            and caller.f_lineno == 98
            and len(iterables) == 2
            and all(isinstance(item, np.ndarray) and item.shape == (100, 3) for item in iterables)
        ):
            evidence["selection_hit_count"] += 1
            return iter(((iterables[0][trial_id], iterables[1][trial_id]),))
        evidence["delegated_zip_call_count"] += 1
        return original_zip(*iterables)

    builtins.zip = selective_zip
    try:
        yield evidence
    finally:
        builtins.zip = original_zip


@dataclass(frozen=True)
class TaskMapAuthority:
    map_authority_id: str
    artifacts: tuple[dict[str, Any], ...]


def _plain_semantic_sha256(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def task_local_map_authority(checkout: Path) -> TaskMapAuthority:
    """Reproduce PR #97 map semantics without importing observer code in ARM A."""
    map_root = (checkout / MAP_RELATIVE).resolve(strict=True)
    relatives = (
        "config.yml", "dataparser_transforms.json",
        "nerfstudio_models/step-000029999.ckpt",
    )
    records = tuple({
        "relative_path": relative,
        "size": (map_root / relative).stat().st_size,
        "sha256": file_sha256(map_root / relative),
    } for relative in sorted(relatives))
    semantic = {
        "schema_version": "MAP_AUTHORITY_MANIFEST_V1",
        "logical_map_name": "STONEHENGE_OFFICIAL_SAFER_MAP",
        "artifacts": records,
        "representation_contract": "OFFICIAL_NERFSTUDIO_SPLATFACTO_ANISOTROPIC_GAUSSIAN_MAP",
        "robot_radius": 0.10,
        "safety_margin": 0.01,
        "effective_radius": 0.11,
        "rho_seg": 0.0,
    }
    return TaskMapAuthority(_plain_semantic_sha256(semantic), records)


def freeze_pr97_map_authority(checkout: Path):
    inst = checkout / "reproduction/instrumentation/l2_h1_on_policy_shadow_instrumentation_v1"
    sys.path.insert(0, str(inst))
    from map_authority import MapAuthorityFreezer

    map_root = (checkout / MAP_RELATIVE).resolve(strict=True)
    artifacts = [
        map_root / "config.yml",
        map_root / "dataparser_transforms.json",
        map_root / "nerfstudio_models/step-000029999.ckpt",
    ]
    return MapAuthorityFreezer().freeze(
        root=map_root,
        artifacts=artifacts,
        logical_map_name="STONEHENGE_OFFICIAL_SAFER_MAP",
        representation_contract="OFFICIAL_NERFSTUDIO_SPLATFACTO_ANISOTROPIC_GAUSSIAN_MAP",
        robot_radius=0.10,
        safety_margin=0.01,
        effective_radius=0.11,
        rho_seg=0.0,
    )


def build_real_frozen_adapter(checkout: Path, map_manifest):
    inst = checkout / "reproduction/instrumentation/l2_h1_on_policy_shadow_instrumentation_v1"
    shadow = checkout / "reproduction/shadow/l2_h1_shadow_certifier_v1"
    unified = checkout / "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1"
    for path in (inst, shadow, unified, checkout):
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))

    from adapters.gaussian_barrier_adapter import SourceGaussianBarrierAdapter
    from certifier.segment_backends.conservative_interval import ConservativeSignedDistanceIntervalBackend
    from frozen_certifier_adapter import ReadOnlyFrozenCertifierAdapter
    from l2_h1_shadow_certifier import l2_h1_shadow_certify, propagate_h1_endpoints
    from shadow_contract import CONSERVATIVE_ELLIPSOID_IDENTITY, load_frozen_robot_margin_contract
    from shadow_types import ExpectedMapSnapshot, FrozenMapQueryContext, ShadowCandidate, ShadowState
    from splat.gsplat_utils import GSplatLoader

    config = (checkout / MAP_RELATIVE / "config.yml").resolve(strict=True)
    loader = GSplatLoader(config, torch.device("cuda:0"))
    map_id = map_manifest.map_authority_id

    def bridge(point, **kwargs):
        if not torch.is_tensor(point):
            point = torch.as_tensor(point, device="cuda:0", dtype=torch.float32)
        return loader.query_distance(point, **kwargs)

    provider = SourceGaussianBarrierAdapter(bridge, map_id, 0.11, int(loader.means.shape[0]))
    backend = ConservativeSignedDistanceIntervalBackend(provider)
    context = FrozenMapQueryContext(
        backend, map_id, CONSERVATIVE_ELLIPSOID_IDENTITY,
        "CONSERVATIVE_LOWER_BOUND", None, "ANISOTROPIC_ELLIPSOID", map_id,
    )
    robot = load_frozen_robot_margin_contract()

    def l0(payload):
        query = provider.query(np.asarray(payload.p_k, dtype=np.float64), map_id, "FULL")
        status = getattr(query.status, "value", str(query.status))
        if status != "FINITE":
            return {"status": "UNKNOWN", "reason": str(query.reason_code)}
        return {"status": "PASS" if float(query.h) >= 0.0 else "FAIL", "reason": "FROZEN_L0_CURRENT_MAP_QUERY"}

    def l1(payload):
        state = ShadowState(payload.p_k, payload.v_k, payload.state_sequence_id, payload.dt)
        candidate = ShadowCandidate(payload.selected_candidate.u, payload.selected_candidate.candidate_id)
        h1 = propagate_h1_endpoints(state, candidate, payload.dt)
        certificate = backend.certify(
            np.asarray(payload.p_k, dtype=np.float64), np.asarray(h1.p_k1, dtype=np.float64),
            map_id, map_id, robot.effective_radius_m, robot.rho_seg,
        )
        raw = certificate.status.value
        mapped = {"CERTIFIED_SAFE": "PASS", "CERTIFIED_UNSAFE": "FAIL"}.get(raw, "UNKNOWN")
        return {"status": mapped, "reason": certificate.reason_code}

    def l2(payload):
        state = ShadowState(payload.p_k, payload.v_k, payload.state_sequence_id, payload.dt)
        candidate = ShadowCandidate(payload.selected_candidate.u, payload.selected_candidate.candidate_id)
        result = l2_h1_shadow_certify(
            state, candidate, ExpectedMapSnapshot(map_id, map_id), context, robot,
        )
        return {"status": result.status.value, "reason": result.reason_code}

    adapter = ReadOnlyFrozenCertifierAdapter(
        l0, l1, l2, backend_identity=CONSERVATIVE_ELLIPSOID_IDENTITY,
    )
    return adapter, loader


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--arm", choices=sorted(ARMS), required=True)
    parser.add_argument("--trial-id", type=int, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--queue-capacity", type=int, default=8)
    parser.add_argument("--shutdown-timeout", type=float, default=120.0)
    args = parser.parse_args()

    if os.environ.get("CUDA_VISIBLE_DEVICES") != "1":
        raise RuntimeError("CUDA_VISIBLE_DEVICES_MUST_BE_PHYSICAL_GPU_1")
    if not 0 <= args.trial_id < 100:
        raise ValueError("trial id outside frozen official100")

    checkout = args.checkout.resolve(strict=True)
    run_path = (checkout / "run.py").resolve(strict=True)
    run_dir = args.run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "outputs").symlink_to((checkout / "outputs").resolve(strict=True), target_is_directory=True)
    (run_dir / "data").symlink_to((checkout / "data").resolve(strict=True), target_is_directory=True)
    os.chdir(run_dir)
    sys.path.insert(0, str(checkout))
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.cuda.manual_seed_all(args.seed)

    arm_name = ARMS[args.arm]
    task_map_manifest = task_local_map_authority(checkout)
    if args.arm == "A":
        map_manifest = task_map_manifest
    else:
        map_manifest = freeze_pr97_map_authority(checkout)
        if map_manifest.map_authority_id != task_map_manifest.map_authority_id:
            raise RuntimeError("TASK_AND_PR97_MAP_AUTHORITY_MISMATCH")
    tracer = FrozenRunTraceCapture(run_path, trial_id=args.trial_id, seed=args.seed, map_authority_id=map_manifest.map_authority_id)
    before_threads = sorted(thread.name for thread in threading.enumerate())
    lifecycle = factory = actual_loader = None
    worker_ident_before = None
    shutdown = None

    with select_exact_official_trial(run_path, args.trial_id) as selection:
        previous_trace = sys.gettrace()
        sys.settrace(tracer)
        try:
            if args.arm == "A":
                globals_after = runpy.run_path(str(run_path), run_name="__main__")
            else:
                inst = checkout / "reproduction/instrumentation/l2_h1_on_policy_shadow_instrumentation_v1"
                if str(inst) not in sys.path:
                    sys.path.insert(0, str(inst))
                from append_only_logger import AppendOnlyEvidenceLogger
                from frozen_certifier_adapter import deterministic_test_adapter
                from lifecycle import ShadowInstrumentationLifecycle
                from run_with_shadow_instrumentation import execute_protected_run

                logger = AppendOnlyEvidenceLogger(run_dir / "instrumentation")
                if args.arm == "C":
                    adapter, actual_loader = build_real_frozen_adapter(checkout, map_manifest)
                    enabled, start_worker = True, True
                else:
                    adapter = deterministic_test_adapter()
                    enabled, start_worker = False, False
                lifecycle = ShadowInstrumentationLifecycle(
                    map_manifest=map_manifest,
                    logger=logger,
                    adapter=adapter,
                    queue_capacity=args.queue_capacity,
                    enabled=enabled,
                    start_worker=start_worker,
                )
                worker_ident_before = lifecycle.worker.ident
                globals_after, factory = execute_protected_run(
                    run_path=run_path, lifecycle=lifecycle, run_id=args.run_id, dt=0.05,
                )
        finally:
            sys.settrace(previous_trace)

    if lifecycle is not None:
        shutdown = lifecycle.shutdown(args.shutdown_timeout)
    trace = tracer.to_record(run_id=args.run_id, arm=arm_name)
    write_json(run_dir / "primary_trace.json", trace)

    inst_dir = run_dir / "instrumentation"
    captures = read_jsonl(inst_dir / "step_capture_log.jsonl")
    results = read_jsonl(inst_dir / "shadow_certificate_result_log.jsonl")
    health = read_jsonl(inst_dir / "instrumentation_health_log.jsonl")
    after_threads = sorted(thread.name for thread in threading.enumerate())
    worker_alive_after = bool(lifecycle and lifecycle.worker.is_alive())
    activation = {
        "schema_version": "L2_H1_SHADOW_EQUIVALENCE_ARM_ACTIVATION_V1",
        "arm": arm_name,
        "wrapper_loaded": args.arm in {"B", "C"},
        "wrapper_factory_trial_count": 0 if factory is None else factory._trial_counter,
        "wrapper_capture_attempt_count": 0 if factory is None else factory._payload_counter,
        "observer_enabled": args.arm == "C",
        "worker_start_requested": args.arm == "C",
        "worker_ident_after_start": worker_ident_before,
        "worker_alive_after_shutdown": worker_alive_after,
        "worker_processed_count": 0 if shutdown is None else shutdown.processed_count,
        "worker_exception_count": 0 if shutdown is None else shutdown.worker_exception_count,
        "shutdown_status": "NOT_APPLICABLE" if shutdown is None else shutdown.status,
        "capture_log_count": len(captures),
        "certificate_result_count": len(results),
        "health_log_count": len(health),
        "certificate_result_present": bool(results),
        "map_manifest_present": (inst_dir / "map_authority_manifest.json").is_file(),
        "controller_authority": False,
        "controller_intervention_count": 0,
        "selected_candidate_replacement_count": 0,
        "thread_names_before": before_threads,
        "thread_names_after": after_threads,
        "leftover_shadow_worker_count": sum(name == "l2-h1-shadow-worker-v1" for name in after_threads),
    }
    activation["intended_state_valid"] = (
        (args.arm == "A" and not activation["wrapper_loaded"] and worker_ident_before is None and not captures and not results)
        or (args.arm == "B" and activation["wrapper_loaded"] and activation["wrapper_factory_trial_count"] == 1 and worker_ident_before is None and not captures and not results)
        or (args.arm == "C" and activation["wrapper_loaded"] and worker_ident_before is not None and len(captures) > 0 and len(results) > 0 and activation["worker_processed_count"] > 0 and not worker_alive_after)
    )
    write_json(run_dir / "arm_activation.json", activation)

    environment = {
        "schema_version": "L2_H1_SHADOW_EQUIVALENCE_RUN_ENVIRONMENT_V1",
        "repo_commit": PR97_HEAD,
        "run_py_sha256": file_sha256(run_path),
        "run_py_git_blob_expected": "361f09fc8f37e4713ea2fc8975d82d56cb9be46a",
        "python": sys.version,
        "platform": platform.platform(),
        "executable": sys.executable,
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
        "cuda_device_name": torch.cuda.get_device_name(0),
        "numpy": np.__version__,
        "map_authority_id": map_manifest.map_authority_id,
        "map_artifact_count": len(map_manifest.artifacts),
        "dt": 0.05,
        "alpha": 5.0,
        "beta": 1.0,
        "controller_radius": 0.015,
        "distance_type": "ball-to-ellipsoid",
        "max_steps": 500,
        "seed": args.seed,
        "trial_id": args.trial_id,
        "deterministic_flags": {
            "PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED"),
            "CUBLAS_WORKSPACE_CONFIG": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
        },
    }
    environment["pairing_identity_hash"] = semantic_sha256({
        key: environment[key] for key in environment if key not in {"trial_id"}
    })
    write_json(run_dir / "environment_identity.json", environment)

    metadata = {
        "run_id": args.run_id,
        "pid": os.getpid(),
        "arm": arm_name,
        "trial_id": args.trial_id,
        "seed": args.seed,
        "qa_only": True,
        "selection": selection,
        "trace_step_count": len(trace["steps"]),
        "trace_hash": trace["primary_trace_semantic_hash"],
        "activation_valid": activation["intended_state_valid"],
        "protected_run_path": str(run_path),
        "protected_run_sha256": environment["run_py_sha256"],
        "runtime_output_path": str(run_dir / "trajs/stonehenge_ball-to-ellipsoid.json"),
        "runtime_output_exists": (run_dir / "trajs/stonehenge_ball-to-ellipsoid.json").is_file(),
    }
    write_json(run_dir / "run_metadata.json", metadata)
    print(json.dumps({"status": "RUN_COMPLETE", **metadata}, sort_keys=True), flush=True)

    if selection["selection_hit_count"] != 1 or not trace["steps"]:
        return 3
    if not activation["intended_state_valid"]:
        return 4
    if activation["leftover_shadow_worker_count"] != 0:
        return 5
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
