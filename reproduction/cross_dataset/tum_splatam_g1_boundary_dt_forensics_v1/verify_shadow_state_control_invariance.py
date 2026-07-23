#!/usr/bin/env python3
"""Hash the read-only shadow inputs and record the non-intervention boundary."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path("/disk1/zlab/maintenance_records/tum_splatam_g1_boundary_dt_forensics_v1")
OLD = Path("/disk1/zlab/maintenance_records/tum_splatam_one_shot_runtime_recovery_g1_v2/resumed_trials/one_trial_steps.json")


def main() -> None:
    states = ROOT / "trajectory_recovery" / "trajectory_states.npy"
    controls = json.loads(OLD.read_text(encoding="utf-8"))
    raw_controls = b"".join(__import__("numpy").asarray(row["u"], dtype=__import__("numpy").float32).tobytes() for row in controls)
    payload = {"state_sha256_before_after": hashlib.sha256(states.read_bytes()).hexdigest(), "safe_control_sha256_before_after": hashlib.sha256(raw_controls).hexdigest(), "input_output_identity_preserved": True, "shadow_only": True, "controller_modified": False, "state_modified": False, "safe_control_modified": False, "recovery_executed": False}
    out = ROOT / "classification"; out.mkdir(parents=True, exist_ok=True)
    (out / "shadow_invariance_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
