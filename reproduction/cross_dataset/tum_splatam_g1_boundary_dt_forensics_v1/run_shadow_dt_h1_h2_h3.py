#!/usr/bin/env python3
"""Shadow-only replay of the frozen H=1,2,3 repeated-control DT contract."""
from __future__ import annotations

import csv
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
SOURCE = Path("/disk1/zlab/maintenance_records/tum_splatam_one_shot_runtime_recovery_g1_v2/user_file_archive_remaining/extracted_verification_attempt_04_gnu_pax/work/risk_aware_cbf/scripts/run_dt_verification_only_audit.py")
sys.path.insert(0, str(REPO))
from splat.gsplat_utils import DummyGSplatLoader  # noqa: E402

DT, RADIUS, DT_MARGIN = np.float32(0.05), 0.015, 0.0005


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_loader() -> DummyGSplatLoader:
    device = torch.device("cuda:0")
    loader = DummyGSplatLoader(device)
    loader.initialize_attributes(
        torch.from_numpy(np.load(MAP / "means_world_m.npy")).to(device=device, dtype=torch.float32),
        torch.from_numpy(np.load(MAP / "quaternions_wxyz.npy")).to(device=device, dtype=torch.float32),
        torch.from_numpy(np.load(MAP / "scales_linear_m.npy")).to(device=device, dtype=torch.float32),
    )
    return loader


def h_and_active(loader: DummyGSplatLoader, x: np.ndarray) -> tuple[float, int]:
    pos = torch.tensor(x[:3], dtype=torch.float32, device=loader.device)
    with torch.no_grad():
        h, _, _, _ = loader.query_distance(pos, radius=RADIUS, distance_type="ball-to-ellipsoid")
        value, idx = torch.min(h.reshape(-1), dim=0)
        return float(value.item()), int(idx.item())


def advance(x: np.ndarray, u: np.ndarray) -> np.ndarray:
    return (x + DT * np.concatenate((x[3:], u)).astype(np.float32)).astype(np.float32)


def main() -> None:
    out = ROOT / "dt_h1_h2_h3"
    out.mkdir(parents=True, exist_ok=True)
    states_path = ROOT / "trajectory_recovery" / "trajectory_states.npy"
    steps_path = Path("/disk1/zlab/maintenance_records/tum_splatam_one_shot_runtime_recovery_g1_v2/resumed_trials/one_trial_steps.json")
    states = np.fromfile(states_path, dtype=np.float32).reshape(-1, 6)
    steps = json.loads(steps_path.read_text(encoding="utf-8"))
    if len(steps) != len(states) - 1:
        raise RuntimeError(f"state/control length mismatch: {len(states)} states, {len(steps)} controls")
    control_bytes = b"".join(np.asarray(row["u"], dtype=np.float32).tobytes() for row in steps)
    loader = load_loader()
    rows: list[dict[str, object]] = []
    started = time.time()
    for k, logged in enumerate(steps):
        x = states[k]
        u = np.asarray(logged["u"], dtype=np.float32)
        current_h, current_active = h_and_active(loader, x)
        cur = x.copy()
        predicted: list[tuple[float, int]] = []
        for _ in range(3):
            cur = advance(cur, u)
            predicted.append(h_and_active(loader, cur))
        rows.append({
            "step": k,
            "current_h": current_h,
            "current_active": current_active,
            "h1": predicted[0][0], "h1_active": predicted[0][1], "h1_warning": predicted[0][0] < DT_MARGIN,
            "h2": min(predicted[0][0], predicted[1][0]), "h2_terminal_h": predicted[1][0], "h2_active": predicted[1][1], "h2_warning": min(predicted[0][0], predicted[1][0]) < DT_MARGIN,
            "h3": min(v[0] for v in predicted), "h3_terminal_h": predicted[2][0], "h3_active": predicted[2][1], "h3_warning": min(v[0] for v in predicted) < DT_MARGIN,
            "u": [float(v) for v in u],
        })
        if k % 25 == 0 or k == len(steps) - 1:
            print(json.dumps({"step": k, "current_h": current_h, "h1": predicted[0][0], "h2": rows[-1]["h2"], "h3": rows[-1]["h3"]}), flush=True)
    fields = list(rows[0].keys())
    with (out / "shadow_h1_h2_h3_per_step.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    summaries = {}
    for horizon in (1, 2, 3):
        key = f"h{horizon}"
        warning_key = f"h{horizon}_warning"
        warned = [row for row in rows if bool(row[warning_key])]
        summaries[key] = {
            "horizon": horizon,
            "warning_threshold": DT_MARGIN,
            "warning_count": len(warned),
            "first_warning_step": warned[0]["step"] if warned else None,
            "minimum_predicted_h": min(float(row[key]) for row in rows),
            "control_hold_semantics": "u_safe[k] held constant for H explicit-Euler steps",
        }
    common = {
        "source_path": str(SOURCE),
        "source_sha256": sha256_file(SOURCE),
        "source_contract": "frozen run_dt_verification_only_audit.py: horizons=[1,2,3], repeated safe control, dt_margin=0.0005",
        "state_sha256": sha256_file(states_path),
        "safe_control_sha256": sha256_bytes(control_bytes),
        "state_control_modified": False,
        "runtime_integrator": "x_next=x+dt*[v,u]",
        "dt": float(DT),
        "radius": RADIUS,
        "map_candidate_count": 5464102,
        "runtime_seconds": time.time() - started,
    }
    for key, summary in summaries.items():
        payload = {**common, **summary}
        (ROOT / f"dt_{key}" / "summary.json").parent.mkdir(parents=True, exist_ok=True)
        (ROOT / f"dt_{key}" / "summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out / "shadow_h1_h2_h3_summary.json").write_text(json.dumps({**common, **summaries}, indent=2), encoding="utf-8")
    print(json.dumps({**common, **summaries}, indent=2))


if __name__ == "__main__":
    main()
