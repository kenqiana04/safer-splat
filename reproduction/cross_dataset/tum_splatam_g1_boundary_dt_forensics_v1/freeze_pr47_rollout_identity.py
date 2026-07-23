#!/usr/bin/env python3
"""Freeze the server-side artifacts consumed by this forensic audit."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path("/disk1/zlab/maintenance_records/tum_splatam_g1_boundary_dt_forensics_v1")
REPO = Path("/disk1/zlab/projects/safer-splat")
OLD = Path("/disk1/zlab/maintenance_records/tum_splatam_one_shot_runtime_recovery_g1_v2/resumed_trials")
MAP = Path("/disk1/zlab/maintenance_records/tum_common_gaussian_map_adapter_qualification_v1/splatam/canonical_export/export_a")
TRANSFORMS = Path("/disk1/zlab/cross_dataset_assets/processed/tum_rgbd/freiburg1_room/transforms.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def blob(path: str) -> str:
    return subprocess.check_output(["git", "-C", str(REPO), "rev-parse", f"HEAD:{path}"], text=True).strip()


def main() -> None:
    artifacts = {"steps": OLD / "one_trial_steps.json", "summary": OLD / "one_trial_summary.json", "transforms": TRANSFORMS}
    payload = {
        "server_checkout_head": subprocess.check_output(["git", "-C", str(REPO), "rev-parse", "HEAD"], text=True).strip(),
        "required_checkout_head": "f63b4c496861c4f8881348d74244c1ff9a528d51",
        "source_blobs": {p: blob(p) for p in ("splat/distances.py", "splat/gsplat_utils.py", "cbf/cbf_utils.py")},
        "required_source_blobs": {"splat/distances.py": "d7f17b67df40e36e458c7a5ed77c4a04659c6f35", "splat/gsplat_utils.py": "782c38eca50e78c605085b481155ed61e4607336", "cbf/cbf_utils.py": "7c6e1300b125cc0a2a950ac2835a1fbe3d0de113"},
        "artifact_sha256": {key: digest(path) for key, path in artifacts.items()},
        "canonical_map": str(MAP), "canonical_gaussian_count": 5464102,
        "frozen_trial": {"start_frame": 0, "goal_frame": 50, "radius": .015, "alpha": 5., "beta": 1., "dt": .05, "max_steps": 800, "goal_tolerance": .001},
    }
    payload["identity_matches"] = payload["server_checkout_head"] == payload["required_checkout_head"] and payload["source_blobs"] == payload["required_source_blobs"]
    out = ROOT / "input_identity"; out.mkdir(parents=True, exist_ok=True)
    (out / "input_identity.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
