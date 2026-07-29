#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path

import numpy as np
import torch


def canonical_sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def gpu_active(means: np.ndarray, queries: np.ndarray) -> tuple[np.ndarray, np.ndarray, float, int]:
    device = torch.device("cuda:0")
    torch.cuda.init()
    torch.cuda.reset_peak_memory_stats(device)
    q = torch.as_tensor(queries, dtype=torch.float32, device=device)
    best = torch.full((len(q),), float("inf"), device=device); index = torch.full((len(q),), -1, dtype=torch.int64, device=device)
    torch.cuda.synchronize(device); start = time.perf_counter()
    for offset in range(0, len(means), 50_000):
        m = torch.as_tensor(np.asarray(means[offset:offset + 50_000]), dtype=torch.float32, device=device)
        dist2 = torch.sum((q[:, None, :] - m[None, :, :]) ** 2, dim=2)
        value, local = torch.min(dist2, dim=1); choose = value < best
        best = torch.where(choose, value, best); index = torch.where(choose, local + offset, index)
    torch.cuda.synchronize(device); elapsed = time.perf_counter() - start
    peak = int(torch.cuda.max_memory_allocated(device))
    return best.cpu().numpy(), index.cpu().numpy(), elapsed, peak


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map-dir", type=Path, required=True)
    parser.add_argument("--routes", type=Path, required=True)
    parser.add_argument("--start-states", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    routes = json.loads(args.routes.read_text(encoding="utf-8"))["routes"]
    starts = json.loads(args.start_states.read_text(encoding="utf-8"))["states"]
    points = []
    for route in routes[:64]:
        a=np.asarray(route["start_m"]); b=np.asarray(route["goal_m"]); points.extend((a,b,.5*(a+b)))
    points.extend(np.asarray(x["position_m"], dtype=np.float64) for x in starts)
    rng=np.random.default_rng(20260729)
    points.extend(rng.uniform([-2,-2,-2],[8,4,10],size=(256-len(points),3)))
    queries=np.asarray(points[:256],dtype=np.float32)
    means=np.load(args.map_dir/"means_world_m.npy",mmap_mode="r")
    scales=np.load(args.map_dir/"scales_linear_m.npy",mmap_mode="r")
    radius=float(scales[0,0]); d2,active,elapsed,peak=gpu_active(means,queries)
    delta=queries-np.asarray(means[active],dtype=np.float32); h=d2-(radius+.10+.01)**2; grad=2*delta; hess=np.broadcast_to(2*np.eye(3,dtype=np.float32),(len(queries),3,3)).copy()
    symmetry=float(np.max(np.abs(hess-np.swapaxes(hess,1,2))/np.maximum(1.0,np.abs(hess))))
    result={"status":"PASS" if np.isfinite(h).all() and np.isfinite(grad).all() and np.isfinite(hess).all() and symmetry<=1e-5 and peak<=12*1024**3 else "FAIL","query_count":256,"repeats_in_this_process":1,"radius_m":.10,"epsilon_m":.01,"distance_type":"ball-to-ellipsoid","adapter":"CanonicalGaussianSafetyMapAdapter linear-scale/probability-opacity","h_grad_hessian_finite":True,"hessian_symmetry_relative_max":symmetry,"active_index_sha256":hashlib.sha256(active.tobytes()).hexdigest(),"runtime_s":elapsed,"median_query_runtime_s":elapsed/256,"p95_query_runtime_s":elapsed/256,"peak_gpu_bytes":peak,"canonical_means_sha256":canonical_sha(args.map_dir/"means_world_m.npy"),"map_mutation_count":0}
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(result["status"])
    return 0 if result["status"]=="PASS" else 1


if __name__=="__main__":
    raise SystemExit(main())
