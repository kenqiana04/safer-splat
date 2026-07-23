#!/usr/bin/env python3
"""Replay frozen PR47 states through the unmodified full-map query contract."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path("/disk1/zlab/maintenance_records/tum_splatam_g1_boundary_dt_forensics_v1")
MAP = Path("/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/splatam/canonical_export/export_a")
REPO = Path("/disk1/zlab/projects/safer-splat")
sys.path.insert(0, str(REPO))
from splat.gsplat_utils import DummyGSplatLoader  # noqa: E402

RADIUS = 0.015
WINDOW = range(740, 774)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_loader() -> DummyGSplatLoader:
    device = torch.device("cuda:0")
    means = torch.from_numpy(np.load(MAP / "means_world_m.npy")).to(device=device, dtype=torch.float32)
    quats = torch.from_numpy(np.load(MAP / "quaternions_wxyz.npy")).to(device=device, dtype=torch.float32)
    scales = torch.from_numpy(np.load(MAP / "scales_linear_m.npy")).to(device=device, dtype=torch.float32)
    loader = DummyGSplatLoader(device)
    loader.initialize_attributes(means, quats, scales)
    return loader


def query(loader: DummyGSplatLoader, pos: np.ndarray) -> dict[str, object]:
    x = torch.tensor(pos, dtype=torch.float32, device=loader.device)
    with torch.no_grad():
        h, grad, hess, info = loader.query_distance(x, radius=RADIUS, distance_type="ball-to-ellipsoid")
        values, indices = torch.topk(h.reshape(-1), k=32, largest=False, sorted=True)
        active = int(indices[0].item())
        tied = torch.where(torch.isclose(h.reshape(-1), values[0], rtol=0.0, atol=0.0))[0]
        result = {
            "h": float(values[0].item()),
            "active_index": active,
            "top32_indices": [int(v) for v in indices.cpu().tolist()],
            "top32_h": [float(v) for v in values.cpu().tolist()],
            "tie_indices_exact": [int(v) for v in tied.cpu().tolist()],
            "candidate_count": int(h.numel()),
            "gradient": [float(v) for v in grad[active].cpu().tolist()],
            "hessian": [[float(v) for v in row] for row in hess[active].cpu().tolist()],
            "closest_point": [float(v) for v in info["y"][active].cpu().tolist()],
            "phi": float(info["phi"][active].cpu().item()),
        }
    return result


def main() -> None:
    out = ROOT / "fullmap_queries"
    out.mkdir(parents=True, exist_ok=True)
    states_path = ROOT / "trajectory_recovery" / "trajectory_states.npy"
    states = np.fromfile(states_path, dtype=np.float32).reshape(-1, 6)
    loader = load_loader()
    rows: list[dict[str, object]] = []
    started = time.time()
    for k in WINDOW:
        labels = [("x_k", k)]
        # The terminal state is step 773.  There is no logged x_774 because the
        # frozen run stopped immediately after evaluating that terminal state.
        if k + 1 < len(states):
            labels.append(("x_next_logged", k + 1))
        for label, state_index in labels:
            item = query(loader, states[state_index, :3])
            item.update({"step": k, "state_label": label, "state_index": state_index, "position": [float(v) for v in states[state_index, :3]]})
            rows.append(item)
            print(json.dumps({"step": k, "label": label, "h": item["h"], "active": item["active_index"]}), flush=True)
    terminal = next(row for row in rows if row["step"] == 773 and row["state_label"] == "x_k")
    payload = {
        "query_semantics": "unmodified GSplatLoader.query_distance(ball-to-ellipsoid); all 5,464,102 canonical Gaussians",
        "radius": RADIUS,
        "window": [740, 773],
        "rows": len(rows),
        "states_sha256": sha256(states_path),
        "terminal": terminal,
        "runtime_seconds": time.time() - started,
    }
    (out / "event_window_fullmap.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    (out / "event_window_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
