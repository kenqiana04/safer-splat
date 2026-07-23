#!/usr/bin/env python3
"""Audit the frozen explicit-Euler state transition without re-executing G1."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path("/disk1/zlab/maintenance_records/tum_splatam_g1_boundary_dt_forensics_v1")
OLD = Path("/disk1/zlab/maintenance_records/tum_splatam_one_shot_runtime_recovery_g1_v2/resumed_trials/one_trial_steps.json")


def main() -> None:
    states_path = ROOT / "trajectory_recovery" / "trajectory_states.npy"
    states = np.fromfile(states_path, dtype=np.float32).reshape(-1, 6)
    steps = json.loads(OLD.read_text(encoding="utf-8"))
    rebuilt = [states[0].copy()]
    alternate = [states[0].astype(np.float64).copy()]
    for row in steps:
        u = np.asarray(row["u"], dtype=np.float32)
        x = rebuilt[-1]
        rebuilt.append((x + np.float32(.05)*np.r_[x[3:], u]).astype(np.float32))
        xa = alternate[-1]; ua = u.astype(np.float64)
        alternate.append(xa + .05*np.r_[xa[3:]+.5*.05*ua, ua])
    rebuilt = np.asarray(rebuilt)
    alternate = np.asarray(alternate)
    summary = {
        "runtime_integrator": "A: p_next=p+dt*v; v_next=v+dt*u (implemented as x_next=x+dt*[v,u])",
        "dt": .05,
        "state_count": int(len(states)),
        "control_count": int(len(steps)),
        "reconstructed_state_max_abs_difference": float(np.max(np.abs(states-rebuilt))),
        "runtime_log_direct_state_sequence_available": False,
        "comparison_scope": "The PR47 steps log contains safe controls but not separately logged x_k values; the recovered sequence is the deterministic control replay, so a direct logged-state mismatch cannot be asserted.",
        "alternate_B_formula": "p_next=p+dt*v+0.5*dt^2*u; v_next=v+dt*u",
        "alternate_B_max_abs_difference": float(np.max(np.abs(states.astype(np.float64)-alternate))),
        "integration_log_mismatch": False,
        "integration_log_mismatch_certifiable": False,
        "states_sha256": hashlib.sha256(states_path.read_bytes()).hexdigest(),
    }
    out = ROOT / "integration_audit"; out.mkdir(parents=True, exist_ok=True)
    (out / "integration_audit_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
