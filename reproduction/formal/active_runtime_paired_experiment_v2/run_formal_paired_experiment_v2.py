#!/usr/bin/env python3
"""Minimal, resumable Formal Paired Experiment V2 orchestrator.

This is task-local orchestration. It imports the already validated Pilot V2 arm
executor from the frozen checkout, expands its manifest to trial IDs 0..99,
and stores every run in an immutable attempt directory. Accepted arms are
indexed, never overwritten, and skipped on resume.
"""
from __future__ import annotations
import argparse, csv, hashlib, importlib.util, json, os, platform, shutil, subprocess, sys, time
from pathlib import Path
from typing import Any

METHOD_HEAD = "606edd1c254f4ffaec48e0b84d8f5e5f29c039ec"
ARMS = ("REFERENCE_CBF_QP", "ACTIVE_RUNTIME_V2")
ALL_TRIALS = tuple(range(100))
FROZEN_PATHS = (
    "reproduction/runtime/active_runtime_assurance_v2",
    "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1",
    "reproduction/smoke/active_runtime_smoke_v2/run_active_runtime_smoke_v2.py",
    "reproduction/pilot/active_runtime_pilot_v2/run_active_runtime_pilot_v2.py",
)

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def semantic_sha256(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(path)

def git(checkout: Path, *args: str, check: bool = True) -> str:
    p = subprocess.run(["git", "-C", str(checkout), *args], text=True, capture_output=True, check=check)
    return p.stdout.strip()

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def load_manifest(control_dir: Path):
    rows = []
    with (control_dir / "FORMAL_TRIAL_MANIFEST_V2.csv").open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            row["trial_id"] = int(row["trial_id"])
            row["execution_rank"] = int(row["execution_rank"])
            rows.append(row)
    rows.sort(key=lambda r: r["execution_rank"])
    ids = [r["trial_id"] for r in rows]
    if sorted(ids) != list(range(100)) or len(ids) != 100:
        raise RuntimeError("FORMAL_MANIFEST_NOT_EXACTLY_100_UNIQUE_TRIALS")
    return rows

def validate_protocol_hashes(control_dir: Path) -> None:
    path = control_dir / "FORMAL_PROTOCOL_FILE_HASHES_V2.json"
    if not path.exists():
        return
    hashes = load_json(path)
    for name, expected in hashes.items():
        p = control_dir / name
        if not p.exists() or sha256_file(p) != expected:
            raise RuntimeError("FORMAL_PROTOCOL_HASH_MISMATCH:" + name)

def verify_frozen_source(checkout: Path) -> None:
    subprocess.run(["git", "-C", str(checkout), "cat-file", "-e", METHOD_HEAD + "^{commit}"], check=True)
    # Current checkout may be a protocol-only descendant, but all execution dependencies must match METHOD_HEAD.
    if subprocess.run(["git", "-C", str(checkout), "merge-base", "--is-ancestor", METHOD_HEAD, "HEAD"]).returncode != 0:
        if git(checkout, "rev-parse", "HEAD") != METHOD_HEAD:
            raise RuntimeError("CHECKOUT_NOT_METHOD_HEAD_OR_DESCENDANT")
    for p in FROZEN_PATHS:
        if git(checkout, "diff", "--name-only", METHOD_HEAD, "--", p):
            raise RuntimeError("FROZEN_SOURCE_DRIFT:" + p)
        if git(checkout, "diff", "--name-only", "--", p) or git(checkout, "diff", "--cached", "--name-only", "--", p):
            raise RuntimeError("FROZEN_SOURCE_DIRTY:" + p)

def formal_verify_inputs(checkout: Path, config: dict[str, Any]):
    verify_frozen_source(checkout)
    map_root = (checkout / config["map_relative_path"]).resolve(strict=True)
    actual = []
    for expected in config["map_artifacts"]:
        p = map_root / expected["relative_path"]
        row = {"relative_path": expected["relative_path"], "size": p.stat().st_size, "sha256": sha256_file(p)}
        if row != expected:
            raise RuntimeError("MAP_ARTIFACT_IDENTITY_MISMATCH:" + expected["relative_path"])
        actual.append(row)
    identity = semantic_sha256({"scene": "stonehenge", "artifacts": actual})
    if identity != config["map_identity"]:
        raise RuntimeError("MAP_SEMANTIC_IDENTITY_MISMATCH")
    return identity, actual

def load_pilot(checkout: Path, control_dir: Path):
    path = checkout / "reproduction/pilot/active_runtime_pilot_v2/run_active_runtime_pilot_v2.py"
    spec = importlib.util.spec_from_file_location("formal_frozen_pilot_executor", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("PILOT_EXECUTOR_IMPORT_FAILED")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.FIXED_TRIALS = ALL_TRIALS
    m.FIXED_ARMS = ARMS
    m.CONFIG_PATH = control_dir / "FORMAL_RUN_CONFIG_V2.json"
    m.verify_inputs = formal_verify_inputs
    return m

def gpu_one_clean() -> bool:
    p = subprocess.run(
        ["nvidia-smi", "-i", "1", "--query-compute-apps=pid,process_name", "--format=csv,noheader,nounits"],
        text=True, capture_output=True, check=False
    )
    return p.returncode == 0 and not p.stdout.strip()

def capture_environment(checkout: Path, control_dir: Path, result_dir: Path):
    validate_protocol_hashes(control_dir)
    verify_frozen_source(checkout)
    config = load_json(control_dir / "FORMAL_RUN_CONFIG_V2.json")
    formal_verify_inputs(checkout, config)
    if not gpu_one_clean():
        raise RuntimeError("GPU_1_NOT_CLEAN_AT_PREFLIGHT")
    py = sys.executable
    probe = subprocess.run(
        [py, "-c", "import json,torch,numpy; print(json.dumps({'python':__import__('platform').python_version(),'torch':torch.__version__,'cuda':torch.version.cuda,'numpy':numpy.__version__,'cuda_available':torch.cuda.is_available(),'cuda_device_count':torch.cuda.device_count()}))"],
        text=True, capture_output=True, check=True,
        env={**os.environ, **config["environment"]}
    )
    pip = subprocess.run([py, "-m", "pip", "freeze"], text=True, capture_output=True, check=False)
    nvsmi = subprocess.run(["nvidia-smi"], text=True, capture_output=True, check=False)
    payload = {
        "schema": "FORMAL_ENVIRONMENT_MANIFEST_V2",
        "captured_at_unix": time.time(),
        "method_head": METHOD_HEAD,
        "checkout_head": git(checkout, "rev-parse", "HEAD"),
        "worktree_status": git(checkout, "status", "--porcelain"),
        "runtime_probe": json.loads(probe.stdout),
        "pip_freeze": pip.stdout.splitlines(),
        "pip_freeze_sha256": hashlib.sha256(pip.stdout.encode()).hexdigest(),
        "nvidia_smi": nvsmi.stdout,
        "nvidia_smi_sha256": hashlib.sha256(nvsmi.stdout.encode()).hexdigest(),
        "gpu1_clean": True,
        "platform": platform.platform(),
    }
    write_json(result_dir / "FORMAL_ENVIRONMENT_MANIFEST.json", payload)
    print("PREFLIGHT=PASS")
    return 0

def accepted_index_path(result_dir: Path) -> Path:
    return result_dir / "FORMAL_ACCEPTED_INDEX.json"

def load_index(result_dir: Path):
    p = accepted_index_path(result_dir)
    return load_json(p) if p.exists() else {"schema": "FORMAL_ACCEPTED_INDEX_V2", "arms": {}}

def arm_key(trial_id: int, arm: str) -> str:
    return f"{trial_id:03d}:{arm}"

def validate_existing_acceptance(result_dir: Path, trial_id: int, arm: str) -> bool:
    idx = load_index(result_dir)
    entry = idx["arms"].get(arm_key(trial_id, arm))
    if not entry:
        return False
    p = Path(entry["summary_path"])
    if not p.exists() or sha256_file(p) != entry["summary_sha256"]:
        raise RuntimeError("ACCEPTED_EVIDENCE_DRIFT:" + arm_key(trial_id, arm))
    return True

def next_attempt_dir(result_dir: Path, trial_id: int, arm: str) -> Path:
    root = result_dir / "attempts" / f"trial_{trial_id:03d}" / arm.lower()
    root.mkdir(parents=True, exist_ok=True)
    existing = [p for p in root.glob("attempt_*") if p.is_dir()]
    n = max([int(p.name.split("_")[-1]) for p in existing], default=0) + 1
    d = root / f"attempt_{n:03d}"
    d.mkdir()
    return d

def summary_path(attempt_dir: Path, trial_id: int, arm: str) -> Path:
    return attempt_dir / "raw" / f"trial_{trial_id:03d}" / arm.lower() / "summary.json"

def acceptance_check(summary: dict[str, Any], arm: str, child_rc: int, gpu_clean: bool):
    reasons = []
    if child_rc != 0: reasons.append("CHILD_NONZERO")
    if not gpu_clean: reasons.append("GPU_NOT_RELEASED")
    if summary.get("hard_blocker"): reasons.append("HARD_BLOCKER")
    if not summary.get("execution_complete"): reasons.append("EXECUTION_INCOMPLETE")
    if not summary.get("evaluation_eligible"): reasons.append("EVALUATION_INELIGIBLE")
    if not summary.get("raw_evidence_lock"): reasons.append("RAW_EVIDENCE_UNLOCKED")
    if int(summary.get("integrity_failure_count", 0)) != 0: reasons.append("INTEGRITY_FAILURE")
    if arm == "ACTIVE_RUNTIME_V2":
        if summary.get("finalization_status") != "FINALIZED": reasons.append("ACTIVE_NOT_FINALIZED")
        if summary.get("trace_record_count") != summary.get("completed_cycles"): reasons.append("TRACE_CYCLE_MISMATCH")
    return len(reasons) == 0, reasons

def record_acceptance(result_dir: Path, trial_id: int, arm: str, attempt_dir: Path, summary: dict[str, Any], summary_file: Path):
    idx = load_index(result_dir)
    key = arm_key(trial_id, arm)
    if key in idx["arms"]:
        raise RuntimeError("ATTEMPT_TO_OVERWRITE_ACCEPTED_ARM:" + key)
    idx["arms"][key] = {
        "trial_id": trial_id,
        "arm": arm,
        "attempt_dir": str(attempt_dir.resolve()),
        "summary_path": str(summary_file.resolve()),
        "summary_sha256": sha256_file(summary_file),
        "raw_evidence_lock": summary.get("raw_evidence_lock"),
        "accepted_at_unix": time.time(),
    }
    write_json(accepted_index_path(result_dir), idx)

def run_parent_arm(checkout: Path, control_dir: Path, result_dir: Path, trial_id: int, arm: str):
    if validate_existing_acceptance(result_dir, trial_id, arm):
        print(f"SKIP_ACCEPTED trial={trial_id} arm={arm}")
        return True
    if not gpu_one_clean():
        raise RuntimeError("GPU_1_NOT_CLEAN_BEFORE_ARM")
    attempt = next_attempt_dir(result_dir, trial_id, arm)
    config = load_json(control_dir / "FORMAL_RUN_CONFIG_V2.json")
    env = {**os.environ, **config["environment"]}
    cmd = [
        sys.executable, str(Path(__file__).resolve()), "--child",
        "--checkout", str(checkout), "--control-dir", str(control_dir),
        "--result-dir", str(result_dir), "--attempt-dir", str(attempt),
        "--trial", str(trial_id), "--arm", arm
    ]
    started = time.time()
    with (attempt / "stdout.log").open("w", encoding="utf-8") as so, (attempt / "stderr.log").open("w", encoding="utf-8") as se:
        p = subprocess.run(cmd, env=env, stdout=so, stderr=se)
    clean = gpu_one_clean()
    sp = summary_path(attempt, trial_id, arm)
    summary = load_json(sp) if sp.exists() else {}
    accepted, reasons = acceptance_check(summary, arm, p.returncode, clean)
    meta = {
        "trial_id": trial_id, "arm": arm, "attempt_dir": str(attempt.resolve()),
        "child_return_code": p.returncode, "gpu1_clean_after": clean,
        "accepted": accepted, "reasons": reasons, "started_unix": started,
        "finished_unix": time.time(), "summary_exists": sp.exists(),
        "summary_sha256": sha256_file(sp) if sp.exists() else None,
    }
    write_json(attempt / "attempt_meta.json", meta)
    if accepted:
        record_acceptance(result_dir, trial_id, arm, attempt, summary, sp)
        print(f"ACCEPTED trial={trial_id} arm={arm}")
        return True
    print(f"STOP_UNACCEPTED trial={trial_id} arm={arm} reasons={','.join(reasons)}", file=sys.stderr)
    return False

def child_run(checkout: Path, control_dir: Path, attempt_dir: Path, trial_id: int, arm: str):
    config = load_json(control_dir / "FORMAL_RUN_CONFIG_V2.json")
    os.environ.update(config["environment"])
    pilot = load_pilot(checkout, control_dir)
    return int(pilot.run_one(checkout, attempt_dir, trial_id, arm))

def status(control_dir: Path, result_dir: Path):
    rows = load_manifest(control_dir)
    idx = load_index(result_dir)
    accepted = idx["arms"]
    primary_ids = {r["trial_id"] for r in rows if str(r["included_in_primary_85"]).lower() == "true"}
    accepted_primary = sum(1 for k,v in accepted.items() if int(v["trial_id"]) in primary_ids)
    print(f"accepted_arms={len(accepted)}/200")
    print(f"accepted_primary_arms={accepted_primary}/{2*len(primary_ids)}")
    for row in rows:
        tid = row["trial_id"]
        for arm in (row["arm_1"], row["arm_2"]):
            if arm_key(tid, arm) not in accepted:
                print(f"next_pending=trial_{tid:03d}:{arm}")
                return
    print("next_pending=NONE")

def build_difficulty(checkout: Path, control_dir: Path, result_dir: Path):
    target = result_dir / "FORMAL_DIFFICULTY_STRATA.csv"
    if target.exists():
        print("DIFFICULTY_ALREADY_EXISTS")
        return 0
    config = load_json(control_dir / "FORMAL_RUN_CONFIG_V2.json")
    pilot = load_pilot(checkout, control_dir)
    map_identity, _ = formal_verify_inputs(checkout, config)
    os.chdir(checkout)
    unified = checkout / "reproduction/cross_dataset/fas_cbf_unified_executable_safety_certifier_v1"
    sys.path[:0] = [str(unified), str(checkout)]
    import numpy as np, torch
    from adapters.gaussian_barrier_adapter import SourceGaussianBarrierAdapter
    from splat.gsplat_utils import GSplatLoader
    loader = GSplatLoader((checkout / config["map_relative_path"] / "config.yml").resolve(strict=True), torch.device("cuda:0"))
    def provider(radius):
        def query(point, **kwargs):
            if not torch.is_tensor(point):
                point = torch.as_tensor(point, device=torch.device("cuda:0"), dtype=torch.float32)
            return loader.query_distance(point, **kwargs)
        return SourceGaussianBarrierAdapter(query, map_identity, radius, int(loader.means.shape[0]))
    p15, p25 = provider(0.015), provider(0.025)
    records = []
    for tid in range(100):
        start, goal = pilot.trial_geometry(tid)
        def clr(prov, a, b, radius):
            st, c = pilot.certify_segment_clearance(prov, np.asarray(a), np.asarray(b), radius)
            if st == "UNKNOWN" or c is None:
                raise RuntimeError(f"DIFFICULTY_CLEARANCE_UNKNOWN trial={tid}")
            return float(c)
        records.append({
            "trial_id": tid,
            "start_clearance_0p015_m": clr(p15, start, start, 0.015),
            "start_clearance_0p025_m": clr(p25, start, start, 0.025),
            "goal_clearance_0p015_m": clr(p15, goal, goal, 0.015),
            "goal_clearance_0p025_m": clr(p25, goal, goal, 0.025),
            "straight_line_min_clearance_0p025_m": clr(p25, start, goal, 0.025),
            "start_goal_distance_m": float(np.linalg.norm(np.asarray(start)-np.asarray(goal))),
        })
    ordered = sorted(records, key=lambda r: (r["straight_line_min_clearance_0p025_m"], r["trial_id"]))
    for rank, r in enumerate(ordered):
        r["difficulty_rank_hard_to_easy"] = rank + 1
        r["difficulty_stratum"] = "HARD" if rank < 33 else ("MODERATE" if rank < 67 else "EASY")
    by_id = {r["trial_id"]: r for r in ordered}
    fields = list(records[0].keys()) + ["difficulty_rank_hard_to_easy", "difficulty_stratum"]
    with target.open("w", encoding="utf-8", newline="") as f:
        w=csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for tid in range(100): w.writerow(by_id[tid])
    print("DIFFICULTY=PASS")
    del loader
    torch.cuda.empty_cache()
    return 0

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--checkout", type=Path, required=True)
    ap.add_argument("--control-dir", type=Path, required=True)
    ap.add_argument("--result-dir", type=Path, required=True)
    modes=ap.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preflight", action="store_true")
    modes.add_argument("--build-difficulty", action="store_true")
    modes.add_argument("--run", action="store_true")
    modes.add_argument("--status", action="store_true")
    modes.add_argument("--one", action="store_true")
    modes.add_argument("--child", action="store_true")
    ap.add_argument("--trial", type=int)
    ap.add_argument("--arm", choices=ARMS)
    ap.add_argument("--attempt-dir", type=Path)
    a=ap.parse_args()
    checkout=a.checkout.resolve(strict=True); control=a.control_dir.resolve(strict=True); result=a.result_dir.resolve()
    result.mkdir(parents=True, exist_ok=True)
    if a.preflight: return capture_environment(checkout, control, result)
    if a.build_difficulty: return build_difficulty(checkout, control, result)
    if a.status: status(control, result); return 0
    if a.child:
        if a.trial is None or a.arm is None or a.attempt_dir is None: raise SystemExit("--child needs --trial --arm --attempt-dir")
        return child_run(checkout, control, a.attempt_dir.resolve(), a.trial, a.arm)
    if not (result/"FORMAL_ENVIRONMENT_MANIFEST.json").exists(): raise RuntimeError("RUN_PREFLIGHT_FIRST")
    if not (result/"FORMAL_DIFFICULTY_STRATA.csv").exists(): raise RuntimeError("BUILD_DIFFICULTY_BEFORE_FORMAL_RUN")
    validate_protocol_hashes(control); verify_frozen_source(checkout)
    if a.one:
        if a.trial is None or a.arm is None: raise SystemExit("--one needs --trial --arm")
        return 0 if run_parent_arm(checkout, control, result, a.trial, a.arm) else 2
    rows=load_manifest(control)
    for row in rows:
        tid=row["trial_id"]
        for arm in (row["arm_1"], row["arm_2"]):
            if not run_parent_arm(checkout, control, result, tid, arm):
                return 2
    print("FORMAL_COLLECTION_COMPLETE=200/200_ACCEPTED")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
